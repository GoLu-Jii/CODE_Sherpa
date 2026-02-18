"""
CLI orchestrator for CODE_Sherpa pipeline.

Pipeline definition (execution order):
    1. analyze   → Static analysis (always runs)
    2. enrich    → Semantic enrichment (optional, controlled by decision logic)
    3. tour      → Guided tour generation
    4. flowchart → Flowchart generation

Control flow:
    - CLI explicitly decides: when enrichment runs, which file downstream consumes
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
from tour.tour_builder import build_learning_order
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


def run_tour(input_file: str, output_file: str) -> None:
    """Pipeline step 2: Guided tour generation."""
    print("Generating tour...")
    with open(input_file, "r", encoding="utf-8") as f:
        analyzer_data = json.load(f)
    result = build_learning_order(analyzer_data)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print("Tour generated")


def run_flowchart(input_file: str, output_file: str) -> None:
    """Pipeline step 3: Flowchart generation."""
    print("Generating flowchart...")
    with open(input_file, "r", encoding="utf-8") as f:
        analyzer_data = json.load(f)
    graph = build_simple_file_graph(analyzer_data)
    export_mermaid(graph, output_file)
    print("Flowchart exported")


def run_enrich(input_file: str, output_file: str) -> None:
    """Pipeline step 4: Semantic enrichment (Optional/Last)."""
    print("Enrichment layer is currently frozen. Skipping.")
    return

    # Original logic (Frozen)
    # api_key = os.getenv("GROQ_API_KEY")
    # if not api_key:
    #     print("Skipping enrichment: GROQ_API_KEY not set")
    #     return

    # print("Running semantic enrichment...")
    # try:
    #     run_enrichment_generation(input_file, output_file, use_llm=True)
    #     print("Enrichment completed (annotations.json created)")
    # except Exception as e:
    #     print(f"Enrichment failed (non-critical): {e}")


# ============================================================
# Pipeline Orchestration
# ============================================================

def run_pipeline(repo_path: str, output_dir: str) -> None:
    """
    Execute the CODE_Sherpa pipeline.
    
    New Flow (Decoupled):
        1. Analyze -> analysis.json
        2. Tour -> learning_order.json (uses analysis.json)
        3. Flowchart -> flowchart.md (uses analysis.json)
        4. Enrich -> annotations.json (uses analysis.json, Optional)
    """
    # Define output files
    analysis_file = os.path.join(output_dir, "analysis.json")
    learning_order_file = os.path.join(output_dir, "learning_order.json")
    flowchart_file = os.path.join(output_dir, "flowchart.md")
    annotations_file = os.path.join(output_dir, "annotations.json")
    
    # Step 1: Analyze
    run_analyze(repo_path, analysis_file)
    
    # Step 2: Tour (Independent of enrichment)
    run_tour(analysis_file, learning_order_file)
    
    # Step 3: Flowchart (Independent of enrichment)
    run_flowchart(analysis_file, flowchart_file)
    
    # Step 4: Enrich (Last & Optional sidecar)
    run_enrich(analysis_file, annotations_file)
    
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
