from langchain_community.retrievers import BM25Retriever
from indexing.vector_store import VectorStore
from core.config import settings
import pickle
from langchain_core.documents import Document
import os
import threading
vector_store = VectorStore()
class BM25RetrieverWrapper:
    def __init__(self):
        self.file_path = settings.BM25_PERSIST_PATH
        self.bm25_retriever = self.get_bm25_retriever()
    def get_bm25_retriever(self)->BM25Retriever:
        if os.path.exists(self.file_path):
            print("==== Load BM25 từ ổ đĩa cứng... ====")
            with open(self.file_path, 'rb') as f:
                bm25_retriever = pickle.load(f)
                
            bm25_retriever.k = settings.RETRIEVER_K_BM25
            return bm25_retriever
        print("==== File BM25 chưa có. Bắt đầu kéo data từ DB để build... ====")
        vectorstore = vector_store.get_vectorstore()
        existing_docs = vectorstore.get()
        # Khởi tạo BM25 từ dữ liệu trong Chroma DB
        if existing_docs and existing_docs.get('documents'):
            db_documents = [
                Document(page_content=content, metadata=meta or {})
                for content, meta in zip(existing_docs['documents'], existing_docs['metadatas'])
            ]
            bm25_retriever = BM25Retriever.from_documents(db_documents)
            bm25_retriever.k = settings.RETRIEVER_K_BM25
            
            with open(self.file_path, 'wb') as f:
                pickle.dump(bm25_retriever, f)
            print("==== Đã lưu BM25 xuống ổ cứng thành công!====")
        else:
            # DB trống
            bm25_retriever = BM25Retriever.from_texts(["Dữ liệu trống"])
            bm25_retriever.k = 1
        # Khởi tạo Vector Store 
        return bm25_retriever
    def invoke(self, query: str) -> list[Document]:
        return self.bm25_retriever.invoke(query)
# ─────────────────────────────────────────────
# Module-level singleton — load BM25 exactly once
# ─────────────────────────────────────────────
_shared_bm25: BM25RetrieverWrapper | None = None
_bm25_lock = threading.Lock()

def get_shared_bm25() -> BM25RetrieverWrapper:
    """Return the process-wide BM25RetrieverWrapper singleton."""
    global _shared_bm25
    if _shared_bm25 is None:
        with _bm25_lock:
            if _shared_bm25 is None:
                _shared_bm25 = BM25RetrieverWrapper()
    return _shared_bm25
