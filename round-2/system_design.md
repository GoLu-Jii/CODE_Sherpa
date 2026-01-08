# CODE-Sherpa — System Design

> **Authority Notice**
>
> This document defines the system architecture of CODE-Sherpa.
> It specifies component boundaries, interfaces, guarantees,
> and explicit non-goals.
>
> Explanatory or rationale documents do not override this design.

---

## 1. Purpose & Scope

### 1.1 Purpose of This Document

This document describes the architecture of CODE-Sherpa as a complete,
deterministic system for understanding codebases through static analysis.

The goal is to clearly define:

- What the system does
- How components interact
- What guarantees the system provides
- What the system intentionally refuses to do

The system described here reflects the current implemented behavior.
No features or intelligence are implied beyond what is defined.

---

### 1.2 Explicit Non-Goals

CODE-Sherpa does **not**:

- Add intelligence or inference beyond code facts
- Execute or trace code at runtime
- Integrate with IDEs or editors
- Modify source code
- Learn from user behavior
- Claim semantic or architectural intent

The system prioritizes correctness, clarity, and determinism over breadth.

---

## 2. Architectural Principles

CODE-Sherpa follows a small set of strict principles.

### 2.1 Deterministic Behavior

- Identical input repositories produce identical outputs
- No probabilistic or heuristic behavior
- No hidden state between runs

---

### 2.2 Static-Only Understanding

- All understanding comes from static source code inspection
- No runtime execution
- No dynamic tracing or profiling

---

### 2.3 Evidence-Driven Outputs

- Every explanation and visual is derived from verified code structure
- No guessing or hallucination
- No interpretation beyond extracted facts

---

### 2.4 Pipeline Isolation

- Each component has a single responsibility
- Components communicate only through structured outputs
- No shared internal state

---

## 3. High-Level Architecture

CODE-Sherpa is organized as a linear, deterministic pipeline.

At a high level:

1. A user invokes the system through a CLI
2. Source code is statically analyzed
3. Extracted facts are stored in a unified JSON model
4. Multiple generators consume the same model
5. Artifacts are written to disk

All downstream understanding is grounded in one verified source of truth.

See: `diagrams/system_architecture.png`

---

## 4. Core Components

Each component below represents a stable architectural boundary.

---

### 4.1 CLI / Trigger Layer

**Responsibility**

- Accept repository path and command
- Validate inputs
- Orchestrate a single pipeline execution

**Notes**

- Stateless
- Contains no analysis logic
- Does not modify data semantics

---

### 4.2 Static Analyzer

**Responsibility**

- Traverse source files
- Parse code using AST
- Extract verified structural facts

**Extracted Facts**

- Files
- Functions
- Imports
- Function calls
- Entry points

**Constraints**

- Static inspection only
- Language-specific parsing
- No runtime interpretation

The analyzer is the only component that reads raw source code.

---

### 4.3 Unified Code Knowledge Model (JSON)

**Responsibility**

- Represent extracted facts in a single structured format
- Act as the system’s single source of truth

**Characteristics**

- Deterministic
- Fully derived from analyzer output
- Stable schema

Downstream components do not re-analyze source code.

---

### 4.4 Tour Generator

**Responsibility**

- Convert code structure into a guided learning order
- Generate step-by-step explanation artifacts

**Input**

- Unified Code Knowledge Model (JSON)

**Behavior**

- Orders learning from entry points to core logic
- Produces structured explanation steps

**Constraints**

- No inference beyond extracted facts
- No architectural guessing

---

### 4.5 Flowchart Generator

**Responsibility**

- Convert structural facts into a visual overview

**Input**

- Unified Code Knowledge Model (JSON)

**Behavior**

- Nodes represent files or functions
- Edges represent calls or dependencies
- Exports diagrams (e.g., Mermaid)

All visuals are derived, never manually drawn.

---

### 4.6 Artifact Output Layer

**Responsibility**

- Persist generated artifacts to disk

**Artifacts Include**

- Guided explanation steps
- Flowchart diagrams
- Supporting metadata

Artifacts are reproducible and inspectable.

---

## 5. Component Interfaces

This section defines what each component guarantees
and what it explicitly does not guarantee.

---

### 5.1 CLI Interface

**Input**

- Repository path
- Execution command

**Output**

- Pipeline execution trigger
- Status reporting

**Guarantees**

- Validated input
- Single execution per invocation

**Non-Guarantees**

- No correctness guarantees about analysis results

---

### 5.2 Analyzer Interface

**Input**

- Repository path

**Output**

- Structured JSON of code facts

**Guarantees**

- Deterministic output
- Static-only analysis
- Best-effort extraction

**Non-Guarantees**

- No semantic understanding
- No architectural intent inference
- No completeness for invalid syntax

---

### 5.3 Unified Knowledge Model Interface

**Input**

- Analyzer output

**Output**

- Canonical JSON representation

**Guarantees**

- Single source of truth
- Stable schema

**Non-Guarantees**

- No enrichment or correction of data

---

### 5.4 Tour Generator Interface

**Input**

- Unified Knowledge Model

**Output**

- Ordered explanation steps

**Guarantees**

- All steps traceable to verified facts

**Non-Guarantees**

- No educational optimization claims

---

### 5.5 Flowchart Generator Interface

**Input**

- Unified Knowledge Model

**Output**

- Graph representation
- Diagram files

**Guarantees**

- Structural correctness
- Fact-derived visuals

**Non-Guarantees**

- No runtime behavior modeling
- No performance analysis

---

## 6. System Boundaries & Non-Goals

CODE-Sherpa will not:

- Execute code
- Infer architectural intent
- Support multiple languages
- Handle very large monorepos
- Integrate with IDEs
- Use AI as a source of truth
- Track users or analytics

These limits preserve correctness and clarity.

---

## 7. Authority Statement

This document defines:

- System structure
- Component boundaries
- Interfaces
- Guarantees and non-guarantees

Any future extension must either conform to this design
or explicitly revise this document.

---

## 8. Final Positioning

CODE-Sherpa is a deterministic system that:

1. Extracts verified code structure
2. Represents it as explicit data
3. Teaches it through text and visuals

The system prioritizes correctness and transparency
over inference or automation.
