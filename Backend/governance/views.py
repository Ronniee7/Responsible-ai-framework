from datetime import datetime, timezone

from django.utils import timezone as django_timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services import AuditService
from governance.models import Review
from governance.serializers import ReviewActionSerializer, ReviewSerializer


class ReviewListView(APIView):
    """List pending and historical review items."""

    @extend_schema(
        responses={200: ReviewSerializer(many=True)},
        description="List all review items, with optional status filter.",
    )
    def get(self, request, *args, **kwargs):
        status_filter = request.query_params.get("status")
        if status_filter and status_filter in dict(Review.STATUS_CHOICES):
            reviews = Review.objects.filter(status=status_filter)
        else:
            reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewDetailView(APIView):
    """View details of a specific review item."""

    def _get_review(self, review_id: str) -> Review | None:
        try:
            import uuid
            return Review.objects.get(id=uuid.UUID(review_id))
        except (ValueError, Review.DoesNotExist):
            return None

    @extend_schema(
        responses={200: ReviewSerializer},
        description="Retrieve a specific review item.",
    )
    def get(self, request, review_id: str, *args, **kwargs):
        review = self._get_review(review_id)
        if not review:
            return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewActionView(APIView):
    """Approve, reject, or edit a review item."""

    def _get_review(self, review_id: str) -> Review | None:
        try:
            import uuid
            return Review.objects.get(id=uuid.UUID(review_id))
        except (ValueError, Review.DoesNotExist):
            return None

    @extend_schema(
        request=ReviewActionSerializer,
        responses={200: ReviewSerializer},
        description="Perform an action on a review item (approve/reject/edit).",
    )
    def post(self, request, review_id: str, *args, **kwargs):
        review = self._get_review(review_id)
        if not review:
            return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        if review.status != "pending":
            return Response(
                {"error": "This review has already been processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        review.status = action
        review.reviewed_at = django_timezone.now()

        if serializer.validated_data.get("reviewer_comments"):
            review.reviewer_comments = serializer.validated_data["reviewer_comments"]

        if serializer.validated_data.get("reviewed_by"):
            review.reviewed_by = serializer.validated_data["reviewed_by"]

        if action == "edited" and serializer.validated_data.get("edited_response"):
            review.edited_response = serializer.validated_data["edited_response"]

        review.save()

        AuditService.log_event(
            "review_action_completed",
            {
                "review_id": str(review.id),
                "action": action,
                "reviewed_by": serializer.validated_data.get("reviewed_by", "unknown"),
            },
        )

        result_serializer = ReviewSerializer(review)
        return Response(result_serializer.data, status=status.HTTP_200_OK)


class ReviewQueueSizeView(APIView):
    """Return the current size of the pending review queue."""

    @extend_schema(
        responses={200: dict},
        description="Return the count of pending reviews.",
    )
    def get(self, request, *args, **kwargs):
        count = Review.objects.filter(status="pending").count()
        return Response({"pending_count": count}, status=status.HTTP_200_OK)