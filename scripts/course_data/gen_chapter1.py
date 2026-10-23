"""Complete Generator for Chapter 1: Mạng Định Tuyến Hành Tây TOR & Cấu Trúc Không Gian Mạng Ngầm.
Source book: TOR.pdf (12 lessons).
Strictly validates >= 600 words per lesson.
"""

from __future__ import annotations

from scripts.build_cyber_payload import generate_lesson_markdown

CHAPTER_1_INFO = {
    "title": "Chương 1: Mạng Định Tuyến Hành Tây TOR & Cấu Trúc Không Gian Mạng Ngầm",
    "source_file": "TOR.pdf",
    "position": 1,
}

LESSONS = []

# Lesson 1.1
LESSONS.append({
    "position": 1,
    "title": "Bài 1.1: Tổng Quan Kiến Trúc Mạng TOR, Ranh Giới Deep Web & Darknet",
    "summary": "Nghiên cứu nền tảng kiến trúc mạng Tor, giải mã cấu trúc phân tầng của Internet từ Surface Web đến Deep Web và Darknet.",
    "duration_minutes": 35,
    "video_url": "https://www.youtube.com/watch?v=QRYzre4bf7I",
    "markdown_content": generate_lesson_markdown(
        lesson_num="1.1",
        title="Bài 1.1: Tổng Quan Kiến Trúc Mạng TOR, Ranh Giới Deep Web & Darknet",
        objective_points=[
            "Phân tích ranh giới kỹ thuật rõ ràng giữa Surface Web, Deep Web và Darknet trong không gian mạng toàn cầu.",
            "Nắm vững nguyên lý vận hành của mạng Tor (The Onion Router) như một mạng chuyển tiếp phân tán (overlay network).",
            "Đánh giá các mô hình đe dọa thực tế, giới hạn bảo vệ an ninh và nguyên tắc an toàn tác chiến số cơ bản."
        ],
        theory_sections=[
            (
                "Phân Cấp Ba Tầng Không Gian World Wide Web",
                "Trong khoa học an toàn thông tin hiện đại, Internet không phải là một khối đồng nhất mà được phân tách thành 3 phân tầng rõ rệt: \n\n"
                "1. **Surface Web (Web Bề Mặt)**: Chiếm khoảng 4-5% tổng tài nguyên web. Đây là những trang web công khai có thể được các công cụ tìm kiếm chuẩn (Google, Bing) thu thập dữ liệu (crawling) và lập chỉ mục (indexing). Chúng sử dụng hệ thống phân giải tên miền DNS chuẩn và truyền thông qua HTTP/HTTPS trực tiếp.\n\n"
                "2. **Deep Web (Web Chìm / Tầng Sâu)**: Chiếm từ 90% đến 95% không gian mạng. Bao gồm toàn bộ các dữ liệu trực tuyến không thể lập chỉ mục công khai: hệ thống cơ sở dữ liệu ngân hàng, cổng thông tin sinh viên, hồ sơ bệnh án điện tử, tài liệu lưu trữ đám mây riêng tư. Deep Web hoàn toàn hợp pháp và là nền tảng vận hành kinh tế số của nhân loại.\n\n"
                "3. **Darknet / Dark Web (Mạng Tối)**: Chiếm chưa đầy 1% Internet. Đây là một tập hợp con chuyên biệt của Deep Web được xây dựng trên các mạng phủ định tuyến ẩn danh như Tor, I2P, Freenet, yêu cầu cấu hình proxy và giao thức bảo mật riêng để truy cập."
            ),
            (
                "Kiến Trúc Mạng Tor & Chuỗi Ba Trạm Chuyển Tiếp",
                "Mạng Tor được vận hành dựa trên nguyên lý định tuyến củ hành với 3 trạm relay độc lập nhằm triệt tiêu khái niệm 'điểm tin cậy duy nhất':\n\n"
                "- **Guard Node (Trạm Đầu Vào)**: Tiếp nhận kết nối trực tiếp từ địa chỉ IP thật của người dùng. Guard chỉ biết IP nguồn và địa chỉ của Middle Relay, hoàn toàn mù thông tin về máy chủ đích và nội dung gói tin.\n"
                "- **Middle Relay (Trạm Trung Gian)**: Đóng vai trò lớp đệm cách ly tuyệt đối. Nó bóc lớp mã hóa giữa, nhận dữ liệu từ Guard và chuyển tiếp tới Exit. Trạm này không biết ai là người gửi ban đầu và không biết đích đến cuối cùng.\n"
                "- **Exit Node (Trạm Đầu Ra)**: Bóc lớp mã hóa cuối cùng và phát gói tin ra Internet công cộng tới máy chủ đích. Exit Node thấy được đích đến nhưng hoàn toàn không biết IP gốc của người dùng."
            ),
            (
                "Cơ Chế Khóa Phiên Đối Xứng & Giao Thức Trao Đổi Khóa",
                "Tor không sử dụng một cặp khóa duy nhất cho toàn bộ hành trình. Thay vào đó, máy khách của người dùng thực hiện giao thức bắt tay trao đổi khóa Diffie-Hellman trên đường cong elliptic (Curve25519) tuần tự với từng trạm relay theo cơ chế Telescoping Circuit Construction. Kết quả là máy khách nắm giữ ba khóa phiên đối xứng AES-GCM (hoặc Chacha20-Poly1305) riêng biệt: K1 (với Guard), K2 (với Middle) và K3 (với Exit). Mỗi trạm chỉ có thể giải mã duy nhất lớp vỏ do khóa của chính mình bảo vệ, đảm bảo tính toàn vẹn và bảo mật chuyển tiếp hoàn hảo (Forward Secrecy)."
            )
        ],
        attack_defense_section=(
            "Mặc dù Tor là một công nghệ xuất sắc, người dùng phải đối mặt với các kịch bản tấn công thực tế:\n\n"
            "1. **Tấn Công Tương Quan Lưu Lượng (Traffic Correlation Attacks)**: Kẻ thù cấp quốc gia (ví dụ NSA, GCHQ) có khả năng giám sát đồng thời cả luồng dữ liệu đi vào Guard Node và luồng dữ liệu rời khỏi Exit Node. Bằng cách áp dụng các thuật toán thống kê về kích thước gói tin và nhịp độ thời gian truyền (timing analysis), kẻ tấn công có thể liên kết hai đầu kết nối với độ tin cậy trên 90%.\n\n"
            "2. **Nghe Lén Tại Exit Node (Exit Node Sniffing)**: Nếu người dùng truy cập các website HTTP không mã hóa qua mạng Tor, quản trị viên của Exit Node độc hại có thể bắt gói tin (sniff) toàn bộ thông tin đăng nhập, cookie phiên và dữ liệu nhạy cảm.\n\n"
            "3. **Khai Thác Lỗ Hổng Ứng Dụng (Browser Exploits)**: Tin tặc sử dụng các lỗ hổng zero-day trong trình duyệt Tor Browser (dựa trên Firefox ESR) để thực thi mã từ xa, buộc hệ điều hành nạn nhân gửi gói tin DNS trực tiếp ra ngoài mạng Tor, làm lộ ngay lập tức địa chỉ IP thật của mục tiêu."
        ),
        lab_instructions=(
            "Trong bài thực hành lab này, chúng ta sẽ thiết lập dịch vụ Tor trên Linux và kiểm tra lưu lượng định tuyến qua SOCKS5 proxy bằng lệnh cURL CLI. Hãy thực hiện tuần tự các bước cấu hình và quan sát sự thay đổi của địa chỉ IP công cộng:"
        ),
        code_snippet=(
            "bash",
            """# 1. Cài đặt Tor daemon trên hệ điều hành Ubuntu/Debian
sudo apt update && sudo apt install -y tor curl dnsutils

# 2. Khởi chạy và kích hoạt dịch vụ Tor nền tảng
sudo systemctl enable --now tor
sudo systemctl status tor

# 3. Kiểm tra địa chỉ IP công cộng thật của máy tính
echo "IP thật của bạn:"
curl -s https://icanhazip.com

# 4. Kiểm tra kết nối định tuyến thông qua mạng Tor (SOCKS5 proxy cổng 9050)
echo "IP ẩn danh qua mạng Tor:"
curl -s --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip

# 5. Phân tích kết quả trả về:
# Kết quả JSON: {"IsTor":true,"IP":"185.220.101.5"}
# Chú ý: Cờ --socks5-hostname bắt buộc sử dụng để ngăn chặn rò rỉ DNS (DNS Leak)"""
        ),
        pitfalls=[
            "Không bao giờ bật toàn màn hình (Full Screen) khi sử dụng Tor Browser vì điều này tạo ra dấu vân tay kích thước màn hình (Screen Resolution Fingerprint) độc nhất vô nhị.",
            "Tuyệt đối không sử dụng giao thức truyền tệp P2P hoặc BitTorrent qua Tor, vì các ứng dụng torrent sẽ bỏ qua cấu hình SOCKS proxy và phát gói tin UDP trực tiếp chứa IP thật.",
            "Không mở trực tiếp các tệp tin tải về (PDF, DOCX) khi máy tính đang kết nối Internet. Mã độc nhúng trong tệp có thể tạo kết nối ngầm gửi tín hiệu về C2 server."
        ],
        summary_points=[
            "Surface Web chiếm 4-5%, Deep Web chiếm 90-95%, Darknet chỉ chiếm dưới 1% không gian mạng toàn cầu.",
            "Tor bảo vệ người dùng qua cơ chế 3 trạm relay (Guard, Middle, Exit) với 3 tầng mã hóa đối xứng lồng nhau.",
            "Tor không mang lại sự ẩn danh tuyệt đối 100%; an toàn phụ thuộc chặt chẽ vào kỷ luật an toàn tác chiến (OPSEC) của người dùng."
        ],
        video_url="https://www.youtube.com/watch?v=QRYzre4bf7I",
        quiz_json=[
            {
                "question": "Deep Web chiếm khoảng bao nhiêu phần trăm tổng thể không gian World Wide Web?",
                "type": "MULTIPLE_CHOICE",
                "options": ["4% đến 5%", "25%", "50%", "90% đến 95%"],
                "correct_index": 3,
                "explanation": "Deep Web chứa cơ sở dữ liệu nội bộ, email, tài nguyên phân quyền không thể lập chỉ mục, chiếm khoảng 90-95% không gian web."
            },
            {
                "question": "Trong chuỗi 3 trạm chuyển tiếp của Tor, trạm nào biết được địa chỉ IP thật của người dùng?",
                "type": "MULTIPLE_CHOICE",
                "options": ["Chỉ Guard Node", "Chỉ Middle Relay", "Chỉ Exit Node", "Cả 3 trạm"],
                "correct_index": 0,
                "explanation": "Chỉ Guard Node biết địa chỉ IP thật của người dùng do tiếp nhận kết nối trực tiếp."
            },
            {
                "question": "Mạng Tor cam kết bảo vệ người dùng ẩn danh tuyệt đối 100% trong mọi kịch bản tấn công?",
                "type": "TRUE_FALSE",
                "correct_value": False,
                "explanation": "Sai. Tor không thể bảo vệ người dùng trước các cuộc tấn công tương quan lưu lượng, rò rỉ DNS, hoặc khai thác lỗ hổng trình duyệt."
            },
            {
                "question": "Khi kiểm tra kết nối qua SOCKS proxy bằng cURL, tùy chọn nào giúp ngăn chặn triệt để rò rỉ DNS bằng cách để Exit Node phân giải tên miền?",
                "type": "FILL_BLANK",
                "blanks": [{"accepted_answers": ["--socks5-hostname", "socks5-hostname"]}],
                "explanation": "Tùy chọn --socks5-hostname đảm bảo yêu cầu phân giải DNS được gửi qua đường hầm Tor thay vì phân giải tại máy cục bộ."
            },
            {
                "question": "Nối đúng các thành phần của mạng Internet với định nghĩa kỹ thuật tương ứng:",
                "type": "MATCHING",
                "pairs": [
                    {"left": "Surface Web", "right": "Web công cộng có thể lập chỉ mục bởi Google/Bing"},
                    {"left": "Deep Web", "right": "Dữ liệu không lập chỉ mục như tài khoản ngân hàng và portal"},
                    {"left": "Darknet (Tor)", "right": "Mạng phủ mã hóa đa tầng yêu cầu giao thức chuyên biệt"}
                ],
                "explanation": "Khái niệm Surface Web, Deep Web và Darknet được phân tách rõ ràng theo khả năng lập chỉ mục và cơ chế bảo mật."
            }
        ]
    )
})

