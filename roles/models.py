from django.db import models


class Role(models.Model):
    role_name = models.CharField(("Role Name"), max_length=50)
    description = models.TextField(("Description"), blank=True, null=True)
    is_active = models.BooleanField(
        default=True,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.role_name
