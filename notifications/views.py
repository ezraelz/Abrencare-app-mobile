from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from selectors.notification_selector import NotificationSelector
from services.notification_service import NotificationService

class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated,]
    pagination_class = NotificationPagination

    def get_queryset(self):
        return NotificationSelector.for_user(self.request.user)

class NotificationMarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def post(self,request,pk,):
        notification = (
            NotificationSelector.get_user_notification(request.user,pk,)
        )
        NotificationService.mark_read(notification)

        return Response(
            {
                "detail":
                "Notification marked as read."
            },
            status=status.HTTP_200_OK,
        )
    
class NotificationMarkAllReadAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def post(self, request,):
        updated = (
            NotificationService.mark_all_read(
                request.user
            )
        )

        return Response(
            {
                "updated": updated,
            },
            status=status.HTTP_200_OK,
        )
    