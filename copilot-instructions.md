# GitHub Copilot Project Instructions

# Project Overview

You are assisting in the development of a Master's research project titled:

**Responsible Generative AI for Customer Service: A Governance-Integrated Framework for Trustworthy Enterprise AI**

The objective is to build an enterprise-grade AI-powered customer service platform that integrates Retrieval-Augmented Generation (RAG), Responsible AI governance, Explainable AI, audit logging, and human oversight into a modular software architecture.

The project must demonstrate production-quality software engineering practices while serving as the implementation artifact for an academic research thesis.

---

# Project Goals

The system should:

- Answer customer questions using enterprise knowledge.
- Retrieve relevant documents using Retrieval-Augmented Generation (RAG).
- Generate responses using OpenAI GPT-4.1.
- Evaluate every generated response before returning it.
- Detect hallucinations.
- Detect potentially biased responses.
- Detect toxic content.
- Validate organizational policy compliance.
- Generate explanations for every AI response.
- Log every interaction for auditing.
- Support future human review workflows.
- Be modular and extensible.

Governance is a runtime component of the inference pipeline, NOT a post-processing step.

---

# Technology Stack

## Frontend

- Next.js (App Router)
- React
- TypeScript
- Tailwind CSS
- React Query
- Axios
- React Hook Form

---

## Backend

- Python 3.13
- Django
- Django REST Framework
- JWT Authentication
- DRF Spectacular
- Django Filter

---

## Database

PostgreSQL

Extensions

- pgvector

Primary keys

- UUID

---

## AI Stack

- OpenAI GPT-4.1
- LangChain
- LangChain OpenAI
- LangChain Community
- LangChain Text Splitters

---

## Document Processing

- PyPDF

---

## Background Tasks

- Celery
- Redis

---

## Containerization

- Docker
- Docker Compose

---

# Software Architecture

The architecture follows a layered design.

Presentation Layer

↓

Application Layer

↓

Domain Layer

↓

Infrastructure Layer

Each layer must be independent.

Business logic should NEVER appear inside API views.

Views should only:

- validate input
- call services
- serialize responses

---

# Backend Modules

authentication/

Responsible for:

- registration
- login
- JWT
- refresh tokens
- permissions

---

users/

Responsible for:

- profiles
- roles
- account management

---

chat/

Responsible for:

- conversations
- messages
- chat history
- session management

---

rag/

Responsible for:

- PDF upload
- document parsing
- chunking
- embeddings
- vector search
- retrieval
- prompt context generation

---

governance/

Responsible for:

- hallucination detection
- bias detection
- toxicity detection
- policy compliance
- confidence scoring

---

explainability/

Responsible for:

- explanation generation
- retrieved sources
- confidence levels
- reasoning summaries

---

audit/

Responsible for:

- prompt logging
- retrieved documents
- AI responses
- governance results
- timestamps
- user actions

---

monitoring/

Responsible for:

- performance metrics
- latency
- health checks
- monitoring endpoints

---

api/

Responsible for:

- routing
- serializers
- endpoint registration

---

# Coding Standards

Always follow:

- SOLID principles
- Clean Architecture
- Clean Code
- DRY
- KISS
- Separation of Concerns

Avoid:

- duplicated code
- fat views
- giant models
- deeply nested functions
- magic numbers
- hardcoded secrets

---

# Python Standards

Always:

- Use Python type hints.
- Follow PEP8.
- Use dataclasses where appropriate.
- Use Enums instead of string literals.
- Use UUID primary keys.
- Write meaningful variable names.
- Use descriptive function names.
- Write Google-style docstrings.

Example:

def upload_document(file: UploadedFile) -> Document:
    """
    Upload and process an enterprise document.

    Args:
        file:
            Uploaded PDF document.

    Returns:
        Stored Document instance.
    """

---

# Django Standards

Always:

- Use class-based views when appropriate.
- Keep business logic inside services.
- Use serializers.
- Use model managers when useful.
- Keep settings modular.
- Validate all inputs.
- Return consistent API responses.

---

# API Standards

Every endpoint must include:

- validation
- authentication
- error handling
- logging
- documentation

Use RESTful naming.

Examples

GET /api/chat/

POST /api/chat/

GET /api/documents/

POST /api/documents/

---

# Database Standards

Every model must include:

- UUID id
- created_at
- updated_at

Relationships should use ForeignKey with related_name.

Indexes should be added where beneficial.

---

# Logging

Every important action must be logged.

Examples

User logged in

Document uploaded

Embedding created

Prompt sent

LLM response received

Governance check passed

Governance check failed

Audit record stored

---

# Error Handling

Never silently ignore errors.

Raise meaningful exceptions.

Return descriptive API errors.

Always log exceptions.

---

# Security

Never expose:

- API keys
- passwords
- tokens

Always:

- validate input
- sanitize user content
- use environment variables
- protect endpoints with JWT

---

# Documentation

Every module should contain:

README.md

Every public function should have docstrings.

Complex algorithms should include explanatory comments.

---

# Testing

Generate unit tests whenever possible.

Prefer pytest-compatible tests.

Test:

- services
- serializers
- endpoints
- utilities

---

# Git Commit Convention

Use Conventional Commits.

Examples

feat:

fix:

docs:

refactor:

test:

style:

chore:

---

# Code Quality Expectations

Generate code that could reasonably be deployed in production.

Prioritize:

- readability
- maintainability
- scalability
- modularity
- performance

Do not generate placeholder implementations unless explicitly requested.

If information is missing, ask for clarification instead of making assumptions.

Always generate complete, production-quality implementations that align with enterprise software engineering standards.

When implementing new features, preserve the existing project architecture and avoid introducing unnecessary dependencies or breaking changes.