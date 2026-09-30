# AI Software Engineer Agent 🤖⚡

An autonomous, full-stack AI Software Engineer Agent built with Python, FastAPI, NetworkX code graph analysis, AST symbol parsing, multi-LLM support (OpenAI, Claude, Gemini, Ollama), and an interactive Web Dashboard.

## Key Capabilities ⭐

- 🔍 **Read & Ingest GitHub Repositories**: Clones remote GitHub repositories or ingests local code directories.
- 📐 **Architecture Knowledge Graph**: Parses AST syntax trees and extracts symbols (functions, classes, imports) into an interactive Vis.js dependency graph (with optional Neo4j database sync).
- 💡 **Deep Code Explainer**: Provides line-by-line breakdown of source files, inputs, outputs, and design patterns.
- 🛠️ **Autonomous Bug Hunter & Fixer**: Locates bug root causes from issue descriptions/tracebacks, generates exact code patches, and applies fixes to workspace files directly.
- 🧪 **Unit Test Generator**: Automates writing pytest / jest unit test suites with mocks and high assertion coverage.
- 🔍 **PR Code Reviewer**: Performs code quality, security, and performance audits on git diffs or pull requests.
- 🚀 **Automated PR Creator**: Creates git branches, commits updated code, and opens GitHub Pull Requests directly using the GitHub REST API.

---

## Tech Stack 🛠️

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic
- **AST & Code Parser**: Python `ast`, Regex multi-language symbol extractor (JS/TS/Go/Java/C++)
- **Knowledge Graph**: NetworkX, Neo4j Graph Database Integration
- **Git & GitHub Integration**: GitPython, PyGithub, HTTP ZIP fallback parser, GitHub REST API
- **AI / LLM Engine**: OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, Google Gemini 2.5, Ollama (Local LLM)
- **Frontend Dashboard**: Vanilla HTML5/CSS3 (Glassmorphic dark design), JavaScript (ES6+), Vis.js, Prism.js, Marked.js
- **Containerization**: Docker, Docker Compose

---

## Quick Start 🚀

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Configure Environment Variables (Optional)
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
GITHUB_TOKEN=ghp_...
DEFAULT_PROVIDER=gemini
```
*(Note: API keys can also be configured dynamically directly within the Web UI Settings tab).*

### 3. Launch Application
```bash
python -m backend.main
```
Or run with uvicorn:
```bash
uvicorn backend.main:app --reload --port 8000
```
Open your browser at: **`http://localhost:8000`**

---

## Docker Deployment 🐳

Run the entire stack (FastAPI Backend + Web Dashboard + Neo4j Database) with Docker Compose:

```bash
docker-compose up --build
```
- Dashboard & API: `http://localhost:8000`
- Neo4j Browser: `http://localhost:7474`
