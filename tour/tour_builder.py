import json
import sys
from typing import Dict, List, Any


def file_group(file_name: str) -> str:
    if file_name.startswith("src/"):
        return "source"
    if file_name.startswith("tests/"):
        return "tests"
    if file_name.startswith("docs/"):
        return "docs"
    return "project"


def learning_rank(file_name: str, incoming: Dict[str, int], outgoing: Dict[str, int]) -> tuple:
    group_priority = {
        "source": 0,
        "project": 1,
        "tests": 2,
        "docs": 3
    }
    group = file_group(file_name)
    # Central files first inside each group.
    return (
        group_priority.get(group, 4),
        -(incoming.get(file_name, 0) + outgoing.get(file_name, 0)),
        file_name
    )


def build_learning_order(analyzer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build learning order from unified model format.
    
    Args:
        analyzer_data: Unified model with structure:
            {
                "entry_point": "file.py",
                "files": {
                    "file.py": {
                        "entry": bool,
                        "imports": [...],
                        "functions": {
                            "func_name": {"calls": [...]}
                        },
                        "depends_on": [...]
                    }
                }
            }
    
    Returns:
        Learning order with files and their functions
    """
    files = analyzer_data.get("files", {})
    entry_point = analyzer_data.get("entry_point")
    learning_order = []

    incoming = {file_name: 0 for file_name in files.keys()}
    outgoing = {file_name: len(file_data.get("depends_on", [])) for file_name, file_data in files.items()}
    for file_name, file_data in files.items():
        for dep in file_data.get("depends_on", []):
            if dep in incoming:
                incoming[dep] += 1
    
    # Extract function info with explanations if present
    def get_function_info(functions_dict: Dict, file_data: Dict) -> List[Dict]:
        """Extract function info with explanations if present."""
        function_list = []
        if isinstance(functions_dict, dict):
            for func_name, func_data in functions_dict.items():
                func_info = {"name": func_name}
                # Include explanation if present (from enrichment)
                explanation = func_data.get("explanation") if isinstance(func_data, dict) else None
                if explanation:
                    func_info["explanation"] = explanation
                function_list.append(func_info)
        elif isinstance(functions_dict, list):
            # Legacy format: just function names
            for func_name in functions_dict:
                # Try to find explanation from file_data
                file_functions = file_data.get("functions", {})
                if isinstance(file_functions, dict) and func_name in file_functions:
                    func_data = file_functions[func_name]
                    if isinstance(func_data, dict):
                        explanation = func_data.get("explanation")
                        if explanation:
                            function_list.append({"name": func_name, "explanation": explanation})
                            continue
                function_list.append({"name": func_name})
        return function_list
    
    # Add entry point first if it exists
    if entry_point and entry_point in files:
        file_data = files[entry_point]
        file_info = {
            "file": entry_point,
            "functions": get_function_info(file_data.get("functions", {}), file_data),
            "is_entry": True,
            "group": file_group(entry_point)
        }
        # Include explanation if present (from enrichment)
        explanation = file_data.get("explanation")
        if explanation:
            file_info["explanation"] = explanation
        learning_order.append(file_info)
    
    ordered_files = sorted(
        [name for name in files.keys() if name != entry_point],
        key=lambda name: learning_rank(name, incoming, outgoing)
    )

    for file_name in ordered_files:
        file_data = files[file_name]
        if file_name == entry_point:
            continue
        file_info = {
            "file": file_name,
            "functions": get_function_info(file_data.get("functions", {}), file_data),
            "is_entry": False,
            "group": file_group(file_name)
        }
        # Include explanation if present (from enrichment)
        explanation = file_data.get("explanation")
        if explanation:
            file_info["explanation"] = explanation
        learning_order.append(file_info)
    
    return {
        "learning_order": learning_order,
        "metadata": {
            "entry_point": entry_point,
            "file_count": len(files),
            "source_count": sum(1 for f in files if file_group(f) == "source"),
            "test_count": sum(1 for f in files if file_group(f) == "tests"),
            "docs_count": sum(1 for f in files if file_group(f) == "docs")
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
