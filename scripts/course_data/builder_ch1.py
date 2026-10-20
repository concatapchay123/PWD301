"""Builder for Chapter 1: Mạng Định Tuyến Hành Tây TOR & Cấu Trúc Không Gian Mạng Ngầm.
Generates all 12 lessons, validating >= 600 words for each.
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.build_cyber_payload import generate_lesson_markdown
from scripts.course_data.common import count_vietnamese_words, validate_lesson_data


def get_chapter_1_lessons() -> list[dict]:
    lessons = []

    # 1.1
    l1 = {
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
                    "Trong khoa học an toàn thông tin hiện đại, Internet không phải là một khối đồng nhất mà được phân tách thành 3 phân tầng rõ rệt: Surface Web chiếm khoảng 4-5% tổng tài nguyên web. Đây là những trang web công khai có thể được các công cụ tìm kiếm chuẩn (Google, Bing) thu thập dữ liệu (crawling) và lập chỉ mục (indexing). Chúng sử dụng hệ thống phân giải tên miền DNS chuẩn và truyền thông qua HTTP/HTTPS trực tiếp. Deep Web (Web Chìm / Tầng Sâu) chiếm từ 90% đến 95% không gian mạng. Bao gồm toàn bộ các dữ liệu trực tuyến không thể lập chỉ mục công khai: hệ thống cơ sở dữ liệu ngân hàng, cổng thông tin sinh viên, hồ sơ bệnh án điện tử, tài liệu lưu trữ đám mây riêng tư. Deep Web hoàn toàn hợp pháp và là nền tảng vận hành kinh tế số của nhân loại. Darknet / Dark Web (Mạng Tối) chiếm chưa đầy 1% Internet. Đây là một tập hợp con chuyên biệt của Deep Web được xây dựng trên các mạng phủ định tuyến ẩn danh như Tor, I2P, Freenet, yêu cầu cấu hình proxy và giao thức bảo mật riêng để truy cập."
                ),
                (
                    "Kiến Trúc Mạng Tor & Chuỗi Ba Trạm Chuyển Tiếp",
                    "Mạng Tor được vận hành dựa trên nguyên lý định tuyến củ hành với 3 trạm relay độc lập nhằm triệt tiêu khái niệm 'điểm tin cậy duy nhất': Guard Node (Trạm Đầu Vào) tiếp nhận kết nối trực tiếp từ địa chỉ IP thật của người dùng. Guard chỉ biết IP nguồn và địa chỉ của Middle Relay, hoàn toàn mù thông tin về máy chủ đích và nội dung gói tin. Middle Relay (Trạm Trung Gian) đóng vai trò lớp đệm cách ly tuyệt đối. Nó bóc lớp mã hóa giữa, nhận dữ liệu từ Guard và chuyển tiếp tới Exit. Trạm này không biết ai là người gửi ban đầu và không biết đích đến cuối cùng. Exit Node (Trạm Đầu Ra) bóc lớp mã hóa cuối cùng và phát gói tin ra Internet công cộng tới máy chủ đích. Exit Node thấy được đích đến nhưng hoàn toàn không biết IP gốc của người dùng."
                ),
                (
                    "Cơ Chế Khóa Phiên Đối Xứng & Giao Thức Trao Đổi Khóa",
                    "Tor không sử dụng một cặp khóa duy nhất cho toàn bộ hành trình. Thay vào đó, máy khách của người dùng thực hiện giao thức bắt tay trao đổi khóa Diffie-Hellman trên đường cong elliptic (Curve25519) tuần tự với từng trạm relay theo cơ chế Telescoping Circuit Construction. Kết quả là máy khách nắm giữ ba khóa phiên đối xứng AES-GCM (hoặc Chacha20-Poly1305) riêng biệt: K1 (với Guard), K2 (với Middle) và K3 (với Exit). Mỗi trạm chỉ có thể giải mã duy nhất lớp vỏ do khóa của chính mình bảo vệ, đảm bảo tính toàn vẹn và bảo mật chuyển tiếp hoàn hảo (Forward Secrecy)."
                )
            ],
            attack_defense_section=(
                "Mặc dù Tor là một công nghệ xuất sắc, người dùng phải đối mặt với các kịch bản tấn công thực tế: Tấn Công Tương Quan Lưu Lượng (Traffic Correlation Attacks) khi kẻ thù cấp quốc gia (ví dụ NSA, GCHQ) có khả năng giám sát đồng thời cả luồng dữ liệu đi vào Guard Node và luồng dữ liệu rời khỏi Exit Node. Bằng cách áp dụng các thuật toán thống kê về kích thước gói tin và nhịp độ thời gian truyền (timing analysis), kẻ tấn công có thể liên kết hai đầu kết nối với độ tin cậy trên 90%. Nghe Lén Tại Exit Node (Exit Node Sniffing): Nếu người dùng truy cập các website HTTP không mã hóa qua mạng Tor, quản trị viên của Exit Node độc hại có thể bắt gói tin (sniff) toàn bộ thông tin đăng nhập, cookie phiên và dữ liệu nhạy cảm. Khai Thác Lỗ Hổng Ứng Dụng (Browser Exploits): Tin tặc sử dụng các lỗ hổng zero-day trong trình duyệt Tor Browser (dựa trên Firefox ESR) để thực thi mã từ xa, buộc hệ điều hành nạn nhân gửi gói tin DNS trực tiếp ra ngoài mạng Tor, làm lộ ngay lập tức địa chỉ IP thật của mục tiêu."
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
    }
    validate_lesson_data(l1)
    lessons.append(l1)

    # Helper function to generate standardized rich lessons for 1.2 to 1.12
    tor_lesson_configs = [
        (
            2,
            "Bài 1.2: Lịch Sử Hình Thành Hải Quân Hoa Kỳ & Nguyên Lý Onion Routing Đa Tầng",
            "Truy vết nguồn gốc quân sự của công nghệ Onion Routing tại Phòng thí nghiệm Nghiên cứu Hải quân Hoa Kỳ (NRL) và giải mã mô hình mật mã học đa tầng.",
            "https://www.youtube.com/watch?v=lVcbq_a5N9I",
            [
                "Khám phá bối cảnh lịch sử và nguồn gốc quân sự của công nghệ Onion Routing tại U.S. Naval Research Laboratory (NRL).",
                "Nắm vững quy trình mật mã học đa tầng (Onion Encryption) và cơ chế trao đổi khóa Diffie-Hellman đối xứng.",
                "Giải mã nghịch lý an ninh mạng: Vì sao một dự án bảo mật quân sự tối mật lại bắt buộc phải được mở mã nguồn cho công chúng."
            ],
            [
                (
                    "Nguồn Gốc Lịch Sử Quân Sự Của Onion Routing",
                    "Vào giữa thập niên 1990, các chuyên gia mật mã học Paul Syverson, Michael G. Reed và David Goldschlag tại Phòng thí nghiệm Nghiên cứu Hải quân Hoa Kỳ (NRL) được giao nhiệm vụ giải quyết bài toán: Làm thế nào để các điệp viên và sĩ quan hải quân Mỹ tại nước ngoài có thể trao đổi thông tin tình báo qua Internet mà không để lại dấu vết có thể truy ngược về nguồn gốc quân sự Mỹ? Nếu quân đội Mỹ xây dựng một mạng lưới mã hóa chuyên dụng đóng kín, đối phương chỉ cần theo dõi các điểm truy cập mạng là có thể xác định ngay lưu lượng nào xuất phát từ quân sự. Đây chính là nguyên lý then chốt của khoa học ẩn danh: Sự ẩn danh cần có một đám đông hỗn độn (Anonymity loves company). Quân đội Mỹ nhận ra rằng cách duy nhất để che giấu sĩ quan của mình là tạo ra một mạng lưới mã hóa công cộng mở, nơi công dân, nhà báo, doanh nghiệp trên toàn thế giới cùng sử dụng. Năm 2004, NRL quyết định phát hành mã nguồn Tor miễn phí dưới giấy phép nguồn mở."
                ),
                (
                    "Mô Hình Toán Học & Cấu Trúc Đóng Gói Củ Hành",
                    "Thuật ngữ 'Onion Routing' phản ánh trực quan cấu trúc gói tin: dữ liệu ban đầu được bao bọc bởi nhiều lớp mã hóa đối xứng tuần tự, tương tự như các lớp vỏ của một củ hành tây. Khi Alice muốn gửi dữ liệu M tới máy chủ đích Bob qua chuỗi 3 trạm R1 (Guard), R2 (Middle), R3 (Exit): Alice tạo 3 khóa phiên đối xứng duy nhất K1, K2, K3 bằng giao thức Curve25519. Sau đó, Alice đóng gói dữ liệu từ trong ra ngoài: Lớp trong cùng mã hóa dữ liệu M và địa chỉ của Bob bằng khóa K3 dành cho Exit Node. Lớp giữa bao bọc gói tin trên cùng địa chỉ của R3 bằng khóa K2 dành cho Middle Node. Lớp ngoài cùng bao bọc toàn bộ khối trên cùng địa chỉ của R2 bằng khóa K1 dành cho Guard Node."
                ),
                (
                    "Giao Thức Kéo Dài Mạch (Telescoping Circuit Construction)",
                    "Một điểm đột phá trong thiết kế của Tor là các khóa phiên không bao giờ được gửi cùng một lúc. Alice thiết lập mạch theo phương pháp kéo dài ống ngắm (telescoping): Alice bắt tay Diffie-Hellman trực tiếp với R1 để thiết lập khóa K1. Thông qua kênh mã hóa K1 đã có, Alice gửi yêu cầu RELAY_EXTEND chỉ thị R1 kết nối tới R2, sau đó thực hiện bắt tay Diffie-Hellman xuyên qua R1 để tạo khóa K2 với R2. Xuyên qua đường hầm K1 và K2, Alice tiếp tục kéo dài mạch từ R2 tới R3 để tạo khóa K3. Mỗi trạm chỉ biết nút trước và nút sau nó trong chuỗi, hoàn toàn không biết cấu trúc toàn tuyến."
                )
            ],
            "Các phân tích an ninh đối với cấu trúc đa tầng: Phân Tích Kích Thước Gói Tin (Packet Size Analysis): Nếu kích thước gói tin thay đổi sau mỗi lần bóc lớp mã hóa, kẻ tấn công đứng trên đường truyền có thể đoán được vị trí của gói tin trong chuỗi. Do đó, Tor chuẩn hóa toàn bộ dữ liệu thành các Cell có kích thước cố định đúng 514 bytes. Mọi gói tin nhỏ hơn đều được đệm (padding) thêm byte rác. Tấn Công Mạch Tái Sử Dụng (Circuit Reuse): Nếu một người dùng sử dụng cùng một mạch 3 node cho nhiều website khác nhau, hành vi duyệt web có thể bị liên kết. Tor áp dụng cơ chế tự động đổi mạch sau mỗi 10 phút và cô lập mạch theo từng tên miền (First-Party Isolation).",
            "Thực hành lập trình Python mô phỏng chính xác thuật toán đóng gói đa tầng AES-GCM và bóc tách từng lớp vỏ hành tây qua 3 trạm chuyển tiếp:",
            ("python", "import os\nfrom cryptography.hazmat.primitives.ciphers.aead import AESGCM\n\npayload = b'SECRET: Target location confirmed'\nk1, k2, k3 = AESGCM.generate_key(256), AESGCM.generate_key(256), AESGCM.generate_key(256)\na1, a2, a3 = AESGCM(k1), AESGCM(k2), AESGCM(k3)\nn1, n2, n3 = os.urandom(12), os.urandom(12), os.urandom(12)\n\nl3 = a3.encrypt(n3, payload, b'Exit')\nl2 = a2.encrypt(n2, l3, b'Middle')\nonion = a1.encrypt(n1, l2, b'Guard')\nprint(f'Encrypted onion cell: {len(onion)} bytes')\n\np1 = a1.decrypt(n1, onion, b'Guard')\np2 = a2.decrypt(n2, p1, b'Middle')\nres = a3.decrypt(n3, p2, b'Exit')\nprint(f'Decrypted: {res.decode()}')"),
            ["Không bao giờ gửi thông tin mật qua HTTP thường ở đầu ra của Exit Node.", "Không sử dụng chung một danh tính trên nhiều mạch định tuyến khác nhau."],
            ["Onion Routing ra đời tại Naval Research Laboratory (NRL) phục vụ an ninh tình báo.", "Mỗi cell dữ liệu của Tor được cố định đúng 514 bytes.", "Chuỗi 3 trạm relay sử dụng 3 khóa phiên đối xứng độc lập."],
            [
                {"question": "Onion Routing ban đầu được nghiên cứu bởi cơ quan nào?", "type": "MULTIPLE_CHOICE", "options": ["CIA", "NRL", "NSA", "DARPA"], "correct_index": 1, "explanation": "Phát triển tại U.S. Naval Research Laboratory (NRL) giữa thập niên 1990."},
                {"question": "Kích thước cố định của mỗi cell dữ liệu trong giao thức Tor là bao nhiêu bytes?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["514", "514 bytes"]}], "explanation": "Kích thước chuẩn là 514 bytes."},
                {"question": "Mỗi relay trong chuỗi đều nắm được địa chỉ của cả 3 node?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Mỗi relay chỉ biết node trước và node sau nó."}
            ]
        ),
        (
            3,
            "Bài 1.3: Phân Định Không Gian Mạng & Khung Pháp Lý: Clear Web, Deep Web và Darknet",
            "Phân tích khung pháp lý, đạo đức và kỹ thuật vận hành giữa Clear Web, Deep Web và Darknet; làm rõ ranh giới giữa bảo vệ quyền riêng tư và tội phạm mạng.",
            "https://www.youtube.com/watch?v=fyySsmKsTlM",
            [
                "Phân tích bản chất pháp lý của việc sử dụng công nghệ ẩn danh tại các khu vực pháp lý khác nhau trên thế giới.",
                "Làm rõ tính hợp pháp của Deep Web đối với hoạt động doanh nghiệp và chính phủ.",
                "Nhận diện các hình thái tội phạm mạng phát sinh trên Darknet và ranh giới trách nhiệm pháp lý của chuyên gia an ninh mạng."
            ],
            [
                (
                    "Tính Hợp Pháp Của Công Nghệ Mã Hóa & Mạng Tor",
                    "Tại hầu hết các quốc gia dân chủ và phát triển (bao gồm Hoa Kỳ, Liên minh Châu Âu, Nhật Bản), việc tải xuống, cài đặt và sử dụng phần mềm Tor là hoàn toàn hợp pháp 100%. Tor được công nhận là một công cụ bảo vệ quyền riêng tư chính đáng, được khuyến nghị bởi các tổ chức nhân quyền (Electronic Frontier Foundation - EFF, Amnesty International), các hãng tin lớn (The New York Times, ProPublica - đều có cổng nhận tin nặc danh qua Tor .onion), và các cơ quan thực thi pháp luật khi điều tra bí mật. Tuy nhiên, hành vi phi pháp trên mạng Tor (như mua bán ma túy, vũ khí, phát tán tài liệu bất hợp pháp, tấn công từ chối dịch vụ) vẫn chịu trách nhiệm hình sự đầy đủ trước pháp luật. Bản thân chiếc búa không có tội, tội lỗi nằm ở hành vi của kẻ sử dụng búa."
                ),
                (
                    "Deep Web: Hạ Tầng Sống Còn Của Kinh Tế Số",
                    "Deep Web thường bị truyền thông gắn nhãn tiêu cực một cách oan uổng. Trên thực tế, nếu không có Deep Web, nền kinh tế số toàn cầu sẽ sụp đổ ngay lập tức: Mỗi lần bạn đăng nhập vào Internet Banking để kiểm tra số dư, bạn đang hoạt động trên Deep Web. Hồ sơ sức khỏe của bệnh nhân được lưu trữ trong hệ thống bệnh viện bảo vệ bởi HIPAA là Deep Web. Tài liệu nghiên cứu mật, mã nguồn nội bộ trên GitHub Enterprise riêng tư là Deep Web. Việc không cho phép máy tìm kiếm như Google lập chỉ mục các trang này là một yêu cầu bắt buộc về bảo mật thông tin (Confidentiality trong mô hình CIA)."
                ),
                (
                    "Darknet: Vùng Xám Công Nghệ & Khủng Hoảng Quản Trị",
                    "Darknet là nơi hội tụ của cả hai thái cực đạo đức số: Mặt tích cực: Là công cụ duy nhất giúp các nhà bất đồng chính kiến, người tố giác sai phạm (Whistleblowers như Edward Snowden) và nhà báo tại các chế độ độc tài có thể cất tiếng nói mà không bị đe dọa tính mạng. Mặt tiêu cực: Là nơi trú ngụ của các chợ đen (Darknet Markets - DNMs), diễn đàn mua bán dữ liệu rò rỉ (Breached Databases), mạng lưới phát tán mã độc tống tiền (Ransomware-as-a-Service - RaaS) và các dịch vụ phi pháp khác."
                )
            ],
            "Kịch bản tấn công pháp lý & điều tra hình sự: Bẫy Mật Phục (Honeypotting): Cơ quan thực thi pháp luật (FBI, Europol) thường xuyên tiếp quản các chợ đen Darknet (như vụ AlphaBay, Hansa Market), âm thầm duy trì máy chủ trong nhiều tuần để thu thập nhật ký truy cập, địa chỉ ví Bitcoin và danh tính thực của người mua lẫn người bán. Tấn Công Dấu Vân Tay Trình Duyệt (Browser Fingerprinting): Khi người dùng truy cập một diễn đàn Darknet, máy chủ có thể chạy các đoạn mã JavaScript đo đạc thời gian render font chữ, card đồ họa WebGL và danh sách plugin để lập hồ sơ theo dõi danh tính.",
            "Thực hành kiểm tra cấu hình an toàn mạng và phát hiện các rò rỉ định danh kỹ thuật số bằng script Bash:",
            ("bash", "echo 'Auditing Network Leaks'\ncat /etc/resolv.conf\nip route show\ncurl -4 -s https://ifconfig.me\ncurl -6 -s https://ifconfig.me 2>/dev/null || echo 'IPv6 disabled'"),
            ["Không bao giờ đăng nhập vào tài khoản cá nhân thông thường trên cùng một phiên trình duyệt đang duyệt Darknet.", "Không thanh toán trên Darknet bằng thẻ tín dụng thông thường hoặc tài khoản PayPal."],
            ["Tor hoàn toàn hợp pháp tại hầu hết các quốc gia dân chủ trên thế giới.", "Deep Web chứa 90-95% tài nguyên bảo mật hợp pháp.", "Cơ quan hành pháp sử dụng honeypotting để thu thập chứng cứ trên Darknet."],
            [
                {"question": "Sử dụng phần mềm Tor có bị coi là phạm pháp ở hầu hết các nước phát triển?", "type": "MULTIPLE_CHOICE", "options": ["Có", "Không, phần mềm hợp pháp, chỉ xử lý hành vi phạm tội", "Bị cấm hoàn toàn", "Chỉ quân sự được dùng"], "correct_index": 1, "explanation": "Bản thân phần mềm Tor hoàn toàn hợp pháp."},
                {"question": "Chiến thuật cơ quan điều tra bí mật tiếp quản máy chủ Darknet để thu thập chứng cứ gọi là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Honeypot", "honeypotting", "honeypot"]}], "explanation": "Honeypotting là kỹ thuật giăng bẫy điều tra."},
                {"question": "Khi sử dụng Tor an toàn, người dùng nên tắt IPv6 để tránh rò rỉ địa chỉ thực?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. IPv6 có thể bypass proxy và làm lộ IP thật."}
            ]
        ),
        (
            4,
            "Bài 1.4: Cơ Chế Đồng Thuận Tor Directory, Consensus & Chuỗi Trạm Guard - Middle - Exit",
            "Khám phá cơ chế điều phối trung tâm của mạng Tor qua hệ thống Directory Authorities, tài liệu Consensus và thuật toán lựa chọn relay.",
            "https://www.youtube.com/watch?v=M99W0d61vsw",
            [
                "Hiểu sâu cơ chế hoạt động của 9 hoặc 10 Directory Authorities (Nhà chức trách danh bạ) của mạng Tor.",
                "Phân tích cấu trúc của văn bản đồng thuận Consensus Document và các cờ trạng thái (Flags) của relay.",
                "Nắm vững thuật toán lựa chọn relay có trọng số băng thông (Bandwidth-weighted Relay Selection)."
            ],
            [
                (
                    "Kiến Trúc Directory Authorities (DirAuths)",
                    "Mạng Tor giải quyết bài toán khám phá nút mạng thông qua hệ thống Directory Authorities (DirAuths). Hiện có khoảng 9-10 máy chủ danh bạ uy tín được vận hành độc lập bởi các thành viên kỳ cựu và đáng tin cậy của cộng đồng Tor Project trên toàn cầu (đặt tại Mỹ, Đức, Hà Lan, Thụy Điển...). Mỗi giờ một lần, các DirAuths này kiểm tra trạng thái của toàn bộ mạng lưới, trao đổi thông tin với nhau và ký số mật mã học để ban hành một văn bản duy nhất gọi là Consensus Document (Văn bản đồng thuận). Mọi máy khách Tor khi khởi động đều tải bản Consensus này về để làm bản đồ định tuyến."
                ),
                (
                    "Cấu Trúc Của Văn Bản Đồng Thuận (Consensus Document)",
                    "Consensus Document liệt kê toàn bộ các relay hợp lệ trong mạng kèm theo các thông tin định danh quan trọng: Tên relay (Nickname), địa chỉ IP và cổng ORPort (Onion Router Port). Khóa nhận dạng RSA Identity Fingerprint và Ed25519 Identity Key. Chỉ số băng thông ước tính (Consensus Weight). Các cờ trạng thái (Flags) được các DirAuths cấp phát dựa trên độ tin cậy và hiệu năng."
                ),
                (
                    "Hệ Thống Các Cờ Trạng Thái (Relay Flags)",
                    "Không phải relay nào cũng có thể đóng vai trò giống nhau. Tor phân loại relay qua các cờ: Authority: Nút là một trong các máy chủ danh bạ. Fast: Relay có băng thông cao, phù hợp để làm Middle hoặc Exit. Guard: Relay có độ ổn định và thời gian uptime cao, được tin cậy để làm trạm đầu vào (Entry Guard). Exit: Relay cho phép phát lưu lượng ra ngoài Internet công cộng theo chính sách Exit Policy quy định. Running: Relay đang trực tuyến và phản hồi các gói tin thăm dò. Valid: Relay đã được xác minh tính hợp lệ của khóa mật mã. Stable: Relay có độ trễ thấp và ít bị ngắt kết nối đột ngột."
                )
            ],
            "Kịch bản tấn công hạ tầng điều phối: Tấn Công Sybil (Sybil Attack): Kẻ tấn công triển khai hàng trăm hoặc hàng nghìn relay ma với băng thông ảo nhằm chiếm đa số trong mạng lưới. Nếu kẻ thù kiểm soát được hơn 50% băng thông của mạng, xác suất một người dùng vô tình chọn cả Guard và Exit thuộc về kẻ tấn công sẽ tăng vọt lên mức nguy hiểm. Cơ chế phòng thủ Entry Guard Pinning: Để chống lại tấn công Sybil, Tor Browser không đổi Guard Node liên tục mỗi phiên. Thay vào đó, máy khách sẽ chọn cố định 1 Guard Node uy tín duy nhất và giữ nguyên Guard đó trong suốt từ 2 đến 3 tháng. Nếu Guard đó không bị thỏa hiệp, kẻ thù hoàn toàn bất lực trong việc giải mã lưu lượng.",
            "Thực hành tải và phân tích tệp tin đồng thuận Consensus của mạng Tor bằng lệnh CLI để kiểm tra danh sách các relay:",
            ("bash", "curl -s http://128.31.0.39:9131/tor/status-vote/current/consensus -o /tmp/consensus.txt\necho 'Total relays:' $(grep '^r ' /tmp/consensus.txt | wc -l)\necho 'Exit relays:' $(grep -A 1 '^r ' /tmp/consensus.txt | grep 's ' | grep 'Exit' | wc -l)"),
            ["Không thay đổi cấu hình Entry Guard tùy tiện trong torrc.", "Không nhầm lẫn giữa Directory Authority và Exit Relay."],
            ["Directory Authorities ban hành Consensus Document mỗi giờ một lần.", "Các cờ như Guard, Exit, Fast, Stable phân loại năng lực của từng relay.", "Entry Guard Pinning giữ cố định Guard 2-3 tháng để chống tấn công Sybil."],
            [
                {"question": "Văn bản nào được các Directory Authorities ký số ban hành mỗi giờ?", "type": "MULTIPLE_CHOICE", "options": ["Tor Whitepaper", "Consensus Document", "Master Ledger", "Root Zone"], "correct_index": 1, "explanation": "Consensus Document được ban hành hàng giờ."},
                {"question": "Tor Browser giữ cố định Entry Guard trong bao lâu để chống Sybil?", "type": "MULTIPLE_CHOICE", "options": ["10 phút", "24 giờ", "2 đến 3 tháng", "Vĩnh viễn"], "correct_index": 2, "explanation": "Entry Guard được ghim trong 2 đến 3 tháng."},
                {"question": "Tấn công tạo hàng loạt nút mạng ma để thao túng mạng phân tán gọi là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Sybil", "sybil", "Sybil Attack"]}], "explanation": "Tấn công Sybil."}
            ]
        ),
        (
            5,
            "Bài 1.5: Thiết Lập Môi Trường Duyệt Web Ẩn Danh Tor Browser Chuẩn An Ninh Tối Đa",
            "Hướng dẫn thực hành cấu hình chuyên sâu Tor Browser, thiết lập mức bảo mật Safest, vô hiệu hóa JavaScript và làm chủ cơ chế Letterboxing.",
            "https://www.youtube.com/watch?v=U2-JPqrALsA",
            [
                "Nắm vững các tầng bảo mật trong Tor Browser: Standard, Safer và Safest.",
                "Hiểu rõ mối đe dọa của JavaScript, WebGL, Canvas API đối với dấu vân tay trình duyệt.",
                "Thực hành cấu hình làm cứng (hardening) Tor Browser và quy tắc chống rò rỉ danh tính thực tế."
            ],
            [
                (
                    "Kiến Trúc Tor Browser & Các Cấp Độ Bảo Mật",
                    "Tor Browser không phải là một trình duyệt thông thường mà là một bản phân phối được làm cứng chuyên sâu từ Mozilla Firefox Extended Support Release (ESR). Toàn bộ mã nguồn mạng của trình duyệt đã được viết lại để ép buộc 100% lưu lượng TCP đi qua SOCKS5 proxy nội bộ (127.0.0.1:9150). Trình duyệt cung cấp 3 cấp độ an ninh: Standard (Tiêu chuẩn): Cho phép mọi tính năng web, JavaScript được bật. Mức này tiện lợi nhưng chứa nhiều rủi ro. Safer (An toàn hơn): Tắt JavaScript trên các trang web không hỗ trợ HTTPS, vô hiệu hóa tự động phát video/audio và một số font chữ phức tạp. Safest (An toàn nhất): Tắt hoàn toàn JavaScript trên tất cả các trang web theo mặc định, vô hiệu hóa WebGL, Canvas, và các icon font SVG. Đây là cấu hình bắt buộc khi truy cập các dịch vụ Darknet nhạy cảm."
                ),
                (
                    "Hiểm Họa Từ JavaScript & Browser Fingerprinting",
                    "JavaScript là vector tấn công số 1 trên Darknet. Khi JavaScript được thực thi, máy chủ web có thể thu thập hàng loạt thông số phần cứng: danh sách font chữ đã cài đặt, độ phân giải màn hình chính xác từng pixel, phiên bản driver card đồ họa qua WebGL, thông số pin (Battery API) và độ lệch thời gian CPU. Tập hợp các thông số này tạo ra một Browser Fingerprint độc nhất vô nhị, cho phép kẻ theo dõi nhận diện bạn trên nhiều phiên làm việc khác nhau dù bạn đã đổi IP qua Tor."
                ),
                (
                    "Cơ Chế Letterboxing Trong Tor Browser",
                    "Để ngăn chặn việc đo đạc kích thước cửa sổ trình duyệt nhằm suy ra độ phân giải màn hình thật, Tor Browser triển khai cơ chế Letterboxing. Khi người dùng thay đổi kích thước cửa sổ, trình duyệt không mở rộng trang web vừa khít theo pixel mà tự động chèn các khoảng viền xám xung quanh, làm tròn kích thước khung nhìn (viewport) thành bội số của 200x100 pixels. Nhờ đó, hàng triệu người dùng Tor trên thế giới đều có chung một kích thước viewport tiêu chuẩn."
                )
            ],
            "Kịch bản tấn công khai thác trình duyệt: Khai Thác Zero-Day Firefox (Firefox Zero-Days): Trong chiến dịch bắt giữ quản trị viên Freedom Hosting năm 2013, FBI đã sử dụng mã khai thác zero-day JavaScript nhắm vào lỗ hổng bộ nhớ trong Firefox. Khi nạn nhân tải trang, mã độc khai thác lỗ hổng để thoát khỏi sandbox trình duyệt, thực thi shellcode trực tiếp trên hệ điều hành Windows và gửi địa chỉ MAC cũng như IP thật về máy chủ của FBI.",
            "Thực hành kiểm tra chỉ số Fingerprint và tính ẩn danh của trình duyệt bằng công cụ kiểm thử bảo mật:",
            ("bash", "# Kiểm tra tính toàn vẹn chữ ký số PGP của bộ cài Tor Browser trước khi chạy\ngpg --auto-key-locate nodefault,wkd --locate-keys torbrowser@torproject.org\ngpg --verify tor-browser-linux64-*.tar.xz.asc tor-browser-linux64-*.tar.xz\n\n# Khởi chạy Tor Browser từ thư mục giải nén\n./Browser/start-tor-browser --detach"),
            ["Không bao giờ cài đặt thêm bất kỳ tiện ích mở rộng (add-on / extension) nào vào Tor Browser (kể cả uBlock hay AdBlock) vì các extension tạo ra fingerprint độc nhất.", "Không thay đổi kích thước cửa sổ hoặc phóng to toàn màn hình."],
            ["Mức bảo mật Safest vô hiệu hóa hoàn toàn JavaScript trên mọi trang web.", "Cơ chế Letterboxing chèn viền xám để chuẩn hóa kích thước khung nhìn viewport.", "Không cài thêm extension bên thứ ba vào Tor Browser."],
            [
                {"question": "Mức bảo mật nào trong Tor Browser vô hiệu hóa hoàn toàn JavaScript trên tất cả các trang web?", "type": "MULTIPLE_CHOICE", "options": ["Standard", "Safer", "Safest", "Custom"], "correct_index": 2, "explanation": "Mức Safest vô hiệu hóa JavaScript hoàn toàn."},
                {"question": "Cơ chế nào trong Tor Browser chèn viền xám để làm tròn kích thước cửa sổ về bội số chuẩn?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Letterboxing", "letterboxing"]}], "explanation": "Letterboxing chuẩn hóa kích thước viewport."},
                {"question": "Cài thêm tiện ích chặn quảng cáo vào Tor Browser sẽ làm tăng độ an toàn và ẩn danh của bạn?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Cài thêm extension tạo ra browser fingerprint độc nhất, khiến bạn dễ bị nhận diện."}
            ]
        ),
        (
            6,
            "Bài 1.6: Kiến Trúc Dịch Vụ Ẩn Danh Tor Hidden Services & Tên Miền .onion v3",
            "Giải mã cấu trúc kỹ thuật của Onion Services thế hệ mới (.onion v3), cơ chế Điểm Hẹn (Rendezvous Point) và mã hóa Ed25519 56 ký tự.",
            "https://www.youtube.com/watch?v=qfvrpHjqZVY",
            [
                "Nắm vững nguyên lý hoạt động của Tor Hidden Services không cần Exit Node.",
                "Giải mã cấu trúc tên miền .onion v3 dài 56 ký tự dựa trên mã hóa Ed25519.",
                "Hiểu rõ quy trình bắt tay 6 bước giữa Client và Onion Service thông qua Rendezvous Point."
            ],
            [
                (
                    "Khái Niệm Onion Services & Lợi Thế Kỹ Thuật",
                    "Phần lớn người dùng chỉ biết đến Tor như một công cụ duyệt web ẩn danh (Client Anonymity). Tuy nhiên, một tính năng mang tính cách mạng khác của Tor là Onion Services (Dịch vụ ẩn danh): cho phép một máy chủ web có thể xuất bản nội dung lên mạng Internet mà hoàn toàn không cần công khai địa chỉ IP của máy chủ (Server Anonymity). Điểm đặc biệt là trong kiến trúc Onion Service, lưu lượng dữ liệu đi hoàn toàn bên trong mạng Tor (Tor-to-Tor) từ máy khách đến máy chủ qua 6 trạm relay, hoàn toàn không cần đi qua bất kỳ Exit Node nào. Điều này loại bỏ 100% rủi ro bị nghe lén tại Exit Node."
                ),
                (
                    "Sự Tiến Hóa Từ .onion v2 Sang .onion v3",
                    "Thế hệ tên miền v2 cũ chỉ dài 16 ký tự, dựa trên hàm băm SHA-1 và khóa RSA-1024 bit đã lỗi thời, dễ bị tấn công va chạm hàm băm (hash collision) và bị lộ thông tin trên hệ thống HSDir (Hidden Service Directory). Năm 2017, Tor Project chính thức triển khai thế hệ .onion v3 với các nâng cấp vượt bậc: Tên miền v3 dài chính xác 56 ký tự (ví dụ: `duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion`). Tên miền v3 chính là chuỗi mã hóa Base32 của Khóa công khai Ed25519 (256-bit) cộng với checksum và phiên bản. Khóa bí mật máy chủ không bao giờ bị lộ ra ngoài, và hệ thống HSDir không thể đọc được nội dung danh mục dịch vụ ẩn danh."
                ),
                (
                    "Quy Trình Bắt Tay Rendezvous 6 Bước",
                    "Làm thế nào Client và Service kết nối được với nhau khi cả hai đều không biết địa chỉ IP của nhau? Quy trình gồm 6 bước chặt chẽ: Bước 1: Onion Service chọn một số relay làm Introduction Points (Điểm Giới Thiệu) và thiết lập mạch tới chúng. Bước 2: Onion Service công bố Bản mô tả dịch vụ (Service Descriptor) đã mã hóa lên hệ thống bảng băm phân tán HSDir. Bước 3: Client muốn kết nối sẽ tải Service Descriptor từ HSDir để lấy khóa công khai và danh sách Introduction Points. Bước 4: Client chọn một relay bất kỳ làm Rendezvous Point (Điểm Hẹn) và gửi một bí mật bắt tay (One-time Cookie). Bước 5: Client gửi thông điệp mã hóa qua một trong các Introduction Points để thông báo cho Onion Service biết Điểm Hẹn và Cookie. Bước 6: Onion Service thiết lập mạch tới Rendezvous Point, xác thực Cookie. Rendezvous Point nối hai đầu mạch lại với nhau, tạo thành một mạch bảo mật 6 chặng hoàn chỉnh."
                )
            ],
            "Kịch bản tấn công định vị máy chủ ẩn danh: Tấn Công Định Vị Đích (Deanonymization via Misconfiguration): Lỗi phổ biến nhất của các quản trị viên Darknet là để máy chủ web (Apache, Nginx) lộ địa chỉ IP thật qua các thông điệp lỗi (Error Pages), tiêu đề Server Header, chứng chỉ SSL tự ký có chứa hostname thực tế, hoặc chức năng gửi mail tự động (PHP mail) gửi IP gốc của máy chủ trong header email.",
            "Thực hành cấu hình một máy chủ web ẩn danh Tor Onion Service v3 trên Linux bằng tệp cấu hình torrc:",
            ("bash", """# Cấu hình Tor Hidden Service v3 trong tệp /etc/tor/torrc
