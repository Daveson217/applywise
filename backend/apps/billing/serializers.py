from rest_framework import serializers

from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    limits = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "status",
            "stripe_customer_id",
            "current_period_end",
            "trial_end",
            "limits",
            "created_at",
        ]
        read_only_fields = fields

    def get_limits(self, obj):
        return obj.limits


class PlanInfoSerializer(serializers.Serializer):
    name = serializers.CharField()
    display_name = serializers.CharField()
    price_monthly = serializers.IntegerField()
    limits = serializers.DictField()
    features = serializers.ListField(child=serializers.CharField())
