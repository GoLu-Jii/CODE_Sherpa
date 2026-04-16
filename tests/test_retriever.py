import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
import unittest
from app.engine_rag.retriever import GraphRetriever


class DummyCollection:
    def __init__(self, ids_by_file=None, documents_by_id=None, metadata_by_id=None):
        self.ids_by_file = ids_by_file or {}
        self.documents_by_id = documents_by_id or {}
        self.metadata_by_id = metadata_by_id or {}

    def get(self, ids=None, where=None):
        if ids is not None:
            documents = [self.documents_by_id.get(node_id, "") for node_id in ids]
            metadatas = [self.metadata_by_id.get(node_id, {}) for node_id in ids]
            return {"ids": ids, "documents": documents, "metadatas": metadatas}

        if where is not None:
            file_path = where.get("file_path")
            if isinstance(file_path, dict) and file_path.get("$contains"):
                substring = file_path["$contains"]
                ids = [node_id for fp, node_ids in self.ids_by_file.items() for node_id in node_ids if substring in fp]
                return {"ids": ids, "documents": [self.documents_by_id[node_id] for node_id in ids], "metadatas": [self.metadata_by_id[node_id] for node_id in ids]}

            if file_path is not None:
                ids = self.ids_by_file.get(file_path, [])
                return {"ids": ids, "documents": [self.documents_by_id.get(node_id, "") for node_id in ids], "metadatas": [self.metadata_by_id.get(node_id, {}) for node_id in ids]}

        return {"ids": [], "documents": [], "metadatas": []}

    def query(self, query_texts=None, n_results=None):
        return {"ids": [[]], "documents": [[]], "metadatas": [[]]}


class GraphRetrieverFileQueryTests(unittest.TestCase):
    def setUp(self):
        ids_by_file = {
            "src/requests/compat.py": ["src.requests.compat._compat_function"],
            "compat.py": ["src.requests.compat._compat_function"],
        }
        documents_by_id = {
            "src.requests.compat._compat_function": "def _compat_function():\n    pass\n"
        }
        metadata_by_id = {
            "src.requests.compat._compat_function": {"resolved_calls": "[]", "file_path": "src/requests/compat.py"}
        }
        self.collection = DummyCollection(ids_by_file, documents_by_id, metadata_by_id)
        self.retriever = GraphRetriever(chroma_db=type("DB", (), {"collection": self.collection}))

    def test_detect_file_query(self):
        self.assertEqual(self.retriever._detect_file_query("what does the file compat.py do?"), "compat.py")
        self.assertEqual(self.retriever._detect_file_query("explain src/requests/compat.py"), "src/requests/compat.py")
        self.assertEqual(self.retriever._detect_file_query("what is purpose of the file exceptions.py"), "exceptions.py")
        self.assertEqual(self.retriever._detect_file_query("what is the purpose of the file exceptions.py"), "exceptions.py")

    def test_find_exact_file_matches_basename(self):
        matches = self.retriever._find_exact_file("compat.py")
        self.assertEqual(matches, ["src.requests.compat._compat_function"])

    def test_retrieve_with_graph_context_file_query(self):
        retrieval = self.retriever.retrieve_with_graph_context("what does the file compat.py do?", n_results=1)
        self.assertEqual(len(retrieval["primary_nodes"]), 1)
        self.assertEqual(retrieval["primary_nodes"][0]["node_id"], "src.requests.compat._compat_function")
        self.assertEqual(retrieval["downstream_context"], [])


if __name__ == "__main__":
    unittest.main()
