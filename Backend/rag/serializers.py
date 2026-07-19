from rest_framework import serializers

from rag.models import Document


class DocumentUploadSerializer(serializers.Serializer):
    """Validate a PDF upload request."""

    file = serializers.FileField(required=True, allow_empty_file=False)
    title = serializers.CharField(required=False, allow_blank=True)
    dataset = serializers.CharField(required=False, allow_blank=True, default="default")
    language = serializers.CharField(required=False, allow_blank=True, default="en")


class DocumentMetadataSerializer(serializers.ModelSerializer):
    """Serialize document metadata for API responses."""

    chunk_count = serializers.IntegerField(read_only=True)
    embedding_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "filename",
            "file_size",
            "status",
            "upload_date",
            "chunk_count",
            "embedding_count",
            "dataset",
            "language",
        ]


class DocumentListSerializer(serializers.ModelSerializer):
    """Serialize a list of documents with summary fields."""

    chunk_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "filename",
            "file_size",
            "status",
            "upload_date",
            "chunk_count",
            "dataset",
            "language",
        ]


class DocumentSearchSerializer(serializers.Serializer):
    """Validate document search requests."""

    query = serializers.CharField(required=True, allow_blank=False)
    limit = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)