# CODE Sherpa

**Theme:** Open Innovation  
**Project Nature:** *Hosted, API-First Code Intelligence Platform*

---

## 📑 Table of Contents

- [CODE Sherpa](#code-sherpa)
  - [📑 Table of Contents](#-table-of-contents)
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

We believe that chat bots and code summarizers are becoming commodities. The true unsolved problem is **grounded system understanding**—knowing not just what a line of code does, but how it fits into the entire machine, with a level of trust that allows for auditing and critical decision making.

---

## Problem Statement

Developers, managers, and auditors struggle to grasp the "big picture" of complex or unfamiliar codebases.

-   **Static Documentation** is dead on arrival.
-   **IDE Navigation** requires you to already know what you are looking for.
-   **AI Chat (RAG)** hallucinates structure and lacks a holistic view of system architecture.

There is no "Google Maps for Code"—a trustworthy, explorable, and guided way to learn a system from the ground up.

---

## The Solution: CODE-Sherpa Platform

CODE-Sherpa is a **hosted, API-first code intelligence platform**. It produces a canonical code knowledge model that serves as the single source of truth for understanding a repository.

### Core Engine (The Brain)
*   **Stateless Analysis Jobs:** fast, deterministic static analysis (AST-based).
*   **Structured Outputs:** a verified JSON graph of the entire system.
*   **Explainability Layer:** AI used strictly as a **narrator**, never as a source of truth.

### Primary Interface: The Web Platform
A collaborative, editor-agnostic space for team understanding.
*   **Upload & Analyze:** Drop a GitHub URL, get a system map.
*   **Interactive System Map:** Visual, zoomable architecture diagrams.
*   **Guided Learning Paths:** "Zero-to-Hero" tours for onboarding new engineers.
*   **Change-Impact Exploration:** Visually trace how a PR affects the wider system.

### Secondary Interfaces
*   **VS Code Extension:** A thin client for developers in the flow.
*   **CLI:** For CI/CD pipelines and power users.
*   **API:** For internal tools and agents to access our canonical knowledge model.

---

## Our Core Philosophy

We are building a platform where **trust is the feature**. Our design goals are:

1.  **Deterministic Truth**: Unlike probabilistic models, we build on a rigid foundation of AST analysis and graph theory.
2.  **Zero Structural Hallucinations**: We guarantee that every node and relationship in our graph exists in the codebase.
3.  **System-Level Context**: We prioritize the holistic view—explaining the "forest" before the "trees"—moving beyond snippet-based understanding.
4.  **The Narrator Pattern**: AI is used strictly to explain verified facts, never to architect or invent structure.

---

## System Overview

The CODE Sherpa system operates as a **deterministic pipeline** with an **optional enrichment sidecar**:

1.  **Repository Analysis**: The codebase is analyzed using static analysis to extract verified structural facts (AST-based).
2.  **Canonical Modeling**: These facts form the "Unified Model" (`analysis.json`), which serves as the single source of truth.
3.  **Parallel Generation**:
    *   **Learning Path**: A guided tour is generated directly from the verified model.
    *   **Visualization**: A flowchart is generated directly from the verified model.
4.  **Semantic Enrichment (Optional/Frozen)**: An AI layer runs *independently* to generate a sidecar file (`annotations.json`) providing natural language explanations. *(Note: Currently frozen/disabled in the CLI).*

This approach ensures the critical path is **fast, deterministic, and offline-capable**, while AI insights are treated as an additive layer context.

---

## How to Run the Prototype

### Current Prototype Status

While our vision is a hosted platform, the **current implementation (Round-2)** is a functional **local CLI tool** serving as the foundational engine.

**Capabilities:**
*   **Language Support:** Python (`.py` files) via AST analysis.
*   **Analysis:** Extracts files, functions, imports, and call graphs.
*   **Enrichment:** Optional integration with Groq API for AI explanations (sidecar mode). *(Currently disabled)*
*   **Outputs:**
    *   `analysis.json`: Raw structural data.
    *   `learning_order.json`: A proposed guided tour path.
    *   `flowchart.md`: Mermaid diagram of file dependencies.
    *   `annotations.json`: Sidecar file with AI explanations (if enabled).

This prototype validates the **Deterministic Engine** core of the architecture.

### Prerequisites

- **Python 3.7 or higher** (Python 3.12+ recommended)
- **Install dependency:** `requests`
  ```bash
  pip install requests
  ```
- **Optional (for semantic enrichment):**
  - Set `GROQ_API_KEY` in your environment (enables LLM-backed explanations)
  - Internet access (enrichment calls the Groq API)
- **Language Support:** The prototype currently supports **Python repositories only**. It analyzes `.py` files and uses Python's AST (Abstract Syntax Tree) for code analysis.

Verify your Python version:
```bash
python --version
```

### Quick Start

1. **Navigate to the project directory:**
   ```bash
   cd CODE_Sherpa__HackTheWinter-SecondWave
   ```

2. **Install `requests` (if not already installed):**
   ```bash
   pip install requests
   ```

3. **(Optional) Enable semantic enrichment via Groq:**
   ```powershell
   # Windows PowerShell
   $env:GROQ_API_KEY="your_api_key_here"
   ```
   ```bash
   # Linux / Mac
   export GROQ_API_KEY="your_api_key_here"
   ```

4. **Run the pipeline on a repository:**
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

- **`demo/analysis.json`** — Complete code analysis including entry points, dependencies, and call graphs. **(Single Source of Truth)**
- **`demo/learning_order.json`** — Structured learning path generated from the analysis.
- **`demo/flowchart.md`** — specific visual dependency graph in Mermaid format.
- **`demo/annotations.json`** — **(Optional)** Sidecar file containing AI-generated explanations for files and functions. Only generated if `GROQ_API_KEY` is present.

### Viewing Results

**View the analysis:**
```bash
# Windows PowerShell
Get-Content demo/analysis.json

# Windows CMD / Linux / Mac
type demo/analysis.json
```

**View the learning order:**
```bash
Get-Content demo/learning_order.json
```

**View the flowchart:**
```bash
Get-Content demo/flowchart.md
```

**View the AI annotations (if enabled):**
```bash
Get-Content demo/annotations.json
```

The flowchart can be visualized using any Mermaid-compatible viewer (e.g., GitHub, VS Code with Mermaid extension, or online Mermaid editors).

### Expected Output

When you run the command, you should see:
```
Running static analysis...
Analysis completed

Generating tour...
Tour generated

Generating flowchart...
Flowchart exported

Enrichment layer is currently frozen. Skipping.

Pipeline completed successfully
```

**Notes:**
- **Performance**: Tour and Flowchart generation are now practically instant as they don't wait for the AI.
- **Resilience**: If Enrichment fails or is skipped, the rest of the pipeline functions normally.

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

**`ModuleNotFoundError: No module named 'requests'`:**
- Install the dependency:
  ```bash
  pip install requests
  ```

**Module not found errors:**
- Ensure you're running from the project root directory
- Verify all folders (`analyzer/`, `cli/`, `tour/`, `flowchart/`, `enrich/`) exist

### Testing Individual Components

You can also run individual components separately:

**Test analyzer only:**
```bash
python -c "from analyzer.analyzer import build_unified_model; import json; result = build_unified_model('sample_repo'); print(json.dumps(result, indent=2))"
```

**Test tour builder:**
```bash
python tour/tour_builder.py demo/analysis.json
```

**Test flowchart builder:**
```bash
python flowchart/flow_builder.py demo/analysis.json
```

---


## System Architecture

CODE-Sherpa is designed as a **deterministic, static-analysis–driven system** that prioritizes speed and structural truth.

The system is organized as a decoupled pipeline:

1.  **Core Analysis**: Source code -> `analysis.json` (Unified Model).
2.  **Derived Views**: `analysis.json` -> Tour & Flowchart (Deterministic, Fast).
3.  **Optional Context**: `analysis.json` + AI -> `annotations.json` (Semantic Sidecar).

This architecture allows the system to provide immediate value (structure, maps, learning order) even without an internet connection or API keys, while "lighting up" with AI explanations when available.
