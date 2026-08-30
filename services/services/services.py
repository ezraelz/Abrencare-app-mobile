"""
Service-layer functions for the catalog app.

Business logic lives here rather than in views or serializers so the same
logic is reusable from the DRF API, Django admin actions, and management
commands, and so transactions/validation live in exactly one place.

Notifications are delegated to ServiceNotificationService, which in turn
delegates to the central NotificationService.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from ..models import Feature, Service, ServiceFeature
from .service_notification_service import ServiceNotificationService


# ============================================================================
# Service lifecycle
# ============================================================================


@transaction.atomic
def create_service(
    *,
    data: dict,
    features: list[dict] | None,
    user=None,
) -> Service:
    """
    Create a service and synchronize its features.

    Args:
        data:
            Validated Service fields, for example:
            code, name, service_for, description, is_active.

        features:
            List of:
                {
                    "feature": Feature instance,
                    "display_order": int,
                }

        user:
            User performing the operation.

    Returns:
        The newly created Service instance.
    """

    service = Service.objects.create(
        **data,
        created_by=user,
        updated_by=user,
    )

    _sync_service_features(service, features or [])

    ServiceNotificationService.notify_service_created(
        service=service,
        actor=user,
        recipients=None,
    )

    return service


@transaction.atomic
def update_service(
    *,
    service: Service,
    data: dict,
    features: list[dict] | None,
    user=None,
) -> Service:
    """
    Update a service and optionally replace its feature relationships.

    Notifications include the fields that actually changed.
    """

    changed_fields: list[str] = []

    for field, value in data.items():
        old_value = getattr(service, field)

        if old_value != value:
            setattr(service, field, value)
            changed_fields.append(field)

    if changed_fields:
        service.updated_by = user

        # Include updated_by only when there was an actual Service change.
        service.save(
            update_fields=[
                *changed_fields,
                "updated_by",
            ]
        )

    if features is not None:
        _sync_service_features(service, features)

    if changed_fields or features is not None:
        if features is not None and "features" not in changed_fields:
            changed_fields.append("features")

        ServiceNotificationService.notify_service_updated(
            service=service,
            actor=user,
            recipients=None,
            changed_fields=changed_fields,
        )

    return service


@transaction.atomic
def soft_delete_service(
    *,
    service: Service,
    user=None,
) -> None:
    """
    Soft-delete a service.

    The service remains in the database but is marked as deleted.
    """

    # Idempotency protection.
    if service.is_deleted:
        return

    service.updated_by = user
    service.is_deleted = True
    service.deleted_at = timezone.now()

    service.save(
        update_fields=[
            "is_deleted",
            "deleted_at",
            "updated_by",
        ]
    )

    ServiceNotificationService.notify_service_soft_deleted(
        service=service,
        actor=user,
        recipients=None,
    )


@transaction.atomic
def restore_service(
    *,
    service: Service,
    user=None,
) -> None:
    """
    Restore a previously soft-deleted service.
    """

    # Idempotency protection.
    if not service.is_deleted:
        return

    service.updated_by = user
    service.is_deleted = False
    service.deleted_at = None

    service.save(
        update_fields=[
            "is_deleted",
            "deleted_at",
            "updated_by",
        ]
    )

    ServiceNotificationService.notify_service_restored(
        service=service,
        actor=user,
        recipients=None,
    )


# ============================================================================
# Feature lifecycle
# ============================================================================


@transaction.atomic
def soft_delete_feature(
    *,
    feature: Feature,
    user=None,
) -> None:
    """
    Soft-delete a feature.
    """

    # Idempotency protection.
    if feature.is_deleted:
        return

    feature.updated_by = user
    feature.is_deleted = True
    feature.deleted_at = timezone.now()

    feature.save(
        update_fields=[
            "is_deleted",
            "deleted_at",
            "updated_by",
        ]
    )

    ServiceNotificationService.notify_feature_soft_deleted(
        feature=feature,
        actor=user,
        recipients=None,
    )


@transaction.atomic
def restore_feature(
    *,
    feature: Feature,
    user=None,
) -> None:
    """
    Restore a previously soft-deleted feature.
    """

    # Idempotency protection.
    if not feature.is_deleted:
        return

    feature.updated_by = user
    feature.is_deleted = False
    feature.deleted_at = None

    feature.save(
        update_fields=[
            "is_deleted",
            "deleted_at",
            "updated_by",
        ]
    )

    ServiceNotificationService.notify_feature_restored(
        feature=feature,
        actor=user,
        recipients=None,
    )


# ============================================================================
# ServiceFeature management
# ============================================================================


def _sync_service_features(
    service: Service,
    features: list[dict],
) -> None:
    """
    Synchronize ServiceFeature rows with the supplied feature list.

    This performs a differential update rather than deleting and recreating
    every relationship.
    """

    incoming = {
        item["feature"].id: item["display_order"]
        for item in features
    }

    existing = {
        service_feature.feature_id: service_feature
        for service_feature in service.service_features.all()
    }

    to_create: list[ServiceFeature] = []
    to_update: list[ServiceFeature] = []

    for feature_id, display_order in incoming.items():
        row = existing.get(feature_id)

        if row is None:
            to_create.append(
                ServiceFeature(
                    service=service,
                    feature_id=feature_id,
                    display_order=display_order,
                )
            )

        elif row.display_order != display_order:
            row.display_order = display_order
            to_update.append(row)

    to_delete_ids = [
        row.id
        for feature_id, row in existing.items()
        if feature_id not in incoming
    ]

    if to_create:
        ServiceFeature.objects.bulk_create(to_create)

    if to_update:
        ServiceFeature.objects.bulk_update(
            to_update,
            ["display_order"],
        )

    if to_delete_ids:
        ServiceFeature.objects.filter(
            id__in=to_delete_ids
        ).delete()


@transaction.atomic
def reorder_service_features(
    *,
    service: Service,
    ordered_feature_ids: list[int],
) -> None:
    """
    Apply a new display order to features already attached to a service.

    Example:

        ordered_feature_ids = [5, 2, 8]

    results in:

        feature 5 -> display_order 0
        feature 2 -> display_order 1
        feature 8 -> display_order 2
    """

    rows = {
        service_feature.feature_id: service_feature
        for service_feature in service.service_features.all()
    }

    missing = set(ordered_feature_ids) - set(rows.keys())

    if missing:
        raise ValueError(
            f"Feature ids not attached to this service: {missing}"
        )

    to_update: list[ServiceFeature] = []

    for order, feature_id in enumerate(ordered_feature_ids):
        row = rows[feature_id]

        if row.display_order != order:
            row.display_order = order
            to_update.append(row)

    if to_update:
        ServiceFeature.objects.bulk_update(
            to_update,
            ["display_order"],
        )
        