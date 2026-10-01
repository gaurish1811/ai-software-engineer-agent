from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from backend.core.repo_manager import RepoManager
from backend.core.code_analyzer import CodeAnalyzer
from backend.core.llm_provider import LLMProvider
from backend.core.agent_engine import AIAgentEngine
from backend.config import settings

router = APIRouter(prefix="/api")

repo_manager = RepoManager()
code_analyzer = CodeAnalyzer()
agent_engine = AIAgentEngine(repo_manager=repo_manager)

# Request Models
class CloneRepoRequest(BaseModel):
    repo_url_or_path: str

class ReadFileRequest(BaseModel):
    repo_path: str
    rel_path: str

class ExplainArchRequest(BaseModel):
    repo_path: str
    provider: Optional[str] = None
    api_key: Optional[str] = None

class ExplainCodeRequest(BaseModel):
    repo_path: str
    target_file: str
    provider: Optional[str] = None
    api_key: Optional[str] = None

class FixBugRequest(BaseModel):
    repo_path: str
    issue_description: str
    target_file: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None

class GenerateTestsRequest(BaseModel):
    repo_path: str
    target_file: str
    provider: Optional[str] = None
    api_key: Optional[str] = None

class ReviewPRRequest(BaseModel):
    git_diff_or_code: str
    provider: Optional[str] = None
    api_key: Optional[str] = None

class CreatePRRequest(BaseModel):
    repo_owner_repo: str  # e.g., "owner/repo"
    branch_name: str
    commit_message: str
    pr_title: str
    pr_body: str
    modified_files: Dict[str, str] # {rel_path: content}
    github_token: Optional[str] = None

# Routes

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "workspace_dir": settings.WORKSPACE_DIR,
        "active_llm_provider": settings.DEFAULT_PROVIDER,
        "github_token_configured": bool(settings.GITHUB_TOKEN or False)
    }

@router.post("/repo/clone")
def clone_repo(req: CloneRepoRequest):
    result = repo_manager.clone_or_load_repo(req.repo_url_or_path)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.get("/repo/tree")
def get_file_tree(repo_path: str):
    tree = repo_manager.get_repo_file_tree(repo_path)
    return {"repo_path": repo_path, "count": len(tree), "files": tree}

@router.post("/repo/read-file")
def read_file(req: ReadFileRequest):
    try:
        content = repo_manager.read_file_content(req.repo_path, req.rel_path)
        return {"repo_path": req.repo_path, "rel_path": req.rel_path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/repo/graph")
def get_codebase_graph(repo_path: str):
    file_tree = repo_manager.get_repo_file_tree(repo_path)
    files_ast = []
    
    for f in file_tree[:60]: # Analyze up to 60 code files for graph
        if f["is_code"]:
            try:
                content = repo_manager.read_file_content(repo_path, f["path"])
                if f["extension"] == ".py":
                    ast_data = code_analyzer.parse_python_file(f["path"], content)
                else:
                    ast_data = code_analyzer.parse_generic_file(f["path"], content, f["extension"])
                files_ast.append(ast_data)
            except Exception:
                pass

    graph_data = code_analyzer.build_dependency_graph(files_ast)
    return {"repo_path": repo_path, "graph": graph_data}

@router.post("/agent/explain-arch")
def explain_architecture(req: ExplainArchRequest):
    try:
        llm = LLMProvider(provider=req.provider, api_key=req.api_key)
        res = agent_engine.explain_architecture(req.repo_path, llm)
        if res.get("status") == "error":
            raise HTTPException(status_code=500, detail=res.get("message"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/explain-code")
def explain_code(req: ExplainCodeRequest):
    try:
        llm = LLMProvider(provider=req.provider, api_key=req.api_key)
        res = agent_engine.explain_code(req.repo_path, req.target_file, llm)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/fix-bug")
def fix_bug(req: FixBugRequest):
    try:
        llm = LLMProvider(provider=req.provider, api_key=req.api_key)
        res = agent_engine.fix_bug(req.repo_path, req.issue_description, llm, req.target_file)
        if res.get("status") == "error":
            raise HTTPException(status_code=500, detail=res.get("message"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/generate-tests")
def generate_tests(req: GenerateTestsRequest):
    try:
        llm = LLMProvider(provider=req.provider, api_key=req.api_key)
        res = agent_engine.generate_unit_tests(req.repo_path, req.target_file, llm)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/review-pr")
def review_pr(req: ReviewPRRequest):
    try:
        llm = LLMProvider(provider=req.provider, api_key=req.api_key)
        res = agent_engine.review_pr(req.git_diff_or_code, llm)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/create-pr")
def create_pull_request(req: CreatePRRequest):
    try:
        res = repo_manager.create_github_pr(
            repo_owner_repo=req.repo_owner_repo,
            branch_name=req.branch_name,
            commit_message=req.commit_message,
            pr_title=req.pr_title,
            pr_body=req.pr_body,
            modified_files=req.modified_files,
            token=req.github_token
        )
        if res.get("status") == "error":
            raise HTTPException(status_code=400, detail=res.get("message"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

