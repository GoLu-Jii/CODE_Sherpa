import os
import logging
from typing import List, Dict, Any
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaCloudDB:
    def __init__(self, collection_name: str = "codesherpa_ast"):
        self.collection_name = collection_name
        
        # Pull credentials from environment variables (.env)
        chroma_api_key = os.getenv("CHROMA_API_KEY")
        chroma_tenant = os.getenv("CHROMA_TENANT")
        chroma_database = os.getenv("CHROMA_DATABASE")

        if not chroma_api_key or not chroma_tenant or not chroma_database:
            logger.warning("Chroma Cloud credentials missing. Defaulting to local persistent DB for testing.")
            self.client = chromadb.PersistentClient(path="./chroma_local_data")
        else:
            # Connect to Chroma Cloud using the official CloudClient
            logger.info(f"Connecting to Chroma Cloud Database: {chroma_database}...")
            self.client = chromadb.CloudClient(
                api_key=chroma_api_key,
                tenant=chroma_tenant,
                database=chroma_database
            )
            
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"} # Cosine similarity is best for code search
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
            ids.append(chunk["id"]) # Natively supports your AST string IDs

        logger.info(f"Uploading {len(chunks)} nodes to Chroma Cloud...")
        
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("Chroma Cloud ingestion completed successfully.")

    def clear_collection(self):
        """Deletes the current collection from Chroma DB to free up space/reset state."""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Successfully deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection {self.collection_name}. It might not exist. Error: {e}")