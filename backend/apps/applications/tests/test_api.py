import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.applications.models import Application, ApplicationActivity, Tag

User = get_user_model()

APPS_URL = "/api/applications/"
TAGS_URL = "/api/tags/"


def app_detail_url(pk):
    return f"/api/applications/{pk}/"


def app_activity_url(pk):
    return f"/api/applications/{pk}/activity/"


@pytest.mark.django_db
class TestApplicationList:
    def test_list_empty(self, authenticated_client):
        response = authenticated_client.get(APPS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_returns_only_own_apps(self, authenticated_client, user, other_user):
        Application.objects.create(
            user=user, company="MyCompany", role="Dev", job_type="internship"
        )
        Application.objects.create(
            user=other_user, company="OtherCompany", role="Dev", job_type="internship"
        )
        response = authenticated_client.get(APPS_URL)
        assert response.data["count"] == 1
        assert response.data["results"][0]["company"] == "MyCompany"

    def test_list_unauthenticated(self, api_client):
        response = api_client.get(APPS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestApplicationCreate:
    def test_create_success(self, authenticated_client):
        data = {
            "company": "Google",
            "role": "SWE Intern",
            "job_type": "internship",
            "status": "saved",
            "priority": "high",
        }
        response = authenticated_client.post(APPS_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["company"] == "Google"

    def test_create_missing_required_fields(self, authenticated_client):
        response = authenticated_client.post(APPS_URL, {"company": "Google"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_logs_activity(self, authenticated_client, user):
        data = {
            "company": "Google",
            "role": "SWE Intern",
            "job_type": "internship",
        }
        response = authenticated_client.post(APPS_URL, data)
        app_id = response.data["id"]
        activity = ApplicationActivity.objects.filter(application_id=app_id)
        assert activity.filter(event_type="created").exists()

    def test_create_with_tags(self, authenticated_client, user):
        tag = Tag.objects.create(user=user, name="FAANG")
        data = {
            "company": "Google",
            "role": "SWE Intern",
            "job_type": "internship",
            "tag_ids": [tag.id],
        }
        response = authenticated_client.post(APPS_URL, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_with_salary(self, authenticated_client):
        data = {
            "company": "Google",
            "role": "SWE",
            "job_type": "fulltime",
            "salary_min": 100000,
            "salary_max": 150000,
        }
        response = authenticated_client.post(APPS_URL, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_invalid_salary_range(self, authenticated_client):
        data = {
            "company": "Google",
            "role": "SWE",
            "job_type": "fulltime",
            "salary_min": 200000,
            "salary_max": 100000,
        }
        response = authenticated_client.post(APPS_URL, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestApplicationDetail:
    def test_retrieve(self, authenticated_client, user):
        app = Application.objects.create(
            user=user, company="Google", role="SWE", job_type="internship"
        )
        response = authenticated_client.get(app_detail_url(app.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["company"] == "Google"
        assert "activity_count" in response.data

    def test_retrieve_other_users_app(self, authenticated_client, other_user):
        app = Application.objects.create(
            user=other_user, company="Secret", role="Dev", job_type="internship"
        )
        response = authenticated_client.get(app_detail_url(app.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update(self, authenticated_client, user):
        app = Application.objects.create(
            user=user, company="Google", role="SWE", job_type="internship"
        )
        response = authenticated_client.patch(
            app_detail_url(app.pk), {"status": "applied"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_status_creates_activity(self, authenticated_client, user):
        app = Application.objects.create(
            user=user,
            company="Google",
            role="SWE",
            job_type="internship",
            status="saved",
        )
        authenticated_client.patch(app_detail_url(app.pk), {"status": "applied"})
        activity = ApplicationActivity.objects.filter(
            application=app, event_type="status_change"
        )
        assert activity.exists()
        assert activity.first().old_value == "saved"
        assert activity.first().new_value == "applied"

    def test_delete(self, authenticated_client, user):
        app = Application.objects.create(
            user=user, company="Google", role="SWE", job_type="internship"
        )
        response = authenticated_client.delete(app_detail_url(app.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Application.objects.filter(pk=app.pk).exists()


@pytest.mark.django_db
class TestApplicationFiltering:
    def test_filter_by_status(self, authenticated_client, user):
        Application.objects.create(
            user=user, company="A", role="Dev", job_type="internship", status="saved"
        )
        Application.objects.create(
            user=user, company="B", role="Dev", job_type="internship", status="applied"
        )
        response = authenticated_client.get(APPS_URL, {"status": "applied"})
        assert response.data["count"] == 1
        assert response.data["results"][0]["company"] == "B"

    def test_filter_by_priority(self, authenticated_client, user):
        Application.objects.create(
            user=user, company="A", role="Dev", job_type="internship", priority="high"
        )
        Application.objects.create(
            user=user, company="B", role="Dev", job_type="internship", priority="low"
        )
        response = authenticated_client.get(APPS_URL, {"priority": "high"})
        assert response.data["count"] == 1

    def test_search_by_company(self, authenticated_client, user):
        Application.objects.create(
            user=user, company="Google", role="Dev", job_type="internship"
        )
        Application.objects.create(
            user=user, company="Meta", role="Dev", job_type="internship"
        )
        response = authenticated_client.get(APPS_URL, {"search": "Google"})
        assert response.data["count"] == 1

    def test_pagination(self, authenticated_client, user):
        for i in range(25):
            Application.objects.create(
                user=user, company=f"Company{i}", role="Dev", job_type="internship"
            )
        response = authenticated_client.get(APPS_URL)
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 20


@pytest.mark.django_db
class TestApplicationActivity:
    def test_activity_list(self, authenticated_client, user):
        app = Application.objects.create(
            user=user, company="Google", role="SWE", job_type="internship"
        )
        ApplicationActivity.objects.create(
            application=app, event_type="created"
        )
        response = authenticated_client.get(app_activity_url(app.pk))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_activity_other_user(self, authenticated_client, other_user):
        app = Application.objects.create(
            user=other_user, company="Secret", role="Dev", job_type="internship"
        )
        response = authenticated_client.get(app_activity_url(app.pk))
        assert response.data["count"] == 0


@pytest.mark.django_db
class TestTagAPI:
    def test_create_tag(self, authenticated_client):
        response = authenticated_client.post(
            TAGS_URL, {"name": "FAANG", "color": "#EF4444"}
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_own_tags(self, authenticated_client, user, other_user):
        Tag.objects.create(user=user, name="mine")
        Tag.objects.create(user=other_user, name="theirs")
        response = authenticated_client.get(TAGS_URL)
        assert response.data["count"] == 1

    def test_duplicate_tag_name(self, authenticated_client, user):
        Tag.objects.create(user=user, name="FAANG")
        response = authenticated_client.post(TAGS_URL, {"name": "FAANG"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
