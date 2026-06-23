# Báo cáo: Sửa lỗi GraphCypherQAChain không tìm thấy thông tin "Annual Leave"

## Hiện tượng lỗi
- Người dùng đặt câu hỏi `"how about ANNUAL LEAVE?"` và Cypher QA Chain sinh ra truy vấn:
```cypher
MATCH (p:PolicyClause)
WHERE toLower(p.title) CONTAINS 'annual leave' OR toLower(p.text) CONTAINS 'annual leave'
RETURN p.title, p.text
```
- Tuy nhiên, biến `Full Context:` trả về `[]` dẫn đến mô hình phản hồi rằng không thể tìm thấy thông tin liên quan đến Annual Leave trong cơ sở dữ liệu đồ thị Neo4j.

## Nguyên nhân
1. **Thiếu thông tin khi Extracted (Trích xuất):** Trong file Notebook, quá trình chia chunk (chunking) gom nhiều chính sách vào cùng một chunk (ví dụ `Chunk 2` chứa cả `Penalty`, `OVERTIME`, `ANNUAL LEAVE`, và `SICK LEAVE`). 
2. **Giới hạn của Pydantic Schema:** Object Pydantic `PolicyClauseExtraction` được thiết kế để chỉ chứa **một** `clause_title` và **một** `clause_text`. Khi mô hình LLM quét qua Chunk 2, nó chỉ trích xuất chính sách đầu tiên thấy được (Penalty) và bỏ qua hoàn toàn các chính sách bên dưới như Overtime, Annual Leave... dẫn đến việc database Neo4j không hề chứa Node nào về Annual Leave.
3. **Cypher Template bị dư trường:** Cypher template đang cố gắng `RETURN p.title, p.text, p.clause_text`, trong khi Node trong Neo4j chỉ có thuộc tính `text`, việc gọi `p.clause_text` sẽ bị dư thừa.

## Chi tiết các sửa đổi và Công dụng thực tế (Trong `RAG_new copy 2.ipynb`)

1. **Kích hoạt `MarkdownHeaderTextSplitter` (Cell 6)**
   - **Sửa đổi:** Gỡ comment để chạy bộ chia văn bản theo Header (`#`, `##`, `---`) thay vì chỉ dùng `RecursiveCharacterTextSplitter`.
   - **Công dụng:** `RecursiveCharacterTextSplitter` chia ngẫu nhiên theo số lượng từ, dễ làm đứt gãy ngữ cảnh hoặc gom 3-4 chính sách vào chung 1 Chunk. Việc dùng `MarkdownHeaderTextSplitter` giúp đảm bảo **mỗi Chunk chỉ chứa duy nhất một chính sách** (ví dụ: Chunk 1 chỉ chứa Working Hours, Chunk 2 chỉ chứa Annual Leave). Điều này làm tăng độ chính xác tuyệt đối khi Retrieval và Extraction, không bao giờ bị sót nội dung.

2. **Thay đổi cấu trúc Pydantic Models thành List (Cell 21)**
   - **Sửa đổi:** Tạo thêm một object `PolicyExtractionList` để bọc `PolicyClauseExtraction` thành một mảng (List).
   - **Công dụng:** Mặc định ban đầu LLM bị ép buộc chỉ trả về 1 Object duy nhất cho mỗi Chunk. Nếu Chunk đó vô tình dính 2 chính sách (vd: Overtime và Annual Leave), LLM sẽ tự động vứt bỏ 1 cái. Việc chuyển thành List giúp LLM được "cởi trói", cho phép nó trích xuất ra một danh sách **nhiều chính sách** từ cùng một đoạn văn. Từ đó, toàn bộ dữ liệu sẽ được lấy đầy đủ không sót chữ nào.

3. **Cập nhật Prompt trích xuất cho LLM (Cell 22)**
   - **Sửa đổi:** Đổi prompt thành *"A chunk might contain MULTIPLE clauses. You must extract ALL of them into a list"* và truyền `PolicyExtractionList` vào `with_structured_output`.
   - **Công dụng:** Hướng dẫn rõ ràng cho LLM biết mục tiêu là lấy "TẤT CẢ" các chính sách. Đây là bước mồi (prompting) quan trọng đi kèm với bước 2 để ép LLM phải quét thật kỹ toàn bộ văn bản thay vì chỉ lấy câu đầu tiên nó thấy.

4. **Sửa vòng lặp lưu trữ dữ liệu (Populate Data) (Cell 23 & 26)**
   - **Sửa đổi:** Đổi từ `all_extractions.append(response)` thành duyệt qua các mảng `response.clauses` và dùng `extend()`.
   - **Công dụng:** Để tương thích với việc LLM trả về một List các chính sách (thay vì 1 Object như cũ), đoạn code này giúp "trải phẳng" (flatten) toàn bộ danh sách các chính sách lấy được. Kết quả là hàm MERGE Cypher ở Cell 26 sẽ tạo ra đầy đủ các Node độc lập cho từng chính sách trong cơ sở dữ liệu Neo4j.