sudo tee -a /etc/tor/torrc << 'EOF'
HiddenServiceDir /var/lib/tor/my_hidden_service/
HiddenServicePort 80 127.0.0.1:8080
HiddenServiceVersion 3
EOF

# Khởi động lại dịch vụ Tor để sinh cặp khóa Ed25519 và tên miền .onion v3
sudo systemctl restart tor

# Xem địa chỉ tên miền .onion v3 56 ký tự vừa được tạo
sudo cat /var/lib/tor/my_hidden_service/hostname"""),
            ["Bảo vệ tuyệt đối tệp hs_ed25519_secret_key trong thư mục HiddenServiceDir; nếu mất khóa này, tên miền .onion sẽ bị mất vĩnh viễn.", "Đảm bảo ứng dụng web chỉ lắng nghe trên 127.0.0.1 (localhost), không lắng nghe trên 0.0.0.0."],
            ["Onion Services cung cấp sự ẩn danh 2 đầu (cả Client lẫn Server) và không cần Exit Node.", "Tên miền .onion v3 dài 56 ký tự dựa trên chữ ký Ed25519 siêu an toàn.", "Kết nối được thiết lập an toàn thông qua Điểm Giới Thiệu (Introduction Points) và Điểm Hẹn (Rendezvous Point)."],
            [
                {"question": "Tên miền Tor Onion Service thế hệ v3 có độ dài chính xác là bao nhiêu ký tự?", "type": "MULTIPLE_CHOICE", "options": ["16 ký tự", "32 ký tự", "56 ký tự", "64 ký tự"], "correct_index": 2, "explanation": "Tên miền v3 dài chính xác 56 ký tự mã hóa Base32 của khóa Ed25519."},
                {"question": "Khi kết nối tới một Onion Service, lưu lượng có phải đi qua Exit Node ra Internet công cộng không?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Lưu lượng kết nối tới Onion Service lưu chuyển hoàn toàn nội bộ trong mạng Tor qua Rendezvous Point."},
                {"question": "Điền tên điểm relay trung gian do máy khách chỉ định để kết nối an toàn với máy chủ ẩn danh:", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Rendezvous Point", "Điểm hẹn", "rendezvous point"]}], "explanation": "Rendezvous Point là điểm hẹn trung gian nối hai mạch Client và Service."}
            ]
        ),
        (
            7,
            "Bài 1.7: Cơ Chế Quản Lý Mạch Circuit Isolation & Phòng Chống Rò Rỉ DNS/WebRTC",
            "Nghiên cứu cơ chế cô lập mạch định tuyến (First-Party Isolation), các kỹ thuật ngăn chặn rò rỉ WebRTC và bảo vệ quyền riêng tư người dùng.",
            "https://www.youtube.com/watch?v=tu-CbGRuS-E",
            [
                "Hiểu rõ cơ chế Circuit Isolation theo tên miền nguồn (SOCKS Username/Password Isolation).",
                "Phân tích nguyên nhân và nguy cơ làm lộ IP thật qua lỗ hổng WebRTC STUN/TURN requests.",
                "Thực hành kiểm tra và khóa chặt các kênh rò rỉ mạng trên hệ điều hành."
            ],
            [
                (
                    "Cơ Chế Cô Lập Mạch (Circuit Isolation)",
                    "Trong các phiên bản Tor đời đầu, nếu người dùng mở đồng thời tab website A và tab website B, cả hai tab này đều dùng chung một mạch 3 node (Guard -> Middle -> Exit). Điều này tạo ra rủi ro nghiêm trọng: Quản trị viên của website A và website B nếu thông đồng với nhau (hoặc cùng nhúng chung một mạng lưới quảng cáo của bên thứ ba như Google Analytics) có thể nhận thấy cùng một địa chỉ Exit IP và cùng một khoảng thời gian truy cập, từ đó liên kết hai danh tính lại với nhau. Để giải quyết triệt để, Tor Browser triển khai cơ chế First-Party Domain Isolation: mỗi tên miền cấp 1 (eTLD+1) được gán một mạch Tor hoàn toàn độc lập với Exit Node riêng biệt."
                ),
                (
                    "Hiểm Họa Rò Rỉ Địa Chỉ IP Thật Qua WebRTC",
                    "WebRTC (Web Real-Time Communication) là công nghệ cho phép trình duyệt truyền trực tiếp âm thanh, video và dữ liệu ngang hàng (P2P). Để thiết lập kết nối P2P qua các tường lửa NAT, WebRTC gửi các gói tin STUN (Session Traversal Utilities for NAT) chứa địa chỉ IP cục bộ (Local IP) và địa chỉ IP công cộng (Public IP) thật của thiết bị. Điểm nguy hiểm chết người là các gói tin STUN này hoạt động ở tầng UDP và thường bỏ qua hoàn toàn cấu hình proxy SOCKS5 của trình duyệt. Chỉ cần một đoạn mã JavaScript WebRTC đơn giản, kẻ tấn công có thể thu được IP thật của người dùng ngay cả khi họ đang bật Tor hoặc VPN!"
                ),
                (
                    "Phương Pháp Vô Hiệu Hóa WebRTC & DNS Hardening",
                    "Tor Browser đã vô hiệu hóa WebRTC ở cấp độ biên dịch mã nguồn (compile-time) và thiết lập cờ `media.peerconnection.enabled = false` trong `about:config`. Tuy nhiên, nếu bạn cấu hình một trình duyệt thông thường (như Chrome, Firefox thường) để đi qua Tor proxy, bạn bắt buộc phải kiểm tra và tắt WebRTC thủ công để tránh rò rỉ tai hại."
                )
            ],
            "Kịch bản tấn công khai thác rò rỉ WebRTC: Tấn Công Bóc Trần IP Qua Trang Web Độc Hại: Tin tặc chèn một đoạn mã JavaScript WebRTC ẩn trong một bài viết trên diễn đàn. Khi người dùng truy cập bằng trình duyệt chưa tắt WebRTC, mã script lập tức gửi một request STUN ra máy chủ của tin tặc. Máy chủ tin tặc ghi nhận địa chỉ IP nguồn thật của gói tin UDP, bóc trần hoàn toàn danh tính người dùng chỉ trong chưa đầy 100 mili-giây.",
            "Thực hành kiểm tra rò rỉ WebRTC bằng đoạn mã JavaScript kiểm thử chuẩn an ninh:",
            ("javascript", """// Đoạn mã kiểm tra xem WebRTC có đang để lộ địa chỉ IP thật hay không
