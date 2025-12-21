CODE_Sherpa: An AI-Assisted System for Guided Codebase Understanding.

1. Architectural Overview:
CODE_Sherpa follows a modular, pipeline-oriented architecture that clearly separates deterministic code analysis from generative explanation logic. This separation ensures predictable behavior, improves explainability, and allows individual components to evolve independently. The system is designed with clear boundaries, controlled AI usage, and explicit data flow between stages.

2. High-level architecture:
The system consists of the following loosely coupled layers:
a. Repository Ingestion:
Accepts a repository and prepares a structured file layout for analysis.
b. Static Code Analysis:
Extracts code structure, dependencies, and relationships without execution.
c. Context Grounding:
Converts analysis results into structured semantic context for explanation.
d. Explanation Engine:
Generates guided, human-readable explanations from grounded context.
e. Developer Interface:
Displays interactive walkthroughs within the developer workflow.

<img width="2896" height="2791" alt="final_system_arch" src="https://github.com/user-attachments/assets/c374339b-1a0e-4934-bd4e-42b12fb1f180" />

4. System Workflow(End to End workflow):

1. Developer submits a source code repository
2. Repository structure is ingested and normalized
3. Static analysis extracts code structure and relationships
4. Grounded context is constructed from analysis artifacts
5. AI generates step-by-step explanations and guided tours
6. Results are presented through an interactive interface
<img width="2124" height="4964" alt="system_workflow" src="https://github.com/user-attachments/assets/81f37f5c-5e69-4cd1-ac8c-d66bddf0392f" />

4. Data Flow Diagrams (DFD):
1. DFD Level 0:
The developer provides a repository to CODE_Sherpa and receives structured explanations in return. Internal processing is abstracted to define clear system boundaries.
<img width="2066" height="1075" alt="dfd0" src="https://github.com/user-attachments/assets/b2c08129-2ee9-4897-9efa-7fa975bff988" />

3. DFD Level 1:
Source code flows through ingestion, analysis, context grounding, and explanation generation stages, producing intermediate artifacts that are progressively refined into human-readable guidance.
<img width="1730" height="3679" alt="dfd1-1" src="https://github.com/user-attachments/assets/ab9a9ff2-267c-4838-a194-8c94209d5014" />


5. Component-Level Architecture:
1. Repository Ingestion: Accepts and structures repositories.
2. Static Analysis: Extracts syntax, dependencies, and symbols.
3. Context Grounding: Converts analysis results into semantic context.
4. Explanation Engine: Generates guided walkthroughs using AI.
5. Developer Interface: Displays explanations interactively.

6. Sequence Flow:
-> A guided walkthrough begins with a developer request. The orchestration layer coordinates analysis and context preparation before invoking the explanation engine. Generated content is then returned to the interface in a controlled request–response flow, ensuring ordered execution and minimal coupling between components.
<img width="3107" height="2488" alt="sequence_diagram1" src="https://github.com/user-attachments/assets/07d990bc-c7be-404e-9c8d-709b86d81216" />

7. Technology Placement:
-> Backend: Repository handling, orchestration, static analysis
-> AI / ML: Explanation and guided tour generation
-> Interface: IDE extension or web-based UI
-> Integration: Communication between backend and interface
-> The architecture is tool-agnostic; technologies can be replaced without redesign.

8. Design Constraints:
-> Limited language support in the initial version
-> Repository size constrained for hackathon feasibility
-> Static analysis only (no runtime execution)
-> Read-only access to repositories
These constraints ensure a stable and demonstrable prototype.

9. Extensibility & Scalability Points:

10. Architecture Summary:
CODE_Sherpa addresses the challenge of understanding complex and unfamiliar codebases through a structured onboarding approach.
-> It combines deterministic static code analysis with grounded AI-based explanation generation.
-> The architecture follows a modular, layered design with clear separation of responsibilities.
-> Deterministic preprocessing ensures reliability before invoking generative components.
-> This design improves clarity, maintainability, and extensibility of the system.
-> The solution remains practical within hackathon constraints while being scalable for real-world developer onboarding.




