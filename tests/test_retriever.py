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

    def get(self, ids=None, where=None, include=None, limit=None):
        if ids is not None:
            documents = [self.documents_by_id.get(node_id, "") for node_id in ids if node_id in self.documents_by_id]
            metadatas = [self.metadata_by_id.get(node_id, {}) for node_id in ids if node_id in self.metadata_by_id]
            return {"ids": ids, "documents": documents, "metadatas": metadatas}

        if where is not None:
            filters = {}
            if "$and" in where:
                for cond in where["$and"]:
                    filters.update(cond)
            else:
                filters.update(where)

            matched_ids = []
            for node_id, meta in self.metadata_by_id.items():
                match = True
                for k, v in filters.items():
                    if k == "file_path":
                        stored_fp = meta.get("file_path", "")
                        if v != stored_fp and v != stored_fp.split('/')[-1]:
                            match = False
                            break
                    elif meta.get(k) != v:
                        if k == "type" and "type" not in meta:
                            pass
                        else:
                            match = False
                            break
                if match:
                    matched_ids.append(node_id)

            if not matched_ids and "file_path" in filters and filters.get("type") != "function":
                fp = filters["file_path"]
                matched_ids = self.ids_by_file.get(fp, [])
                if not matched_ids and "/" not in fp:
                    for stored_fp, ids_list in self.ids_by_file.items():
                        if stored_fp.endswith(fp) or stored_fp.split('/')[-1] == fp:
                            matched_ids.extend(ids_list)
                matched_ids = list(set(matched_ids))

            if limit is not None:
                matched_ids = matched_ids[:limit]

            documents = [self.documents_by_id.get(node_id, "") for node_id in matched_ids]
            metadatas = [self.metadata_by_id.get(node_id, {}) for node_id in matched_ids]
            return {"ids": matched_ids, "documents": documents, "metadatas": metadatas}

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
            "src.requests.compat._compat_function": {"resolved_calls": "[]", "file_path": "src/requests/compat.py", "type": "file"}
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
