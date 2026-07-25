from rest_framework import serializers

from .models import AIUsageLog, CoverLetter


class CoverLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = [
            "id",
            "application",
            "cv_version",
            "content",
            "job_description",
            "provider",
            "model",
            "prompt_settings",
            "version_number",
            "created_at",
        ]
        read_only_fields = ["id", "content", "provider", "model", "created_at"]


class CoverLetterRequestSerializer(serializers.Serializer):
    job_url = serializers.URLField(required=False, allow_blank=True)
    job_description = serializers.CharField(required=False, allow_blank=True)
    cv_version_id = serializers.IntegerField()
    application_id = serializers.IntegerField(required=False)
    company = serializers.CharField(max_length=255)
    job_title = serializers.CharField(max_length=255)
    tone = serializers.ChoiceField(
        choices=["formal", "conversational", "enthusiastic"],
        default="formal",
    )
    length = serializers.ChoiceField(
        choices=["brief", "standard", "detailed"],
        default="standard",
    )
    emphasis = serializers.ChoiceField(
        choices=["skills", "achievements", "culture_fit"],
        default="skills",
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.CharField(required=False)
    model = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get("job_url") and not data.get("job_description"):
            raise serializers.ValidationError("Either job_url or job_description is required.")
        return data


class QARequestSerializer(serializers.Serializer):
    question = serializers.CharField()
    cv_version_id = serializers.IntegerField()
    job_context = serializers.CharField(required=False, allow_blank=True)
    character_limit = serializers.IntegerField(required=False)
    provider = serializers.CharField(required=False)
    model = serializers.CharField(required=False)


class FitScoreRequestSerializer(serializers.Serializer):
    job_url = serializers.URLField(required=False, allow_blank=True)
    job_description = serializers.CharField(required=False, allow_blank=True)
    cv_version_id = serializers.IntegerField()
    company = serializers.CharField(max_length=255, required=False, default="")
    job_title = serializers.CharField(max_length=255, required=False, default="")
    provider = serializers.CharField(required=False)
    model = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get("job_url") and not data.get("job_description"):
            raise serializers.ValidationError("Either job_url or job_description is required.")
        return data


class ATSScoreRequestSerializer(serializers.Serializer):
    job_description = serializers.CharField()
    cv_version_id = serializers.IntegerField()
    provider = serializers.CharField(required=False)
    model = serializers.CharField(required=False)


class AIUsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIUsageLog
        fields = [
            "id",
            "feature",
            "provider",
            "model",
            "input_tokens",
            "output_tokens",
            "timestamp",
        ]
