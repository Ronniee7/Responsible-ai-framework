from django.urls import path

from governance.views import (
    ReviewActionView,
    ReviewDetailView,
    ReviewListView,
    ReviewQueueSizeView,
)

urlpatterns = [
    path("reviews/", ReviewListView.as_view(), name="review-list"),
    path("reviews/queue-size/", ReviewQueueSizeView.as_view(), name="review-queue-size"),
    path("reviews/<uuid:review_id>/", ReviewDetailView.as_view(), name="review-detail"),
    path("reviews/<uuid:review_id>/action/", ReviewActionView.as_view(), name="review-action"),
]