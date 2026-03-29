import json
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphRetriever:
    def __init__(self, qdrant_db):
        """Accepts the instantiated QdrantGraphDB instance."""
        self.db = qdrant_db
        self.client = qdrant_db.client
        self.collection_name = qdrant_db.collection_name

    def retrieve_with_graph_context(self, query: str, limit: int = 2) -> Dict[str, Any]:
        """
        Executes Semantic Search -> AST Graph Traversal -> Dependency Context Retrieval
        """
        logger.info(f"Executing Qdrant Graph-RAG for query: '{query}'")
        
        # Step 1: Semantic Search for the primary target
        search_results = self.client.query(
            collection_name=self.collection_name,
            query_text=query,
            limit=limit
        )

        if not search_results:
            return {"primary_nodes": [], "downstream_context": []}

        primary_nodes = []
        downstream_ids_to_fetch = set()

        # Step 2: Extract primary nodes and identify dependencies
        for point in search_results:
            # Safely extract Qdrant payload (metadata + document text)
            payload = point.metadata if hasattr(point, 'metadata') else getattr(point, 'payload', {})
            code = getattr(point, 'document', payload.get('document', ''))
            
            node_id = payload.get("node_id", "Unknown")
            resolved_calls_str = payload.get("resolved_calls", "[]")
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
        
        # Step 3: Graph Traversal (Fetch explicitly dependent functions by UUID)
        if downstream_ids_to_fetch:
            # Convert string IDs to Qdrant UUIDs using our deterministic method
            uuid_list = [self.db.generate_deterministic_uuid(nid) for nid in downstream_ids_to_fetch]
            
            logger.info(f"Fetching downstream dependencies: {downstream_ids_to_fetch}")
            graph_results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=uuid_list
            )
            
            for record in graph_results:
                payload = getattr(record, 'payload', {})
                code = payload.get('document', '')
                downstream_context.append({
                    "node_id": payload.get("node_id", "Unknown"),
                    "code": code
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