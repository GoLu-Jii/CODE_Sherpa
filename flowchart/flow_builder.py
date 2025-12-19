import json

def load_analysis(path):
    with open(path, "r", encoding="utf-16") as f:
        return json.load(f)

def build_graph(data):
    graph = {
        "nodes": set(),
        "edges": []
    }

    for file, meta in data.items():
        file_node = file.replace("/", "_")
        graph["nodes"].add(file_node)

        # File → imported files
        for imp in meta.get("imports", []):
            imp_node = imp.replace(".", "_")
            graph["edges"].append((file_node, imp_node))

        # Function-level calls
        for fn, fn_meta in meta.get("functions", {}).items():
            fn_node = f"{file_node}::{fn}"
            graph["nodes"].add(fn_node)

            for call in fn_meta.get("calls", []):
                call_node = call.replace(".", "_")
                graph["edges"].append((fn_node, call_node))

    return graph

if __name__ == "__main__":
    data = load_analysis("analysis.json")
    graph = build_graph(data)
    print("Nodes:", len(graph["nodes"]))
    print("Edges:", len(graph["edges"]))

from exporter import export_mermaid

export_mermaid(graph)
print("Flowchart exported to flowchart.md")
