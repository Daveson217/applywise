"""Integration tests for _check_rules profile-defaults fallback.

_check_rules now FLAGS matches (matched_rules / matched_at) rather than
creating a Notification per job — emails are batched by the digest task.
So these assert on the posting's matched_rules flag.
"""

import pytest

from apps.watchlist.models import JobPosting, WatchlistCompany, WatchlistRule
from apps.watchlist.tasks import _check_rules


def _make_posting(company, title="Software Engineer", location="Remote"):
    return JobPosting.objects.create(
        company=company,
        external_id=f"ext-{title}-{location}",
        title=title,
        url="https://example.com/job/1",
        location=location,
    )


def _matched(posting) -> bool:
    posting.refresh_from_db()
    return posting.matched_rules


@pytest.mark.django_db
class TestProfileDefaultsFallback:
    def test_no_rules_no_profile_defaults_no_match(self, user):
        """A company with no rules and an empty profile should never match
        (avoid flagging everything)."""
        company = WatchlistCompany.objects.create(user=user, name="Acme")
        posting = _make_posting(company, title="Marketing Manager")

        _check_rules(posting, company)

        assert _matched(posting) is False

    def test_no_rules_uses_profile_defaults(self, user):
        """When a company has no rules, matching falls through to profile
        defaults so users don't have to duplicate rules per company."""
        user.profile.target_roles = ["ml"]
        user.profile.target_job_types = ["internship"]
        user.profile.save()

        company = WatchlistCompany.objects.create(user=user, name="Acme")
        matching = _make_posting(company, title="Machine Learning Intern")
        non_matching = _make_posting(company, title="Senior Product Manager")

        _check_rules(matching, company)
        _check_rules(non_matching, company)

        assert _matched(matching) is True
        assert _matched(non_matching) is False

    def test_rule_empty_field_falls_back_to_profile(self, user):
        """If a rule has no keywords but the profile does, use the profile's."""
        user.profile.target_roles = ["ml"]
        user.profile.save()

        company = WatchlistCompany.objects.create(user=user, name="Acme")
        # Rule filters on location only; keywords are empty → profile fills in.
        WatchlistRule.objects.create(company=company, locations=["remote"])

        posting = _make_posting(company, title="ML Engineer", location="Remote")
        _check_rules(posting, company)

        assert _matched(posting) is True

    def test_rule_field_overrides_profile(self, user):
        """A non-empty rule field wins over the profile default."""
        user.profile.target_roles = ["marketing"]  # profile wants marketing
        user.profile.save()

        company = WatchlistCompany.objects.create(user=user, name="Acme")
        # Rule explicitly asks for engineering; should win.
        WatchlistRule.objects.create(company=company, keywords=["engineer"])

        matching = _make_posting(company, title="Backend Engineer")
        non_matching = _make_posting(company, title="Marketing Lead")

        _check_rules(matching, company)
        _check_rules(non_matching, company)

        assert _matched(matching) is True
        assert _matched(non_matching) is False

    def test_profile_excludes_always_apply(self, user):
        """Excludes from the profile should apply on top of any rule — a rule
        matching 'engineer' still gets skipped if profile excludes 'senior'."""
        user.profile.excluded_keywords = ["senior"]
        user.profile.save()

        company = WatchlistCompany.objects.create(user=user, name="Acme")
        WatchlistRule.objects.create(company=company, keywords=["engineer"])

        junior = _make_posting(company, title="Junior Backend Engineer")
        senior = _make_posting(company, title="Senior Backend Engineer")

        _check_rules(junior, company)
        _check_rules(senior, company)

        assert _matched(junior) is True
        assert _matched(senior) is False

    def test_profile_defaults_respect_synonyms(self, user):
        """Profile-driven matching still uses the synonym expansion."""
        user.profile.target_roles = ["ml"]  # should also match "Machine Learning"
        user.profile.save()

        company = WatchlistCompany.objects.create(user=user, name="Acme")
        posting = _make_posting(company, title="Senior Machine Learning Scientist")

        _check_rules(posting, company)

        assert _matched(posting) is True
