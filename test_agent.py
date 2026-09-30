import os
from pathlib import Path
from backend.core.repo_manager import RepoManager
from backend.core.code_analyzer import CodeAnalyzer

def test_engine():
    repo_mgr = RepoManager()
    analyzer = CodeAnalyzer()

    sample_dir = str(Path("workspaces/sample_calculator").resolve())
    print(f"Testing with sample directory: {sample_dir}")

    # 1. Test Ingestion
    res = repo_mgr.clone_or_load_repo(sample_dir)
    print("Ingestion result:", res)
    assert res["status"] == "success"

    # 2. Test File Tree
    tree = repo_mgr.get_repo_file_tree(sample_dir)
    print(f"Found {len(tree)} files in workspace tree:")
    for f in tree:
        print(" -", f["path"])

    # 3. Test AST Parsing
    calc_code = repo_mgr.read_file_content(sample_dir, "calculator.py")
    ast_calc = analyzer.parse_python_file("calculator.py", calc_code)
    print("calculator.py AST parsed functions:", [fn["name"] for fn in ast_calc["functions"]])
    print("calculator.py AST parsed classes:", [cl["name"] for cl in ast_calc["classes"]])

    utils_code = repo_mgr.read_file_content(sample_dir, "utils.py")
    ast_utils = analyzer.parse_python_file("utils.py", utils_code)

    # 4. Test Graph Building
    graph_data = analyzer.build_dependency_graph([ast_calc, ast_utils])
    print(f"Graph nodes count: {graph_data['total_nodes']}, edges count: {graph_data['total_edges']}")

    print("\nSUCCESS! All core unit checks passed cleanly.")

if __name__ == "__main__":
    test_engine()