const rtc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
rtc.createDataChannel("");
rtc.createOffer().then(offer => rtc.setLocalDescription(offer));
rtc.onicecandidate = (event) => {
    if (event && event.candidate && event.candidate.candidate) {
        console.warn("[CẢNH BÁO NGUY HIỂM] WebRTC candidate phát hiện:", event.candidate.candidate);
    } else {
        console.log("[AN TOÀN] Không phát hiện rò rỉ WebRTC candidate.");
    }
};"""),
            ["Không bao giờ sử dụng trình duyệt thông thường (Chrome, Edge) để duyệt Darknet vì WebRTC được bật mặc định.", "Đảm bảo tùy chọn media.peerconnection.enabled luôn là false."],
            ["Circuit Isolation phân tách mỗi tab tên miền thành một mạch định tuyến riêng biệt.", "WebRTC là lỗ hổng nguy hiểm nhất có thể làm lộ IP thật qua các gói tin STUN UDP.", "Tor Browser vô hiệu hóa WebRTC ở cấp độ cốt lõi."],
            [
                {"question": "Giao thức nào cho phép trình duyệt gửi gói tin STUN làm rò rỉ địa chỉ IP thật qua proxy?", "type": "MULTIPLE_CHOICE", "options": ["WebSockets", "WebRTC", "HTTP/2", "FTP"], "correct_index": 1, "explanation": "WebRTC gửi gói tin STUN qua UDP, bỏ qua SOCKS proxy."},
                {"question": "Cơ chế Circuit Isolation đảm bảo mỗi website khác nhau sẽ sử dụng một mạch Tor độc lập?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. First-Party Isolation phân tách mạch theo tên miền."},
                {"question": "Trong about:config của Firefox, giá trị của cờ media.peerconnection.enabled phải là gì để tắt WebRTC?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["false", "False"]}], "explanation": "Giá trị false tắt WebRTC."}
            ]
        ),
        (
            8,
            "Bài 1.8: So Sánh Chuyên Sâu Mạng Tor & I2P (Invisible Internet Project)",
            "Đối chiếu toàn diện kiến trúc kỹ thuật giữa mạng Tor (Onion Routing) và mạng I2P (Garlic Routing), phân tích ưu thế và nhược điểm của từng hệ thống.",
            "https://www.youtube.com/watch?v=llrhht8t4dA",
            [
                "Nắm vững nguyên lý Garlic Routing (Định tuyến nhánh tỏi) của mạng I2P.",
                "So sánh sự khác biệt cốt lõi giữa mô hình Outproxy của Tor và mô hình Internal Network của I2P.",
                "Đánh giá tính phù hợp của Tor và I2P đối với từng kịch bản bảo vệ an ninh tác chiến."
            ],
            [
                (
                    "Tổng Quan Mạng I2P (Invisible Internet Project)",
                    "Trong khi Tor là dự án mạng ẩn danh nổi tiếng nhất, I2P (Invisible Internet Project) là một mạng lưới đối trọng được thiết kế với triết lý hoàn toàn khác biệt. I2P được phát triển từ năm 2003, hoạt động như một mạng nội bộ hoàn toàn khép kín (Network-inside-the-Network). Trong khi mục đích chính của Tor là giúp người dùng truy cập Internet công cộng một cách ẩn danh (thông qua Exit Node), mục đích tối thượng của I2P là tạo ra một thế giới mạng nội bộ phi tập trung, an toàn, nơi các dịch vụ (Eepsites, I2P-Bote mail, torrent ẩn danh) hoạt động bên trong mà không cần kết nối ra ngoài Internet."
                ),
                (
                    "Garlic Routing (Định Tuyến Nhánh Tỏi) vs Onion Routing",
                    "Điểm khác biệt căn bản nhất về mật mã học nằm ở cơ chế đóng gói dữ liệu: Onion Routing của Tor: Đóng gói từng thông điệp đơn lẻ qua nhiều lớp mã hóa của 3 trạm relay theo một đường ống duy nhất hai chiều (Bi-directional circuit). Garlic Routing của I2P: Gom cụm nhiều thông điệp khác nhau (như các tép tỏi trong một củ tỏi) vào cùng một gói tin mã hóa. Hơn thế nữa, I2P sử dụng hai đường hầm một chiều riêng biệt (Unidirectional Tunnels): lưu lượng gửi đi (Outbound Tunnel) và lưu lượng nhận về (Inbound Tunnel) đi qua hai chuỗi relay hoàn toàn khác nhau. Điều này khiến cho các cuộc tấn công phân tích lưu lượng đối xứng trở nên khó khăn hơn gấp nhiều lần."
                ),
                (
                    "Mô Hình Phân Tán: Bảng Băm Kademlia DHT vs Directory Authorities",
                    "Mạng Tor phụ thuộc vào 9-10 máy chủ Directory Authorities tập trung để ban hành Consensus. Nếu các máy chủ này bị tấn công từ chối dịch vụ hoặc bị kiểm duyệt cấp quốc gia, mạng Tor có thể gặp trục trặc nghiêm trọng. Ngược lại, I2P hoạt động hoàn toàn phi tập trung thông qua bảng băm phân tán Kademlia DHT (gọi là NetDb). Mỗi máy khách I2P đều là một router tham gia duy trì cơ sở dữ liệu định tuyến toàn mạng, không có bất kỳ điểm tập trung nào."
                )
            ],
            "So sánh tính năng và ứng dụng thực tế: Tor vượt trội về tốc độ duyệt web thông thường và hỗ trợ truy cập các trang Surface Web qua Exit Node. I2P vượt trội về khả năng chia sẻ tệp ngang hàng (P2P / Torrent ẩn danh) và khả năng chống kiểm duyệt nội bộ cực kỳ bền bỉ.",
            "Thực hành cài đặt và khởi chạy I2P daemon trên Linux để kết nối mạng I2P song song với Tor:",
            ("bash", """# Cài đặt I2P router trên Ubuntu
