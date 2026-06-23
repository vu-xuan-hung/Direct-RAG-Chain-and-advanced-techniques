from typing import List, Any
from langchain_core.documents import Document
from .cross_encoder_reranker import CrossEncoderReranker
from .mmr import MMRReranker

class PostRetrievalPipeline:
    """
    Pipeline kết hợp Cross-Encoder và MMR để rerank tài liệu sau khi đã được truy xuất từ retriever cơ bản.
    - Cross-Encoder sẽ đánh giá mức độ liên quan giữa query và từng chunk để chọn ra top K tài liệu có điểm cao nhất.
    - MMR sẽ được sử dụng để đảm bảo sự đa dạng trong các tài liệu được chọn
    """
    def __init__(self, embeddings_model: Any, cross_encoder_model_name: str, device: str = "cpu"):
        self.cross_encoder_reranker = CrossEncoderReranker(model_name=cross_encoder_model_name, device=device)
        self.mmr_reranker = MMRReranker(embeddings_model=embeddings_model)

    def run_pipeline(
        self, 
        query: str, 
        candidate_docs: List[Document], 
        order: str = "ce_first", 
        ce_top_k: int = 15, 
        mmr_top_k: int = 5,
        mmr_lambda: float = 0.5
    ) -> List[Document]:
        """
        Run the post-retrieval pipeline using Cross-Encoder and MMR.
        
        :param query: The user query
        :param candidate_docs: The retrieved documents from the base retriever
        :param order: "ce_first" or "mmr_first"
        :param ce_top_k: Top K chunks to keep after Cross-Encoder
        :param mmr_top_k: Top K chunks to keep after MMR
        :param mmr_lambda: Diversity parameter for MMR (default 0.5)
        """
        if order == "ce_first":
            # 1. Rerank with Cross Encoder to get top ce_top_k
            reranked_docs = self.cross_encoder_reranker.rerank(
                query=query, 
                all_contexts=candidate_docs, 
                top_k=ce_top_k
            )
            # 2. Add diversity with MMR to get final mmr_top_k
            final_docs = self.mmr_reranker.rerank(
                query=query, 
                candidate_docs=reranked_docs, 
                top_k=mmr_top_k, 
                lambda_param=mmr_lambda
            )
        elif order == "mmr_first":
            # 1. Add diversity with MMR to get top ce_top_k (using ce_top_k as intermediate size)
            mmr_docs = self.mmr_reranker.rerank(
                query=query, 
                candidate_docs=candidate_docs, 
                top_k=ce_top_k, 
                lambda_param=mmr_lambda
            )
            # 2. Rerank with Cross Encoder to get final mmr_top_k
            final_docs = self.cross_encoder_reranker.rerank(
                query=query, 
                all_contexts=mmr_docs, 
                top_k=mmr_top_k
            )
        else:
            raise ValueError("order must be 'ce_first' or 'mmr_first'")
            
        return final_docs
