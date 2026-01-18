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

This document describes the **planned architecture** for the complete CODE-Sherpa system,
building upon the Round-1 prototype foundation. It specifies how we plan to extend
the deterministic static analysis core with AI-assisted explanations and IDE integration.

The goal is to clearly define:

- How the full system will be structured
- How components will interact
- What guarantees the system will provide
- What the system intentionally refuses to do


---

### 1.2 Explicit Non-Goals & Constraints CODE-Sherpa does not:

- Allow AI to hallucinate code structure (AI is constrained by AST facts).
- Execute code at runtime.
- Modify source code.
- Crucially: We do not use AI as an Architect, only as an Explainer. The AST is the Judge; the AI is the Narrator.
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

CODE-Sherpa is organized as a linear, deterministic pipeline with optional
AI enrichment and IDE integration layers.

**Planned Full System Architecture:**

At a high level, the full system extends the Round-1 foundation:

1. **User Interface Layer:** User invokes through VS Code Extension (or CLI for backward compatibility)
2. **Analysis Layer:** Source code is statically analyzed (Round-1 foundation)
3. **Knowledge Model:** Extracted facts stored in unified JSON model (Round-1 foundation)
4. **Enrichment Layer (New):** AI-assisted semantic enrichment adds context (planned)
5. **Generation Layer:** Multiple generators consume the enriched model
6. **Presentation Layer:** Interactive tours in VS Code or artifacts on disk

All downstream understanding is grounded in one verified source of truth (the AST-derived knowledge model).

**Component Communication Flow:**
- User → VS Code Extension → Analysis Pipeline
- Analysis Pipeline → Unified JSON Model
- Unified JSON Model → AI Enrichment (optional) → Enriched Model
- Enriched Model → Tour Generator + Flowchart Generator
- Generators → VS Code Extension (for interactive display) OR Disk (for file output)

See: `diagrams/system_architecture.png`

---

## 4. Core Components

Each component below represents a stable architectural boundary.

---

### 4.1 User Interface Layer

**Responsibility**

- Accept user requests (repository path, commands)
- Validate inputs
- Orchestrate pipeline execution
- Present results to user

**Components:**

**4.1.1 VS Code Extension (Planned - Primary Interface)**
- Provides interactive guided tours within the editor
- Opens files and highlights code sections automatically
- Displays explanations in webview panels
- Enables step-by-step navigation through learning path
- Supports comprehension checks and user interaction

**4.1.2 CLI Interface (Round-1 Foundation - Backward Compatibility)**
- Accept repository path and command
- Validate inputs
- Orchestrate pipeline execution
- Output artifacts to disk

**Notes**

- Stateless execution
- Contains no analysis logic
- Does not modify data semantics
- VS Code Extension is the planned primary interface; CLI remains for automation/backward compatibility

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

### 4.4.5 Semantic Enrichment Layer (The "Sherpa Brain") - Planned

**Responsibility**: Enriches the static AST model with semantic context and explanations.

**Input:**
- Verified AST Nodes from Unified Knowledge Model
- Raw code snippets for context

**Output:**
- AI-generated annotations appended to the JSON model
- Explanations of code purpose and design patterns
- Context about why code exists (not just what it does)

**Constraints:**
- Constrained to explain only nodes provided by the Analyzer
- Cannot invent new code structures
- Must be grounded in verified AST facts
- AI acts as Narrator, not Architect (AST is the source of truth)

**Implementation Notes:**
- Uses LLM API (planned integration)
- Applies only after static analysis completes
- Optional layer - system can operate without it (falls back to template-based explanations)

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

### 4.6 Presentation & Output Layer

**Responsibility**

- Present generated artifacts to users
- Support interactive exploration (planned)
- Persist artifacts to disk (when needed)

**Components:**

**4.6.1 VS Code Extension Presentation (Planned - Primary)**
- Interactive guided tours within editor
- Step-by-step navigation
- Code highlighting and file opening
- Comprehension checks and user interaction
- Real-time display of explanations and flowcharts

**4.6.2 File-Based Output (Round-1 Foundation)**
- Persist artifacts to disk for offline viewing
- Guided explanation steps (JSON format)
- Flowchart diagrams (Mermaid format)
- Supporting metadata

**Artifacts Include**

- Guided explanation steps
- Flowchart diagrams
- Supporting metadata
- AI-generated annotations (when enrichment layer is active)

Artifacts are reproducible and inspectable.

---

## 6. Component Interfaces

This section defines what each component guarantees
and what it explicitly does not guarantee.

---

### 6.1 User Interface Layer Interface

**Input**

- Repository path
- Execution command (analyze, etc.)
- User preferences (enable/disable AI enrichment, output format)

**Output**

- Pipeline execution trigger
- Status reporting
- Interactive tours (VS Code Extension) or file artifacts (CLI)

**Guarantees**

- Validated input
- Single execution per invocation
- Clear error messages for invalid inputs

**Non-Guarantees**

- No correctness guarantees about analysis results
- VS Code Extension requires VS Code environment

---

### 6.2 Analyzer Interface

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

### 6.3 Unified Knowledge Model Interface

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

### 6.4 Semantic Enrichment Layer Interface (Planned)

**Input**

- Unified Knowledge Model (JSON)
- Raw code snippets (for context)

**Output**

- Enriched Knowledge Model with AI annotations

**Guarantees**

- All annotations traceable to AST nodes
- No new code structures invented
- Backward compatible (enriched model extends base model)

**Non-Guarantees**

- No availability guarantees (depends on external LLM API)
- Explanations are best-effort (may not capture all nuance)
- Requires network connectivity for LLM access

---

### 6.5 Tour Generator Interface

**Input**

- Unified Knowledge Model

**Output**

- Ordered explanation steps

**Guarantees**

- All steps traceable to verified facts

**Non-Guarantees**

- No educational optimization claims

---

### 6.6 Flowchart Generator Interface

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

## 7. System Boundaries & Non-Goals

CODE-Sherpa will not:

- Execute code at runtime
- Infer architectural intent beyond static analysis
- Support multiple languages in initial version (Python-only)
- Handle extremely large monorepos without limits (see scalability strategy)
- Use AI as a source of structural truth (AI only enriches, never defines structure)
- Track users or analytics without explicit consent
- Modify source code
- Support real-time collaborative editing (single-user focused)

**Note:** VS Code integration is planned and contradicts the "no IDE integration" constraint
that may have been stated earlier. The system will integrate with VS Code as the primary interface,
while maintaining CLI compatibility.

These limits preserve correctness and clarity.

---

## 8. Authority Statement

This document defines:

- System structure
- Component boundaries
- Interfaces
- Guarantees and non-guarantees

Any future extension must either conform to this design
or explicitly revise this document.

---

## 9. Final Positioning

CODE-Sherpa is a deterministic system (with optional AI enhancement) that:

1. Extracts verified code structure through static analysis
2. Represents it as explicit, structured data
3. Optionally enriches it with AI-generated explanations
4. Teaches it through interactive tours and visualizations

The system prioritizes correctness and transparency over inference or automation.
AI is used to enhance explanations, not to determine code structure.

**Architecture Evolution:**
- **Round-1:** Established deterministic foundation (implemented)
- **Full Solution:** Adds AI enrichment and IDE integration (planned, described in this document)
- **Future:** May extend to additional languages, enhanced AI capabilities, etc.
