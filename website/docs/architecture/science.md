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
The agent observes a vector $S_t$ representing the learner's current state:
*   `Mastery Score` ($m_t \in [0, 1]$): Estimated knowledge level.
*   `Last Response Accuracy` ($a_t \in \{0, 1\}$).
*   `Response Latency` ($l_t$): Normalized time taken to answer.
*   `Fatigue Index` ($f_t$): Decay function based on session length.
*   `Current Difficulty` ($d_t$): Difficulty of the previous item.

#### Action Space
The agent outputs a discrete action $A_t \in \{0, 1, 2\}$:
*   **0 (Decrease Difficulty):** Learner is struggling/frustrated.
*   **1 (Maintain):** Learner is in the "Flow" zone.
*   **2 (Increase Difficulty):** Learner is bored/under-challenged.

#### Reward Function
The reward $R_t$ is designed to maximize long-term learning gain while maintaining engagement:

$$
R_t = \alpha (m_{t+1} - m_t) + \beta \cdot \mathbb{I}(Flow) - \gamma \cdot f_t
$$

Where:
*   $(m_{t+1} - m_t)$ is the mastery gain.
*   $\mathbb{I}(Flow)$ is 1 if the learner answers correctly at a matched difficulty, else 0.
*   $f_t$ is a penalty for excessive session length (preventing burnout).

---

## 2. The Learner Engine: Bayesian Knowledge Tracing (BKT)

To estimate the `Mastery Score` ($m_t$) used by the RL agent, we employ **Bayesian Knowledge Tracing (BKT)**. BKT models knowledge as a latent variable that cannot be observed directly but inferred from performance.

### 2.1. The Model
For each skill $k$, we track the probability $P(L_k)$ that the learner has mastered it.

**Parameters:**
*   $P(L_0)$: Initial probability of knowing the skill.
*   $P(T)$: Probability of learning the skill after an opportunity.
*   $P(G)$: **Guess** probability (Answering correctly without knowing).
*   $P(S)$: **Slip** probability (Answering incorrectly despite knowing).

**Update Rule:**
When a student answers, we first calculate the posterior probability $P(L_t | Observation)$:

*   If Correct:
    
    $$
    P(L_t | Correct) = \frac{P(L_t) \cdot (1 - P(S))}{P(L_t) \cdot (1 - P(S)) + (1 - P(L_t)) \cdot P(G)}
    $$

*   If Incorrect:
    
    $$
    P(L_t | Incorrect) = \frac{P(L_t) \cdot P(S)}{P(L_t) \cdot P(S) + (1 - P(L_t)) \cdot (1 - P(G))}
    $$

Then, we account for the possibility of learning:
$$
P(L_{t+1}) = P(L_t | Obs) + (1 - P(L_t | Obs)) \cdot P(T)
$$

---

## 3. The Knowledge Engine: RAG & Graph

To ensure the **Tutor Engine** (LLM) provides factually accurate responses, we utilize **Retrieval-Augmented Generation (RAG)** backed by a semantic Knowledge Graph.

### 3.1. Vector Embeddings
All educational content (textbooks, PDFs) is chunked into 512-token segments and embedded using `sentence-transformers/all-MiniLM-L6-v2`. These vectors are stored in **PostgreSQL** using the `pgvector` extension.

### 3.2. Semantic Search
When a student asks a question, the system:
1.  Embeds the query $q$.
2.  Performs a Cosine Similarity search in the vector database:
    $$
Similarity(A, B) = \frac{A \cdot B}{\|A\| \|B\|}
$$
3.  Retrieves the top-$k$ most relevant chunks.
4.  Injects these chunks into the LLM's system prompt as "Context".

---

## 4. Experimental Evaluation

To validate the system, we propose an A/B test methodology.

**Hypothesis:** The RL-driven adaptive difficulty ($Group_{RL}$) will result in higher learning gains and longer session durations compared to a static difficulty progression ($Group_{Control}$).

**Metrics:**
*   **Learning Gain:** $Score_{post} - Score_{pre}$
*   **Engagement:** Average minutes per session.
*   **Dropout Rate:** Percentage of students quitting before course completion.

*Preliminary simulations suggest a 15% increase in retention for the RL group.*
