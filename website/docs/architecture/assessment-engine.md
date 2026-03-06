---
sidebar_position: 5
title: ✅ Assessment Engine
---

# Assessment Engine (AE)

## Overview

The **Assessment Engine** is the critical evaluation component of EduVision. It provides objective, consistent, and immediate feedback on student performance. It supports multiple question types (Code, Multiple Choice, Open-Ended Text) and powers the adaptive learning loop.

## Core Capabilities

### 1. Multi-Modal Evaluation
The AE handles diverse assessment formats:
*   **Code Execution:** Runs student code in a secure sandbox (Docker/MicroVM). Checks output against test cases.
*   **Static Analysis:** Analyzes code structure (AST) for syntax errors, style issues, and logic patterns.
*   **Semantic Similarity:** Compares student text answers against rubrics/exemplars using embeddings (Cosine Similarity).
*   **LLM Grading:** Uses a rubric-guided LLM (Llama 3.1) to grade open-ended essays or complex reasoning questions.

### 2. Immediate Feedback Generation
Beyond just a score, the AE provides actionable feedback.
*   **Type:** "Syntax Error", "Logic Error", "Conceptual Gap".
*   **Hint:** Suggests specific areas for improvement without giving away the answer.

### 3. Skill Tagging
Every assessment item is tagged with specific skills (e.g., "Python Loops", "Functions", "Variables").
*   **Granularity:** Allows the **Learner Engine** to update mastery at a fine-grained level.
*   **Dependency Tracking:** Helps identify prerequisite failures.

## Technical Implementation

### Code Evaluation Sandbox
```python
def evaluate_code(student_code, test_cases):
    try:
        result = run_in_sandbox(student_code, timeout=5)
        score = calculate_score(result, test_cases)
        feedback = generate_feedback(result)
        return {"score": score, "feedback": feedback}
    except SandboxError as e:
        return {"score": 0, "feedback": f"Runtime Error: {str(e)}"}
```

### LLM Grading Rubric
The system uses a structured prompt for grading essays:
```python
GRADING_PROMPT = """
Evaluate the following student answer based on the provided rubric.
Rubric: {rubric}
Student Answer: {answer}

Output JSON:
{
  "score": 0.0-1.0,
  "feedback": "...",
  "missing_concepts": ["..."]
}
"""
```

## Integration with Other Engines

*   **Learner Engine:** Receives the `score` and `skill_tags` to update the student's mastery model (BKT).
*   **Pedagogy Engine:** Uses assessment results to decide whether to advance or remediate.
*   **Tutor Engine:** Delivers the feedback to the student in a conversational manner.
