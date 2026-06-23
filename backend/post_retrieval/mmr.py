import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Any
from langchain_core.documents import Document

class MMRReranker:
    def __init__(self, embeddings_model: Any):
        """
        :param embeddings_model: An embeddings model instance that has embed_query and embed_documents methods
        """
        self.embeddings_model = embeddings_model

    def rerank(self, query: str, candidate_docs: List[Document], top_k: int = 5, lambda_param: float = 0.5) -> List[Document]:
        if len(candidate_docs) <= top_k:
            return candidate_docs
        
        query_embedding = self.embeddings_model.embed_query(query)
        embedding_docs = self.embeddings_model.embed_documents([doc.page_content for doc in candidate_docs])
        
        # tính cosine similarity giữa query và từng document
        query_doc = cosine_similarity([query_embedding], embedding_docs)[0]
        # tính cosine similarity cho từng document
        doc_docs = cosine_similarity(embedding_docs, embedding_docs)
       
        selected_indices = []
        unselected_indices = list(range(len(embedding_docs)))
        
        first_docs = np.argmax(query_doc)
        selected_indices.append(int(first_docs))
        unselected_indices.remove(int(first_docs))

        while len(selected_indices) < top_k and unselected_indices:
            best_idx = -1
            best_score = -np.inf
            for unselect in unselected_indices:
                Sim1 = query_doc[unselect]
                Sim2 = max([doc_docs[unselect][selected] for selected in selected_indices])
                MMR_score = lambda_param * Sim1 - (1 - lambda_param) * Sim2
                if MMR_score > best_score:
                    best_idx = unselect
                    best_score = MMR_score
            selected_indices.append(best_idx)
            unselected_indices.remove(best_idx)
            
        return [candidate_docs[i] for i in selected_indices]
