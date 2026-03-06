---
sidebar_position: 2
title: 🧠 Pedagogy Engine
---

# Pedagogy Engine (PE)

## Overview

The **Pedagogy Engine** is the strategic "cortex" of the ITS. It is responsible for instructional decision-making—determining *what* to teach next and *how* to teach it. By analyzing the learner's state from the Learner Engine and the content structure from the Knowledge Engine, it orchestrates a personalized learning path.

## Core Capabilities

### 1. Zone of Proximal Development (ZPD) Targeting
The PE aims to keep the student in their **Zone of Proximal Development**—the sweet spot where the material is challenging enough to be engaging but not so difficult as to be frustrating.
*   **Too Easy:** Increase difficulty or switch to "Socratic" mode.
*   **Too Hard:** Decrease difficulty, activate "Scaffolding", or switch to a prerequisite topic.

### 2. Adaptive Instructional Strategies
The engine dynamically selects the best pedagogical approach based on real-time triggers:

| Strategy | Trigger Condition | Description |
| :--- | :--- | :--- |
| **Direct Instruction** | New Topic / Low Mastery | Clear, concise explanations and examples. Default mode for introducing concepts. |
| **Socratic Method** | High Mastery (>0.7) | Instead of giving answers, the AI asks guiding questions to stimulate critical thinking and deep understanding. |
| **Feynman Technique** | Conceptual Misconception | The AI asks the student to explain the concept "in their own words" to diagnose gaps in mental models. |
| **Scaffolding** | Repeated Failures (Stuck) | Breaks a complex problem down into smaller, manageable steps, providing hints at each stage. |
| **Spiral Review** | SRS Trigger (Memory Decay) | Re-introduces previously learned topics mixed with new material to reinforce long-term retention. |

### 3. Curriculum Sequencing
The PE traverses the **Knowledge Graph** to determine the optimal sequence of topics.
*   **Prerequisite Checking:** Ensures the student has mastered dependencies (e.g., "Variables" before "Loops").
*   **Remediation Loops:** If a student fails a concept, the PE backtracks to the underlying prerequisite rather than just repeating the same question.

## Technical Implementation

### Remediation Logic (`RemediationPlanner`)
```python
def plan_next_step(student_state, recent_errors):
    if len(recent_errors) > 2 and recent_errors[-1]['type'] == 'conceptual':
        return {
            "strategy": "feynman",
            "content": "Explain this concept simply...",
            "difficulty": student_state.mastery * 0.8
        }
    
    if student_state.mastery > 0.8:
        return {
            "strategy": "socratic",
            "content": generate_challenge_question(),
            "difficulty": student_state.mastery * 1.2
        }

    return {"strategy": "direct_instruction", "content": get_next_topic()}
```

## Integration with Other Engines

*   **Learner Engine:** Provides the `mastery_level` and `error_history` needed to make decisions.
*   **Knowledge Engine:** Provides the `dependency_graph` to navigate prerequisites.
*   **Tutor Engine:** Receives the `strategy` instruction (e.g., "Be Socratic") to condition the LLM's response.
