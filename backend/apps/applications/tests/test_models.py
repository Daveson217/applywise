import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.applications.models import Application, ApplicationActivity, Tag

User = get_user_model()


@pytest.mark.django_db
class TestApplicationModel:
    def test_create_application(self, user):
        app = Application.objects.create(
            user=user,
            company="Google",
            role="SWE Intern",
            job_type="internship",
        )
        assert app.status == "saved"
        assert app.priority == "medium"
        assert str(app) == "Google - SWE Intern"

    def test_salary_constraint(self, user):
        with pytest.raises(IntegrityError):
            Application.objects.create(
                user=user,
                company="Google",
                role="SWE",
                job_type="fulltime",
                salary_min=200000,
                salary_max=100000,
            )

    def test_status_change_creates_activity(self, user):
        app = Application.objects.create(
            user=user,
            company="Google",
            role="SWE Intern",
            job_type="internship",
            status="saved",
        )
        app.status = "applied"
        app.save()

        activity = ApplicationActivity.objects.filter(application=app).first()
        assert activity is not None
        assert activity.event_type == "status_change"
        assert activity.old_value == "saved"
        assert activity.new_value == "applied"


@pytest.mark.django_db
class TestTagModel:
    def test_create_tag(self, user):
        tag = Tag.objects.create(user=user, name="FAANG", color="#EF4444")
        assert str(tag) == "FAANG"

    def test_unique_tag_per_user(self, user):
        Tag.objects.create(user=user, name="FAANG")
        with pytest.raises(IntegrityError):
            Tag.objects.create(user=user, name="FAANG")

    def test_same_tag_name_different_users(self, user, other_user):
        Tag.objects.create(user=user, name="FAANG")
        tag2 = Tag.objects.create(user=other_user, name="FAANG")
        assert tag2.pk is not None
