from django.urls import path

from .views import (
    FeatureDetailAPIView,
    FeatureListCreateAPIView,
    FeatureRestoreAPIView,
    ServiceDetailAPIView,
    ServiceListCreateAPIView,
    ServiceReorderFeaturesAPIView,
    ServiceRestoreAPIView,
)

urlpatterns = [
    path("features/", FeatureListCreateAPIView.as_view(), name="feature-list"),
    path("features/<int:pk>/", FeatureDetailAPIView.as_view(), name="feature-detail"),
    path(
        "features/<int:pk>/restore/",
        FeatureRestoreAPIView.as_view(),
        name="feature-restore",
    ),
    path("services/", ServiceListCreateAPIView.as_view(), name="service-list"),
    path("services/<int:pk>/", ServiceDetailAPIView.as_view(), name="service-detail"),
    path(
        "services/<int:pk>/restore/",
        ServiceRestoreAPIView.as_view(),
        name="service-restore",
    ),
    path(
        "services/<int:pk>/reorder-features/",
        ServiceReorderFeaturesAPIView.as_view(),
        name="service-reorder-features",
    ),
]
