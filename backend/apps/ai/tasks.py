import asyncio
import json
import logging
import re

from celery import shared_task

from llm_providers.registry import get_llm_provider

from .models import AIGeneration, AIUsageLog, CoverLetter
from .prompts import (
    ATS_SCORE_PROMPT,
    ATS_SCORE_SYSTEM,
    COVER_LETTER_PROMPT,
    COVER_LETTER_SYSTEM,
    FIT_SCORE_PROMPT,
    FIT_SCORE_SYSTEM,
    QA_PROMPT,
    QA_SYSTEM,
)

logger = logging.getLogger(__name__)

LENGTH_MAP = {"brief": "250 words", "standard": "400 words", "detailed": "600 words"}


def _extract_json(text: str) -> dict | None:
    """Robustly pull a JSON object out of an LLM response. Handles code
    fences (```json ... ```), preamble text, and trailing prose.
    Returns None if nothing usable is found."""
    if not text:
        return None
    # Strip markdown code fences if present.
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    # Direct parse first.
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    # Fallback: find the first balanced {...} block. Greedy on outer braces.
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _publish_chunk(task_id: str, chunk: str, done: bool = False):
    """Publish a token chunk to the Redis pubsub channel for SSE streaming."""
    import json

    import redis
    from django.conf import settings

    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        channel = f"cover_letter:{task_id}"
        r.publish(channel, json.dumps({"chunk": chunk, "done": done}))
    except Exception as e:
        logger.warning(f"Failed to publish to {task_id}: {e}")