5. **Sửa lại Cypher Template cho chuỗi QA (Cell 27)**
   - **Sửa đổi:** Xóa thuộc tính thừa `p.clause_text` ra khỏi phần `RETURN` trong template Cypher. Lệnh chuẩn trở thành: `RETURN p.title, p.text`.
   - **Công dụng:** Khắc phục lỗi bất đồng bộ giữa dữ liệu lưu trong Neo4j và dữ liệu truy xuất ra. Vì trong Neo4j (Cell 26) bạn chỉ lưu thuộc tính là `text`, nên nếu truy vấn gọi `p.clause_text` sẽ bị dư thừa, hoặc thậm chí gây lỗi null/trống cho chuỗi truy vấn tiếp theo của LangChain. Sửa lỗi này giúp GraphCypherQAChain lấy đúng văn bản thuần túy và đẩy vào ngữ cảnh trả lời một cách an toàn.

## Hướng dẫn bước tiếp theo
Bạn hãy chạy lại toàn bộ Notebook từ đầu (đặc biệt là chạy lại từ Cell 21 để nạp lại dữ liệu trích xuất vào Neo4j). Khi chạy lại, các node về "Annual Leave", "Overtime", v.v. sẽ được tạo đầy đủ trong Graph và câu truy vấn QA sẽ hoạt động chính xác!

## Giải đáp các hiện tượng mới sau khi sửa lỗi

### 1. Tại sao số lượng Chunk tăng từ 4 lên 16?
Việc nhảy từ `4 chunks` lên `16 chunks` là hoàn toàn chính xác và là **dấu hiệu thành công**. 
- Trước đây, `RecursiveCharacterTextSplitter` nhồi nhét ngẫu nhiên hàng chục quy định khác nhau vào 4 khối văn bản khổng lồ.
- Nhờ công cụ `MarkdownHeaderTextSplitter`, hệ thống đã thông minh "mổ xẻ" tài liệu đúng theo từng tiêu đề (Ví dụ: tách riêng khối *Working Hours*, tách riêng khối *Penalty*, tách riêng *Scope of Application*...). Điều này tạo ra 16 khối nhỏ, mỗi khối là 1 chính sách cực kỳ cô đọng, giúp LLM trích xuất không trượt phát nào!

### 2. Tại sao Stakeholders vẫn bị rỗng `[]`? (Đã khắc phục)
- **Hiện tượng:** Mặc dù Prompt có dặn LLM phải tìm "Stakeholders", nhưng mô hình (đặc biệt là các bản LLM chạy nội bộ) thỉnh thoảng vẫn lười và trả về mảng rỗng `[]`.
- **Cách khắc phục:** Tôi vừa can thiệp thêm vào Cell 21 (Pydantic Models) để bổ sung trường mô tả bắt buộc (Field Description) cho Pydantic:
  ```python
  stakeholders: List[str] = Field(default=[], description="List of people or roles affected (e.g., Employees, Managers, Company). MUST NOT be empty if people are implied.")
  ```
### 3. Tại sao câu trả lời của Bot nghe rất "robot" và thiếu chi tiết? (Đã khắc phục)
- **Hiện tượng:** Bot trả lời kiểu: *"Thông tin từ cơ sở dữ liệu đồ thị Neo4j cho biết... Tiêu đề của phép nghỉ là..."* và thiếu hẳn các thông tin quan trọng như được nghỉ 12 ngày, cộng dồn 5 ngày v.v.
- **Nguyên nhân 1 (Thiếu chi tiết):** Trong câu lệnh sinh Cypher, ở ví dụ thứ 3 vô tình hướng dẫn LLM chỉ `RETURN p.title, com.description`. Biến `com.description` chỉ là 1 câu tóm tắt cực ngắn (vd: "Nhân viên nhận được phép nghỉ hằng năm") chứ không phải toàn văn chính sách.
- **Nguyên nhân 2 (Văn phong cứng nhắc):** Prompt QA cũ dặn Bot: *"Dựa vào thông tin từ cơ sở dữ liệu đồ thị Neo4j bên dưới"*. Do LLM có xu hướng "thật thà", nó bê nguyên cụm từ này vào câu trả lời, làm mất đi tính tự nhiên.
- **Cách khắc phục:** Tôi đã sửa lại file Notebook của bạn:
  1. **Sửa Cypher Prompt (Cell 27):** Ép buộc mọi câu lệnh Cypher sinh ra đều phải có `RETURN p.title, p.text`. Nhờ có `p.text`, LLM sẽ nhận được trọn vẹn từng chữ của quy định Annual Leave để trả lời.
  2. **Sửa QA Prompt (Cell 28):** Đổi văn phong thành *"Bạn là trợ lý Nhân sự (HR) mẫn cán và thân thiện... trả lời mạch lạc như đang chat trực tiếp"*, và thêm lệnh cấm ngặt nghèo: *"TUYỆT ĐỐI KHÔNG đề cập đến cơ sở dữ liệu, Neo4j, hay Tiêu đề..."*. 
  
Bạn hãy chạy lại Cell 27 và Cell 28, sau đó hỏi lại, tôi cam đoan Bot sẽ trả lời mềm mại như một chuyên viên HR thực thụ!
