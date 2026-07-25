import json

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import CVVersion
from apps.billing.quotas import (
    check_provider_allowed,
    reserve_ai_quota,
)
from llm_providers.registry import PROVIDER_INFO

from .models import AIUsageLog, CoverLetter
from .serializers import (
    ATSScoreRequestSerializer,
    CoverLetterRequestSerializer,
    CoverLetterSerializer,
    FitScoreRequestSerializer,
    QARequestSerializer,
)
from .tasks import (
    compute_ats_score,
    compute_fit_score,
    generate_cover_letter,
    generate_qa_answer,
)

# ─── SSE stream auth ─────────────────────────────────────────────────────
# EventSource can't send Authorization headers, so the SSE endpoint can't
# use normal JWT auth. Instead the POST that creates a task returns a
# signed stream_token. The SSE endpoint requires the token in its URL,
# verifies the signature, and confirms it was issued for THIS task_id.
# Tokens expire after 5 minutes — long enough for the slowest LLM, short
# enough to limit damage if leaked in a log.
_STREAM_SIGNER = TimestampSigner(salt="cover-letter-stream-v1")
_STREAM_TOKEN_TTL_SECONDS = 300


def _make_stream_token(user_id: int, task_id: str) -> str:
    return _STREAM_SIGNER.sign(f"{user_id}:{task_id}")


