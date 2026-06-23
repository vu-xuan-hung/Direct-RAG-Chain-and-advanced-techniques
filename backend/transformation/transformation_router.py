from core.config import settings

class TransformationRouter:
    def __init__(self, llm):
        self.llm = llm

    def route_query(self, query: str) -> str:
        """
        Classifies a user query into one of three categories: "simple", "vague", or "complex".
        - simple: Direct and clear queries. Pass directly to Retriever.
        - vague: Short or lacking context. Route to HyDE.
        - complex: Multi-part or comparison. Route to Query Decomposition.
        """
        # Optimized: Rule-based routing instead of slow LLM call
        cleaned_query = query.lower()
        words_count = len(cleaned_query.split())
        
        # Rule for complex: contains comparison keywords or has multiple parts
        if any(keyword in cleaned_query for keyword in ["so sánh", "khác biệt", "phân biệt", "và", "nhưng"]):
            if words_count > 7:
                return "complex"
                
        # Rule for vague: only truly single-word or 2-word queries trigger HyDE
        # e.g. "nghỉ phép", "lương" → vague; "quy định đi muộn" → simple
        if words_count <= 2:
            return "vague"
            
        return "simple"