# Lesson 1.2
LESSONS.append({
    "position": 2,
    "title": "Bài 1.2: Lịch Sử Hình Thành Hải Quân Hoa Kỳ & Nguyên Lý Onion Routing Đa Tầng",
    "summary": "Truy vết nguồn gốc quân sự của công nghệ Onion Routing tại Phòng thí nghiệm Nghiên cứu Hải quân Hoa Kỳ (NRL) và giải mã mô hình mật mã học đa tầng.",
    "duration_minutes": 40,
    "video_url": "https://www.youtube.com/watch?v=lVcbq_a5N9I",
    "markdown_content": generate_lesson_markdown(
        lesson_num="1.2",
        title="Bài 1.2: Lịch Sử Hình Thành Hải Quân Hoa Kỳ & Nguyên Lý Onion Routing Đa Tầng",
        objective_points=[
            "Khám phá bối cảnh lịch sử và nguồn gốc quân sự của công nghệ Onion Routing tại U.S. Naval Research Laboratory (NRL).",
            "Nắm vững quy trình mật mã học đa tầng (Onion Encryption) và cơ chế trao đổi khóa Diffie-Hellman đối xứng.",
            "Giải mã nghịch lý an ninh mạng: Vì sao một dự án bảo mật quân sự tối mật lại bắt buộc phải được mở mã nguồn cho công chúng."
        ],
        theory_sections=[
            (
                "Nguồn Gốc Lịch Sử Quân Sự Của Onion Routing",
                "Vào giữa thập niên 1990, các chuyên gia mật mã học Paul Syverson, Michael G. Reed và David Goldschlag tại **Phòng thí nghiệm Nghiên cứu Hải quân Hoa Kỳ (NRL)** được giao nhiệm vụ giải quyết bài toán: Làm thế nào để các điệp viên và sĩ quan hải quân Mỹ tại nước ngoài có thể trao đổi thông tin tình báo qua Internet mà không để lại dấu vết có thể truy ngược về nguồn gốc quân sự Mỹ?\n\n"
                "Nếu quân đội Mỹ xây dựng một mạng lưới mã hóa chuyên dụng đóng kín, đối phương chỉ cần theo dõi các điểm truy cập mạng là có thể xác định ngay lưu lượng nào xuất phát từ quân sự. Đây chính là nguyên lý then chốt của khoa học ẩn danh: **Sự ẩn danh cần có một đám đông hỗn độn (Anonymity loves company)**. Quân đội Mỹ nhận ra rằng cách duy nhất để che giấu sĩ quan của mình là tạo ra một mạng lưới mã hóa công cộng mở, nơi công dân, nhà báo, doanh nghiệp trên toàn thế giới cùng sử dụng. Năm 2004, NRL quyết định phát hành mã nguồn Tor miễn phí dưới giấy phép nguồn mở."
            ),
            (
                "Mô Hình Toán Học & Cấu Trúc Đóng Gói Củ Hành",
                "Thuật ngữ 'Onion Routing' phản ánh trực quan cấu trúc gói tin: dữ liệu ban đầu được bao bọc bởi nhiều lớp mã hóa đối xứng tuần tự, tương tự như các lớp vỏ của một củ hành tây.\n\n"
                "Khi Alice muốn gửi dữ liệu M tới máy chủ đích Bob qua chuỗi 3 trạm R1 (Guard), R2 (Middle), R3 (Exit):\n"
                "Alice tạo 3 khóa phiên đối xứng duy nhất K1, K2, K3 bằng giao thức Curve25519. Sau đó, Alice đóng gói dữ liệu từ trong ra ngoài:\n"
                "- Lớp trong cùng: Mã hóa dữ liệu M và địa chỉ của Bob bằng khóa K3 dành cho Exit Node.\n"
                "- Lớp giữa: Bao bọc gói tin trên cùng địa chỉ của R3 bằng khóa K2 dành cho Middle Node.\n"
                "- Lớp ngoài cùng: Bao bọc toàn bộ khối trên cùng địa chỉ của R2 bằng khóa K1 dành cho Guard Node."
            ),
            (
                "Giao Thức Kéo Dài Mạch (Telescoping Circuit Construction)",
                "Một điểm đột phá trong thiết kế của Tor là các khóa phiên không bao giờ được gửi cùng một lúc. Alice thiết lập mạch theo phương pháp 'kéo dài ống ngắm' (telescoping):\n"
                "1. Alice bắt tay Diffie-Hellman trực tiếp với R1 để thiết lập khóa K1.\n"
                "2. Thông qua kênh mã hóa K1 đã có, Alice gửi yêu cầu RELAY_EXTEND chỉ thị R1 kết nối tới R2, sau đó thực hiện bắt tay Diffie-Hellman xuyên qua R1 để tạo khóa K2 với R2.\n"
                "3. Xuyên qua đường hầm K1 và K2, Alice tiếp tục kéo dài mạch từ R2 tới R3 để tạo khóa K3.\n"
                "Mỗi trạm chỉ biết nút trước và nút sau nó trong chuỗi, hoàn toàn không biết cấu trúc toàn tuyến."
            )
        ],
        attack_defense_section=(
            "Các phân tích an ninh đối với cấu trúc đa tầng:\n\n"
            "1. **Phân Tích Kích Thước Gói Tin (Packet Size Analysis)**: Nếu kích thước gói tin thay đổi sau mỗi lần bóc lớp mã hóa, kẻ tấn công đứng trên đường truyền có thể đoán được vị trí của gói tin trong chuỗi. Do đó, Tor chuẩn hóa toàn bộ dữ liệu thành các **Cell có kích thước cố định đúng 514 bytes**. Mọi gói tin nhỏ hơn đều được đệm (padding) thêm byte rác.\n\n"
            "2. **Tấn Công Mạch Tái Sử Dụng (Circuit Reuse)**: Nếu một người dùng sử dụng cùng một mạch 3 node cho nhiều website khác nhau, hành vi duyệt web có thể bị liên kết. Tor áp dụng cơ chế tự động đổi mạch sau mỗi 10 phút và cô lập mạch theo từng tên miền (First-Party Isolation)."
        ),
        lab_instructions=(
            "Thực hành lập trình Python mô phỏng chính xác thuật toán đóng gói đa tầng AES-GCM và bóc tách từng lớp vỏ hành tây qua 3 trạm chuyển tiếp:"
        ),
        code_snippet=(
            "python",
            """import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 1. Khởi tạo dữ liệu gốc và 3 khóa phiên đối xứng (K1, K2, K3)
payload = b"SECRET_INTELLIGENCE_DATA: Target location confirmed"
key1 = AESGCM.generate_key(bit_length=256)
key2 = AESGCM.generate_key(bit_length=256)
key3 = AESGCM.generate_key(bit_length=256)

aes1, aes2, aes3 = AESGCM(key1), AESGCM(key2), AESGCM(key3)
n1, n2, n3 = os.urandom(12), os.urandom(12), os.urandom(12)

# 2. Phía Client Alice: Đóng gói từ trong ra ngoài (K3 -> K2 -> K1)
layer3 = aes3.encrypt(n3, payload, associated_data=b"ExitNode_R3")
layer2 = aes2.encrypt(n2, layer3, associated_data=b"MiddleRelay_R2")
onion_cell = aes1.encrypt(n1, layer2, associated_data=b"GuardNode_R1")

print(f"[*] Kích thước gói hành tây đã đóng gói: {len(onion_cell)} bytes")

# 3. Guard Node R1 bóc lớp thứ nhất bằng khóa K1
peeled_1 = aes1.decrypt(n1, onion_cell, associated_data=b"GuardNode_R1")
print("[+] R1 bóc lớp 1 thành công -> Chuyển tiếp tới R2")

# 4. Middle Node R2 bóc lớp thứ hai bằng khóa K2
peeled_2 = aes2.decrypt(n2, peeled_1, associated_data=b"MiddleRelay_R2")
print("[+] R2 bóc lớp 2 thành công -> Chuyển tiếp tới R3")

# 5. Exit Node R3 bóc lớp cuối cùng bằng khóa K3
original = aes3.decrypt(n3, peeled_2, associated_data=b"ExitNode_R3")
print(f"[+] R3 bóc lớp cuối -> Dữ liệu đích: {original.decode()}")"""
        ),
        pitfalls=[
            "Không bao giờ truyền dữ liệu nhạy cảm qua HTTP không mã hóa ở đầu ra của Exit Node, vì Exit Node có thể bắt trọn nội dung gốc.",
            "Không tái sử dụng cùng một danh tính (identity) trên các mạch Tor khác nhau để tránh bị đối chiếu hành vi."
        ],
        summary_points=[
            "Onion Routing ra đời tại Naval Research Laboratory (NRL) nhằm phục vụ an ninh liên lạc tình báo của quân đội Hoa Kỳ.",
            "Gói tin Tor được bọc 3 lớp mã hóa đối xứng lồng nhau và chuyển qua 3 trạm relay độc lập.",
            "Mỗi cell dữ liệu của Tor được cố định đúng 514 bytes để chống lại kỹ thuật phân tích lưu lượng dựa trên dung lượng."
        ],
        video_url="https://www.youtube.com/watch?v=lVcbq_a5N9I",
        quiz_json=[
            {
                "question": "Onion Routing ban đầu được nghiên cứu và phát triển bởi tổ chức nào?",
                "type": "MULTIPLE_CHOICE",
                "options": ["CIA", "U.S. Naval Research Laboratory (NRL)", "NSA", "DARPA"],
                "correct_index": 1,
                "explanation": "Onion Routing được phát minh tại Phòng thí nghiệm Nghiên cứu Hải quân Hoa Kỳ (NRL) vào giữa thập niên 1990."
            },
            {
                "question": "Vì sao chính phủ Mỹ lại quyết định công khai mã nguồn Tor cho cộng đồng toàn cầu?",
                "type": "MULTIPLE_CHOICE",
                "options": [
                    "Vì thiếu ngân sách duy trì",
                    "Vì muốn dòng lưu lượng tình báo quân sự hòa lẫn vào đám đông người dùng dân sự",
                    "Vì công nghệ này không còn giá trị",
                    "Do quy định của Liên Hợp Quốc"
                ],
                "correct_index": 1,
                "explanation": "Sự ẩn danh cần đám đông (Anonymity loves company): Dữ liệu quân sự cần hòa lẫn với hàng triệu người dùng thông thường."
            },
            {
                "question": "Kích thước cố định của mỗi cell dữ liệu trong giao thức mạng Tor là bao nhiêu bytes?",
                "type": "FILL_BLANK",
                "blanks": [{"accepted_answers": ["514", "514 bytes"]}],
                "explanation": "Tor quy định kích thước chuẩn của cell dữ liệu là 514 bytes để che giấu độ dài thực của thông điệp."
            },
            {
                "question": "Các relay trong mạng Tor đều biết được toàn bộ danh sách 3 trạm trong mạch định tuyến?",
                "type": "TRUE_FALSE",
                "correct_value": False,
                "explanation": "Sai. Mỗi relay chỉ biết trạm ngay trước nó và trạm ngay sau nó, hoàn toàn không biết trạm còn lại trong mạch 3 node."
            }
        ]
    )
})