def _verify_stream_token(token: str, task_id: str) -> int | None:
    """Returns user_id on success; None if signature/expiry/task mismatch."""
    try:
        value = _STREAM_SIGNER.unsign(token, max_age=_STREAM_TOKEN_TTL_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    try:
        user_id_str, signed_task_id = value.split(":", 1)
        if signed_task_id != task_id:
            return None
        return int(user_id_str)
    except (ValueError, AttributeError):
        return None


def _quota_error(quota_result) -> Response:
    """Standard 403 response for any quota violation."""
    return Response(
        {
            "error": quota_result.reason,
            "limit": quota_result.limit,
            "used": quota_result.used,
            "plan": quota_result.plan,
            "upgrade_url": "/pricing",
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _resolve_provider_model(request, data):
    """Pull provider/model from request, falling back to user defaults."""
    provider_name = data.get("provider") or request.user.profile.default_llm_provider
    model_name = data.get("model") or request.user.profile.default_llm_model
    return provider_name, model_name


class ProvidersView(APIView):
    def get(self, request):
        return Response(PROVIDER_INFO)


class CoverLetterView(APIView):
    def post(self, request):
        serializer = CoverLetterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            cv = CVVersion.objects.get(pk=data["cv_version_id"], user=request.user)
        except CVVersion.DoesNotExist:
            return Response(
                {"error": "CV version not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        provider_name, model_name = _resolve_provider_model(request, data)

        # Provider gating (cheap check first — no DB lock needed)
        provider_check = check_provider_allowed(request.user, provider_name, model_name)
        if not provider_check.allowed:
            return _quota_error(provider_check)

        # Atomic reserve — race-safe quota enforcement
        quota = reserve_ai_quota(request.user, "cover_letter")
        if not quota.allowed:
            return _quota_error(quota)

        task = generate_cover_letter.delay(
            user_id=request.user.id,
            cv_text=cv.extracted_text,
            job_description=data.get("job_description", ""),
            company=data["company"],
            job_title=data["job_title"],
            tone=data.get("tone", "formal"),
            length=data.get("length", "standard"),
            emphasis=data.get("emphasis", "skills"),
            notes=data.get("notes", ""),
            provider_name=provider_name,
            model_name=model_name,
            application_id=data.get("application_id"),
            cv_version_id=cv.id,
            reservation_id=getattr(quota, "reservation_id", None),
        )

        return Response(
            {
                "task_id": task.id,
                "status": "queued",
                "quota_remaining": quota.remaining,
                # Token for the SSE stream — never share, expires in 5 min
                "stream_token": _make_stream_token(request.user.id, task.id),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class CoverLetterListView(generics.ListAPIView):
    serializer_class = CoverLetterSerializer

    def get_queryset(self):
        return CoverLetter.objects.filter(user=self.request.user)


class QAView(APIView):
    def post(self, request):
        serializer = QARequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            cv = CVVersion.objects.get(pk=data["cv_version_id"], user=request.user)
        except CVVersion.DoesNotExist:
            return Response(
                {"error": "CV version not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        provider_name, model_name = _resolve_provider_model(request, data)

        provider_check = check_provider_allowed(request.user, provider_name, model_name)
        if not provider_check.allowed:
            return _quota_error(provider_check)

        quota = reserve_ai_quota(request.user, "qa")
        if not quota.allowed:
            return _quota_error(quota)

        task = generate_qa_answer.delay(
            user_id=request.user.id,
            question=data["question"],
            cv_text=cv.extracted_text,
            job_context=data.get("job_context", ""),
            character_limit=data.get("character_limit"),
            provider_name=provider_name,
            model_name=model_name,
            reservation_id=getattr(quota, "reservation_id", None),
        )

        return Response(
            {
                "task_id": task.id,
                "status": "queued",
                "quota_remaining": quota.remaining,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class FitScoreView(APIView):
    def post(self, request):
        serializer = FitScoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            cv = CVVersion.objects.get(pk=data["cv_version_id"], user=request.user)
        except CVVersion.DoesNotExist:
            return Response(
                {"error": "CV version not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        provider_name, model_name = _resolve_provider_model(request, data)

        # Fit score has no monthly cap per spec — only provider gating
        provider_check = check_provider_allowed(request.user, provider_name, model_name)
        if not provider_check.allowed:
            return _quota_error(provider_check)

        task = compute_fit_score.delay(
            user_id=request.user.id,
            cv_text=cv.extracted_text,
            job_description=data.get("job_description", ""),
            company=data.get("company", ""),
            job_title=data.get("job_title", ""),
            provider_name=provider_name,
            model_name=model_name,
        )

        return Response(
            {"task_id": task.id, "status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )


class ATSScoreView(APIView):
    def post(self, request):
        serializer = ATSScoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            cv = CVVersion.objects.get(pk=data["cv_version_id"], user=request.user)
        except CVVersion.DoesNotExist:
            return Response(
                {"error": "CV version not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        provider_name, model_name = _resolve_provider_model(request, data)

        provider_check = check_provider_allowed(request.user, provider_name, model_name)
        if not provider_check.allowed:
            return _quota_error(provider_check)

        quota = reserve_ai_quota(request.user, "ats_score")
        if not quota.allowed:
            return _quota_error(quota)

        task = compute_ats_score.delay(
            user_id=request.user.id,
            cv_text=cv.extracted_text,
            job_description=data["job_description"],
            provider_name=provider_name,
            model_name=model_name,
            reservation_id=getattr(quota, "reservation_id", None),
        )

        return Response(
            {
                "task_id": task.id,
                "status": "queued",
                "quota_remaining": quota.remaining,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class AIUsageView(APIView):
    def get(self, request):
        usage = (
            AIUsageLog.objects.filter(user=request.user)
            .values("feature")
            .annotate(
                total_input=Sum("input_tokens"),
                total_output=Sum("output_tokens"),
                count=Sum("id"),
            )
        )

        monthly = (
            AIUsageLog.objects.filter(user=request.user)
            .annotate(month=TruncMonth("timestamp"))
            .values("month")
            .annotate(
                total_input=Sum("input_tokens"),
                total_output=Sum("output_tokens"),
            )
            .order_by("-month")[:6]
        )

        return Response(
            {
                "by_feature": list(usage),
                "by_month": list(monthly),
            }
        )


class CoverLetterStreamView(APIView):
    """SSE endpoint streaming cover letter generation token-by-token.

    AUTH: Requires `?token=...` query param containing a signed token issued
    by CoverLetterView. The token binds the user_id to the task_id and
    expires after 5 minutes. EventSource can't send Authorization headers,
    so this token-in-URL is the standard pattern.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # auth is via stream_token instead

    # Hard maximum stream lifetime — even if Redis hangs we won't keep a
    # connection open forever
    MAX_STREAM_DURATION_SECONDS = 300

    def get(self, request, task_id):
        token = request.query_params.get("token", "")
        if not token:
            return Response(
                {"error": "Missing stream token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user_id = _verify_stream_token(token, task_id)
        if user_id is None:
            return Response(
                {"error": "Invalid or expired stream token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        def event_stream():
            import time

            import redis
            from django.conf import settings

            r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            pubsub = r.pubsub()
            channel = f"cover_letter:{task_id}"
            pubsub.subscribe(channel)

            started = time.time()
            try:
                yield "event: connected\ndata: {}\n\n"

                # Use a polling get_message loop with a timeout so we can
                # enforce MAX_STREAM_DURATION_SECONDS
                while True:
                    if time.time() - started > self.MAX_STREAM_DURATION_SECONDS:
                        yield 'event: timeout\ndata: {"error":"stream timeout"}\n\n'
                        break

                    message = pubsub.get_message(timeout=1.0)
                    if message is None:
                        continue
                    if message["type"] != "message":
                        continue
                    try:
                        payload = json.loads(message["data"])
                    except (json.JSONDecodeError, TypeError):
                        continue

                    yield f"data: {json.dumps(payload)}\n\n"

                    if payload.get("done"):
                        break
            finally:
                pubsub.unsubscribe(channel)
                pubsub.close()

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
