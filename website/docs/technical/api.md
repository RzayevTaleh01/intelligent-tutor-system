---
sidebar_position: 3
title: API & Jobs
---

# API & Background Jobs

## Overview

The EduVision ITS backend is built on **FastAPI**, providing high-performance, asynchronous endpoints for both real-time interaction (Chat) and administrative tasks (Course Management).

## ⚡ Core API Endpoints (`main.py`)

### 1. Course Management (`/courses`)
*   `POST /` - Create a new course (Teacher Only).
*   `GET /{id}` - Retrieve course details and structure.
*   `POST /{id}/upload` - Upload PDFs or text for ingestion. This triggers a background vectorization job.

### 2. Interaction Layer (`/chat`, `/attempt`)
*   `POST /chat/` - The main interface for the **Tutor Engine**.
    *   **Input:** User message, Session ID.
    *   **Process:** RAG retrieval (pgvector) -> Pedagogy check -> Together AI (Llama 3) generation.
    *   **Output:** Streaming response.
*   `POST /attempt/` - Submits a student's answer for grading.
    *   **Input:** Question ID, Answer.
    *   **Process:** **Assessment Engine** grades -> **Learner Engine** updates BKT.

### 3. Analytics (`/analytics`)
*   `GET /student/{id}/progress` - Returns mastery over time.
*   `GET /course/{id}/heatmap` - Returns class-wide performance.

## ⏳ Asynchronous Background Jobs

Heavy computational tasks are offloaded to a background worker system to keep the API responsive.

### `Job` Model (`models_prod.py`)
Tracks the status of long-running operations.
*   `id` (UUID)
*   `type` (Enum: `embedding_generation`, `course_ingest`, `analytics_refresh`)
*   `status` (Enum: `pending`, `processing`, `completed`, `failed`)
*   `result` (JSON) - Stores output or error messages.

### Key Workers

#### 1. Embedding Generator (`JobType.EMBEDDING_GENERATION`)
Triggered when a teacher uploads a document.
*   **Task:** Uses `sentence-transformers` to compute vectors for all text chunks.
*   **Storage:** Saves vectors directly to PostgreSQL using `pgvector`.
*   **Performance:** Batched processing.

#### 2. Knowledge Graph Builder (`JobType.COURSE_INGEST`)
Triggered after embeddings are ready.
*   **Task:** Identifies key concepts and relationships (e.g., "Loop" requires "Variable").
*   **Output:** Creates edges in the graph database tables (`KnowledgeEdge`).

#### 3. Analytics Refresh (`JobType.ANALYTICS_REFRESH`)
Scheduled nightly.
*   **Task:** Aggregates student data to update class-wide metrics and difficulty parameters (IRT calibration).
