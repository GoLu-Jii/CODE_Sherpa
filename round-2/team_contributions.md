# Team Contributions & Ownership

This document explicitly defines ownership and responsibility for each team member in CODE-Sherpa.
Each role has clearly scoped files and non-overlapping responsibilities to ensure architectural clarity,
accountability, and reviewability.

No member claims ownership outside the files listed below.

---

## Member 1 — Static Code Analyzer Engineer
 
## Name - Gaurav Joshi

**Owned folders**
- `analyzer/`

**Owned files**
- `analyzer/parser.py`
- `analyzer/dependency.py`
- `analyzer/analyzer.py`

**Responsibility**

Member 1 implemented the deterministic static analysis core of CODE-Sherpa.
This component traverses source repositories, parses code using abstract syntax trees (AST),
and extracts factual structure such as functions, imports, call relationships, and entry points.
The analyzer produces a verified, structured JSON representation that serves as the single
source of truth for all downstream components.

This role explicitly excludes CLI orchestration, visualization, guided explanations,
and any form of AI inference.

---

## Member 2 — Guided Tour & Explanation Engineer

## Name - Parth Joshi

**Owned folders**
- `tour/`

**Owned files**
- `tour/tour_generator.py`
- `tour/templates.py`

**Responsibility**

Member 2 designed the guided explanation layer that transforms static analyzer output into
a step-by-step onboarding experience.
This component determines a logical learning order, selects key flows,
and generates structured explanation steps using predefined templates.

This role does not perform static code parsing, dependency extraction,
flowchart generation, or system orchestration.

---

## Member 3 — Flowchart & Visualization Engineer

## Name - Prateek Banoula

**Owned folders**
- `flowchart/`

**Owned files**
- `flowchart/flow_builder.py`
- `flowchart/exporter.py`

**Responsibility**

Member 3 implemented the visualization layer responsible for converting analyzer JSON
into a logical dependency graph.
This graph models files and functions as nodes and represents call and import relationships as edges.
The component exports this structure into visual artifacts such as Mermaid-based flowcharts,
enabling repository-level comprehension without reading source code.

This role does not parse source files, generate textual explanations,
or manage execution flow.

---

## Member 4 — CLI , Integration and Quality Controller

## Name - Raj Pratap

**Owned areas**
- Member 4 owns the system integration layer, responsible for connecting all independently developed modules into a single     
executable pipeline.


**Owned files**
- `cli/main.py`
- `requirements.txt`

**Responsibility**

Member 4 implemented the system integration layer during Round-1 by owning the CLI entry point
that orchestrates the analyzer, tour generator, and flowchart generator as a single executable pipeline.
This role ensured correct invocation order, path validation, and end-to-end execution consistency
across components.