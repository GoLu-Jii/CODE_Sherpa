"""
CLI orchestrator for CODE_Sherpa pipeline.

Pipeline definition (execution order):
    1. analyze   → Static analysis (always runs)
    2. flowchart → Flowchart generation

Control flow:
    - Each step consumes a clearly chosen input file
    - Pipeline behavior is declared, not inferred
"""
import sys
import os
import json
import argparse

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analyzer.analyzer import build_unified_model
from flowchart.flow_builder import build_simple_file_graph
from flowchart.exporter import export_mermaid


# ============================================================
# Pipeline Step Implementations
# ============================================================

def run_analyze(repo_path: str, output_file: str) -> None:
    """Pipeline step 1: Static analysis."""
    print("Running static analysis...")
    analysis_result = build_unified_model(repo_path)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2)
    
    print("Analysis completed")


def run_flowchart(input_file: str, output_file: str) -> None:
    """Pipeline step 2: Flowchart generation."""
    print("Generating flowchart...")
    with open(input_file, "r", encoding="utf-8") as f:
        analyzer_data = json.load(f)
    graph = build_simple_file_graph(analyzer_data)
    export_mermaid(graph, output_file)
    print("Flowchart exported")


# ============================================================
# Pipeline Orchestration
# ============================================================

def run_pipeline(repo_path: str, output_dir: str) -> None:
    """
    Execute the CODE_Sherpa pipeline.
    
    Flow:
        1. Analyze -> analysis.json
        2. Flowchart -> flowchart.md (uses analysis.json)
    """
    # Define output files
    analysis_file = os.path.join(output_dir, "analysis.json")
    flowchart_file = os.path.join(output_dir, "flowchart.md")
    
    # Step 1: Analyze
    run_analyze(repo_path, analysis_file)
    
    # Step 2: Flowchart
    run_flowchart(analysis_file, flowchart_file)
    
    print("\nPipeline completed successfully")

# ============================================================
# CLI Entry Point
# ============================================================

def main():
    """CLI entry point. Validates input and delegates to pipeline."""
    parser = argparse.ArgumentParser(description="CODE_Sherpa CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument("repo_path", help="Repository path")
    analyze_parser.add_argument(
        "--output-dir",
        default="demo",
        help="Output directory for generated artifacts (default: demo)"
    )

    args = parser.parse_args()
    if args.command != "analyze":
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    repo_path = args.repo_path
    if not os.path.exists(repo_path):
        print(f"Error: Repository path not found: {repo_path}")
        sys.exit(1)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Execute pipeline
    try:
        run_pipeline(repo_path, output_dir)
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
