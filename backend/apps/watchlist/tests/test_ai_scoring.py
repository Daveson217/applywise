"""Tests for the AI relevance scoring gate."""

from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.notifications.models import Notification
from apps.watchlist.ai_scoring import _parse_score, should_score
from apps.watchlist.models import JobPosting, WatchlistCompany, WatchlistRule
from apps.watchlist.tasks import _check_rules


class TestParseScore:
    def test_bare_json(self):
        assert _parse_score('{"score": 0.85}') == 0.85

    def test_wrapped_in_code_fence(self):
        assert _parse_score('```json\n{"score": 0.7}\n```') == 0.7

    def test_clamps_above_one(self):
        assert _parse_score('{"score": 1.5}') == 1.0

    def test_clamps_negative(self):
        assert _parse_score('{"score": -0.2}') == 0.0

    def test_missing_key_returns_none(self):
        assert _parse_score('{"other": 1}') is None

    def test_malformed_returns_none(self):
        assert _parse_score("not json at all") is None

    def test_int_score(self):
        assert _parse_score('{"score": 1}') == 1.0


@pytest.mark.django_db
class TestShouldScore:
    def test_disabled_by_default(self, user):
        assert should_score(user) is False

    def test_enabled_when_payments_off_and_opted_in(self, user):
        user.profile.ai_relevance_enabled = True
        user.profile.save()
        with override_settings(PAYMENTS_ENABLED=False):
            assert should_score(user) is True

    def test_disabled_when_payments_on_and_free_plan(self, user):
        user.profile.ai_relevance_enabled = True
        user.profile.save()
        with override_settings(PAYMENTS_ENABLED=True):
            assert should_score(user) is False


@pytest.mark.django_db
class TestAIScoringGate:
    def _setup(self, user, *, score_value):
        user.profile.ai_relevance_enabled = True
        user.profile.target_roles = ["ml"]
        user.profile.save()
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        WatchlistRule.objects.create(company=company, keywords=["ml"])
        posting = JobPosting.objects.create(
            company=company,
            external_id="ext-1",
            title="ML Engineer",
            url="https://example.com/job/1",
            location="Remote",
            description_text="Work on models.",
        )
        return company, posting

    @override_settings(PAYMENTS_ENABLED=False)
    def test_high_score_fires_notification(self, user):
        company, posting = self._setup(user, score_value=0.9)
        with patch("apps.watchlist.ai_scoring.score_posting", return_value=0.9):
            _check_rules(posting, company)
        assert Notification.objects.filter(user=user).count() == 1
        posting.refresh_from_db()
        assert posting.ai_relevance_score == 0.9

    @override_settings(PAYMENTS_ENABLED=False)
    def test_low_score_skips_notification(self, user):
        company, posting = self._setup(user, score_value=0.3)
        with patch("apps.watchlist.ai_scoring.score_posting", return_value=0.3):
            _check_rules(posting, company)
        # Below threshold → no notification, but score IS cached.
        assert Notification.objects.filter(user=user).count() == 0
        posting.refresh_from_db()
        assert posting.ai_relevance_score == 0.3

    @override_settings(PAYMENTS_ENABLED=False)
    def test_scorer_error_fails_open(self, user):
        """LLM outage returns None → we still notify (tier-2 already passed)."""
        company, posting = self._setup(user, score_value=None)
        with patch("apps.watchlist.ai_scoring.score_posting", return_value=None):
            _check_rules(posting, company)
        assert Notification.objects.filter(user=user).count() == 1

    @override_settings(PAYMENTS_ENABLED=False)
    def test_scorer_not_called_when_opted_out(self, user):
        # Default profile: ai_relevance_enabled=False
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        WatchlistRule.objects.create(company=company, keywords=["ml"])
        posting = JobPosting.objects.create(
            company=company,
            external_id="ext-2",
            title="ML Engineer",
            url="https://example.com/job/2",
            location="Remote",
        )
        with patch("apps.watchlist.ai_scoring.score_posting") as mock_score:
            _check_rules(posting, company)
        mock_score.assert_not_called()
        assert Notification.objects.filter(user=user).count() == 1
