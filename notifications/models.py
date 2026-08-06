from django.db import models
from accounts.models import User
import uuid

class NotificationType(models.TextChoices):
    APPOINTMENT = ("appointment","Appointment",)
    PRESCRIPTION = ("prescription","Prescription",)
    PAYMENT = ("payment","Payment",)
    CHAT = ("chat","Chat",)
    SYSTEM = ("system","System",)

class Notification(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True,blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="notifications")
    title = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    notification_type = models.CharField(max_length=20,choices=NotificationType.choices, default=NotificationType.SYSTEM,)
    is_read = models.BooleanField(default=False)
    action_url = models.CharField(max_length=255,blank=True,)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True,)
    read_at = models.DateTimeField(null=True,blank=True)

    class Meta:
        ordering = [ "-created_at",]
        indexes = [
            models.Index(fields=["user","-created_at",]),
            models.Index(fields=["user","is_read",]),
            models.Index(fields=["notification_type",]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def to_payload(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.notification_type,
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read,
            "data": self.data,
        }
    