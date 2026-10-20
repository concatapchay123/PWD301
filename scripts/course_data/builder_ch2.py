"""Builder for Chapter 2: Kỹ Thuật Ẩn Danh Chuyên Sâu, Chống Giám Sát NSA & An Toàn Vận Hành OPSEC.
Source book: Tor_and_The_Dark_Net_Remain_Anonymous_and_Evade_NSA_Spying_by_Ja.pdf (11 lessons).
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

CHAPTER_2_INFO = {
    "title": "Chương 2: Kỹ Thuật Ẩn Danh Chuyên Sâu, Chống Giám Sát NSA & An Toàn Vận Hành OPSEC",
    "source_file": "Tor_and_The_Dark_Net_Remain_Anonymous_and_Evade_NSA_Spying_by_Ja.pdf",
    "position": 2,
}


def get_chapter_2_lessons() -> list[dict]:
    lessons = []

    configs = [
        (
            1,
            "Bài 2.1: Mô Hình Đe Dọa (Threat Modeling) & Các Kỹ Thuật Giám Sát Hàng Loạt Của NSA",
            "Nghiên cứu kiến trúc giám sát toàn cầu của NSA (PRISM, XKeyscore), mô hình đe dọa thực tế và phương pháp luận thiết lập ranh giới phòng thủ số.",
            "https://www.youtube.com/watch?v=u5Lv_HXICpo",
            [
                "Phân tích các chương trình giám sát đại trà của NSA được tiết lộ qua tài liệu Edward Snowden.",
                "Nắm vững phương pháp luận xây dựng Mô hình đe dọa (Threat Model) cá nhân hóa.",
                "Đánh giá năng lực của các đối thủ cấp độ quốc gia (Nation-state Actors) và ranh giới khả thi của mật mã học dân sự."
            ],
            [
                (
                    "Các Chương Trình Giám Sát Toàn Cầu: PRISM & XKeyscore",
                    "Năm 2013, cựu chuyên viên phân tích tình báo Edward Snowden đã làm rúng động thế giới khi công bố hàng nghìn tài liệu tối mật về hệ thống giám sát toàn cầu của Cơ quan An ninh Quốc gia Hoa Kỳ (NSA) và liên minh Ngũ Nhãn (Five Eyes: Mỹ, Anh, Canada, Úc, New Zealand). Hai chương trình tiêu biểu nhất bao gồm: PRISM: Cho phép NSA tiếp cận trực tiếp vào các máy chủ trung tâm của 9 tập đoàn công nghệ khổng lồ (Microsoft, Google, Apple, Yahoo, Facebook...) để trích xuất email, tin nhắn âm thanh, video chat, hình ảnh và tài liệu lưu trữ đám mây của người dùng mà không cần trát tòa riêng biệt. XKeyscore: Hệ thống xử lý dữ liệu lớn thời gian thực có khả năng nghe lén gần như toàn bộ lưu lượng Internet toàn cầu đi qua các đường cáp quang ngầm xuyên đại dương. Chỉ với một cú nhấp chuột, một nhà phân tích tình báo có thể nhập địa chỉ IP hoặc từ khóa để xem toàn bộ lịch sử duyệt web và nội dung email chưa mã hóa của bất kỳ ai."
                ),
                (
                    "Phương Pháp Luận Xây Dựng Mô Hình Đe Dọa (Threat Modeling)",
                    "Trong an ninh tác chiến (OPSEC), không có giải pháp an ninh nào phù hợp cho tất cả mọi người. Một sai lầm tai hại là cố gắng 'chống lại tất cả mọi thứ' để rồi tạo ra sự bất tiện không thể chịu nổi dẫn đến phá vỡ kỷ luật an ninh. Bạn bắt buộc phải trả lời 5 câu hỏi cốt lõi: 1. Bạn muốn bảo vệ tài sản số nào? (Khóa bí mật PGP, danh tính thực, tài liệu mật, địa chỉ ví). 2. Ai là đối thủ tiềm tàng của bạn? (Kẻ trộm máy tính, đối thủ kinh doanh, hacker mũ đen, cảnh sát địa phương hay cơ quan tình báo quốc gia). 3. Hậu quả là gì nếu tài sản bị lộ? (Mất tiền, mất uy tín, hầu tòa hay đe dọa tính mạng). 4. Khả năng đối thủ tấn công thành công là bao nhiêu? 5. Bạn sẵn sàng chấp nhận bao nhiêu sự bất tiện để ngăn chặn nguy cơ đó?"
                ),
                (
                    "Ranh Giới Phòng Thủ Số Trước Cơ Quan Tình Báo",
                    "Mặc dù NSA sở hữu các siêu máy tính mạnh mẽ nhất thế giới, các nhà toán học đã khẳng định: Mật mã học mạnh (Strong Cryptography) như AES-256, RSA-4096 hay Ed25519 vẫn bất khả xâm phạm trước năng lực tính toán hiện tại. NSA không thể phá vỡ thuật toán toán học; thay vào đó, họ tấn công vào các điểm yếu biên: phần mềm độc hại cài cắm tại máy trạm (End-point Malware), các cửa hậu phần cứng (Hardware Backdoors), và các sai sót sơ đẳng của người dùng khi thiết lập khóa mật mã."
                )
            ],
            "Kịch bản tấn công thực tế: Khai Thác Lưu Lượng Sợi Cáp Quang Ngầm: NSA đặt các thiết bị tách chùm quang (Optical Splitters) trực tiếp tại các trạm cập bờ cáp biển. Lưu lượng dữ liệu được nhân bản 1:1 và chuyển về các trung tâm dữ liệu khổng lồ (như Utah Data Center) để lưu trữ vĩnh viễn và xử lý bằng trí tuệ nhân tạo.",
            "Thực hành kiểm tra và rà soát các dịch vụ đám mây công cộng đang lưu trữ dữ liệu cá nhân của bạn:",
            ("bash", """# Kiểm tra các kết nối mạng đang xuất phát từ máy tính đến các máy chủ đám mây lớn
echo "=== KIỂM TRA LƯU LƯỢNG MẠNG TỚI CÁC MÁY CHỦ NGOÀI ==="
ss -tupn | grep -E "ESTAB" | awk '{print $5}' | cut -d: -f1 | sort -u | while read ip; do
    whois $ip 2>/dev/null | grep -iE "OrgName|NetName" | head -n 1
done"""),
            ["Không bao giờ xây dựng mô hình đe dọa dựa trên sự phỏng đoán cảm tính mà không đánh giá tài sản thực tế.", "Hiểu rằng không có hệ điều hành thương mại đóng mã nguồn nào (Windows, macOS) có thể đảm bảo 100% không có backdoor tình báo."],
            ["PRISM và XKeyscore chứng minh sự tồn tại của hạ tầng giám sát Internet đại trà cấp quốc gia.", "Mô hình đe dọa (Threat Modeling) là nền móng xác định mức độ phòng thủ cần thiết.", "Mật mã học mạnh vẫn là vũ khí hữu hiệu nhất chống lại sự giám sát diện rộng."],
            [
                {"question": "Chương trình giám sát nào của NSA cho phép trích xuất trực tiếp dữ liệu từ máy chủ các tập đoàn công nghệ lớn?", "type": "MULTIPLE_CHOICE", "options": ["PRISM", "Stuxnet", "Pegasus", "Echelon"], "correct_index": 0, "explanation": "Chương trình PRISM tiếp cận dữ liệu từ Microsoft, Google, Apple..."},
                {"question": "Mật mã học mạnh như AES-256 hiện tại đã bị NSA giải mã toán học thành công?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Thuật toán toán học của AES-256 vẫn chưa thể bị bẻ gãy bằng sức mạnh tính toán hiện nay."},
                {"question": "Điền tên tiến trình đánh giá 5 câu hỏi cốt lõi để xác định đối thủ, tài sản và mức độ phòng thủ an ninh cá nhân:", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Threat Modeling", "Mô hình đe dọa", "threat modeling"]}], "explanation": "Threat Modeling (Mô hình đe dọa)."}
            ]
        ),
        (
            2,
            "Bài 2.2: Triển Khai Hệ Điều Hành Bảo Mật Amnesic Tails OS Trên USB Mã Hóa",
            "Làm chủ Tails OS (The Amnesic Incognito Live System): Kiến trúc xóa sạch dấu vết trong RAM, ép buộc định tuyến Tor và phân vùng lưu trữ Persistent Storage.",
            "https://www.youtube.com/watch?v=xZkudBtPgiE",
            [
                "Nắm vững kiến trúc phần mềm amnesic (mất trí nhớ) của Tails OS.",
                "Thực hành cài đặt Tails OS chuẩn an ninh lên USB rời và xác thực chữ ký PGP của ảnh đĩa.",
                "Cấu hình phân vùng lưu trữ bền vững được mã hóa LUKS (Encrypted Persistent Storage)."
            ],
            [
                (
                    "Bản Chất Kỹ Thuật Của Hệ Điều Hành Amnesic",
                    "Tails (The Amnesic Incognito Live System) là một bản phân phối Linux độc lập dựa trên Debian, được thiết kế chuyên biệt để chạy trực tiếp từ bộ nhớ USB hoặc thẻ nhớ SD. Khái niệm 'Amnesic' (mất trí nhớ) thể hiện cơ chế an toàn tối thượng: Tails hoàn toàn không bao giờ sử dụng hoặc ghi bất kỳ byte dữ liệu nào lên ổ cứng (HDD/SSD) của máy tính chủ. Toàn bộ hệ điều hành, tệp đệm, nhật ký hoạt động đều hoạt động 100% trong bộ nhớ tạm RAM. Ngay khi người dùng tắt máy hoặc rút thẻ USB ra khỏi cổng kết nối (Emergency Shutdown), máy tính sẽ tự động kích hoạt tiến trình ghi đè bộ nhớ RAM bằng dữ liệu ngẫu nhiên, xóa sạch mọi dấu vết điện tử."
                ),
                (
                    "Ép Buộc Định Tuyến Tor Toàn Diện (Tor Enforcement)",
                    "Trong các hệ điều hành thông thường, nếu một ứng dụng bị lỗi cấu hình proxy, nó có thể tự do phát các gói tin TCP/UDP trực tiếp ra Internet qua card mạng máy tính, làm lộ địa chỉ IP thật của người dùng. Ngược lại, trong Tails OS, tường lửa nhân Linux Netfilter/iptables được cấu hình chặt chẽ theo nguyên tắc khóa kín: MỌI kết nối mạng đi ra ngoài đều bị chặn tuyệt đối, NGOẠI TRỪ các kết nối xuất phát từ daemon Tor nội bộ. Bất kỳ ứng dụng nào cố tình gửi gói tin ra ngoài mạng Tor đều bị tường lửa hủy bỏ ngay lập tức."
                ),
                (
                    "Phân Vùng Lưu Trữ Mã Hóa Persistent Storage",
                    "Mặc dù Tails là hệ điều hành mất trí nhớ, người dùng vẫn có nhu cầu lưu lại các khóa PGP bí mật, mật khẩu KeePassXC hoặc tài liệu làm việc quan trọng. Tails giải quyết bài toán này thông qua tính năng Persistent Storage: Một phân vùng riêng biệt trên chính chiếc USB được mã hóa cực kỳ mạnh bằng chuẩn LUKS (Linux Unified Key Setup) với thuật toán AES-XTS 512-bit và hàm băm Argon2id. Phân vùng này chỉ được giải mã khi người dùng nhập mật khẩu quản trị lúc khởi động hệ điều hành."
                )
            ],
            "Kịch bản tấn công thu thập chứng cứ pháp y bộ nhớ RAM: Tấn Công Khởi Động Lạnh (Cold Boot Attack): Khi một máy tính bị tắt nguồn đột ngột, các transistor trong thanh RAM không mất dữ liệu ngay lập tức mà vẫn giữ lại nội dung trong vài giây đến vài phút (đặc biệt nếu được làm lạnh bằng khí nén nito lỏng). Chuyên gia pháp y có thể cắm USB cứu hộ để trích xuất toàn bộ khóa giải mã từ RAM. Tails OS khắc phục rủi ro này bằng cách chủ động ghi đè dữ liệu ngẫu nhiên lên toàn bộ RAM ngay trong tiến trình shutdown.",
            "Thực hành xác thực chữ ký số PGP của ảnh đĩa Tails OS trên môi trường dòng lệnh Linux:",
            ("bash", """# 1. Tải khóa công khai ký số chính thức của Tails Project
