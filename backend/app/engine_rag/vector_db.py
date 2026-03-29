import os
import uuid
import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantGraphDB:
    def __init__(self, collection_name: str = "codesherpa_ast"):
        self.collection_name = collection_name
        
        # Pull credentials from environment variables (.env)
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url or not qdrant_api_key:
            logger.warning("QDRANT_URL or API_KEY missing. Defaulting to local memory DB for testing.")
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )
            
        # Initializes the fastembed local model automatically
        self.client.set_model("BAAI/bge-small-en-v1.5") 

    def generate_deterministic_uuid(self, node_id: str) -> str:
        """Converts string IDs (src.api.get) into Qdrant-compliant UUIDs deterministically."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, node_id))

    def ingest_chunks(self, chunks: List[Dict[str, Any]]):
        """Ingests AST chunks into Qdrant Cloud."""
        if not chunks:
            logger.warning("No chunks provided for ingestion.")
            return

        documents = []
        metadatas = []
        ids = []

        for chunk in chunks:
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"])
            ids.append(self.generate_deterministic_uuid(chunk["id"]))

        logger.info(f"Uploading {len(chunks)} nodes to Qdrant Cloud...")
        
        # Qdrant's high-level API handles the embedding generation automatically
        self.client.add(
            collection_name=self.collection_name,
            documents=documents,
            metadata=metadatas,
            ids=ids
        )
        logger.info("Qdrant ingestion completed successfully.")