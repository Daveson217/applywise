"""Tests for the name-based ATS auto-probe."""

from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from apps.watchlist.models import WatchlistCompany
from apps.watchlist.probe import _slug_candidates, probe_by_name


class TestSlugCandidates:
    def test_simple_name(self):
        cands = _slug_candidates("Stripe")
        assert "stripe" in cands

    def test_strips_suffix(self):
        cands = _slug_candidates("Acme Technologies Inc")
        # Should have "acme" up front, not "acme-technologies-inc" first.
        assert cands[0] == "acme"

    def test_hyphenates_and_concatenates(self):
        cands = _slug_candidates("Palo Alto")
        assert "palo-alto" in cands
        assert "paloalto" in cands

    def test_empty_returns_empty(self):
        assert _slug_candidates("") == []
        assert _slug_candidates("   ") == []

    def test_dedupes(self):
        cands = _slug_candidates("Stripe Inc")
        assert len(cands) == len(set(cands))


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    # Default: an empty dict — for the default validator (status-code-only)
    # this is irrelevant. For SR's validator it's an explicit "no postings".
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


class TestProbeByName:
    def test_first_hit_wins(self):
        # Greenhouse returns 200 for "stripe" — should stop there.
        with patch("apps.watchlist.probe.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = client
            client.get.side_effect = [_mock_response(200)]  # first call is greenhouse
            result = probe_by_name("Stripe")
            assert result is not None
            assert result.provider == "greenhouse"
            assert result.slug == "stripe"
            assert "boards.greenhouse.io/stripe" in result.board_url

    def test_falls_through_to_next_provider(self):
        with patch("apps.watchlist.probe.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = client
            # greenhouse=404, lever=200 for first slug candidate
            client.get.side_effect = [_mock_response(404), _mock_response(200)]
            result = probe_by_name("Netflix")
            assert result is not None
            assert result.provider == "lever"

    def test_no_hits_returns_none(self):
        with patch("apps.watchlist.probe.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = client
            # All 404s across all providers + all candidates.
            client.get.return_value = _mock_response(404)
            assert probe_by_name("Some Random Company") is None

    def test_network_error_moves_on(self):
        import httpx

        with patch("apps.watchlist.probe.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = client
            # First raises, second returns 200 → still finds a match.
            client.get.side_effect = [
                httpx.TimeoutException("slow"),
                _mock_response(200),
            ]
            result = probe_by_name("Anthropic")
            assert result is not None

    def test_smartrecruiters_empty_response_rejected(self):
        """Regression: SR returns 200 with empty postings for invalid tenants.
        We must NOT treat that as a match."""
        with patch("apps.watchlist.probe.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = client
            # First 4 providers 404 → falls through to SR → SR returns 200
            # with a valid-shaped but empty body → must be rejected.
            client.get.side_effect = [
                _mock_response(404),  # greenhouse
                _mock_response(404),  # lever
                _mock_response(404),  # ashby
                _mock_response(404),  # workable
                _mock_response(200, {"totalFound": 0, "content": []}),  # SR empty
                # Same again for second slug candidate
                _mock_response(404),
                _mock_response(404),
                _mock_response(404),
                _mock_response(404),
                _mock_response(200, {"totalFound": 0, "content": []}),
            ]
            assert probe_by_name("Notion") is None

    def test_smartrecruiters_real_hit_accepted(self):
        """SR match with actual postings should still be accepted."""
        with patch("apps.watchlist.probe.httpx.Client") as mock_client_cls:
            client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = client
            client.get.side_effect = [
                _mock_response(404),  # greenhouse
                _mock_response(404),  # lever
                _mock_response(404),  # ashby
                _mock_response(404),  # workable
                _mock_response(
                    200,
                    {"totalFound": 12, "content": [{"id": "x", "name": "Y"}]},
                ),
            ]
            result = probe_by_name("Bosch")
            assert result is not None
            assert result.provider == "smartrecruiters"


@pytest.mark.django_db
class TestProbeEndpoint:
    URL = "/api/watchlist/probe/"

    def test_requires_auth(self, api_client):
        response = api_client.post(self.URL, {"name": "Stripe"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_name_returns_400(self, authenticated_client):
        response = authenticated_client.post(self.URL, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_hit_returns_detected(self, authenticated_client):
        with patch("apps.watchlist.probe.probe_by_name") as mock:
            from apps.watchlist.probe import ProbeResult

            mock.return_value = ProbeResult(
                provider="greenhouse",
                slug="stripe",
                board_url="https://boards.greenhouse.io/stripe",
            )
            response = authenticated_client.post(self.URL, {"name": "Stripe"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detected"] is True
        assert response.data["provider"] == "greenhouse"
        assert response.data["slug"] == "stripe"

    def test_miss_returns_not_detected(self, authenticated_client):
        with patch("apps.watchlist.probe.probe_by_name", return_value=None):
            response = authenticated_client.post(self.URL, {"name": "Nonesuch"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detected"] is False


@pytest.mark.django_db
class TestCreateWithProbeFallback:
    def test_create_probes_when_url_unmatched(self, authenticated_client, user):
        from apps.watchlist.probe import ProbeResult

        with patch("apps.watchlist.probe.probe_by_name") as mock:
            mock.return_value = ProbeResult(
                provider="greenhouse",
                slug="stripe",
                board_url="https://boards.greenhouse.io/stripe",
            )
            response = authenticated_client.post(
                "/api/watchlist/",
                {"name": "Stripe", "careers_url": "https://stripe.com/jobs"},
            )
        assert response.status_code == status.HTTP_201_CREATED
        # URL didn't match a known ATS → fell through to name probe.
        company = WatchlistCompany.objects.get(name="Stripe")
        assert company.ats_provider == "greenhouse"
        assert company.ats_company_slug == "stripe"

    def test_create_skips_probe_when_url_matches(self, authenticated_client, user):
        # URL alone tells us everything — probe should not be called.
        with patch("apps.watchlist.probe.probe_by_name") as mock:
            response = authenticated_client.post(
                "/api/watchlist/",
                {
                    "name": "Anthropic",
                    "careers_url": "https://boards.greenhouse.io/anthropic",
                },
            )
        assert response.status_code == status.HTTP_201_CREATED
        mock.assert_not_called()
        company = WatchlistCompany.objects.get(name="Anthropic")
        assert company.ats_provider == "greenhouse"
