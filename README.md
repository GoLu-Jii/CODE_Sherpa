# CODE Sherpa

**Project Nature:** *Deterministic Code Intelligence Engine (CLI Prototype)*  
**Long-Term Vision:** *Hosted, API-First Platform*

### Project Status

This repository currently implements the **deterministic core engine** of the CODE-Sherpa platform as a local CLI tool.

The hosted web platform, API service, and editor integrations described below represent the **intended product direction** and are not yet implemented.

---

## ðŸ“‘ Table of Contents

- [CODE Sherpa](#code-sherpa)
  - [ðŸ“‘ Table of Contents](#-table-of-contents)
  - [Mission Statement](#mission-statement)
  - [Problem Statement](#problem-statement)
  - [The Solution: CODE-Sherpa Platform](#the-solution-code-sherpa-platform)
  - [Our Core Philosophy](#our-core-philosophy)
  - [System Overview](#system-overview)
  - [How to Run the Prototype](#how-to-run-the-prototype)
    - [Current Prototype Status](#current-prototype-status)
    - [Prerequisites](#prerequisites)
    - [Quick Start](#quick-start)
    - [Output Files](#output-files)
    - [Viewing Results](#viewing-results)
    - [Expected Output](#expected-output)
    - [Troubleshooting](#troubleshooting)
    - [Testing Individual Components](#testing-individual-components)
  - [System Architecture](#system-architecture)


---

## Mission Statement

**To provide a deterministic, explainable, system-level understanding of software repositories.**

We believe that chat bots and code summarizers are becoming commodities. The true unsolved problem is **grounded system understanding**â€”knowing not just what a line of code does, but how it fits into the entire machine, with a level of trust that allows for auditing and critical decision making.

---

## Problem Statement

Developers, managers, and auditors struggle to grasp the "big picture" of complex or unfamiliar codebases.

-   **Static Documentation** is dead on arrival.
-   **IDE Navigation** requires you to already know what you are looking for.
-   **AI Chat (RAG)** hallucinates structure and lacks a holistic view of system architecture.

There is no "Google Maps for Code"â€”a trustworthy, explorable, and guided way to learn a system from the ground up.

---

## The Vision: CODE-Sherpa Platform

CODE-Sherpa is designed to be a **hosted, API-first code intelligence platform**. It produces a canonical code knowledge model that serves as the single source of truth for understanding a repository.

### Core Engine (The Brain) - *Implemented*
*   **Stateless Analysis Jobs:** fast, deterministic static analysis (AST-based).
*   **Structured Outputs:** a verified JSON graph of the entire system.
*   **Explainability Layer:** AI used strictly as a **narrator**, never as a source of truth.

### Future Roadmap
The following components are part of the long-term vision but are **not yet implemented**:

#### Primary Interface: The Web Platform
A collaborative, editor-agnostic space for team understanding.
*   **Upload & Analyze:** Drop a GitHub URL, get a system map.
*   **Interactive System Map:** Visual, zoomable architecture diagrams.
*   **Guided Learning Paths:** "Zero-to-Hero" tours for onboarding new engineers.
*   **Visual Dependency Exploration:** Visual discovery to reason about potential change impact.

#### Secondary Interfaces
*   **VS Code Extension:** A thin client for developers in the flow.
*   **CLI:** For CI/CD pipelines and power users.
*   **API:** For internal tools and agents to access our canonical knowledge model.

---

## Our Core Philosophy

We are building a platform where **trust is the feature**. Our design goals are:

1.  **Deterministic Truth**: Unlike probabilistic models, we build on a rigid foundation of AST analysis and graph theory.
2.  **Zero Structural Hallucinations**: We guarantee that every node and relationship in our graph exists in the codebase.
3.  **System-Level Context**: We prioritize the holistic viewâ€”explaining the "forest" before the "trees"â€”moving beyond snippet-based understanding.
4.  **The Narrator Pattern**: AI is used strictly to explain verified facts, never to architect or invent structure.

---

## System Overview

The CODE Sherpa system operates as a **deterministic pipeline** that analyzes code structure:

1.  **Repository Analysis**: The codebase is analyzed using static analysis to extract verified structural facts (AST-based).
2.  **Canonical Modeling**: These facts form the "Unified Model" (`analysis.json`), which serves as the single source of truth.
3.  **Visualization**: A flowchart is generated directly from the verified model.

This approach ensures the pipeline is **fast, deterministic, and offline-capable**.

---

## How to Run the Prototype

### Current Prototype Status

While our vision is a hosted platform, the **current implementation ** is a functional **local CLI tool** serving as the foundational engine.

**Capabilities:**
*   **Language Support:** Python (`.py` files) via AST analysis.
*   **Analysis:** Extracts files, functions, imports, file dependencies, and resolved inter-file call edges.
*   **Outputs:**
    *   `analysis.json`: Raw structural data.
    *   `flowchart.md`: Mermaid diagram of file dependencies.

This prototype validates the **Deterministic Engine** core of the architecture.

### Prerequisites

- **Python 3.7 or higher** 
- **Core Engine Dependencies:**
  - None (Python standard library only)
- **Language Support:** The prototype currently supports **Python repositories only**. It analyzes `.py` files and uses Python's AST (Abstract Syntax Tree) for code analysis.

Verify your Python version:
```bash
python --version
```

### Quick Start

1. **Navigate to the project directory:**
   ```bash
   cd CODE_Sherpa
   ```

3. **Run the pipeline on a repository:**
   ```bash
   python cli/main.py analyze <repository_path>
   ```

   **Example with sample repository:**
   ```bash
   python cli/main.py analyze sample_repo
   ```

   **Example with your own repository:**
   ```bash
   python cli/main.py analyze C:\Users\YourName\Projects\my_project
   ```

### Output Files

After running, the following files will be generated in the `demo/` folder:

- **`demo/analysis.json`** – Complete code analysis including entry points, dependencies, raw calls, and resolved call edges (`metadata.resolved_call_edges`). **(Single Source of Truth)**
- **`demo/flowchart.md`** – specific visual dependency graph in Mermaid format.

### Viewing Results

**View the analysis:**
```bash
# Windows PowerShell
Get-Content demo/analysis.json

# Windows CMD / Linux / Mac
type demo/analysis.json
```

**View the flowchart:**
```bash
Get-Content demo/flowchart.md
```

The flowchart can be visualized using any Mermaid-compatible viewer (e.g., GitHub, VS Code with Mermaid extension, or online Mermaid editors).

### Expected Output

When you run the command, you should see:
```
Running static analysis...
Analysis completed

Generating flowchart...
Flowchart exported

Pipeline completed successfully
```

### Troubleshooting

**Encoding errors on Windows:**
If you encounter Unicode encoding issues, set the encoding environment variable:
```powershell
$env:PYTHONIOENCODING="utf-8"
python cli/main.py analyze sample_repo
```

**Repository path not found:**
- Use absolute paths: `python cli/main.py analyze C:\full\path\to\repo`
- Or relative paths: `python cli/main.py analyze ./repo_name`
- Ensure the path exists and contains Python files (`.py` extension)
- **Note:** Only Python repositories are currently supported

**Module not found errors:**
- Ensure you're running from the project root directory
- Verify all folders (`analyzer/`, `cli/`, `flowchart/`) exist

### Testing Individual Components

You can also run individual components separately:

**Test analyzer only:**
```bash
python -c "from analyzer.analyzer import build_unified_model; import json; result = build_unified_model('sample_repo'); print(json.dumps(result, indent=2))"
```

**Test flowchart builder:**
```bash
python flowchart/flow_builder.py demo/analysis.json
```

---


## System Architecture

CODE-Sherpa is designed as a **deterministic, static-analysisâ€“driven system** that prioritizes speed and structural truth.

The system is organized as a decoupled pipeline:

1.  **Core Analysis**: Source code -> `analysis.json` (Unified Model).
2.  **Derived Views**: `analysis.json` -> Flowchart (Deterministic, Fast).

This architecture ensures the system provides immediate value (structure and dependency visualization) in a fast, deterministic, and offline-capable manner.



