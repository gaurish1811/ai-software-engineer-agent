# AI Software Engineer Agent 🤖⚡

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-Render-brightgreen.svg)](https://ai-software-engineer-agent-e922.onrender.com)
[![CI](https://github.com/gaurish1811/ai-software-engineer-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/gaurish1811/ai-software-engineer-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)
![LLM](https://img.shields.io/badge/LLM-GPT4o%20%7C%20Claude%20%7C%20Gemini%20%7C%20Ollama-blueviolet.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An autonomous, full-stack AI Software Engineer Agent that can **read codebases, find bugs, write tests, review PRs, and open GitHub Pull Requests** — powered by GPT-4o, Claude 3.5, Gemini 2.5, or a local Ollama model.

---

## 🌟 Key Features

| Feature | Description |
|---|---|
| 🔍 **GitHub Repo Ingestion** | Clones any public/private GitHub repo or ingests local directories |
| 📐 **Architecture Knowledge Graph** | Parses AST trees → extracts functions, classes, imports → renders interactive Vis.js dependency graph |
| 💡 **Deep Code Explainer** | Line-by-line breakdown of any file: inputs, outputs, design patterns |
| 🛠️ **Autonomous Bug Hunter & Fixer** | Locates root cause from issue description → generates code patch → applies fix to file |
| 🧪 **Unit Test Generator** | Writes full pytest/jest test suites with mocks and edge cases |
| 🔍 **PR Code Reviewer** | Security, performance, and quality audit on git diffs or pull requests |
| 🚀 **Automated PR Creator** | Creates branch → commits fix → opens GitHub Pull Request via REST API |

---

## 🏗️ System Architecture

```
[ GitHub Repo / Local Directory ]
            │
            ▼
[ AST Parser + Symbol Extractor ]  ── Python ast, Regex (JS/TS/Go/Java/C++)
            │
            ▼
[ Knowledge Graph ]  ──────────────  NetworkX + optional Neo4j
            │
            ▼
[ LangChain-style Agent Loop ]  ───  Task routing + context injection
            │
            ▼
[ Multi-LLM Engine ]  ─────────────  GPT-4o / Claude 3.5 / Gemini 2.5 / Ollama
            │
            ▼
[ FastAPI REST API ]  ─────────────  Uvicorn, Pydantic v2
            │
            ▼
[ Web Dashboard ]  ────────────────  Vanilla HTML/CSS/JS, Vis.js, Prism.js
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2
- **AST & Code Parser**: Python `ast`, Regex multi-language symbol extractor (JS/TS/Go/Java/C++)
- **Knowledge Graph**: NetworkX, Neo4j Graph Database (optional)
- **Git & GitHub Integration**: GitPython, PyGithub, GitHub REST API
- **AI / LLM Engine**: OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, Google Gemini 2.5 Flash, Ollama (Local)
- **Frontend Dashboard**: Vanilla HTML5/CSS3 (Glassmorphic dark UI), Vis.js, Prism.js, Marked.js
- **Containerization**: Docker, Docker Compose

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/gaurish1811/ai-software-engineer-agent.git
cd ai-software-engineer-agent
pip install -r backend/requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
GITHUB_TOKEN=ghp_...
DEFAULT_PROVIDER=gemini
```
> API keys can also be set dynamically in the **Web UI → Settings tab** — no restart needed.

### 3. Launch
```bash
python -m backend.main
```
Open **`http://localhost:8000`** in your browser.

---

## 🐳 Docker Deployment

Run the full stack (FastAPI + Neo4j) with one command:
```bash
docker-compose up --build
```
- **Dashboard & API**: `http://localhost:8000`
- **Neo4j Browser**: `http://localhost:7474`

---

## ☁️ Cloud Deployment (Render)

One-click deploy via the included `render.yaml`:

1. Fork this repo
2. Go to [render.com](https://render.com) → **New** → **Blueprint**
3. Connect your forked repo
4. Add your `GEMINI_API_KEY` (or any LLM key) as an environment variable
5. Click **Apply** — live in ~3 minutes

---

## 📁 Project Structure

```
ai-software-engineer-agent/
├── backend/
│   ├── main.py          # FastAPI app entry point
│   ├── config.py        # Pydantic settings (env vars)
│   ├── api/             # REST API route handlers
│   └── core/            # Agent logic, AST parser, LLM engine
├── frontend/
│   ├── index.html       # Web dashboard
│   ├── app.js           # Dashboard logic (Vis.js, Prism.js)
│   └── styles.css       # Glassmorphic dark UI
├── Dockerfile
├── docker-compose.yml
├── render.yaml          # Render cloud deployment blueprint
└── test_agent.py        # Test suite
```
