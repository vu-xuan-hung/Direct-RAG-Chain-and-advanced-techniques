import hashlib
import os
import shutil

# from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from core.config import settings
from core.device import DEVICE
from indexing.semantic_chuck import IndexingPipeline

class VectorStore:
    def __init__(self):
        self.vectorstore = None

    def get_vectorstore(self):
        if self.vectorstore is None:
            self.vectorstore = self._create_vectorstore()
        return self.vectorstore

    def _create_vectorstore(self):
        print(f"==== Đang khởi tạo mô hình nhúng ({settings.EMBEDDING_MODEL}) trên {DEVICE}... ====")
        embed = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': DEVICE}
        )
        print("==== Đang kết nối tới Chroma DB... ====")
        
        try:
            vectorstore = Chroma(
                collection_name=settings.COLLECTION_NAME,
                embedding_function=embed,
                persist_directory=settings.CHROMA_PERSIST_DIR,
                collection_metadata=settings.HNSW_metadata
            )
            # Kiểm tra dữ liệu và thử truy vấn mẫu để phát hiện lệch chiều (dimension mismatch)
            existing_docs = vectorstore._collection.count()
            if existing_docs > 0:
                vectorstore.similarity_search("kiểm tra kết nối", k=1)
        except Exception as e:
            print(f"==== Lỗi kết nối hoặc lệch chiều vector DB ({e}). Tiến hành dựng lại DB... ====")
            if os.path.exists(settings.CHROMA_PERSIST_DIR):
                try:
                    shutil.rmtree(settings.CHROMA_PERSIST_DIR)
                except Exception as del_err:
                    print(f"Không thể xóa thư mục cũ: {del_err}")
            
            vectorstore = Chroma(
                collection_name=settings.COLLECTION_NAME,
                embedding_function=embed,
                persist_directory=settings.CHROMA_PERSIST_DIR,
                collection_metadata=settings.HNSW_metadata
            )
            existing_docs = 0

        if existing_docs:
            print(f"==== DB đã có {existing_docs} chunks. Bỏ qua xử lý... ====")
        else:
            if not os.path.exists(settings.POLICY_PATH):
                print(f"Warning: Không tìm thấy file chính sách tại {settings.POLICY_PATH}")
            else:
                print("==== DB trống, bắt đầu tải và xử lý dữ liệu chính sách... ====")
                indexing_pipeline = IndexingPipeline(vectorstore=vectorstore, config=settings)
                indexing_pipeline.run_indexing()
                print("==== Hoàn thành tải và xử lý dữ liệu chính sách. ====")
        return vectorstore



