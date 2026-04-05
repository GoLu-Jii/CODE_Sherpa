import json
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphRetriever:
    def __init__(self, chroma_db):
        """Accepts the instantiated ChromaCloudDB instance."""
        self.collection = chroma_db.collection

    def _detect_symbol_query(self, query: str) -> str:
        """
        Detect if the query is asking about a specific code symbol.
        Returns the extracted symbol name if detected, empty string otherwise.
        """
        import re
        
        # Patterns for symbol lookup queries
        patterns = [
            r"what does (?:the function |function )?([\w\.]+) do\??",
            r"what is (?:the function |function )?([\w\.]+)\??",
            r"explain (?:the function |function )?([\w\.]+)",
            r"tell me about (?:the function |function )?([\w\.]+)",
            r"([\w\.]+) function",
            r"([\w\.]+) method",
        ]
        
        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return match.group(1)
        
        return ""

    def _find_exact_symbol(self, symbol: str) -> List[str]:
        """
        Find exact matches for a symbol in the database.
        Returns list of matching node_ids.
        """
        matching_ids = []
        
        try:
            # Try exact match on qualified_name first
            results = self.collection.get(
                where={"qualified_name": symbol}
            )
            if results and results['ids']:
                matching_ids.extend(results['ids'])
            
            # If no qualified match, try function_name
            if not matching_ids:
                results = self.collection.get(
                    where={"function_name": symbol}
                )
                if results and results['ids']:
                    matching_ids.extend(results['ids'])
            
            # If still no match and symbol contains dots, try partial matches
            if not matching_ids and '.' in symbol:
                parts = symbol.split('.')
                function_name = parts[-1]
                results = self.collection.get(
                    where={"function_name": function_name}
                )
                if results and results['ids']:
                    # Filter to only those that end with the full symbol
                    for node_id in results['ids']:
                        if node_id.endswith(symbol):
                            matching_ids.append(node_id)
        
        except Exception as e:
            logger.warning(f"Error during exact symbol lookup: {e}")
        
        return list(set(matching_ids))  # Remove duplicates

    def retrieve_with_graph_context(self, query: str, n_results: int) -> Dict[str, Any]:
        """
        Executes Hybrid Search: Exact Symbol Lookup -> Semantic Search -> AST Graph Traversal -> Dependency Context Retrieval
        """
        logger.info(f"Executing Hybrid Graph-RAG for query: '{query}'")
        
        primary_nodes = []
        downstream_ids_to_fetch = set()
        
        # Step 1: Try exact symbol lookup first
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
        
        # Step 2: If no exact matches or not a symbol query, fall back to semantic search
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
            prompt += f"Function [{node['node_id']}] explicitly calls -> {node['calls']}:\n"
            prompt += f"```python\n{node['code']}\n```\n\n"

        if retrieval_data["downstream_context"]:
            prompt += "--- DOWNSTREAM DEPENDENCY CONTEXT ---\n"
            for dep in retrieval_data["downstream_context"]:
                prompt += f"Definition for [{dep['node_id']}]:\n"
                prompt += f"```python\n{dep['code']}\n```\n\n"

        return prompt