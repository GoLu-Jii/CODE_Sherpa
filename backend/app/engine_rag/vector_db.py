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

        logger.info(f"Uploading {len(chunks)} nodes to Chroma Cloud in batches...")
        
        # Chroma Cloud has a limit of 300 records per API call
        batch_size = 300
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            self.collection.upsert(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            logger.info(f"Uploaded batch {i//batch_size + 1} of {total_batches}")
            
        logger.info("Chroma Cloud ingestion completed successfully.")

    def clear_collection(self):
        """Deletes all items from the current collection to reset state without triggering 'soft deleted' errors in Chroma Cloud."""
        try:
            # Fetch only the IDs of all existing records to minimize payload size
            existing_data = self.collection.get(include=[])
            ids_to_delete = existing_data.get("ids", [])
            
            if ids_to_delete:
                # Delete in batches to respect rate limits / size limits
                batch_size = 300
                total_batches = (len(ids_to_delete) + batch_size - 1) // batch_size
                
                for i in range(0, len(ids_to_delete), batch_size):
                    batch_ids = ids_to_delete[i:i + batch_size]
                    self.collection.delete(ids=batch_ids)
                    
                logger.info(f"Successfully cleared {len(ids_to_delete)} documents from {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} is already empty.")
                
        except Exception as e:
            logger.error(f"Failed to clear documents from collection {self.collection_name}. Error: {e}")