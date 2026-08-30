"""
Service catalog models.

Notes for maintainers:
- These models represent catalog metadata (services/features offered),
  NOT patient health records. If you extend this app to reference actual
  patient/clinical data, do NOT reuse this file's patterns as-is —
  PHI-bearing models need field-level encryption, stricter access
  control, and request-level audit logging in addition to what's here.
- Soft delete (`is_deleted`) is separate from `is_active`:
    * is_active  -> business toggle ("is this service currently offered")
    * is_deleted -> retirement of the record while preserving history
"""

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# ---------------------------------------------------------------------------
# Shared abstract base classes
# ---------------------------------------------------------------------------


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at to any model that inherits from it."""

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        abstract = True


class AuditableModel(models.Model):
    """
    Adds created_by / updated_by for compliance/audit trails.
    Nullable + SET_NULL so deleting a user account never cascades
    into deleting catalog data.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Created by"),
        related_name="%(class)s_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Updated by"),
        related_name="%(class)s_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Default manager excludes soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class ActiveManager(SoftDeleteManager):
    """Default manager excludes soft-deleted AND inactive rows."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class SoftDeleteModel(models.Model):
    """
    Adds soft-delete support.

    `objects`      -> active, non-deleted rows (use this everywhere by default)
    `all_objects`  -> everything, including deleted/inactive (use for admin/audit)
    """

    is_deleted = models.BooleanField(_("Deleted"), default=False, db_index=True)
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------


class ServiceAudience(models.TextChoices):
    INDIVIDUAL = "individual", _("Individual")
    FAMILY = "family", _("Family")
    EXECUTIVE = "executive", _("Executive")
    ORGANIZATION = "organization", _("Organization")


# Enforce lowercase, hyphen-separated codes for stable API/URL usage.
code_validator = RegexValidator(
    regex=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    message=_(
        "Code must be lowercase alphanumeric, using hyphens to separate words "
        "(e.g. 'annual-checkup')."
    ),
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Feature(TimeStampedModel, AuditableModel, SoftDeleteModel):
    name = models.CharField(_("Feature Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Feature")
        verbose_name_plural = _("Features")
        indexes = [
            models.Index(fields=["is_active", "is_deleted"]),
        ]

    def __str__(self):
        return self.name


class Service(TimeStampedModel, AuditableModel, SoftDeleteModel):
    code = models.SlugField(
        _("Service Code"),
        max_length=50,
        unique=True,
        validators=[code_validator],
        help_text=_("Stable identifier used in APIs/URLs, e.g. 'annual-checkup'."),
    )
    name = models.CharField(_("Service Name"), max_length=100)
    service_for = models.CharField(
        _("Service For"),
        max_length=20,
        choices=ServiceAudience.choices,
        db_index=True,
    )
    description = models.TextField(_("Description"), blank=True)
    features = models.ManyToManyField(
        Feature,
        through="ServiceFeature",
        related_name="services",
        blank=True,
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        constraints = [
            models.UniqueConstraint(
                fields=["name", "service_for"],
                name="unique_service_name_per_audience",
            ),
        ]
        indexes = [
            models.Index(fields=["service_for", "is_active"]),
            models.Index(fields=["is_active", "is_deleted"]),
        ]

    def __str__(self):
        return self.name


class ServiceFeature(models.Model):
    """Through model linking Service <-> Feature with explicit ordering."""

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="service_features",
    )
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name="feature_services",
    )
    display_order = models.PositiveSmallIntegerField(_("Display Order"), default=0)

    class Meta:
        ordering = ["display_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "feature"],
                name="unique_service_feature",
            ),
        ]
        indexes = [
            models.Index(fields=["service", "display_order"]),
        ]
        verbose_name = _("Service Feature")
        verbose_name_plural = _("Service Features")

    def __str__(self):
        # Note: iterating many of these without select_related("service", "feature")
        # will cause N+1 queries — prefetch in admin/list views.
        return f"{self.service.name} - {self.feature.name}"
    