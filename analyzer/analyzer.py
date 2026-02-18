"""
analyzer.py - AST-based Code Analysis for CODE_Sherpa

Now includes:
- File-level imports/dependencies
- Intra-file raw call extraction
- Inter-file call target resolution (best-effort, deterministic)
- Global resolved call edges in unified model metadata
"""

import ast
import json
from pathlib import Path
from typing import Dict, Set, Optional, List, Tuple, Any


def rel_file_to_module(rel_path: str) -> str:
    module = rel_path[:-3] if rel_path.endswith(".py") else rel_path
    module = module.replace("/", ".")
    if module.endswith(".__init__"):
        return module[:-9]
    return module


def build_module_alias_map(file_paths: List[str]) -> Dict[str, str]:
    alias_map: Dict[str, str] = {}
    for file_path in file_paths:
        canonical = rel_file_to_module(file_path)
        alias_map[canonical] = canonical
        if file_path.startswith("src/"):
            alt = rel_file_to_module(file_path[4:])
            alias_map[alt] = canonical
    return alias_map


def canonicalize_module(module_name: str, alias_map: Dict[str, str]) -> str:
    return alias_map.get(module_name, module_name)


def parse_python_file(file_path: Path) -> Tuple[Optional[ast.AST], Optional[str]]:
    try:
        source = file_path.read_text(encoding="utf-8")
        return ast.parse(source, filename=str(file_path)), None
    except Exception as exc:
        return None, str(exc)


def resolve_relative_import(
    current_module: str,
    is_package_module: bool,
    level: int,
    module: Optional[str],
    imported_names: List[str]
) -> List[str]:
    if level <= 0:
        if module:
            return [module]
        return imported_names

    current_parts = [p for p in current_module.split(".") if p]
    if not current_parts:
        return []

    package_parts = current_parts if is_package_module else current_parts[:-1]
    ascend = max(level - 1, 0)
    if ascend > len(package_parts):
        return []
    anchor = package_parts[:len(package_parts) - ascend]

    resolved: List[str] = []
    if module:
        resolved.append(".".join(anchor + module.split(".")))
    else:
        for name in imported_names:
            resolved.append(".".join(anchor + name.split(".")))
    return [item for item in resolved if item]


def get_attr_chain(node: ast.AST) -> Optional[List[str]]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        parent = get_attr_chain(node.value)
        if parent is None:
            return None
        return parent + [node.attr]
    return None


