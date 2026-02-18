"""
dependency.py - Deterministic dependency graph construction.
Builds local file relationships from normalized import modules.
"""

from pathlib import Path
from typing import Dict, List, Set, DefaultDict
from collections import defaultdict


def file_to_module(file_path: str) -> str:
    module = file_path[:-3] if file_path.endswith(".py") else file_path
    module = module.replace("/", ".")
    if module.endswith(".__init__"):
        module = module[:-9]
    return module


def aliases_for_file(file_path: str) -> Set[str]:
    aliases = {file_to_module(file_path)}
    if file_path.startswith("src/"):
        aliases.add(file_to_module(file_path[4:]))
    return {alias for alias in aliases if alias}


def build_module_index(analysis_results: Dict[str, Dict]) -> Dict[str, List[str]]:
    module_index: DefaultDict[str, List[str]] = defaultdict(list)
    for file_path in sorted(analysis_results.keys()):
        for alias in aliases_for_file(file_path):
            module_index[alias].append(file_path)
    return dict(module_index)


def rank_candidate_file(file_path: str) -> int:
    score = 0
    if file_path.startswith("src/"):
        score += 30
    if file_path.startswith("tests/"):
        score -= 20
    if file_path.startswith("docs/"):
        score -= 25
    score -= len(file_path)
    return score


def import_to_file(import_name: str, module_index: Dict[str, List[str]]) -> str | None:
    if import_name in module_index:
        candidates = sorted(
            module_index[import_name],
            key=lambda path: rank_candidate_file(path),
            reverse=True
        )
        return candidates[0]

    # Fallback for package imports: "pkg.sub.module.symbol"
    parts = import_name.split(".")
    while len(parts) > 1:
        parts = parts[:-1]
        module_candidate = ".".join(parts)
        if module_candidate in module_index:
            candidates = sorted(
                module_index[module_candidate],
                key=lambda path: rank_candidate_file(path),
                reverse=True
            )
            return candidates[0]
    return None


def build_file_dependency_graph(analysis_results: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    Build a graph showing which files depend on which other files.
    
    Only includes local file dependencies (automatically excludes stdlib and third-party
    by checking if imports exist in the analyzed repository).
    
    Args:
        analysis_results: Output from analyze_repo_files()
    
    Returns:
        Dictionary mapping file -> list of files it depends on
    
    Example:
        >>> build_file_dependency_graph({
        ...     'app.py': {'imports': ['os', 'service']},
        ...     'service.py': {'imports': ['json', 'database']},
        ...     'database.py': {'imports': ['sqlite3']}
        ... })
        {
            'app.py': ['service.py'],
            'service.py': ['database.py'],
            'database.py': []
        }
    """
    module_index = build_module_index(analysis_results)
    
    # Build dependency graph
    dependency_graph = {}
    
    for file_path, file_data in analysis_results.items():
        dependencies = []
        
        # Get imports for this file
        imports = file_data.get('imports', [])
        
        for import_name in imports:
            target_file = import_to_file(import_name, module_index)
            
            if target_file and target_file != file_path:  # Don't self-reference
                dependencies.append(target_file)
        
        # Remove duplicates and sort for consistency
        dependency_graph[file_path] = sorted(list(set(dependencies)))
    
    return dependency_graph


def identify_entry_point(analysis_results: Dict[str, Dict]) -> str | None:
    """
    Identify the likely entry point of the codebase.
    
    Uses strict detection: only files with if __name__ == "__main__"
    
    Args:
        analysis_results: Output from analyze_repo_files()
    
    Returns:
        Relative path to the entry point file, or None if not found
    
    Example:
        >>> identify_entry_point({
        ...     'app.py': {'entry': True},
        ...     'service.py': {'entry': False}
        ... })
        'app.py'
    """
    entry_points = sorted([
        file_path
        for file_path, file_data in analysis_results.items()
        if file_data.get('entry', False)
    ])

    if not entry_points:
        return None

    def score_entry(path: str) -> int:
        name = Path(path).name
        score = 0
        if name == "__main__.py":
            score += 120
        if name in {"main.py", "app.py", "run.py", "start.py", "manage.py"}:
            score += 60
        if path.startswith("cli/") or path.startswith("bin/") or path.startswith("scripts/"):
            score += 40
        if path.startswith("tests/") or path.startswith("docs/"):
            score -= 40
        if path.startswith("src/"):
            score -= 20
        return score

    ranked = sorted(entry_points, key=score_entry, reverse=True)
    if score_entry(ranked[0]) <= 0:
        return None
    return ranked[0]
    return None


def get_dependency_summary(dependency_graph: Dict[str, List[str]]) -> Dict:
    """
    Generate summary statistics for the dependency graph.
    
    Args:
        dependency_graph: Output from build_file_dependency_graph()
    
    Returns:
        Dictionary with summary statistics
    """
    total_files = len(dependency_graph)
    total_dependencies = sum(len(deps) for deps in dependency_graph.values())
    
    # Find files with no dependencies (leaf nodes)
    leaf_files = [
        file_path
        for file_path, deps in dependency_graph.items()
        if len(deps) == 0
    ]
    
    # Find files with most dependencies
    if dependency_graph:
        max_deps_file = max(dependency_graph.items(), key=lambda x: len(x[1]))
        max_deps_count = len(max_deps_file[1])
        max_deps_name = max_deps_file[0]
    else:
        max_deps_count = 0
        max_deps_name = None
    
    return {
        'total_files': total_files,
        'total_dependencies': total_dependencies,
        'leaf_files_count': len(leaf_files),
        'leaf_files': leaf_files,
        'max_dependencies': max_deps_count,
        'most_dependent_file': max_deps_name
    }


# CLI interface for testing
if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python dependency.py <repository_path>")
        print("\nExample:")
        print("  python dependency.py ./sample_repo")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    try:
        # Import analyzer
        from analyzer import analyze_repo_files
        
        # Run analysis
        print(f"Analyzing repository: {repo_path}")
        analysis_results = analyze_repo_files(repo_path)
        
        # Build dependency graph
        print("\nBuilding dependency graph...")
        dep_graph = build_file_dependency_graph(analysis_results)
        
        # Identify entry point
        entry_point = identify_entry_point(analysis_results)
        
        # Print results
        print("\n" + "="*60)
        print("DEPENDENCY GRAPH")
        print("="*60)
        print(json.dumps(dep_graph, indent=2))
        
        print("\n" + "="*60)
        print("ENTRY POINT")
        print("="*60)
        if entry_point:
            print(f"✓ {entry_point}")
        else:
            print("✗ No entry point found")
        
        # Print summary
        summary = get_dependency_summary(dep_graph)
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total files: {summary['total_files']}")
        print(f"Total dependencies: {summary['total_dependencies']}")
        print(f"Leaf files (no dependencies): {summary['leaf_files_count']}")
        if summary['most_dependent_file']:
            print(f"Most dependent file: {summary['most_dependent_file']} ({summary['max_dependencies']} deps)")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
