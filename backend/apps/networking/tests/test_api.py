import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.networking.models import Contact, Interaction

User = get_user_model()

CONTACTS_URL = "/api/contacts/"


@pytest.mark.django_db
class TestContactCRUD:
    def test_list_empty(self, authenticated_client):
        response = authenticated_client.get(CONTACTS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_create_contact(self, authenticated_client):
        data = {
            "name": "Jane Smith",
            "company": "Google",
            "role": "Recruiter",
            "relationship_type": "recruiter",
            "email": "jane@google.com",
        }
        response = authenticated_client.post(CONTACTS_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Jane Smith"

    def test_list_scoped_to_user(self, authenticated_client, user, other_user):
        Contact.objects.create(user=user, name="Mine")
        Contact.objects.create(user=other_user, name="Theirs")
        response = authenticated_client.get(CONTACTS_URL)
        assert response.data["count"] == 1

    def test_update_contact(self, authenticated_client, user):
        contact = Contact.objects.create(user=user, name="Jane")
        response = authenticated_client.patch(f"{CONTACTS_URL}{contact.pk}/", {"company": "Meta"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["company"] == "Meta"

    def test_delete_contact(self, authenticated_client, user):
        contact = Contact.objects.create(user=user, name="Jane")
        response = authenticated_client.delete(f"{CONTACTS_URL}{contact.pk}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_contact_has_interaction_count(self, authenticated_client, user):
        contact = Contact.objects.create(user=user, name="Jane")
        Interaction.objects.create(contact=contact, type="coffee_chat", date="2026-01-01")
        response = authenticated_client.get(f"{CONTACTS_URL}{contact.pk}/")
        assert response.data["interactions_count"] == 1


@pytest.mark.django_db
class TestInteractions:
    def test_create_interaction(self, authenticated_client, user):
        contact = Contact.objects.create(user=user, name="Jane")
        data = {
            "type": "coffee_chat",
            "date": "2026-06-01",
            "notes": "Great conversation about team culture",
        }
        response = authenticated_client.post(f"{CONTACTS_URL}{contact.pk}/interactions/", data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_interactions(self, authenticated_client, user):
        contact = Contact.objects.create(user=user, name="Jane")
        Interaction.objects.create(contact=contact, type="email", date="2026-01-01")
        response = authenticated_client.get(f"{CONTACTS_URL}{contact.pk}/interactions/")
        assert response.status_code == status.HTTP_200_OK

    def test_interaction_scoped(self, authenticated_client, user, other_user):
        other_contact = Contact.objects.create(user=other_user, name="Secret")
        Interaction.objects.create(contact=other_contact, type="call", date="2026-01-01")
        response = authenticated_client.get(f"{CONTACTS_URL}{other_contact.pk}/interactions/")
        # paginated response — check count instead of len
        data = response.data
        if isinstance(data, dict) and "count" in data:
            assert data["count"] == 0
        else:
            assert len(data) == 0
