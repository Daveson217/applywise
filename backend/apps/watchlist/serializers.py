from rest_framework import serializers

from .models import JobPosting, WatchlistCompany, WatchlistRule


class WatchlistRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchlistRule
        fields = ["id", "keywords", "locations", "job_types", "is_active"]
        read_only_fields = ["id"]

    @staticmethod
    def _bounded_string_list(value, *, max_items=50, max_len=100):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of strings.")
        if len(value) > max_items:
            raise serializers.ValidationError(
                f"At most {max_items} items allowed."
            )
        cleaned = []
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Items must be strings.")
            item = item.strip()[:max_len]
            if item:
                cleaned.append(item)
        return cleaned

    def validate_keywords(self, value):
        return self._bounded_string_list(value)

    def validate_locations(self, value):
        return self._bounded_string_list(value)

    def validate_job_types(self, value):
        return self._bounded_string_list(value, max_items=10, max_len=30)


class JobPostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosting
        fields = [
            "id",
            "external_id",
            "title",
            "url",
            "location",
            "first_seen_at",
            "last_seen_at",
            "is_active",
            "is_reposted",
            "matched_rules",
        ]


class WatchlistCompanySerializer(serializers.ModelSerializer):
    rules = WatchlistRuleSerializer(many=True, read_only=True)
    active_postings_count = serializers.SerializerMethodField()
    total_postings_count = serializers.SerializerMethodField()

    class Meta:
        model = WatchlistCompany
        fields = [
            "id",
            "name",
            "careers_url",
            "ats_provider",
            "ats_company_slug",
            "scrape_status",
            "last_checked_at",
            "last_error",
            "rules",
            "active_postings_count",
            "total_postings_count",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "ats_provider",
            "ats_company_slug",
            "scrape_status",
            "last_checked_at",
            "last_error",
            "created_at",
        ]

    def get_active_postings_count(self, obj):
        return obj.postings.filter(is_active=True).count()

    def get_total_postings_count(self, obj):
        return obj.postings.count()

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class WatchlistCompanyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    careers_url = serializers.URLField(required=False, allow_blank=True)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        # Reject control chars (would break logs, emails, UI rendering)
        if any(ord(c) < 32 for c in value):
            raise serializers.ValidationError("Invalid characters in name.")
        return value

    def validate_careers_url(self, value):
        # Defense in depth: reject obviously dangerous URLs even though we
        # don't fetch them in this code path. Future code might.
        if not value:
            return value
        from apps.common.url_validation import (
            URLValidationError,
            validate_external_url,
        )

        try:
            validate_external_url(value)
        except URLValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return WatchlistCompany.objects.create(**validated_data)


class ATSDetectSerializer(serializers.Serializer):
    url = serializers.URLField()

    def validate_url(self, value):
        # Same SSRF guard as in WatchlistCompanyCreateSerializer
        from apps.common.url_validation import (
            URLValidationError,
            validate_external_url,
        )

        try:
            validate_external_url(value)
        except URLValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
