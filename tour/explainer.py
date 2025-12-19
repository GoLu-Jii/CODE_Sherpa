import json
import sys
FILE_ENTRY_TEMPLATE = (
    "This file acts as the entry point of the system. "
    "Execution of the application begins here."
)
FILE_CALLED_TEMPLATE = (
    "This file participates in the system's execution flow "
    "and is invoked by other components."
)
FILE_SUPPORT_TEMPLATE = (
    "This file provides supporting or utility functionality "
    "used across the project."
)
FUNCTION_ENTRY_TEMPLATE = (
    "This function initiates execution and drives the main flow of the system."
)
FUNCTION_GENERIC_TEMPLATE = (
    "This function contributes to the system's behavior as part of its execution."
)
def explain_file(file_name, analyzer_files, entry_point):
    if file_name == entry_point:
        return FILE_ENTRY_TEMPLATE
    calls = analyzer_files.get(file_name, {}).get("calls", [])
    if calls:
        return FILE_CALLED_TEMPLATE
    return FILE_SUPPORT_TEMPLATE
def explain_functions(functions, is_entry_file):
    explained = []
    for func in functions:
        if is_entry_file:
            explanation = FUNCTION_ENTRY_TEMPLATE
        else:
            explanation = FUNCTION_GENERIC_TEMPLATE
        explained.append({
            "name": func,
            "explanation": explanation
        })
    return explained
def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python explainer.py analyzer_output.json learning_order.json",
            file=sys.stderr
        )
        sys.exit(1)
    analyzer_output_path = sys.argv[1]
    learning_order_path = sys.argv[2]
    with open(analyzer_output_path, "r") as f:
        analyzer_data = json.load(f)
    with open(learning_order_path, "r") as f:
        learning_order_data = json.load(f)
    analyzer_files = analyzer_data.get("files", {})
    entry_point = learning_order_data["metadata"].get("entry_point")
    learning_steps = []
    for item in learning_order_data["learning_order"]:
        file_name = item["file"]
        functions = item.get("functions", [])
        is_entry = item.get("is_entry", False)
        step = {
            "file": file_name,
            "summary": explain_file(file_name, analyzer_files, entry_point),
            "functions": explain_functions(functions, is_entry)
        }
        learning_steps.append(step)
    output = {
        "learning_steps": learning_steps
    }
    print(json.dumps(output, indent=2))
if __name__ == "__main__":
    main()
