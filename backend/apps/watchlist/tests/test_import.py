"""Tests for the watchlist CSV/XLSX import endpoint."""

import io
import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from apps.billing.models import Subscription
from apps.watchlist.models import WatchlistCompany

URL = "/api/watchlist/import/"


def _csv(*lines: str) -> SimpleUploadedFile:
    text = "\n".join(lines).encode("utf-8")
    return SimpleUploadedFile("companies.csv", text, content_type="text/csv")


@pytest.mark.django_db
class TestWatchlistImportPreview:
    def test_preview_returns_normalized_rows(self, authenticated_client):
        f = _csv(
            "name,careers_url",
            "Stripe,https://boards.greenhouse.io/stripe",
            "Anthropic,https://boards.greenhouse.io/anthropic",
        )
        response = authenticated_client.post(URL, {"file": f}, format="multipart")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["row_count"] == 2
        assert response.data["rows"][0]["name"] == "Stripe"
        assert "greenhouse.io" in response.data["rows"][0]["careers_url"]

    def test_preview_accepts_common_header_aliases(self, authenticated_client):
        f = _csv(
            "Company,Website",
            "Notion,https://notion.com/careers",
        )
        response = authenticated_client.post(URL, {"file": f}, format="multipart")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["rows"][0]["name"] == "Notion"
        assert response.data["rows"][0]["careers_url"] == "https://notion.com/careers"

    def test_preview_name_only_is_valid(self, authenticated_client):
        f = _csv("company", "Ramp", "Linear")
        response = authenticated_client.post(URL, {"file": f}, format="multipart")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["row_count"] == 2
        # Empty careers_url is fine
        assert response.data["rows"][0]["careers_url"] == ""

    def test_preview_skips_blank_name_rows(self, authenticated_client):
        f = _csv("name,careers_url", ",https://x.com", "Stripe,https://y.com", ",")
        response = authenticated_client.post(URL, {"file": f}, format="multipart")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["row_count"] == 1
        assert response.data["rows"][0]["name"] == "Stripe"

    def test_preview_no_valid_column_returns_400(self, authenticated_client):
        f = _csv("foo,bar", "baz,qux")
        response = authenticated_client.post(URL, {"file": f}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detected_headers" in response.data

    def test_preview_no_file_returns_400(self, authenticated_client):
        response = authenticated_client.post(URL, {}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_preview_bom_stripped(self, authenticated_client):
        # Excel-saved CSVs start with a UTF-8 BOM. Make sure we tolerate it.
        raw = "﻿name,careers_url\nStripe,https://x.com".encode()
        f = SimpleUploadedFile("companies.csv", raw, content_type="text/csv")
        response = authenticated_client.post(URL, {"file": f}, format="multipart")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["rows"][0]["name"] == "Stripe"

    def test_preview_non_utf8_returns_400(self, authenticated_client):
        # Windows-1252 with non-ASCII byte
        raw = b"name,careers_url\n\xe9foo,https://x.com"
        f = SimpleUploadedFile("companies.csv", raw, content_type="text/csv")
        response = authenticated_client.post(URL, {"file": f}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestWatchlistImportCommit:
    def _preview_and_commit(self, client, rows):
        return client.post(
            URL,
            {"commit": "true", "rows": json.dumps(rows)},
            format="multipart",
        )

    def test_commit_creates_rows(self, authenticated_client):
        Subscription.objects.create(
            user=authenticated_client.handler._force_user, plan="pro", status="active"
        )
        response = self._preview_and_commit(
            authenticated_client,
            [
                {"name": "Stripe", "careers_url": "https://boards.greenhouse.io/stripe"},
                {"name": "Anthropic", "careers_url": ""},
            ],
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["created"] == 2

        stripe = WatchlistCompany.objects.get(name="Stripe")
        assert stripe.ats_provider == "greenhouse"
        assert stripe.ats_company_slug == "stripe"

    def test_commit_skips_case_insensitive_duplicates(self, authenticated_client, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        WatchlistCompany.objects.create(user=user, name="Stripe")

        response = self._preview_and_commit(
            authenticated_client,
            [
                {"name": "stripe", "careers_url": ""},
                {"name": "STRIPE", "careers_url": ""},
                {"name": "Notion", "careers_url": ""},
            ],
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["created"] == 1
        assert response.data["skipped_duplicates"] == 2

    def test_commit_enforces_free_tier_quota(self, authenticated_client, user):
        # Free tier limit is 5 watchlist companies
        for i in range(3):
            WatchlistCompany.objects.create(user=user, name=f"Existing{i}")

        response = self._preview_and_commit(
            authenticated_client,
            [{"name": f"New{i}", "careers_url": ""} for i in range(5)],
        )
        assert response.status_code == status.HTTP_200_OK
        # Only 2 slots left → creates 2, skips 3
        assert response.data["created"] == 2
        assert response.data.get("skipped_over_limit", 0) > 0
        assert "message" in response.data

    def test_commit_row_cap(self, authenticated_client):
        big = [{"name": f"C{i}"} for i in range(501)]
        response = self._preview_and_commit(authenticated_client, big)
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    def test_commit_invalid_json_rejected(self, authenticated_client):
        response = authenticated_client.post(
            URL,
            {"commit": "true", "rows": "not-json"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_commit_ignores_non_dict_items(self, authenticated_client, user):
        Subscription.objects.create(user=user, plan="pro", status="active")
        response = self._preview_and_commit(
            authenticated_client,
            ["not-a-dict", 42, {"name": "OK"}, None],
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["created"] == 1

    def test_unauthenticated_rejected(self, api_client):
        response = api_client.post(
            URL,
            {"commit": "true", "rows": "[]"},
            format="multipart",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
