"""
DRF API views for the service catalog, written as plain APIView subclasses
(rather than ModelViewSet) for cases where you want explicit control over
routing and per-endpoint behavior.

- GET endpoints are public (read-only for anonymous users) since this is
  catalog/marketing data, not PHI.
- Staff-only actions (create/update/delete/restore/reorder) are gated by
  IsStaffOrReadOnly — swap for a stricter permission if your roles are
  more granular than `is_staff`.
- Staff see soft-deleted/inactive rows too (via `all_objects`); everyone
  else only sees the live catalog (via the default `objects` manager).
- List views prefetch/filter/search/order manually since APIView (unlike
  GenericAPIView) doesn't apply filter_backends automatically.
"""

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .filters import ServiceFilter
from .models import Feature, Service
from .permissions import IsStaffOrReadOnly
from .serializers import (
    FeatureSerializer,
    FeatureWriteSerializer,
    ServiceDetailSerializer,
    ServiceListSerializer,
    ServiceWriteSerializer,
)


def _is_staff(request) -> bool:
    return bool(request.user and request.user.is_staff)


class CatalogPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


def _apply_filters(request, view, queryset, filter_backends):
    """Runs a list of DRF filter backends against a queryset manually,
    since plain APIView doesn't do this for us like GenericAPIView does."""
    for backend in filter_backends:
        queryset = backend().filter_queryset(request, queryset, view)
    return queryset


# ---------------------------------------------------------------------------
# Feature views
# ---------------------------------------------------------------------------


class FeatureListCreateAPIView(APIView):
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    pagination_class = CatalogPagination

    def get(self, request):
        manager = Feature.all_objects if _is_staff(request) else Feature.objects
        queryset = _apply_filters(request, self, manager.all(), self.filter_backends)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = FeatureSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = FeatureWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feature = Feature.objects.create(
            **serializer.validated_data,
            created_by=request.user,
            updated_by=request.user,
        )
        return Response(FeatureSerializer(feature).data, status=status.HTTP_201_CREATED)


class FeatureDetailAPIView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get_object(self, request, pk):
        manager = Feature.all_objects if _is_staff(request) else Feature.objects
        return get_object_or_404(manager, pk=pk)

    def get(self, request, pk):
        feature = self.get_object(request, pk)
        return Response(FeatureSerializer(feature).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        feature = self.get_object(request, pk)
        serializer = FeatureWriteSerializer(feature, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(feature, field, value)
        feature.updated_by = request.user
        feature.save()
        return Response(FeatureSerializer(feature).data)

    def delete(self, request, pk):
        feature = self.get_object(request, pk)
        services.soft_delete_feature(feature=feature, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeatureRestoreAPIView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def post(self, request, pk):
        feature = get_object_or_404(Feature.all_objects, pk=pk)
        services.restore_feature(feature=feature, user=request.user)
        return Response(FeatureSerializer(feature).data)


# ---------------------------------------------------------------------------
# Service views
# ---------------------------------------------------------------------------


class ServiceListCreateAPIView(APIView):
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ["name", "description", "code"]
    ordering_fields = ["name", "created_at"]
    pagination_class = CatalogPagination

    def get(self, request):
        manager = Service.all_objects if _is_staff(request) else Service.objects
        queryset = manager.all().prefetch_related("service_features__feature")
        queryset = _apply_filters(request, self, queryset, self.filter_backends)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ServiceListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ServiceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        features = serializer.validated_data.pop("features", [])
        service = services.create_service(
            data=serializer.validated_data, features=features, user=request.user
        )
        return Response(ServiceDetailSerializer(service).data, status=status.HTTP_201_CREATED)


class ServiceDetailAPIView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get_object(self, request, pk):
        manager = Service.all_objects if _is_staff(request) else Service.objects
        return get_object_or_404(
            manager.prefetch_related("service_features__feature"), pk=pk
        )

    def get(self, request, pk):
        service = self.get_object(request, pk)
        return Response(ServiceDetailSerializer(service).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        service = self.get_object(request, pk)
        serializer = ServiceWriteSerializer(service, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        features = serializer.validated_data.pop("features", None)
        service = services.update_service(
            service=service,
            data=serializer.validated_data,
            features=features,
            user=request.user,
        )
        return Response(ServiceDetailSerializer(service).data)

    def delete(self, request, pk):
        service = self.get_object(request, pk)
        services.soft_delete_service(service=service, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceRestoreAPIView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def post(self, request, pk):
        service = get_object_or_404(Service.all_objects, pk=pk)
        services.restore_service(service=service, user=request.user)
        return Response(ServiceDetailSerializer(service).data)


class ServiceReorderFeaturesAPIView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def post(self, request, pk):
        manager = Service.all_objects if _is_staff(request) else Service.objects
        service = get_object_or_404(manager, pk=pk)

        ordered_ids = request.data.get("feature_ids", [])
        if not isinstance(ordered_ids, list) or not ordered_ids:
            return Response(
                {"detail": "feature_ids must be a non-empty list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            services.reorder_service_features(
                service=service, ordered_feature_ids=ordered_ids
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        service.refresh_from_db()
        return Response(ServiceDetailSerializer(service).data)
    