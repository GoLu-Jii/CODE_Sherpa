import json
import os
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartChunker:
    def __init__(self, analysis_file_path: str, repo_base_path: str):
        self.analysis_file_path = analysis_file_path
        self.repo_base_path = repo_base_path
        
        try:
            with open(self.analysis_file_path, "r", encoding="utf-8") as f:
                self.ast_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Analysis file not found at {self.analysis_file_path}")
            self.ast_data = {"files": {}}

    def extract_chunks(self) -> List[Dict[str, Any]]:
        """
        Slices files into intact function chunks based on AST coordinates
        and injects deterministic dependency metadata.
        For files without functions/classes (like main.py), saves the complete file content.
        """
        chunks = []
        files_data = self.ast_data.get("files", {})

        for file_path, file_info in files_data.items():
            full_path = os.path.join(self.repo_base_path, file_path)
            
            if not os.path.exists(full_path):
                logger.warning(f"Source file missing: {full_path}. Skipping.")
                continue
                
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            module_path = file_path.replace("\\", "/").replace(".py", "").replace("/", ".")

            # --- Add File-Level Chunk ---
            classes_list = list(file_info.get("classes", {}).keys())
            functions_list = list(file_info.get("functions", {}).keys())
            imports_list = file_info.get("imports", [])
            full_content = "".join(lines)
            
            # For files without functions/classes, include complete file content
            # Otherwise just show summary with preview
            if not functions_list and not classes_list:
                file_summary = (
                    f"File Path: {file_path}\n"
                    f"Architecture Node: {module_path}\n"
                    f"Module Type: Top-Level Python Module (no classes or functions)\n"
                    f"Imports: {imports_list}\n"
                    f"\n--- Complete File Content ---\n"
                    f"{full_content}"
                )
            else:
                file_summary = (
                    f"File Path: {file_path}\n"
                    f"Architecture Node: {module_path}\n"
                    f"Module Type: Python File\n"
                    f"Contains Classes: {classes_list}\n"
                    f"Contains Functions: {functions_list}\n"
                    f"Imports: {imports_list}\n"
                    f"\n--- Top Level Code / Docstring ---\n"
                    f"{''.join(lines[:max(15, min(len(lines), 30))])}"
                )

            file_node_id = f"{module_path}__file__"
            chunks.append({
                "id": file_node_id,
                "text": file_summary,
                "metadata": {
                    "file_path": file_path,
                    "node_id": module_path,
                    "function_name": "", 
                    "qualified_name": module_path,
                    "type": "file",
                    "start_line": 1,
                    "end_line": len(lines),
                    "resolved_calls": "[]"
                }
            })

            # Process Functions
            for func_name, func_details in file_info.get("functions", {}).items():
                start_line = func_details.get("lineno", 1) - 1  # 0-indexed
                end_line = func_details.get("end_lineno", start_line + 1)
                
                # Slice the exact code block mathematically
                code_snippet = "".join(lines[start_line:end_line])
                
                node_id = f"{module_path}.{func_name}"

                # Contextualize textual embedding!!!
                enriched_text = (
                    f"File: {file_path}\n"
                    f"Function Name: {func_name}\n"
                    f"Module: {module_path}\n"
                    f"---\n"
                    f"{code_snippet}"
                )

                # Inject Graph-RAG Metadata (Must be strings/ints for ChromaDB)
                resolved_calls = func_details.get("resolved_calls", [])
                metadata = {
                    "file_path": file_path,
                    "node_id": node_id,
                    "function_name": func_name,  # Plain function name for exact matching
                    "qualified_name": node_id,  # Full qualified name (same as node_id)
                    "type": "function",
                    "start_line": start_line + 1,
                    "end_line": end_line,
                    "resolved_calls": json.dumps(resolved_calls) # Stringify list for DB
                }

                chunks.append({
                    "id": node_id,
                    "text": enriched_text,
                    "metadata": metadata
                })

        logger.info(f"Successfully extracted {len(chunks)} structural chunks.")
        return chunks