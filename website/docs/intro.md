---
sidebar_position: 1
title: Research Overview
slug: /
---

# EduVision: A Neuro-Symbolic Adaptive Intelligent Tutoring System

**Author:** Taleh Rzayev  
**Research Domain:** Artificial Intelligence in Education (AIED)  
**System Version:** 2.0 (Research Edition)

---

## 1. Abstract

The democratization of personalized education remains one of the grand challenges of the 21st century. While traditional **Intelligent Tutoring Systems (ITS)** offer structured learning paths, they lack the conversational flexibility of human tutors. Conversely, modern **Large Language Models (LLMs)** provide fluency but suffer from hallucinations and a lack of pedagogical strategy.

**EduVision** proposes a novel **Neuro-Symbolic Architecture** that bridges this gap. By orchestrating a Generative AI (Llama 3.1) within a deterministic framework of **Bayesian Knowledge Tracing (BKT)** and **Deep Reinforcement Learning (RL)**, EduVision creates an adaptive learning environment that is both pedagogically sound and conversationally engaging. This documentation outlines the system's theoretical foundations, architectural design, and technical implementation.

---

## 2. Research Methodology

Our approach integrates three distinct fields of study to create a cohesive tutoring experience.

### 2.1. Cognitive Science: The Zone of Proximal Development
Drawing from Vygotsky's theory, EduVision aims to keep the learner in their **Zone of Proximal Development (ZPD)**—the sweet spot between what a learner can do unaided and what they can't do at all.

*   **Implementation:** We employ a **Proximal Policy Optimization (PPO)** Reinforcement Learning agent.
*   **State Space:** The agent observes the learner's `Mastery Score`, `Response Latency`, and `Error Rate`.
*   **Action Space:** The agent dynamically adjusts the **Difficulty Parameter ($\beta$)** of the next problem.
*   **Reward Signal:** The agent is rewarded for keeping the learner in a "Flow State" (high accuracy at appropriate difficulty).

### 2.2. Psychometrics: Bayesian Knowledge Tracing (BKT)
To model the "invisible" state of a learner's knowledge, we utilize **BKT**, a Hidden Markov Model.

$$ P(L_{t+1}) = P(L_t) \cdot (1 - P(S)) + (1 - P(L_t)) \cdot P(T) $$

Where:
*   $P(L_t)$: Probability the skill is known at step $t$.
*   $P(S)$: Slip probability (knowing but erring).
*   $P(T)$: Transition probability (learning).

### 2.3. AI Alignment: Retrieval-Augmented Generation (RAG)
To prevent LLM hallucinations, all pedagogical responses are grounded in a verified **Knowledge Graph**. The system retrieves semantic chunks from uploaded textbooks before generating a response, ensuring factual accuracy.

---

## 3. System Architecture: The 5-Engine Design

EduVision is not a monolith but a distributed system of five specialized "Intelligent Engines."

```mermaid
graph TD
    subgraph "The Brain (EduVision Core)"
        KE[🗂️ Knowledge Engine]
        PE[🧠 Pedagogy Engine]
        LE[📈 Learner Engine]
        TE[💬 Tutor Engine]
        AE[✅ Assessment Engine]
        
        RL[🤖 RL Agent (PPO)]
        BKT[📊 BKT Model]
    end

    User([👨‍🎓 Learner]) <-->|Natural Language| TE
    TE <-->|Context| KE
    User -->|Submission| AE
    AE -->|Grade| LE
    LE -->|State Update| BKT
    BKT -->|Mastery Prob| PE
    PE <-->|Reward/Action| RL
    PE -->|Strategy| TE
```

### 3.1. 🗂️ Knowledge Engine
*   **Function:** Ingests educational content (PDF/Text), chunks it, and creates vector embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
*   **Storage:** `pgvector` (PostgreSQL) for high-performance similarity search.

### 3.2. 🧠 Pedagogy Engine (The Strategist)
*   **Function:** The central decision-maker. It uses the **RL Agent** to determine the optimal next step (e.g., "Increase Difficulty", "Review Prerequisite", "Explain Concept").
*   **Novelty:** Replaces static "if-then" rules with a trained neural policy.

### 3.3. 💬 Tutor Engine (The Persona)
*   **Function:** The interface layer. It uses **Meta Llama 3.1 (8B)** via Together AI to generate empathetic, Socratic dialogue based on the Pedagogy Engine's instructions.

### 3.4. 📈 Learner Engine (The Memory)
*   **Function:** Maintains the persistent state of the learner, tracking mastery probabilities across the Knowledge Graph.

### 3.5. ✅ Assessment Engine (The Critic)
*   **Function:** Evaluates learner inputs against ground-truth rubrics using a hybrid Rule-Based + LLM approach.

---

## 4. Evaluation Metrics

To validate the efficacy of EduVision, we track the following key performance indicators (KPIs):

| Metric Categories | Specific Metrics | Goal |
| :--- | :--- | :--- |
| **Pedagogical** | **Learning Gain** | Rate of mastery increase per session. |
| | **Retention Rate** | Performance on delayed post-tests (SRS intervals). |
| **Technical** | **Inference Latency** | Time to generate a Tutor response (< 2s). |
| | **RAG Precision** | Relevance of retrieved knowledge chunks. |
| **Engagement** | **Session Duration** | Average time spent learning per login. |
| | **Flow Ratio** | % of time spent in the ZPD (optimal difficulty). |

---

## 5. Technical Implementation Overview

*   **Backend:** FastAPI (Async Python)
*   **Database:** PostgreSQL 16 (Relational + Vector)
*   **AI Inference:** Together AI (Serverless LLM)
*   **ML Framework:** PyTorch + Stable-Baselines3 (RL)
*   **Infrastructure:** Docker & Docker Compose

For detailed technical setup and API documentation, please refer to the **[Technical Guide](./technical/intro)**.

---

*© 2026 EduVision Project. Created by Taleh Rzayev for PhD Research.*