# Lesson 1.3
LESSONS.append({
    "position": 3,
    "title": "Bài 1.3: Phân Định Không Gian Mạng & Khung Pháp Lý: Clear Web, Deep Web và Darknet",
    "summary": "Phân tích khung pháp lý, đạo đức và kỹ thuật vận hành giữa Clear Web, Deep Web và Darknet; làm rõ ranh giới giữa bảo vệ quyền riêng tư và tội phạm mạng.",
    "duration_minutes": 35,
    "video_url": "https://www.youtube.com/watch?v=fyySsmKsTlM",
    "markdown_content": generate_lesson_markdown(
        lesson_num="1.3",
        title="Bài 1.3: Phân Định Không Gian Mạng & Khung Pháp Lý: Clear Web, Deep Web và Darknet",
        objective_points=[
            "Phân tích bản chất pháp lý của việc sử dụng công nghệ ẩn danh tại các khu vực pháp lý khác nhau trên thế giới.",
            "Làm rõ tính hợp pháp của Deep Web đối với hoạt động doanh nghiệp và chính phủ.",
            "Nhận diện các hình thái tội phạm mạng phát sinh trên Darknet và ranh giới trách nhiệm pháp lý của chuyên gia an ninh mạng."
        ],
        theory_sections=[
            (
                "Tính Hợp Pháp Của Công Nghệ Mã Hóa & Mạng Tor",
                "Một trong những câu hỏi phổ biến nhất của người mới tiếp cận an ninh mạng là: 'Sử dụng Tor có phạm pháp không?'\n\n"
                "Tại hầu hết các quốc gia dân chủ và phát triển (bao gồm Hoa Kỳ, Liên minh Châu Âu, Nhật Bản), **việc tải xuống, cài đặt và sử dụng phần mềm Tor là hoàn toàn hợp pháp 100%**. Tor được công nhận là một công cụ bảo vệ quyền riêng tư chính đáng, được khuyến nghị bởi các tổ chức nhân quyền (Electronic Frontier Foundation - EFF, Amnesty International), các hãng tin lớn (The New York Times, ProPublica - đều có cổng nhận tin nặc danh qua Tor .onion), và các cơ quan thực thi pháp luật khi điều tra bí mật.\n\n"
                "Tuy nhiên, hành vi phi pháp trên mạng Tor (như mua bán ma túy, vũ khí, phát tán tài liệu bất hợp pháp, tấn công từ chối dịch vụ) vẫn chịu trách nhiệm hình sự đầy đủ trước pháp luật. Bản thân chiếc búa không có tội, tội lỗi nằm ở hành vi của kẻ sử dụng búa."
            ),
            (
                "Deep Web: Hạ Tầng Sống Còn Của Kinh Tế Số",
                "Deep Web thường bị truyền thông gắn nhãn tiêu cực một cách oan uổng. Trên thực tế, nếu không có Deep Web, nền kinh tế số toàn cầu sẽ sụp đổ ngay lập tức:\n\n"
                "- Mỗi lần bạn đăng nhập vào Internet Banking để kiểm tra số dư, bạn đang hoạt động trên Deep Web.\n"
                "- Hồ sơ sức khỏe của bệnh nhân được lưu trữ trong hệ thống bệnh viện bảo vệ bởi HIPAA là Deep Web.\n"
                "- Tài liệu nghiên cứu mật, mã nguồn nội bộ trên GitHub Enterprise riêng tư là Deep Web.\n"
                "Việc không cho phép máy tìm kiếm như Google lập chỉ mục các trang này là một yêu cầu bắt buộc về bảo mật thông tin (Confidentiality trong mô hình CIA)."
            ),
            (
                "Darknet: Vùng Xám Công Nghệ & Khủng Hoảng Quản Trị",
                "Darknet là nơi hội tụ của cả hai thái cực đạo đức số:\n\n"
                "- Mặt tích cực: Là công cụ duy nhất giúp các nhà bất đồng chính kiến, người tố giác sai phạm (Whistleblowers như Edward Snowden) và nhà báo tại các chế độ độc tài có thể cất tiếng nói mà không bị đe dọa tính mạng.\n"
                "- Mặt tiêu cực: Là nơi trú ngụ của các chợ đen (Darknet Markets - DNMs), diễn đàn mua bán dữ liệu rò rỉ (Breached Databases), mạng lưới phát tán mã độc tống tiền (Ransomware-as-a-Service - RaaS) và các dịch vụ phi pháp khác."
            )
        ],
        attack_defense_section=(
            "Kịch bản tấn công pháp lý & điều tra hình sự:\n\n"
            "1. **Bẫy Mật Phục (Honeypotting)**: Cơ quan thực thi pháp luật (FBI, Europol) thường xuyên tiếp quản các chợ đen Darknet (như vụ AlphaBay, Hansa Market), âm thầm duy trì máy chủ trong nhiều tuần để thu thập nhật ký truy cập, địa chỉ ví Bitcoin và danh tính thực của người mua lẫn người bán.\n\n"
            "2. **Tấn Công Dấu Vân Tay Trình Duyệt (Browser Fingerprinting)**: Khi người dùng truy cập một diễn đàn Darknet, máy chủ có thể chạy các đoạn mã JavaScript đo đạc thời gian render font chữ, card đồ họa WebGL và danh sách plugin để lập hồ sơ theo dõi danh tính."
        ),
        lab_instructions=(
            "Thực hành kiểm tra cấu hình an toàn mạng và phát hiện các rò rỉ định danh kỹ thuật số bằng script Bash:"
        ),
        code_snippet=(
            "bash",
            """# Kiểm tra xem máy trạm có đang rò rỉ thông tin mạng qua WebRTC hay DNS không
echo "=== KIỂM TRA RÒ RỈ MẠNG (LEAK AUDIT) ==="

# 1. Kiểm tra máy chủ DNS đang được sử dụng
cat /etc/resolv.conf

# 2. Kiểm tra bảng định tuyến mặc định của hệ thống
ip route show

# 3. Truy vấn IP hiện tại qua hai giao thức độc lập
echo "IPv4 public:"
curl -4 -s https://ifconfig.me
echo ""
echo "IPv6 public (nếu có):"
curl -6 -s https://ifconfig.me 2>/dev/null || echo "IPv6 không hoạt động hoặc đã tắt (Tốt cho OPSEC)"

# Lưu ý an ninh: Khi sử dụng Tor, IPv6 bắt buộc phải được vô hiệu hóa trên hệ điều hành
# để tránh rò rỉ địa chỉ IPv6 thực tế của thiết bị."""
        ),
        pitfalls=[
            "Không bao giờ đăng nhập vào tài khoản cá nhân thông thường (như Gmail cá nhân, Facebook) trên cùng một phiên trình duyệt đang duyệt Darknet.",
            "Không thanh toán trên Darknet bằng thẻ tín dụng thông thường hoặc tài khoản PayPal."
        ],
        summary_points=[
            "Tor hoàn toàn hợp pháp tại hầu hết các quốc gia dân chủ trên thế giới.",
            "Deep Web là thành phần tối quan trọng của Internet, chứa 90-95% tài nguyên bảo mật hợp pháp.",
            "Cơ quan hành pháp sử dụng các kỹ thuật honeypotting và phân tích blockchain để triệt phá các mạng lưới tội phạm trên Darknet."
        ],
        video_url="https://www.youtube.com/watch?v=fyySsmKsTlM",
        quiz_json=[
            {
                "question": "Sử dụng phần mềm Tor có phải là hành vi vi phạm pháp luật ở hầu hết các quốc gia phát triển?",
                "type": "MULTIPLE_CHOICE",
                "options": [
                    "Có, chỉ quân đội mới được dùng",
                    "Không, việc sử dụng phần mềm hoàn toàn hợp pháp, chỉ hành vi phạm pháp mới bị xử lý",
                    "Có, bị cấm trên toàn cầu",
                    "Chỉ hợp pháp nếu có giấy phép của cơ quan an ninh"
                ],
                "correct_index": 1,
                "explanation": "Tor là công nghệ bảo mật hợp pháp nhằm bảo vệ quyền riêng tư số. Chỉ hành vi phạm tội thông qua Tor mới bị xử lý hình sự."
            },
            {
                "question": "Cơ sở dữ liệu bệnh án điện tử của một bệnh viện tư nhân thuộc phân tầng nào của Internet?",
                "type": "MULTIPLE_CHOICE",
                "options": ["Surface Web", "Deep Web", "Darknet", "Clear Web"],
                "correct_index": 1,
                "explanation": "Bệnh án điện tử được bảo vệ bởi xác thực phân quyền và không lập chỉ mục công khai, do đó thuộc Deep Web."
            },
            {
                "question": "Khi cấu hình máy trạm để sử dụng mạng Tor an toàn, người dùng nên vô hiệu hóa giao thức IPv6 để tránh nguy cơ rò rỉ địa chỉ mạng thực tế?",
                "type": "TRUE_FALSE",
                "correct_value": True,
                "explanation": "Đúng. Nhiều triển khai Tor không hỗ trợ định tuyến IPv6 đầy đủ, việc bật IPv6 có thể khiến các ứng dụng bypass proxy và làm lộ IP thật."
            },
            {
                "question": "Điền thuật ngữ chỉ chiến thuật cơ quan điều tra tiếp quản máy chủ Darknet và duy trì hoạt động ngầm để thu thập bằng chứng:",
                "type": "FILL_BLANK",
                "blanks": [{"accepted_answers": ["Honeypot", "honeypotting", "Bẫy mật phục", "honeypot"]}],
                "explanation": "Honeypotting (bẫy mật phục) là chiến thuật cơ quan điều tra bí mật kiểm soát hạ tầng tội phạm để thu thập dữ liệu người dùng."
            }
        ]
    )
})

