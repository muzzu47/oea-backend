# OEA Backend (`oea-backend`)

The unified **Python (FastAPI)** application backend engine powering the AI-driven Computer-Based Test (CBT) platform. Built as a highly optimized **Modular Monolith** to maximize developer velocity, reduce infrastructure overhead, and provide zero-latency performance tracking during the MVP phase.

## 🏗️ Core Architectural Responsibilities

The codebase is strictly structured into isolated modules to handle the three primary backend workflows:

* **API Routing & Engine Gateway:** High-concurrency async endpoints managing authentication, session tokens, and fetching randomized 25-question mock tests or 160-question model tests instantly.
* **Ahead-of-Time (AOT) AI Generation:** Stateful, multi-agent AI execution loops powered by **LangGraph / CrewAI** (Author, Curriculum Auditor, and Peer Reviewer) that generate, validate, and parse complex mathematical/science questions using LaTeX formulas into a `draft_questions` staging pool.
* **Hybrid Post-Exam Evaluation:** A multi-tier evaluation system that utilizes native Python logic for high-speed calculators (Overall Scores, Time-Management telemetry analysis, and Proficiency Subject Mapping) alongside background async AI tasks for generating personalized strategic advice.

## 📊 Shared Data & Infrastructure Stack

* **FastAPI:** Asynchronous routing framework handling high-concurrency client connections and real-time Server-Sent Events (SSE).
* **PostgreSQL:** Relational data layer ensuring bulletproof ACID compliance for critical examination states, transactions, and flexible `JSONB` logging for granular student clickstream tracking.
* **pgvector:** Direct native database extension handling high-speed vector similarity lookups for AI-generated question chunks, eliminating multi-database sync overhead.
