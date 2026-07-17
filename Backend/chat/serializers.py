from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    """Validate inbound chat requests."""

    message = serializers.CharField(required=True, allow_blank=False)


class ChatResponseSerializer(serializers.Serializer):
    """Serialize chat responses for API consumers."""

    response = serializers.CharField()
    explanation = serializers.CharField()
    governance = serializers.DictField()
