"""Tests for the watchlist digest task and matched-jobs feed."""

from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status

from apps.watchlist.models import JobPosting, WatchlistCompany


def _matched_posting(company, title="ML Intern", ext="1"):
    return JobPosting.objects.create(
        company=company,
        external_id=ext,
        title=title,
        url=f"https://example.com/{ext}",
        location="Remote",
        matched_rules=True,
        matched_at=timezone.now(),
    )


@pytest.mark.django_db
class TestDigestTask:
    def test_sends_digest_and_marks_notified(self, user):
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        p1 = _matched_posting(company, "ML Intern", "1")
        p2 = _matched_posting(company, "CV Intern", "2")

        from apps.watchlist.tasks import send_watchlist_digests

        with patch("apps.watchlist.tasks._send_digest_email") as mock_email:
            send_watchlist_digests()

        mock_email.assert_called_once()
        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.match_notified is True
        assert p2.match_notified is True

        # A single in-app notification summarizing the batch.
        from apps.notifications.models import Notification

        assert Notification.objects.filter(user=user).count() == 1

        user.profile.refresh_from_db()
        assert user.profile.watchlist_digest_last_sent is not None

    def test_off_frequency_skips(self, user):
        user.profile.watchlist_digest_frequency = "off"
        user.profile.save()
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        _matched_posting(company)

        from apps.watchlist.tasks import send_watchlist_digests

        with patch("apps.watchlist.tasks._send_digest_email") as mock_email:
            send_watchlist_digests()
        mock_email.assert_not_called()

    def test_respects_cadence(self, user):
        # Already sent recently → daily cadence should skip.
        user.profile.watchlist_digest_last_sent = timezone.now()
        user.profile.save()
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        _matched_posting(company)

        from apps.watchlist.tasks import send_watchlist_digests

        with patch("apps.watchlist.tasks._send_digest_email") as mock_email:
            send_watchlist_digests()
        mock_email.assert_not_called()

    def test_no_pending_no_email(self, user):
        # Company exists but no matched postings → nothing to send.
        WatchlistCompany.objects.create(user=user, name="Acme")

        from apps.watchlist.tasks import send_watchlist_digests

        with patch("apps.watchlist.tasks._send_digest_email") as mock_email:
            send_watchlist_digests()
        mock_email.assert_not_called()

    def test_dismissed_excluded_from_digest(self, user):
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        p = _matched_posting(company)
        p.match_dismissed = True
        p.save()

        from apps.watchlist.tasks import send_watchlist_digests

        with patch("apps.watchlist.tasks._send_digest_email") as mock_email:
            send_watchlist_digests()
        mock_email.assert_not_called()


@pytest.mark.django_db
class TestMatchedJobsFeed:
    URL = "/api/watchlist/matches/"

    def test_lists_matched_only(self, authenticated_client, user):
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        _matched_posting(company, "ML Intern", "1")
        # Non-matched posting should not appear.
        JobPosting.objects.create(
            company=company,
            external_id="2",
            title="Sales Rep",
            url="https://example.com/2",
            location="NY",
            matched_rules=False,
        )

        response = authenticated_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "ML Intern"
        assert response.data["results"][0]["company_name"] == "Acme"

    def test_dismiss_removes_from_feed(self, authenticated_client, user):
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        p = _matched_posting(company)

        r = authenticated_client.post(f"{self.URL}{p.id}/dismiss/")
        assert r.status_code == status.HTTP_200_OK

        response = authenticated_client.get(self.URL)
        assert response.data["count"] == 0

    def test_scoped_to_user(self, authenticated_client, user, other_user):
        mine = WatchlistCompany.objects.create(user=user, name="Mine")
        theirs = WatchlistCompany.objects.create(user=other_user, name="Theirs")
        _matched_posting(mine, "Mine Job", "1")
        _matched_posting(theirs, "Their Job", "2")

        response = authenticated_client.get(self.URL)
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Mine Job"

    def test_dismiss_other_user_404(self, authenticated_client, other_user):
        theirs = WatchlistCompany.objects.create(user=other_user, name="Theirs")
        p = _matched_posting(theirs)
        r = authenticated_client.post(f"{self.URL}{p.id}/dismiss/")
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_unauth_rejected(self, api_client):
        assert api_client.get(self.URL).status_code == status.HTTP_401_UNAUTHORIZED
