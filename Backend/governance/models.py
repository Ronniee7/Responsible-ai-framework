import uuid

from django.db import models


class Review(models.Model):
    """
    Stores pending human review items flagged by the governance pipeline.

    When governance requires review, a Review record is created with:
    - the original question
    - retrieved chunks
    - AI response
    - governance metrics
    - timestamp
    """

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("edited", "Edited"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    retrieved_chunks = models.JSONField(default=list, blank=True)
    ai_response = models.TextField()
    edited_response = models.TextField(blank=True, default="")
    governance_metrics = models.JSONField(default=dict, blank=True)
    reviewer_comments = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.CharField(max_length=255, blank=True, default="")
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self) -> str:
        return f"Review {self.id} - {self.status} - {self.question[:60]}"