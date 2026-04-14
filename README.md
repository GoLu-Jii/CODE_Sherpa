# CODE Sherpa 🏔️

<div align="center">
  <img src="https://img.shields.io/badge/version-v0.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/react-19-blue.svg" alt="React Setup">
  <img src="https://img.shields.io/badge/license-MIT-purple.svg" alt="License">
</div>

<br/>

**CODE Sherpa** is a deterministic code intelligence engine designed to provide advanced **Graph-RAG** retrieval, combining file, symbol, and semantic search models to analyze and understand entire repositories.

Featuring a high-performance Python FastAPI backend and a sleek, developer-first React telemetry dashboard UI, CODE Sherpa turns raw codebases into interactively navigable architectures. In version 0.1, the engine is optimized exclusively for Python repositories.

---

## 🚀 Key Features

- **Graph-RAG Retrieval Engine:** Seamlessly combines abstract syntax tree (AST) graph data with semantic embeddings, enabling complex code structure queries.
- **Developer-centric Telemetry Dashboard:** A state-of-the-art UI featuring cipher-scrambled elements, responsive command bars, and a floating interactive architecture map using `@xyflow/react`.
- **Intelligent Repository Ingestion:** Simply provide a GitHub URL, and the engine automatically clones and generates deterministic structural maps alongside vector-based representations via **ChromaDB**.
- **Dual Interfaces:** Fully functional REST API paired with a standalone CLI tool for automation and continuous integration pipelines.
- **Built-in Session Cleanup:** Effortless management of ChromaDB sessions, keeping your local data clean across restarts.

## 🛠️ Technology Stack

**Frontend Interface (`/frontend`)**
* **Framework:** React 19 + Vite
* **State Management:** Zustand
* **Graph Visualization:** React Flow (`@xyflow/react`)
* **Styling:** TailwindCSS 4 + Lucide React

**Intelligence Engine (`/backend`)**
* **Core:** Python 3.8+ & FastAPI
* **NLP / LLM:** Groq API
* **Vector Store:** ChromaDB (Local persistence)

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed and set up on your machine:

1. **Python 3.8 or higher**
2. **Node.js (LTS recommended) & npm**
3. **Groq API Key:** Required for Large Language Model processing. Grab one from the [Groq Console](https://console.groq.com).
4. **Chroma Token:** Required for ChromaDB authentication if hosted, though local configurations are handled automatically.

---

## 💻 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/CODE_Sherpa.git
cd CODE_Sherpa
```

### 2. Backend Environment (API & Engine)

Navigate to the project root and set up your virtual environment:

```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
# source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

Set up your required environment variables:

```bash
# Windows PowerShell
$env:GROQ_API_KEY="your_groq_key_here"
$env:CHROMA_TOKEN="your_chroma_token_here"
```

### 3. Frontend Environment (Telemetry Dashboard)

Open a new terminal window, navigate to the frontend directory, and install dependencies:

```bash
cd frontend
npm install
```

Configure your local environment variables:
```bash
cp .env.example .env
# Ensure VITE_API_URL is pointing to your local backend (e.g., http://localhost:8000)
```

---

## 🏃‍♂️ Running the System

Start both systems to experience the full CODE Sherpa interface.

### Start the Intelligence Backend

```bash
# Ensure .venv is activated
python backend/app/main.py server
```
*The API will be available at: http://localhost:8000*

### Start the Telemetry UI

```bash
cd frontend
npm run dev
```
*The dashboard will be available at: http://localhost:5173*

---

## 🔌 API & CLI Usage Guide

If your integrations require headless interactions, you can use the REST API or the provided CLI.

### CLI Analysis

Quickly analyze a local codebase directly from your terminal:

```bash
python backend/app/main.py analyze <absolute_path_to_local_repo>
```

**Outputs generated:**
* `demo/analysis.json` - Comprehensive structural graph data.
* `demo/flowchart.md` - Mermaid diagram mapping the repository's architecture.

### API Reference Examples

**1. Ingest a Repository:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

**2. Query via Graph-RAG:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "repo_id", "query": "Explain how the session object is initialized."}'
```

---

## 🚧 Troubleshooting

* **Backend Port Conflicts:** If port 8000 is occupied, launch the server on an alternative port:
  `python backend/app/main.py server --port 8001`
* **Local ChromaDB Issues:** Ensure the `chroma_local_data` directory is not corrupted or locked by another process. For a clean slate, you can wipe it between sessions.
* **CLI Pathing:** If the CLI fails to resolve a file tree, make sure you are passing the absolute file system path (e.g., `C:\Projects\target-repo`).

---

## 📄 License

This project is licensed under the terms of the MIT License. See the [LICENSE](LICENSE) file for more information.
