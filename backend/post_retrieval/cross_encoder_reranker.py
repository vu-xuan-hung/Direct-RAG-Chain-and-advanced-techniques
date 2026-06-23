from sentence_transformers import CrossEncoder
from typing import List
from langchain_core.documents import Document

class CrossEncoderReranker:
    def __init__(self, model_name: str, device: str = "cpu"):
        self.cross_encoder = CrossEncoder(model_name, device=device)

    def rerank(self, query: str, all_contexts: List[Document], top_k: int = 5) -> List[Document]:
        unique_docs = []
        seen_contents = set()
        
        for doc in all_contexts:
            content = doc.page_content.strip()
            if len(content) > 15 and content not in seen_contents:
                seen_contents.add(content)
                unique_docs.append(doc)
                
        if len(unique_docs) <= top_k:
            return unique_docs
        
        contents_to_rank = [doc.page_content for doc in unique_docs]
        ranks = self.cross_encoder.rank(query, contents_to_rank)
        
        top_contexts = []
        for rank in ranks:
            doc_index = rank['corpus_id']
            selected_doc = unique_docs[doc_index]
            if len(selected_doc.page_content.strip()) > 15:
                top_contexts.append(selected_doc)
                
            if len(top_contexts) == top_k:
                break
                
        return top_contexts
