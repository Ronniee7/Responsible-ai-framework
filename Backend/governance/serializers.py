from rest_framework import serializers

from governance.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serialize review items for the human-in-the-loop workflow."""

    class Meta:
        model = Review
        fields = [
            "id",
            "question",
            "retrieved_chunks",
            "ai_response",
            "edited_response",
            "governance_metrics",
            "reviewer_comments",
            "status",
            "created_at",
            "updated_at",
            "reviewed_by",
            "reviewed_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ReviewActionSerializer(serializers.Serializer):
    """Validate review actions (approve, reject, edit)."""

    action = serializers.ChoiceField(choices=["approved", "rejected", "edited"])
    reviewer_comments = serializers.CharField(required=False, allow_blank=True, default="")
    edited_response = serializers.CharField(required=False, allow_blank=True, default="")
    reviewed_by = serializers.CharField(required=False, allow_blank=True, default="")