
import hashlib
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import TextLoader
from core.config import settings
from core.device import DEVICE
class IndexingPipeline:
    def __init__(self, vectorstore,config):
        self.vectorstore = vectorstore
        self.config = config
        
        self.embedder = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': DEVICE}
        )
    def generate_chunk_ids(self, chunks):
        ids = []
        for chunk in chunks:
            unique_string = f"{chunk.page_content}-{chunk.metadata.get('source', '')}"
            chunk_id = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
            ids.append(chunk_id)
        return ids
    def run_indexing(self):
        print("==== Đang tải và xử lý dữ liệu chính sách... ====")
        loader = TextLoader(settings.POLICY_PATH, encoding="utf-8")
        documents = loader.load()
        text_splitter = SemanticChunker(
            self.embedder,
            breakpoint_threshold_type=settings.breakpoint_threshold_type,
            breakpoint_threshold_amount=settings.breakpoint_threshold_amount
        )
        chunks = text_splitter.split_documents(documents)
        chunk_ids = self.generate_chunk_ids(chunks)

        self.vectorstore.add_documents(documents=chunks, ids=chunk_ids)
        return True