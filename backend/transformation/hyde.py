from core.config import settings

class HyDEGenerator:
    def __init__(self, llm, embed):
        self.llm = llm
        self.embed = embed
    def generate_hypothetical_answer(self,query: str) -> str:
        """
        Sinh ra đoạn văn bản giả định chứa từ khóa chuyên môn.
        """
        system_prompt ="""
            Bạn là một chuyên gia Nhân sự (HR). Người dùng đang hỏi một câu rất ngắn hoặc mơ hồ về chính sách công ty.
            Nhiệm vụ của bạn: Hãy viết một đoạn văn (khoảng 3-4 câu) GIẢ ĐỊNH trả lời cho câu hỏi đó. 
            Không cần thông tin số liệu chính xác, nhưng PHẢI dùng các thuật ngữ chuyên ngành HR, quy trình công ty, văn bản pháp lý liên quan.
            Không mở bài hay kết luận, chỉ viết phần nội dung chính.
        """
        hypothetical_answer= self.llm.invoke(system_prompt + "\n\nUser question: " + query).content
        print(f"Hypothetical answer generated for query '{query}':\n{hypothetical_answer}\n")
        return hypothetical_answer
    def get_embeddings(self,query:str)-> list:
        heypothetical_answer = self.generate_hypothetical_answer(query)
        embedding = self.embed.embed_query(heypothetical_answer)
        return embedding
