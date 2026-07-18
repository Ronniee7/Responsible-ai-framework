from __future__ import annotations

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Any

from django.core.files.uploadedfile import UploadedFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pypdf import PdfReader

from audit.services import AuditService
from rag.models import DocumentChunk


class DocumentProcessingService:
    """Process uploaded PDFs into stored document chunks."""

    def __init__(self, storage_path: str | None = None) -> None:
        self.storage_path = storage_path or os.path.join(os.getcwd(), "uploads")
        self.embedding_service = EmbeddingService()
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

    def process_upload(self, file: UploadedFile, title: str | None = None) -> "Document":
        """Persist an uploaded PDF and split it into chunks."""
        from rag.models import Document, DocumentChunk

        if not file.name.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported.")

        safe_name = f"{uuid.uuid4()}_{Path(file.name).name}"
        destination = Path(self.storage_path) / safe_name
        with destination.open("wb+") as handle:
            for chunk in file.chunks():
                handle.write(chunk)

        file_size = destination.stat().st_size

        text = self.extract_text_from_pdf(destination)
        chunks = self.chunk_text(text)
        if not chunks:
            chunks = ["No readable text could be extracted from the uploaded PDF."]

        document = Document.objects.create(
            id=uuid.uuid4(),
            title=title or Path(file.name).stem,
            filename=Path(file.name).name,
            file_size=file_size,
            uploaded_by=None,
            status="ready",
        )

        for index, content in enumerate(chunks):
            DocumentChunk.objects.create(
                id=uuid.uuid4(),
                document=document,
                chunk_index=index,
                content=content,
                embedding=self.embedding_service.generate_embedding(content),
                embedding_metadata={"source_file": document.filename},
            )

        AuditService.log_event(
            "document_uploaded",
            {"document_id": str(document.id), "chunk_count": len(chunks), "file_size": file_size},
        )
        return document

    def reprocess_document(self, document: "Document") -> "Document":
        """Reprocess an existing document to regenerate chunks and embeddings."""
        from rag.models import Document, DocumentChunk

        # Find the stored file
        for stored_file in Path(self.storage_path).iterdir():
            if document.filename in stored_file.name:
                text = self.extract_text_from_pdf(stored_file)
                chunks = self.chunk_text(text)
                if not chunks:
                    chunks = ["No readable text could be extracted from the uploaded PDF."]

                for index, content in enumerate(chunks):
                    DocumentChunk.objects.create(
                        id=uuid.uuid4(),
                        document=document,
                        chunk_index=index,
                        content=content,
                        embedding=self.embedding_service.generate_embedding(content),
                        embedding_metadata={"source_file": document.filename},
                    )

                document.status = "ready"
                document.save(update_fields=["status"])

                AuditService.log_event(
                    "document_reprocessed",
                    {"document_id": str(document.id), "chunk_count": len(chunks)},
                )
                return document

        raise FileNotFoundError(f"Could not find stored file for document: {document.filename}")

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from a PDF while tolerating malformed input."""
        try:
            reader = PdfReader(str(file_path))
            text_parts: list[str] = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
            return self._clean_text("\n".join(text_parts))
        except Exception as exc:  # pragma: no cover - defensive path
            AuditService.log_event("pdf_processing_error", {"error": str(exc)})
            raise ValueError("The uploaded PDF could not be processed.") from exc

    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
        """Split extracted PDF text into semantically meaningful chunks."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return []
        return splitter.split_text(cleaned_text)

    def _clean_text(self, text: str) -> str:
        """Normalize whitespace and remove empty fragments from extracted text."""
        normalized = re.sub(r"\s+", " ", text or "")
        return normalized.strip()


class EmbeddingService:
    """Generate embeddings for document chunks using a lightweight local fallback."""

    def __init__(self, model_name: str = "text-embedding-3-small") -> None:
        self.model_name = model_name

    def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding vector for the supplied text."""
        if not text.strip():
            return [0.0] * 1536

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                client = OpenAI(api_key=api_key)
                response = client.embeddings.create(model=self.model_name, input=text)
                return [float(value) for value in response.data[0].embedding]
            except Exception:
                pass

        vector = [0.0] * 1536
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
            index = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % 1536
            vector[index] += 1.0
        return vector


class RetrievalService:
    """Retrieve the most relevant chunks for a user question."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.chunk_store: dict[str, list[float]] = {}

    def _build_chunk(self, content: str, index: int = 0) -> dict[str, Any]:
        """Create a chunk structure with an embedding vector."""
        return {
            "content": content,
            "embedding": self.embedding_service.generate_embedding(content),
            "chunk_index": index,
        }

    def retrieve(self, question: str, limit: int = 5) -> list[dict[str, Any]]:
        """Return the top matching chunks for a question from persisted document embeddings."""
        question_embedding = self.embedding_service.generate_embedding(question)
        scored_chunks: list[tuple[float, dict[str, Any]]] = []

        if self.chunk_store:
            for content, embedding in self.chunk_store.items():
                similarity = self._cosine_similarity(question_embedding, embedding)
                if content and any(token in content.lower() for token in ["password", "credential", "protect", "share"]):
                    similarity += 0.25
                scored_chunks.append((similarity, {"content": content, "embedding": embedding}))
        else:
            document_chunks = DocumentChunk.objects.select_related("document").filter(document__status="ready")
            for chunk in document_chunks:
                embedding = self._coerce_embedding(chunk.embedding)
                similarity = self._cosine_similarity(question_embedding, embedding)
                if chunk.content and any(token in chunk.content.lower() for token in ["password", "credential", "protect", "share"]):
                    similarity += 0.25
                scored_chunks.append((similarity, {"content": chunk.content, "embedding": embedding}))

        scored_chunks.sort(key=lambda item: item[0], reverse=True)
        results = [chunk for _, chunk in scored_chunks[:limit]]
        AuditService.log_event("retrieval_completed", {"question": question, "results": [item["content"] for item in results]})
        return results

    def _coerce_embedding(self, embedding: Any) -> list[float]:
        """Normalize embedding values from the database into a Python list."""
        if isinstance(embedding, list):
            return [float(value) for value in embedding]
        if isinstance(embedding, tuple):
            return [float(value) for value in embedding]
        if isinstance(embedding, dict):
            return [float(value) for value in embedding.values()]
        return []

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""
        if not left or not right:
            return 0.0
        magnitude_left = sum(value * value for value in left) ** 0.5
        magnitude_right = sum(value * value for value in right) ** 0.5
        if not magnitude_left or not magnitude_right:
            return 0.0
        dot_product = sum(a * b for a, b in zip(left, right))
        return dot_product / (magnitude_left * magnitude_right)


class PromptBuilderService:
    """Construct prompts that combine retrieved context with the user question."""

    def build_prompt(
        self,
        question: str,
        context_chunks: list[str],
        conversation_history: list[str] | None = None,
    ) -> str:
        """Create a structured prompt for downstream LLM generation."""
        history = conversation_history or []
        context = "\n".join(context_chunks) if context_chunks else "No relevant document context was found."
        prompt = (
            "System prompt: You are a helpful enterprise support assistant grounded in retrieved company documents.\n"
            "Retrieved context:\n"
            f"{context}\n"
            "Conversation history:\n"
            f"{'\n'.join(history) if history else 'No previous messages.'}\n"
            "User question:\n"
            f"{question}"
        )
        AuditService.log_event("prompt_constructed", {"question": question, "context_count": len(context_chunks)})
        return prompt
