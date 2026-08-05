from django.db import models


class Feature(models.Model):
    feature_name = models.CharField(("Feature Name"), max_length=50)
    description = models.TextField(("Description"), blank=True, null=True)
    created_at = models.DateTimeField(("Created at"), auto_now=False, auto_now_add=True)

    def __str__(self):
        return self.feature_name

class Service(models.Model):
    service_name = models.CharField(("Service Name"), max_length=50)
    service_for = models.CharField(("Service For"), max_length=50)
    features = models.ManyToManyField(Feature, related_name="services")
    description = models.TextField(("Description"), blank=True, null=True)
    created_at = models.DateTimeField(("Created at"), auto_now=False, auto_now_add=True)

    def __str__(self):
        return self.service_name
    
