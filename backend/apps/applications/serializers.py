from rest_framework import serializers

from .models import Application, ApplicationActivity, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        user = self.context["request"].user
        qs = Tag.objects.filter(user=user, name=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("You already have a tag with this name.")
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ApplicationActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationActivity
        fields = ["id", "event_type", "old_value", "new_value", "timestamp"]
        read_only_fields = fields


class ApplicationListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "company",
            "role",
            "status",
            "job_type",
            "priority",
            "applied_date",
            "deadline",
            "location",
            "is_remote",
            "source",
            "url",
            "ai_fit_score",
            "tags",
            "created_at",
            "updated_at",
        ]


class ApplicationDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    activity_count = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "company",
            "role",
            "status",
            "job_type",
            "applied_date",
            "deadline",
            "salary_min",
            "salary_max",
            "salary_currency",
            "location",
            "is_remote",
            "url",
            "source",
            "notes",
            "priority",
            "tags",
            "ai_fit_score",
            "follow_up_date",
            "recruiter_name",
            "recruiter_email",
            "activity_count",
            "created_at",
            "updated_at",
        ]

    def get_activity_count(self, obj):
        return obj.activities.count()


class ApplicationCreateUpdateSerializer(serializers.ModelSerializer):
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Application
        fields = [
            "id",
            "company",
            "role",
            "status",
            "job_type",
            "applied_date",
            "deadline",
            "salary_min",
            "salary_max",
            "salary_currency",
            "location",
            "is_remote",
            "url",
            "source",
            "notes",
            "priority",
            "follow_up_date",
            "recruiter_name",
            "recruiter_email",
            "tag_ids",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        salary_min = data.get("salary_min") or (
            self.instance.salary_min if self.instance else None
        )
        salary_max = data.get("salary_max") or (
            self.instance.salary_max if self.instance else None
        )
        if salary_min is not None and salary_max is not None:
            if salary_min > salary_max:
                raise serializers.ValidationError(
                    {"salary_min": "Minimum salary cannot exceed maximum salary."}
                )
        return data

    def create(self, validated_data):
        tag_ids = validated_data.pop("tag_ids", [])
        validated_data["user"] = self.context["request"].user
        application = Application.objects.create(**validated_data)
        if tag_ids:
            tags = Tag.objects.filter(
                id__in=tag_ids, user=self.context["request"].user
            )
            application.tags.set(tags)
        ApplicationActivity.objects.create(
            application=application, event_type="created"
        )
        return application

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            tags = Tag.objects.filter(
                id__in=tag_ids, user=self.context["request"].user
            )
            instance.tags.set(tags)
        return instance
