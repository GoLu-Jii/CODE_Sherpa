import json
import logging
import re
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphRetriever:
    def __init__(self, chroma_db):
        """Accepts the instantiated ChromaCloudDB instance."""
        self.collection = chroma_db.collection

    def _detect_file_query(self, query: str) -> str:
        # scan for .py
        match = re.search(r"([\w/\\\.\-]+\.py)", query.lower())
        
        return match.group(1).strip() if match else ""

    import re

    def _detect_symbol_query(self, query: str) -> str:

        patterns = [
            # 1. Backticks (The universal dev standard): `process_data` or `UserAuth`
            r"`([\w\.]+)`",
            
            # 2. Function execution syntax: init_db() or app.run()
            r"([\w\.]+)\(\)",
            
            # 3. Explicit prefix keywords: "function my_func", "class UserAuth", "method process"
            # It also catches optional quotes like: function 'my_func'
            r"(?:function|method|class|module|variable|symbol)\s+['\"]?([\w\.]+)['\"]?",
            
            # 4. Explicit suffix keywords: "my_func function", "UserAuth class"
            r"['\"]?([\w\.]+)['\"]?\s+(?:function|method|class|module)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return ""

    def _find_exact_file(self, file_path: str) -> List[str]:
        """
        Find exact file matches by file_path and normalized basename.
        First tries full path, then basename, then searches all files for basename match.
        """
        matching_ids = []
        basename = file_path.replace("\\", "/").split("/")[-1]

        # Try exact full path match first
        try:
            results = self.collection.get(
                where={"$and": [{"file_path": file_path}, {"type": "file"}]},
                include=["metadatas"]
            )
            if results and results.get('ids'):
                matching_ids.extend(results['ids'])
                logger.info(f"Found exact file match for '{file_path}': {results['ids']}")
                return list(set(matching_ids))
        except Exception as e:
            logger.debug(f"Exact path query failed: {e}")

        # Try basename match if full path didn't work
        if basename != file_path:
            try:
                results = self.collection.get(
                    where={"$and": [{"file_path": basename}, {"type": "file"}]},
                    include=["metadatas"]
                )
                if results and results.get('ids'):
                    matching_ids.extend(results['ids'])
                    logger.info(f"Found basename match for '{basename}': {results['ids']}")
                    return list(set(matching_ids))
            except Exception as e:
                logger.debug(f"Basename query failed: {e}")

        # Fall back to manual search through all file metadata
        # (Chroma's $contains doesn't work reliably for this use case)
        try:
            all_files = self.collection.get(
                where={"type": "file"},
                include=["metadatas"]
            )
            for i, file_id in enumerate(all_files.get('ids', [])):
                metadata = all_files.get('metadatas', [])[i]
                stored_path = metadata.get('file_path', '')
                # Check if stored path contains the basename
                if basename.lower() in stored_path.lower():
                    # Prefer exact basename endings
                    if stored_path.endswith(basename) or f"/{basename}" in stored_path:
                        matching_ids.append(file_id)
                        logger.info(f"Found file matching basename '{basename}' via manual search: {file_id}")
        except Exception as e:
            logger.debug(f"Manual file search failed: {e}")

        return list(set(matching_ids))  # Remove duplicates

    def _find_exact_symbol(self, symbol: str) -> List[str]:
        """
        Find exact matches for a symbol in the database.
        Returns list of matching node_ids with proper filtering.
        """
        matching_ids = []
        
        try:
            # Try exact match on qualified_name first
            results = self.collection.get(
                where={"qualified_name": symbol},
                include=["metadatas", "documents"]
            )
            if results and results['ids']:
                matching_ids.extend(results['ids'])
                logger.info(f"Found exact qualified_name match for '{symbol}': {results['ids']}")
            
            # If no qualified match, try function_name
            if not matching_ids:
                results = self.collection.get(
                    where={"function_name": symbol},
                    include=["metadatas", "documents"]
                )
                if results and results['ids']:
                    matching_ids.extend(results['ids'])
                    logger.info(f"Found exact function_name match for '{symbol}': {results['ids']}")
            
            # If still no match and symbol contains dots, try partial matches
            if not matching_ids and '.' in symbol:
                parts = symbol.split('.')
                function_name = parts[-1]
                results = self.collection.get(
                    where={"function_name": function_name},
                    include=["metadatas", "documents"]
                )
                if results and results['ids']:
                    # Filter to only those that end with the full symbol
                    for node_id in results['ids']:
                        if node_id.endswith(symbol):
                            matching_ids.append(node_id)
                    if matching_ids:
                        logger.info(f"Found partial match for '{symbol}': {matching_ids}")
        
        except Exception as e:
            logger.warning(f"Error during exact symbol lookup for '{symbol}': {e}")
        
        return list(set(matching_ids))  # Remove duplicates

    def retrieve_with_graph_context(self, query: str, n_results: int) -> Dict[str, Any]:
        """
        Executes Hybrid Search: Exact Symbol Lookup -> Semantic Search -> AST Graph Traversal -> Dependency Context Retrieval
        """
        logger.info(f"Executing Hybrid Graph-RAG for query: '{query}'")
        
        primary_nodes = []
        downstream_ids_to_fetch = set()
        
        # Step 1: Try file-level lookup first
        file_query = self._detect_file_query(query)
        if file_query:
            logger.info(f"Detected file query for: '{file_query}'")
            exact_matches = self._find_exact_file(file_query)
            if exact_matches:
                logger.info(f"Found {len(exact_matches)} exact file matches: {exact_matches}")
                exact_results = self.collection.get(ids=exact_matches)

                for i in range(len(exact_results['ids'])):
                    node_id = exact_results['ids'][i]
                    code = exact_results['documents'][i]
                    metadata = exact_results['metadatas'][i]

                    resolved_calls_str = metadata.get("resolved_calls", "[]")
                    resolved_calls = json.loads(resolved_calls_str)

                    primary_nodes.append({
                        "node_id": node_id,
                        "code": code,
                        "calls": resolved_calls
                    })

                    for call_id in resolved_calls:
                        downstream_ids_to_fetch.add(call_id)

        # Step 2: Try exact symbol lookup next
        if not primary_nodes:
            symbol = self._detect_symbol_query(query)
            if symbol:
                logger.info(f"Detected symbol query for: '{symbol}'")
                exact_matches = self._find_exact_symbol(symbol)
                
                if exact_matches:
                    logger.info(f"Found {len(exact_matches)} exact matches: {exact_matches}")
                    
                    # Fetch the exact match details
                    exact_results = self.collection.get(ids=exact_matches)
                    
                    for i in range(len(exact_results['ids'])):
                        node_id = exact_results['ids'][i]
                        code = exact_results['documents'][i]
                        metadata = exact_results['metadatas'][i]
                        
                        resolved_calls_str = metadata.get("resolved_calls", "[]")
                        resolved_calls = json.loads(resolved_calls_str)
                        
                        primary_nodes.append({
                            "node_id": node_id,
                            "code": code,
                            "calls": resolved_calls
                        })
                        
                        # Queue downstream dependencies
                        for call_id in resolved_calls:
                            downstream_ids_to_fetch.add(call_id)

        # Step 3: If no exact matches, fall back to semantic search
        if not primary_nodes:
            logger.info("No exact matches found, falling back to semantic search")
            search_results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not search_results or not search_results['ids'][0]:
                return {"primary_nodes": [], "downstream_context": []}
            
            # Process semantic search results
            for i in range(len(search_results['ids'][0])):
                node_id = search_results['ids'][0][i]
                code = search_results['documents'][0][i]
                metadata = search_results['metadatas'][0][i]
                
                resolved_calls_str = metadata.get("resolved_calls", "[]")
                resolved_calls = json.loads(resolved_calls_str)
                
                primary_nodes.append({
                    "node_id": node_id,
                    "code": code,
                    "calls": resolved_calls
                })
                
                # Queue downstream dependencies
                for call_id in resolved_calls:
                    downstream_ids_to_fetch.add(call_id)

        downstream_context = []
        
        # Step 3: Graph Traversal (Fetch explicitly dependent functions by String ID)
        if downstream_ids_to_fetch:
            logger.info(f"Fetching downstream dependencies: {downstream_ids_to_fetch}")
            
            # Direct database lookup by ID (No semantic search needed)
            graph_results = self.collection.get(
                ids=list(downstream_ids_to_fetch)
            )
            
            for i in range(len(graph_results['ids'])):
                downstream_context.append({
                    "node_id": graph_results['ids'][i],
                    "code": graph_results['documents'][i]
                })

        return {
            "primary_nodes": primary_nodes,
            "downstream_context": downstream_context
        }

    def format_llm_prompt(self, retrieval_data: Dict[str, Any], user_query: str) -> str:
        """Constructs the strict, hallucination-free prompt for the LLM."""
        prompt = (
            "You are CODE Sherpa, an expert architectural engineering AI.\n"
            "You must answer the user's question using ONLY the provided exact code chunks and explicit deterministic dependencies. Do not guess or hallucinate logic.\n\n"
            f"USER QUESTION: {user_query}\n\n"
            "--- PRIMARY RELEVANT CODE ---\n"
        )

        for node in retrieval_data["primary_nodes"]:
            prompt += f"Node [{node['node_id']}] context -> {node['calls']}:\n"
            prompt += f"```python\n{node['code']}\n```\n\n"

        if retrieval_data["downstream_context"]:
            prompt += "--- DOWNSTREAM DEPENDENCY CONTEXT ---\n"
            for dep in retrieval_data["downstream_context"]:
                prompt += f"Definition for [{dep['node_id']}]:\n"
                prompt += f"```python\n{dep['code']}\n```\n\n"

        return prompt