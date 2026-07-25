"""Tests for the authenticated password-change endpoint."""

import pytest
from rest_framework import status

CHANGE_URL = "/api/auth/password/change/"


@pytest.mark.django_db
class TestPasswordChange:
    def test_valid_change_updates_password(self, authenticated_client, user):
        response = authenticated_client.post(
            CHANGE_URL,
            {
                "current_password": "testpass123!",
                "new_password": "NewStrongPass!456",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("NewStrongPass!456")

    def test_wrong_current_password_rejected(self, authenticated_client, user):
        response = authenticated_client.post(
            CHANGE_URL,
            {
                "current_password": "wrong-password",
                "new_password": "NewStrongPass!456",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Old password still works
        user.refresh_from_db()
        assert user.check_password("testpass123!")

    def test_same_as_old_password_rejected(self, authenticated_client, user):
        response = authenticated_client.post(
            CHANGE_URL,
            {
                "current_password": "testpass123!",
                "new_password": "testpass123!",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

    def test_weak_new_password_rejected(self, authenticated_client):
        response = authenticated_client.post(
            CHANGE_URL,
            {
                "current_password": "testpass123!",
                "new_password": "short",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_current_password_rejected(self, authenticated_client):
        response = authenticated_client.post(
            CHANGE_URL,
            {"new_password": "NewStrongPass!456"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_rejected(self, api_client):
        response = api_client.post(
            CHANGE_URL,
            {
                "current_password": "x",
                "new_password": "NewStrongPass!456",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_blacklists_other_sessions(self, api_client, user):
        # Two "devices": each does its own login
        login1 = api_client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "testpass123!"},
        )
        login2 = api_client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "testpass123!"},
        )
        refresh1 = login1.data["refresh"]
        refresh2 = login2.data["refresh"]

        # Device 1 changes password, preserving its own refresh
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login1.data['access']}")
        response = api_client.post(
            CHANGE_URL,
            {
                "current_password": "testpass123!",
                "new_password": "NewStrongPass!456",
                "current_refresh": refresh1,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        # Device 2's refresh must now fail
        api_client.credentials()  # clear
        r2 = api_client.post("/api/auth/token/refresh/", {"refresh": refresh2})
        assert r2.status_code == status.HTTP_401_UNAUTHORIZED

        # Device 1's refresh should still work
        r1 = api_client.post("/api/auth/token/refresh/", {"refresh": refresh1})
        assert r1.status_code == status.HTTP_200_OK