wget https://tails.net/tails-signing.key

# 2. Nhập khóa công khai vào vòng khóa GnuPG cá nhân
gpg --import tails-signing.key

# 3. Xác thực vân tay khóa (Fingerprint) chuẩn của Tails Project:
# A8DB D322 B36C D4A9 2166  9724 18AC C420 250D A26B
gpg --fingerprint 18ACC420250DA26B

# 4. Xác thực tính toàn vẹn và nguồn gốc của tệp ảnh đĩa Tails ISO
gpg --verify tails-amd64-*.img.sig tails-amd64-*.img"""),
            ["Tuyệt đối không chạy Tails OS bên trong một máy ảo trên Windows vì hệ điều hành Windows chủ có thể chụp lén màn hình và ghi lại nhật ký bàn phím (Keylogger).", "Luôn chọn mật khẩu phân vùng Persistent Storage có độ dài trên 20 ký tự."],
            ["Tails OS hoạt động hoàn toàn trên RAM và không ghi bất kỳ dữ liệu nào vào ổ cứng máy tính.", "Tường lửa iptables ép buộc 100% lưu lượng mạng phải đi xuyên qua Tor.", "Phân vùng Persistent Storage được mã hóa mạnh mẽ bằng chuẩn LUKS AES-512."],
            [
                {"question": "Đặc tính 'Amnesic' của Tails OS có ý nghĩa kỹ thuật là gì?", "type": "MULTIPLE_CHOICE", "options": ["Hệ thống không ghi dữ liệu lên ổ cứng và xóa sạch RAM khi tắt máy", "Hệ thống tự động xóa mật khẩu người dùng", "Hệ thống tự đổi tên file", "Hệ thống ngắt kết nối internet"], "correct_index": 0, "explanation": "Amnesic nghĩa là không lưu vết trên ổ đĩa và tẩy sạch bộ nhớ RAM."},
                {"question": "Chuẩn mã hóa nào được Tails OS sử dụng để bảo vệ phân vùng lưu trữ bền vững Persistent Storage?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["LUKS", "luks"]}], "explanation": "Linux Unified Key Setup (LUKS)."},
                {"question": "Chạy Tails OS bên trong máy ảo trên hệ điều hành Windows là an toàn tuyệt đối 100%?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Windows máy chủ có thể theo dõi bộ nhớ, chụp màn hình và ghi nhật ký phím của máy ảo."}
            ]
        ),
        (
            3,
            "Bài 2.3: Thiết Lập Máy Ảo Cô Lập Mạng Tor Qua Whonix Gateway & Workstation",
            "Mổ xẻ kiến trúc hai máy ảo cô lập (Two-VM Isolation) của Whonix: Ngăn chặn triệt để rò rỉ địa chỉ IP thật ngay cả khi hệ điều hành máy trạm bị chiếm quyền root.",
            "https://www.youtube.com/watch?v=KxfAW8wPDX4",
            [
                "Hiểu rõ kiến trúc phân tách vật lý hai máy ảo: Whonix-Gateway và Whonix-Workstation.",
                "Giải thích cơ chế cách ly mạng nội bộ (Internal Virtual Network) và triệt tiêu nguy cơ rò rỉ IP ở mức độ hạt nhân.",
                "Thực hành cài đặt và cấu hình Whonix trên VirtualBox/KVM chuẩn an ninh doanh nghiệp."
            ],
            [
                (
                    "Hạn Chế Của Tails OS & Sự Ra Đời Của Whonix",
                    "Mặc dù Tails OS rất mạnh mẽ, nó có một điểm yếu chí mạng về mặt an ninh kiến trúc: Tails chạy tất cả các ứng dụng (trình duyệt, bộ gõ, phần mềm phân tích) trên cùng một hệ điều hành duy nhất. Nếu một kẻ tấn công khai thác thành công một lỗ hổng zero-day trong trình duyệt và leo thang đặc quyền lên tài khoản root của Tails, hắn có thể đọc trực tiếp bộ nhớ của nhân Linux và trích xuất địa chỉ IP thật của card mạng vật lý. Để giải quyết triệt để nguy cơ này, kiến trúc Whonix ra đời với triết lý: **Phân tách hoàn toàn môi trường mạng và môi trường ứng dụng thành hai máy ảo riêng biệt**."
                ),
                (
                    "Kiến Trúc Hai Máy Ảo: Gateway vs Workstation",
                    "Whonix chia hệ thống thành hai cỗ máy ảo độc lập nối với nhau qua một mạng nội bộ ảo hoàn toàn cô lập: 1. Whonix-Gateway (Cổng Chuyển Tiếp): Máy ảo này có 2 card mạng: Card 1 kết nối ra ngoài Internet thông qua NAT để tải dữ liệu Tor; Card 2 kết nối vào mạng nội bộ riêng (Internal Network). Gateway chạy daemon Tor và hoạt động như một router trung chuyển. Nó không chạy bất kỳ ứng dụng duyệt web nào của người dùng. 2. Whonix-Workstation (Máy Trạm Làm Việc): Máy ảo này chỉ có DUY NHẤT một card mạng nội bộ kết nối trực tiếp với Whonix-Gateway. Toàn bộ phần mềm duyệt web, chat, xử lý tài liệu đều chạy trên Workstation. Workstation hoàn toàn không hề biết địa chỉ IP thật của máy tính vật lý; địa chỉ IP duy nhất mà Workstation nhìn thấy là địa chỉ mạng nội bộ 10.152.152.xx do Gateway cấp phát!"
                ),
                (
                    "Cơ Chế Bất Khả Xâm Phạm Của Whonix",
                    "Điều gì xảy ra nếu tin tặc chiếm quyền root trên Whonix-Workstation? Câu trả lời là: Tin tặc vẫn hoàn toàn bất lực trong việc tìm ra địa chỉ IP thật của bạn! Vì về mặt vật lý ảo, Workstation không có card mạng nào kết nối ra Internet và không thể giao tiếp trực tiếp với router Wi-Fi của bạn. Mọi gói tin mà mã độc phát ra đều bị ép buộc phải đi qua Gateway và bị Gateway biến thành luồng dữ liệu Tor. Đây là cơ chế bảo vệ tối thượng chống lại các phần mềm độc hại khai thác danh tính tinh vi nhất."
                )
            ],
            "Kịch bản tấn công phá vỡ máy ảo: Tấn Công Thoát Khỏi Máy Ảo (VM Escape Attack): Nếu tin tặc sở hữu mã độc khai thác lỗ hổng trong hypervisor (VirtualBox/KVM) để nhảy từ hệ điều hành khách (Guest OS) ra hệ điều hành chủ (Host OS), hắn mới có thể tìm được IP thật. Do đó, việc cập nhật phần mềm ảo hóa VirtualBox/KVM thường xuyên là yêu cầu bắt buộc.",
            "Thực hành kiểm tra cấu hình mạng nội bộ trên Whonix-Workstation:",
            ("bash", """# Kiểm tra cấu hình card mạng trên Whonix-Workstation
