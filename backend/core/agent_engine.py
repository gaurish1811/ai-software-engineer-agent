import json
import re
from typing import Dict, List, Any, Optional
from backend.core.repo_manager import RepoManager
from backend.core.code_analyzer import CodeAnalyzer
from backend.core.llm_provider import LLMProvider

class AIAgentEngine:
    """Core reasoning engine orchestrating all developer agent capabilities."""

    def __init__(self, repo_manager: Optional[RepoManager] = None):
        self.repo_manager = repo_manager or RepoManager()
        self.code_analyzer = CodeAnalyzer()

    def explain_architecture(
        self,
        repo_path: str,
        llm: LLMProvider
    ) -> Dict[str, Any]:
        """Scans workspace files, parses AST graph, and generates full architecture explanation."""
        file_tree = self.repo_manager.get_repo_file_tree(repo_path, max_files=200)
        
        # Parse AST for code files
        files_ast = []
        code_snippets = []
        for file_info in file_tree[:40]: # Sample key files for context
            if file_info["is_code"]:
                try:
                    content = self.repo_manager.read_file_content(repo_path, file_info["path"])
                    ast_data = self.code_analyzer.parse_python_file(file_info["path"], content) if file_info["extension"] == ".py" else self.code_analyzer.parse_generic_file(file_info["path"], content, file_info["extension"])
                    files_ast.append(ast_data)
                    # Include top lines of code for summary
                    top_lines = "\n".join(content.splitlines()[:50])
                    code_snippets.append(f"--- File: {file_info['path']} ---\n{top_lines}\n")
                except Exception:
                    pass

        graph_summary = self.code_analyzer.build_dependency_graph(files_ast)

        prompt = f"""
Analyze the following codebase structure and AST dependency graph, then provide a clear, professional architectural breakdown.

File Tree:
{json.dumps([f['path'] for f in file_tree[:50]], indent=2)}

AST & Dependency Graph Overview:
- Total Nodes: {graph_summary['total_nodes']}
- Total Dependency Edges: {graph_summary['total_edges']}
- Hub Core Files: {graph_summary['top_hub_files']}

Representative Code Snippets:
{"".join(code_snippets[:10])}

Please format your response in Markdown covering:
1. **System Architecture Overview** (Core design pattern, e.g., MVC, Microservices, FastAPI REST + AST Pipeline)
2. **Key Components & Modules** (Role of primary hub files)
3. **Data & Dependency Flow** (How entry points communicate with sub-modules)
4. **Architectural Recommendations / Improvements**
"""
        explanation = llm.generate(prompt, system_prompt="You are a Principal Software Architect performing a code audit.")

        return {
            "status": "success",
            "repo_path": repo_path,
            "graph_summary": graph_summary,
            "architecture_markdown": explanation
        }

    def explain_code(
        self,
        repo_path: str,
        target_file: str,
        llm: LLMProvider
    ) -> Dict[str, Any]:
        """Explains a specific code file in detail."""
        content = self.repo_manager.read_file_content(repo_path, target_file)
        
        prompt = f"""
Explain the following code file in detail:

File: `{target_file}`
```
{content}
```

Format your explanation in Markdown:
1. **File Purpose Summary**
2. **Main Classes, Methods, & Functions Breakdown**
3. **Inputs, Outputs, & Side Effects**
4. **Potential Vulnerabilities or Refactoring Opportunities**
"""
        explanation = llm.generate(prompt, system_prompt="You are an expert Senior Code Reviewer.")
        return {
            "status": "success",
            "target_file": target_file,
            "explanation_markdown": explanation
        }

    def fix_bug(
        self,
        repo_path: str,
        issue_description: str,
        llm: LLMProvider,
        target_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Identifies bug, generates patch diff, applies changes to file, and returns diff preview."""
        file_tree = self.repo_manager.get_repo_file_tree(repo_path)
        
        # If target file specified, use it; otherwise search for relevant file
        relevant_files = []
        if target_file:
            relevant_files.append((target_file, self.repo_manager.read_file_content(repo_path, target_file)))
        else:
            for f in file_tree[:15]:
                if f["is_code"]:
                    try:
                        content = self.repo_manager.read_file_content(repo_path, f["path"])
                        relevant_files.append((f["path"], content))
                    except Exception:
                        pass

        context_str = ""
        for path, code in relevant_files:
            context_str += f"\n=== File: {path} ===\n{code}\n"

        prompt = f"""
You are an autonomous AI Software Engineer. Fix the reported bug described below:

Issue Description / Error Log:
{issue_description}

Code Context:
{context_str}

Respond strictly in JSON format with the following keys:
- "target_file": relative path of the file to fix (e.g., "backend/main.py")
- "explanation": brief explanation of the bug cause and fix strategy
- "original_code_snippet": exact block of code being replaced
- "fixed_code_snippet": exact replacement code block
- "full_updated_content": complete updated file code string
"""

        response_text = llm.generate(prompt, system_prompt="You are a senior bug-fixing software engineer. Output valid JSON only.")
        
        try:
            # Parse JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                fix_data = json.loads(json_match.group(0))
            else:
                fix_data = json.loads(response_text)

            affected_file = fix_data.get("target_file") or (target_file if target_file else relevant_files[0][0])
            updated_content = fix_data.get("full_updated_content", "")

            if updated_content and affected_file:
                # Apply fix directly to file in workspace
                self.repo_manager.write_file_content(repo_path, affected_file, updated_content)
                applied = True
            else:
                applied = False

            return {
                "status": "success",
                "target_file": affected_file,
                "explanation": fix_data.get("explanation", "Bug fix generated"),
                "applied_to_file": applied,
                "original_snippet": fix_data.get("original_code_snippet", ""),
                "fixed_snippet": fix_data.get("fixed_code_snippet", ""),
                "full_updated_content": updated_content
            }
        except Exception as err:
            return {
                "status": "error",
                "message": f"Failed to parse LLM bug fix output: {str(err)}",
                "raw_output": response_text
            }

    def generate_unit_tests(
        self,
        repo_path: str,
        target_file: str,
        llm: LLMProvider
    ) -> Dict[str, Any]:
        """Generates unit tests for the target code file."""
        content = self.repo_manager.read_file_content(repo_path, target_file)
        ext = Path(target_file).suffix.lower()
        test_framework = "pytest" if ext == ".py" else ("jest" if ext in (".js", ".ts") else "standard test suite")

        prompt = f"""
Generate comprehensive unit tests using `{test_framework}` for the following source file:

File: `{target_file}`
```
{content}
```

Requirements:
- Cover happy path, edge cases, missing arguments, and error handling.
- Include proper mock objects if external APIs or filesystem calls exist.
- Return ONLY the executable test file code inside a codeblock.
"""
        test_code_raw = llm.generate(prompt, system_prompt=f"You are a QA Lead writing high-coverage {test_framework} unit tests.")
        
        # Clean codeblock wrappers
        test_code = re.sub(r'^```[a-zA-Z]*\n', '', test_code_raw.strip())
        test_code = re.sub(r'\n```$', '', test_code)

        # Derive test file path
        p = Path(target_file)
        if ext == ".py":
            test_file_path = f"tests/test_{p.stem}.py"
        else:
            test_file_path = f"tests/{p.stem}.test{p.suffix}"

        # Save generated test file
        self.repo_manager.write_file_content(repo_path, test_file_path, test_code)

        return {
            "status": "success",
            "target_file": target_file,
            "test_file_path": test_file_path,
            "test_code": test_code
        }

    def review_pr(
        self,
        git_diff_or_code: str,
        llm: LLMProvider
    ) -> Dict[str, Any]:
        """Performs automated code review on a git diff or pull request."""
        prompt = f"""
Perform a comprehensive code review on the following Pull Request / Git Diff:

```diff
{git_diff_or_code}
```

Please structure your review in Markdown:
1. **PR Overview & Impact Rating** (1 to 10 score)
2. **Security & Vulnerability Analysis**
3. **Performance & Optimization Checks**
4. **Line-by-Line Code Quality & Bugs**
5. **Approved / Changes Requested Recommendation**
"""
        review = llm.generate(prompt, system_prompt="You are a Lead Staff Engineer reviewing Pull Requests.")
        return {
            "status": "success",
            "review_markdown": review
        }
