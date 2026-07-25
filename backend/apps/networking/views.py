from rest_framework import viewsets

from .models import Contact, Interaction
from .serializers import ContactSerializer, InteractionSerializer


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    search_fields = ["name", "company", "role"]
    ordering_fields = ["name", "company", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return Contact.objects.filter(
            user=self.request.user
        ).prefetch_related("interactions")


class InteractionViewSet(viewsets.ModelViewSet):
    serializer_class = InteractionSerializer

    def get_queryset(self):
        return Interaction.objects.filter(
            contact_id=self.kwargs["contact_pk"],
            contact__user=self.request.user,
        )

    def perform_create(self, serializer):
        contact = Contact.objects.get(
            pk=self.kwargs["contact_pk"],
            user=self.request.user,
        )
        serializer.save(contact=contact)