sudo apt-add-repository ppa:i2p-maintainers/i2p -y
sudo apt update && sudo apt install -y i2p

# Khởi chạy dịch vụ I2P
i2prouter start

# Truy cập bảng điều khiển I2P Console tại cổng 7657
curl -s http://127.0.0.1:7657 | grep -i "I2P Router Console"
echo "I2P Console đang lắng nghe tại cổng nội bộ 7657." """),
            ["Không sử dụng I2P để duyệt web thông thường vì số lượng Outproxy của I2P rất ít và tốc độ chậm.", "Không để lộ các cổng điều khiển nội bộ 7657 ra mạng bên ngoài."],
            ["Tor sử dụng Onion Routing với 1 mạch 2 chiều; I2P sử dụng Garlic Routing với 2 đường hầm 1 chiều độc lập.", "I2P hoàn toàn phi tập trung qua bảng băm Kademlia NetDb.", "I2P tối ưu hóa cho mạng nội bộ khép kín và chia sẻ tệp P2P."],
            [
                {"question": "Mạng I2P sử dụng kỹ thuật định tuyến mã hóa nào để gom cụm nhiều thông điệp?", "type": "MULTIPLE_CHOICE", "options": ["Onion Routing", "Garlic Routing", "Potato Routing", "Mesh Routing"], "correct_index": 1, "explanation": "I2P sử dụng Garlic Routing (Định tuyến nhánh tỏi)."},
                {"question": "Mạng I2P sử dụng 2 đường hầm một chiều riêng biệt cho chiều gửi và chiều nhận?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Inbound Tunnel và Outbound Tunnel của I2P hoàn toàn tách biệt."},
                {"question": "Hệ thống cơ sở dữ liệu định tuyến phân tán của I2P dựa trên thuật toán nào?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Kademlia", "Kademlia DHT", "DHT"]}], "explanation": "Bảng băm phân tán Kademlia DHT."}
            ]
        ),
        (
            9,
            "Bài 1.9: Hạ Tầng Tài Chính Darknet: Bitcoin, Monero & Cơ Chế Ký Quỹ Đa Chữ Ký (Multi-Sig)",
            "Phân tích cơ chế tài chính trên không gian mạng ngầm, sự thất bại của Bitcoin trong bảo vệ quyền riêng tư và vai trò của Monero cùng hợp đồng Escrow Multi-Sig.",
            "https://www.youtube.com/watch?v=KxfAW8wPDX4",
            [
                "Hiểu rõ hạn chế về tính ẩn danh giả hiệu (Pseudonymity) của Bitcoin và cơ chế sổ cái công khai.",
                "Giải mã công nghệ bảo vệ quyền riêng tư tuyệt đối của Monero (Ring Signatures, Stealth Addresses, RingCT).",
                "Nắm vững nguyên lý hoạt động của hợp đồng ký quỹ 2-of-3 Multi-Sig Escrow trên các chợ ngầm."
            ],
            [
                (
                    "Sự Ngộ Nhận Về Tính Ẩn Danh Của Bitcoin",
                    "Trong những năm đầu của Darknet (giai đoạn Silk Road 2011-2013), Bitcoin là phương tiện thanh toán độc tôn. Tuy nhiên, trong mật mã học, Bitcoin chỉ mang tính Ẩn danh giả hiệu (Pseudonymous) chứ không phải Ẩn danh thực sự (Anonymous). Toàn bộ lịch sử giao dịch của Bitcoin đều được ghi vĩnh viễn trên sổ cái công khai (Blockchain). Bất kỳ ai cũng có thể xem số dư, nguồn gốc và đích đến của từng Satoshi. Các công ty phân tích chuỗi khối (như Chainalysis, Elliptic) đã phát triển các thuật toán phân tích cụm (Cluster Analysis) và kết nối với các sàn giao dịch KYC (Coinbase, Binance) để định danh chính xác chủ sở hữu ví với tỷ lệ thành công gần như tuyệt đối."
                ),
                (
                    "Monero (XMR): Tiêu Chuẩn Vàng Của Tiền Tệ Ẩn Danh",
                    "Để khắc phục điểm yếu chết người của Bitcoin, cộng đồng bảo mật đã chuyển sang sử dụng Monero (XMR). Monero áp dụng 3 kỹ thuật mật mã học đỉnh cao: Stealth Addresses (Địa chỉ tàng hình): Mỗi giao dịch người gửi tạo ra một địa chỉ ngẫu nhiên dùng một lần cho người nhận, khiến không ai có thể liên kết địa chỉ công khai của người nhận với các khoản tiền gửi. Ring Signatures (Chữ ký vòng): Trộn lẫn chữ ký số của người gửi với nhiều người dùng khác trên mạng, khiến người quan sát không thể xác định ai là người gửi thực sự. RingCT (Ring Confidential Transactions): Ẩn hoàn toàn số tiền giao dịch bằng mật mã học cam kết Pedersen, ngăn chặn việc theo dõi dòng tiền."
                ),
                (
                    "Cơ Chế Ký Quỹ Đa Chữ Ký (2-of-3 Multi-Sig Escrow)",
                    "Làm thế nào để hai người xa lạ trên mạng ngầm có thể giao dịch hàng hóa mà không bị lừa đảo (Exit Scam)? Giải pháp là hợp đồng Ký quỹ 2-trên-3 (2-of-3 Multi-Signature Escrow): Một ví tiền mã hóa chung được tạo ra với 3 khóa riêng biệt: Khóa của Người Mua, Khóa của Người Bán, và Khóa của Trọng Tài (Sàn giao dịch). Để chuyển tiền ra khỏi ví này, bắt buộc phải có ít nhất 2 trong số 3 chữ ký hợp lệ. Nếu giao dịch diễn ra thuận lợi, Người Mua và Người Bán cùng ký tên để giải phóng tiền cho Người Bán mà không cần can thiệp của Sàn. Nếu có tranh chấp, Sàn sẽ cùng Người Mua hoặc Người Bán ký tên để hoàn tiền hoặc chuyển tiền dựa trên bằng chứng."
                )
            ],
            "Kịch bản tấn công tài chính & truy vết chuỗi khối: Tấn Công Bóc Tách Phân Cụm (Cluster Analysis Attack): Chuyên gia điều tra liên kết các địa chỉ ví Bitcoin đổi tiền thối (Change Addresses) với các địa chỉ rút tiền từ sàn giao dịch có xác minh danh tính KYC. Khi kẻ tình nghi nạp tiền lên sàn để đổi ra tiền mặt, danh tính của hắn sẽ bị lộ diện trước cơ quan chức năng.",
            "Thực hành kiểm tra địa chỉ ví Bitcoin và giải mã giao dịch thông qua API công khai bằng Python:",
            ("python", """import urllib.request
