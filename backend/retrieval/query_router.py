import re

class QueryRouter:
    def __init__(self):
        # Regex to detect product IDs, Error codes, or specific versions
        # Matches formats like: ERR-404, V2.5, HR-402, TX_990
        self.keyword_pattern = re.compile(r'\b[A-Z]+[-\._]*\d+\b|\b\d+\.\d+\b')
        
    def route(self, query: str) -> str:
        """
        Analyzes the query and returns the optimal search strategy:
        'keyword', 'semantic', or 'hybrid'
        """
        query_length = len(query.split())
        has_id = bool(self.keyword_pattern.search(query))
        
        # Scenario 1: User is looking up a specific code or ID
        if has_id and query_length < 5:
            return "keyword"  # Prioritize BM25 entirely
            
        # Scenario 2: User is asking a broad, conceptual question
        elif not has_id and query_length > 7:
            return "semantic" # Prioritize Vector Search
            
        # Default fallback: The safest option
        return "hybrid"
    