ip addr show eth0

# Kiểm tra bảng định tuyến mặc định của Workstation (phải trỏ về IP của Gateway 10.152.152.10)
ip route show

# Kiểm tra kết nối định tuyến qua Tor bằng lệnh curl từ Workstation
curl -s https://check.torproject.org/api/ip"""),
            ["Tuyệt đối không gắn thêm card mạng NAT hoặc Bridged vào Whonix-Workstation, vì điều này sẽ phá hủy hoàn toàn kiến trúc cách ly an toàn của Whonix.", "Không chia sẻ tệp tin giữa máy thật (Host) và máy ảo Workstation qua Shared Folders có phân quyền ghi."],
            ["Whonix phân tách hệ thống thành 2 máy ảo: Whonix-Gateway và Whonix-Workstation.", "Workstation hoàn toàn không biết địa chỉ IP thật của thiết bị vật lý.", "Ngay cả khi bị chiếm quyền root trên Workstation, địa chỉ IP thật của người dùng vẫn được bảo vệ nguyên vẹn."],
            [
                {"question": "Trong kiến trúc Whonix, máy ảo nào chịu trách nhiệm kết nối trực tiếp ra mạng Internet công cộng và chạy Tor daemon?", "type": "MULTIPLE_CHOICE", "options": ["Whonix-Workstation", "Whonix-Gateway", "Whonix-Master", "Whonix-Client"], "correct_index": 1, "explanation": "Whonix-Gateway đóng vai trò làm router Tor chuyển tiếp."},
                {"question": "Nếu tin tặc chiếm quyền root trên Whonix-Workstation, hắn có thể đọc được ngay địa chỉ IP thật của máy chủ vật lý?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Workstation chỉ nhìn thấy IP mạng nội bộ ảo, không chứa bất kỳ thông tin nào về IP thật."},
                {"question": "Mô hình phân tách của Whonix gồm mấy máy ảo độc lập?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["2", "hai", "2 máy ảo"]}], "explanation": "Mô hình 2 máy ảo (Two-VM Isolation)."}
            ]
        ),
        (
            4,
            "Bài 2.4: Mã Hóa Bất Đối Xứng PGP/GPG Chuyên Sâu & Quản Lý Keyring An Toàn",
            "Làm chủ mật mã học bất đối xứng PGP/GPG: Cấu trúc cặp khóa RSA/Ed25519, chữ ký số (Digital Signatures), mã hóa thông điệp và quản lý vòng khóa an toàn.",
            "https://www.youtube.com/watch?v=u5Lv_HXICpo",
            [
                "Nắm vững nguyên lý mật mã học bất đối xứng (Public Key vs Private Key).",
                "Thực hành tạo cặp khóa GnuPG chuẩn công nghiệp (Ed25519/RSA-4096) và xuất khóa công khai.",
                "Thực hành mã hóa, giải mã thông điệp và xác thực chữ ký số bằng dòng lệnh CLI."
            ],
            [
                (
                    "Nguyên Lý Cốt Lõi Của Mật Mã Bất Đối Xứng (Asymmetric Cryptography)",
                    "Trong mật mã học truyền thống đối xứng (như AES), cả người gửi và người nhận đều phải dùng chung một khóa bí mật để mã hóa và giải mã. Điều này dẫn đến lỗ hổng sống còn: Làm thế nào để hai người chưa từng gặp mặt có thể chia sẻ khóa bí mật đó qua Internet mà không bị nghe lén? Năm 1991, Phil Zimmermann phát minh ra phần mềm PGP (Pretty Good Privacy) dựa trên mật mã bất đối xứng: Mỗi người dùng sở hữu một cặp khóa toán học duy nhất gắn kết chặt chẽ với nhau: Khóa Công Khai (Public Key): Dùng để MÃ HÓA dữ liệu hoặc XÁC THỰC chữ ký số. Khóa này có thể gửi công khai cho bất kỳ ai trên thế giới hoặc tải lên các máy chủ khóa (Keyservers). Khóa Bí Mật (Private Key): Dùng để GIẢI MÃ dữ liệu hoặc TẠO chữ ký số. Khóa này bắt buộc phải được bảo vệ tuyệt mật trên thiết bị cá nhân và khóa bằng một mật khẩu mạnh (passphrase)."
                ),
                (
                    "Quy Trình Mã Hóa & Chữ Ký Số PGP",
                    "Khi Bob muốn gửi một bức thư mật cho Alice: Bob sử dụng Khóa Công Khai của Alice để mã hóa bức thư. Sau khi đã mã hóa, CHỈ DUY NHẤT Khóa Bí Mật của Alice mới có thể giải mã được bức thư đó. Ngay cả chính Bob sau khi mã hóa xong cũng không thể tự đọc lại nội dung của mình! Ngược lại, khi Alice muốn chứng minh bức thư do chính tay mình viết mà không bị ai giả mạo: Alice dùng Khóa Bí Mật của mình để tạo ra một Chữ Ký Số (Digital Signature) đính kèm bức thư. Bob và bất kỳ ai trên thế giới đều có thể dùng Khóa Công Khai của Alice để xác thực tính toàn vẹn và nguồn gốc của bức thư."
                ),
                (
                    "Lựa Chọn Thuật Toán: RSA-4096 vs Elliptic Curve (Ed25519)",
                    "Trước đây, chuẩn công nghiệp phổ biến là RSA với độ dài khóa 4096-bit. Tuy nhiên, các cặp khóa RSA lớn có tốc độ xử lý chậm và kích thước tệp lớn. Hiện nay, cộng đồng an ninh chuyển đổi mạnh mẽ sang sử dụng Mật mã đường cong Elliptic (ECC), cụ thể là thuật toán **Ed25519 (chữ ký số)** và **Cv25519 (mã hóa trao đổi khóa)**. Khóa Ed25519 256-bit có độ bảo mật tương đương khóa RSA 3072-bit nhưng có tốc độ xử lý nhanh hơn gấp 10 lần và kích thước khóa siêu nhỏ gọn."
                )
            ],
            "Kịch bản tấn công vòng khóa PGP: Tấn Công Tráo Khóa Công Khai (Man-in-the-Middle Key Substitution): Nếu Alice gửi khóa công khai cho Bob qua một kênh liên lạc không an toàn (như email không mã hóa), kẻ tấn công đứng giữa có thể đánh tráo khóa của Alice bằng khóa công khai của chính kẻ tấn công. Khi Bob dùng khóa giả để mã hóa dữ liệu, kẻ tấn công sẽ chặn và đọc được toàn bộ bí mật. Do đó, việc đối chiếu Vân Tay Khóa (Key Fingerprint) qua một kênh độc lập là bắt buộc.",
            "Thực hành tạo cặp khóa Ed25519 bằng công cụ GnuPG CLI và thực hiện mã hóa thông điệp:",
            ("bash", """# 1. Tạo cặp khóa GPG với thuật toán hiện đại Ed25519
gpg --expert --full-generate-key
# Chọn tùy chọn: (9) ECC and ECC -> Curve 25519 -> Nhập Tên và Email

# 2. Xem danh sách các khóa và kiểm tra vân tay khóa (Fingerprint)
gpg --list-secret-keys --keyid-format LONG

# 3. Xuất khóa công khai dạng văn bản ASCII (Armor) để chia sẻ
gpg --armor --export "your_email@example.com" > public_key.asc

# 4. Mã hóa một tệp tin văn bản bí mật bằng khóa công khai
echo "Du lieu tinh bao toi mat" > secret.txt
gpg --armor --encrypt --recipient "your_email@example.com" secret.txt

# 5. Giải mã tệp tin đã mã hóa bằng khóa bí mật
gpg --decrypt secret.txt.asc"""),
            ["Không bao giờ lưu khóa bí mật PGP trên các dịch vụ lưu trữ đám mây công cộng (Google Drive, Dropbox) mà không có lớp mã hóa thứ cấp.", "Luôn tạo chứng chỉ thu hồi khóa (Revocation Certificate) ngay sau khi tạo khóa để phòng trường hợp bị mất khóa bí mật."],
            ["Mật mã bất đối xứng PGP sử dụng cặp khóa Public Key và Private Key độc lập.", "Ed25519 là tiêu chuẩn hiện đại mang lại hiệu năng cao và bảo mật vượt trội so với RSA truyền thống.", "Luôn xác thực Key Fingerprint để chống tấn công đánh tráo khóa công khai."],
            [
                {"question": "Khóa nào trong cặp khóa PGP có thể được chia sẻ công khai cho tất cả mọi người?", "type": "MULTIPLE_CHOICE", "options": ["Khóa Bí Mật (Private Key)", "Khóa Công Khai (Public Key)", "Khóa Phiên (Session Key)", "Master Key"], "correct_index": 1, "explanation": "Khóa Công Khai (Public Key) được thiết kế để phân phát tự do cho mọi người."},
                {"question": "Khi gửi thư mật cho Alice, người gửi sẽ sử dụng khóa nào của Alice để mã hóa dữ liệu?", "type": "MULTIPLE_CHOICE", "options": ["Khóa Bí Mật của Alice", "Khóa Công Khai của Alice", "Khóa Bí Mật của người gửi", "Khóa ngẫu nhiên"], "correct_index": 1, "explanation": "Mã hóa bằng Khóa Công Khai của người nhận, giải mã bằng Khóa Bí Mật của người nhận."},
                {"question": "Khóa công khai và khóa bí mật của PGP có thể giải mã thay thế cho nhau một cách tùy ý?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Khóa công khai chỉ mã hóa, chỉ có khóa bí mật tương ứng mới giải mã được."}
            ]
        )
    ]

    # Generate 2.1 to 2.4
    for (pos, title, summary, v_url, obj_pts, theory_secs, att_def, lab_inst, code_snip, pits, sums, q_json) in configs:
        l = {
            "position": pos,
            "title": title,
            "summary": summary,
            "duration_minutes": 35,
            "video_url": v_url,
            "markdown_content": generate_lesson_markdown(
                lesson_num=f"2.{pos}",
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

    # Now add lessons 2.5 to 2.11
    configs_part2 = [
        (
            5,
            "Bài 2.5: Mã Hóa Toàn Bộ Ổ Đĩa (Full Disk Encryption) Với VeraCrypt & LUKS",
            "Nghiên cứu nguyên lý bảo vệ dữ liệu khi tắt máy (Data at Rest) bằng công nghệ mã hóa khối VeraCrypt và LUKS, cơ chế phòng vệ cưỡng bức Plausible Deniability.",
            "https://www.youtube.com/watch?v=xZkudBtPgiE",
            [
                "Nắm vững nguyên lý mã hóa toàn bộ ổ đĩa FDE (Full Disk Encryption) với các chế độ mã hóa khối XTS.",
                "Thực hành tạo ổ đĩa mã hóa ảo bằng VeraCrypt và phân vùng LUKS trên Linux.",
                "Giải mã kỹ thuật tạo ổ đĩa ẩn (Hidden Volume) để áp dụng cơ chế Chối bỏ hợp lý (Plausible Deniability)."
            ],
            [
                (
                    "Khái Niệm Data at Rest & Sự Cần Thiết Của FDE",
                    "Khi máy tính của bạn bị tắt nguồn hoặc bị tịch thu vật lý, toàn bộ dữ liệu trên ổ đĩa SSD/HDD đều có thể bị đọc trực tiếp nếu không được mã hóa. Mã Hóa Toàn Bộ Ổ Đĩa (Full Disk Encryption - FDE) là kỹ thuật mã hóa từng khu vực (sector) của ổ cứng bằng các thuật toán đối xứng mạnh mẽ như AES-256 ở chế độ hoạt động XTS (XEX Tweakable Block Cipher with Ciphertext Stealing). Không có mật khẩu giải mã đúng, toàn bộ ổ đĩa chỉ là một mớ dữ liệu ngẫu nhiên không có ý nghĩa."
                ),
                (
                    "Cơ Chế Chối Bỏ Hợp Lý (Plausible Deniability) Trong VeraCrypt",
                    "Trong nhiều tình huống thực tế, đối phương có thể sử dụng các biện pháp tra khảo, ép buộc pháp lý hoặc bạo lực thể xác để buộc bạn phải giao mật khẩu giải mã (Rubber-hose Cryptanalysis). VeraCrypt giải quyết tình huống ngặt nghèo này bằng công nghệ **Ổ Đĩa Ẩn (Hidden Volume)**: Bên trong một vùng chứa mã hóa thông thường (Outer Volume), VeraCrypt tạo ra một vùng chứa mã hóa thứ hai hoàn toàn vô hình (Hidden Volume) nằm trong các block dữ liệu trông như dữ liệu ngẫu nhiên. Khi bị ép buộc, bạn cung cấp Mật Khẩu Ngoài (Outer Password), mở ra một hệ điều hành nghi binh chứa các tài liệu vô thưởng vô phạt. Đối phương hoàn toàn không thể chứng minh toán học rằng có sự tồn tại của ổ đĩa ẩn bên trong!"
                ),
                (
                    "Cấu Trúc Khối Mã Hóa Chuẩn LUKS Trên Linux",
                    "Trên các hệ điều hành máy chủ và bảo mật Linux, LUKS (Linux Unified Key Setup) là chuẩn mã hóa khối số 1. LUKS cung cấp phần tiêu đề (LUKS Header) hỗ trợ tới 8 khe cắm khóa (Key Slots), cho phép nhiều người dùng hoặc các khóa sao lưu (Backup Keys) khác nhau cùng mở khóa ổ đĩa."
                )
            ],
            "Kịch bản tấn công: Phá Hủy Tiêu Đề LUKS (LUKS Header Destruction): Nếu tiêu đề LUKS bị ghi đè hoặc hỏng, toàn bộ dữ liệu trên ổ cứng sẽ bị mất vĩnh viễn không thể khôi phục dù bạn có đúng mật khẩu. Do đó, việc sao lưu tệp tiêu đề (Header Backup) vào một thiết bị lưu trữ an toàn độc lập là yêu cầu sống còn.",
            "Thực hành tạo và mã hóa một phân vùng bằng công cụ cryptsetup chuẩn LUKS trên Linux:",
            ("bash", """# 1. Tạo tệp đệm 1GB giả lập ổ đĩa
dd if=/dev/urandom of=/tmp/secure_volume.img bs=1M count=1024

# 2. Định dạng tệp đệm thành phân vùng mã hóa LUKS2
sudo cryptsetup luksFormat --type luks2 /tmp/secure_volume.img

# 3. Mở khóa phân vùng mã hóa và gán vào thiết bị ảo
sudo cryptsetup open /tmp/secure_volume.img my_encrypted_drive

# 4. Tạo hệ thống tệp ext4 và gắn kết vào thư mục làm việc
sudo mkfs.ext4 /dev/mapper/my_encrypted_drive
sudo mkdir -p /mnt/secure
sudo mount /dev/mapper/my_encrypted_drive /mnt/secure
echo "Ổ đĩa mã hóa đã sẵn sàng sử dụng tại /mnt/secure!" """),
            ["Luôn sao lưu tệp tiêu đề (LUKS Header) của ổ đĩa mã hóa.", "Tuyệt đối không sử dụng mật khẩu ngắn hoặc dễ đoán."],
            ["FDE bảo vệ dữ liệu khi thiết bị tắt máy (Data at Rest).", "Cơ chế Plausible Deniability trong VeraCrypt bảo vệ người dùng trước sự cưỡng bức tra khảo.", "LUKS là chuẩn mã hóa đĩa hàng đầu trên Linux."],
            [
                {"question": "Cơ chế nào trong VeraCrypt cho phép người dùng phủ nhận sự tồn tại của dữ liệu nhạy cảm khi bị ép cung?", "type": "MULTIPLE_CHOICE", "options": ["Hidden Volume (Ổ đĩa ẩn)", "Quick Format", "RAM Wipe", "Auto-Delete"], "correct_index": 0, "explanation": "Hidden Volume cung cấp tính năng Plausible Deniability."},
                {"question": "Chuẩn mã hóa khối nào là tiêu chuẩn mặc định trên các bản phân phối Linux?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["LUKS", "luks"]}], "explanation": "Linux Unified Key Setup (LUKS)."},
                {"question": "Mã hóa FDE có thể bảo vệ dữ liệu khi máy tính đang bật và mở khóa?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. FDE chỉ bảo vệ dữ liệu khi tắt máy (Data at Rest)."}
            ]
        ),
        (
            6,
            "Bài 2.6: Kỹ Thuật Tiêu Hủy Dữ Liệu An Toàn (Secure File Shredding) & Chống Phục Hồi Pháp Y",
            "Mổ xẻ cơ chế lưu trữ của hệ thống tệp tin, sự vô nghĩa của việc xóa file thông thường và làm chủ các kỹ thuật tiêu hủy dữ liệu tiêu chuẩn quân sự.",
            "https://www.youtube.com/watch?v=1-FyyhpW-t8",
            [
                "Hiểu rõ cơ chế xóa file của hệ điều hành (chỉ xóa con trỏ Inode/MFT, không xóa dữ liệu thực).",
                "Nắm vững các thuật toán tiêu hủy dữ liệu: Gutmann, DoD 5220.22-M và ghi đè ngẫu nhiên.",
                "Thực hành sử dụng công cụ `shred`, `srm` và quản lý lệnh TRIM trên ổ cứng thể rắn SSD."
            ],
            [
                (
                    "Sự Thật Về Lệnh Xóa Tệp Tin (File Deletion Illusion)",
                    "Hầu hết người dùng máy tính đều tin rằng khi nhấn phím 'Delete' và dọn sạch 'Thùng rác' (Recycle Bin), tệp tin đã bị xóa vĩnh viễn khỏi ổ đĩa. Đây là một ảo tưởng cực kỳ nguy hiểm trong an ninh số! Về mặt kỹ thuật, hệ điều hành (như Windows NTFS hay Linux Ext4) hoàn toàn không hề ghi đè hay xóa các byte dữ liệu thực tế trên bề mặt đĩa. Hệ điều hành chỉ đơn giản là đánh dấu con trỏ tệp tin (Inode trong Linux hoặc Master File Table entry trong NTFS) là 'đã giải phóng'. Các khối dữ liệu thực tế vẫn nằm nguyên vẹn trên đĩa cho đến khi có một tệp tin khác ghi đè lên. Bất kỳ phần mềm khôi phục pháp y nào (như Autopsy, Recuva hay Photorec) đều có thể phục hồi lại 100% tệp tin chỉ trong vài giây."
                ),
                (
                    "Các Thuật Toán Tiêu Hủy Tiêu Chuẩn Quân Sự",
                    "Để xóa dữ liệu thực sự, phần mềm phải ghi đè các byte dữ liệu mới lên đúng các khối đĩa vật lý chứa tệp cũ: Thuật toán DoD 5220.22-M của Bộ Quốc phòng Mỹ: Ghi đè 3 lượt (Lượt 1: Ghi số 0; Lượt 2: Ghi số 1; Lượt 3: Ghi các byte ngẫu nhiên). Thuật toán Peter Gutmann: Ghi đè tới 35 lượt với các chuỗi mẫu phức tạp nhằm triệt tiêu hiện tượng từ dư (Magnetic Remanence) trên các ổ cứng cơ học HDD đời cũ. Trong thực tiễn hiện đại, việc ghi đè ngẫu nhiên 3 đến 7 lượt bằng dữ liệu ngẫu nhiên `/dev/urandom` là hoàn toàn đủ để ngăn chặn mọi kính hiển vi lực từ (MFM) của các phòng thí nghiệm pháp y tối tân nhất."
                ),
                (
                    "Thách Thức Với Ổ Đĩa Thể Rắn SSD & Cơ Chế Wear Leveling",
                    "Trên ổ đĩa SSD hiện đại sử dụng bộ nhớ flash NAND, các lệnh ghi đè thông thường như `shred` không còn đảm bảo hiệu quả 100%. Lý do là vi điều khiển (controller) của SSD sử dụng thuật toán Cân bằng hao mòn (Wear Leveling): khi bạn yêu cầu ghi đè lên một sector, controller sẽ ghi dữ liệu mới vào một ô nhớ flash mới và giữ nguyên ô nhớ cũ trong danh sách chờ giải phóng. Để tiêu hủy dữ liệu an toàn trên SSD, giải pháp duy nhất là: Mã hóa toàn bộ ổ đĩa từ ban đầu, hoặc thực hiện lệnh xả điện toàn diện **ATA Secure Erase / NVMe Format**."
                )
            ],
            "Kịch bản phục hồi pháp y số: Chuyên viên điều tra thu giữ ổ cứng bị xóa nhanh, sử dụng công cụ `ddrescue` để trích xuất toàn bộ ảnh đĩa nhị phân thô (Raw Bitstream Image), sau đó chạy kỹ thuật Khắc tệp tin (File Carving) dựa trên phần tiêu đề Magic Bytes (như `%PDF` cho tài liệu PDF, `FF D8 FF` cho ảnh JPEG) để khôi phục toàn bộ tài liệu.",
            "Thực hành tiêu hủy tệp tin an toàn bằng lệnh shred trên Linux:",
            ("bash", """# 1. Tạo tệp tin chứa dữ liệu nhạy cảm giả lập
echo "Thong tin mat can tieu huy" > /tmp/confidential.txt

# 2. Tiêu hủy tệp tin bằng lệnh shred:
# -u: Cắt ngắn và xóa file sau khi ghi đè
# -z: Lượt cuối cùng ghi đè bằng số 0 để che giấu dấu vết shredding
# -n 3: Ghi đè 3 lượt ngẫu nhiên
shred -u -z -n 3 /tmp/confidential.txt

# 3. Kiểm tra xem tệp tin còn tồn tại không
ls -l /tmp/confidential.txt 2>/dev/null || echo "Tệp tin đã bị tiêu hủy hoàn toàn!" """),
            ["Không bao giờ tin tưởng vào lệnh xóa thông thường (rm hoặc Delete).", "Đối với ổ đĩa SSD, luôn kích hoạt mã hóa toàn ổ đĩa FDE ngay từ ngày đầu sử dụng."],
            ["Xóa file thông thường chỉ xóa con trỏ chỉ mục, dữ liệu thực vẫn còn nguyên trên đĩa.", "Thuật toán tiêu hủy ghi đè dữ liệu ngẫu nhiên nhiều lượt để chống khôi phục pháp y.", "Ổ đĩa SSD đòi hỏi kỹ thuật ATA Secure Erase do cơ chế Wear Leveling."],
            [
                {"question": "Khi xóa file bằng lệnh rm thông thường trên Linux, dữ liệu thực tế trên ổ đĩa sẽ như thế nào?", "type": "MULTIPLE_CHOICE", "options": ["Bị xóa sạch vĩnh viễn", "Vẫn còn nguyên vẹn trên đĩa, chỉ có con trỏ chỉ mục bị xóa", "Bị mã hóa lại", "Bị nén nhỏ lại"], "correct_index": 1, "explanation": "Dữ liệu thực vẫn còn nguyên vẹn cho đến khi bị ghi đè."},
                {"question": "Lệnh nào trên Linux được thiết kế chuyên biệt để ghi đè dữ liệu ngẫu nhiên tiêu hủy tệp tin?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["shred", "srm"]}], "explanation": "Lệnh shred."},
                {"question": "Thuật toán Wear Leveling trên ổ SSD có thể khiến lệnh ghi đè file thông thường không thể xóa triệt để ô nhớ cũ?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Wear Leveling ghi dữ liệu mới sang ô nhớ khác."}
            ]
        ),
        (
            7,
            "Bài 2.7: Rủi Ro Thực Thi JavaScript Trên Dark Web & Cách Vô Hiệu Hóa Triệt Để",
            "Mổ xẻ các kỹ thuật khai thác lỗ hổng trình duyệt thông qua JavaScript, kỹ thuật Canvas Fingerprinting và cách khóa chặn hoàn toàn mã thực thi.",
            "https://www.youtube.com/watch?v=U2-JPqrALsA",
            [
                "Nắm vững các mối đe dọa an ninh bắt nguồn từ JavaScript trên các trang web .onion.",
                "Giải mã kỹ thuật nhận diện người dùng qua HTML5 Canvas và AudioContext Fingerprinting.",
                "Thực hành cấu hình vô hiệu hóa JavaScript triệt để trên Tor Browser và NoScript."
            ],
            [
                (
                    "JavaScript: Con Ngựa Thành Troy Trên Không Gian Ngầm",
                    "Trong phát triển web thông thường, JavaScript là linh hồn tạo nên các trải nghiệm tương tác mượt mà. Tuy nhiên, trên không gian Darknet, JavaScript là kẻ thù số 1 của quyền riêng tư. Khi bạn cho phép một trang web Darknet thực thi mã JavaScript, bạn đang cho phép một máy chủ nặc danh hoàn toàn xa lạ chạy mã nguồn trực tiếp bên trong tiến trình trình duyệt trên máy tính của bạn. Mọi API của trình duyệt đều có thể bị vũ khí hóa để thăm dò hệ thống."
                ),
                (
                    "Kỹ Thuật Canvas & AudioContext Fingerprinting",
                    "Làm thế nào một trang web có thể nhận dạng bạn mà không cần dùng cookie? Kỹ thuật Canvas Fingerprinting: Đoạn mã JavaScript âm thầm ra lệnh cho trình duyệt vẽ một đoạn văn bản hoặc hình khối 3D ẩn bằng thẻ HTML5 `<canvas>`. Do mỗi loại card đồ họa (GPU), driver màn hình và hệ điều hành có cách khử răng cưa và xử lý điểm ảnh khác nhau ở mức độ vi mô, hình ảnh vẽ ra sẽ tạo ra một mã băm (Hash) độc nhất cho máy tính của bạn. Kỹ thuật AudioContext Fingerprinting: JavaScript tạo ra một tín hiệu âm thanh tần số thấp qua Web Audio API và đo đạc cách thức card âm thanh xử lý tín hiệu đó để tạo ra dấu vân tay phần cứng."
                ),
                (
                    "Khóa Chặn Tuyệt Đối Bằng Tor Safest Mode & NoScript",
                    "Để triệt tiêu hoàn toàn bề mặt tấn công này, người dùng bắt buộc phải chuyển mức bảo mật của Tor Browser sang chế độ **Safest**. Khi ở chế độ Safest, tiện ích NoScript tích hợp sẵn sẽ vô hiệu hóa 100% JavaScript trên toàn bộ các trang web, khóa chặn các thẻ nhúng đa phương tiện độc hại."
                )
            ],
            "Kịch bản tấn công: Khai Thác Lỗ Hổng Tràn Bộ Đệm JavaScript Engine: Tin tặc thiết kế các mảng dữ liệu đặc biệt (Array Buffer) trong JavaScript để kích hoạt lỗi giải phóng bộ nhớ (Use-After-Free) trong trình thông dịch SpiderMonkey của Firefox, chiếm quyền điều khiển con trỏ lệnh EIP/RIP và thực thi shellcode gửi IP thật về máy chủ tấn công.",
            "Thực hành kiểm tra xem JavaScript có đang hoạt động trên trình duyệt hay không bằng thẻ HTML noscript:",
            ("html", """<!-- Đoạn mã HTML kiểm tra trạng thái JavaScript -->
<!DOCTYPE html>
<html>
<head><title>Kiểm tra JavaScript</title></head>
<body>
    <script>
        document.write("<h2 style='color:red;'>CẢNH BÁO: JavaScript đang BẬT! Bạn đang đối mặt với rủi ro de-anonymization!</h2>");
    </script>
    <noscript>
        <h2 style='color:green;'>AN TOÀN: JavaScript đã bị VÔ HIỆU HÓA hoàn toàn.</h2>
    </noscript>
</body>
</html>"""),
            ["Không bao giờ bật lại JavaScript chỉ vì một trang web Darknet yêu cầu điều đó.", "Hầu hết các trang web Darknet chân chính đều hỗ trợ hoạt động hoàn hảo khi tắt JavaScript."],
            ["JavaScript là vector tấn công bóc trần danh tính phổ biến nhất trên Darknet.", "Canvas Fingerprinting đo đạc sự khác biệt vi mô của GPU để lập hồ sơ người dùng.", "Chế độ Safest của Tor Browser là lựa chọn duy nhất đảm bảo an toàn."],
            [
                {"question": "Kỹ thuật nào sử dụng thẻ HTML5 canvas để đo đạc sự khác biệt trong render đồ họa nhằm nhận diện người dùng?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Canvas Fingerprinting", "canvas fingerprinting"]}], "explanation": "Canvas Fingerprinting."},
                {"question": "Bật JavaScript khi duyệt Darknet có an toàn không?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. JavaScript tạo ra rủi ro bị bóc trần IP rất cao."},
                {"question": "Tiện ích mở rộng nào được tích hợp sẵn trong Tor Browser để kiểm soát và chặn mã JavaScript?", "type": "MULTIPLE_CHOICE", "options": ["AdBlock", "NoScript", "Tampermonkey", "Postman"], "correct_index": 1, "explanation": "Tiện ích NoScript."}
            ]
        ),
        (
            8,
            "Bài 2.8: Tẩy Sạch Siêu Dữ Liệu (Metadata & EXIF Stripping) Trước Khi Phát Tán Tệp Tin",
            "Giải mã các loại siêu dữ liệu ẩn giấu trong tệp tin hình ảnh, PDF, văn bản Office và thực hành sử dụng bộ công cụ MAT2 để làm sạch triệt để.",
            "https://www.youtube.com/watch?v=tu-CbGRuS-E",
            [
                "Hiểu rõ khái niệm siêu dữ liệu (Metadata) và cấu trúc EXIF trong tệp tin ảnh số.",
                "Nhận diện các hiểm họa rò rỉ tọa độ GPS, số serial thiết bị và tên tác giả tài liệu.",
                "Thực hành sử dụng công cụ Metadata Anonymisation Toolkit v2 (MAT2) trên Linux."
            ],
            [
                (
                    "Bản Chất Kỹ Thuật Của Siêu Dữ Liệu (Metadata)",
                    "Siêu dữ liệu (Metadata) là 'dữ liệu về dữ liệu'. Khi bạn chụp một bức ảnh bằng điện thoại thông minh hoặc soạn thảo một tài liệu Word, phần mềm không chỉ lưu trữ hình ảnh hoặc nội dung chữ mà còn tự động nhúng vào bên trong tệp hàng trăm thông số ẩn: Dữ liệu EXIF trong ảnh: Tọa độ GPS chính xác từng mét nơi bức ảnh được chụp, ngày giờ chụp, dòng máy điện thoại (ví dụ: iPhone 15 Pro), số serial camera, thông số phơi sáng. Siêu dữ liệu trong tài liệu (PDF, DOCX): Tên thật của người đăng ký bản quyền phần mềm, tên tài khoản máy tính, phiên bản hệ điều hành, thời gian chỉnh sửa và lịch sử các phiên bản cũ."
                ),
                (
                    "Những Vụ Án Bị Bắt Giữ Vì Siêu Dữ Liệu",
                    "Lịch sử an ninh mạng ghi nhận rất nhiều hacker khét tiếng bị bắt chỉ vì một bức ảnh: Năm 2012, hacker Higinio O. Ochoa của nhóm CabinCrue đã đăng tải một bức ảnh chụp bạn gái kèm thông điệp chế nhạo cảnh sát lên Twitter. Bức ảnh được chụp bằng điện thoại thông minh và chưa hề được tẩy dữ liệu EXIF. Cục điều tra FBI chỉ cần đọc tọa độ GPS nhúng trong bức ảnh là có thể xác định ngay ngôi nhà của đối tượng tại Texas và bắt giữ hắn ngay hôm sau."
                ),
                (
                    "Công Cụ Tẩy Sạch Siêu Dữ Liệu Chuyên Dụng: MAT2",
                    "Các công cụ xóa thông thường thường bỏ sót nhiều trường dữ liệu phức tạp. Để làm sạch hoàn toàn, cộng đồng bảo mật sử dụng công cụ **MAT2 (Metadata Anonymisation Toolkit v2)** - công cụ tiêu chuẩn được tích hợp sẵn trong Tails OS. MAT2 hỗ trợ quét và xóa bỏ siêu dữ liệu của hàng chục định dạng tệp tin: ảnh (PNG, JPEG), tài liệu (PDF, DOCX, ODT), âm thanh (MP3, FLAC) và video mà không làm suy giảm chất lượng dữ liệu."
                )
            ],
            "Kịch bản điều tra pháp y siêu dữ liệu: Điều tra viên sử dụng lệnh `exiftool` để quét hàng loạt tệp tin được đăng tải trên diễn đàn ngầm, trích xuất chuỗi serial máy ảnh hoặc tên tác giả tài liệu để kết nối các tài liệu khác nhau về cùng một đối tượng tình nghi.",
            "Thực hành trích xuất và tẩy sạch siêu dữ liệu bằng exiftool và mat2 trên dòng lệnh Linux:",
            ("bash", """# 1. Kiểm tra siêu dữ liệu ẩn trong một bức ảnh bằng exiftool
exiftool sample_image.jpg

# 2. Cài đặt và sử dụng công cụ MAT2 để làm sạch siêu dữ liệu
sudo apt install -y mat2

# 3. Tiến hành tẩy sạch siêu dữ liệu của tệp tin
mat2 sample_image.jpg

# 4. Kiểm tra lại tệp tin đã làm sạch (sample_image.cleaned.jpg)
exiftool sample_image.cleaned.jpg | grep -iE "GPS|Camera|Author|Model"
echo "Nếu không có kết quả trả về, tệp tin đã sạch siêu dữ liệu an toàn!" """),
            ["Luôn chạy công cụ tẩy siêu dữ liệu trước khi tải bất kỳ tệp tin nào lên không gian mạng.", "Cần chụp ảnh màn hình (screenshot) thay vì gửi tệp gốc nếu không chắc chắn về siêu dữ liệu."],
            ["Siêu dữ liệu EXIF có thể chứa tọa độ GPS và thông tin thiết bị chụp ảnh.", "MAT2 là công cụ chuẩn quốc tế để làm sạch siêu dữ liệu của nhiều định dạng tệp.", "Nhiều tội phạm mạng bị bắt giữ chỉ vì quên xóa dữ liệu GPS trong ảnh chụp."],
            [
                {"question": "Dữ liệu EXIF trong bức ảnh chụp bằng điện thoại có thể để lộ thông tin nhạy cảm nào sau đây?", "type": "MULTIPLE_CHOICE", "options": ["Tọa độ vị trí GPS chính xác", "Số dư tài khoản ngân hàng", "Mật khẩu wifi", "Địa chỉ MAC của router"], "correct_index": 0, "explanation": "Dữ liệu EXIF thường lưu tọa độ vị trí GPS nơi chụp ảnh."},
                {"question": "Công cụ làm sạch siêu dữ liệu tiêu chuẩn được tích hợp trong Tails OS có tên là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["MAT2", "mat2"]}], "explanation": "Metadata Anonymisation Toolkit v2 (MAT2)."},
                {"question": "Chuyển ảnh sang dạng tệp PDF sẽ tự động xóa sạch dữ liệu EXIF của bức ảnh đó?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Dữ liệu EXIF vẫn có thể được nhúng nguyên vẹn bên trong tệp PDF."}
            ]
        ),
        (
            9,
            "Bài 2.9: Kỹ Thuật Kết Hợp Tor Qua VPN: Phân Biệt Tor-over-VPN và VPN-over-Tor",
            "Mổ xẻ hai mô hình định tuyến lai ghép phức tạp: Lợi thế kỹ thuật, nguy cơ rò rỉ và khuyến nghị an ninh từ Tor Project.",
            "https://www.youtube.com/watch?v=fyySsmKsTlM",
            [
                "Phân biệt rạch ròi giữa mô hình Tor-over-VPN và VPN-over-Tor.",
                "Hiểu rõ ưu nhược điểm và mô hình tin cậy (Trust Model) của từng phương thức.",
                "Đánh giá rủi ro bị nhà cung cấp dịch vụ VPN ghi nhật ký (logging) và bán đứng người dùng."
            ],
            [
                (
                    "Mô Hình 1: Tor-over-VPN (Client -> VPN -> Tor -> Internet)",
                    "Trong mô hình này, người dùng kết nối tới dịch vụ VPN trước, sau đó mới khởi chạy Tor Browser để truyền dữ liệu. Ưu điểm: Nhà cung cấp mạng Internet địa phương (ISP) chỉ nhìn thấy bạn đang kết nối tới máy chủ VPN, hoàn toàn không biết bạn đang sử dụng mạng Tor. Guard Node của Tor chỉ nhìn thấy địa chỉ IP của máy chủ VPN, không biết IP thật của bạn. Nhược điểm: Bạn chuyển toàn bộ sự tin tưởng từ ISP sang nhà cung cấp VPN. Nếu nhà cung cấp VPN âm thầm ghi nhật ký kết nối (Connection Logs), họ có thể liên kết danh tính của bạn với thời điểm kết nối vào mạng Tor."
                ),
                (
                    "Mô Hình 2: VPN-over-Tor (Client -> Tor -> VPN -> Internet)",
                    "Trong mô hình này, người dùng kết nối vào mạng Tor trước, sau đó thiết lập đường hầm VPN đi xuyên qua Tor ra Internet. Ưu điểm: Exit Node của Tor không thể nhìn thấy lưu lượng thực tế vì dữ liệu đã được mã hóa bởi VPN. Các trang web chặn mạng Tor sẽ cho phép bạn truy cập vì địa chỉ IP cuối cùng là IP của máy chủ VPN. Nhược điểm: Cấu hình kỹ thuật cực kỳ phức tạp và dễ gặp lỗi rò rỉ dữ liệu. Hơn thế nữa, phương thức thanh toán tiền cho dịch vụ VPN đó có thể trở thành sợi dây truy vết danh tính thật của bạn."
                ),
                (
                    "Khuyến Nghị Chính Thức Từ Tor Project",
                    "Trái ngược với các chiến dịch quảng cáo rầm rộ của các công ty VPN thương mại, Tor Project chính thức khuyến nghị: **Hầu hết người dùng thông thường KHÔNG NÊN sử dụng VPN cùng với Tor**. Việc kết hợp VPN tạo thêm một điểm lỗi trung tâm (Single Point of Failure), tăng độ trễ mạng và đưa một bên thứ ba thương mại có khả năng ghi log vào chuỗi bảo vệ vốn đã rất an toàn của Tor."
                )
            ],
            "Kịch bản tấn công nhà cung cấp VPN: Vụ Án PureVPN & Lời Hứa 'No Logs' Giả Tạo: Năm 2017, dịch vụ PureVPN quảng cáo chính sách 'Không lưu nhật ký' (No-Logs Policy) nhưng khi FBI gửi trát hầu tòa yêu cầu cung cấp dữ liệu về một nghi phạm mạng, PureVPN đã lập tức bàn giao đầy đủ nhật ký địa chỉ IP nguồn và thời gian kết nối, dẫn đến việc nghi phạm bị bắt giữ ngay lập tức.",
            "Thực hành kiểm tra địa chỉ IP đầu vào và đầu ra khi sử dụng Tor kết hợp VPN:",
            ("bash", """# Kiểm tra IP công cộng trước và sau khi bật các tầng proxy
echo "IP hiện tại của hệ thống:"
curl -s https://icanhazip.com

# Kiểm tra kết nối định tuyến Tor qua proxy nội bộ
curl -s --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip"""),
            ["Tuyệt đối không tin tưởng mù quáng vào các lời quảng cáo 'No-Logs' của các dịch vụ VPN thương mại.", "Không thanh toán dịch vụ VPN bằng thẻ ngân hàng chính chủ nếu muốn sử dụng cho các mục đích nhạy cảm."],
            ["Tor-over-VPN che giấu việc dùng Tor với nhà mạng ISP nhưng đặt niềm tin vào nhà cung cấp VPN.", "VPN-over-Tor giúp vượt qua các bộ lọc chặn Tor nhưng cấu hình rất phức tạp.", "Tor Project khuyến nghị người dùng nên sử dụng Tor độc lập mà không cần VPN."],
            [
                {"question": "Trong mô hình Tor-over-VPN, nhà cung cấp dịch vụ mạng ISP sẽ nhìn thấy bạn đang kết nối tới đâu?", "type": "MULTIPLE_CHOICE", "options": ["Nhìn thấy bạn kết nối tới Guard Node của Tor", "Chỉ nhìn thấy kết nối tới máy chủ VPN", "Nhìn thấy trang web đích cuối cùng", "Không nhìn thấy bất kỳ gói tin nào"], "correct_index": 1, "explanation": "ISP chỉ nhìn thấy kết nối tới máy chủ VPN."},
                {"question": "Tor Project có khuyến nghị người dùng đại trà luôn luôn phải bật VPN khi sử dụng Tor không?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Tor Project khuyến nghị phần lớn người dùng không cần thiết và không nên dùng VPN cùng Tor."},
                {"question": "Mô hình nào cho phép người dùng truy cập các website chặn Tor bằng cách dùng IP máy chủ VPN ở trạm ra cuối cùng?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["VPN-over-Tor", "vpn-over-tor"]}], "explanation": "VPN-over-Tor."}
            ]
        ),
        (
            10,
            "Bài 2.10: Phân Tích Các Sai Lầm OPSEC Kinh Điển: Bài Học Từ Sabu Và Jeremy Hammond",
            "Mổ xẻ vụ án nhóm tin tặc LulzSec/Anonymous: Cách FBI cài cắm chỉ điểm viên Sabu (Hector Monsegur) để triệt phá hacker thiên tài Jeremy Hammond.",
            "https://www.youtube.com/watch?v=seB4a3Oph34",
            [
                "Nghiên cứu quá trình hoạt động của nhóm tin tặc LulzSec và cuộc tấn công Stratfor.",
                "Phân tích sự thỏa hiệp của Hector Monsegur (Sabu) và kỹ thuật giám sát nguồn tin nội gián của FBI.",
                "Rút ra các bài học đắt giá về niềm tin trên mạng, quản lý danh tính số và an toàn truyền thông."
            ],
            [
                (
                    "Sự Trỗi Dậy Của LulzSec & Huyền Thoại Hacker 'Sabu'",
                    "Năm 2011, nhóm tin tặc LulzSec (nhánh tinh nhuệ của Anonymous) do một hacker khét tiếng mang biệt danh 'Sabu' lãnh đạo đã thực hiện hàng loạt vụ tấn công mạng chấn động nhắm vào FBI, CIA, Sony Pictures, Thượng viện Mỹ. Sabu được coi là một huyền thoại ngầm về an ninh và kỹ năng khai thác lỗ hổng. Tuy nhiên, đằng sau bàn phím, Sabu tên thật là Hector Monsegur, sống tại một căn hộ nhỏ ở New York. Chỉ một lần duy nhất sơ suất quên bật Tor khi đăng nhập vào máy chủ IRC, địa chỉ IP thật của Monsegur đã bị FBI ghi nhận. Đặc vụ FBI ập vào nhà lúc nửa đêm, đưa ra mức án 120 năm tù và yêu cầu Monsegur trở thành nội gián bí mật cho chính phủ."
                ),
                (
                    "Cái Bẫy Đưa Jeremy Hammond Vào Lưới",
                    "Sau khi bị FBI kiểm soát 100%, Monsegur tiếp tục đóng vai trò thủ lĩnh trên các kênh chat IRC mã hóa ngầm. Mục tiêu lớn nhất mà FBI nhắm tới là **Jeremy Hammond (biệt danh 'Anarchaos')** - một trong những hacker xuất chúng nhất thời điểm đó. Hammond đã thực hiện vụ tấn công lịch sử vào công ty tình báo tư nhân Stratfor, đánh cắp hàng triệu email mật và dữ liệu thẻ tín dụng. Monsegur (dưới sự chỉ đạo của FBI) đã cung cấp cho Hammond một máy chủ lưu trữ dữ liệu tại nước ngoài để chứa dữ liệu bị đánh cắp. Máy chủ đó thực chất do chính FBI bí mật kiểm soát và ghi nhận toàn bộ chứng cứ phạm tội!"
                ),
                (
                    "Sai Lầm OPSEC Chết Người Của Jeremy Hammond",
                    "Mặc dù Hammond luôn sử dụng Tor và mã hóa tệp tin cẩn thận, hắn đã phạm 3 sai lầm OPSEC không thể cứu vãn: 1. Đặt niềm tin mù quáng vào một nhân vật ảo trên mạng: Hammond tin tưởng Sabu tuyệt đối mà không có cơ chế xác minh tính độc lập của kênh liên lạc. 2. Thói quen sử dụng mật khẩu yếu trên máy tính cá nhân: Mật khẩu mã hóa ổ đĩa TrueCrypt trên laptop cá nhân của Hammond là `Cheico` - tên chú mèo cưng của hắn! Các chuyên gia pháp y FBI đã giải mã toàn bộ ổ đĩa chỉ sau vài giờ tấn công từ điển (Dictionary Attack). 3. Không tách biệt danh tính thực và ảo: Các bài viết chính trị ngoài đời của Hammond có giọng văn và tư tưởng trùng khớp 100% với các thông điệp của Anarchaos trên mạng."
                )
            ],
            "Bài học an ninh sâu sắc: Trong thế giới ngầm, kẻ thù nguy hiểm nhất không phải là hệ thống phòng thủ mạng của đối phương, mà là người đồng đội thân cận nhất bị thỏa hiệp. Nguyên tắc Zero Trust bắt buộc bạn không được phép tin tưởng tuyệt đối bất kỳ ai trên không gian mạng.",
            "Thực hành kiểm tra độ mạnh của mật khẩu mã hóa bằng script Python đánh giá entropy toán học:",
            ("python", """import math

def calculate_entropy(password):
    pool = 0
    if any(c.islower() for c in password): pool += 26
    if any(c.isupper() for c in password): pool += 26
    if any(c.isdigit() for c in password): pool += 10
    if any(not c.isalnum() for c in password): pool += 32
    if pool == 0: return 0
    return len(password) * math.log2(pool)

# So sánh mật khẩu của Jeremy Hammond ("Cheico") và mật khẩu chuẩn an ninh
pw1 = "Cheico"
pw2 = "correct-horse-battery-staple-99$"
print(f"Entropy của 'Cheico': {calculate_entropy(pw1):.2f} bits (Quá yếu, bị bẻ gãy ngay)")
print(f"Entropy của mật khẩu chuẩn: {calculate_entropy(pw2):.2f} bits (Siêu an toàn)")"""),
            ["Không bao giờ sử dụng tên thú cưng, người thân hoặc ngày sinh làm mật khẩu mã hóa ổ đĩa.", "Tuyệt đối không tin tưởng mù quáng vào bất kỳ ai trên mạng Internet; luôn áp dụng nguyên tắc Zero Trust."],
            ["Sabu bị bắt do một lần sơ suất không bật Tor khi đăng nhập IRC và trở thành nội gián FBI.", "Jeremy Hammond bị bắt do đặt mật khẩu ổ đĩa yếu và tin tưởng mù quáng vào Sabu.", "Phân tích văn phong (Stylometry) có thể liên kết danh tính đời thực với tài khoản ảo."],
            [
                {"question": "Hector Monsegur (Sabu) bị FBI phát hiện địa chỉ IP thật do sơ suất kỹ thuật nào?", "type": "MULTIPLE_CHOICE", "options": ["Bị nhiễm virus trojan", "Quên bật Tor một lần duy nhất khi đăng nhập IRC", "Bị lộ thẻ ngân hàng", "Bị máy tính bốc cháy"], "correct_index": 1, "explanation": "Sơ suất đăng nhập IRC bằng IP thật một lần duy nhất."},
                {"question": "Mật khẩu mã hóa ổ đĩa TrueCrypt của Jeremy Hammond bị FBI giải mã dễ dàng vì lý do gì?", "type": "MULTIPLE_CHOICE", "options": ["Đặt mật khẩu theo tên thú cưng quá ngắn và dễ đoán", "Sử dụng mã hóa lỗi thời", "Bị rò rỉ trên mạng", "Bị FBI dùng siêu máy tính lượng tử"], "correct_index": 0, "explanation": "Đặt mật khẩu 'Cheico' là tên mèo cưng, bị bẻ khóa từ điển nhanh chóng."},
                {"question": "Trong không gian mạng ngầm, người dùng nên tin tưởng tuyệt đối vào các đồng đội thân thiết lâu năm?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Nguyên tắc Zero Trust: Bất kỳ ai cũng có thể bị cơ quan an ninh thỏa hiệp để trở thành nội gián."}
            ]
        ),
        (
            11,
            "Bài 2.11: Giao Thức Liên Lạc Ẩn Danh TorChat & Bảo Mật Tài Khoản Chống Điều Tra Số",
            "Nghiên cứu các giao thức nhắn tin ngang hàng ẩn danh (TorChat, Briar, Cwtch), nguyên lý End-to-End Encryption và các biện pháp bảo mật tài khoản tuyệt đối.",
            "https://www.youtube.com/watch?v=QRYzre4bf7I",
            [
                "Hiểu rõ kiến trúc nhắn tin ngang hàng (P2P Messaging) qua Tor Hidden Services không cần máy chủ trung tâm.",
                "Phân tích giao thức bảo vệ cuộc trò chuyện Off-the-Record (OTR) và Signal Protocol.",
                "Thực hành xây dựng quy trình bảo vệ tài khoản số và kỹ thuật chống điều tra pháp y hiện đại."
            ],
            [
                (
                    "Sự Nguy Hiểm Của Các Ứng Dụng Nhắn Tin Tập Trung",
                    "Hầu hết các ứng dụng nhắn tin phổ biến (Telegram, WhatsApp, Signal) đều phụ thuộc vào máy chủ trung tâm để điều phối tin nhắn. Ngay cả khi tin nhắn được mã hóa đầu cuối (E2EE), máy chủ trung tâm vẫn lưu trữ toàn bộ Siêu dữ liệu liên lạc (Metadata): Ai đang nói chuyện với ai, vào thời điểm nào, tần suất bao nhiêu lần và kích thước tin nhắn là bao nhiêu. Đối với cơ quan điều tra, siêu dữ liệu này hoàn toàn đủ để vẽ nên mạng lưới quan hệ xã hội của một tổ chức mà không cần đọc nội dung tin nhắn."
                ),
                (
                    "Kiến Trúc P2P Không Máy Chủ Của TorChat & Briar",
                    "Để triệt tiêu hoàn toàn rủi ro siêu dữ liệu, các giao thức nhắn tin ẩn danh như TorChat, Briar và Cwtch hoạt động theo mô hình hoàn toàn phân tán: Mỗi người dùng khi cài đặt ứng dụng sẽ tự động khởi chạy một **Tor Onion Service v3 cục bộ** trên máy của mình. ID liên lạc của bạn chính là địa chỉ `.onion` 56 ký tự của bạn. Khi Alice nhắn tin cho Bob, máy của Alice thiết lập một kết nối Tor-to-Tor trực tiếp tới Onion Service của Bob thông qua Rendezvous Point. Hoàn toàn không có bất kỳ máy chủ trung tâm nào tồn tại; không ai có thể thu thập siêu dữ liệu liên lạc."
                ),
                (
                    "Mã Hóa Chuyển Tiếp Hoàn Hảo (Perfect Forward Secrecy - PFS)",
                    "Các giao thức nhắn tin an toàn hiện đại áp dụng thuật toán Double Ratchet (như trong Signal và OTR) để đảm bảo tính năng Perfect Forward Secrecy: Mỗi tin nhắn được gửi đi đều sử dụng một khóa mã hóa dùng một lần mới tinh. Ngay sau khi tin nhắn được giải mã, khóa đó sẽ bị hủy vĩnh viễn khỏi bộ nhớ. Nếu kẻ tấn công thu giữ được máy tính của bạn và giải mã được tin nhắn của ngày hôm nay, hắn vẫn hoàn toàn không thể giải mã các tin nhắn trong quá khứ."
                )
            ],
            "Kịch bản tấn công: Khai Thác Kênh Phụ Phân Tích Kích Thước Tin Nhắn (Traffic Shaping Attacks): Kẻ tấn công quan sát kích thước của các gói tin mã hóa đi qua mạng Tor để đoán xem người dùng đang gõ phím, gửi ảnh hay truyền tệp tin. Các ứng dụng hiện đại như Briar áp dụng cơ chế đệm dữ liệu (Message Padding) để chuẩn hóa mọi tin nhắn về kích thước đồng nhất.",
            "Thực hành kiểm tra cơ chế mã hóa và gửi thông điệp bảo mật bằng công cụ dòng lệnh:",
            ("bash", """# Mô phỏng quá trình tạo thông điệp mã hóa tự hủy một lần
echo "Tin nhắn tuyệt mật: Cuộc họp lúc 14:00" > /tmp/secret_msg.txt

# Mã hóa tệp tin bằng thuật toán AES-256 đối xứng với mật khẩu ngẫu nhiên
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 -in /tmp/secret_msg.txt -out /tmp/secret_msg.enc -k "SuperSecureOneTimeKey"

# Xóa tệp tin gốc an toàn bằng lệnh shred
shred -u -z /tmp/secret_msg.txt
echo "Thông điệp đã được mã hóa an toàn thành /tmp/secret_msg.enc!" """),
            ["Không bao giờ sử dụng số điện thoại cá nhân thật để đăng ký các tài khoản nhắn tin bảo mật.", "Luôn kích hoạt tính năng tự hủy tin nhắn (Disappearing Messages) trên các ứng dụng trò chuyện."],
            ["Ứng dụng nhắn tin P2P qua Tor triệt tiêu nguy cơ rò rỉ siêu dữ liệu tập trung.", "Perfect Forward Secrecy bảo vệ các cuộc trò chuyện trong quá khứ ngay cả khi khóa bị lộ.", "Briar và TorChat biến mỗi người dùng thành một Onion Service độc lập."],
            [
                {"question": "Trong kiến trúc của TorChat hoặc Briar, ID liên lạc của người dùng chính là gì?", "type": "MULTIPLE_CHOICE", "options": ["Số điện thoại", "Địa chỉ email", "Địa chỉ tên miền .onion của dịch vụ ẩn danh nội bộ", "Mã số căn cước"], "correct_index": 2, "explanation": "ID liên lạc chính là địa chỉ .onion của Onion Service cục bộ."},
                {"question": "Đặc tính nào đảm bảo rằng nếu khóa hiện tại bị lộ, các tin nhắn trong quá khứ vẫn không thể bị giải mã?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Perfect Forward Secrecy", "PFS", "Bảo mật chuyển tiếp hoàn hảo"]}], "explanation": "Perfect Forward Secrecy (PFS)."},
                {"question": "Các ứng dụng nhắn tin tập trung như Telegram có thể lưu trữ siêu dữ liệu về thời gian và người nhận tin nhắn?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Máy chủ tập trung luôn nắm giữ siêu dữ liệu liên lạc."}
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
                lesson_num=f"2.{pos}",
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
    ls = get_chapter_2_lessons()
    print(f"Generated {len(ls)} lessons for Chapter 2.")
    for l in ls:
        wc = count_vietnamese_words(l["markdown_content"])
        print(f"  - {l['title'][:40]}: {wc} words")
