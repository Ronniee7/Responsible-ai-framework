from __future__ import annotations

import hashlib
import math
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
    """
    Handles PDF ingestion, text extraction, chunking and embedding generation.

    Responsibilities
    ----------------
    - Save uploaded PDFs
    - Extract text while preserving structure
    - Generate semantic chunks
    - Store embeddings
    """

    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 100

    def __init__(self, storage_path: str | None = None):

        self.storage_path = (
            storage_path
            or os.path.join(os.getcwd(), "uploads")
        )

        Path(self.storage_path).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.embedding_service = EmbeddingService()

    ###########################################################################
    # Public API
    ###########################################################################

    def process_upload(
        self,
        file: UploadedFile,
        title: str | None = None,
    ):

        from rag.models import Document

        if not file.name.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported.")

        filename = f"{uuid.uuid4()}_{Path(file.name).name}"

        destination = Path(self.storage_path) / filename

        with destination.open("wb+") as handle:
            for chunk in file.chunks():
                handle.write(chunk)

        document = Document.objects.create(
            id=uuid.uuid4(),
            title=title or Path(file.name).stem,
            filename=Path(file.name).name,
            file_size=destination.stat().st_size,
            uploaded_by=None,
            status="processing",
        )

        self._generate_chunks(
            document=document,
            pdf_path=destination,
        )

        document.status = "ready"
        document.save(update_fields=["status"])

        AuditService.log_event(
            "document_uploaded",
            {
                "document_id": str(document.id),
                "filename": document.filename,
            },
        )

        return document

    ###########################################################################
    # Reprocess
    ###########################################################################

    def reprocess_document(self, document):

        for file in Path(self.storage_path).iterdir():

            if document.filename not in file.name:
                continue

            document.chunks.all().delete()

            self._generate_chunks(
                document=document,
                pdf_path=file,
            )

            document.status = "ready"

            document.save(update_fields=["status"])

            AuditService.log_event(
                "document_reprocessed",
                {
                    "document_id": str(document.id),
                },
            )

            return document

        raise FileNotFoundError(document.filename)

    ###########################################################################
    # Internal
    ###########################################################################

    def _generate_chunks(
        self,
        document,
        pdf_path: Path,
    ):

        pages = self.extract_pages(pdf_path)

        chunk_index = 0

        for page_number, page_text in pages:

            chunks = self.chunk_text(page_text)

            for chunk in chunks:

                DocumentChunk.objects.create(
                    id=uuid.uuid4(),
                    document=document,
                    chunk_index=chunk_index,
                    content=chunk,
                    embedding=self.embedding_service.generate_embedding(
                        chunk
                    ),
                    embedding_metadata={
                        "page": page_number,
                        "source": document.filename,
                        "title": document.title,
                    },
                )

                chunk_index += 1

    ###########################################################################
    # PDF Extraction
    ###########################################################################

    def extract_pages(
        self,
        pdf_path: Path,
    ) -> list[tuple[int, str]]:

        try:

            reader = PdfReader(str(pdf_path))

            pages = []

            for index, page in enumerate(reader.pages):

                text = page.extract_text() or ""

                text = self.clean_text(text)

                if text:

                    pages.append(
                        (
                            index + 1,
                            text,
                        )
                    )

            return pages

        except Exception as exc:

            AuditService.log_event(
                "pdf_processing_error",
                {"error": str(exc)},
            )

            raise ValueError(
                "Unable to process uploaded PDF."
            ) from exc

    ###########################################################################
    # Chunking
    ###########################################################################

    def chunk_text(
        self,
        text: str,
    ) -> list[str]:

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.DEFAULT_CHUNK_SIZE,
            chunk_overlap=self.DEFAULT_CHUNK_OVERLAP,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "; ",
                ", ",
                " ",
                "",
            ],
        )

        return splitter.split_text(text)

    ###########################################################################
    # Cleaning
    ###########################################################################

    def clean_text(
        self,
        text: str,
    ) -> str:

        text = text.replace("\r", "")

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()


###############################################################################
# Embedding Service
###############################################################################


class EmbeddingService:
    """
    Generates embeddings.

    If an OpenAI API key exists,
    OpenAI embeddings are used.

    Otherwise a deterministic local embedding
    is generated as a fallback.
    """

    DIMENSION = 1536

    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
    ):
        self.model_name = model_name

    def generate_embedding(
        self,
        text: str,
    ) -> list[float]:

        text = text.strip()

        if not text:

            return [0.0] * self.DIMENSION

        api_key = os.getenv("OPENAI_API_KEY")

        if api_key:

            try:

                client = OpenAI(api_key=api_key)

                response = client.embeddings.create(
                    model=self.model_name,
                    input=text,
                )

                return list(
                    map(
                        float,
                        response.data[0].embedding,
                    )
                )

            except Exception:

                pass

        return self._fallback_embedding(text)

    ###########################################################################
    # Local fallback
    ###########################################################################

    def _fallback_embedding(
        self,
        text: str,
    ) -> list[float]:

        vector = [0.0] * self.DIMENSION

        words = re.findall(
            r"[A-Za-z0-9]+",
            text.lower(),
        )

        for word in words:

            index = (
                int(
                    hashlib.sha256(
                        word.encode()
                    ).hexdigest()[:8],
                    16,
                )
                % self.DIMENSION
            )

            vector[index] += 1.0

        magnitude = math.sqrt(
            sum(x * x for x in vector)
        )

        if magnitude == 0:

            return vector

        return [
            value / magnitude
            for value in vector
        ]
    
    ###############################################################################
