import sys
import os
import json
import subprocess

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analyzer.analyzer import build_unified_model
from enrich.enrich import enrich_file


def main():
    # Step A: Check if user gave enough information
    if len(sys.argv) < 3:
        print("Usage: python cli/main.py analyze <repo_path>")
        return

    # Step B: Read what the user typed
    command = sys.argv[1]
    repo_path = sys.argv[2]

    # Step C: Check if command is correct
    if command != "analyze":
        print(f"Unknown command: {command}")
        return

    # Step D: Check if folder really exists
    if not os.path.exists(repo_path):
        print("Error: Repository path not found")
        return

    # Step E: Create demo folder for output files
    demo_dir = "demo"
    os.makedirs(demo_dir, exist_ok=True)

    # Step F: Run analyzer
    print("Running static analysis...")
    try:
        analysis_result = build_unified_model(repo_path)

        # Persist analyzer output for downstream steps
        analysis_file = os.path.join(demo_dir, "analysis.json")
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=2)

        print("Analysis completed")
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step G: Run semantic enrichment (optional)
    enriched_file = os.path.join(demo_dir, "enriched_analysis.json")
    print("\nRunning semantic enrichment...")
    try:
        # Check if GROQ_API_KEY is set to decide if we use LLM
        use_llm = bool(os.getenv("GROQ_API_KEY"))
        enrich_file(analysis_file, enriched_file, use_llm=use_llm)
        print("Enrichment completed")
        # Use enriched file for downstream steps if it exists
        input_for_downstream = enriched_file if os.path.exists(enriched_file) else analysis_file
    except Exception as e:
        print(f"Enrichment failed (using fallback): {e}")
        # Continue with unenriched analysis if enrichment fails
        input_for_downstream = analysis_file

    # Step H: Run tour generator
    print("\nGenerating guided tour...")
    try:
        result = subprocess.run(
            [sys.executable, "tour/tour_builder.py", input_for_downstream],
            check=True,
            capture_output=True,
            text=True
        )
        # Save tour output to file
        learning_order_file = os.path.join(demo_dir, "learning_order.json")
        with open(learning_order_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        print("Tour generated")
    except subprocess.CalledProcessError as e:
        print(f"Tour generation failed: {e}")
        print(f"Error output: {e.stderr}")
        return

    # Step I: Run flowchart generator
    print("\nGenerating flowchart...")
    try:
        flowchart_file = os.path.join(demo_dir, "flowchart.md")
        subprocess.run(
            [sys.executable, "flowchart/flow_builder.py", input_for_downstream, "--output", flowchart_file],
            check=True
        )
        if os.path.exists(flowchart_file):
            print("Flowchart exported")
        else:
            print("Flowchart export failed - file not created")
    except subprocess.CalledProcessError as e:
        print(f"Flowchart generation failed: {e}")
        return

    # Final success message
    print("\nPipeline completed successfully")


if __name__ == "__main__":
    main()
