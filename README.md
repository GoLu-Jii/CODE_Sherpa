# CODE Sherpa

**Status:** Backend API + CLI Fully Functional  

Deterministic code intelligence engine with Graph-RAG retrieval (file/symbol/semantic search).

## Quick Start

### Backend API
```bash
pip install -r backend/requirements.txt
export GROQ_API_KEY="your_key"
export CHROMA_TOKEN="your_token"
python backend/app/main.py server
# API at http://localhost:8000
```

### CLI Tool
```bash
python backend/app/main.py analyze sample_repo
# Outputs: demo/analysis.json + demo/flowchart.md
```

---

## Backend API

**Prerequisites:** Python 3.8+, Groq API key, Chroma Cloud account

**Setup:**
```bash
cd CODE_Sherpa
pip install -r backend/requirements.txt
```

**Environment:**
```bash
$env:GROQ_API_KEY="your_groq_key"
$env:CHROMA_TOKEN="your_chroma_token"
```

**Run:**
```bash
.venv\Scripts\Activate.ps1
python backend/app/main.py server
```

**Endpoints:**

`POST /ingest` – Clone & analyze GitHub repo
```json
{"github_url": "https://github.com/owner/repo"}
```

`POST /chat` – Query with Graph-RAG
```json
{"collection_id": "repo_id", "query": "What does file.py do?"}
```

**Examples:**
```bash
# Ingest
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "repo", "query": "What does exceptions.py do?"}'
```

---

## CLI Tool

**Prerequisites:** Python 3.8+ (no external dependencies)

**Usage:**
```bash
python backend/app/main.py analyze <repo_path>
```

**Examples:**
```bash
python backend/app/main.py analyze sample_repo
python backend/app/main.py analyze C:\Users\YourName\Projects\my_project
```

**Output:**
- `demo/analysis.json` – Structural graph
- `demo/flowchart.md` – Mermaid diagram

**View:**
```bash
Get-Content demo/analysis.json
Get-Content demo/flowchart.md
```

---

## Troubleshooting

**Backend API:**
- Port in use: `python backend/app/main.py server --port 8001`
- Groq key error: Verify at https://console.groq.com
- Chroma error: Check `CHROMA_TOKEN` environment variable

**CLI:**
- Encoding errors: `$env:PYTHONIOENCODING="utf-8"`
- Path not found: Use absolute paths like `C:\full\path\to\repo`
- Module errors: Run from project root and verify `backend/app/` folder exists
