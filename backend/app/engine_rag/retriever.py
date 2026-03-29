import json
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphRetriever:
    def __init__(self, chroma_db):
        """Accepts the instantiated ChromaCloudDB instance."""
        self.collection = chroma_db.collection

    def retrieve_with_graph_context(self, query: str, n_results: int = 2) -> Dict[str, Any]:
        """
        Executes Semantic Search -> AST Graph Traversal -> Dependency Context Retrieval
        """
        logger.info(f"Executing Chroma Graph-RAG for query: '{query}'")
        
        # Step 1: Semantic Search for the primary target
        search_results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        if not search_results or not search_results['ids'][0]:
            return {"primary_nodes": [], "downstream_context": []}

        primary_nodes = []
        downstream_ids_to_fetch = set()

        # Step 2: Extract primary nodes and identify dependencies
        for i in range(len(search_results['ids'][0])):
            node_id = search_results['ids'][0][i]
            code = search_results['documents'][0][i]
            metadata = search_results['metadatas'][0][i]
            
            # Parse the stringified graph data
            resolved_calls_str = metadata.get("resolved_calls", "[]")
            resolved_calls = json.loads(resolved_calls_str)
            
            primary_nodes.append({
                "node_id": node_id,
                "code": code,
                "calls": resolved_calls
            })
            
            # Queue the downstream dependencies for the secondary lookup
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