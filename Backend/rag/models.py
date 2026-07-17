import os
import uuid

from django.conf import settings
from django.db import models

try:
    from pgvector.django import VectorField as PgVectorField
except ImportError:  # pragma: no cover - optional dependency fallback
    PgVectorField = None


def _get_embedding_field() -> models.Field:
    """Return a pgvector-backed field for PostgreSQL and a JSON fallback for local development."""
    backend = settings.DATABASES.get('default', {}).get('ENGINE', '')
    if backend.endswith('postgresql') and PgVectorField is not None:
        return PgVectorField(dimensions=1536, blank=True, null=True)
    return models.JSONField(default=list, blank=True)


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
    """Stores a chunk of text extracted from a document and its embedding vector."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    embedding = _get_embedding_field()
    embedding_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]
