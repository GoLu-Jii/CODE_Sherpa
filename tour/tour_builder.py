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
    
    # Add entry point first if it exists
    if entry_point and entry_point in files:
        file_data = files[entry_point]
        learning_order.append({
            "file": entry_point,
            "functions": get_function_names(file_data.get("functions", {})),
            "is_entry": True
        })
    
    # Add other files
    for file_name, file_data in files.items():
        if file_name == entry_point:
            continue
        learning_order.append({
            "file": file_name,
            "functions": get_function_names(file_data.get("functions", {})),
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
