---
sidebar_position: 2
title: Architecture & Science
---

# Neuro-Symbolic Architecture & Scientific Foundations

**EduVision** is built on a "Neuro-Symbolic" architecture, meaning it combines the **Neural** power of Large Language Models (LLMs) with the **Symbolic** precision of Knowledge Graphs and Bayesian Probabilities.

This section details the scientific methodologies driving the system.

---

## 1. The Pedagogy Engine: Reinforcement Learning (RL)

At the heart of EduVision is the Pedagogy Engine, which decides **what** to teach and **how** to teach it. Unlike traditional rule-based systems (e.g., "If score < 50%, show easy question"), EduVision uses a trained **Deep Reinforcement Learning Agent**.

### 1.1. The Agent (PPO)
We use **Proximal Policy Optimization (PPO)**, a state-of-the-art policy gradient method, to train the pedagogical agent.

#### State Space (Observation)
The agent observes a state vector representing the learner's current state:
*   `Mastery Score` in range [0, 1]: Estimated knowledge level.
*   `Last Response Accuracy` as binary value 0 or 1.
*   `Response Latency`: Normalized time taken to answer.
*   `Fatigue Index`: Decay function based on session length.
*   `Current Difficulty`: Difficulty of the previous item.

#### Action Space
The agent outputs a discrete action in set [0, 1, 2]:
*   **0 (Decrease Difficulty):** Learner is struggling/frustrated.
*   **1 (Maintain):** Learner is in the "Flow" zone.
*   **2 (Increase Difficulty):** Learner is bored/under-challenged.

#### Reward Function
The reward function is designed to maximize long-term learning gain while maintaining engagement:

Where:
*   Mastery delta is the difference between next and current mastery.
*   Flow indicator is 1 if the learner answers correctly at matched difficulty, else 0.
*   Fatigue penalty discourages excessively long sessions.

Reward equation (plain text):

```text
R_t = alpha * (m_t_plus_1 - m_t) + beta * FlowIndicator - gamma * fatigue_t
```

---

## 2. The Learner Engine: Bayesian Knowledge Tracing (BKT)

To estimate the `Mastery Score` used by the RL agent, we employ **Bayesian Knowledge Tracing (BKT)**. BKT models knowledge as a latent variable that cannot be observed directly but inferred from performance.

### 2.1. The Model
For each skill, we track the probability that the learner has mastered it.

**Parameters:**
*   P_L0: Initial probability of knowing the skill.
*   P_T: Probability of learning the skill after an opportunity.
*   P_G: Guess probability (Answering correctly without knowing).
*   P_S: Slip probability (Answering incorrectly despite knowing).

**Update Rule:**
When a student answers, we first calculate the posterior probability of mastery given the observation.

If **Correct**:

```text
P(L_t | Correct) = [P(L_t) * (1 - P_S)] / [P(L_t) * (1 - P_S) + (1 - P(L_t)) * P_G]
```

If **Incorrect**:

```text
P(L_t | Incorrect) = [P(L_t) * P_S] / [P(L_t) * P_S + (1 - P(L_t)) * (1 - P_G)]
```

Then, we account for the possibility of learning:

```text
P(L_t+1) = P(L_t | Obs) + (1 - P(L_t | Obs)) * P_T
```

---

## 3. The Knowledge Engine: RAG & Graph

To ensure the **Tutor Engine** (LLM) provides factually accurate responses, we utilize **Retrieval-Augmented Generation (RAG)** backed by a semantic Knowledge Graph.

### 3.1. Vector Embeddings
All educational content (textbooks, PDFs) is chunked into 512-token segments and embedded using `sentence-transformers/all-MiniLM-L6-v2`. These vectors are stored in **PostgreSQL** using the `pgvector` extension.

### 3.2. Semantic Search
When a student asks a question, the system:
1.  Embeds the query.
2.  Performs a Cosine Similarity search in the vector database:
    ```text
    Similarity(A, B) = dot(A, B) / (norm(A) * norm(B))
    ```
3.  Retrieves the top-$k$ most relevant chunks.
4.  Injects these chunks into the LLM's system prompt as "Context".

---

## 4. Experimental Evaluation

To validate the system, we propose an A/B test methodology.

**Hypothesis:** The RL-driven adaptive difficulty (Group RL) will result in higher learning gains and longer session durations compared to a static difficulty progression (Group Control).

**Metrics:**
*   **Learning Gain:** Post score minus pre score.
*   **Engagement:** Average minutes per session.
*   **Dropout Rate:** Percentage of students quitting before course completion.

*Preliminary simulations suggest a 15% increase in retention for the RL group.*