async def _stream_and_collect(provider, prompt, system, task_id):
    """Stream tokens from provider, publishing each chunk and returning full text."""
    full_text = ""
    async for chunk in provider.stream(prompt, {"system": system}):
        full_text += chunk
        _publish_chunk(task_id, chunk, done=False)
    _publish_chunk(task_id, "", done=True)
    return full_text


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_cover_letter(
    self,
    user_id: int,
    cv_text: str,
    job_description: str,
    company: str,
    job_title: str,
    tone: str = "formal",
    length: str = "standard",
    emphasis: str = "skills",
    notes: str = "",
    provider_name: str = "gemini",
    model_name: str | None = None,
    application_id: int | None = None,
    cv_version_id: int | None = None,
    reservation_id: int | None = None,
):
    from apps.billing.quotas import (
        finalize_ai_reservation,
        release_ai_reservation,
    )

    try:
        provider = get_llm_provider(provider_name, model_name)
        task_id = self.request.id

        prompt = COVER_LETTER_PROMPT.format(
            job_title=job_title,
            company=company,
            job_description=job_description,
            cv_text=cv_text,
            tone=tone,
            length=LENGTH_MAP.get(length, "400 words"),
            emphasis=emphasis,
            additional_notes=f"Additional notes: {notes}" if notes else "",
        )

        # Try streaming first; fall back to single generate() if it fails
        try:
            full_text = asyncio.run(
                _stream_and_collect(provider, prompt, COVER_LETTER_SYSTEM, task_id)
            )
            input_tokens = provider.estimate_tokens(prompt + COVER_LETTER_SYSTEM)
            output_tokens = provider.estimate_tokens(full_text)
            model_used = provider.model
            provider_used = provider.name
        except Exception:
            response = asyncio.run(provider.generate(prompt, {"system": COVER_LETTER_SYSTEM}))
            full_text = response.text
            input_tokens = response.input_tokens
            output_tokens = response.output_tokens
            model_used = response.model
            provider_used = response.provider
            _publish_chunk(task_id, full_text, done=False)
            _publish_chunk(task_id, "", done=True)

        cover_letter = CoverLetter.objects.create(
            user_id=user_id,
            application_id=application_id,
            cv_version_id=cv_version_id,
            content=full_text,
            job_description=job_description,
            provider=provider_used,
            model=model_used,
            prompt_settings={
                "tone": tone,
                "length": length,
                "emphasis": emphasis,
            },
        )

        # Finalize the pre-reserved usage log row, or create one if no
        # reservation was made (e.g. internal/batch calls).
        if reservation_id:
            finalize_ai_reservation(
                reservation_id,
                provider_used,
                model_used,
                input_tokens,
                output_tokens,
            )
        else:
            AIUsageLog.objects.create(
                user_id=user_id,
                feature="cover_letter",
                provider=provider_used,
                model=model_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        return {"cover_letter_id": cover_letter.id, "content": full_text}

    except Exception as exc:
        # Release the reservation so the user gets their quota slot back
        if reservation_id:
            release_ai_reservation(reservation_id)
        logger.error(f"Cover letter generation failed: {exc}")
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=2)
def generate_qa_answer(
    self,
    user_id: int,
    question: str,
    cv_text: str,
    job_context: str = "",
    character_limit: int | None = None,
    provider_name: str = "gemini",
    model_name: str | None = None,
    reservation_id: int | None = None,
):
    from apps.billing.quotas import (
        finalize_ai_reservation,
        release_ai_reservation,
    )

    try:
        provider = get_llm_provider(provider_name, model_name)

        char_limit_text = (
            f"\n**Character limit:** {character_limit} characters" if character_limit else ""
        )

        prompt = QA_PROMPT.format(
            question=question,
            cv_text=cv_text,
            job_context=job_context or "Not provided",
            character_limit=char_limit_text,
        )

        response = asyncio.run(provider.generate(prompt, {"system": QA_SYSTEM}))

        if reservation_id:
            finalize_ai_reservation(
                reservation_id,
                response.provider,
                response.model,
                response.input_tokens,
                response.output_tokens,
            )
        else:
            AIUsageLog.objects.create(
                user_id=user_id,
                feature="qa",
                provider=response.provider,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )

        result = {"answer": response.text}
        AIGeneration.objects.create(
            user_id=user_id,
            feature="qa",
            title=question[:200],
            input={"question": question, "job_context": job_context},
            result=result,
            provider=response.provider,
            model=response.model,
        )
        return result

    except Exception as exc:
        if reservation_id:
            release_ai_reservation(reservation_id)
        logger.error(f"QA generation failed: {exc}")
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=2)
def compute_fit_score(
    self,
    user_id: int,
    cv_text: str,
    job_description: str,
    company: str = "",
    job_title: str = "",
    provider_name: str = "gemini",
    model_name: str | None = None,
):
    try:
        provider = get_llm_provider(provider_name, model_name)

        prompt = FIT_SCORE_PROMPT.format(
            job_title=job_title,
            company=company,
            job_description=job_description,
            cv_text=cv_text,
        )

        response = asyncio.run(provider.generate(prompt, {"system": FIT_SCORE_SYSTEM}))

        AIUsageLog.objects.create(
            user_id=user_id,
            feature="fit_score",
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )

        parsed = _extract_json(response.text)
        if parsed is None:
            # Couldn't get structured output — surface the raw text so the
            # user sees something useful instead of a hardcoded zero.
            result = {
                "score": 0,
                "strengths": [],
                "gaps": [],
                "recommendation": response.text,
            }
        else:
            result = parsed

        AIGeneration.objects.create(
            user_id=user_id,
            feature="fit_score",
            title=(f"{job_title} @ {company}" if job_title or company else "Fit score")[:200],
            input={"company": company, "job_title": job_title, "job_description": job_description},
            result=result,
            provider=response.provider,
            model=response.model,
        )
        return result

    except Exception as exc:
        logger.error(f"Fit score computation failed: {exc}")
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=2)
def compute_ats_score(
    self,
    user_id: int,
    cv_text: str,
    job_description: str,
    provider_name: str = "gemini",
    model_name: str | None = None,
    reservation_id: int | None = None,
):
    from apps.billing.quotas import (
        finalize_ai_reservation,
        release_ai_reservation,
    )

    try:
        provider = get_llm_provider(provider_name, model_name)

        prompt = ATS_SCORE_PROMPT.format(
            job_description=job_description,
            cv_text=cv_text,
        )

        response = asyncio.run(provider.generate(prompt, {"system": ATS_SCORE_SYSTEM}))

        if reservation_id:
            finalize_ai_reservation(
                reservation_id,
                response.provider,
                response.model,
                response.input_tokens,
                response.output_tokens,
            )
        else:
            AIUsageLog.objects.create(
                user_id=user_id,
                feature="ats_score",
                provider=response.provider,
                model=response.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
            )

        parsed = _extract_json(response.text)
        if parsed is None:
            result = {
                "score": 0,
                "matched_keywords": [],
                "missing_keywords": [],
                "suggestions": [response.text],  # surface the raw text at least
            }
        else:
            result = parsed

        AIGeneration.objects.create(
            user_id=user_id,
            feature="ats_score",
            title=(job_description[:120] + "…") if len(job_description) > 120 else job_description,
            input={"job_description": job_description},
            result=result,
            provider=response.provider,
            model=response.model,
        )
        return result

    except Exception as exc:
        if reservation_id:
            release_ai_reservation(reservation_id)
        logger.error(f"ATS score computation failed: {exc}")
        raise self.retry(exc=exc) from exc
