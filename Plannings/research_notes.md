# Research Notes — Design Rationale

> **Non-Authoritative Document**
>
> This document explains *why* certain design decisions were made.
> It does **not** define system behavior, guarantees, or scope.
>
> The authoritative system definition lives in `system_design.md`.

---

## 1. Purpose of This Document

The purpose of this document is to capture the reasoning behind
the architectural choices made in CODE-Sherpa.

It exists to:
- Make design intent explicit
- Show that alternatives were considered
- Explain why complexity was intentionally avoided

This document does not expand scope or promise future behavior.

---

## 2. Why Static Analysis Was Chosen

A core design decision was to rely primarily on static analysis for structure, using AI strictly for semantic enrichment.

This choice was driven by three factors:

1. **Determinism**  
   Static analysis produces repeatable results for the same input.
   This makes the system easier to reason about and evaluate.

2. **Safety and Simplicity**  
   No code execution means no runtime side effects,
   no sandboxing concerns, and no environment dependency.

3. **Defensibility**  
   All extracted facts can be directly traced to source code,
   making outputs auditable and verifiable.

Dynamic analysis and runtime tracing were intentionally excluded
to preserve these properties.

---

## 3. Why a Unified JSON Knowledge Model Exists

Instead of passing raw analyzer output directly to generators,
a unified JSON knowledge model was introduced.

The motivation was:
- To create a single source of truth
- To decouple analysis from presentation
- To allow multiple downstream consumers without duplication

This structure also makes it explicit that:
- Generators do not interpret source code
- All understanding flows through verified data

---

## 4. Why the System Is a Linear Pipeline

A linear pipeline was chosen over more complex architectures
such as event-driven systems or feedback loops.

Reasons include:
- Easier mental model for reviewers
- Clear data dependencies
- No hidden state or cyclic behavior

The system favors clarity over flexibility,
which aligns with its educational and explanatory goals.

---

## 5. Why We Chose a "Hybrid Graph-RAG" Architecture

**We observed that pure Static Analysis is accurate but dry, while pure LLM analysis is insightful but hallucination-prone.**

We rejected "Chat with Codebase" tools (pure RAG) because they lack structural awareness. Instead, we implemented a Hybrid Pipeline:

- Structure (AST): Extracts the "Skeleton" (Files, Classes, Imports). This is 100% deterministic.

- Semantics (LLM): Fills in the "Flesh" (Design Patterns, Intent).

- The Key Innovation: We use the AST to ground the AI. The LLM is never asked "What is in this repo?"; it is asked "Here is function X in file Y; explain its role." This minimizes hallucinations to near zero.
---

## 6. Alternatives Considered

Several alternatives were considered and rejected:

- **IDE-first design**  
  Rejected to avoid coupling system logic to presentation layers.

- **LLM-first explanation generation**  
  Rejected to keep the system grounded in verifiable facts.

- **Automatic architecture inference**  
  Rejected due to ambiguity and lack of reliable evidence.

Each rejection favored correctness and auditability
over feature richness.

---

## 7. Why Explicit Non-Goals Are Stated

Non-goals are stated explicitly to:
- Prevent scope creep
- Avoid misinterpretation by reviewers
- Make system limits clear and honest

This ensures the system is evaluated
for what it actually does, not what it could do.

---

## 8. Summary

CODE-Sherpa was designed with restraint.

Every major design choice favors:
- Determinism
- Clarity
- Verifiability
- Reviewer trust

Complexity was avoided not due to lack of ambition,
but to preserve correctness and credibility.
