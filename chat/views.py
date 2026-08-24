from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
)

from .serializers import (
    ConversationSerializer,
    MessageSerializer,
)

from .services.conversation_services import (
    ConversationService,
)

User = get_user_model()

class ConversationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = (
            Conversation.objects
            .filter(
                participants__user=request.user
            )
            .prefetch_related(
                "participants__user"
            )
            .distinct()
            .order_by("-updated_at")
        )

        serializer = ConversationSerializer(
            conversations,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        conversation_type = request.data.get(
            "conversation_type",
            "private",
        )

        if conversation_type == "private":
            other_user_id = request.data.get(
                "user_id"
            )

            if not other_user_id:
                return Response(
                    {
                        "detail": "user_id is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                other_user = User.objects.get(
                    id=other_user_id
                )
            except User.DoesNotExist:
                return Response(
                    {
                        "detail": "User not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                conversation = (
                    ConversationService
                    .create_private_conversation(
                        user=request.user,
                        other_user=other_user,
                    )
                )

            except ValueError as exc:
                return Response(
                    {
                        "detail": str(exc)
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            name = request.data.get("name")

            participant_ids = request.data.get(
                "participant_ids",
                [],
            )

            if not name:
                return Response(
                    {
                        "detail": "Group name is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not isinstance(
                participant_ids,
                list,
            ):
                return Response(
                    {
                        "detail": (
                            "participant_ids must be a list."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            conversation = (
                ConversationService
                .create_group_conversation(
                    user=request.user,
                    name=name,
                    participant_ids=participant_ids,
                )
            )

        serializer = ConversationSerializer(
            conversation
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_conversation(self, request, pk):
        try:
            conversation = (
                Conversation.objects
                .prefetch_related(
                    "participants__user"
                )
                .get(
                    id=pk,
                    participants__user=request.user,
                )
            )

            return conversation

        except Conversation.DoesNotExist:
            return None

    def get(self, request, pk):
        conversation = self.get_conversation(
            request,
            pk,
        )

        if not conversation:
            return Response(
                {
                    "detail": "Conversation not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ConversationSerializer(
            conversation
        )

        return Response(serializer.data)


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        is_participant = (
            ConversationParticipant.objects
            .filter(
                conversation_id=pk,
                user=request.user,
            )
            .exists()
        )
        if not is_participant:
            return Response(
                {
                    "detail": "Conversation not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = (
            Message.objects
            .filter(
                conversation_id=pk,
            )
            .select_related(
                "sender"
            )
            .order_by("created_at")
        )

        serializer = MessageSerializer(
            messages,
            many=True,
        )

        return Response(serializer.data)
    