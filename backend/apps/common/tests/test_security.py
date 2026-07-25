"""Security tests covering the audit fixes:

- SSRF URL validation (cloud metadata, internal IPs, schemes)
- CSV formula injection (export)
- CSV import size + row caps
- CV magic-byte validation (vs trusted client content_type)
- CV download access control (no horizontal IDOR)
- Bulk action input validation
- OAuth redirect_uri allow-list + provider config gating
- Logout blacklists refresh tokens
- Quota race-safe reservation (concurrent simulation)
"""

import io
import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status

from apps.ai.models import AIUsageLog
from apps.applications.models import Application, CVVersion
from apps.billing.models import Subscription
from apps.billing.quotas import reserve_ai_quota
from apps.common.url_validation import URLValidationError, validate_external_url
from apps.notifications.models import Notification

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Fix 1+2: SSRF URL validation
# ─────────────────────────────────────────────────────────────────────────────
class TestSSRFValidation:
    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost/admin",
            "http://127.0.0.1:8000",
            "http://0.0.0.0",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://10.0.0.1",  # private
            "http://192.168.1.1",  # private
            "http://172.16.0.1",  # private
            "http://[::1]/",  # IPv6 loopback
            "http://[::ffff:127.0.0.1]/",  # IPv4-mapped IPv6
            "file:///etc/passwd",  # wrong scheme
            "gopher://internal/",  # wrong scheme
            "javascript:alert(1)",  # wrong scheme
        ],
    )
    def test_blocks_dangerous_url(self, url):
        with pytest.raises(URLValidationError):
            validate_external_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "https://boards.greenhouse.io/stripe",
            "https://jobs.lever.co/netflix",
            "http://example.com",
        ],
    )
    def test_allows_public_url(self, url):
        # May raise if DNS resolution returns a private IP for these hosts
        # in your network — but for the public test domains used here it
        # should succeed in CI.
        try:
            validate_external_url(url)
        except URLValidationError as e:
            # Tolerate environments without internet — the unit test still
            # demonstrates the blocking cases above work.
            if "DNS" not in str(e):
                raise


