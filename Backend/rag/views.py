from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from rag.serializers import DocumentMetadataSerializer, DocumentUploadSerializer
from rag.services import DocumentProcessingService


class DocumentUploadView(APIView):
    """Upload a PDF document and create a searchable document record."""

    parser_classes = (MultiPartParser,)

    @extend_schema(
        request=DocumentUploadSerializer,
        responses={201: DocumentMetadataSerializer},
        description="Upload and process a PDF document for retrieval-augmented generation.",
    )
    def post(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DocumentProcessingService()
        document = service.process_upload(
            serializer.validated_data["file"],
            title=serializer.validated_data.get("title") or None,
        )
        payload = DocumentMetadataSerializer(document).data
        return Response(payload, status=status.HTTP_201_CREATED)
