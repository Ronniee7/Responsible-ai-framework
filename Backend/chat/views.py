from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.serializers import ChatRequestSerializer, ChatResponseSerializer
from chat.services import ChatService


class ChatView(APIView):
    """Handle chat requests and return a governance-aware response with full metadata."""

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        message = validated_data["message"]
        provider_name = validated_data.get("provider", "openai")

        service = ChatService(provider_name=provider_name)
        result = service.generate_response(message)

        # Use the result as a dict for the serializer
        payload = ChatResponseSerializer(result.__dict__).data
        return Response(payload, status=status.HTTP_200_OK)