"""
flow_builder.py - Builds flowchart graph from analysis results
Converts dependency graph to Mermaid flowchart format.
"""

import json
import sys
import os
from typing import Dict, List, Any

# Add project root to Python path so imports work
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flowchart.exporter import export_mermaid


def build_graph_from_analysis(analysis_data: Dict[str, Any]) -> Dict[str, List]:
    """
    Build graph structure with edges from unified model.
    
    Args:
        analysis_data: Unified model with structure:
            {
                "entry_point": "file.py",
                "files": {
                    "file.py": {
                        "depends_on": ["other.py"],
                        "functions": {...}
                    }
                }
            }
    
    Returns:
        Dictionary with "edges" list: [("source", "target"), ...]
    """
    edges = []
    files = analysis_data.get("files", {})
    
    # Build edges from file dependencies
    for file_path, file_data in files.items():
        depends_on = file_data.get("depends_on", [])
        for dep_file in depends_on:
            # Create edge: dependency -> file (reverse direction for flow)
            # Actually, for flowchart we want: file -> dependency (shows what file uses)
            edges.append((file_path, dep_file))
        
        # Also add function-level edges within files
        functions = file_data.get("functions", {})
        for func_name, func_data in functions.items():
            calls = func_data.get("calls", [])
            for called_func in calls:
                # Check if called function is in another file
                for other_file, other_data in files.items():
                    if other_file != file_path:
                        other_functions = other_data.get("functions", {})
                        if called_func in other_functions:
                            # Function call across files
                            edges.append((f"{file_path}::{func_name}", f"{other_file}::{called_func}"))
                            break
    
    return {"edges": edges}


def build_simple_file_graph(analysis_data: Dict[str, Any]) -> Dict[str, List]:
    """
    Build simpler graph showing only file-level dependencies.
    
    Args:
        analysis_data: Unified model format
    
    Returns:
        Dictionary with "edges" list for file dependencies only
    """
    edges = []
    files = analysis_data.get("files", {})
    
    # Build edges from file dependencies
    for file_path, file_data in files.items():
        depends_on = file_data.get("depends_on", [])
        for dep_file in depends_on:
            # Normalize node names for Mermaid (replace special chars)
            src = file_path.replace("/", "_").replace(".", "_").replace("-", "_")
            dst = dep_file.replace("/", "_").replace(".", "_").replace("-", "_")
            edges.append((src, dst))
    
    return {"edges": edges}


def main():
    if len(sys.argv) < 2:
        print("Usage: python flow_builder.py <analysis.json> [--output <output_file>]", file=sys.stderr)
        sys.exit(1)
    
    analysis_file = sys.argv[1]
    output_file = "flowchart.md"
    
    # Parse optional output file
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    if not os.path.exists(analysis_file):
        print(f"Error: Analysis file not found: {analysis_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load analysis data
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        # Build graph (using simple file-level graph)
        graph = build_simple_file_graph(analysis_data)
        
        # Export to Mermaid format
        export_mermaid(graph, output_file)
        
        print(f"Flowchart exported to {output_file}")
        
    except Exception as e:
        print(f"Error building flowchart: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
