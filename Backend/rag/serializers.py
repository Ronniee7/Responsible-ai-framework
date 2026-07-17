from rest_framework import serializers


class DocumentUploadSerializer(serializers.Serializer):
    """Validate a PDF upload request."""

    file = serializers.FileField(required=True, allow_empty_file=False)
    title = serializers.CharField(required=False, allow_blank=True)


class DocumentMetadataSerializer(serializers.Serializer):
    """Serialize document metadata for API responses."""

    id = serializers.UUIDField()
    title = serializers.CharField()
    filename = serializers.CharField()
    status = serializers.CharField()
    upload_date = serializers.DateTimeField()
