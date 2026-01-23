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
import subprocess
from typing import Tuple

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analyzer.analyzer import build_unified_model
from enrich.enrich import run_enrichment_generation


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
    result = subprocess.run(
        [sys.executable, "tour/tour_builder.py", input_file],
        check=True,
        capture_output=True,
        text=True
    )
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.stdout)
    
    print("Tour generated")


def run_flowchart(input_file: str, output_file: str) -> None:
    """Pipeline step 3: Flowchart generation."""
    print("Generating flowchart...")
    subprocess.run(
        [sys.executable, "flowchart/flow_builder.py", input_file, "--output", output_file],
        check=True
    )
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
    if len(sys.argv) < 3:
        print("Usage: python cli/main.py analyze <repo_path>")
        sys.exit(1)
    
    command = sys.argv[1]
    repo_path = sys.argv[2]
    
    if command != "analyze":
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    if not os.path.exists(repo_path):
        print(f"Error: Repository path not found: {repo_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir = "demo"
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
