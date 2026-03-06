# Pedagogy Engine & Adaptive Strategies

## Overview
The Pedagogy Engine is the "brain" of the Intelligent Tutoring System (ITS). It determines **what** to teach next and **how** to teach it based on the learner's current state, error history, and mastery level.

## Recent Upgrades (v2.1)

We have moved beyond simple difficulty adjustment (Easy/Medium/Hard) to implement sophisticated **Cognitive Science Strategies**.

### 1. New Teaching Strategies

| Strategy | Trigger Condition | Description |
| :--- | :--- | :--- |
| **Socratic Method** | High Mastery (>0.6) or Minor Errors | Instead of giving answers, the AI asks guiding questions to lead the student to the solution. Promotes critical thinking. |
| **Feynman Technique** | Conceptual Errors (Wrong Choice) | The AI asks the student to explain the concept in simple terms ("as if teaching a beginner") to identify gaps in understanding. |
| **Scaffolding** | Repeated Errors (Stuck State) | When a student fails the same concept twice, the AI breaks the problem down into smaller, manageable steps and provides hints. |
| **Direct Instruction** | Standard Learning | Clear, concise explanation and guidance (default mode). |

### 2. Adaptive Logic (`RemediationPlanner`)

The `RemediationPlanner` now analyzes the `ErrorTaxonomy` and `ErrorCount` to select the best strategy:

- **If `error_count >= 2` (Stuck):** -> Activates **Scaffolding** (Breakdown & Hints).
- **If `error_type == CONCEPTUAL`:** -> Activates **Feynman** (Explain in own words).
- **If `mastery > 0.8` (Advanced):** -> Activates **Socratic Challenge** (Deep questioning).

### 3. Dynamic Prompt Engineering (`TutorEngine`)

The `TutorEngine` dynamically injects specific instructions into the LLM's System Prompt based on the selected strategy.

**Example (Socratic):**
> "STRATEGY: SOCRATIC METHOD. Do NOT provide the direct answer. Ask guiding questions..."

**Example (Scaffolding):**
> "STRATEGY: SCAFFOLDING. The student is stuck. Break the problem down into smaller steps..."

## Integration Flow

1. **Assessment Engine** grades the student's attempt.
2. **Learner Engine** updates the state (BKT) and records errors.
3. **Pedagogy Engine** (`RemediationPlanner`) analyzes the state and selects a Strategy (e.g., "socratic").
4. **TutorEngine** constructs the prompt using the selected Strategy and generates the AI response.
