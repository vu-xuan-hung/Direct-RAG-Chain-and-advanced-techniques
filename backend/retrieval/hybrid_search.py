# Hybrid search
from typing import List

from core.config import settings
from indexing.vector_store import VectorStore
from retrieval.bm25_retriever import get_shared_bm25
from langchain_classic.retrievers import EnsembleRetriever

# Shared singletons — initialized once at startup
_vector_store = VectorStore()


class HybridSearch:
    def __init__(self):
        bm25_wrapper = get_shared_bm25()
        self.vectorstore_retriever = _vector_store.get_vectorstore().as_retriever(
            search_kwargs={"k": settings.RETRIEVER_K}
        )
        self.bm25_retriever = bm25_wrapper.get_bm25_retriever()
        self.retriever_instance = EnsembleRetriever(
            retrievers=[self.vectorstore_retriever, self.bm25_retriever],
            weights=[0.5, 0.5],
        )

    def invoke(self, query: str) -> List:
        return self.retriever_instance.invoke(query)
