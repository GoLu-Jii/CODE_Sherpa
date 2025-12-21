import sys
import os
import json
import subprocess

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analyzer.analyzer import analyze_repo_files


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

    # Step E: Run analyzer
    print("▶ Running static analysis...")
    try:
        analysis_result = analyze_repo_files(repo_path)

        # Persist analyzer output for downstream steps
        with open("analysis.json", "w") as f:
            json.dump(analysis_result, f, indent=2)

        print("✔ Analysis completed")
    except Exception:
        print("✖ Analysis failed")
        return

    # Step F: Run tour generator
    print("\n▶ Generating guided tour...")
    try:
        subprocess.run(
            [sys.executable, "tour/tour_builder.py", "analysis.json"],
            check=True
        )
        print("✔ Tour generated")
    except subprocess.CalledProcessError:
        print("✖ Tour generation failed")
        return


if __name__ == "__main__":
    main()