# Retrieval Service
###############################################################################


class RetrievalService:
    """
    Performs semantic retrieval over stored document chunks.
    """

    DEFAULT_LIMIT = 5
    MIN_SIMILARITY = 0.35

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
    ):
        self.embedding_service = (
            embedding_service
            or EmbeddingService()
        )

    ###########################################################################
    # Public API
    ###########################################################################

    def retrieve(
        self,
        question: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, Any]]:

        question_embedding = self.embedding_service.generate_embedding(
            question
        )

        scored_chunks: list[tuple[float, dict[str, Any]]] = []

        chunks = (
            DocumentChunk.objects.select_related("document")
            .filter(document__status="ready")
        )

        for chunk in chunks:
            
            embedding = self._coerce_embedding(
                chunk.embedding
                
            )

            similarity = self.cosine_similarity(
                question_embedding,
                embedding,
            )
            print("=" * 60)
            print("Question:", question)
            print("Chunk:", chunk.chunk_index)
            print("Similarity:", similarity)
            print("Contains STOP:", "stop" in chunk.content.lower())
            print(chunk.content[:120])
            

            print(similarity)
            print(similarity >= self.MIN_SIMILARITY)

            # if similarity < self.MIN_SIMILARITY:
            #     continue

            metadata = chunk.embedding_metadata or {}

            scored_chunks.append(
                (
                    similarity,
                    {
                        "content": chunk.content,
                        "score": similarity,
                        "chunk_index": chunk.chunk_index,
                        "page": metadata.get("page"),
                        "source": metadata.get("source"),
                        "title": metadata.get("title"),
                    },
                )
            )

        scored_chunks.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        results = []
        seen = set()

        for _, chunk in scored_chunks:

            fingerprint = hashlib.sha256(
                chunk["content"].encode()
            ).hexdigest()

            if fingerprint in seen:
                continue

            seen.add(fingerprint)
            results.append(chunk)

            if len(results) >= limit:
                break

        AuditService.log_event(
            "retrieval_completed",
            {
                "question": question,
                "matches": len(results),
                "top_scores": [
                    round(item["score"], 3)
                    for item in results
                ],
            },
        )
        print("Threshold:", self.MIN_SIMILARITY)
        print("Total scored:", len(scored_chunks))
        print("Returned:", len(results))
        return results

    ###########################################################################
    # Helpers
    ###########################################################################

    def _coerce_embedding(
        self,
        embedding: Any,
    ) -> list[float]:

        if isinstance(embedding, list):
            return [float(v) for v in embedding]

        if isinstance(embedding, tuple):
            return [float(v) for v in embedding]

        if isinstance(embedding, dict):
            return [
                float(v)
                for v in embedding.values()
            ]

        return []

    ###########################################################################
    # Cosine Similarity
    ###########################################################################

    @staticmethod
    def cosine_similarity(
        left: list[float],
        right: list[float],
    ) -> float:

        if not left or not right:
            return 0.0

        if len(left) != len(right):
            return 0.0

        dot = sum(
            a * b
            for a, b in zip(left, right)
        )

        left_norm = math.sqrt(
            sum(x * x for x in left)
        )

        right_norm = math.sqrt(
            sum(x * x for x in right)
        )

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return dot / (left_norm * right_norm)


###############################################################################
# Prompt Builder
###############################################################################

class PromptBuilderService:
    """
    Builds an enterprise-grade RAG prompt.
    """

    SYSTEM_PROMPT = """
You are an enterprise AI assistant.

Rules:

1. Answer ONLY using the retrieved document context.

2. If the answer cannot be found inside the context,
reply exactly:

"I could not find this information in the uploaded documents."

3. Never invent policies.

4. Never use outside knowledge.

5. If multiple retrieved chunks disagree,
state that the document contains conflicting information.

6. Always answer in concise professional language.

7. Quote the page number whenever available.
"""


    def build_prompt(
        self,
        question,
        context_chunks=None,
        conversation_history=None
    ):
        """
        Build final RAG prompt using retrieved context.
        """

        retrieved_chunks = context_chunks or []

        history = conversation_history or []

        context_sections = []


        for chunk in retrieved_chunks:

            # Old pipeline:
            # chunk is plain text
            if isinstance(chunk, str):
                context_sections.append(chunk)
                continue


            # New pipeline:
            # chunk is dictionary
            source = chunk.get(
                "source",
                "Unknown"
            )

            page = chunk.get(
                "page",
                "?"
            )

            score = round(
                chunk.get(
                    "score",
                    0
                ),
                3
            )

            content = chunk.get(
                "content",
                ""
            )


            context_sections.append(
                f"""
SOURCE : {source}
PAGE   : {page}
SCORE  : {score}

{content}
""".strip()
            )


        context = (
            "\n\n-------------------------\n\n"
            .join(context_sections)
        )


        if not context:
            context = (
                "No relevant document context was retrieved."
            )


        history_text = (
            "\n".join(history)
            if history
            else "No previous conversation."
        )


        prompt = f"""
{self.SYSTEM_PROMPT}



RETRIEVED DOCUMENTS
========================

{context}

========================
CONVERSATION HISTORY
========================

{history_text}

========================
USER QUESTION
========================

{question}

========================
ASSISTANT ANSWER
========================
"""

        AuditService.log_event(
            "prompt_constructed",
            {
                "question": question,
                "context_chunks": len(retrieved_chunks),
            },
        )

        return prompt