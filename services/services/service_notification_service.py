# notifications/services/service_notification_service.py
"""
Notification helpers specific to the catalog (Service / Feature) domain.

All real work is delegated to NotificationService so that:
- DB writes + WebSocket fan-out stay in one place
- transactions are respected (on_commit)
- the same payload shape is used everywhere
"""

from __future__ import annotations

from typing import Iterable

from django.contrib.auth import get_user_model

from notifications.services.notification_service import NotificationService
from ..models import Service, Feature 

User = get_user_model()


class ServiceNotificationService:
    """
    High-level notification API for catalog events.
    """

    # ------------------------------------------------------------------
    # Service lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def notify_service_created(
        cls,
        *,
        service: Service,
        recipients,
        actor,
    ) -> list:
        """
        Notify interested users that a new service was created.
        """
        title = f"New service: {service.name}"
        message = (
            f"Service «{service.name}» ({service.code}) has been created"
            + (f" by {actor.get_full_name() or actor}" if actor else "")
            + "."
        )
        data = {
            "event": "service.created",
            "service_id": service.id,
            "service_code": service.code,
            "service_name": service.name,
            "actor_id": actor.id if actor else None,
        }

        return cls._broadcast(
            users=recipients or cls._default_recipients(service),
            title=title,
            message=message,
            notification_type="service.created",
            data=data,
        )

    @classmethod
    def notify_service_updated(
        cls,
        *,
        service: Service,
        recipients,
        actor,
        changed_fields: list[str] | None = None,
    ) -> list:
        title = f"Service updated: {service.name}"
        fields = ", ".join(changed_fields) if changed_fields else "details"
        message = (
            f"Service «{service.name}» ({service.code}) was updated"
            + (f" by {actor.get_full_name() or actor}" if actor else "")
            + f" ({fields})."
        )
        data = {
            "event": "service.updated",
            "service_id": service.id,
            "service_code": service.code,
            "service_name": service.name,
            "changed_fields": changed_fields or [],
            "actor_id": actor.id if actor else None,
        }

        return cls._broadcast(
            users=recipients or cls._default_recipients(service),
            title=title,
            message=message,
            notification_type="service.updated",
            data=data,
        )

    @classmethod
    def notify_service_soft_deleted(
        cls,
        *,
        service: Service,
        recipients,
        actor,
    ) -> list:
        title = f"Service deleted: {service.name}"
        message = (
            f"Service «{service.name}» ({service.code}) has been soft-deleted"
            + (f" by {actor.get_full_name() or actor}" if actor else "")
            + "."
        )
        data = {
            "event": "service.soft_deleted",
            "service_id": service.id,
            "service_code": service.code,
            "service_name": service.name,
            "actor_id": actor.id if actor else None,
        }

        return cls._broadcast(
            users=recipients or cls._default_recipients(service),
            title=title,
            message=message,
            notification_type="service.soft_deleted",
            data=data,
        )

    @classmethod
    def notify_service_restored(
        cls,
        *,
        service: Service,
        recipients,
        actor,
    ) -> list:
        title = f"Service restored: {service.name}"
        message = (
            f"Service «{service.name}» ({service.code}) has been restored"
            + (f" by {actor.get_full_name() or actor}" if actor else "")
            + "."
        )
        data = {
            "event": "service.restored",
            "service_id": service.id,
            "service_code": service.code,
            "service_name": service.name,
            "actor_id": actor.id if actor else None,
        }

        return cls._broadcast(
            users=recipients or cls._default_recipients(service),
            title=title,
            message=message,
            notification_type="service.restored",
            data=data,
        )

    # ------------------------------------------------------------------
    # Feature lifecycle (optional, but useful)
    # ------------------------------------------------------------------

    @classmethod
    def notify_feature_soft_deleted(
        cls,
        *,
        feature: Feature,
        recipients,
        actor,
    ) -> list:
        title = f"Feature deleted: {feature.name}"
        message = (
            f"Feature «{feature.name}» has been soft-deleted"
            + (f" by {actor.get_full_name() or actor}" if actor else "")
            + "."
        )
        data = {
            "event": "feature.soft_deleted",
            "feature_id": feature.id,
            "feature_name": feature.name,
            "actor_id": actor.id if actor else None,
        }

        return cls._broadcast(
            users=recipients or [],
            title=title,
            message=message,
            notification_type="feature.soft_deleted",
            data=data,
        )

    @classmethod
    def notify_feature_restored(
        cls,
        *,
        feature: Feature,
        recipients,
        actor,
    ) -> list:
        title = f"Feature restored: {feature.name}"
        message = (
            f"Feature «{feature.name}» has been restored"
            + (f" by {actor.get_full_name() or actor}" if actor else "")
            + "."
        )
        data = {
            "event": "feature.restored",
            "feature_id": feature.id,
            "feature_name": feature.name,
            "actor_id": actor.id if actor else None,
        }

        return cls._broadcast(
            users=recipients or [],
            title=title,
            message=message,
            notification_type="feature.restored",
            data=data,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _broadcast(
        cls,
        *,
        users,
        title: str,
        message: str,
        notification_type: str,
        data: dict | None = None,
    ) -> list:
        """
        Thin wrapper around NotificationService.broadcast.
        Filters out None / empty iterables so callers can pass None safely.
        """
        users = [u for u in (users or []) if u is not None]
        if not users:
            return []

        return NotificationService.broadcast(
            users=users,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data,
        )

    @classmethod
    def _default_recipients(cls, service: Service) -> list:
        """
        Decide who should be notified by default when a service changes.

        Current policy (adjust to your needs):
        - the user who created the service (if still active)
        - anyone you later add as “watchers” / subscribers
        """
        recipients = []
        if getattr(service, "created_by", None) and service.created_by.is_active:
            recipients.append(service.created_by)
        return recipients
    