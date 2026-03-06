---
sidebar_position: 2
title: 🗂️ Knowledge Engine
---

# Knowledge Engine (KE)

## Overview

The **Knowledge Engine** is the foundational layer of the EduVision architecture. It serves as the system's "Brain," responsible for ingesting, structuring, and retrieving educational content. It transforms unstructured data (PDFs, text, slides) into a structured **Knowledge Graph (KG)** that can be navigated by the other engines.

## Core Capabilities

### 1. Semantic Search (RAG)
The KE utilizes a vector database (e.g., ChromaDB, FAISS) to perform semantic searches. When a student asks a question, the KE retrieves the most relevant "chunks" of information based on embedding similarity, not just keyword matching.

*   **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (optimized for speed/accuracy trade-off).
*   **Vector Database:** Used for dense retrieval.

### 2. Knowledge Graph Construction
Beyond simple text chunks, the KE builds a graph of concepts.
*   **Nodes:** Concepts (e.g., "Loop", "Variable", "Recursion").
*   **Edges:** Relationships (e.g., "requires", "is-a", "part-of").

This graph structure allows the Pedagogy Engine to understand prerequisites. For example, knowing that "Recursion" *requires* "Functions" allows the system to enforce learning paths.

### 3. Automatic Chunking
The engine intelligently splits long documents into pedagogically sound units.
*   **Strategy:** Recursive Character Splitting + Semantic Boundary Detection.
*   **Metadata:** Each chunk is tagged with its source, difficulty level, and associated learning objectives.

## Technical Implementation

```python
class KnowledgeEngine:
    def __init__(self, vector_store, graph_store):
        self.vector_store = vector_store
        self.graph_store = graph_store

    def ingest(self, document):
        chunks = self.chunker.split(document)
        embeddings = self.embedder.embed(chunks)
        self.vector_store.add(chunks, embeddings)
        self.graph_builder.extract_entities(chunks)
```

## Integration with Other Engines

*   **Pedagogy Engine:** Queries the KE to find the *next* concept in the dependency graph.
*   **Tutor Engine:** Uses retrieved context from the KE to ground its responses (reducing hallucinations).
*   **Assessment Engine:** Uses KE to generate relevant questions based on the specific content taught.
