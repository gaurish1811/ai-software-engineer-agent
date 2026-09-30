import os
import shutil
import zipfile
import tempfile
import httpx
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from backend.config import settings

class RepoManager:
    """Manages cloning, zip extracting, file reading, and GitHub PR creation."""
    
    def __init__(self, workspace_root: str = settings.WORKSPACE_DIR):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, repo_url_or_path: str) -> str:
        """Derive a safe folder name from URL or path."""
        clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', repo_url_or_path.strip('/'))
        return clean[-40:] if len(clean) > 40 else clean

    def clone_or_load_repo(self, repo_input: str) -> Dict[str, Any]:
        """
        Accepts a GitHub URL (https://github.com/owner/repo) or a local absolute path.
        Clones remote repos into workspace directory or loads local directory.
        """
        repo_input = repo_input.strip()
        
        # Check if local path
        if os.path.exists(repo_input) and os.path.isdir(repo_input):
            repo_path = Path(repo_input)
            repo_name = repo_path.name
            return {
                "status": "success",
                "repo_name": repo_name,
                "repo_path": str(repo_path.resolve()),
                "is_remote": False
            }

        # Otherwise treat as remote GitHub URL or "owner/repo"
        if not repo_input.startswith("http"):
            if "/" in repo_input and not repo_input.startswith("/"):
                repo_url = f"https://github.com/{repo_input}.git"
            else:
                repo_url = repo_input
        else:
            repo_url = repo_input

        # Normalize URL
        if repo_url.endswith(".git"):
            clean_url = repo_url[:-4]
        else:
            clean_url = repo_url

        parts = clean_url.rstrip("/").split("/")
        repo_name = parts[-1] if len(parts) > 0 else "downloaded_repo"
        target_dir = self.workspace_root / f"{repo_name}_{self._sanitize_name(repo_url)}"

        # If already exists, return existing
        if target_dir.exists():
            return {
                "status": "success",
                "repo_name": repo_name,
                "repo_path": str(target_dir.resolve()),
                "is_remote": True,
                "note": "Loaded existing clone"
            }

        # Try GitPython first
        try:
            import git
            git.Repo.clone_from(repo_url, target_dir)
            return {
                "status": "success",
                "repo_name": repo_name,
                "repo_path": str(target_dir.resolve()),
                "is_remote": True
            }
        except Exception as git_err:
            # Fallback to direct GitHub ZIP download if git binary/GitPython fails
            try:
                zip_url = f"{clean_url}/archive/refs/heads/main.zip"
                response = httpx.get(zip_url, follow_redirects=True, timeout=30.0)
                if response.status_code != 200:
                    zip_url = f"{clean_url}/archive/refs/heads/master.zip"
                    response = httpx.get(zip_url, follow_redirects=True, timeout=30.0)

                if response.status_code == 200:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
                        tmp_zip.write(response.content)
                        tmp_zip_path = tmp_zip.name

                    with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                        zip_ref.extractall(self.workspace_root)
                    
                    os.remove(tmp_zip_path)
                    
                    # Find extracted directory
                    extracted_dirs = [d for d in self.workspace_root.iterdir() if d.is_dir() and d.name.startswith(repo_name)]
                    if extracted_dirs:
                        final_dir = extracted_dirs[0]
                        return {
                            "status": "success",
                            "repo_name": repo_name,
                            "repo_path": str(final_dir.resolve()),
                            "is_remote": True,
                            "note": "Downloaded via ZIP fallback"
                        }

                raise ValueError(f"HTTP download failed with status {response.status_code}")
            except Exception as zip_err:
                return {
                    "status": "error",
                    "message": f"Failed to clone or download repo: {str(git_err)} | Zip error: {str(zip_err)}"
                }

    def get_repo_file_tree(self, repo_path: str, max_files: int = 500) -> List[Dict[str, Any]]:
        """Returns flat file tree listing relative paths, sizes, and file extensions."""
        base = Path(repo_path)
        if not base.exists():
            return []

        ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.idea', '.vscode'}
        file_tree = []

        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(base)
                
                # Filter out binary or large non-code files
                suffix = full_path.suffix.lower()
                is_code = suffix in {'.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.java', '.c', '.cpp', '.h', '.html', '.css', '.json', '.md', '.yml', '.yaml', '.sh', '.sql', '.toml'}
                
                try:
                    size = full_path.stat().st_size
                except Exception:
                    size = 0

                file_tree.append({
                    "path": str(rel_path).replace("\\", "/"),
                    "full_path": str(full_path),
                    "extension": suffix,
                    "is_code": is_code,
                    "size": size
                })
                
                if len(file_tree) >= max_files:
                    break
            if len(file_tree) >= max_files:
                break

        return file_tree

    def read_file_content(self, repo_path: str, rel_path: str) -> str:
        """Reads file content safely."""
        full_path = Path(repo_path) / rel_path
        if not full_path.exists() or not full_path.is_file():
            raise FileNotFoundError(f"File not found: {rel_path}")

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"// Error reading file content: {str(e)}"

    def write_file_content(self, repo_path: str, rel_path: str, content: str) -> bool:
        """Writes/modifies file content within repo."""
        full_path = Path(repo_path) / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    def create_github_pr(
        self,
        repo_owner_repo: str,
        branch_name: str,
        commit_message: str,
        pr_title: str,
        pr_body: str,
        modified_files: Dict[str, str], # {rel_path: content}
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates branch, commits files, and creates Pull Request using GitHub API."""
        gh_token = token or settings.GITHUB_TOKEN
        if not gh_token:
            return {
                "status": "error",
                "message": "GitHub Personal Access Token is required to create Pull Requests. Please provide it in settings."
            }

        headers = {
            "Authorization": f"token {gh_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                # 1. Get default branch SHA
                repo_url = f"https://api.github.com/repos/{repo_owner_repo}"
                repo_resp = client.get(repo_url, headers=headers)
                if repo_resp.status_code != 200:
                    return {"status": "error", "message": f"GitHub API error fetching repo info: {repo_resp.text}"}
                
                default_branch = repo_resp.json().get("default_branch", "main")
                
                # Get SHA of default branch
                ref_resp = client.get(f"{repo_url}/git/ref/heads/{default_branch}", headers=headers)
                if ref_resp.status_code != 200:
                    return {"status": "error", "message": f"Could not get ref for {default_branch}: {ref_resp.text}"}
                
                base_sha = ref_resp.json()["object"]["sha"]

                # 2. Create new branch
                new_ref = f"refs/heads/{branch_name}"
                create_ref_resp = client.post(
                    f"{repo_url}/git/refs",
                    headers=headers,
                    json={"ref": new_ref, "sha": base_sha}
                )
                if create_ref_resp.status_code not in (201, 422): # 422 if branch exists
                    return {"status": "error", "message": f"Failed to create branch {branch_name}: {create_ref_resp.text}"}

                # 3. Update files in branch
                for file_path, content in modified_files.items():
                    # Get existing file sha if exists
                    file_url = f"{repo_url}/contents/{file_path}"
                    file_info = client.get(f"{file_url}?ref={branch_name}", headers=headers)
                    file_sha = file_info.json().get("sha") if file_info.status_code == 200 else None

                    import base64
                    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                    
                    payload = {
                        "message": commit_message,
                        "content": encoded_content,
                        "branch": branch_name
                    }
                    if file_sha:
                        payload["sha"] = file_sha

                    put_resp = client.put(file_url, headers=headers, json=payload)
                    if put_resp.status_code not in (200, 201):
                        return {"status": "error", "message": f"Failed to commit file {file_path}: {put_resp.text}"}

                # 4. Open Pull Request
                pr_payload = {
                    "title": pr_title,
                    "head": branch_name,
                    "base": default_branch,
                    "body": pr_body
                }
                pr_resp = client.post(f"{repo_url}/pulls", headers=headers, json=pr_payload)
                if pr_resp.status_code in (200, 201):
                    pr_data = pr_resp.json()
                    return {
                        "status": "success",
                        "pr_url": pr_data.get("html_url"),
                        "pr_number": pr_data.get("number"),
                        "title": pr_data.get("title")
                    }
                else:
                    return {"status": "error", "message": f"Failed to open PR: {pr_resp.text}"}

        except Exception as e:
            return {"status": "error", "message": f"GitHub PR Creation failed: {str(e)}"}
