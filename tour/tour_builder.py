import json
import sys
def build_learning_order(analyzer_data):
    files = analyzer_data.get("files", {})
    entry_point = analyzer_data.get("entry_point")
    learning_order = []
    if entry_point and entry_point in files:
        learning_order.append({
            "file": entry_point,
            "functions": files[entry_point].get("functions", []),
            "is_entry": True
        })
    for file_name, metadata in files.items():
        if file_name == entry_point:
            continue
        learning_order.append({
            "file": file_name,
            "functions": metadata.get("functions", []),
            "is_entry": False
        })
    return {
        "learning_order": learning_order,
        "metadata": {
            "entry_point": entry_point
        }
    }
def main():
    if len(sys.argv) != 2:
        print("Usage: python tour_builder.py analyzer_output.json", file=sys.stderr)
        sys.exit(1)
    analyzer_output_path = sys.argv[1]
    with open(analyzer_output_path, "r") as f:
        analyzer_data = json.load(f)
    result = build_learning_order(analyzer_data)
    print(json.dumps(result, indent=2))
if __name__ == "__main__":
    main()
