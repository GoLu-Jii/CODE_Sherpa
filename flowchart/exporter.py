def export_mermaid(graph, out_file="flowchart.md"):
    lines = ["graph TD"]

    for src, dst in graph["edges"]:
        lines.append(f"{src} --> {dst}")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
