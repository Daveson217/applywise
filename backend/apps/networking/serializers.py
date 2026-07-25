from rest_framework import serializers

from .models import Contact, Interaction


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = [
            "id",
            "type",
            "date",
            "notes",
            "linked_application",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ContactSerializer(serializers.ModelSerializer):
    interactions_count = serializers.SerializerMethodField()
    last_interaction_date = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "company",
            "role",
            "email",
            "linkedin_url",
            "relationship_type",
            "notes",
            "interactions_count",
            "last_interaction_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_interactions_count(self, obj):
        return obj.interactions.count()

    def get_last_interaction_date(self, obj):
        last = obj.interactions.first()
        return last.date if last else None

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
