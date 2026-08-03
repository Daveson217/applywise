"""End-to-end tests for the watchlist match → notification → email chain."""

from unittest.mock import patch

import pytest

from apps.notifications.email import render_template, send_job_alert
from apps.notifications.models import Notification
from apps.watchlist.models import JobPosting, WatchlistCompany, WatchlistRule
from apps.watchlist.tasks import _check_rules


@pytest.mark.django_db
class TestWatchlistFlagsMatches:
    """_check_rules flags matches (matched_rules) for the feed; it no longer
    emails per job — the digest task batches emails separately."""

    def test_matched_rule_flags_posting(self, user):
        company = WatchlistCompany.objects.create(
            user=user, name="Stripe", ats_provider="greenhouse"
        )
        WatchlistRule.objects.create(
            company=company,
            keywords=["intern"],
            locations=[],
            is_active=True,
        )
        posting = JobPosting.objects.create(
            company=company,
            external_id="123",
            title="Software Engineer Intern",
            url="https://example.com/job/123",
            location="Remote",
        )

        # No per-job email should be enqueued anymore.
        with patch("apps.notifications.tasks.send_notification_email.delay") as mock_send:
            _check_rules(posting, company)

        posting.refresh_from_db()
        assert posting.matched_rules is True
        assert posting.matched_at is not None
        # No Notification and no email at match time (digest handles it).
        assert Notification.objects.filter(user=user).count() == 0
        mock_send.assert_not_called()

    def test_unmatched_rule_flags_nothing(self, user):
        company = WatchlistCompany.objects.create(
            user=user, name="Stripe", ats_provider="greenhouse"
        )
        WatchlistRule.objects.create(
            company=company,
            keywords=["senior"],
            locations=[],
            is_active=True,
        )
        posting = JobPosting.objects.create(
            company=company,
            external_id="123",
            title="Junior Developer",
            url="https://example.com/job/123",
        )

        _check_rules(posting, company)

        posting.refresh_from_db()
        assert posting.matched_rules is False
        assert Notification.objects.filter(user=user).count() == 0

    def test_no_rules_no_profile_flags_nothing(self, user):
        company = WatchlistCompany.objects.create(
            user=user, name="Stripe", ats_provider="greenhouse"
        )
        posting = JobPosting.objects.create(
            company=company,
            external_id="123",
            title="Software Engineer Intern",
            url="https://example.com/job/123",
        )

        _check_rules(posting, company)

        posting.refresh_from_db()
        assert posting.matched_rules is False

    def test_matches_once_across_multiple_rules(self, user):
        company = WatchlistCompany.objects.create(
            user=user, name="Stripe", ats_provider="greenhouse"
        )
        WatchlistRule.objects.create(company=company, keywords=["intern"], is_active=True)
        WatchlistRule.objects.create(company=company, keywords=["engineer"], is_active=True)
        posting = JobPosting.objects.create(
            company=company,
            external_id="123",
            title="Software Engineer Intern",
            url="https://example.com/job/123",
        )

        _check_rules(posting, company)

        posting.refresh_from_db()
        assert posting.matched_rules is True


@pytest.mark.django_db
class TestNotificationSignal:
    def test_notification_create_enqueues_email(self, user, django_capture_on_commit_callbacks):
        with patch("apps.notifications.tasks.send_notification_email.delay") as mock_send:
            with django_capture_on_commit_callbacks(execute=True):
                notif = Notification.objects.create(
                    user=user,
                    type="system",
                    title="Welcome",
                    body="Welcome to Applywise!",
                )

        mock_send.assert_called_once_with(notif.id)

    def test_notification_update_does_not_fire(self, user):
        notif = Notification.objects.create(user=user, type="system", title="Hi", body="Body")

        with patch("apps.notifications.tasks.send_notification_email.delay") as mock_send:
            notif.is_read = True
            notif.save()

        mock_send.assert_not_called()


class TestEmailTemplating:
    def test_render_template_substitutes_vars(self):
        result = render_template(
            "Hello {{name}}, welcome to {{app}}!",
            {"name": "John", "app": "Applywise"},
        )
        assert result == "Hello John, welcome to Applywise!"

    def test_render_template_ignores_unknown_vars(self):
        result = render_template("Hi {{name}}", {"other": "x"})
        assert "{{name}}" in result  # leaves unsubstituted

    def test_render_template_empty_context(self):
        assert render_template("Static text", {}) == "Static text"


@pytest.mark.django_db
class TestSendJobAlert:
    def test_send_job_alert_calls_email_send(self, user):
        company = WatchlistCompany.objects.create(
            user=user, name="Stripe", ats_provider="greenhouse"
        )
        posting = JobPosting.objects.create(
            company=company,
            external_id="123",
            title="SWE Intern",
            url="https://stripe.com/jobs/123",
            location="SF",
        )

        with patch("apps.notifications.email.send_email") as mock_send:
            mock_send.return_value = True
            result = send_job_alert(user, posting)

        assert result is True
        mock_send.assert_called_once()
        # Verify the email contents include the key fields
        call_args = mock_send.call_args
        assert call_args[0][0] == user.email
        assert "Stripe" in call_args[0][1]  # subject
        assert "SWE Intern" in call_args[0][1]
