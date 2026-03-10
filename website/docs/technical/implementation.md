---
sidebar_position: 3
title: Technical Implementation
---

# Technical Architecture & System Design

**EduVision** is designed as a scalable, cloud-native **Intelligent Tutoring System (ITS)**. It leverages modern microservices principles, containerization, and high-performance asynchronous processing.

This section details the technical implementation of the 5-Engine Architecture.

---

## 1. System Overview

The system is composed of five specialized engines, orchestrated by a central **FastAPI** backend and supported by a **PostgreSQL** database with vector capabilities.

### 1.1. Technology Stack

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend API** | Python (FastAPI) | 3.11+ | Async REST API, Engine Orchestration |
| **Database** | PostgreSQL | 16 | Relational Data + Vector Storage (`pgvector`) |
| **AI Inference** | Together AI | Llama 3.1 | Serverless LLM for Tutor Engine |
| **Embeddings** | Sentence-Transformers | all-MiniLM-L6-v2 | Semantic Search & RAG |
| **Reinforcement Learning** | Stable-Baselines3 | 2.3.0 | PPO Agent Training & Inference |
| **Task Queue** | BackgroundTasks | Native | Asynchronous Job Processing (Ingestion) |
| **Containerization** | Docker | 24.0+ | Deployment & Environment Consistency |

---

## 2. Database Design (Schema)

The database schema is optimized for high-concurrency read/write operations and vector similarity search.

### 2.1. Core Tables

*   **`users`**: Stores authentication details (hashed passwords via `pbkdf2_sha256`) and tenant information.
*   **`courses`**: Metadata for educational content.
*   **`sessions`**: Active learning sessions linking students to courses.

### 2.2. Adaptive Learning Tables (Indexed)

To support real-time adaptability for thousands of students, we use composite indexes:

*   **`learner_theta`**: Stores the latent ability parameter ($\theta$) for IRT.
    *   *Index:* `ix_learner_theta_session` (Hash Index)
*   **`learner_skills`**: Stores BKT parameters ($P(L)$, $P(S)$, $P(G)$) per skill.
    *   *Index:* `ix_learner_skills_lookup` (B-Tree on `session_id`, `skill_tag`)
*   **`knowledge_embeddings`**: Stores 384-dimensional vectors for RAG.
    *   *Index:* `hnsw` (Hierarchical Navigable Small World) for approximate nearest neighbor search.

---

## 3. API Architecture

The backend follows a **Clean Architecture** pattern, separating concerns into:
1.  **Routers (`src/api/routers`):** Handle HTTP requests/responses.
2.  **Services (`src/core/engines`):** Implement business logic (Pedagogy, Assessment).
3.  **Repositories (`src/db`):** Handle database interactions.

### 3.1. Key Endpoints

#### `POST /chat/` (The Loop)
This is the primary interaction point. It triggers the full neuro-symbolic cycle:

1.  **Receive:** Student message + Session ID.
2.  **Retrieve (RAG):** Knowledge Engine fetches relevant context.
3.  **Decide (RL):** Pedagogy Engine's PPO Agent selects the next action (e.g., "Hint").
4.  **Generate (LLM):** Tutor Engine constructs a prompt and calls Llama 3.1.
5.  **Respond:** Returns the AI's response to the student.

#### `POST /attempt/` (The Assessment)
1.  **Receive:** Student answer + Item ID.
2.  **Evaluate:** Assessment Engine grades the response (0.0 - 1.0).
3.  **Update:** Learner Engine updates BKT probabilities ($P(L_{t+1})$).
4.  **Schedule:** SRS algorithm schedules the next review.

---

## 4. Scalability & Performance

### 4.1. Concurrency (AsyncIO)
The entire backend is built on Python's `asyncio`. Network-bound operations (DB queries, LLM calls) are non-blocking, allowing a single server instance to handle thousands of concurrent connections.

### 4.2. GPU Acceleration
For heavy computational tasks (Embedding generation, RL Inference), the system automatically detects CUDA-enabled GPUs via PyTorch:

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer(model_name, device=device)
```

### 4.3. Caching Strategy (Future)
To further reduce latency, a **Redis** layer is planned to cache:
*   Common vector search results.
*   Learner state for active sessions.
*   LLM responses for identical queries.

---

## 5. Security

*   **Authentication:** OAuth2 with Password Flow (JWT Tokens).
*   **Password Hashing:** `pbkdf2_sha256` (NIST recommended) replaces legacy `bcrypt` to avoid truncation vulnerabilities.
*   **Tenant Isolation:** All database queries are scoped by `tenant_id` to ensure data privacy in multi-school deployments.
