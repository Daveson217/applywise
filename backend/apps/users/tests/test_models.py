import pytest
from django.contrib.auth import get_user_model

from apps.users.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123!",
            first_name="John",
            last_name="Doe",
        )
        assert user.email == "test@example.com"
        assert user.check_password("testpass123!")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_no_email_raises(self):
        with pytest.raises(ValueError, match="Email is required"):
            User.objects.create_user(email="", password="testpass123!")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123!",
            first_name="Admin",
            last_name="User",
        )
        assert user.is_staff
        assert user.is_superuser

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == "email"

    def test_str(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123!",
            first_name="John",
            last_name="Doe",
        )
        assert str(user) == "test@example.com"


@pytest.mark.django_db
class TestUserProfile:
    def test_profile_auto_created(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123!",
            first_name="John",
            last_name="Doe",
        )
        assert hasattr(user, "profile")
        assert isinstance(user.profile, UserProfile)

    def test_profile_defaults(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123!",
            first_name="John",
            last_name="Doe",
        )
        profile = user.profile
        assert profile.weekly_goal == 10
        assert profile.theme == "system"
        assert profile.accent_color == "blue"
        assert profile.default_llm_provider == "gemini"
        assert not profile.onboarding_completed