class FunctionBodyResolver(ast.NodeVisitor):
    def __init__(
        self,
        current_module: str,
        current_class: Optional[str],
        top_level_functions: Set[str],
        local_classes: Set[str],
        import_modules: Dict[str, str],
        import_symbols: Dict[str, str]
    ) -> None:
        self.current_module = current_module
        self.current_class = current_class
        self.top_level_functions = top_level_functions
        self.local_classes = local_classes
        self.import_modules = import_modules
        self.import_symbols = import_symbols
        self.local_var_types: Dict[str, str] = {}
        self.raw_calls: Set[str] = set()
        self.resolved_calls: Set[str] = set()

    def qualify_local(self, name: str) -> str:
        if self.current_class:
            return f"{self.current_module}.{self.current_class}.{name}"
        return f"{self.current_module}.{name}"

    def resolve_name(self, name: str) -> Optional[str]:
        if name in self.import_symbols:
            return self.import_symbols[name]
        if name in self.import_modules:
            return self.import_modules[name]
        if self.current_class and name in {"self", "cls"}:
            return f"{self.current_module}.{self.current_class}"
        if name in self.local_classes:
            return f"{self.current_module}.{name}"
        if name in self.top_level_functions:
            return f"{self.current_module}.{name}"
        return None

    def resolve_attribute_chain(self, chain: List[str]) -> Optional[str]:
        if not chain:
            return None
        base = chain[0]
        tail = chain[1:]
        if not tail:
            return self.resolve_name(base)

        if base in self.local_var_types:
            var_type = self.local_var_types[base]
            # Heuristic: adapter objects returned from get_adapter map to known Adapter classes.
            if var_type.endswith(".get_adapter"):
                adapter_symbols = sorted(
                    value for value in self.import_symbols.values()
                    if value.split(".")[-1].endswith("Adapter")
                )
                if adapter_symbols:
                    return f"{adapter_symbols[0]}.{'.'.join(tail)}"
            return f"{var_type}.{'.'.join(tail)}"
        if base in self.import_modules:
            return f"{self.import_modules[base]}.{'.'.join(tail)}"
        if base in self.import_symbols:
            return f"{self.import_symbols[base]}.{'.'.join(tail)}"
        if self.current_class and base in {"self", "cls"}:
            return f"{self.current_module}.{self.current_class}.{'.'.join(tail)}"
        return None

    def maybe_capture_instance_type(self, target: ast.AST, value: ast.AST) -> None:
        if not isinstance(target, ast.Name):
            return
        if not isinstance(value, ast.Call):
            return
        class_target = self.resolve_call_target(value.func)
        if class_target:
            self.local_var_types[target.id] = class_target

    def resolve_call_target(self, call_func: ast.AST) -> Optional[str]:
        chain = get_attr_chain(call_func)
        if chain is None:
            return None
        if len(chain) == 1:
            return self.resolve_name(chain[0])
        return self.resolve_attribute_chain(chain)

    def visit_Assign(self, node: ast.Assign) -> Any:
        for target in node.targets:
            self.maybe_capture_instance_type(target, node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        if node.value is not None:
            self.maybe_capture_instance_type(node.target, node.value)
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> Any:
        for item in node.items:
            if item.optional_vars is not None:
                self.maybe_capture_instance_type(item.optional_vars, item.context_expr)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> Any:
        for item in node.items:
            if item.optional_vars is not None:
                self.maybe_capture_instance_type(item.optional_vars, item.context_expr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        chain = get_attr_chain(node.func)
        if chain:
            self.raw_calls.add(chain[-1])
        resolved = self.resolve_call_target(node.func)
        if resolved:
            self.resolved_calls.add(resolved)
        self.generic_visit(node)


def analyze_file(file_path: Path, rel_path: str, module_alias_map: Dict[str, str]) -> Dict:
    tree, parse_error = parse_python_file(file_path)
    if tree is None:
        return {
            "entry": False,
            "imports": [],
            "functions": {},
            "parse_error": parse_error
        }

    current_module = canonicalize_module(rel_file_to_module(rel_path), module_alias_map)
    is_package_module = rel_path.endswith("__init__.py")

    has_main_guard = False
    imports: Set[str] = set()
    import_modules: Dict[str, str] = {}
    import_symbols: Dict[str, str] = {}

    top_level_functions: Set[str] = set()
    class_methods: Dict[str, Set[str]] = {}
    local_classes: Set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
                local_name = alias.asname or alias.name.split(".")[0]
                import_modules[local_name] = canonicalize_module(alias.name, module_alias_map)
        elif isinstance(node, ast.ImportFrom):
            imported_names = [a.name for a in node.names]
            resolved_modules = resolve_relative_import(
                current_module=current_module,
                is_package_module=is_package_module,
                level=node.level,
                module=node.module,
                imported_names=imported_names
            )
            if node.module:
                base_module = canonicalize_module(resolved_modules[0], module_alias_map) if resolved_modules else ""
                if base_module:
                    imports.add(base_module)
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    import_symbols[local] = f"{base_module}.{alias.name}" if base_module else alias.name
            else:
                for alias, resolved_module in zip(node.names, resolved_modules):
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    canonical_module = canonicalize_module(resolved_module, module_alias_map)
                    imports.add(canonical_module)
                    import_symbols[local] = canonical_module
        elif isinstance(node, ast.FunctionDef):
            top_level_functions.add(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            top_level_functions.add(node.name)
        elif isinstance(node, ast.ClassDef):
            local_classes.add(node.name)
            methods: Set[str] = set()
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(child.name)
            class_methods[node.name] = methods
        elif isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Compare):
                if (
                    len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)
                    and len(test.comparators) == 1
                ):
                    left = test.left
                    right = test.comparators[0]
                    if (
                        (isinstance(left, ast.Name) and left.id == "__name__" and isinstance(right, ast.Constant) and right.value == "__main__")
                        or (isinstance(right, ast.Name) and right.id == "__name__" and isinstance(left, ast.Constant) and left.value == "__main__")
                    ):
                        has_main_guard = True

    functions_out: Dict[str, Dict[str, List[str]]] = {}

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            resolver = FunctionBodyResolver(
                current_module=current_module,
                current_class=None,
                top_level_functions=top_level_functions,
                local_classes=local_classes,
                import_modules=import_modules,
                import_symbols=import_symbols
            )
            for body_node in node.body:
                resolver.visit(body_node)
            functions_out[node.name] = {
                "calls": sorted(resolver.raw_calls),
                "resolved_calls": sorted(resolver.resolved_calls)
            }
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    resolver = FunctionBodyResolver(
                        current_module=current_module,
                        current_class=node.name,
                        top_level_functions=top_level_functions,
                        local_classes=local_classes,
                        import_modules=import_modules,
                        import_symbols=import_symbols
                    )
                    for body_node in child.body:
                        resolver.visit(body_node)
                    key = f"{node.name}.{child.name}"
                    functions_out[key] = {
                        "calls": sorted(resolver.raw_calls),
                        "resolved_calls": sorted(resolver.resolved_calls)
                    }

    return {
        "entry": has_main_guard,
        "imports": sorted(imports),
        "functions": functions_out,
        "parse_error": None
    }


def analyze_repo_files(repo_path: str) -> Dict[str, Dict]:
    from analyzer.parser import get_python_files

    results: Dict[str, Dict] = {}
    files = get_python_files(repo_path)
    module_alias_map = build_module_alias_map(files)

    for file_rel_path in files:
        full_path = Path(repo_path) / file_rel_path
        results[file_rel_path] = analyze_file(full_path, file_rel_path, module_alias_map)
    return results


def build_unified_model(repo_path: str) -> Dict:
    analysis_results = analyze_repo_files(repo_path)

    from analyzer.dependency import build_file_dependency_graph, identify_entry_point

    dependency_graph = build_file_dependency_graph(analysis_results)
    entry_point = identify_entry_point(analysis_results)

    unified = {
        "entry_point": entry_point,
        "metadata": {
            "parse_errors": [],
            "resolved_call_edges": []
        },
        "files": {}
    }

    for file_path, file_data in analysis_results.items():
        file_module = rel_file_to_module(file_path)
        unified["files"][file_path] = {
            "entry": file_data["entry"],
            "imports": file_data["imports"],
            "functions": file_data["functions"],
            "depends_on": dependency_graph.get(file_path, [])
        }

        for function_name, function_data in file_data["functions"].items():
            src = f"{file_module}.{function_name}"
            for target in function_data.get("resolved_calls", []):
                unified["metadata"]["resolved_call_edges"].append({
                    "from": src,
                    "to": target
                })

        if file_data.get("parse_error"):
            unified["metadata"]["parse_errors"].append({
                "file": file_path,
                "error": file_data["parse_error"]
            })

    unified["metadata"]["resolved_call_edges"] = sorted(
        unified["metadata"]["resolved_call_edges"],
        key=lambda e: (e["from"], e["to"])
    )
    return unified


def build_resolved_call_adjacency(unified_model: Dict) -> Dict[str, List[str]]:
    adjacency: Dict[str, Set[str]] = {}
    edges = unified_model.get("metadata", {}).get("resolved_call_edges", [])
    for edge in edges:
        src = edge.get("from")
        dst = edge.get("to")
        if not src or not dst:
            continue
        adjacency.setdefault(src, set()).add(dst)
    return {src: sorted(list(dsts)) for src, dsts in adjacency.items()}


def trace_call_chain(
    unified_model: Dict,
    start_function: str,
    target_function: str,
    max_depth: int = 8
) -> Optional[List[str]]:
    adjacency = build_resolved_call_adjacency(unified_model)
    if start_function == target_function:
        return [start_function]

    queue: List[Tuple[str, List[str], int]] = [(start_function, [start_function], 0)]
    seen: Set[str] = {start_function}

    while queue:
        node, path, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        for nxt in adjacency.get(node, []):
            if nxt == target_function:
                return path + [nxt]
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, path + [nxt], depth + 1))
    return None


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
