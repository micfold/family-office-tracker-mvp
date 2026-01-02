# src/core/vector_store.py
import chromadb
from chromadb.utils import embedding_functions
from typing import Optional, Dict


# We use a small, fast, local model. No data leaves the machine.
# 'all-MiniLM-L6-v2' is standard for this (80MB download once).
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class VectorRuleEngine:
    def __init__(self, persist_path=".data/chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)

        # Use default Sentence Transformer (local)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )

        # Get or create the collection for categorization rules
        self.collection = self.client.get_or_create_collection(
            name="transaction_rules",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}  # Cosine similarity is best for text matching
        )

    def add_rule(self, rule_id: str, description: str, metadata: Dict):
        """
        Learns a new rule.
        :param description: The transaction text (e.g. "Starbucks London")
        :param metadata: The result (e.g. {'category': 'Coffee', 'type': 'Expense'})
        """
        self.collection.upsert(
            ids=[rule_id],
            documents=[description],
            metadatas=[metadata]
        )

    def find_match(self, description: str, threshold: float = 0.3) -> Optional[Dict]:
        """
        Finds the closest matching rule.
        :param threshold: Maximum cosine distance allowed for a match. Chroma returns
                          a distance where 0 = exact match and smaller values mean
                          closer matches, so lower thresholds are stricter. A value
                          around 0.3 is quite strict; higher values (e.g. 0.5–0.8)
                          allow looser, more permissive semantic matches.
        """
        results = self.collection.query(
            query_texts=[description],
            n_results=1
        )

        if not results['ids'] or not results['ids'][0]:
            return None

        # Check distance (smaller distance = closer match)
        distance = results['distances'][0][0]
        if distance < threshold:
            return results['metadatas'][0][0]

        return None

    def delete_rule(self, rule_id: str):
        self.collection.delete(ids=[rule_id])