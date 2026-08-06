from rest_framework import serializers
from .models import Feature, Service


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"
        read_only_fields = ("created_at",)


class ServiceSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, read_only=True)
    feature_ids = serializers.PrimaryKeyRelatedField(
        queryset=Feature.objects.all(),
        source="features",
        many=True,
        write_only=True
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "service_name",
            "service_for",
            "features",
            "feature_ids",
            "description",
            "created_at",
        ]
        read_only_fields = ("created_at",)
        