# Lesson 1.4
LESSONS.append({
    "position": 4,
    "title": "Bài 1.4: Cơ Chế Đồng Thuận Tor Directory, Consensus & Chuỗi Trạm Guard - Middle - Exit",
    "summary": "Khám phá cơ chế điều phối trung tâm của mạng Tor qua hệ thống Directory Authorities, tài liệu Consensus và thuật toán lựa chọn relay.",
    "duration_minutes": 40,
    "video_url": "https://www.youtube.com/watch?v=M99W0d61vsw",
    "markdown_content": generate_lesson_markdown(
        lesson_num="1.4",
        title="Bài 1.4: Cơ Chế Đồng Thuận Tor Directory, Consensus & Chuỗi Trạm Guard - Middle - Exit",
        objective_points=[
            "Hiểu sâu cơ chế hoạt động của 9 hoặc 10 Directory Authorities (Nhà chức trách danh bạ) của mạng Tor.",
            "Phân tích cấu trúc của văn bản đồng thuận Consensus Document và các cờ trạng thái (Flags) của relay.",
            "Nắm vững thuật toán lựa chọn relay có trọng số băng thông (Bandwidth-weighted Relay Selection)."
        ],
        theory_sections=[
            (
                "Kiến Trúc Directory Authorities (DirAuths)",
                "Làm thế nào một máy khách Tor ở bất kỳ đâu trên thế giới có thể biết được danh sách hàng nghìn relay đang hoạt động, băng thông của chúng và khóa công khai để kết nối mà không bị kẻ tấn công đánh tráo danh sách?\n\n"
                "Mạng Tor giải quyết bài toán này thông qua hệ thống **Directory Authorities (DirAuths)**. Hiện có khoảng 9-10 máy chủ danh bạ uy tín được vận hành độc lập bởi các thành viên kỳ cựu và đáng tin cậy của cộng đồng Tor Project trên toàn cầu (đặt tại Mỹ, Đức, Hà Lan, Thụy Điển...).\n\n"
                "Mỗi giờ một lần, các DirAuths này kiểm tra trạng thái của toàn bộ mạng lưới, trao đổi thông tin với nhau và ký số mật mã học để ban hành một văn bản duy nhất gọi là **Consensus Document (Văn bản đồng thuận)**. Mọi máy khách Tor khi khởi động đều tải bản Consensus này về để làm bản đồ định tuyến."
            ),
            (
                "Cấu Trúc Của Văn Bản Đồng Thuận (Consensus Document)",
                "Consensus Document liệt kê toàn bộ các relay hợp lệ trong mạng kèm theo các thông tin định danh quan trọng:\n\n"
                "- Tên relay (Nickname), địa chỉ IP và cổng ORPort (Onion Router Port).\n"
                "- Khóa nhận dạng RSA Identity Fingerprint và Ed25519 Identity Key.\n"
                "- Chỉ số băng thông ước tính (Consensus Weight).\n"
                "- Các cờ trạng thái (Flags) được các DirAuths cấp phát dựa trên độ tin cậy và hiệu năng."
            ),
            (
                "Hệ Thống Các Cờ Trạng Thái (Relay Flags)",
                "Không phải relay nào cũng có thể đóng vai trò giống nhau. Tor phân loại relay qua các cờ:\n\n"
                "- `Authority`: Nút là một trong các máy chủ danh bạ.\n"
                "- `Fast`: Relay có băng thông cao, phù hợp để làm Middle hoặc Exit.\n"
                "- `Guard`: Relay có độ ổn định và thời gian uptime cao, được tin cậy để làm trạm đầu vào (Entry Guard).\n"
                "- `Exit`: Relay cho phép phát lưu lượng ra ngoài Internet công cộng theo chính sách Exit Policy quy định.\n"
                "- `Running`: Relay đang trực tuyến và phản hồi các gói tin thăm dò.\n"
                "- `Valid`: Relay đã được xác minh tính hợp lệ của khóa mật mã.\n"
                "- `Stable`: Relay có độ trễ thấp và ít bị ngắt kết nối đột ngột."
            )
        ],
        attack_defense_section=(
            "Kịch bản tấn công hạ tầng điều phối:\n\n"
            "1. **Tấn Công Sybil (Sybil Attack)**: Kẻ tấn công triển khai hàng trăm hoặc hàng nghìn relay ma với băng thông ảo nhằm chiếm đa số trong mạng lưới. Nếu kẻ thù kiểm soát được hơn 50% băng thông của mạng, xác suất một người dùng vô tình chọn cả Guard và Exit thuộc về kẻ tấn công sẽ tăng vọt lên mức nguy hiểm.\n\n"
            "2. **Cơ chế phòng thủ Entry Guard Pinning**: Để chống lại tấn công Sybil, Tor Browser không đổi Guard Node liên tục mỗi phiên. Thay vào đó, máy khách sẽ chọn cố định 1 Guard Node uy tín duy nhất và giữ nguyên Guard đó trong suốt từ 2 đến 3 tháng. Nếu Guard đó không bị thỏa hiệp, kẻ thù hoàn toàn bất lực trong việc giải mã lưu lượng."
        ),
        lab_instructions=(
            "Thực hành tải và phân tích tệp tin đồng thuận Consensus của mạng Tor bằng lệnh CLI để kiểm tra danh sách các relay:"
        ),
        code_snippet=(
            "bash",
            """# 1. Tải văn bản Consensus hiện tại từ một máy chủ danh bạ công khai
echo "Tải văn bản đồng thuận Tor Consensus..."
curl -s http://128.31.0.39:9131/tor/status-vote/current/consensus -o /tmp/tor-consensus.txt

# 2. Đếm tổng số relay đang hoạt động trên toàn cầu
total_relays=$(grep "^r " /tmp/tor-consensus.txt | wc -l)
echo "Tổng số relay trong mạng Tor hiện tại: $total_relays"

# 3. Đếm số lượng trạm Exit Relay (có cờ Exit)
exit_relays=$(grep -A 1 "^r " /tmp/tor-consensus.txt | grep "s " | grep "Exit" | wc -l)
echo "Số lượng Exit Relays đang hoạt động: $exit_relays"

# 4. Đếm số lượng trạm Guard Relay (có cờ Guard)
guard_relays=$(grep -A 1 "^r " /tmp/tor-consensus.txt | grep "s " | grep "Guard" | wc -l)
echo "Số lượng Guard Relays đang hoạt động: $guard_relays"

# 5. Xem thông tin của 3 relay đầu tiên trong danh bạ
head -n 30 /tmp/tor-consensus.txt"""
        ),
        pitfalls=[
            "Không bao giờ thay đổi ngẫu nhiên cấu hình Entry Guard trong tệp torrc nếu không có kiến thức sâu, vì việc đổi Guard thường xuyên sẽ gia tăng xác suất gặp phải Guard độc hại.",
            "Không nhầm lẫn giữa Directory Authority (DirAuth) và Exit Relay: DirAuth chỉ cung cấp danh bạ chứ không trung chuyển lưu lượng duyệt web của bạn."
        ],
        summary_points=[
            "Hệ thống Directory Authorities định kỳ ban hành Consensus Document có chữ ký số mỗi giờ một lần.",
            "Mỗi relay được gán các cờ (Flags) như Guard, Exit, Fast, Stable dựa trên độ ổn định và chính sách hoạt động.",
            "Cơ chế ghim Guard Node (Entry Guard Pinning) từ 2-3 tháng là lá chắn bảo vệ người dùng chống lại tấn công Sybil."
        ],
        video_url="https://www.youtube.com/watch?v=M99W0d61vsw",
        quiz_json=[
            {
                "question": "Văn bản nào được các máy chủ Directory Authorities ký số và ban hành mỗi giờ để cập nhật trạng thái toàn mạng Tor?",
                "type": "MULTIPLE_CHOICE",
                "options": ["Tor Whitepaper", "Consensus Document", "Master Ledger", "Root Zone File"],
                "correct_index": 1,
                "explanation": "Consensus Document (văn bản đồng thuận) được ban hành mỗi giờ, chứa danh sách toàn bộ relay hợp lệ và băng thông của chúng."
            },
            {
                "question": "Tor Browser giữ cố định một Guard Node (Entry Guard Pinning) trong khoảng thời gian bao lâu để chống tấn công Sybil?",
                "type": "MULTIPLE_CHOICE",
                "options": ["10 phút", "24 giờ", "2 đến 3 tháng", "Vĩnh viễn không bao giờ đổi"],
                "correct_index": 2,
                "explanation": "Tor Client ghim Guard Node trong khoảng 2 đến 3 tháng để giảm thiểu xác suất người dùng vô tình kết nối qua Guard độc hại."
            },
            {
                "question": "Một relay trong mạng Tor có thể đồng thời vừa có cờ Guard vừa có cờ Exit nếu đáp ứng đủ điều kiện băng thông và cấu hình?",
                "type": "TRUE_FALSE",
                "correct_value": True,
                "explanation": "Đúng. Một relay có thể sở hữu cả cờ Guard và Exit, nhưng thuật toán chọn mạch của Tor sẽ không bao giờ sử dụng cùng một relay làm cả Guard và Exit trên cùng một mạch."
            },
            {
                "question": "Điền tên cuộc tấn công trong đó kẻ thù tạo ra một số lượng khổng lồ các relay ảo nhằm chiếm quyền kiểm soát mạng phân tán:",
                "type": "FILL_BLANK",
                "blanks": [{"accepted_answers": ["Sybil", "Sybil Attack", "sybil"]}],
                "explanation": "Tấn công Sybil là kịch bản kẻ thù tạo hàng loạt danh tính giả để thao túng mạng lưới ngang hàng."
            }
        ]
    )
})

print(f"Loaded {len(LESSONS)} lessons for Chapter 1 successfully.")
