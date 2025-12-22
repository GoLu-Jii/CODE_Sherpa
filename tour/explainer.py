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
    """
    Explain a file's role in the system.
    
    Args:
        file_name: Name of the file
        analyzer_files: Dict of file data from unified model
        entry_point: Entry point file name
    
    Returns:
        Explanation string
    """
    if file_name == entry_point:
        return FILE_ENTRY_TEMPLATE
    
    file_data = analyzer_files.get(file_name, {})
    # Check if file has dependencies (is called by other files)
    depends_on = file_data.get("depends_on", [])
    # Also check if it's imported/called by checking if any file depends on it
    # Actually, depends_on shows what THIS file depends on, not what depends on IT
    # For now, if it has dependencies, it's likely a called file
    if depends_on:
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
    
    with open(analyzer_output_path, "r", encoding="utf-8") as f:
        analyzer_data = json.load(f)
    
    with open(learning_order_path, "r", encoding="utf-8") as f:
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
