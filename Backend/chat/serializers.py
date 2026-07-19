from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    """Validate inbound chat requests."""

    message = serializers.CharField(required=True, allow_blank=False)
    provider = serializers.CharField(required=False, allow_blank=True, default="gemini")


class ChatResponseSerializer(serializers.Serializer):
    """Serialize chat responses with full governance metadata for API consumers."""

    response = serializers.CharField()
    provider = serializers.CharField(default="")
    model = serializers.CharField(default="")
    latency = serializers.FloatField(default=0.0)
    token_usage = serializers.DictField(default=dict)
    retrieved_chunks = serializers.ListField(child=serializers.CharField(), default=list)
    retrieved_documents = serializers.ListField(default=list)
    confidence = serializers.DictField(default=dict)
    hallucination_score = serializers.FloatField(default=0.0)
    bias_score = serializers.FloatField(default=0.0)
    toxicity_score = serializers.FloatField(default=0.0)
    policy_compliant = serializers.BooleanField(default=True)
    requires_human_review = serializers.BooleanField(default=False)
    governance_summary = serializers.DictField(default=dict)
    explanation = serializers.DictField(default=dict)

    # Backward-compatible fields
    governance = serializers.DictField(default=dict)