---
sidebar_position: 2
title: Database Schema
---

# Database Schema & Models

## Overview

EduVision ITS uses **PostgreSQL** as its primary relational database. The schema is designed to support high-throughput interactions while maintaining relational integrity for complex educational data.

## 🗄️ Core Tables (`models_prod.py`)

These tables handle the administrative and structural aspects of the LMS.

### `User`
*   `id` (UUID, PK)
*   `tenant_id` (FK -> Tenant)
*   `email` (Unique)
*   `hashed_password`
*   `role` (Enum: `admin`, `teacher`, `student`)

### `Course`
*   `id` (UUID, PK)
*   `teacher_id` (FK -> User)
*   `title`
*   `description`
*   `is_published` (Boolean)

### `Session`
*   `id` (UUID, PK)
*   `student_id` (FK -> User)
*   `course_id` (FK -> Course)
*   `started_at` (DateTime)
*   `ended_at` (DateTime, Nullable)

## 🧠 Knowledge Graph (`models_knowledge.py`)

These tables persist the semantic structure of the course material.

### `KnowledgeChunk`
*   `id` (UUID, PK)
*   `content` (Text)
*   `embedding` (Vector[768]) - **PGVector Extension**
*   `source_file` (String)

### `KnowledgeEdge`
*   `source_chunk_id` (FK)
*   `target_chunk_id` (FK)
*   `relation_type` (Enum: `requires`, `part_of`, `similar_to`)

## 📈 Adaptive Learning (`models_adaptive.py`)

These tables store the probabilistic state of each learner.

### `LearnerSkill` (BKT State)
Tracks mastery for a specific skill.
*   `student_id` (FK)
*   `skill_id` (String)
*   `mastery_probability` (Float: 0.0 - 1.0)
*   `slip_probability` (Float)
*   `guess_probability` (Float)
*   `last_updated` (DateTime)

### `LearnerSchedule` (SRS State)
Tracks review timing for spaced repetition.
*   `student_id` (FK)
*   `item_id` (String)
*   `next_review` (DateTime)
*   `interval_days` (Integer)
*   `ease_factor` (Float)

## 📊 Diagnostics (`models_diagnostics.py`)

Used for psychometric analysis (IRT - Item Response Theory).

### `LearnerTheta`
*   `student_id` (FK)
*   `theta` (Float) - Latent ability estimate.
*   `standard_error` (Float)

### `SkillDifficulty`
*   `skill_id` (String)
*   `difficulty` (Float) - Calibrated difficulty parameter.
*   `discrimination` (Float) - How well the item differentiates ability levels.
