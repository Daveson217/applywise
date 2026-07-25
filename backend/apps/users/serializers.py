from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "phone",
            "graduation_date",
            "university",
            "target_roles",
            "preferred_locations",
            "linkedin_url",
            "github_url",
            "website_url",
            "bio",
            "weekly_goal",
            "theme",
            "accent_color",
            "default_llm_provider",
            "default_llm_model",
            "onboarding_completed",
        ]

    @staticmethod
    def _validate_string_list(value, *, max_items=20, max_item_length=200):
        """Bound JSON list fields so a user can't dump 100MB into the DB."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of strings.")
        if len(value) > max_items:
            raise serializers.ValidationError(
                f"At most {max_items} items allowed."
            )
        result = []
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Items must be strings.")
            item = item.strip()
            if len(item) > max_item_length:
                raise serializers.ValidationError(
                    f"Each item must be ≤ {max_item_length} chars."
                )
            if item:
                result.append(item)
        return result

    def validate_target_roles(self, value):
        return self._validate_string_list(value, max_items=20, max_item_length=100)

    def validate_preferred_locations(self, value):
        return self._validate_string_list(value, max_items=20, max_item_length=100)

    def validate_bio(self, value):
        if value and len(value) > 2000:
            raise serializers.ValidationError("Bio must be ≤ 2000 characters.")
        return value

    def validate_weekly_goal(self, value):
        if not 1 <= value <= 200:
            raise serializers.ValidationError("Weekly goal must be 1-200.")
        return value


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_email_verified",
            "date_joined",
            "profile",
        ]
        read_only_fields = ["id", "email", "is_email_verified", "date_joined"]


class MeSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_email_verified",
            "date_joined",
            "profile",
        ]
        read_only_fields = ["id", "email", "is_email_verified", "date_joined"]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save()

        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)