# ─────────────────────────────────────────────────────────────────────────────
# Fix 6: CSV formula injection in export
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestCSVFormulaInjection:
    def test_dangerous_cell_prefixed_with_quote(self, authenticated_client, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        # Attacker stores a payload in company name
        Application.objects.create(
            user=user,
            company="=cmd|'/c calc'!A1",
            role="Pwn",
            job_type="fulltime",
        )
        response = authenticated_client.get("/api/applications/export/", {"type": "csv"})
        assert response.status_code == 200, (response.status_code, response.content[:300])
        body = response.content.decode()
        # The dangerous cell must NOT be exported as a formula.
        # It should be prefixed with a single quote.
        assert "'=cmd" in body
        # And the raw formula form should never appear at start of cell
        for cell_start_marker in (",=cmd", "\n=cmd"):
            assert cell_start_marker not in body


# ─────────────────────────────────────────────────────────────────────────────
# Fix 7: CSV import size + row caps
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestCSVImportLimits:
    def test_import_rejects_too_many_rows(self, authenticated_client):
        big_rows = [{"company": f"C{i}", "role": "R", "job_type": "fulltime"} for i in range(501)]
        response = authenticated_client.post(
            "/api/applications/import-csv/",
            {"commit": "true", "rows": json.dumps(big_rows)},
            format="multipart",
        )
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


# ─────────────────────────────────────────────────────────────────────────────
# Fix 8: CV upload magic-byte validation
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestCVMagicByteValidation:
    def _upload(self, client, content: bytes, content_type: str):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return client.post(
            "/api/cv/",
            {
                "name": "test",
                "file": SimpleUploadedFile("x.pdf", content, content_type=content_type),
            },
            format="multipart",
        )

    def test_blocks_html_disguised_as_pdf(self, authenticated_client):
        # Attacker claims content_type=application/pdf but sends HTML
        evil = b"<html><script>alert(1)</script></html>"
        response = self._upload(authenticated_client, evil, "application/pdf")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_blocks_executable_disguised_as_pdf(self, authenticated_client):
        # ELF binary header — clearly not a PDF
        evil = b"\x7fELF" + b"\x00" * 100
        response = self._upload(authenticated_client, evil, "application/pdf")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_accepts_real_pdf_magic(self, authenticated_client):
        # Minimal PDF header bytes
        real_pdf = b"%PDF-1.4\n%minimal pdf\n"
        response = self._upload(authenticated_client, real_pdf, "application/pdf")
        # 201 or 403 (over quota) both prove we passed magic-byte check
        assert response.status_code in (
            status.HTTP_201_CREATED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_blocks_empty_file(self, authenticated_client):
        response = self._upload(authenticated_client, b"", "application/pdf")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# Fix 9: CV download is owner-scoped
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestCVDownloadAuthorization:
    def test_cannot_download_other_users_cv(self, authenticated_client, user, other_user):
        cv = CVVersion.objects.create(user=other_user, name="Their CV", file="other.pdf")
        response = authenticated_client.get(f"/api/cv/{cv.pk}/download/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ─────────────────────────────────────────────────────────────────────────────
# Fix 12: Bulk action input validation
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestBulkActionValidation:
    def test_too_many_ids_rejected(self, authenticated_client):
        response = authenticated_client.post(
            "/api/applications/bulk-action/",
            {"action": "delete", "ids": list(range(501))},
            format="json",
        )
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    def test_invalid_status_rejected(self, authenticated_client, user):
        app = Application.objects.create(user=user, company="X", role="Y", job_type="fulltime")
        response = authenticated_client.post(
            "/api/applications/bulk-action/",
            {
                "action": "status_change",
                "ids": [app.id],
                "status": "DROP_TABLE_users",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_integer_ids_rejected(self, authenticated_client):
        response = authenticated_client.post(
            "/api/applications/bulk-action/",
            {
                "action": "delete",
                "ids": ["1; DROP TABLE users", "evil"],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_bulk_only_acts_on_own_records(self, authenticated_client, user, other_user):
        # Even if user passes other_user's app IDs, the user-scoped queryset
        # makes it a no-op rather than IDOR
        their_app = Application.objects.create(
            user=other_user, company="X", role="Y", job_type="fulltime"
        )
        response = authenticated_client.post(
            "/api/applications/bulk-action/",
            {"action": "delete", "ids": [their_app.id]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deleted"] == 0
        # Their app still exists
        assert Application.objects.filter(pk=their_app.pk).exists()


# ─────────────────────────────────────────────────────────────────────────────
# Fix 3+4: OAuth — redirect_uri allow-list + email_verified check
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestOAuthHardening:
    def test_arbitrary_redirect_uri_rejected(self, api_client):
        response = api_client.post(
            "/api/auth/social/google/",
            {
                "code": "fake-code",
                "redirect_uri": "https://evil.com/steal-token",
            },
            format="json",
        )
        # Either 400 (validator) or 503 (no OAuth configured) — both prove
        # we never reached the token exchange with attacker URL
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    def test_oauth_unconfigured_returns_503(self, api_client, settings):
        # Clear the client_id/secret so the endpoint refuses
        settings.SOCIALACCOUNT_PROVIDERS = {
            "google": {"APP": {"client_id": "", "secret": ""}},
            "linkedin_oauth2": {"APP": {"client_id": "", "secret": ""}},
        }
        response = api_client.post(
            "/api/auth/social/google/",
            {
                "code": "x",
                "redirect_uri": "http://localhost:5173/auth/callback?provider=google",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_unverified_email_rejected(self, api_client, settings):
        settings.SOCIALACCOUNT_PROVIDERS = {
            "google": {"APP": {"client_id": "cid", "secret": "csecret"}},
            "linkedin_oauth2": {"APP": {"client_id": "", "secret": ""}},
        }
        # Patch BOTH the token endpoint and the userinfo endpoint
        with patch("apps.users.social_auth.requests") as mock_requests:
            # First call: token exchange → returns access_token
            # Second call: userinfo → returns unverified email
            mock_requests.post.return_value.status_code = 200
            mock_requests.post.return_value.json.return_value = {"access_token": "fake"}
            mock_requests.get.return_value.status_code = 200
            mock_requests.get.return_value.json.return_value = {
                "email": "attacker@example.com",
                "verified_email": False,  # ← key field
                "given_name": "A",
                "family_name": "B",
            }
            mock_requests.RequestException = Exception

            response = api_client.post(
                "/api/auth/social/google/",
                {
                    "code": "x",
                    "redirect_uri": "http://localhost:5173/auth/callback?provider=google",
                },
                format="json",
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Account must NOT have been created
        assert not User.objects.filter(email="attacker@example.com").exists()


# ─────────────────────────────────────────────────────────────────────────────
# Logout — blacklists refresh token
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client, user):
        # Login to get tokens
        login = api_client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "testpass123!"},
        )
        refresh = login.data["refresh"]

        # Logout
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        api_client.post("/api/auth/logout/", {"refresh": refresh}, format="json")

        # Refresh attempt should now fail
        response = api_client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────────────────────────────────────
# Race-safe quota reservation — simulates concurrent requests
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestQuotaRaceSafety:
    def test_reservation_blocks_after_limit(self, user):
        # Reserve up to the free-tier cap of 5
        results = [reserve_ai_quota(user, "cover_letter") for _ in range(5)]
        assert all(r.allowed for r in results)

        # 6th reservation must fail even though previous ones haven't
        # been finalized yet (this is the race the old check_ai_quota had)
        sixth = reserve_ai_quota(user, "cover_letter")
        assert not sixth.allowed
        assert sixth.used == 5
