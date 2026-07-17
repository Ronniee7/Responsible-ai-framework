import uuid

from django.conf import settings
from django.db import models


class Document(models.Model):
    """Represents an uploaded enterprise document available to the RAG pipeline."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="processing")

    class Meta:
        ordering = ["-upload_date"]


class DocumentChunk(models.Model):
    """Stores a chunk of text extracted from a document."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    embedding_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]