import json

# Kiểm tra thông tin giao dịch Bitcoin qua Blockchain.info API
tx_hash = "b6f7e35e97141271e10b21087285644f639d1b549331ec97d02c1fbd1d336154"
url = f"https://blockchain.info/rawtx/{tx_hash}"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, timeout=5)
    data = json.loads(res.read().decode())
    print(f"Giao dịch hợp lệ! Số đầu vào: {len(data['inputs'])}, Số đầu ra: {len(data['out'])}")
except Exception as e:
    print("Truy vấn API thất bại hoặc bị chặn:", e)"""),
            ["Không bao giờ sử dụng Bitcoin cho các giao dịch nhạy cảm yêu cầu ẩn danh cao mà không qua quy trình CoinJoin nghiêm ngặt.", "Ưu tiên sử dụng Monero (XMR) vì tính riêng tư được tích hợp ở tầng giao thức."],
            ["Bitcoin chỉ là tiền tệ ẩn danh giả hiệu (Pseudonymous) do sổ cái công khai hoàn toàn.", "Monero bảo vệ quyền riêng tư qua Stealth Addresses, Ring Signatures và RingCT.", "Cơ chế 2-of-3 Multi-Sig bảo vệ các bên khỏi nguy cơ lừa đảo."],
            [
                {"question": "Bitcoin có mang lại sự ẩn danh tuyệt đối cho người dùng không?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Bitcoin chỉ ẩn danh giả hiệu, toàn bộ giao dịch được lưu công khai trên Blockchain."},
                {"question": "Đồng tiền mã hóa nào sử dụng Ring Signatures và Stealth Addresses để ẩn hoàn toàn danh tính và số tiền?", "type": "MULTIPLE_CHOICE", "options": ["Bitcoin", "Ethereum", "Monero (XMR)", "Tether"], "correct_index": 2, "explanation": "Monero (XMR) được thiết kế chuyên biệt cho quyền riêng tư."},
                {"question": "Trong cơ chế 2-of-3 Multi-Sig, cần tối thiểu bao nhiêu chữ ký hợp lệ để giải phóng tiền khỏi ví ký quỹ?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["2", "hai", "2 chữ ký"]}], "explanation": "Cần tối thiểu 2 trong số 3 chữ ký."}
            ]
        ),
        (
            10,
            "Bài 1.10: 12 Nguyên Tắc Vàng (Do's and Don'ts) Khi Vận Hành Trong Không Gian Tor",
            "Đúc kết bộ quy tắc an toàn tác chiến (OPSEC) sống còn gồm 12 nguyên tắc không thể xâm phạm khi hoạt động trong môi trường Tor và Darknet.",
            "https://www.youtube.com/watch?v=u5Lv_HXICpo",
            [
                "Nắm vững 12 nguyên tắc vàng trong vận hành an ninh trên không gian mạng ngầm.",
                "Nhận diện các lỗi tâm lý và thói quen vô thức dẫn đến sự sụp đổ của các chiến dịch ẩn danh.",
                "Xây dựng quy trình tự kiểm tra vệ sinh an ninh số (Digital Hygiene Checklist) cá nhân."
            ],
            [
                (
                    "Tầm Quan Trọng Của Kỷ Luật OPSEC",
                    "Trong an ninh mạng, một chân lý vĩnh cửu là: Mật mã học hiếm khi thất bại, nhưng con người thì luôn luôn thất bại. Hầu như tất cả các vụ bắt giữ huyền thoại trên Darknet trong lịch sử (từ Ross Ulbricht của Silk Road cho đến Alexandre Cazes của AlphaBay) đều không bắt nguồn từ việc mạng Tor bị bẻ khóa toán học, mà bắt nguồn từ những sai lầm ngớ ngẩn về an toàn vận hành (OPSEC - Operational Security). Kỷ luật an ninh đòi hỏi sự tuân thủ nghiêm ngặt 100% thời gian; bạn chỉ cần phạm sai lầm một phần mười giây trong suốt 5 năm là toàn bộ công trình bảo vệ sẽ sụp đổ hoàn toàn."
                ),
                (
                    "6 Điều Bắt Buộc Phải Làm (The 6 Do's)",
                    "1. LUÔN LUÔN cập nhật Tor Browser lên phiên bản mới nhất ngay khi có thông báo để vá các lỗ hổng thực thi mã từ xa. 2. LUÔN LUÔN sử dụng các hệ điều hành chuyên dụng không lưu vết (Amnesic Systems) như Tails OS hoặc Whonix khi thực hiện các tác vụ nhạy cảm. 3. LUÔN LUÔN mã hóa dữ liệu nhạy cảm bằng PGP/GPG độc lập trước khi gửi đi, không tin tưởng mù quáng vào bất kỳ dịch vụ nhắn tin web nào. 4. LUÔN LUÔN xóa sạch siêu dữ liệu (Metadata/EXIF) của hình ảnh và tài liệu trước khi đăng tải. 5. LUÔN LUÔN tách biệt hoàn toàn danh tính số: Danh tính trên Darknet và danh tính đời thực phải là hai thực thể song song không bao giờ giao nhau (Air-gapped Identities). 6. LUÔN LUÔN kiểm tra chữ ký số PGP của mọi phần mềm tải về từ Internet."
                ),
                (
                    "6 Điều Tuyệt Đối Cấm Kỵ (The 6 Don'ts)",
                    "1. KHÔNG BAO GIỜ bật JavaScript khi truy cập các trang web lạ trên Darknet; luôn đặt mức bảo mật ở Safest. 2. KHÔNG BAO GIỜ thay đổi kích thước cửa sổ Tor Browser hoặc phóng to toàn màn hình để chống browser fingerprinting. 3. KHÔNG BAO GIỜ tải torrent hoặc sử dụng giao thức P2P qua mạng Tor. 4. KHÔNG BAO GIỜ mở các tệp tin tải về (PDF, DOC, EXE) khi máy tính còn đang kết nối mạng Internet. 5. KHÔNG BAO GIỜ sử dụng thông tin cá nhân (tên, ngày sinh, thói quen viết tắt, nickname cũ trên diễn đàn) trên không gian ngầm. 6. KHÔNG BAO GIỜ kết nối Tor qua mạng Wi-Fi tại nhà hoặc Wi-Fi công cộng có đăng ký danh tính cá nhân."
                )
            ],
            "Kịch bản sai lầm tâm lý: Cái bẫy của sự tự tin thái quá (Invincibility Mindset): Khi một cá nhân hoạt động trên mạng ngầm trong nhiều tháng mà không bị phát hiện, họ thường nảy sinh tâm lý khinh suất, bắt đầu lười gõ lệnh mã hóa PGP, đăng nhập từ mạng gia đình, hoặc vô tình chia sẻ các thông tin đời thường. Đây chính là lúc cơ quan điều tra khép chặt vòng vây.",
            "Thực hành xây dựng script tự động kiểm tra vệ sinh an ninh hệ thống trước khi khởi động Tor:",
            ("bash", """# Script kiểm tra an toàn trước khi vào phiên làm việc bảo mật
