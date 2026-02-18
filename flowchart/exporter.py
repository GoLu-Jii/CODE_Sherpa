def export_mermaid(graph, out_file="flowchart.md"):
    lines = ["graph TD"]

    groups = {
        "source": "Source",
        "project": "Project",
        "tests": "Tests",
        "docs": "Docs"
    }

    nodes_by_group = {k: [] for k in groups.keys()}
    for node in graph.get("nodes", []):
        group = node.get("group", "project")
        nodes_by_group.setdefault(group, []).append(node)

    for group_key, group_title in groups.items():
        nodes = sorted(nodes_by_group.get(group_key, []), key=lambda n: n["label"])
        if not nodes:
            continue
        lines.append(f"subgraph {group_title}")
        for node in nodes:
            node_id = node["id"]
            label = node["label"].replace('"', "'")
            lines.append(f'  {node_id}["{label}"]')
        lines.append("end")

    for edge in graph.get("edges", []):
        src = edge["source"]
        dst = edge["target"]
        lines.append(f"{src} --> {dst}")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
