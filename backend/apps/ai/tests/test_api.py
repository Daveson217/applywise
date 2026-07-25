import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.ai.models import AIUsageLog, CoverLetter
from apps.applications.models import CVVersion

User = get_user_model()

PROVIDERS_URL = "/api/ai/providers/"
COVER_LETTER_URL = "/api/ai/cover-letter/"
COVER_LETTERS_URL = "/api/ai/cover-letters/"
QA_URL = "/api/ai/question-answer/"
FIT_URL = "/api/ai/fit-score/"
ATS_URL = "/api/ai/ats-score/"
USAGE_URL = "/api/ai/usage/"


@pytest.mark.django_db
class TestAIProviders:
    def test_list_providers(self, authenticated_client):
        response = authenticated_client.get(PROVIDERS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        names = [p["name"] for p in response.data]
        assert "gemini" in names
        assert "openai" in names
        assert "anthropic" in names

    def test_providers_have_models(self, authenticated_client):
        response = authenticated_client.get(PROVIDERS_URL)
        for provider in response.data:
            assert len(provider["models"]) >= 1

    def test_unauthenticated(self, api_client):
        response = api_client.get(PROVIDERS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCoverLetterEndpoint:
    def test_requires_cv_version(self, authenticated_client):
        data = {
            "job_description": "Build software",
            "cv_version_id": 99999,
            "company": "Google",
            "job_title": "SWE",
        }
        response = authenticated_client.post(COVER_LETTER_URL, data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_job_desc_or_url(self, authenticated_client, user):
        cv = CVVersion.objects.create(
            user=user, name="Test CV", file="test.pdf", extracted_text="Skills: Python"
        )
        data = {
            "cv_version_id": cv.id,
            "company": "Google",
            "job_title": "SWE",
        }
        response = authenticated_client.post(COVER_LETTER_URL, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_cover_letters(self, authenticated_client, user):
        cv = CVVersion.objects.create(
            user=user, name="CV", file="t.pdf", extracted_text="test"
        )
        CoverLetter.objects.create(
            user=user,
            cv_version=cv,
            content="Dear Hiring Manager...",
            provider="gemini",
            model="gemini-2.5-flash",
        )
        response = authenticated_client.get(COVER_LETTERS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestQAEndpoint:
    def test_requires_fields(self, authenticated_client):
        response = authenticated_client.post(QA_URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestScoringEndpoints:
    def test_fit_score_requires_fields(self, authenticated_client):
        response = authenticated_client.post(FIT_URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ats_score_requires_fields(self, authenticated_client):
        response = authenticated_client.post(ATS_URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAIUsage:
    def test_usage_empty(self, authenticated_client):
        response = authenticated_client.get(USAGE_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "by_feature" in response.data
        assert "by_month" in response.data

    def test_usage_with_logs(self, authenticated_client, user):
        AIUsageLog.objects.create(
            user=user,
            feature="cover_letter",
            provider="gemini",
            model="gemini-2.5-flash",
            input_tokens=500,
            output_tokens=300,
        )
        response = authenticated_client.get(USAGE_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["by_feature"]) >= 1
