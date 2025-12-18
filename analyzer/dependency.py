"""
dependency.py - Dependency Graph Construction
Builds relationships between files based on imports.
"""

from typing import Dict, List, Set


def get_available_modules(analysis_results: Dict[str, Dict]) -> Set[str]:
    """
    Extract all available module names from analyzed files.
    
    A file 'service.py' provides module 'service'.
    A file 'utils/helper.py' provides module 'helper' and 'utils.helper'.
    
    Args:
        analysis_results: Output from analyze_repo_files()
    
    Returns:
        Set of available module names
    
    Examples:
        >>> get_available_modules({'service.py': {...}, 'utils/helper.py': {...}})
        {'service', 'helper', 'utils', 'utils.helper'}
    """
    available = set()
    
    for file_path in analysis_results.keys():
        # Remove .py extension
        if file_path.endswith('.py'):
            module_path = file_path[:-3]
        else:
            module_path = file_path
        
        # Convert path separators to dots
        module_path = module_path.replace('/', '.')
        
        # Add the full module path
        available.add(module_path)
        
        # Add just the filename (last component)
        module_name = module_path.split('.')[-1]
        available.add(module_name)
        
        # Add parent package names (e.g., 'utils' from 'utils.helper')
        parts = module_path.split('.')
        for i in range(1, len(parts)):
            available.add('.'.join(parts[:i]))
    
    return available


def is_local_module(import_name: str, available_modules: Set[str]) -> bool:
    """
    Check if an import refers to a local module in the repository.
    
    This is deterministic and repo-aware: if the import name (or its top-level
    package) exists in our analyzed files, it's local. Otherwise it's external
    (stdlib or third-party).
    
    Args:
        import_name: The imported module name
        available_modules: Set of available module names in the repo
    
    Returns:
        True if module is local to this repo, False if external
    
    Examples:
        >>> is_local_module('service', {'service', 'utils'})
        True
        >>> is_local_module('os', {'service', 'utils'})
        False
        >>> is_local_module('numpy', {'service', 'utils'})
        False
    """
    # Check if the import or its top-level package is in our repo
    top_level = import_name.split('.')[0]
    return top_level in available_modules


def import_to_file(import_name: str, available_modules: Set[str], 
                   all_files: Set[str]) -> str | None:
    """
    Convert an import name to a file path.
    
    Simple mapping rules:
    - 'service' -> 'service.py' (if exists)
    - 'utils.helper' -> 'utils/helper.py' (if exists)
    - 'helper' -> could match 'helper.py' or 'utils/helper.py'
    
    Args:
        import_name: The imported module name
        available_modules: Set of available module names in the repo
        all_files: Set of all file paths in the repo
    
    Returns:
        File path if found, None otherwise
    
    Examples:
        >>> import_to_file('service', {'service'}, {'service.py'})
        'service.py'
        >>> import_to_file('os', {'service'}, {'service.py'})
        None
    """
    # First check if this import is available in our repo
    if not is_local_module(import_name, available_modules):
        return None
    
    # Try direct mapping: 'service' -> 'service.py'
    direct_file = f"{import_name}.py"
    if direct_file in all_files:
        return direct_file
    
    # Try package mapping: 'utils.helper' -> 'utils/helper.py'
    package_file = f"{import_name.replace('.', '/')}.py"
    if package_file in all_files:
        return package_file
    
    # Try to find matching file (handle 'helper' -> 'utils/helper.py')
    simple_name = import_name.split('.')[-1]
    for file_path in all_files:
        # Get module name from file path
        if file_path.endswith('.py'):
            file_module = file_path[:-3].replace('/', '.')
            # Check if it ends with our import name
            if file_module.endswith(import_name) or file_module.endswith(simple_name):
                return file_path
    
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
    # Get available local modules
    available_modules = get_available_modules(analysis_results)
    all_files = set(analysis_results.keys())
    
    # Build dependency graph
    dependency_graph = {}
    
    for file_path, file_data in analysis_results.items():
        dependencies = []
        
        # Get imports for this file
        imports = file_data.get('imports', [])
        
        for import_name in imports:
            # Only process local modules (automatically filters out stdlib/third-party)
            if not is_local_module(import_name, available_modules):
                continue
            
            # Try to resolve to a file
            target_file = import_to_file(import_name, available_modules, all_files)
            
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
    entry_points = [
        file_path
        for file_path, file_data in analysis_results.items()
        if file_data.get('entry', False)
    ]
    
    # If exactly one entry point, return it
    if len(entry_points) == 1:
        return entry_points[0]
    
    # If multiple entry points, prioritize common names
    priority_names = ['main.py', 'app.py', '__main__.py', 'run.py', 'start.py']
    for priority_name in priority_names:
        if priority_name in entry_points:
            return priority_name
    
    # If still multiple, return the first one alphabetically
    if entry_points:
        return sorted(entry_points)[0]
    
    # No entry point found
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