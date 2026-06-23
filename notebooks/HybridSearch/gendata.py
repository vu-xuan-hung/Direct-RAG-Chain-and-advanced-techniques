import os
import random

# Danh sách các mã lỗi
error_codes = [
    "ERR_503_SERVICE_UNAVAILABLE do overload", 
    "NXDOMAIN_1009", 
    "CRITICAL_BUG_X99",
    "ERR_CONNECTION_RESET_104",
    "TIMEOUT_408_GATEWAY",
    "DB_DEADLOCK_ERROR_0x889",
    "AUTH_FAILED_401_UNAUTHORIZED",
    "MEM_LEAK_WARN_9901"
]

# Danh sách các mã sản phẩm (SKUs/Models)
skus = [
    "Laptop ThinkPad-T14-Gen3-21AH", 
    "Bàn phím cơ KCH-990-RGB", 
    "Router RTX-8900-AX",
    "Màn hình Dell-U2723QE-4K",
    "Chuột Logitech-MX-Master-3S",
    "Server Dell-PowerEdge-R750",
    "Switch Cisco-C9200L-48P-4G",
    "Ổ cứng SSD-Samsung-980-Pro-1TB"
]

# Danh sách các thuật ngữ viết tắt (Acronyms)
acronyms = ["TCP/IP", "RESTful API", "k8s", "VPC", "JWT", "CI/CD", "AWS EC2", "IAM", "JSON", "DNS"]

# Các template văn xuôi mô tả ngữ cảnh
templates = [
    "Hệ thống vừa ghi nhận sự cố liên quan đến {error}. Đội ngũ kỹ thuật đang tiến hành kiểm tra nguyên nhân cốt lõi. Trong lúc này, các dịch vụ phụ thuộc vào {acronym} có thể bị gián đoạn. Vui lòng tham khảo tài liệu nội bộ để biết thêm chi tiết.",
    "Khách hàng báo cáo thiết bị {sku} không thể kết nối mạng. Qua kiểm tra ban đầu, có vẻ cấu hình {acronym} đang gặp vấn đề. Mã lỗi hiển thị trên màn hình là {error}. Cần gửi nhân viên hỗ trợ đến tận nơi.",
    "Hướng dẫn xử lý lỗi {error} trên thiết bị {sku}: Bước 1, kiểm tra kết nối mạng và đảm bảo {acronym} hoạt động bình thường. Bước 2, khởi động lại thiết bị. Nếu vẫn gặp lỗi, vui lòng liên hệ bộ phận IT.",
    "Theo chính sách bảo hành mới của công ty, các sản phẩm như {sku} sẽ được hỗ trợ kỹ thuật tận nơi. Tuy nhiên, nếu phát hiện lỗi phần mềm do cấu hình sai {acronym} dẫn đến {error}, khách hàng sẽ phải tự chịu trách nhiệm.",
    "Tài liệu thiết kế kiến trúc hệ thống mới: Chúng ta sẽ sử dụng {acronym} để tối ưu hóa hiệu suất giao tiếp giữa các microservices. Khi triển khai trên cụm máy chủ, cần theo dõi sát sao logs để phát hiện sớm {error}. Các thiết bị đầu cuối được đề xuất là {sku}.",
    "Báo cáo sự cố hệ thống: Vào lúc 02:00 AM, monitor báo động với mã {error}. Nguyên nhân do việc cập nhật module {acronym} gây ra xung đột với hệ thống quản lý kho của sản phẩm {sku}. Đã rollback về phiên bản trước đó.",
    "Quy trình khắc phục sự cố mạng: Khi người dùng phàn nàn về hiệu suất của {sku}, hãy yêu cầu họ cung cấp log hệ thống. Thường thì vấn đề nằm ở cấu hình {acronym} không chuẩn, dẫn đến {error}. Vui lòng tạo ticket trên hệ thống JIRA.",
    "Thông báo cập nhật firmware cho {sku}. Phiên bản mới này sẽ cải thiện độ ổn định và sửa triệt để {error}. Yêu cầu hệ thống phải hỗ trợ {acronym} trước khi tiến hành cập nhật để tránh rủi ro."
]

def generate_document():
    error = random.choice(error_codes)
    sku = random.choice(skus)
    acronym = random.choice(acronyms)
    
    # Chọn một template ngẫu nhiên và điền thông tin
    template = random.choice(templates)
    doc_content = template.format(error=error, sku=sku, acronym=acronym)
    
    # Thêm một vài câu ngẫu nhiên để làm đoạn văn dài hơn (từ 3-5 câu tổng cộng)
    extra_sentences = [
        f"Vui lòng ghi nhớ mã lỗi {error} để báo cáo lên cấp trên.",
        f"Thiết bị {sku} hiện đang trong tình trạng hết hàng tại các kho khu vực.",
        f"Kiến thức cơ bản về {acronym} là bắt buộc đối với tất cả nhân viên kỹ thuật.",
        "Việc đào tạo nội bộ sẽ được tổ chức vào thứ Sáu tuần này.",
        "Mọi thắc mắc xin vui lòng gửi email về địa chỉ support@company.com.",
        "Đây là thông báo tự động từ hệ thống giám sát cảnh báo.",
        "Nhớ kiểm tra lại các bản ghi log trong 24 giờ qua.",
        "Hãy luôn sao lưu dữ liệu trước khi thực hiện bất kỳ thay đổi nào."
    ]
    
    doc_content += " " + " ".join(random.sample(extra_sentences, random.randint(1, 3)))
    return doc_content

def main():
    # Lấy đường dẫn thư mục hiện tại của script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, 'data')
    
    # Tạo thư mục data/ nếu chưa có
    os.makedirs(target_dir, exist_ok=True)
    
    # Sinh ra 100 files
    for i in range(1, 101):
        filename = f"doc_{i:03d}.txt"
        filepath = os.path.join(target_dir, filename)
        content = generate_document()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    print(f"✅ Đã tạo thành công 100 file text với nội dung trộn lẫn vào thư mục '{target_dir}'.")

if __name__ == '__main__':
    main()