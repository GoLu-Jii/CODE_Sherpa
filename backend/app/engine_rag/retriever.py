import json
import logging
import re
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_FUNCTIONS = 10  # Max function chunks to fetch for a file query


class GraphRetriever:
    def __init__(self, chroma_db):
        self.collection = chroma_db.collection

    def _detect_file_query(self, query: str) -> str:
        match = re.search(r"([\w/\\\.\-]+\.py)", query.lower())
        return match.group(1).strip() if match else ""

    def _detect_symbol_query(self, query: str) -> str:
        patterns = [
            r"`([\w\.]+)`",
            r"([\w\.]+)\(\)",
            r"(?:function|method|class|module|variable|symbol)\s+['\"]?([\w\.]+)['\"]?",
            r"['\"]?([\w\.]+)['\"]?\s+(?:function|method|class|module)"
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _find_exact_file(self, file_path: str) -> List[str]:
        """Returns file-level chunk IDs matching the given path or basename."""
        matching_ids = []
        basename = file_path.replace("\\", "/").split("/")[-1]

        # Try exact full path match
        try:
            results = self.collection.get(
                where={"$and": [{"file_path": file_path}, {"type": "file"}]},
                include=["metadatas"]
            )
            if results and results.get("ids"):
                logger.info(f"Exact file match for '{file_path}': {results['ids']}")
                return list(set(results["ids"]))
        except Exception as e:
            logger.debug(f"Exact path query failed: {e}")

        # Try basename match
        if basename != file_path:
            try:
                results = self.collection.get(
                    where={"$and": [{"file_path": basename}, {"type": "file"}]},
                    include=["metadatas"]
                )
                if results and results.get("ids"):
                    logger.info(f"Basename match for '{basename}': {results['ids']}")
                    return list(set(results["ids"]))
            except Exception as e:
                logger.debug(f"Basename query failed: {e}")

        # Manual scan as last resort
        try:
            all_files = self.collection.get(
                where={"type": "file"},
                include=["metadatas"]
            )
            for i, file_id in enumerate(all_files.get("ids", [])):
                stored_path = all_files["metadatas"][i].get("file_path", "")
                if basename.lower() in stored_path.lower():
                    if stored_path.endswith(basename) or f"/{basename}" in stored_path:
                        matching_ids.append(file_id)
                        logger.info(f"Manual search match for '{basename}': {file_id}")
        except Exception as e:
            logger.debug(f"Manual file search failed: {e}")

        return list(set(matching_ids))

    def _find_functions_for_file(self, file_path: str) -> List[Dict]:
        """
        Fetches function-level chunks belonging to a file.
        Returns a list of {node_id, code, calls} dicts capped at MAX_FILE_FUNCTIONS.
        """
        try:
            results = self.collection.get(
                where={"$and": [{"file_path": file_path}, {"type": "function"}]},
                include=["documents", "metadatas"],
                limit=MAX_FILE_FUNCTIONS
            )
            nodes = []
            for i in range(len(results.get("ids", []))):
                nodes.append({
                    "node_id": results["ids"][i],
                    "code": results["documents"][i],
                    "calls": json.loads(results["metadatas"][i].get("resolved_calls", "[]"))
                })
            logger.info(f"Fetched {len(nodes)} function chunks for file '{file_path}'")
            return nodes
        except Exception as e:
            logger.warning(f"Failed to fetch functions for file '{file_path}': {e}")
            return []

    def _find_exact_symbol(self, symbol: str) -> List[str]:
        """Returns chunk IDs matching the symbol by qualified_name or function_name."""
        matching_ids = []
        try:
            # Try qualified_name first
            results = self.collection.get(
                where={"qualified_name": symbol},
                include=["metadatas"]
            )
            if results and results["ids"]:
                matching_ids.extend(results["ids"])
                logger.info(f"Qualified name match for '{symbol}': {results['ids']}")

            # Fall back to function_name
            if not matching_ids:
                results = self.collection.get(
                    where={"function_name": symbol},
                    include=["metadatas"]
                )
                if results and results["ids"]:
                    matching_ids.extend(results["ids"])
                    logger.info(f"Function name match for '{symbol}': {results['ids']}")

            # Partial dotted match
            if not matching_ids and "." in symbol:
                function_name = symbol.split(".")[-1]
                results = self.collection.get(
                    where={"function_name": function_name},
                    include=["metadatas"]
                )
                if results and results["ids"]:
                    for node_id in results["ids"]:
                        if node_id.endswith(symbol):
                            matching_ids.append(node_id)
                    if matching_ids:
                        logger.info(f"Partial match for '{symbol}': {matching_ids}")

        except Exception as e:
            logger.warning(f"Symbol lookup failed for '{symbol}': {e}")

        return list(set(matching_ids))

    def retrieve_with_graph_context(self, query: str, n_results: int) -> Dict[str, Any]:
        """
        Hybrid search pipeline:
        1. File query  -> file chunk + all its function chunks
        2. Symbol query -> exact function/class chunk + downstream deps
        3. Semantic fallback -> top-n chunks + downstream deps
        """
        logger.info(f"Hybrid Graph-RAG query: '{query}'")

        primary_nodes = []
        downstream_ids_to_fetch = set()

        # --- Step 1: File-level query ---
        file_query = self._detect_file_query(query)
        if file_query:
            logger.info(f"Detected file query: '{file_query}'")
            file_chunk_ids = self._find_exact_file(file_query)

            if file_chunk_ids:
                # Fetch the file-level summary chunk
                file_results = self.collection.get(ids=file_chunk_ids)
                stored_file_path = ""

                for i in range(len(file_results["ids"])):
                    metadata = file_results["metadatas"][i]
                    resolved_calls = json.loads(metadata.get("resolved_calls", "[]"))
                    stored_file_path = metadata.get("file_path", "")

                    primary_nodes.append({
                        "node_id": file_results["ids"][i],
                        "code": file_results["documents"][i],
                        "calls": resolved_calls
                    })
                    for call_id in resolved_calls:
                        downstream_ids_to_fetch.add(call_id)

                # Also fetch the actual function chunks inside this file
                if stored_file_path:
                    func_nodes = self._find_functions_for_file(stored_file_path)
                    for node in func_nodes:
                        primary_nodes.append(node)
                        for call_id in node["calls"]:
                            downstream_ids_to_fetch.add(call_id)

        # --- Step 2: Symbol-level query ---
        if not primary_nodes:
            symbol = self._detect_symbol_query(query)
            if symbol:
                logger.info(f"Detected symbol query: '{symbol}'")
                exact_ids = self._find_exact_symbol(symbol)

                if exact_ids:
                    exact_results = self.collection.get(ids=exact_ids)
                    for i in range(len(exact_results["ids"])):
                        resolved_calls = json.loads(
                            exact_results["metadatas"][i].get("resolved_calls", "[]")
                        )
                        primary_nodes.append({
                            "node_id": exact_results["ids"][i],
                            "code": exact_results["documents"][i],
                            "calls": resolved_calls
                        })
                        for call_id in resolved_calls:
                            downstream_ids_to_fetch.add(call_id)

        # --- Step 3: Semantic fallback ---
        if not primary_nodes:
            logger.info("No exact matches, falling back to semantic search")
            search_results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            if not search_results or not search_results["ids"][0]:
                return {"primary_nodes": [], "downstream_context": []}

            for i in range(len(search_results["ids"][0])):
                resolved_calls = json.loads(
                    search_results["metadatas"][0][i].get("resolved_calls", "[]")
                )
                primary_nodes.append({
                    "node_id": search_results["ids"][0][i],
                    "code": search_results["documents"][0][i],
                    "calls": resolved_calls
                })
                for call_id in resolved_calls:
                    downstream_ids_to_fetch.add(call_id)

        # --- Step 4: Graph traversal for downstream dependencies ---
        downstream_context = []
        if downstream_ids_to_fetch:
            logger.info(f"Fetching {len(downstream_ids_to_fetch)} downstream dependencies")
            try:
                graph_results = self.collection.get(ids=list(downstream_ids_to_fetch))
                for i in range(len(graph_results["ids"])):
                    downstream_context.append({
                        "node_id": graph_results["ids"][i],
                        "code": graph_results["documents"][i]
                    })
            except Exception as e:
                logger.warning(f"Downstream fetch failed: {e}")

        return {
            "primary_nodes": primary_nodes,
            "downstream_context": downstream_context
        }