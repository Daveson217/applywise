import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.watchlist.models import JobPosting, WatchlistCompany, WatchlistRule

User = get_user_model()

WATCHLIST_URL = "/api/watchlist/"
DETECT_URL = "/api/watchlist/detect-ats/"


@pytest.mark.django_db
class TestWatchlistCRUD:
    def test_list_empty(self, authenticated_client):
        response = authenticated_client.get(WATCHLIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_create_company(self, authenticated_client):
        data = {"name": "Stripe", "careers_url": "https://boards.greenhouse.io/stripe"}
        response = authenticated_client.post(WATCHLIST_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Stripe"
        assert response.data["ats_provider"] == "greenhouse"
        assert response.data["ats_company_slug"] == "stripe"

    def test_create_company_without_url(self, authenticated_client):
        data = {"name": "Unknown Corp"}
        response = authenticated_client.post(WATCHLIST_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["ats_provider"] == ""

    def test_delete_company(self, authenticated_client, user):
        company = WatchlistCompany.objects.create(user=user, name="Test", ats_provider="greenhouse")
        response = authenticated_client.delete(f"{WATCHLIST_URL}{company.pk}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_list_scoped_to_user(self, authenticated_client, user, other_user):
        WatchlistCompany.objects.create(user=user, name="Mine")
        WatchlistCompany.objects.create(user=other_user, name="Theirs")
        response = authenticated_client.get(WATCHLIST_URL)
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Mine"


@pytest.mark.django_db
class TestATSDetection:
    def test_detect_greenhouse(self, authenticated_client):
        response = authenticated_client.post(
            DETECT_URL, {"url": "https://boards.greenhouse.io/stripe"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detected"] is True
        assert response.data["provider"] == "greenhouse"
        assert response.data["slug"] == "stripe"

    def test_detect_unknown(self, authenticated_client):
        response = authenticated_client.post(DETECT_URL, {"url": "https://careers.randomcorp.com"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detected"] is False


@pytest.mark.django_db
class TestWatchlistRules:
    def test_create_rule(self, authenticated_client, user):
        company = WatchlistCompany.objects.create(user=user, name="Stripe")
        response = authenticated_client.post(
            f"{WATCHLIST_URL}{company.pk}/rules/",
            {"keywords": ["intern", "engineer"], "locations": ["SF"]},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["keywords"] == ["intern", "engineer"]

    def test_list_rules(self, authenticated_client, user):
        company = WatchlistCompany.objects.create(user=user, name="Stripe")
        WatchlistRule.objects.create(company=company, keywords=["intern"], is_active=True)
        response = authenticated_client.get(f"{WATCHLIST_URL}{company.pk}/rules/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestWatchlistPostings:
    def test_list_postings(self, authenticated_client, user):
        company = WatchlistCompany.objects.create(user=user, name="Stripe")
        JobPosting.objects.create(
            company=company,
            external_id="123",
            title="SWE Intern",
            url="https://boards.greenhouse.io/stripe/jobs/123",
        )
        response = authenticated_client.get(f"{WATCHLIST_URL}{company.pk}/postings/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
