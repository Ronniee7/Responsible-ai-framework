from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.serializers import ChatRequestSerializer, ChatResponseSerializer
from chat.services import ChatService


class ChatView(APIView):
    """Handle chat requests and return a governance-aware response."""

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ChatService()
        result = service.generate_response(serializer.validated_data["message"])
        payload = ChatResponseSerializer(result.__dict__).data
        return Response(payload, status=status.HTTP_200_OK)
