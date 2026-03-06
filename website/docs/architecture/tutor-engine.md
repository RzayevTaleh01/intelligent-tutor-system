---
sidebar_position: 4
title: 💬 Tutor Engine
---

# Tutor Engine (TE)

## Overview

The **Tutor Engine** is the conversational interface of EduVision. It is the "Voice" that interacts directly with the student. Powered by **Large Language Models (LLMs)**, it transforms raw pedagogical strategies into natural, empathetic, and context-aware dialogue.

## Core Capabilities

### 1. Neuro-Symbolic Dialogue Management
Unlike generic chatbots, the TE follows a strict pedagogical protocol dictated by the **Pedagogy Engine**.
*   **Strategy Injection:** The prompt context includes the specific teaching strategy (e.g., "Socratic Method", "Direct Instruction", "Scaffolding").
*   **Safety Rails:** Prevents the LLM from giving direct answers when the goal is to guide the student.

### 2. Context-Aware Generation (RAG)
To minimize hallucinations and ensure accuracy, the TE uses **Retrieval-Augmented Generation (RAG)**.
*   **Context Retrieval:** Queries the **Knowledge Engine** for relevant excerpts.
*   **Prompt Construction:** Combining system instructions, conversation history, and retrieved knowledge.

### 3. Adaptive Tone & Style
The TE adjusts its persona based on the student's profile (from the **Learner Engine**).
*   **Beginner:** Encouraging, simple language, more emojis.
*   **Advanced:** Concise, technical, challenging.

## Technical Implementation

### Prompt Engineering
The system uses a sophisticated prompt template structure:

```python
SYSTEM_PROMPT = """
You are an expert AI Tutor.
Current Strategy: {strategy}
Student Level: {mastery_level}

CONTEXT:
{retrieved_knowledge}

INSTRUCTIONS:
- Do not reveal the answer directly if the strategy is 'Socratic'.
- Use the provided context to answer questions.
- Maintain an encouraging tone.
"""
```

### Model Configuration
*   **Base Model:** `meta-llama/Meta-Llama-3-8B-Instruct` (Fine-tuned on educational datasets).
*   **Inference:** Optimized with quantization (4-bit/8-bit) for efficient deployment.
*   **Parameters:** `temperature=0.7` (Creative but focused), `max_tokens=512`.

## Integration with Other Engines

*   **Pedagogy Engine:** Provides the `strategy` and `next_step` instructions.
*   **Knowledge Engine:** Provides the factual content (`context`) for the response.
*   **Learner Engine:** Provides the student's `profile` and `history` for personalization.
