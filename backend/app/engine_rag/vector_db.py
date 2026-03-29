import os
import logging
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaCloudDB:
    def __init__(self, collection_name: str = "codesherpa_ast"):
        self.collection_name = collection_name
        
        # Pull credentials from environment variables (.env)
        chroma_host = os.getenv("CHROMA_HOST") # e.g., "api.chroma.cloud" or your custom URL
        chroma_port = os.getenv("CHROMA_PORT", "443")
        chroma_api_key = os.getenv("CHROMA_API_KEY")

        if not chroma_host:
            logger.warning("CHROMA_HOST missing. Defaulting to local persistent DB for testing.")
            self.client = chromadb.PersistentClient(path="./chroma_local_data")
        else:
            # Connect to Chroma Cloud / Remote Hosted Chroma
            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port,
                headers={"X-Chroma-Token": chroma_api_key} if chroma_api_key else {},
                settings=Settings(chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider") if chroma_api_key else Settings()
            )
            
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"} # Cosine similarity is best for code
        )

    def ingest_chunks(self, chunks: List[Dict[str, Any]]):
        """Ingests AST chunks into Chroma Cloud using native String IDs."""
        if not chunks:
            logger.warning("No chunks provided for ingestion.")
            return

        documents = []
        metadatas = []
        ids = []

        for chunk in chunks:
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"])
            ids.append(chunk["id"]) # Chroma natively supports your AST string IDs!

        logger.info(f"Uploading {len(chunks)} nodes to Chroma Cloud...")
        
        # Upsert automatically handles embeddings if no custom embedding function is passed
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("Chroma Cloud ingestion completed successfully.")