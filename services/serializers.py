"""
DRF serializers for the service catalog.

Design notes:
- Explicit `fields` lists everywhere (never `__all__`) so new model fields
  don't get silently exposed to API clients.
- Read and write concerns are split: list/detail serializers are read-only
  and denormalize nested feature data; the write serializer accepts a flat
  payload plus a `features` list of {feature_id, display_order}. Persistence
  is delegated to services.py rather than DRF's default M2M handling, which
  doesn't support `through` models with extra fields like `display_order`.
"""

from rest_framework import serializers

from .models import Feature, Service, ServiceAudience, ServiceFeature


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FeatureWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ["name", "description", "is_active"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Feature name cannot be blank.")
        return value


class ServiceFeatureSerializer(serializers.ModelSerializer):
    """Read representation of a feature attached to a service, with ordering."""

    id = serializers.IntegerField(source="feature.id", read_only=True)
    name = serializers.CharField(source="feature.name", read_only=True)
    description = serializers.CharField(source="feature.description", read_only=True)

    class Meta:
        model = ServiceFeature
        fields = ["id", "name", "description", "display_order"]


class ServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no nested feature lookups."""

    class Meta:
        model = Service
        fields = [
            "id",
            "code",
            "name",
            "service_for",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ServiceDetailSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id",
            "code",
            "name",
            "service_for",
            "description",
            "features",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_features(self, obj):
        # Expects `service_features` to be prefetched with
        # .select_related("feature") by the view — see ServiceViewSet.get_queryset().
        ordered = sorted(obj.service_features.all(), key=lambda sf: sf.display_order)
        return ServiceFeatureSerializer(ordered, many=True).data


class ServiceFeatureInputSerializer(serializers.Serializer):
    """One entry in the `features` list accepted by ServiceWriteSerializer."""

    feature_id = serializers.PrimaryKeyRelatedField(
        source="feature", queryset=Feature.objects.all()
    )
    display_order = serializers.IntegerField(min_value=0, default=0)


class ServiceWriteSerializer(serializers.ModelSerializer):
    features = ServiceFeatureInputSerializer(many=True, required=False)

    class Meta:
        model = Service
        fields = [
            "code",
            "name",
            "service_for",
            "description",
            "is_active",
            "features",
        ]

    def validate_service_for(self, value):
        if value not in ServiceAudience.values:
            raise serializers.ValidationError("Invalid audience.")
        return value

    def validate_features(self, value):
        feature_ids = [item["feature"].id for item in value]
        if len(feature_ids) != len(set(feature_ids)):
            raise serializers.ValidationError("Duplicate feature_id in features list.")
        return value
