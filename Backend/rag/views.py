from __future__ import annotations

import uuid

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services import AuditService
from rag.models import Document, DocumentChunk
from rag.serializers import (
    DocumentListSerializer,
    DocumentMetadataSerializer,
    DocumentSearchSerializer,
    DocumentUploadSerializer,
)
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


class DocumentListView(APIView):
    """List all uploaded documents with metadata."""

    @extend_schema(
        responses={200: DocumentListSerializer(many=True)},
        description="List all uploaded documents with chunk counts and status.",
    )
    def get(self, request, *args, **kwargs):
        documents = Document.objects.all()
        serializer = DocumentListSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentDetailView(APIView):
    """Retrieve, delete, or reprocess a specific document."""

    def _get_document(self, doc_id: str) -> Document | None:
        try:
            return Document.objects.get(id=uuid.UUID(doc_id))
        except (ValueError, Document.DoesNotExist):
            return None

    @extend_schema(
        responses={200: DocumentMetadataSerializer},
        description="Retrieve detailed metadata for a specific document.",
    )
    def get(self, request, doc_id: str, *args, **kwargs):
        document = self._get_document(doc_id)
        if not document:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = DocumentMetadataSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={204: None},
        description="Delete a document and all its chunks.",
    )
    def delete(self, request, doc_id: str, *args, **kwargs):
        document = self._get_document(doc_id)
        if not document:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        AuditService.log_event(
            "document_deleted",
            {"document_id": str(document.id), "title": document.title, "chunk_count": document.chunk_count},
        )
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentReprocessView(APIView):
    """Reprocess a document to regenerate chunks and embeddings."""

    @extend_schema(
        responses={200: DocumentMetadataSerializer},
        description="Reprocess a document to regenerate chunks and embeddings.",
    )
    def post(self, request, doc_id: str, *args, **kwargs):
        try:
            document = Document.objects.get(id=uuid.UUID(doc_id))
        except (ValueError, Document.DoesNotExist):
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        # Delete existing chunks
        DocumentChunk.objects.filter(document=document).delete()

        # Reprocess
        document.status = "processing"
        document.save(update_fields=["status"])

        service = DocumentProcessingService()
        try:
            document = service.reprocess_document(document)
            serializer = DocumentMetadataSerializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            document.status = "error"
            document.save(update_fields=["status"])
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentStatusView(APIView):
    """Check the processing status of a document."""

    @extend_schema(
        responses={200: dict},
        description="Check the processing status of a document.",
    )
    def get(self, request, doc_id: str, *args, **kwargs):
        try:
            document = Document.objects.get(id=uuid.UUID(doc_id))
        except (ValueError, Document.DoesNotExist):
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "id": str(document.id),
                "status": document.status,
                "chunk_count": document.chunk_count,
                "embedding_count": document.embedding_count,
            },
            status=status.HTTP_200_OK,
        )


class DocumentSearchView(APIView):
    """Search across document titles and content."""

    @extend_schema(
        request=DocumentSearchSerializer,
        responses={200: DocumentListSerializer(many=True)},
        description="Search documents by title or filename.",
    )
    def post(self, request, *args, **kwargs):
        serializer = DocumentSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data["query"].lower()
        limit = serializer.validated_data["limit"]

        documents = Document.objects.filter(
            title__icontains=query,
        ) | Document.objects.filter(
            filename__icontains=query,
        )

        documents = documents.distinct()[:limit]
        result_serializer = DocumentListSerializer(documents, many=True)
        return Response(result_serializer.data, status=status.HTTP_200_OK)