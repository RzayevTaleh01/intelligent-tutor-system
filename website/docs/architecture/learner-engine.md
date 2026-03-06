---
sidebar_position: 3
title: 📈 Learner Engine
---

# Learner Engine (LE)

## Overview

The **Learner Engine** is the system's "hippocampus"—responsible for modeling the student's cognitive state. It transforms the ITS from a stateless chatbot into a persistent, adaptive educational companion. By tracking mastery levels and predicting memory decay, it ensures that learning is personalized and durable.

## Core Capabilities

### 1. Bayesian Knowledge Tracing (BKT)
BKT is a probabilistic model used to infer latent student knowledge from observed performance.
*   **Purpose:** To estimate the probability $P(L_n)$ that a student has mastered a skill after $n$ attempts.
*   **Parameters:**
    *   $P(L_0)$: Initial probability of knowing the skill.
    *   $P(T)$: Probability of learning the skill at each step.
    *   $P(G)$: Probability of guessing correctly (Guess).
    *   $P(S)$: Probability of slipping (mistake despite knowing) (Slip).
*   **Update Rule:** The system updates $P(L)$ after every attempt using Bayes' theorem.

### 2. Spaced Repetition System (SRS)
To combat the **Ebbinghaus Forgetting Curve**, the LE implements a modified **SM-2 Algorithm** (similar to Anki).
*   **Logic:**
    *   Correct answer $\rightarrow$ Increase interval (e.g., 1 day $\rightarrow$ 3 days $\rightarrow$ 7 days).
    *   Incorrect answer $\rightarrow$ Reset interval to 1 day.
*   **Goal:** Schedule reviews exactly when the student is about to forget the concept (90% retention probability).

### 3. User Profiling
The LE maintains a comprehensive profile for each student:
*   **Global Readiness Score:** An aggregate metric of overall course progress (0.0 - 1.0).
*   **Skill Matrix:** A detailed map of mastery probabilities for every concept in the Knowledge Graph.
*   **Learning Style:** Inferred preferences (e.g., visual vs. textual, theoretical vs. practical).

## Technical Implementation

### BKT Update Logic
```python
def update_bkt(p_known, is_correct):
    if is_correct:
        p_learned = (p_known * (1 - p_slip)) / (p_known * (1 - p_slip) + (1 - p_known) * p_guess)
    else:
        p_learned = (p_known * p_slip) / (p_known * p_slip + (1 - p_known) * (1 - p_guess))
    
    return p_learned + (1 - p_learned) * p_transit
```

### SRS Scheduling
```python
def schedule_next_review(current_interval, performance_rating):
    if performance_rating >= 3:
        if current_interval == 0:
            return 1
        elif current_interval == 1:
            return 6
        else:
            return round(current_interval * ease_factor)
    else:
        return 1 # Reset
```

## Integration with Other Engines

*   **Pedagogy Engine:** Uses the student's mastery state ($P(L)$) to decide the next topic.
*   **Assessment Engine:** Provides the raw performance data (Correct/Incorrect) to trigger updates.
*   **Tutor Engine:** Uses the user profile to personalize the dialogue style.
