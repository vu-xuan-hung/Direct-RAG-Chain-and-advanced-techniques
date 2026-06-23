import json
from core.config import settings
class QueryDecomposer:
    def __init__(self, llm):
        self.llm = llm
    def decompose(self, query: str) -> list[str]:
        """
        Tách câu hỏi phức tạp thành danh sách các câu hỏi con độc lập.
        """
        system_prompt = """
        Người dùng đang đặt một câu hỏi phức tạp yêu cầu thông tin từ nhiều khía cạnh hoặc so sánh.
        Hãy phân rã câu hỏi này thành một danh sách các câu hỏi con đơn giản hơn.
        Nguyên tắc quan trọng: Mỗi câu hỏi con phải TỰ ĐỨNG ĐỘC LẬP (phải giữ nguyên ngữ cảnh, không dùng đại từ thay thế như "nó", "chính sách đó").
        CHỈ trả về mảng JSON, tuyệt đối KHÔNG giải thích, KHÔNG bọc bằng markdown, KHÔNG thêm bất kỳ từ ngữ nào khác.
        Chỉ trả về JSON định dạng mảng các chuỗi: ["câu hỏi 1", "câu hỏi 2"]
        """
        response = self.llm.invoke(system_prompt + "\n\nUser question: " + query).content
        print(f"\n[DEBUG RAW LLM DECOMPOSE] {response}\n")
        
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        try:
            sub_questions = json.loads(cleaned_response)
            if isinstance(sub_questions, list) and all(isinstance(q, str) for q in sub_questions):
                return sub_questions
            else:
                return [query]
        except json.JSONDecodeError:
            print("[Warning] Decomposer fail parse JSON, fallback to original query.")
            return [query]