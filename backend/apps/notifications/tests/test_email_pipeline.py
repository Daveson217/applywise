"""End-to-end tests for the watchlist match → notification → email chain."""

from unittest.mock import patch

import pytest

from apps.notifications.email import render_template, send_job_alert
from apps.notifications.models import Notification
from apps.watchlist.models import JobPosting, WatchlistCompany, WatchlistRule
from apps.watchlist.tasks import _check_rules


@pytest.mark.django_db
class TestWatchlistTriggersNotification:
    def test_matched_rule_creates_notification(
        self, user, django_capture_on_commit_callbacks
    ):
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

        with patch(
            "apps.notifications.tasks.send_notification_email.delay"
        ) as mock_send:
            # Capture and execute on_commit callbacks so we can assert they ran
            with django_capture_on_commit_callbacks(execute=True):
                _check_rules(posting, company)

        notif = Notification.objects.filter(user=user, type="job_alert").first()
        assert notif is not None
        assert "Stripe" in notif.title
        assert "Software Engineer Intern" in notif.title
        # Posting ID now lives in structured metadata, not free-text body
        assert notif.metadata.get("posting_id") == posting.id
        # Signal fires the email task post-commit
        mock_send.assert_called_once_with(notif.id)

    def test_unmatched_rule_creates_nothing(self, user):
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

        with patch(
            "apps.notifications.tasks.send_notification_email.delay"
        ) as mock_send:
            _check_rules(posting, company)

        assert Notification.objects.filter(user=user).count() == 0
        mock_send.assert_not_called()

    def test_no_rules_skips_notification(self, user):
        company = WatchlistCompany.objects.create(
            user=user, name="Stripe", ats_provider="greenhouse"
        )
        posting = JobPosting.objects.create(
            company=company,
            external_id="123",
            title="Software Engineer Intern",
            url="https://example.com/job/123",
        )

        with patch(
            "apps.notifications.tasks.send_notification_email.delay"
        ) as mock_send:
            _check_rules(posting, company)

        assert Notification.objects.filter(user=user).count() == 0
        mock_send.assert_not_called()

    def test_only_first_matching_rule_fires(self, user):
        company = WatchlistCompany.objects.create(
            user=user, name="Stripe", ats_provider="greenhouse"
        )
        WatchlistRule.objects.create(
            company=company, keywords=["intern"], is_active=True
        )
        WatchlistRule.objects.create(
            company=company, keywords=["engineer"], is_active=True
        )
        posting = JobPosting.objects.create(
            company=company,
            external_id="123",
            title="Software Engineer Intern",
            url="https://example.com/job/123",
        )

        with patch(
            "apps.notifications.tasks.send_notification_email.delay"
        ) as mock_send:
            from django.db import transaction
            with transaction.atomic():
                _check_rules(posting, company)
            # Manually fire on_commit hooks queued in the atomic block above
            for callback in transaction.get_connection().run_on_commit:
                callback[1]()

        # Both rules match but we only create one notification
        assert Notification.objects.filter(user=user).count() == 1
        assert mock_send.call_count == 1


@pytest.mark.django_db
class TestNotificationSignal:
    def test_notification_create_enqueues_email(
        self, user, django_capture_on_commit_callbacks
    ):
        with patch(
            "apps.notifications.tasks.send_notification_email.delay"
        ) as mock_send:
            with django_capture_on_commit_callbacks(execute=True):
                notif = Notification.objects.create(
                    user=user,
                    type="system",
                    title="Welcome",
                    body="Welcome to Applywise!",
                )

        mock_send.assert_called_once_with(notif.id)

    def test_notification_update_does_not_fire(self, user):
        notif = Notification.objects.create(
            user=user, type="system", title="Hi", body="Body"
        )

        with patch(
            "apps.notifications.tasks.send_notification_email.delay"
        ) as mock_send:
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
