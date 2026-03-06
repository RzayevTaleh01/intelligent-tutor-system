---
sidebar_position: 4
title: Testing & Experiments
---

# Testing Framework & Experiments

## Overview

EduVision ITS employs a **Comprehensive Testing Framework** to validate its stability, reliability, and pedagogical effectiveness. This includes everything from simple unit tests to complex A/B experiments on instructional strategies.

## 🧪 Testing Pyramid

### 1. Unit Tests (`/tests`)
We use `pytest` for all backend testing.
*   **Coverage:** 85%+ of critical paths (Auth, BKT, API).
*   **Mocking:** `pytest-mock` is used to simulate LLM responses and database interactions.

### 2. Smoke Tests (`/scripts`)
End-to-end validation scripts ensure the entire system works together.
*   `verify_trainable.py`: Simulates a full teacher-student workflow (Create Course -> Upload -> Chat -> Attempt).
*   `adaptive_smoke_test.py`: Verifies the **Learner Engine**'s ability to update mastery probabilities (BKT) and schedule reviews (SRS).

### 3. Integration Tests (`/tests/integration`)
These tests verify the interaction between engines.
*   **Example:** Ensuring the `AssessmentEngine` correctly triggers a `LearnerEngine` update.

## 🔬 A/B Experimentation Framework (`src/core/experiments/ab.py`)

To continuously improve the system's teaching quality, we have built a deterministic A/B testing module.

### Core Components

#### `Experiment` Class
Defines a specific hypothesis to test.
*   **Name:** Unique identifier (e.g., `socratic_vs_direct`).
*   **Variants:** List of possible treatments (e.g., `["control", "socratic"]`).
*   **Weights:** Probability distribution for assignment (e.g., `[0.5, 0.5]`).

#### `Assignment` Logic
Users are consistently assigned to the same variant based on a hash of their `user_id` and the `experiment_name`. This ensures a stable user experience.

```python
def get_variant(user_id: str, experiment_name: str) -> str:
    # Deterministic assignment based on hash
    hash_val = sha256(f"{user_id}:{experiment_name}".encode()).hexdigest()
    ...
```

### Running Experiments

1.  **Define:** Create a new `Experiment` in `ab.py`.
2.  **Deploy:** The system automatically starts assigning users.
3.  **Track:** All interactions are logged with the assigned `variant_id`.
4.  **Analyze:** Use the `/analytics` endpoint to compare performance metrics (e.g., mastery gain, retention) between variants.

## 📊 Evaluation Metrics

We track the following key performance indicators (KPIs) for each experiment:
*   **Mastery Gain:** Change in `learner_skill.mastery_probability` over time.
*   **Engagement:** Number of sessions and messages per user.
*   **Retention:** Probability of returning for a scheduled SRS review.
