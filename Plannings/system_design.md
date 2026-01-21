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

This document describes the **target architecture** for the CODE-Sherpa Platform, moving beyond the Round-1 prototype.

The goal is to clearly define:

-   The transition to a **Hosted, API-First Platform**.
-   The role of the **Core Engine** vs. the **Web Interface**.
-   How the system delivers **Grounded, Explainable Code Intelligence**.

---

### 1.2 Explicit Non-Goals & Constraints CODE-Sherpa does not:

-   Allow AI to hallucinate code structure (AI is constrained by AST facts).
-   Execute code at runtime.
-   Modify source code (we are a read-only observability platform).
-   **Crucially:** \We do not use AI as an Architect, only as an Explainer. The AST is the Judge; the AI is the Narrator.

---

## 2. Architectural Principles

CODE-Sherpa follows a small set of strict principles.

### 2.1 API-First & Hosted
The core intelligence lives in a hosted engine, accessible via API. The UI (Web, IDE) is just a consumer of this API. This enables a single source of truth across all tools.

### 2.2 Deterministic Behavior
-   Identical input repositories produce identical outputs.
-   No probabilistic or heuristic behavior in the structural layer.

### 2.3 Static-Only Understanding
-   All understanding comes from static source code inspection.
-   No runtime execution or dynamic tracing.

### 2.4 Evidence-Driven Outputs
-   Every explanation and visual is derived from verified code structure.
-   No guessing or hallucination.

---

## 3. High-Level Architecture

CODE-Sherpa is a **Cloud-Native Code Intelligence Platform**.

**The Stack:**

1.  **Platform Layer (The API):** Receives requests, manages jobs, serves the Knowledge Graph.
2.  **Engine Layer (The Brain):** Stateless workers that clone repos, run AST analysis, and build the graph.
3.  **Enrichment Layer:** Semantic processing (LLM) that annotates the graph.
4.  **Interface Layer:**
    *   **Web Platform (Primary):** Rich, interactive system maps and tours.
    *   **IDE Extensions (Secondary):** Thin clients that pull data from the API.

**Component Communication Flow:**
-   User (Web/IDE) -> **Sherpa API** -> Job Queue
-   **Worker** -> Clones Repo -> Runs Analysis -> Saves **Canonical Knowledge Model**
-   **Sherpa API** -> Serves Model to Web/IDE

See: `diagrams/system_architecture.png` (needs update)

---

## 4. Core Components

Each component below represents a stable architectural boundary.

---

### 4.1 Interface Layer

#### 4.1.1 Web Application (Primary Interface)
**Responsibility:**
-   The "Google Maps" for your codebase.
-   Interactive, zoomable system diagrams.
-   Team collaboration (sharing tours, annotations).
-   Onboarding hubs ("Start here to learn Auth Service").

#### 4.1.2 VS Code Extension (Secondary Interface)
**Responsibility:**
-   A **thin client** that connects to the Sherpa API.
-   Overlays the "Guided Tour" directly on the user's active editor.
-   Does *no* heavy lifting locally.

---

### 4.2 The Hosted Engine (Core)

**Responsibility:**
-   Scalable, stateless job runner.
-   Takes a Repo URL -> Returns a Knowledge Graph.

**Components:**
1.  **Repo Cloner:** Ephemeral storage of source code.
2.  **Static Analyzer:** Language-specific drivers (Python AST, Tree-sitter for others).
3.  **Graph Builder:** Unifies analysis into the **Canonical Code Knowledge Model**.

---

### 4.3 Unified Code Knowledge Model (JSON/Graph)

**Responsibility:**
-   The "Database" of the code.
-   Represents Files, Functions, Classes, and their exact relationships.
-   **Single Source of Truth** for all interfaces.

---

### 4.4 Semantic Enrichment Layer (The "Sherpa Narrator")

**Responsibility:**
-   Adds the "Why" to the "What".
-   Consumes the Verified Graph components.
-   Queries LLMs to explain *specific* nodes (e.g., "Explain the purpose of this auth logic").
-   **Constraint:** Can never add nodes that don't exist in the AST.

---

### 4.5 Generators (Tour & Flowchart)

**Responsibility:**
-   **Tour Generator:** Algorithms to determine the "optimal learning path" (e.g., BFS from entry points, topological sort).
-   **Flowchart Generator:** Renders the graph for visual consumption (Mermaid/ReactFlow).


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
