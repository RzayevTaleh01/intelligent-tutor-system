# EduVision ITS

**EduVision ITS (Intelligent Tutoring System)** is a Next-Generation Adaptive Learning Platform driven by **Neuro-Symbolic AI** and **Cognitive Modeling**.

Unlike traditional LMS platforms that serve static content, EduVision acts as a **dynamic, personalized digital tutor**. It understands the learner's cognitive state, predicts memory decay, and adapts instructional strategies in real-time.

---

## 📚 Documentation

Full technical and architectural documentation is available at:

👉 **[https://RzayevTaleh01.github.io/intelligent-tutor-system/](https://RzayevTaleh01.github.io/intelligent-tutor-system/)**

Please refer to the documentation site for:
*   **System Architecture:** Detailed breakdown of the 5-Engine Core (Knowledge, Pedagogy, Learner, Tutor, Assessment).
*   **API Reference:** Endpoints for Course Management, Chat, and Analytics.
*   **Deployment Guide:** Instructions for Docker and Kubernetes.
*   **Research Background:** Implementation of Bayesian Knowledge Tracing (BKT) and Item Response Theory (IRT).

---

## 🚀 Quick Start

### Prerequisites
*   Docker & Docker Compose
*   NVIDIA GPU (Recommended for LLM inference) or 16GB+ RAM for CPU mode.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/RzayevTaleh01/intelligent-tutor-system.git
    cd intelligent-tutor-system
    ```

2.  **Start the System:**
    ```bash
    docker-compose up -d --build
    ```

3.  **Access the Interface:**
    *   **API Docs (Swagger):** `http://localhost:8000/docs`
    *   **Frontend (if deployed):** `http://localhost:3000`

---

## 🧪 Running Tests

To verify the system's cognitive functions:

```bash
# Run the full smoke test (Teacher -> Student -> Grading)
python scripts/verify_trainable.py

# Run the adaptive learning test (BKT & SRS updates)
python scripts/adaptive_smoke_test.py
```

---

## 🏗️ Core Technologies

*   **AI Model:** Llama 3.1 8B (Fine-tuned for Pedagogy)
*   **Backend:** FastAPI (Python)
*   **Database:** PostgreSQL (with `pgvector`)
*   **Cognitive Modeling:** Bayesian Knowledge Tracing (BKT), Spaced Repetition (SRS)
*   **Architecture:** Event-Driven Microservices

---

*© 2024 EduVision Research Lab. All Rights Reserved.*