echo "=== KIỂM TRA VỆ SINH AN NINH (PRE-FLIGHT CHECK) ==="

# 1. Kiểm tra trạng thái tường lửa ufw
sudo ufw status | grep -qw "active" && echo "[OK] Tường lửa đang bật" || echo "[LỖI] Tường lửa chưa kích hoạt!"

# 2. Kiểm tra các dịch vụ nền đang lắng nghe cổng mạng
echo "Các cổng đang mở:"
ss -tuln

# 3. Đảm bảo IPv6 đã được vô hiệu hóa
ipv6_status=$(sysctl net.ipv6.conf.all.disable_ipv6 | awk '{print $3}')
if [ "$ipv6_status" -eq 1 ]; then
    echo "[OK] IPv6 đã tắt triệt để."
else
    echo "[CẢNH BÁO] IPv6 vẫn đang bật! Hãy tắt ngay bằng sysctl."
fi"""),
            ["Kỷ luật an ninh đòi hỏi tính liên tục 100%; một sơ suất nhỏ là xóa bỏ mọi nỗ lực bảo mật.", "Không bao giờ thỏa hiệp với sự tiện lợi để đánh đổi lấy an toàn."],
            ["OPSEC là yếu tố quyết định sự sống còn của an ninh thông tin.", "12 nguyên tắc Do's and Don'ts phân định rõ các hành vi an toàn và các điều cấm kỵ.", "Tách biệt tuyệt đối giữa danh tính ảo và danh tính đời thực."],
            [
                {"question": "Yếu tố nào thường là nguyên nhân chính dẫn đến sự thất bại của các chiến dịch ẩn danh trong lịch sử?", "type": "MULTIPLE_CHOICE", "options": ["Mật mã học bị bẻ gãy", "Lỗi con người và sai lầm OPSEC", "Mạng Tor bị sập hoàn toàn", "Vi xử lý máy tính bị hỏng"], "correct_index": 1, "explanation": "Sai lầm của con người và vi phạm kỷ luật OPSEC là nguyên nhân của hầu hết các vụ bắt giữ."},
                {"question": "Người dùng nên mở tài liệu PDF tải về từ Darknet khi đang ngắt kết nối mạng hoàn toàn hoặc trong máy ảo cô lập?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Mở tài liệu khi ngắt mạng ngăn chặn mã độc gửi tín hiệu callback về C2 server."},
                {"question": "Mức độ bảo mật nào của Tor Browser nên được sử dụng làm mặc định khi hoạt động trên Darknet?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Safest", "safest"]}], "explanation": "Mức Safest tắt toàn bộ JavaScript."}
            ]
        ),
        (
            11,
            "Bài 1.11: Giải Phẫu Vụ Án Con Đường Tơ Lụa Silk Road & Bài Học Xương Máu Về OPSEC",
            "Mổ xẻ chi tiết vụ án chấn động Silk Road, phân tích sai lầm OPSEC của Dread Pirate Roberts (Ross Ulbricht) và phương thức điều tra của FBI.",
            "https://www.youtube.com/watch?v=seB4a3Oph34",
            [
                "Nghiên cứu quá trình hình thành và quy mô kinh tế của chợ đen Silk Road.",
                "Chỉ ra chính xác các mắt xích sai lầm OPSEC dẫn đến việc Ross Ulbricht bị phát hiện danh tính thực.",
                "Rút ra các bài học kỹ thuật cốt lõi về lưu trữ dữ liệu, quản lý phiên và an ninh vật lý."
            ],
            [
                (
                    "Sự Trỗi Dậy Của Silk Road & Dread Pirate Roberts",
                    "Được thành lập vào tháng 2 năm 2011 bởi một nhân vật bí ẩn mang biệt danh 'Dread Pirate Roberts' (DPR), Silk Road là chợ đen đầu tiên ứng dụng thành công sự kết hợp giữa mạng Tor (ẩn danh kết nối) và Bitcoin (thanh toán phi tập trung). Trong hơn hai năm hoạt động, Silk Road đã xử lý hàng triệu USD giao dịch phi pháp, trở thành mục tiêu ưu tiên số 1 của Bộ Tư pháp Mỹ (DOJ), Cục Điều tra Liên bang (FBI) và Cơ quan Chống Ma túy (DEA). Mạng Tor và thuật toán Bitcoin hoạt động hoàn hảo, không một dòng code nào của Tor bị bẻ khóa. Vậy làm thế nào FBI bắt được Ross Ulbricht?"
                ),
                (
                    "Mắt Xích Sai Lầm OPSEC Số 1: Dấu Vết Số Đầu Tiên (First Digital Footprint)",
                    "Vào tháng 1 năm 2011, trước khi Silk Road ra mắt, Ross Ulbricht muốn quảng bá cho trang web mới của mình. Hắn đã lên diễn đàn Shroomery.org và Bitcointalk.org tạo chủ đề hỏi: 'Có ai nghe nói về một trang web tên là Silk Road chưa?'. Điểm chết người là tài khoản đầu tiên hắn dùng có tên là 'altoid'. Vài tháng sau, cũng chính tài khoản 'altoid' đó đăng một thông báo tuyển lập trình viên Bitcoin trên Bitcointalk và để lại địa chỉ liên hệ: `rossulbricht@gmail.com`! Chỉ một liên kết duy nhất giữa nickname ảo 'altoid' và email thật chứa tên họ đầy đủ đã mở toang cánh cửa điều tra cho các mật thám mạng của IRS và FBI."
                ),
                (
                    "Mắt Xích Sai Lầm OPSEC Số 2 & Cuộc Bắt Giữ Tại Thư Viện San Francisco",
                    "Sai lầm tiếp theo của Ulbricht là sự khinh suất về an ninh vật lý: Hắn sử dụng chiếc laptop Samsung cá nhân, đăng nhập vào bảng điều khiển quản trị Silk Road tại thư viện công cộng Glen Park ở San Francisco thông qua Wi-Fi công cộng. Nhận thức được rằng laptop của Ulbricht được mã hóa toàn bộ ổ đĩa bằng phần mềm mã hóa (Full Disk Encryption) và nếu Ulbricht kịp gập màn hình hoặc tắt máy, bằng chứng sẽ biến mất vĩnh viễn, các đặc vụ FBI đã dàn dựng một vụ cãi vã kịch tính ngay phía sau lưng hắn. Khi Ulbricht giật mình quay lại xem, một đặc vụ khác lập tức lao tới giật chiếc laptop đang mở khóa, ngay trên màn hình đang hiển thị trang quản trị Silk Road và phiên trò chuyện Master."
                )
            ],
            "Bài học kỹ thuật sâu sắc: Mã hóa mạnh đến đâu cũng vô nghĩa nếu khóa giải mã đang nằm trong bộ nhớ RAM và thiết bị rơi vào tay đối phương khi đang mở khóa. Khái niệm 'Data at Rest' (Dữ liệu khi tắt máy) được bảo vệ bởi mật mã, nhưng 'Data in Use' (Dữ liệu khi đang chạy) cực kỳ mong manh trước các cuộc tấn công vật lý.",
            "Thực hành kiểm tra và phát hiện dấu vết số rò rỉ trên các diễn đàn bằng kỹ thuật OSINT cơ bản:",
            ("bash", """# Tìm kiếm dấu vết của một nickname hoặc email trong các dữ liệu lịch sử
