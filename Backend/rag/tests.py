from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from pypdf import PdfWriter

from rag.services import (
    DocumentProcessingService,
    EmbeddingService,
    PromptBuilderService,
    RetrievalService,
)


class RAGPipelineTests(TestCase):
    def setUp(self) -> None:
        self.processing_service = DocumentProcessingService()
        self.embedding_service = EmbeddingService()
        self.retrieval_service = RetrievalService(embedding_service=self.embedding_service)
        self.prompt_builder = PromptBuilderService()

    def test_pdf_upload_creates_document_and_chunks(self) -> None:
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf_bytes = BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)

        uploaded_file = SimpleUploadedFile(
            "policy.pdf",
            pdf_bytes.getvalue(),
            content_type="application/pdf",
        )

        document = self.processing_service.process_upload(uploaded_file, title="Policy guide")

        self.assertEqual(document.title, "Policy guide")
        self.assertEqual(document.filename, "policy.pdf")
        self.assertEqual(document.status, "ready")
        self.assertGreater(document.chunks.count(), 0)

    def test_chunk_creation_splits_large_text(self) -> None:
        text = " ".join([f"policy paragraph {index}" for index in range(80)])
        chunks = self.processing_service.chunk_text(text)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(chunk for chunk in chunks))

    def test_document_chunks_store_embedding_vectors(self) -> None:
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        pdf_bytes = BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)

        uploaded_file = SimpleUploadedFile(
            "policy.pdf",
            pdf_bytes.getvalue(),
            content_type="application/pdf",
        )

        document = self.processing_service.process_upload(uploaded_file, title="Policy guide")
        first_chunk = document.chunks.order_by("chunk_index").first()

        self.assertIsNotNone(first_chunk)
        self.assertTrue(first_chunk.embedding)
        self.assertEqual(len(first_chunk.embedding), 1536)

    def test_embedding_generation_returns_vectors(self) -> None:
        embedding = self.embedding_service.generate_embedding("customer refund policy")

        self.assertEqual(len(embedding), 1536)
        self.assertTrue(all(isinstance(value, float) for value in embedding))

    def test_retrieval_returns_top_relevant_chunks(self) -> None:
        documents = [
            "Customer support should never share passwords.",
            "Refunds take up to five business days.",
            "The company policy covers warranty claims.",
        ]
        chunks = []
        for index, document in enumerate(documents):
            chunk = self.retrieval_service._build_chunk(document, index=index)
            self.retrieval_service.chunk_store[chunk["content"]] = chunk["embedding"]
            chunks.append(chunk)

        results = self.retrieval_service.retrieve("How do I protect customer passwords?", limit=3)

        self.assertTrue(results)
        self.assertEqual(results[0]["content"], "Customer support should never share passwords.")

    def test_prompt_builder_formats_context_for_llm(self) -> None:
        prompt = self.prompt_builder.build_prompt(
            question="What is the refund policy?",
            context_chunks=["Refunds take five business days.", "Warranty claims require proof of purchase."],
            conversation_history=["User asked about support coverage."],
        )

        self.assertIn("System prompt", prompt)
        self.assertIn("Retrieved context", prompt)
        self.assertIn("Conversation history", prompt)
        self.assertIn("User question", prompt)
