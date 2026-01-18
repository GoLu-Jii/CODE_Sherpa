import json
import sys
from typing import Dict, List, Any

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
    
    # Extract function names from the functions dict
    def get_function_names(functions_dict: Dict) -> List[str]:
        """Extract function names from functions dict."""
        if isinstance(functions_dict, dict):
            return list(functions_dict.keys())
        elif isinstance(functions_dict, list):
            return functions_dict
        else:
            return []
    
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
            "is_entry": True
        }
        # Include explanation if present (from enrichment)
        explanation = file_data.get("explanation")
        if explanation:
            file_info["explanation"] = explanation
        learning_order.append(file_info)
    
    # Add other files
    for file_name, file_data in files.items():
        if file_name == entry_point:
            continue
        file_info = {
            "file": file_name,
            "functions": get_function_info(file_data.get("functions", {}), file_data),
            "is_entry": False
        }
        # Include explanation if present (from enrichment)
        explanation = file_data.get("explanation")
        if explanation:
            file_info["explanation"] = explanation
        learning_order.append(file_info)
    
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