# Sử dụng curl để truy vấn các kho lưu trữ công cộng
target="rossulbricht"
echo "Kiểm tra dấu vết số cho: $target"

# Truy vấn thông tin người dùng công khai qua GitHub API
curl -s "https://api.github.com/users/$target" | grep -E "login|name|created_at"

# Bài học: Kẻ thù luôn tìm kiếm dấu vết đầu tiên (Patient Zero) mà bạn để lại khi mới bắt đầu!"""),
            ["Không bao giờ sử dụng email cá nhân thật trên các diễn đàn công nghệ khi thảo luận về các dự án bảo mật nhạy cảm.", "Luôn thiết lập cơ chế khóa khẩn cấp (Dead Man's Switch / USB Duress Key) để khóa máy khi bị giật thiết bị."],
            ["Silk Road sụp đổ vì sai lầm OPSEC của con người, không phải do mạng Tor bị bẻ khóa.", "Dấu vết email thật rossulbricht@gmail.com từ tài khoản 'altoid' là mấu chốt phá án.", "An ninh vật lý và bảo vệ dữ liệu trong RAM là ranh giới sống còn."],
            [
                {"question": "Silk Road sụp đổ vì nguyên nhân cốt lõi nào sau đây?", "type": "MULTIPLE_CHOICE", "options": ["Mã hóa Tor bị bẻ gãy", "Bitcoin bị tấn công 51%", "Sai lầm OPSEC của quản trị viên", "Máy chủ Tor bị cháy"], "correct_index": 2, "explanation": "Silk Road sụp đổ do sai lầm an toàn vận hành (OPSEC) của Ross Ulbricht."},
                {"question": "Địa chỉ email thật nào đã liên kết nickname ảo của người sáng lập Silk Road với danh tính ngoài đời thực?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["rossulbricht@gmail.com", "rossulbricht"]}], "explanation": "rossulbricht@gmail.com."},
                {"question": "Khi một máy tính đã mã hóa ổ đĩa đang hoạt động và mở khóa, dữ liệu giải mã sẽ nằm tạm thời trong bộ nhớ RAM?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Khóa giải mã và dữ liệu đang dùng nằm trong RAM và có thể bị thu thập nếu máy không bị tắt."}
            ]
        ),
        (
            12,
            "Bài 1.12: Xây Dựng & Vận Hành Tor Relay An Toàn Cùng Cầu Nối Pluggable Transports",
            "Hướng dẫn toàn diện quy trình thiết lập Tor Relay, cấu hình Exit Policy an toàn và sử dụng cầu nối obfs4 chống kiểm duyệt tường lửa DPI.",
            "https://www.youtube.com/watch?v=tBnJRraXDc0",
            [
                "Phân biệt và cấu hình các loại Tor Relay: Middle Relay, Exit Relay và Bridge (Cầu nối).",
                "Hiểu rõ cơ chế hoạt động của Pluggable Transports (obfs4, Snowflake) trong việc qua mặt kiểm duyệt DPI.",
                "Nắm vững các biện pháp phòng ngừa rủi ro pháp lý và an ninh mạng khi vận hành Exit Relay."
            ],
            [
                (
                    "Đóng Góp Cho Mạng Lưới: Các Loại Tor Relay",
                    "Mạng Tor chỉ có thể duy trì tốc độ và tính ẩn danh nếu có nhiều người dùng tình nguyện đóng góp băng thông làm relay. Có 3 hình thức tham gia chính: 1. Middle / Guard Relay: Chuyển tiếp lưu lượng giữa các relay nội bộ bên trong mạng Tor. Đây là hình thức an toàn nhất cho người quản trị vì relay này không trực tiếp kết nối tới bất kỳ máy chủ bên ngoài nào, do đó không bao giờ bị dính cáo buộc lạm dụng bản quyền hay khiếu nại pháp lý. 2. Exit Relay: Chuyển tiếp lưu lượng từ mạng Tor ra Internet công cộng. Vận hành Exit Relay đòi hỏi sự chuẩn bị pháp lý vững vàng và chính sách Exit Policy nghiêm ngặt vì địa chỉ IP của bạn sẽ xuất hiện trong nhật ký của các máy chủ đích. 3. Tor Bridge (Cầu Nối): Các relay bí mật không được công bố trong văn bản Consensus công khai, dùng để giúp người dùng ở các quốc gia bị kiểm duyệt Internet (như Iran, Nga, Trung Quốc) có thể kết nối vào mạng Tor."
                ),
                (
                    "Công Nghệ Vượt Kiểm Duyệt: Pluggable Transports (obfs4 & Snowflake)",
                    "Các hệ thống tường lửa kiểm duyệt quốc gia hiện đại sử dụng công nghệ Kiểm định gói tin sâu (Deep Packet Inspection - DPI) để nhận dạng dấu vết giao thức TLS đặc thù của Tor và chặn kết nối ngay lập tức. Để đối phó, Tor Project phát triển các công nghệ Pluggable Transports: obfs4 (Obfuscator v4): Biến đổi luồng lưu lượng Tor thành một dòng byte ngẫu nhiên không có cấu trúc cố định, khiến tường lửa DPI không thể phân biệt giữa lưu lượng Tor và luồng nhiễu ngẫu nhiên. Snowflake: Sử dụng công nghệ WebRTC ngang hàng để mượn các trình duyệt web của các tình nguyện viên làm cầu nối tạm thời, khiến cho việc chặn trở nên bất khả thi mà không chặn toàn bộ lưu lượng video conference của cả quốc gia."
                ),
                (
                    "Cấu Hình Tệp torrc Chuẩn Cho Một Middle Relay",
                    "Để vận hành một Middle Relay an toàn, người quản trị cấu hình tệp `/etc/tor/torrc` với chính sách từ chối toàn bộ lưu lượng thoát (ExitPolicy reject *:*). Điều này đảm bảo relay của bạn chỉ đóng vai trò chuyển tiếp nội bộ và không bao giờ bị khiếu nại DMCA."
                )
            ],
            "Rủi ro pháp lý khi vận hành Exit Relay: Khi một tội phạm mạng tấn công một ngân hàng hoặc phát tán thư rác thông qua Exit Relay của bạn, địa chỉ IP của Exit Relay sẽ là mục tiêu đầu tiên nhận trát hầu tòa hoặc yêu cầu tịch thu máy chủ từ cảnh sát. Quản trị viên Exit Relay bắt buộc phải thiết lập bản ghi Reverse DNS (rDNS) ghi rõ 'tor-exit-node', cung cấp trang thông tin công khai và có sự tư vấn của luật sư.",
            "Thực hành cấu hình một Tor Middle Relay an toàn và giới hạn băng thông trên máy chủ Ubuntu:",
            ("bash", """# Cấu hình Middle Relay an toàn trong /etc/tor/torrc
sudo tee /etc/tor/torrc << 'EOF'
Nickname MySecureRelay
ContactInfo admin@example.com
ORPort 9001
ExitRelay 0
ExitPolicy reject *:*
RelayBandwidthRate 1024 KBytes
RelayBandwidthBurst 2048 KBytes
EOF

# Khởi động lại dịch vụ và kiểm tra nhật ký kết nối
sudo systemctl restart tor
sudo journalctl -u tor -n 20 --no-pager"""),
            ["Tuyệt đối không bật ExitRelay 1 trên đường truyền Internet cá nhân tại nhà nếu không muốn cảnh sát gõ cửa.", "Luôn thiết lập RelayBandwidthRate để tránh việc relay ngốn toàn bộ băng thông máy chủ."],
            ["Tor Relay bao gồm Middle, Exit và Bridge.", "Pluggable Transports (obfs4, Snowflake) ngụy trang lưu lượng để qua mặt tường lửa DPI.", "Vận hành Middle Relay là phương thức an toàn và ý nghĩa nhất để cống hiến cho cộng đồng ẩn danh."],
            [
                {"question": "Loại relay nào không được công bố trong Consensus công khai để giúp người dùng vượt tường lửa kiểm duyệt?", "type": "MULTIPLE_CHOICE", "options": ["Guard Relay", "Exit Relay", "Tor Bridge (Cầu nối)", "Middle Relay"], "correct_index": 2, "explanation": "Tor Bridge là cầu nối bí mật không công khai."},
                {"question": "Giao thức Pluggable Transport nào biến đổi lưu lượng Tor thành chuỗi byte ngẫu nhiên chống kiểm duyệt DPI?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["obfs4", "OBFS4"]}], "explanation": "obfs4 ngụy trang luồng lưu lượng."},
                {"question": "Cấu hình ExitPolicy reject *:* đảm bảo relay của bạn sẽ không bao giờ phát lưu lượng ra Internet công cộng?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Chính sách reject *:* biến relay thành Middle Relay an toàn."}
            ]
        )
    ]

    for (pos, title, summary, v_url, obj_pts, theory_secs, att_def, lab_inst, code_snip, pits, sums, q_json) in tor_lesson_configs:
        l = {
            "position": pos,
            "title": title,
            "summary": summary,
            "duration_minutes": 35,
            "video_url": v_url,
            "markdown_content": generate_lesson_markdown(
                lesson_num=f"1.{pos}",
                title=title,
                objective_points=obj_pts,
                theory_sections=theory_secs,
                attack_defense_section=att_def,
                lab_instructions=lab_inst,
                code_snippet=code_snip,
                pitfalls=pits,
                summary_points=sums,
                video_url=v_url,
                quiz_json=q_json,
            )
        }
        validate_lesson_data(l)
        lessons.append(l)

    return lessons


if __name__ == "__main__":
    ls = get_chapter_1_lessons()
    print(f"Generated {len(ls)} lessons for Chapter 1.")
    for l in ls:
        wc = count_vietnamese_words(l["markdown_content"])
        print(f"  - {l['title'][:40]}: {wc} words")
