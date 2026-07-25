import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
REFRESH_URL = "/api/auth/token/refresh/"
ME_URL = "/api/users/me/"


@pytest.mark.django_db
class TestRegister:
    def test_register_success(self, api_client):
        data = {
            "email": "new@example.com",
            "password": "strongpass123!",
            "password_confirm": "strongpass123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(REGISTER_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]
        assert response.data["user"]["email"] == "new@example.com"

    def test_register_duplicate_email(self, api_client, user):
        data = {
            "email": user.email,
            "password": "strongpass123!",
            "password_confirm": "strongpass123!",
            "first_name": "Dup",
            "last_name": "User",
        }
        response = api_client.post(REGISTER_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client):
        data = {
            "email": "new@example.com",
            "password": "strongpass123!",
            "password_confirm": "differentpass123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(REGISTER_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client):
        data = {
            "email": "new@example.com",
            "password": "123",
            "password_confirm": "123",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(REGISTER_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_fields(self, api_client):
        response = api_client.post(REGISTER_URL, {"email": "new@example.com"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, user):
        response = api_client.post(
            LOGIN_URL, {"email": user.email, "password": "testpass123!"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_credentials(self, api_client, user):
        response = api_client.post(
            LOGIN_URL, {"email": user.email, "password": "wrongpass"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post(
            LOGIN_URL, {"email": "ghost@example.com", "password": "testpass123!"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_success(self, api_client, user):
        login_response = api_client.post(
            LOGIN_URL, {"email": user.email, "password": "testpass123!"}
        )
        refresh_token = login_response.data["refresh"]

        response = api_client.post(REFRESH_URL, {"refresh": refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token(self, api_client):
        response = api_client.post(REFRESH_URL, {"refresh": "invalid-token"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMeEndpoint:
    def test_get_me(self, authenticated_client, user):
        response = authenticated_client.get(ME_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert "profile" in response.data

    def test_get_me_unauthenticated(self, api_client):
        response = api_client.get(ME_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_me(self, authenticated_client):
        response = authenticated_client.patch(
            ME_URL,
            {"first_name": "Updated", "profile": {"university": "MIT"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"
        assert response.data["profile"]["university"] == "MIT"

    def test_update_profile_preferences(self, authenticated_client):
        response = authenticated_client.patch(
            ME_URL,
            {"profile": {"theme": "dark", "weekly_goal": 15}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["profile"]["theme"] == "dark"
        assert response.data["profile"]["weekly_goal"] == 15
