"""
analyzer.py - AST-based Code Analysis for CODE_Sherpa

Final Day-3 version.

Capabilities:
- File-level analysis (imports, functions)
- Intra-function call extraction
- Entry-point detection (__name__ == "__main__" at top level)
- Unified model generation with file dependencies

Main public API:
- analyze_file()
- analyze_repo_files()
- build_unified_model()  ← FINAL OUTPUT
"""

import ast
from pathlib import Path
from typing import Dict, Set, Optional, List
import json


# ============================================================
# AST Visitor
# ============================================================

class CodeVisitor(ast.NodeVisitor):
    """AST visitor that extracts imports, functions, calls, and entry points."""

    def __init__(self):
        self.imports: Set[str] = set()
        self.functions: Set[str] = set()
        self.calls: Dict[str, Set[str]] = {}

        self.current_function: Optional[str] = None
        self.has_main_guard: bool = False

        # Track nesting to ensure __main__ guard is top-level only
        self.nesting_level: int = 0

    # ---------------- Imports ----------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)

    # ---------------- Functions ----------------

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.add(node.name)
        self.calls[node.name] = set()

        self.nesting_level += 1
        prev_function = self.current_function
        self.current_function = node.name

        self.generic_visit(node)

        self.current_function = prev_function
        self.nesting_level -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.functions.add(node.name)
        self.calls[node.name] = set()

        self.nesting_level += 1
        prev_function = self.current_function
        self.current_function = node.name

        self.generic_visit(node)

        self.current_function = prev_function
        self.nesting_level -= 1

    # ---------------- Calls ----------------

    def visit_Call(self, node: ast.Call) -> None:
        if self.current_function is not None:
            func_name = None

            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name:
                self.calls[self.current_function].add(func_name)

        self.generic_visit(node)

    # ---------------- Entry Point ----------------

    def visit_If(self, node: ast.If) -> None:
        # Only consider top-level if-statements
        if self.nesting_level == 0 and self._is_main_guard(node.test):
            self.has_main_guard = True

        self.generic_visit(node)

    def _is_main_guard(self, test: ast.expr) -> bool:
        if not isinstance(test, ast.Compare):
            return False
        if len(test.ops) != 1 or len(test.comparators) != 1:
            return False
        if not isinstance(test.ops[0], ast.Eq):
            return False

        left = test.left
        right = test.comparators[0]

        return (
            self._is_name_dunder(left) and self._is_main_string(right)
        ) or (
            self._is_main_string(left) and self._is_name_dunder(right)
        )

    @staticmethod
    def _is_name_dunder(node: ast.expr) -> bool:
        return isinstance(node, ast.Name) and node.id == "__name__"

    @staticmethod
    def _is_main_string(node: ast.expr) -> bool:
        return isinstance(node, ast.Constant) and node.value == "__main__"


# ============================================================
# Parsing Helpers
# ============================================================

def parse_python_file(file_path: Path) -> Optional[ast.AST]:
    try:
        source = file_path.read_text(encoding="utf-8")
        return ast.parse(source, filename=str(file_path))
    except Exception:
        return None


# ============================================================
# File Analysis
# ============================================================

def analyze_file(file_path: Path) -> Dict:
    tree = parse_python_file(file_path)

    if tree is None:
        return {
            "entry": False,
            "imports": [],
            "functions": {}
        }

    visitor = CodeVisitor()
    visitor.visit(tree)

    return {
        "entry": visitor.has_main_guard,
        "imports": sorted(visitor.imports),
        "functions": {
            name: {
                "calls": sorted(visitor.calls.get(name, []))
            }
            for name in sorted(visitor.functions)
        }
    }


def analyze_repo_files(repo_path: str) -> Dict[str, Dict]:
    from analyzer.parser import get_python_files

    results = {}
    files = get_python_files(repo_path)

    for file_rel_path in files:
        full_path = Path(repo_path) / file_rel_path
        results[file_rel_path] = analyze_file(full_path)

    return results


# ============================================================
# Unified Model (FINAL OUTPUT)
# ============================================================

def build_unified_model(repo_path: str) -> Dict:
    """
    Final Day-3 output.
    Combines:
    - entry point detection
    - function call analysis
    - file-level dependencies
    """

    analysis_results = analyze_repo_files(repo_path)

    from analyzer.dependency import (
        build_file_dependency_graph,
        identify_entry_point
    )

    dependency_graph = build_file_dependency_graph(analysis_results)
    entry_point = identify_entry_point(analysis_results)

    unified = {
        "entry_point": entry_point,
        "files": {}
    }

    for file_path, file_data in analysis_results.items():
        unified["files"][file_path] = {
            "entry": file_data["entry"],
            "imports": file_data["imports"],
            "functions": file_data["functions"],
            "depends_on": dependency_graph.get(file_path, [])
        }

    return unified


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <repo_path> [--unified]")
        sys.exit(1)

    repo_path = sys.argv[1]
    use_unified = "--unified" in sys.argv

    if use_unified:
        result = build_unified_model(repo_path)
        print(json.dumps(result, indent=2))
    else:
        result = analyze_repo_files(repo_path)
        print(json.dumps(result, indent=2))
