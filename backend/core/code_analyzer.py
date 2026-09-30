import ast
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import networkx as nx
from backend.config import settings

class CodeAnalyzer:
    """Parses codebase ASTs, extracts functions, classes, imports, and builds dependency graph."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def parse_python_file(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """Parses Python file using standard `ast` module to extract symbols."""
        imports = []
        functions = []
        classes = []

        try:
            tree = ast.parse(code_content, filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    args = [a.arg for a in node.args.args]
                    docstring = ast.get_docstring(node) or ""
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": args,
                        "docstring": docstring,
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = []
                    bases = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            bases.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            bases.append(base.attr)
                    
                    for sub_node in node.body:
                        if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append(sub_node.name)

                    docstring = ast.get_docstring(node) or ""
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "bases": bases,
                        "docstring": docstring
                    })

        except Exception as err:
            # Fallback regex if syntax error or invalid snippet
            functions, classes, imports = self._regex_fallback_parser(code_content)

        return {
            "file": file_path,
            "language": "python",
            "imports": list(set(imports)),
            "functions": functions,
            "classes": classes
        }

    def parse_generic_file(self, file_path: str, code_content: str, extension: str) -> Dict[str, Any]:
        """Regex and symbol parser for JS/TS/Go/Java/C++ files."""
        functions, classes, imports = self._regex_fallback_parser(code_content)
        lang_map = {
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".go": "go",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c"
        }
        return {
            "file": file_path,
            "language": lang_map.get(extension, "code"),
            "imports": list(set(imports)),
            "functions": functions,
            "classes": classes
        }

    def _regex_fallback_parser(self, code_content: str):
        imports = []
        functions = []
        classes = []

        # Imports regex (JS/TS import, Python import, Go import)
        import_matches = re.findall(r'import\s+(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]|import\s+[\'"]([^\'"]+)[\'"]|import\s+([\w\.]+)', code_content)
        for match in import_matches:
            imp = next((m for m in match if m), None)
            if imp:
                imports.append(imp)

        # Functions regex (function name, const name = () =>, def name, func name)
        func_matches = re.finditer(r'(?:function\s+([a-zA-Z0-9_]+)|const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(|def\s+([a-zA-Z0-9_]+)|func\s+([a-zA-Z0-9_]+))', code_content)
        for idx, match in enumerate(func_matches):
            fname = next((m for m in match.groups() if m), None)
            if fname and fname not in ("if", "for", "while", "switch"):
                functions.append({"name": fname, "line": idx + 1, "args": [], "docstring": ""})

        # Classes regex (class Name, struct Name, type Name struct)
        class_matches = re.finditer(r'(?:class\s+([a-zA-Z0-9_]+)|type\s+([a-zA-Z0-9_]+)\s+struct)', code_content)
        for idx, match in enumerate(class_matches):
            cname = next((m for m in match.groups() if m), None)
            if cname:
                classes.append({"name": cname, "line": idx + 1, "methods": [], "bases": [], "docstring": ""})

        return functions, classes, imports

    def build_dependency_graph(self, files_ast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Constructs NetworkX Directed Graph representing files, modules, classes, and import relationships."""
        self.graph = nx.DiGraph()
        
        file_symbol_map = {}

        # 1. Add File and Symbol Nodes
        for f in files_ast:
            file_node = f["file"]
            self.graph.add_node(file_node, type="file", language=f["language"], functions_count=len(f["functions"]), classes_count=len(f["classes"]))
            
            # Map file to exported symbols
            symbols = [fn["name"] for fn in f["functions"]] + [cl["name"] for cl in f["classes"]]
            file_symbol_map[file_node] = symbols

            # Add function nodes
            for fn in f["functions"]:
                fn_id = f"{file_node}::{fn['name']}"
                self.graph.add_node(fn_id, type="function", name=fn["name"], line=fn["line"])
                self.graph.add_edge(file_node, fn_id, relationship="contains")

            # Add class nodes
            for cl in f["classes"]:
                cl_id = f"{file_node}::{cl['name']}"
                self.graph.add_node(cl_id, type="class", name=cl["name"], line=cl["line"])
                self.graph.add_edge(file_node, cl_id, relationship="contains")

        # 2. Add Import Dependency Edges between files
        all_files = list(file_symbol_map.keys())
        for f in files_ast:
            src_file = f["file"]
            for imp in f["imports"]:
                # Match import to file path
                clean_imp = imp.replace(".", "/").strip("/")
                for target_file in all_files:
                    if target_file != src_file and (clean_imp in target_file or target_file.startswith(clean_imp)):
                        self.graph.add_edge(src_file, target_file, relationship="imports", import_name=imp)

        # 3. Compute network statistics (degree centrality, hub files)
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())
        
        top_dependencies = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]

        # Convert to serializable format for Vis.js UI graph rendering
        nodes = []
        for n, data in self.graph.nodes(data=True):
            node_type = data.get("type", "file")
            label = n.split("/")[-1] if node_type == "file" else n.split("::")[-1]
            nodes.append({
                "id": n,
                "label": label,
                "full_id": n,
                "group": node_type,
                "title": f"{node_type.upper()}: {n}"
            })

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "label": data.get("relationship", "depends_on"),
                "arrows": "to"
            })

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "top_hub_files": [item[0] for item in top_dependencies if self.graph.nodes[item[0]].get("type") == "file"],
            "nodes": nodes,
            "edges": edges
        }

    def sync_to_neo4j(self, graph_data: Dict[str, Any]) -> bool:
        """Optional exporter to Neo4j if configured."""
        if not settings.ENABLE_NEO4J:
            return False
        
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
            with driver.session() as session:
                # Create nodes
                for node in graph_data["nodes"]:
                    session.run("MERGE (n:CodeNode {id: $id}) SET n.label = $label, n.group = $group", id=node["id"], label=node["label"], group=node["group"])
                # Create edges
                for edge in graph_data["edges"]:
                    session.run(
                        """
                        MATCH (a:CodeNode {id: $from}), (b:CodeNode {id: $to})
                        MERGE (a)-[r:DEPENDS_ON {type: $label}]->(b)
                        """,
                        from_node=edge["from"], to_node=edge["to"], label=edge["label"]
                    )
            driver.close()
            return True
        except Exception:
            return False
