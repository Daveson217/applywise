import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.notifications.models import Notification

User = get_user_model()

NOTIF_URL = "/api/notifications/"
UNREAD_URL = "/api/notifications/unread-count/"
MARK_ALL_URL = "/api/notifications/mark-all-read/"


@pytest.mark.django_db
class TestNotifications:
    def test_list_empty(self, authenticated_client):
        response = authenticated_client.get(NOTIF_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_own_notifications(self, authenticated_client, user, other_user):
        Notification.objects.create(
            user=user, type="system", title="Welcome!", body="Hello"
        )
        Notification.objects.create(
            user=other_user, type="system", title="Their notif", body="Hi"
        )
        response = authenticated_client.get(NOTIF_URL)
        assert response.data["count"] == 1

    def test_unread_count(self, authenticated_client, user):
        Notification.objects.create(
            user=user, type="system", title="N1", body="B1"
        )
        Notification.objects.create(
            user=user, type="system", title="N2", body="B2", is_read=True
        )
        response = authenticated_client.get(UNREAD_URL)
        assert response.data["count"] == 1

    def test_mark_read(self, authenticated_client, user):
        notif = Notification.objects.create(
            user=user, type="system", title="N1", body="B1"
        )
        response = authenticated_client.post(f"{NOTIF_URL}{notif.pk}/read/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_read"] is True

    def test_mark_all_read(self, authenticated_client, user):
        Notification.objects.create(
            user=user, type="system", title="N1", body="B1"
        )
        Notification.objects.create(
            user=user, type="system", title="N2", body="B2"
        )
        response = authenticated_client.post(MARK_ALL_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["marked"] == 2
        assert Notification.objects.filter(user=user, is_read=False).count() == 0
