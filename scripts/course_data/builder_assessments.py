# -*- coding: utf-8 -*-
"""Assessment builders for Black Hat Cybersecurity Course:
5 Chapter Quizzes (10 questions each = 50 questions) + 1 Final Test (20 questions) = 70 questions total.
"""

from decimal import Decimal

def get_chapter_1_quiz_data():
    return {
        "title": "Bài Kiểm Tra Đánh Giá Năng Lực Chương 1: Kiến Trúc Mạng Tor & Định Tuyến Củ Hành",
        "description": "Bài kiểm tra chính thức 10 câu hỏi bao quát toàn bộ lý thuyết và kỹ thuật thực hành mạng Tor, cấu trúc mạch 3-hop, Directory Authorities, Hidden Services v3 và Pluggable Transports.",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 25,
        "attempt_limit": 3,
        "passing_percent": Decimal("80.00"),
        "points_per_question": Decimal("10.00"),
        "questions": [
            {
                "code": "CH1_Q01",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Xác định vai trò của các relay trong mạch Tor 3-hop",
                "question_type": "SINGLE_CHOICE",
                "content": "Trong một mạch kết nối Tor tiêu chuẩn (3-hop circuit), node nào là thực thể DUY NHẤT nhìn thấy địa chỉ IP gốc thực tế của client?",
                "explanation": "Entry Guard (Guard Node) là điểm chạm đầu tiên của Client vào mạng Tor, do đó nó biết IP thực của Client nhưng không biết đích đến. Exit Node biết đích đến nhưng không biết IP thực của Client.",
                "choices": [
                    {"content": "Entry Guard (Guard Node)", "is_correct": True, "position": 1},
                    {"content": "Middle Relay", "is_correct": False, "position": 2},
                    {"content": "Exit Node", "is_correct": False, "position": 3},
                    {"content": "Directory Authority", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH1_Q02",
                "difficulty": "APPLY",
                "learning_objective": "Hiểu cơ chế trao đổi khóa mật mã đa tầng",
                "question_type": "SINGLE_CHOICE",
                "content": "Giao thức mật mã nào được client Tor sử dụng để đàm phán từng khóa đối xứng tạm thời (ephemeral keys) với lần lượt Guard, Middle và Exit node?",
                "explanation": "Tor sử dụng giao thức ntor handshake (dựa trên đường cong Elliptic Curve Curve25519) để đàm phán khóa bí mật phiên độc lập với từng hop trong mạch.",
                "choices": [
                    {"content": "ntor handshake (Curve25519 ECDH)", "is_correct": True, "position": 1},
                    {"content": "RSA-4096 Key Transport", "is_correct": False, "position": 2},
                    {"content": "Kerberos v5 Ticket Granting", "is_correct": False, "position": 3},
                    {"content": "Diffie-Hellman 1024-bit Legacy", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH1_Q03",
                "difficulty": "REMEMBER",
                "learning_objective": "Nắm vững số lượng và vai trò của Directory Authorities",
                "question_type": "SINGLE_CHOICE",
                "content": "Hệ thống mạng Tor hiện tại duy trì bao nhiêu máy chủ thư mục đặc quyền (Directory Authorities) để tạo bản đồng thuận mạng (Consensus Document)?",
                "explanation": "Tor mạng công cộng hiện có chính xác 9 Directory Authorities đặt tại nhiều quốc gia và được vận hành bởi các bên độc lập đáng tin cậy để biểu quyết tài liệu consensus mỗi giờ.",
                "choices": [
                    {"content": "9 Directory Authorities", "is_correct": True, "position": 1},
                    {"content": "13 Root Servers", "is_correct": False, "position": 2},
                    {"content": "5 Central Authorities", "is_correct": False, "position": 3},
                    {"content": "21 Validator Nodes", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH1_Q04",
                "difficulty": "APPLY",
                "learning_objective": "Hiểu cấu trúc và độ dài của địa chỉ Onion v3",
                "question_type": "SINGLE_CHOICE",
                "content": "Một địa chỉ Tor Hidden Service thế hệ v3 (vd: `... .onion`) có tổng cộng bao nhiêu ký tự base32 trong phần tiền tố tên miền?",
                "explanation": "Onion v3 chứa khóa công khai ed25519 32-byte cùng checksum và version byte, khi mã hóa base32 tạo thành một chuỗi chính xác 56 ký tự (so với 16 ký tự của v2 cũ).",
                "choices": [
                    {"content": "56 ký tự", "is_correct": True, "position": 1},
                    {"content": "16 ký tự", "is_correct": False, "position": 2},
                    {"content": "32 ký tự", "is_correct": False, "position": 3},
                    {"content": "64 ký tự", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH1_Q05",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Phân tích giao thức kết nối Rendezvous Point",
                "question_type": "SINGLE_CHOICE",
                "content": "Trong quá trình Client kết nối tới Hidden Service v3, vai trò chính của Rendezvous Point (RP) là gì?",
                "explanation": "Rendezvous Point là relay trung gian nơi mạch 3-hop của Client và mạch 3-hop của Hidden Service gặp nhau, giúp 2 bên truyền dữ liệu mà không bên nào biết địa chỉ IP thực của đối phương.",
                "choices": [
                    {"content": "Là điểm gặp gỡ trung gian kết nối mạch của Client và Hidden Service mà không làm lộ IP của cả hai", "is_correct": True, "position": 1},
                    {"content": "Là máy chủ lưu trữ toàn bộ cơ sở dữ liệu của trang web .onion", "is_correct": False, "position": 2},
                    {"content": "Là node thực hiện giải mã toàn bộ dữ liệu HTTP trước khi chuyển tiếp", "is_correct": False, "position": 3},
                    {"content": "Là node cấp phát chứng chỉ SSL/TLS cho dịch vụ ẩn", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH1_Q06",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Đánh giá các kỹ thuật vượt tường lửa qua Pluggable Transports",
                "question_type": "SINGLE_CHOICE",
                "content": "Giao thức Pluggable Transport obfs4 có đặc tính vượt trội nào giúp vượt qua hệ thống kiểm duyệt gói tin sâu (Deep Packet Inspection - DPI)?",
                "explanation": "obfs4 làm lu mờ hoàn toàn các dấu hiệu nhận dạng của Tor traffic thành dữ liệu ngẫu nhiên (random-looking noise) và sử dụng chứng chỉ public key đàm phán bí mật để ngăn máy quét DPI chủ động.",
                "choices": [
                    {"content": "Biến đổi toàn bộ luồng gói tin thành chuỗi byte ngẫu nhiên không có entropy định danh", "is_correct": True, "position": 1},
                    {"content": "Nén dữ liệu thành định dạng ZIP trước khi truyền qua mạng", "is_correct": False, "position": 2},
                    {"content": "Chuyển toàn bộ dữ liệu sang giao thức ICMP Ping", "is_correct": False, "position": 3},
                    {"content": "Nhúng mã HTML vào tiêu đề gói tin TCP", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH1_Q07",
                "difficulty": "APPLY",
                "learning_objective": "Nhận diện điểm yếu của Exit Node đối với lưu lượng Cleartext",
                "question_type": "TRUE_FALSE",
                "content": "Nếu Client sử dụng Tor để truy cập một trang web HTTP không mã hóa (cleartext), Exit Node độc hại hoàn toàn có thể đọc trộm và chỉnh sửa dữ liệu mật khẩu, cookie của phiên duyệt web.",
                "explanation": "Đúng. Tor chỉ mã hóa giữa Client và Exit Node. Tại Exit Node, lớp vỏ củ hành cuối cùng bị bóc tách và dữ liệu truyền tới web server dưới dạng HTTP thô nếu không dùng HTTPS.",
                "choices": [
                    {"content": "Đúng", "is_correct": True, "position": 1},
                    {"content": "Sai", "is_correct": False, "position": 2},
                ]
            },
            {
                "code": "CH1_Q08",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Hiểu cơ chế bảo vệ của Entry Guards đối với tấn công phân tích lưu lượng",
                "question_type": "SINGLE_CHOICE",
                "content": "Tại sao Tor Browser lại ghim cố định một Guard Node (Guard Pinning) trong nhiều tháng thay vì chọn Guard ngẫu nhiên cho mỗi phiên kết nối?",
                "explanation": "Nếu chọn Guard ngẫu nhiên liên tục, xác suất Client chạm phải một Guard Node do kẻ tấn công kiểm soát sẽ tiến tới 100% theo thời gian. Ghim Guard hạn chế tối đa rủi ro này.",
                "choices": [
                    {"content": "Giảm thiểu xác suất chạm phải Guard Node bị kiểm soát bởi kẻ nghe lén theo thời gian", "is_correct": True, "position": 1},
                    {"content": "Tăng tốc độ tải trang web lên gấp 3 lần", "is_correct": False, "position": 2},
                    {"content": "Tiết kiệm băng thông cho mạng lưới máy chủ Directory Authorities", "is_correct": False, "position": 3},
                    {"content": "Để tương thích với hệ điều hành Windows cũ", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH1_Q09",
                "difficulty": "APPLY",
                "learning_objective": "Phân tích tấn công tương quan thời gian (Traffic Correlation Attack)",
                "question_type": "SINGLE_CHOICE",
                "content": "Một tổ chức gián điệp mạng có thể giải mã danh tính người dùng Tor bằng tấn công tương quan lưu lượng (Traffic Correlation) khi họ kiểm soát được đồng thời hai vị trí nào?",
                "explanation": "Tấn công End-to-End Traffic Correlation xảy ra khi kẻ tấn công quan sát được đồng thời lưu lượng vào tại Entry Guard và lưu lượng ra tại Exit Node, so sánh mẫu kích thước và thời gian gói tin.",
                "choices": [
                    {"content": "Entry Guard và Exit Node của cùng một mạch", "is_correct": True, "position": 1},
                    {"content": "Hai Middle Relay khác nhau trong mạng", "is_correct": False, "position": 2},
                    {"content": "DNS Server cục bộ của người dùng và Web Server", "is_correct": False, "position": 3},
                    {"content": "Tường lửa của Client và máy tính cá nhân", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH1_Q10",
                "difficulty": "REMEMBER",
                "learning_objective": "Nhận biết cổng dịch vụ SOCKS5 mặc định của Tor",
                "question_type": "SINGLE_CHOICE",
                "content": "Cổng mạng SOCKS5 proxy cục bộ mặc định mà tiến trình Tor daemon lắng nghe trên hệ thống Linux/macOS là cổng nào?",
                "explanation": "Tor client daemon mặc định mở cổng SOCKS5 tại 127.0.0.1:9050 (trong khi Tor Browser Bundle độc lập thường dùng cổng 9150).",
                "choices": [
                    {"content": "Port 9050 (hoặc 9150 đối với Tor Browser)", "is_correct": True, "position": 1},
                    {"content": "Port 8080 (hoặc 8443)", "is_correct": False, "position": 2},
                    {"content": "Port 1080 (hoặc 3128)", "is_correct": False, "position": 3},
                    {"content": "Port 443 (hoặc 80)", "is_correct": False, "position": 4},
                ]
            }
        ]
    }

def get_chapter_2_quiz_data():
    return {
        "title": "Bài Kiểm Tra Đánh Giá Năng Lực Chương 2: Kỹ Thuật Ẩn Danh, OPSEC & Phòng Thủ Trinh Sát",
        "description": "Bài kiểm tra chính thức 10 câu hỏi bao quát các phương pháp bảo vệ danh tính, hệ điều hành Tails OS amnesic, quản lý khóa PGP/GPG, chống rò rỉ DNS/WebRTC và mô hình cách ly Whonix.",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 25,
        "attempt_limit": 3,
        "passing_percent": Decimal("80.00"),
        "points_per_question": Decimal("10.00"),
        "questions": [
            {
                "code": "CH2_Q01",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Hiểu kiến trúc Amnesic của Tails OS",
                "question_type": "SINGLE_CHOICE",
                "content": "Tại sao hệ điều hành Tails OS (The Amnesic Incognito Live System) lại không để lại bất kỳ dấu vết dữ liệu nào trên ổ đĩa cứng của máy tính sau khi tắt máy?",
                "explanation": "Tails OS hoạt động hoàn toàn trên bộ nhớ RAM (Live RAM execution) và ghi đè toàn bộ RAM (RAM flush) trước khi tắt nguồn, không bao giờ tự động ghi dữ liệu vào ổ cứng.",
                "choices": [
                    {"content": "Hệ thống chỉ chạy trên bộ nhớ RAM và tự động xả sạch RAM trước khi tắt nguồn", "is_correct": True, "position": 1},
                    {"content": "Tails tự động format toàn bộ ổ cứng máy tính mỗi lần khởi động", "is_correct": False, "position": 2},
                    {"content": "Hệ thống gửi toàn bộ file hệ thống lên đám mây máy chủ Tor", "is_correct": False, "position": 3},
                    {"content": "Hệ điều hành sử dụng công nghệ ảo hóa đám mây AWS", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH2_Q02",
                "difficulty": "APPLY",
                "learning_objective": "Xử lý lỗ hổng rò rỉ WebRTC trong trình duyệt",
                "question_type": "SINGLE_CHOICE",
                "content": "Lỗ hổng rò rỉ WebRTC (WebRTC Local IP Leak) có thể làm lộ thông tin nhạy cảm nào của người dùng dù đang chạy VPN hoặc Proxy?",
                "explanation": "WebRTC sử dụng giao thức STUN/TURN để thiết lập kết nối P2P, có thể gửi truy vấn trực tiếp qua interface mạng thật và làm lộ địa chỉ IP cục bộ (LAN IP) cũng như IP công cộng thật của máy tính.",
                "choices": [
                    {"content": "Địa chỉ IP thực của card mạng nội bộ và IP nhà mạng cung cấp (ISP IP)", "is_correct": True, "position": 1},
                    {"content": "Mật khẩu đăng nhập Windows của người dùng", "is_correct": False, "position": 2},
                    {"content": "Lịch sử duyệt web trong 30 ngày gần nhất", "is_correct": False, "position": 3},
                    {"content": "Địa chỉ MAC của thiết bị router Wi-Fi hàng xóm", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH2_Q03",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Hiểu kiến trúc phân tách 2 máy ảo của Whonix",
                "question_type": "SINGLE_CHOICE",
                "content": "Trong kiến trúc hệ điều hành Whonix, nhiệm vụ chính của máy ảo `Whonix-Gateway` là gì?",
                "explanation": "Whonix-Gateway đóng vai trò là router bảo vệ, bắt buộc toàn bộ lưu lượng mạng từ Whonix-Workstation phải đi qua Tor và ngăn chặn hoàn toàn rò rỉ IP thực ngay cả khi Workstation bị root exploit.",
                "choices": [
                    {"content": "Ép buộc toàn bộ kết nối từ Workstation phải đi qua Tor và chặn triệt để rò rỉ IP trực tiếp", "is_correct": True, "position": 1},
                    {"content": "Dùng để người dùng trực tiếp mở trình duyệt web và gõ văn bản", "is_correct": False, "position": 2},
                    {"content": "Chuyên đào tiền điện tử Bitcoin để duy trì hoạt động máy ảo", "is_correct": False, "position": 3},
                    {"content": "Lưu trữ các file tải về từ Darknet vào phân vùng bảo mật", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH2_Q04",
                "difficulty": "APPLY",
                "learning_objective": "Nguyên tắc bảo vệ khóa bí mật trong mã hóa PGP/GPG",
                "question_type": "SINGLE_CHOICE",
                "content": "Khi thực hiện trao đổi thông tin bí mật qua PGP/GPG, nguyên tắc nào sau đây là BẮT BUỘC để đảm bảo an toàn tuyệt đối?",
                "explanation": "Khóa công khai (Public Key) có thể chia sẻ tự do cho mọi người để họ mã hóa gửi cho bạn, nhưng Khóa bí mật (Private Key) tuyệt đối không bao giờ được chia sẻ hoặc tải lên mạng.",
                "choices": [
                    {"content": "Tuyệt đối không bao giờ chia sẻ Private Key cho bất kỳ ai hoặc tải lên Keyserver công cộng", "is_correct": True, "position": 1},
                    {"content": "Gửi cả Public Key và Private Key kèm theo tin nhắn để người nhận tiện giải mã", "is_correct": False, "position": 2},
                    {"content": "Đặt mật khẩu bảo vệ Private Key trùng với địa chỉ email cá nhân", "is_correct": False, "position": 3},
                    {"content": "Tải Private Key lên Github để làm bản sao lưu dự phòng", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH2_Q05",
                "difficulty": "UNDERSTAND",
                "learning_objective": "So sánh tính ẩn danh giữa Bitcoin và Monero",
                "question_type": "SINGLE_CHOICE",
                "content": "Tại sao tiền mã hóa Monero (XMR) lại được xem là lựa chọn tối ưu hơn hẳn Bitcoin (BTC) trong các giao dịch ẩn danh tài chính?",
                "explanation": "Bitcoin có sổ cái công khai hoàn toàn (public transparent ledger) nên mọi giao dịch đều có thể bị truy vết (blockchain forensics). Monero áp dụng Ring Signatures, RingCT và Stealth Addresses để ẩn danh hoàn toàn người gửi, người nhận và số tiền.",
                "choices": [
                    {"content": "Monero mặc định ẩn người gửi, người nhận và số tiền giao dịch qua RingCT và Stealth Addresses", "is_correct": True, "position": 1},
                    {"content": "Bitcoin đã bị chính phủ toàn cầu đóng cửa hoàn toàn không thể sử dụng", "is_correct": False, "position": 2},
                    {"content": "Monero không sử dụng công nghệ blockchain mà dùng cơ sở dữ liệu SQL", "is_correct": False, "position": 3},
                    {"content": "Phí giao dịch của Monero luôn bằng 0 trong mọi trường hợp", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH2_Q06",
                "difficulty": "APPLY",
                "learning_objective": "Phòng tránh tấn công Browser Fingerprinting",
                "question_type": "TRUE_FALSE",
                "content": "Việc cài đặt thêm nhiều tiện ích mở rộng (extensions) trên Tor Browser (như AdBlock, Dark Reader) sẽ giúp người dùng an toàn hơn và khó bị nhận dạng hơn.",
                "explanation": "Sai. Mỗi extension bổ sung sẽ làm dấu vân tay trình duyệt (browser fingerprint) trở nên độc nhất vô nhị giữa đám đông, giúp các tracker dễ dàng nhận dạng và theo vết người dùng.",
                "choices": [
                    {"content": "Đúng", "is_correct": False, "position": 1},
                    {"content": "Sai", "is_correct": True, "position": 2},
                ]
            },
            {
                "code": "CH2_Q07",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Hiểu rủi ro giả mạo địa chỉ MAC",
                "question_type": "SINGLE_CHOICE",
                "content": "Kỹ thuật MAC Address Spoofing trước khi kết nối vào mạng Wi-Fi công cộng nhằm mục đích chính là gì?",
                "explanation": "Địa chỉ MAC của card mạng là định danh phần cứng duy nhất. Đổi MAC giả ngăn chặn quản trị viên mạng Wi-Fi hoặc cơ quan điều tra liên kết thiết bị vật lý cụ thể với hoạt động mạng.",
                "choices": [
                    {"content": "Ngăn chặn router và hệ thống giám sát lưu vết định danh phần cứng vật lý của máy tính", "is_correct": True, "position": 1},
                    {"content": "Tăng cường tốc độ download của đường truyền Internet", "is_correct": False, "position": 2},
                    {"content": "Tự động vượt qua mật khẩu mã hóa WPA3 của trạm Wi-Fi", "is_correct": False, "position": 3},
                    {"content": "Bảo vệ màn hình máy tính khỏi bị quay lén từ xa", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH2_Q08",
                "difficulty": "APPLY",
                "learning_objective": "Quy tắc an ninh OPSEC trong truyền thông",
                "question_type": "SINGLE_CHOICE",
                "content": "Nguyên tắc ' compartmentalization' (phân vùng danh tính) trong OPSEC đòi hỏi chuyên gia an ninh phải tuân thủ điều gì?",
                "explanation": "Phân vùng danh tính yêu cầu tách biệt hoàn toàn giữa danh tính thực (real life) và các bí danh trực tuyến (personas), không dùng chung email, số điện thoại, thiết bị hay thói quen ngôn ngữ.",
                "choices": [
                    {"content": "Tách biệt triệt để mọi bí danh (personas) trực tuyến với danh tính thực tế, không dùng chung thông tin hay thiết bị", "is_correct": True, "position": 1},
                    {"content": "Sử dụng cùng một mật khẩu phức tạp cho toàn bộ các tài khoản để tránh quên", "is_correct": False, "position": 2},
                    {"content": "Chia sẻ vị trí GPS thời gian thực cho các thành viên trong nhóm nghiên cứu", "is_correct": False, "position": 3},
                    {"content": "Đăng ký tài khoản mạng xã hội bằng số điện thoại chính chủ để dễ phục hồi", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH2_Q09",
                "difficulty": "REMEMBER",
                "learning_objective": "Nhận biết công cụ mã hóa ổ đĩa tiêu chuẩn cao",
                "question_type": "SINGLE_CHOICE",
                "content": "Phần mềm mã hóa ổ đĩa mã nguồn mở kế thừa từ TrueCrypt, hỗ trợ tạo Hidden Operating System và Outer/Inner Volume là gì?",
                "explanation": "VeraCrypt là phần mềm mã hóa ổ đĩa hàng đầu kế thừa TrueCrypt, hỗ trợ thuật toán AES-Twofish-Serpent và tính năng phủ nhận chính đáng (plausible deniability) qua hidden volume.",
                "choices": [
                    {"content": "VeraCrypt", "is_correct": True, "position": 1},
                    {"content": "BitLocker Home", "is_correct": False, "position": 2},
                    {"content": "WinRAR Password Protect", "is_correct": False, "position": 3},
                    {"content": "FileVault Basic", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH2_Q10",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Cơ chế bảo vệ của Canary Domain trong threat intel",
                "question_type": "SINGLE_CHOICE",
                "content": "Khái niệm 'Warrant Canary' được các dịch vụ lưu trữ và nhà cung cấp VPN sử dụng nhằm mục đích gì?",
                "explanation": "Warrant Canary là một thông báo công khai được cập nhật định kỳ xác nhận công ty chưa bị cơ quan điều tra bí mật yêu cầu giao nộp dữ liệu hoặc gắn backdoor (National Security Letter). Nếu thông báo biến mất, người dùng hiểu rằng hệ thống đã bị xâm phạm.",
                "choices": [
                    {"content": "Cảnh báo gián tiếp cho người dùng biết khi hệ thống bị cơ quan chấp pháp bí mật yêu cầu can thiệp", "is_correct": True, "position": 1},
                    {"content": "Kiểm tra tốc độ kết nối định kỳ của đường truyền cáp quang biển", "is_correct": False, "position": 2},
                    {"content": "Tự động gửi email thông báo mã giảm giá dịch vụ hàng tháng", "is_correct": False, "position": 3},
                    {"content": "Bảo vệ trang web khỏi các cuộc tấn công DDoS quy mô lớn", "is_correct": False, "position": 4},
                ]
            }
        ]
    }

def get_chapter_3_quiz_data():
    return {
        "title": "Bài Kiểm Tra Đánh Giá Năng Lực Chương 3: Phân Tích Mã Độc, Botnet & Thế Giới Ngầm Dark Web",
        "description": "Bài kiểm tra chính thức 10 câu hỏi bao quát thị trường ngầm Darknet, kiến trúc mã độc Ransomware, cơ chế lẩn tránh Sandbox, C2 Hidden Service và quy trình điều tra an ninh mạng.",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 25,
        "attempt_limit": 3,
        "passing_percent": Decimal("80.00"),
        "points_per_question": Decimal("10.00"),
        "questions": [
            {
                "code": "CH3_Q01",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Hiểu cơ chế ký quỹ đa chữ ký trên Dark Web",
                "question_type": "SINGLE_CHOICE",
                "content": "Cơ chế Multisig Escrow 2-of-3 trên các chợ đen Darknet bảo vệ người mua và người bán khỏi nguy cơ 'Exit Scam' của ban quản trị chợ như thế nào?",
                "explanation": "Cần 2 trong 3 chữ ký (Buyer, Seller, Market) để giải ngân tiền. Ban quản trị chợ chỉ có 1 khóa nên không thể tự ý rút tiền khi không có sự đồng thuận của Buyer hoặc Seller.",
                "choices": [
                    {"content": "Cần ít nhất 2 trong 3 bên (Buyer, Seller, Market) đồng thuận ký giao dịch mới giải phóng được tiền", "is_correct": True, "position": 1},
                    {"content": "Toàn bộ tiền được chuyển vào tài khoản ngân hàng thụy sĩ của người mua", "is_correct": False, "position": 2},
                    {"content": "Hệ thống tự động hoàn tiền sau 24 giờ bất kể hàng đã giao hay chưa", "is_correct": False, "position": 3},
                    {"content": "Cơ quan điều tra FBI là bên thứ ba giữ khóa giải mã duy nhất", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH3_Q02",
                "difficulty": "APPLY",
                "learning_objective": "Phân tích mô hình hoạt động Ransomware-as-a-Service",
                "question_type": "SINGLE_CHOICE",
                "content": "Trong mô hình Ransomware-as-a-Service (RaaS), đối tượng 'Affiliate' đóng vai trò chính là gì?",
                "explanation": "Trong RaaS, nhóm Core phát triển mã độc và cổng thanh toán, còn Affiliate là bên trực tiếp tìm kiếm mục tiêu, xâm nhập mạng nội bộ nạn nhân và thực thi payload mã độc để ăn chia phần trăm tiền chuộc.",
                "choices": [
                    {"content": "Là bên trực tiếp xâm nhập hệ thống mục tiêu và thực thi payload mã độc tống tiền", "is_correct": True, "position": 1},
                    {"content": "Là công ty bảo hiểm bồi thường thiệt hại cho các nạn nhân bị mã hóa", "is_correct": False, "position": 2},
                    {"content": "Là lập trình viên viết ra trình giải mã miễn phí cho cộng đồng", "is_correct": False, "position": 3},
                    {"content": "Là tổ chức ngân hàng đứng ra rửa tiền chuộc sang tiền mặt", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH3_Q03",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Nhận diện cơ chế C2 thông qua Tor Hidden Service",
                "question_type": "SINGLE_CHOICE",
                "content": "Ưu điểm lớn nhất mà các nhóm điều hành Botnet nhận được khi đặt máy chủ Command & Control (C2) dưới dạng Tor Hidden Service (.onion) là gì?",
                "explanation": "Máy chủ C2 chạy dưới dạng Onion Service không để lộ địa chỉ IP thật, chống được việc bị nhà mạng hosting đình chỉ (Bulletproof Hosting) và miễn nhiễm với việc thu hồi tên miền DNS (Domain Takedown).",
                "choices": [
                    {"content": "Ẩn giấu địa chỉ IP thực của máy chủ C2 và miễn nhiễm với các lệnh triệt hạ tên miền DNS", "is_correct": True, "position": 1},
                    {"content": "Tăng tốc độ truyền tải tệp tin độc hại nhanh hơn mạng Internet thông thường", "is_correct": False, "position": 2},
                    {"content": "Tự động giải mã toàn bộ dữ liệu trên các máy tính nạn nhân mà không cần khóa", "is_correct": False, "position": 3},
                    {"content": "Được miễn trừ trách nhiệm pháp lý theo điều lệ quốc tế", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH3_Q04",
                "difficulty": "APPLY",
                "learning_objective": "Kỹ thuật phát hiện và lẩn tránh môi trường máy ảo Sandbox",
                "question_type": "SINGLE_CHOICE",
                "content": "Mã độc hiện đại thường kiểm tra các dấu hiệu nào sau đây để phát hiện nó đang bị phân tích trong môi trường Sandbox tự động?",
                "explanation": "Mã độc kiểm tra số nhân CPU (< 2 vCPU), dung lượng RAM (< 4GB), sự hiện diện của driver máy ảo (VBoxGuestAdditions, VmTools), độ trễ thời gian (sleep acceleration) và chuyển động chuột của người dùng.",
                "choices": [
                    {"content": "Kiểm tra kích thước RAM < 4GB, vCPU < 2 nhân, thiếu driver chuột thật và sự tồn tại của VM Guest Tools", "is_correct": True, "position": 1},
                    {"content": "Kiểm tra máy tính có cài đặt ứng dụng Microsoft Word hay không", "is_correct": False, "position": 2},
                    {"content": "Kiểm tra phiên bản BIOS có hỗ trợ đèn LED RGB hay không", "is_correct": False, "position": 3},
                    {"content": "Kiểm tra tốc độ gõ bàn phím của người dùng vượt quá 100 từ/phút", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH3_Q05",
                "difficulty": "REMEMBER",
                "learning_objective": "Phân loại Crypters và Stub trong phân phối mã độc",
                "question_type": "SINGLE_CHOICE",
                "content": "Thuật ngữ 'FUD Crypter' (Fully Undetectable) trong cộng đồng phát triển mã độc ám chỉ công cụ có chức năng gì?",
                "explanation": "FUD Crypter có nhiệm vụ mã hóa payload độc hại gốc và đóng gói cùng một 'Stub' thực thi để khi quét bởi các công cụ Antivirus (như VirusTotal, Windows Defender) thì tỷ lệ phát hiện là 0/70.",
                "choices": [
                    {"content": "Công cụ mã hóa và bao bọc payload để vượt qua toàn bộ các bộ giải pháp diệt virus (AV/EDR) tại thời điểm xuất xưởng", "is_correct": True, "position": 1},
                    {"content": "Phần mềm khôi phục dữ liệu đã bị xóa vĩnh viễn trên máy tính", "is_correct": False, "position": 2},
                    {"content": "Trình duyệt web chuyên dụng dành riêng cho các thành viên chính phủ", "is_correct": False, "position": 3},
                    {"content": "Hệ thống tường lửa ngăn chặn xâm nhập mạng cấp doanh nghiệp", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH3_Q06",
                "difficulty": "APPLY",
                "learning_objective": "Khai thác lỗ hổng Log4Shell trong chuỗi cung ứng",
                "question_type": "SINGLE_CHOICE",
                "content": "Thành phần nào trong Java được Log4j2 sử dụng để tra cứu tên miền độc hại, trực tiếp dẫn tới lỗ hổng thực thi mã từ xa Log4Shell (CVE-2021-44228)?",
                "explanation": "Java Naming and Directory Interface (JNDI) kết hợp với các giao thức như LDAP/RMI cho phép Log4j tự động gửi request đến máy chủ điều khiển và nạp class bytecode độc hại vào JVM.",
                "choices": [
                    {"content": "JNDI Lookup kết hợp với giao thức LDAP/RMI", "is_correct": True, "position": 1},
                    {"content": "JDBC Connector kết nối cơ sở dữ liệu MySQL", "is_correct": False, "position": 2},
                    {"content": "Java Swing giao diện người dùng đồ họa", "is_correct": False, "position": 3},
                    {"content": "Java Garbage Collector quản lý bộ nhớ heap", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH3_Q07",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Chiến thuật Double Extortion trong Ransomware",
                "question_type": "SINGLE_CHOICE",
                "content": "Chiến thuật tống tiền kép ('Double Extortion') của các nhóm Ransomware Dark Web bao gồm hai hành vi chính nào?",
                "explanation": "Double Extortion không chỉ mã hóa dữ liệu cục bộ đòi tiền chuộc giải mã, mà còn đánh cắp dữ liệu nhạy cảm từ trước (data exfiltration) và đe dọa phát tán công khai trên các 'DLS' (Data Leak Sites) nếu không trả tiền.",
                "choices": [
                    {"content": "Vừa mã hóa dữ liệu đòi tiền chuộc giải mã, vừa đánh cắp dữ liệu dọa phát tán công khai lên Data Leak Site", "is_correct": True, "position": 1},
                    {"content": "Mã hóa 2 lần liên tiếp bằng 2 thuật toán khác nhau", "is_correct": False, "position": 2},
                    {"content": "Đòi tiền chuộc bằng cả Bitcoin và Monero cùng một lúc", "is_correct": False, "position": 3},
                    {"content": "Yêu cầu cả nạn nhân và công ty bảo hiểm cùng thanh toán tiền chuộc", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH3_Q08",
                "difficulty": "APPLY",
                "learning_objective": "Nhận biết kỹ thuật điều tra Operation Onymous",
                "question_type": "TRUE_FALSE",
                "content": "Trong chiến dịch triệt phá Silk Road 2.0 (Operation Onymous), các cơ quan thực thi pháp luật đã phối hợp nghiên cứu kỹ thuật tấn công tấn công gắn tag lưu lượng (traffic tagging/confirmation attack) để xác định vị trí thực của các server ẩn.",
                "explanation": "Đúng. Các nhà nghiên cứu và cơ quan chấp pháp đã tận dụng các lỗ hổng căn chỉnh lưu lượng và relay trong mạng Tor để xác thực vị trí vật lý của máy chủ Silk Road 2.0.",
                "choices": [
                    {"content": "Đúng", "is_correct": True, "position": 1},
                    {"content": "Sai", "is_correct": False, "position": 2},
                ]
            },
            {
                "code": "CH3_Q09",
                "difficulty": "REMEMBER",
                "learning_objective": "Hiểu khái niệm Initial Access Brokers",
                "question_type": "SINGLE_CHOICE",
                "content": "Trên thị trường ngầm, nhóm đối tượng 'Initial Access Brokers' (IAB) kiếm tiền bằng cách nào?",
                "explanation": "IAB chuyên quét tìm, khai thác lỗ hổng và xâm nhập bước đầu vào mạng doanh nghiệp (qua VPN credentials, RDP, webshell), sau đó bán lại quyền truy cập này cho các nhóm Ransomware hoặc APT.",
                "choices": [
                    {"content": "Bán lại quyền truy cập ban đầu (RDP, VPN, WebShell) vào mạng doanh nghiệp cho các nhóm Ransomware", "is_correct": True, "position": 1},
                    {"content": "Cung cấp dịch vụ Internet vệ tinh cho các quốc gia đang phát triển", "is_correct": False, "position": 2},
                    {"content": "Môi giới tuyển dụng nhân sự IT cao cấp cho các tập đoàn công nghệ", "is_correct": False, "position": 3},
                    {"content": "Bán các bản quyền phần mềm Microsoft Office chính hãng giá rẻ", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH3_Q10",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Phòng thủ phát hiện mã độc bằng YARA Rules",
                "question_type": "SINGLE_CHOICE",
                "content": "Công cụ YARA được các chuyên gia phân tích mã độc và Blue Team sử dụng chủ yếu để làm gì?",
                "explanation": "YARA cho phép viết các quy tắc nhận dạng dựa trên chuỗi mẫu (strings, regex) và điều kiện logic để phân loại và phát hiện các mẫu mã độc độc hại trong tệp tin hoặc bộ nhớ tiến trình.",
                "choices": [
                    {"content": "Viết các luật đối sánh mẫu chuỗi và nhị phân để nhận diện và phân loại họ mã độc", "is_correct": True, "position": 1},
                    {"content": "Tự động bẻ khóa mật khẩu Wi-Fi xung quanh văn phòng", "is_correct": False, "position": 2},
                    {"content": "Quét và dọn dẹp các tập tin rác tạm thời của hệ điều hành", "is_correct": False, "position": 3},
                    {"content": "Tạo chứng chỉ bảo mật SSL miễn phí cho tên miền", "is_correct": False, "position": 4},
                ]
            }
        ]
    }

def get_chapter_4_quiz_data():
    return {
        "title": "Bài Kiểm Tra Đánh Giá Năng Lực Chương 4: Lập Trình Khai Thác Mũ Đen & Tối Ưu Bộ Nhớ Với Rust",
        "description": "Bài kiểm tra chính thức 10 câu hỏi bao quát việc ứng dụng ngôn ngữ Rust trong phát triển mã độc tấn công, tiêm shellcode bộ nhớ, tương tác Windows API qua FFI, né tránh Antivirus/EDR.",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 25,
        "attempt_limit": 3,
        "passing_percent": Decimal("80.00"),
        "points_per_question": Decimal("10.00"),
        "questions": [
            {
                "code": "CH4_Q01",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Lợi ích của ngôn ngữ Rust trong phát triển mã độc mũ đen",
                "question_type": "SINGLE_CHOICE",
                "content": "Đặc tính nào của ngôn ngữ Rust khiến nó ngày càng được các nhóm phát triển mã độc chuyên nghiệp ưa chuộng thay thế C/C++?",
                "explanation": "Rust biên dịch ra mã máy native hiệu năng cao như C/C++, không cần runtime VM nặng nề, cơ chế Borrow Checker loại bỏ memory corruption bugs ngớ ngẩn và hệ sinh thái thư viện đa nền tảng mạnh mẽ.",
                "choices": [
                    {"content": "Biên dịch native hiệu năng cao, không cần runtime VM, kiểm soát an toàn bộ nhớ tuyệt đối và chữ ký mã máy mới lạ khó bị AV gắn cờ", "is_correct": True, "position": 1},
                    {"content": "Rust là ngôn ngữ thông dịch giống Python nên chạy không cần biên dịch", "is_correct": False, "position": 2},
                    {"content": "Rust mặc định được miễn nhiễm với mọi luật an ninh mạng quốc tế", "is_correct": False, "position": 3},
                    {"content": "Toàn bộ mã nguồn Rust khi biên dịch sẽ tự động mã hóa thành file ảnh JPG", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH4_Q02",
                "difficulty": "APPLY",
                "learning_objective": "Sử dụng khối lệnh unsafe trong Rust cho FFI",
                "question_type": "SINGLE_CHOICE",
                "content": "Từ khóa nào trong Rust bắt buộc phải được sử dụng khi lập trình viên cần giải tham chiếu con trỏ thô (raw pointer) hoặc gọi các hàm Windows API C-style qua FFI?",
                "explanation": "Trong Rust, việc giải tham chiếu raw pointers (*const T, *mut T) hoặc gọi hàm FFI từ bên ngoài là hoạt động tiềm ẩn rủi ro bộ nhớ nên compiler bắt buộc phải đặt trong khối `unsafe { ... }`.",
                "choices": [
                    {"content": "unsafe", "is_correct": True, "position": 1},
                    {"content": "virtual", "is_correct": False, "position": 2},
                    {"content": "dynamic", "is_correct": False, "position": 3},
                    {"content": "unmanaged", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH4_Q03",
                "difficulty": "APPLY",
                "learning_objective": "Kỹ thuật tiêm Shellcode cục bộ trong Rust",
                "question_type": "SINGLE_CHOICE",
                "content": "Bộ 3 hàm Windows API kinh điển nào thường được mã độc sử dụng để tiêm và thực thi shellcode trong không gian bộ nhớ của chính tiến trình hiện tại?",
                "explanation": "VirtualAlloc cấp phát vùng nhớ thực thi (RWX), RtlCopyMemory sao chép shellcode vào vùng nhớ đó, và VirtualProtect (hoặc CreateThread) chuyển quyền và kích hoạt thực thi luồng mã độc.",
                "choices": [
                    {"content": "VirtualAlloc, RtlCopyMemory / WriteProcessMemory, VirtualProtect / CreateThread", "is_correct": True, "position": 1},
                    {"content": "CreateWindow, ShowWindow, UpdateWindow", "is_correct": False, "position": 2},
                    {"content": "RegOpenKey, RegSetValue, RegCloseKey", "is_correct": False, "position": 3},
                    {"content": "Socket, Bind, Listen", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH4_Q04",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Nhận biết kỹ thuật Process Injection DLL Hollowing",
                "question_type": "SINGLE_CHOICE",
                "content": "Kỹ thuật 'Process Hollowing' (RunPE) được thực hiện như thế nào trong các chiến dịch tấn công bằng mã độc nhắm mục tiêu?",
                "explanation": "Process Hollowing khởi tạo một tiến trình hợp pháp của Windows (như svchost.exe) ở trạng thái tạm dừng (CREATE_SUSPENDED), dỡ bỏ (unmap) mã gốc và thay thế bằng payload độc hại trước khi resume thread.",
                "choices": [
                    {"content": "Khởi tạo tiến trình hợp lệ ở trạng thái treo, dỡ bỏ mã gốc và thế chỗ bằng payload độc hại rồi tiếp tục thực thi", "is_correct": True, "position": 1},
                    {"content": "Xóa toàn bộ thư mục System32 và khởi động lại máy tính", "is_correct": False, "position": 2},
                    {"content": "Gửi hàng triệu yêu cầu HTTP tới máy chủ nạn nhân làm sập dịch vụ", "is_correct": False, "position": 3},
                    {"content": "Thay đổi hình nền desktop của người dùng thành logo tin tặc", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH4_Q05",
                "difficulty": "APPLY",
                "learning_objective": "Tối ưu kích thước nhị phân binary của Rust",
                "question_type": "SINGLE_CHOICE",
                "content": "Cấu hình nào trong tệp `Cargo.toml` của dự án Rust giúp giảm kích thước nhị phân tối đa và loại bỏ bảng ký hiệu debug symbols (strip)?",
                "explanation": "Trong `[profile.release]`, thiết lập `opt-level = \"z\"` (hoặc \"s\"), `lto = true`, `codegen-units = 1`, `panic = \"abort\"` và `strip = true` giúp nén nhị phân xuống kích thước siêu nhỏ lý tưởng cho malware.",
                "choices": [
                    {"content": "opt-level = 'z', lto = true, strip = true, panic = 'abort'", "is_correct": True, "position": 1},
                    {"content": "debug = true, overflow-checks = true", "is_correct": False, "position": 2},
                    {"content": "incremental = true, codegen-units = 256", "is_correct": False, "position": 3},
                    {"content": "edition = '2015', rpath = true", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH4_Q06",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Kỹ thuật vô hiệu hóa EDR Userland Hooks",
                "question_type": "SINGLE_CHOICE",
                "content": "Các giải pháp EDR hiện đại (như CrowdStrike, Defender for Endpoint) thường giám sát các hàm API nhạy cảm bằng kỹ thuật nào trong không gian Userland?",
                "explanation": "EDR inject một DLL giám sát vào tiến trình của người dùng và cài đặt 'inline hook' (thường là lệnh JMP 5-byte) tại phần đầu (prologue) của các hàm API quan trọng trong `ntdll.dll` để chặn bắt tham số.",
                "choices": [
                    {"content": "Inline API Hooking (chèn lệnh JMP tại phần đầu hàm trong ntdll.dll để kiểm tra hành vi)", "is_correct": True, "position": 1},
                    {"content": "Đóng băng toàn bộ kết nối Internet của máy tính nạn nhân", "is_correct": False, "position": 2},
                    {"content": "Chụp ảnh webcam người dùng mỗi 5 giây", "is_correct": False, "position": 3},
                    {"content": "Khóa bàn phím và chuột khi phát hiện tệp tin mới", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH4_Q07",
                "difficulty": "APPLY",
                "learning_objective": "Kỹ thuật Direct System Calls (Syscalls) trong Rust",
                "question_type": "SINGLE_CHOICE",
                "content": "Để vượt qua các inline hook của EDR cài đặt trong `ntdll.dll`, mã độc viết bằng Rust có thể áp dụng kỹ thuật nào?",
                "explanation": "Kỹ thuật Direct Syscalls (hoặc Indirect Syscalls như Hell's Gate / Halos Gate) trực tiếp đưa số hiệu syscall (SSN) vào thanh ghi EAX và gọi lệnh `syscall` bằng hợp ngữ inline asm, bỏ qua hoàn toàn wrapper ntdll bị hook.",
                "choices": [
                    {"content": "Sử dụng Direct / Indirect Syscalls gọi trực tiếp số hiệu SSN vào Kernel thông qua inline assembly", "is_correct": True, "position": 1},
                    {"content": "Khởi động lại máy tính nạn nhân vào chế độ Safe Mode", "is_correct": False, "position": 2},
                    {"content": "Đổi tên tệp tin thực thi thành notepad.exe", "is_correct": False, "position": 3},
                    {"content": "Tắt nguồn card mạng Wi-Fi trước khi thực thi", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH4_Q08",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Vượt qua AMSI (Antimalware Scan Interface)",
                "question_type": "TRUE_FALSE",
                "content": "AMSI (Antimalware Scan Interface) của Microsoft chỉ hoạt động với PowerShell script và hoàn toàn vô tác dụng đối với các tệp tin thực thi nhị phân (.exe) độc hại.",
                "explanation": "Sai. AMSI được tích hợp sâu vào PowerShell, VBScript, JavaScript, .NET CLR và các ứng dụng có đăng ký kiểm tra buffer bộ nhớ trước khi thực thi.",
                "choices": [
                    {"content": "Đúng", "is_correct": False, "position": 1},
                    {"content": "Sai", "is_correct": True, "position": 2},
                ]
            },
            {
                "code": "CH4_Q09",
                "difficulty": "APPLY",
                "learning_objective": "Mã hóa chuỗi chuỗi ký tự (String Encryption) trong mã nguồn Rust",
                "question_type": "SINGLE_CHOICE",
                "content": "Tại sao trong phát triển phần mềm tấn công, lập trình viên không bao giờ nên để chuỗi ký tự dạng plain-text (vd: URL C2, tên API) trong mã nguồn Rust?",
                "explanation": "Các chuỗi plain-text sẽ nằm nguyên vẹn trong phân vùng `.rdata` của file nhị phân PE/ELF, giúp công cụ phân tích (như `strings` hay AV static signatures) phát hiện và gắn cờ mã độc tức thì.",
                "choices": [
                    {"content": "Vì chuỗi trần sẽ bị trích xuất dễ dàng bởi tiện ích `strings` và bộ lọc chữ ký tĩnh của AV", "is_correct": True, "position": 1},
                    {"content": "Vì Rust không hỗ trợ kiểu dữ liệu chuỗi ký tự String", "is_correct": False, "position": 2},
                    {"content": "Vì chuỗi trần làm tốc độ biên dịch của Cargo bị chậm đi 50%", "is_correct": False, "position": 3},
                    {"content": "Vì hệ điều hành Windows sẽ từ chối chạy các chương trình có chứa ký tự tiếng Anh", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH4_Q10",
                "difficulty": "REMEMBER",
                "learning_objective": "Thao tác Raw Sockets trong lập trình mạng Rust",
                "question_type": "SINGLE_CHOICE",
                "content": "Crate nổi tiếng nào trong hệ sinh thái Rust thường được sử dụng để xây dựng và phân tích các gói tin mạng cấp thấp tùy biến (Raw Network Packets)?",
                "explanation": "`pnet` (libpnet) là crate hàng đầu trong Rust cung cấp các kiểu dữ liệu và phương thức an toàn để tạo lập và phân tích các gói tin Ethernet, IP, TCP, UDP ở tầng raw socket.",
                "choices": [
                    {"content": "pnet (libpnet)", "is_correct": True, "position": 1},
                    {"content": "serde_json", "is_correct": False, "position": 2},
                    {"content": "actix-web", "is_correct": False, "position": 3},
                    {"content": "diesel", "is_correct": False, "position": 4},
                ]
            }
        ]
    }

def get_chapter_5_quiz_data():
    return {
        "title": "Bài Kiểm Tra Đánh Giá Năng Lực Chương 5: Đánh Giá An Ninh & Tấn Công Khai Thác Hệ Thống GraphQL",
        "description": "Bài kiểm tra chính thức 10 câu hỏi bao quát việc khai thác lỗ hổng GraphQL, lạm dụng Introspection, tấn công DoS đệ quy, Batching brute-force, BOLA/IDOR trong Resolvers và chiến lược phòng thủ.",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 25,
        "attempt_limit": 3,
        "passing_percent": Decimal("80.00"),
        "points_per_question": Decimal("10.00"),
        "questions": [
            {
                "code": "CH5_Q01",
                "difficulty": "UNDERSTAND",
                "learning_objective": "So sánh kiến trúc GraphQL với REST API truyền thống",
                "question_type": "SINGLE_CHOICE",
                "content": "Điểm khác biệt kiến trúc cốt lõi giữa GraphQL và REST API truyền thống là gì?",
                "explanation": "REST phân tán tài nguyên qua nhiều endpoint URL và phương thức HTTP khác nhau, trong khi GraphQL chỉ sử dụng duy nhất một endpoint (thường là POST /graphql) tiếp nhận query tùy biến của client.",
                "choices": [
                    {"content": "GraphQL tiếp nhận mọi thao tác truy vấn và biến đổi thông qua duy nhất một endpoint duy nhất (Single Endpoint)", "is_correct": True, "position": 1},
                    {"content": "GraphQL không sử dụng giao thức HTTP mà chạy trên UDP", "is_correct": False, "position": 2},
                    {"content": "GraphQL chỉ có thể trả về định dạng dữ liệu XML", "is_correct": False, "position": 3},
                    {"content": "REST API không hỗ trợ cơ chế xác thực người dùng", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH5_Q02",
                "difficulty": "APPLY",
                "learning_objective": "Khai thác tính năng Introspection trong GraphQL",
                "question_type": "SINGLE_CHOICE",
                "content": "Tính năng Introspection trong GraphQL nếu không bị vô hiệu hóa trên môi trường Production sẽ dẫn tới rủi ro an ninh nghiêm trọng nào?",
                "explanation": "Introspection query (`__schema`) cho phép bất kỳ ai cũng có thể kết xuất toàn bộ lược đồ dữ liệu hệ thống (Schema Dump), bao gồm tất cả Types, Queries, Mutations bí mật và trường nhạy cảm.",
                "choices": [
                    {"content": "Cho phép kẻ tấn công tải về toàn bộ Schema hoàn chỉnh của hệ thống bao gồm các hàm và trường nhạy cảm", "is_correct": True, "position": 1},
                    {"content": "Xóa sạch toàn bộ dữ liệu trong cơ sở dữ liệu ngay lập tức", "is_correct": False, "position": 2},
                    {"content": "Tự động cấp quyền Root quản trị viên cho mọi tài khoản người dùng", "is_correct": False, "position": 3},
                    {"content": "Làm hỏng chứng chỉ SSL của máy chủ web", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH5_Q03",
                "difficulty": "APPLY",
                "learning_objective": "Tấn công Từ chối Dịch vụ (DoS) qua Circular Query",
                "question_type": "SINGLE_CHOICE",
                "content": "Cơ chế nào cho phép tin tặc thực hiện tấn công Từ chối dịch vụ (DoS) làm cạn kiệt tài nguyên CPU và RAM của GraphQL Server chỉ bằng một truy vấn duy nhất?",
                "explanation": "Lồng ghép quan hệ đệ quy vòng lặp sâu vô tận (Circular / Nested Recursive Query) giữa các bảng liên kết (vd: Thread -> Comments -> Author -> Threads) buộc server tính toán hàm mũ tài nguyên.",
                "choices": [
                    {"content": "Lồng ghép các trường đệ quy vòng lặp vô tận (Nested Circular Query) khai thác mối quan hệ giữa các thực thể", "is_correct": True, "position": 1},
                    {"content": "Gửi một file ảnh kích thước lớn hơn 50MB", "is_correct": False, "position": 2},
                    {"content": "Gửi tiêu đề User-Agent chứa ký tự đặc biệt", "is_correct": False, "position": 3},
                    {"content": "Truy cập vào trang đăng nhập quá 5 lần trong một phút", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH5_Q04",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Kỹ thuật Batching Attack vượt giới hạn Rate Limit",
                "question_type": "SINGLE_CHOICE",
                "content": "Kỹ thuật 'Query Batching' hoặc 'Aliases' trong GraphQL giúp kẻ tấn công vượt qua cơ chế giới hạn tần suất (Rate Limiting) tầng HTTP như thế nào?",
                "explanation": "Kẻ tấn công gom hàng trăm phép thử (như đoán OTP hay mật khẩu) vào cùng một HTTP Request duy nhất bằng nhiều mutation hoặc aliases, khiến WAF tầng HTTP chỉ tính là 1 request.",
                "choices": [
                    {"content": "Gửi hàng trăm phép thử brute-force trong cùng một HTTP Request duy nhất khiến WAF chỉ ghi nhận 1 lượt truy cập", "is_correct": True, "position": 1},
                    {"content": "Thay đổi địa chỉ IP liên tục trong tiêu đề X-Forwarded-For", "is_correct": False, "position": 2},
                    {"content": "Mã hóa toàn bộ truy vấn bằng khóa RSA 4096-bit", "is_correct": False, "position": 3},
                    {"content": "Chuyển phương thức HTTP từ POST sang OPTIONS", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH5_Q05",
                "difficulty": "APPLY",
                "learning_objective": "Phát hiện lỗ hổng BOLA / IDOR trong Resolver",
                "question_type": "SINGLE_CHOICE",
                "content": "Lỗ hổng BOLA (Broken Object Level Authorization) trong GraphQL thường phát sinh do nguyên nhân cốt lõi nào trong mã nguồn backend?",
                "explanation": "Resolver tin tưởng trực tiếp tham số ID do client truyền lên (vd: `user(id: 123)`) và truy vấn thẳng vào CSDL mà không kiểm tra đối tượng đó có thuộc sở hữu của người dùng hiện tại hay không.",
                "choices": [
                    {"content": "Hàm Resolver truy vấn trực tiếp bản ghi theo ID từ tham số mà không kiểm tra quyền sở hữu của người dùng đang đăng nhập", "is_correct": True, "position": 1},
                    {"content": "Máy chủ cơ sở dữ liệu bị mất kết nối mạng Internet", "is_correct": False, "position": 2},
                    {"content": "Lập trình viên quên không biên dịch mã nguồn sang file nhị phân", "is_correct": False, "position": 3},
                    {"content": "Người dùng không kích hoạt JavaScript trên trình duyệt", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH5_Q06",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Tấn công tiêm nhiễm SQL / NoSQL qua GraphQL",
                "question_type": "TRUE_FALSE",
                "content": "GraphQL có cơ chế định kiểu dữ liệu nghiêm ngặt (Strict Schema Typing) nên hoàn toàn miễn nhiễm với các cuộc tấn công SQL Injection và NoSQL Injection.",
                "explanation": "Sai. Type checking của GraphQL chỉ xác thực kiểu dữ liệu đầu vào (vd: String, Int). Nếu bên trong Resolver, lập trình viên ghép chuỗi thô vào câu lệnh SQL thì SQLi vẫn diễn ra bình thường.",
                "choices": [
                    {"content": "Đúng", "is_correct": False, "position": 1},
                    {"content": "Sai", "is_correct": True, "position": 2},
                ]
            },
            {
                "code": "CH5_Q07",
                "difficulty": "APPLY",
                "learning_objective": "Tấn công Cross-Site WebSocket Hijacking (CSWSH)",
                "question_type": "SINGLE_CHOICE",
                "content": "Tính năng GraphQL Subscriptions chạy trên nền giao thức WebSockets có thể bị tấn công CSWSH nếu máy chủ thiếu cơ chế kiểm tra nào?",
                "explanation": "Trong WebSocket handshake, trình duyệt tự động gửi kèm cookie xác thực. Nếu server không kiểm tra tiêu đề `Origin` của request, trang web độc hại của tin tặc có thể mở WebSocket và đánh cắp dữ liệu realtime.",
                "choices": [
                    {"content": "Xác thực nghiêm ngặt tiêu đề Origin (Origin Header Validation) trong quá trình bắt tay WebSocket Handshake", "is_correct": True, "position": 1},
                    {"content": "Kiểm tra kích thước màn hình của người dùng", "is_correct": False, "position": 2},
                    {"content": "Bắt buộc người dùng phải gõ mã Captcha mỗi khi nhận tin nhắn mới", "is_correct": False, "position": 3},
                    {"content": "Giới hạn tốc độ gõ phím không quá 10 ký tự/giây", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH5_Q08",
                "difficulty": "REMEMBER",
                "learning_objective": "Nhận biết công cụ pentest GraphQL chuyên dụng",
                "question_type": "SINGLE_CHOICE",
                "content": "Bộ công cụ mã nguồn mở viết bằng Python/CLI nào được sử dụng rộng rãi để tự động quét, trích xuất schema và kiểm thử lỗ hổng GraphQL?",
                "explanation": "`Clairvoyance`, `InQL` và `GraphQLMap` là những công cụ hàng đầu giúp pentester tự động trích xuất schema ngay cả khi Introspection bị tắt một phần và tạo payload kiểm thử.",
                "choices": [
                    {"content": "InQL (hoặc Clairvoyance, GraphQLMap)", "is_correct": True, "position": 1},
                    {"content": "Aircrack-ng", "is_correct": False, "position": 2},
                    {"content": "John the Ripper", "is_correct": False, "position": 3},
                    {"content": "Wireshark Packet Dissector", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH5_Q09",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Giải pháp Query Depth Limiting phòng thủ DoS",
                "question_type": "SINGLE_CHOICE",
                "content": "Biện pháp phòng thủ nào là hiệu quả nhất để ngăn chặn các truy vấn GraphQL lồng nhau quá sâu làm sập máy chủ backend?",
                "explanation": "Cấu hình Query Depth Limiting (giới hạn độ sâu tối đa của AST, ví dụ không quá 5-7 tầng) sẽ loại bỏ ngay lập tức các truy vấn lồng nhau quá mức trước khi tiến hành thực thi.",
                "choices": [
                    {"content": "Thiết lập quy tắc Query Depth Limiting để từ chối các truy vấn có độ lồng cây AST vượt ngưỡng cho phép", "is_correct": True, "position": 1},
                    {"content": "Tăng gấp đôi dung lượng RAM máy chủ mỗi tháng", "is_correct": False, "position": 2},
                    {"content": "Cấm người dùng sử dụng phương thức POST", "is_correct": False, "position": 3},
                    {"content": "Chuyển cơ sở dữ liệu sang chạy trên hệ điều hành MS-DOS", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "CH5_Q10",
                "difficulty": "APPLY",
                "learning_objective": "Cơ chế Query Cost Analysis và Whitelisting",
                "question_type": "SINGLE_CHOICE",
                "content": "Chiến lược an ninh tối thượng ('Gold Standard') để bảo vệ GraphQL endpoint của ứng dụng Mobile/SPA trong môi trường Production là gì?",
                "explanation": "Sử dụng Persistent Queries (Query Whitelisting / Allowlisting), trong đó chỉ những truy vấn được định nghĩa trước khi build ứng dụng mới được server chấp nhận thực thi qua mã băm SHA-256.",
                "choices": [
                    {"content": "Triển khai Persistent Queries (Automatic Persisted Queries với strict Allowlist)", "is_correct": True, "position": 1},
                    {"content": "Đặt mật khẩu bảo vệ endpoint và gửi mật khẩu qua tin nhắn SMS", "is_correct": False, "position": 2},
                    {"content": "Yêu cầu người dùng cài đặt thêm plugin trên điện thoại", "is_correct": False, "position": 3},
                    {"content": "Chặn toàn bộ truy cập đến từ các thiết bị di động", "is_correct": False, "position": 4},
                ]
            }
        ]
    }

def get_final_exam_data():
    return {
        "title": "Bài Thi Tốt Nghiệp Khóa Học: An Ninh Mạng Mũ Đen Toàn Diện (Final Comprehensive Exam)",
        "description": "Bài thi chính thức gồm 20 câu hỏi đánh giá tổng hợp toàn diện kiến thức chuyên sâu 5 phân hệ: Mạng Tor, Hệ điều hành Amnesic & OPSEC, Mã độc Dark Web & C2, Lập trình khai thác Rust FFI, và Đánh giá an ninh GraphQL.",
        "assessment_type": "FINAL",
        "time_limit_minutes": 50,
        "attempt_limit": 2,
        "passing_percent": Decimal("75.00"),
        "points_per_question": Decimal("5.00"),
        "questions": [
            # 4 questions from Chapter 1 (Tor)
            {
                "code": "FIN_Q01",
                "difficulty": "APPLY",
                "learning_objective": "Phân tích luồng dữ liệu Tor circuit",
                "question_type": "SINGLE_CHOICE",
                "content": "Giả sử một kẻ tấn công nghe lén đường truyền mạng giữa Client và Entry Guard của Tor, kẻ tấn công có thể thu thập được thông tin nào?",
                "explanation": "Kẻ nghe lén chỉ biết được rằng Client đang kết nối tới một máy chủ Tor Relay (IP của Guard), nhưng không thể biết đích đến cuối cùng hoặc nội dung bên trong các lớp mã hóa củ hành.",
                "choices": [
                    {"content": "Biết Client đang kết nối tới một Entry Guard của Tor, nhưng không biết nội dung hay đích đến cuối cùng", "is_correct": True, "position": 1},
                    {"content": "Biết chính xác tên miền web .onion và nội dung trang web Client đang xem", "is_correct": False, "position": 2},
                    {"content": "Biết mật khẩu tài khoản người dùng đang gõ trên trình duyệt", "is_correct": False, "position": 3},
                    {"content": "Giải mã được toàn bộ lưu lượng qua khóa bí mật của Exit Node", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q02",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Cấu trúc định danh Onion Service v3",
                "question_type": "SINGLE_CHOICE",
                "content": "Tại sao tên miền Onion v3 lại miễn nhiễm với tấn công Enumeration Directory tấn công vét cạn danh mục hơn hẳn Onion v2 cũ?",
                "explanation": "Onion v3 sử dụng thuật toán phái sinh khóa bí mật và blinded public keys để lưu trữ descriptor trên HSDir, khiến các node thư mục không thể liệt kê hay giải mã danh tính dịch vụ ẩn nếu không có public key gốc.",
                "choices": [
                    {"content": "Sử dụng cơ chế Blinded Public Keys khiến HSDir node không thể giải mã hay liệt kê danh mục dịch vụ ẩn", "is_correct": True, "position": 1},
                    {"content": "Vì tên miền v3 ngắn hơn nên máy quét không thể tìm ra", "is_correct": False, "position": 2},
                    {"content": "Vì v3 yêu cầu mật khẩu đăng nhập trước khi tải trang web", "is_correct": False, "position": 3},
                    {"content": "Vì toàn bộ mạng lưới v3 được quản lý bởi công ty Google", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q03",
                "difficulty": "APPLY",
                "learning_objective": "Sử dụng Tor Bridges chống kiểm duyệt",
                "question_type": "SINGLE_CHOICE",
                "content": "Khi một quốc gia kích hoạt Great Firewall chặn toàn bộ dải IP của các Tor Relay công khai, giải pháp nào giúp người dùng kết nối mạng Tor thành công?",
                "explanation": "Tor Bridges là các node trung chuyển bí mật không được công bố công khai trong consensus document, kết hợp với Pluggable Transports (như obfs4, meek, snowflake) để vượt qua bộ lọc tường lửa.",
                "choices": [
                    {"content": "Sử dụng Tor Bridges không công bố công khai kết hợp với Pluggable Transports (obfs4 / Snowflake)", "is_correct": True, "position": 1},
                    {"content": "Đổi cổng kết nối của card mạng máy tính sang cổng 21", "is_correct": False, "position": 2},
                    {"content": "Tắt tính năng mã hóa trên trình duyệt Tor Browser", "is_correct": False, "position": 3},
                    {"content": "Xóa toàn bộ bộ nhớ cache DNS của hệ điều hành", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q04",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Ngăn chặn rò rỉ DNS qua Tor Socks5",
                "question_type": "SINGLE_CHOICE",
                "content": "Khi cấu hình ứng dụng bên thứ ba (như cURL hoặc Python) chạy qua Tor, tại sao ta bắt buộc phải sử dụng `socks5h://` thay vì `socks5://`?",
                "explanation": "Tiền tố `socks5h://` chỉ định rằng việc phân giải tên miền (DNS Resolution) phải được ủy quyền thực hiện từ xa tại Exit Node của Tor, ngăn chặn rò rỉ DNS cục bộ (Local DNS Leak) tại máy Client.",
                "choices": [
                    {"content": "Để phân giải DNS từ xa tại Exit Node, ngăn chặn hoàn toàn việc lộ truy vấn DNS tại máy Client", "is_correct": True, "position": 1},
                    {"content": "Để tăng gấp đôi tốc độ tải xuống dữ liệu", "is_correct": False, "position": 2},
                    {"content": "Vì giao thức socks5 không hỗ trợ kết nối mạng Internet", "is_correct": False, "position": 3},
                    {"content": "Để cho phép ứng dụng gửi email nặc danh tự động", "is_correct": False, "position": 4},
                ]
            },

            # 4 questions from Chapter 2 (OPSEC & Anonymity)
            {
                "code": "FIN_Q05",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Đặc tính bảo mật của Tails OS Persistence Storage",
                "question_type": "SINGLE_CHOICE",
                "content": "Phân vùng Persistent Storage trên Tails OS được bảo vệ bằng công nghệ mã hóa nào để đảm bảo dữ liệu lưu lại an toàn?",
                "explanation": "Tails OS sử dụng LUKS (Linux Unified Key Setup) với thuật toán mã hóa đối xứng AES-XTS 512-bit để bảo vệ phân vùng lưu trữ lâu dài của người dùng.",
                "choices": [
                    {"content": "Mã hóa phân vùng ổ đĩa LUKS (Linux Unified Key Setup) với AES-XTS", "is_correct": True, "position": 1},
                    {"content": "Nén file dạng ZIP có mật khẩu 6 ký tự", "is_correct": False, "position": 2},
                    {"content": "Lưu file văn bản thô trên USB ẩn danh", "is_correct": False, "position": 3},
                    {"content": "Mã hóa MD5 một chiều không thể đảo ngược", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q06",
                "difficulty": "APPLY",
                "learning_objective": "Kỹ thuật chống Forensic phân tích siêu dữ liệu (Metadata)",
                "question_type": "SINGLE_CHOICE",
                "content": "Trước khi phát tán một tài liệu PDF hoặc ảnh chụp nhạy cảm lên Internet, công cụ nào sau đây giúp loại bỏ triệt để siêu dữ liệu EXIF/GPS?",
                "explanation": "MAT2 (Metadata Anonymisation Toolkit v2) hoặc ExifTool là công cụ chuyên dụng giúp phân tích và xóa sạch toàn bộ siêu dữ liệu địa lý GPS, thông tin máy ảnh và định danh tác giả.",
                "choices": [
                    {"content": "MAT2 (Metadata Anonymisation Toolkit) hoặc ExifTool", "is_correct": True, "position": 1},
                    {"content": "Adobe Acrobat Pro watermark generator", "is_correct": False, "position": 2},
                    {"content": "Microsoft Paint crop tool", "is_correct": False, "position": 3},
                    {"content": "Windows Defender offline scanner", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q07",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Nguyên lý ký khóa PGP Web of Trust",
                "question_type": "SINGLE_CHOICE",
                "content": "Mô hình mạng lưới tín nhiệm (Web of Trust - WoT) của PGP xác thực tính chính danh của một Public Key thông qua cơ chế nào?",
                "explanation": "Trong PGP Web of Trust, không có cơ quan cấp chứng chỉ trung tâm (CA); thay vào đó các thành viên tin tưởng lẫn nhau bằng cách ký số chéo (cross-signing) lên public key của người khác.",
                "choices": [
                    {"content": "Các người dùng tự ký số xác nhận lẫn nhau theo phân cấp tín nhiệm phi tập trung không cần CA trung tâm", "is_correct": True, "position": 1},
                    {"content": "Bộ Thông tin và Truyền thông trực tiếp cấp giấy phép số", "is_correct": False, "position": 2},
                    {"content": "Tự động xác thực qua tin nhắn xác nhận trên mạng xã hội Facebook", "is_correct": False, "position": 3},
                    {"content": "Sử dụng mã OTP gửi về số điện thoại cá nhân", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q08",
                "difficulty": "APPLY",
                "learning_objective": "Bảo mật kênh trao đổi trực tiếp với OTR / OMEMO",
                "question_type": "SINGLE_CHOICE",
                "content": "Đặc tính an ninh mật mã 'Perfect Forward Secrecy' (PFS) trong giao thức liên lạc bảo mật (như Signal/OMEMO) đảm bảo điều gì?",
                "explanation": "PFS sinh khóa phiên tạm thời (ephemeral keys) cho mỗi tin nhắn; do đó ngay cả khi khóa dài hạn của người dùng bị lộ trong tương lai thì toàn bộ tin nhắn đã trao đổi trong quá khứ vẫn không thể bị giải mã.",
                "choices": [
                    {"content": "Dù khóa bí mật dài hạn bị lộ trong tương lai, kẻ tấn công vẫn không thể giải mã các tin nhắn cũ trong quá khứ", "is_correct": True, "position": 1},
                    {"content": "Tin nhắn sẽ tự động gửi tới tất cả người dùng trong danh bạ", "is_correct": False, "position": 2},
                    {"content": "Người gửi có thể thu hồi tin nhắn trên máy người nhận bất kỳ lúc nào", "is_correct": False, "position": 3},
                    {"content": "Tốc độ truyền tin luôn đạt chuẩn cáp quang quân sự", "is_correct": False, "position": 4},
                ]
            },

            # 4 questions from Chapter 3 (Malware & Dark Web)
            {
                "code": "FIN_Q09",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Kiến trúc mã hóa lai của Ransomware",
                "question_type": "SINGLE_CHOICE",
                "content": "Tại sao mã độc Ransomware hiện đại luôn sử dụng mô hình mã hóa lai (Hybrid Encryption: AES-GCM kết hợp RSA/ECC) để mã hóa tập tin nạn nhân?",
                "explanation": "AES đối xứng mã hóa tệp tin với tốc độ cực nhanh, sau đó khóa AES này được mã hóa bảo vệ bằng khóa công khai RSA/ECC của tin tặc. Nạn nhân chỉ có thể giải mã khi có khóa bí mật RSA từ C2.",
                "choices": [
                    {"content": "Tận dụng tốc độ mã hóa cực nhanh của thuật toán đối xứng (AES) và bảo vệ khóa phiên an toàn bằng thuật toán bất đối xứng (RSA/ECC)", "is_correct": True, "position": 1},
                    {"content": "Vì hệ điều hành Windows không hỗ trợ chạy riêng thuật toán AES", "is_correct": False, "position": 2},
                    {"content": "Để làm cho kích thước tập tin sau khi mã hóa bị thu nhỏ lại 90%", "is_correct": False, "position": 3},
                    {"content": "Nhằm mục đích tránh bị phần mềm diệt virus phát hiện vì dung lượng file lớn", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q10",
                "difficulty": "APPLY",
                "learning_objective": "Kỹ thuật phân tích động Dynamic Malware Analysis",
                "question_type": "SINGLE_CHOICE",
                "content": "Khi phân tích động một mẫu mã độc trong môi trường cô lập, chuyên gia sử dụng công cụ FakeNet-NG / INetSim nhằm mục đích gì?",
                "explanation": "FakeNet-NG / INetSim giả lập các dịch vụ Internet thông dụng (DNS, HTTP, HTTPS, SMTP) để đánh lừa mã độc tưởng rằng có mạng thật, kích hoạt hành vi kết nối C2 để ghi nhận log phân tích.",
                "choices": [
                    {"content": "Giả lập toàn bộ các phản hồi dịch vụ Internet (DNS, HTTP, SSL) để kích hoạt và ghi nhận hành vi kết nối C2 của mã độc", "is_correct": True, "position": 1},
                    {"content": "Tấn công ngược lại máy chủ của kẻ phát tán mã độc", "is_correct": False, "position": 2},
                    {"content": "Tự động tạo ra mã nguồn C++ hoàn chỉnh từ file nhị phân", "is_correct": False, "position": 3},
                    {"content": "Tải mẫu mã độc lên mạng xã hội để người khác kiểm thử", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q11",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Cơ chế hoạt động của Dead Man's Switch",
                "question_type": "SINGLE_CHOICE",
                "content": "Khái niệm 'Dead Man's Switch' trong các tổ chức ngầm hoặc hoạt động an ninh thông tin được hiểu là gì?",
                "explanation": "Dead Man's Switch là cơ chế tự động thực hiện hành vi định trước (như phát tán dữ liệu mật hoặc xóa sạch ổ cứng) nếu người vận hành không thực hiện việc check-in định kỳ theo lịch trình.",
                "choices": [
                    {"content": "Cơ chế tự động giải phóng thông tin hoặc tiêu hủy dữ liệu nếu chủ sở hữu không thực hiện xác thực định kỳ theo chu kỳ", "is_correct": True, "position": 1},
                    {"content": "Cầu dao điện tự ngắt khi máy chủ bị sét đánh trúng", "is_correct": False, "position": 2},
                    {"content": "Phím tắt khẩn cấp trên bàn phím để tắt màn hình máy tính", "is_correct": False, "position": 3},
                    {"content": "Chương trình tự động tắt máy khi người dùng không di chuột trong 15 phút", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q12",
                "difficulty": "APPLY",
                "learning_objective": "Phương pháp điều tra bẫy Canary Tokens",
                "question_type": "SINGLE_CHOICE",
                "content": "Việc cấy một 'Canary Token' (như tài liệu Word giả mạo chứa webhook ẩn) vào thư mục nội bộ mang lại lợi ích gì cho đội ngũ phòng thủ Blue Team?",
                "explanation": "Khi tin tặc xâm nhập và mở tài liệu bẫy, webhook sẽ tự động gửi cảnh báo tức thì kèm địa chỉ IP và môi trường của kẻ xâm nhập về cho trung tâm điều hành SOC.",
                "choices": [
                    {"content": "Kích hoạt cảnh báo thời gian thực kèm IP và thông tin máy tính của kẻ tấn công ngay khi tài liệu bị mở", "is_correct": True, "position": 1},
                    {"content": "Mã hóa toàn bộ máy tính của tin tặc để trả đũa", "is_correct": False, "position": 2},
                    {"content": "Tăng cường tính năng định dạng văn bản cho Microsoft Office", "is_correct": False, "position": 3},
                    {"content": "Tự động sao lưu dữ liệu lên Google Drive mỗi ngày", "is_correct": False, "position": 4},
                ]
            },

            # 4 questions from Chapter 4 (Rust Exploits)
            {
                "code": "FIN_Q13",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Tương tác FFI và chuyển đổi kiểu dữ liệu trong Rust",
                "question_type": "SINGLE_CHOICE",
                "content": "Khi truyền một chuỗi ký tự từ Rust sang các hàm Windows API C-style (như `CreateFileA` hoặc `LoadLibraryA`), kiểu dữ liệu nào bắt buộc phải được sử dụng để đảm bảo có null-terminator `\\0`?",
                "explanation": "Trong Rust, `std::ffi::CString` đại diện cho chuỗi byte kết thúc bằng byte null `\\0` tương thích chuẩn với con trỏ `const char*` trong C/C++.",
                "choices": [
                    {"content": "std::ffi::CString (hoặc CStr)", "is_correct": True, "position": 1},
                    {"content": "std::string::String thông thường", "is_correct": False, "position": 2},
                    {"content": "u64 integer array", "is_correct": False, "position": 3},
                    {"content": "Vec<bool> vector", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q14",
                "difficulty": "APPLY",
                "learning_objective": "Kỹ thuật phản xạ DLL Injection (Reflective DLL Loading)",
                "question_type": "SINGLE_CHOICE",
                "content": "Điểm độc đáo của kỹ thuật Reflective DLL Injection viết bằng Rust so với DLL Injection truyền thống là gì?",
                "explanation": "Reflective DLL Injection tự thực hiện công việc của Windows PE Loader trong bộ nhớ, nạp DLL trực tiếp từ buffer RAM vào tiến trình mục tiêu mà không bao giờ ghi tệp DLL xuống ổ cứng hay gọi API `LoadLibrary`.",
                "choices": [
                    {"content": "Tự phân tích và ánh xạ PE header trong bộ nhớ, nạp DLL trực tiếp từ RAM mà không cần ghi file xuống đĩa hay gọi LoadLibrary", "is_correct": True, "position": 1},
                    {"content": "Yêu cầu máy tính phải cài đặt sẵn môi trường Microsoft Visual Studio", "is_correct": False, "position": 2},
                    {"content": "Chỉ hoạt động được trên các máy chủ chạy hệ điều hành macOS", "is_correct": False, "position": 3},
                    {"content": "Tự động đổi màu giao diện của cửa sổ ứng dụng mục tiêu", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q15",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Kỹ thuật che giấu lưu lượng C2 qua HTTPS Domain Fronting",
                "question_type": "SINGLE_CHOICE",
                "content": "Kỹ thuật 'Domain Fronting' được mã độc sử dụng để ngụy trang lưu lượng kết nối C2 thông qua các mạng phân phối nội dung (CDN) hoạt động trên nguyên lý nào?",
                "explanation": "Domain Fronting khai thác sự khác biệt giữa tên miền trong SNI (Server Name Indication) ở tầng TLS handshake (tên miền uy tín được phép) và tiêu đề `Host` ở tầng HTTP request bên trong (tên miền C2 thực tế của tin tặc).",
                "choices": [
                    {"content": "Khác biệt giữa tên miền hợp pháp trong TLS SNI và tên miền độc hại thực tế trong tiêu đề HTTP Host header", "is_correct": True, "position": 1},
                    {"content": "Đổi cổng kết nối liên tục từ cổng 80 sang cổng 443", "is_correct": False, "position": 2},
                    {"content": "Gửi tín hiệu qua giao thức sóng radio ngắn", "is_correct": False, "position": 3},
                    {"content": "Sử dụng các trạm phát sóng vệ tinh tư nhân để truyền tin", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q16",
                "difficulty": "APPLY",
                "learning_objective": "Vượt qua kiểm tra chữ ký Authenticode",
                "question_type": "TRUE_FALSE",
                "content": "Việc sử dụng chứng chỉ số bị đánh cắp (Stolen Code-Signing Certificate) để ký số lên tệp nhị phân Rust có thể giúp mã độc vượt qua cảnh báo SmartScreen của Windows và dễ dàng né tránh các bộ lọc Antivirus cơ bản.",
                "explanation": "Đúng. Hệ điều hành và phần mềm bảo vệ có độ tin cậy rất cao đối với các tệp tin có chữ ký số hợp lệ từ các tổ chức phát triển uy tín.",
                "choices": [
                    {"content": "Đúng", "is_correct": True, "position": 1},
                    {"content": "Sai", "is_correct": False, "position": 2},
                ]
            },

            # 4 questions from Chapter 5 (GraphQL Pentesting)
            {
                "code": "FIN_Q17",
                "difficulty": "APPLY",
                "learning_objective": "Xác định lỗ hổng Field Suggestion Information Disclosure",
                "question_type": "SINGLE_CHOICE",
                "content": "Khi tính năng Introspection bị tắt, tính năng mặc định nào của GraphQL Engine (như Apollo/GraphQL-Java) vẫn có thể vô tình tiết lộ tên của các trường nhạy cảm?",
                "explanation": "Tính năng 'Field Suggestion' (Did you mean...?) khi người dùng gõ sai một ký tự sẽ gợi ý trường đúng, cho phép công cụ tự động vét cạn (brute-force schema reconstruction) toàn bộ cấu trúc Schema.",
                "choices": [
                    {"content": "Cơ chế gợi ý sửa lỗi chính tả trường ('Did you mean...?') trong thông báo lỗi", "is_correct": True, "position": 1},
                    {"content": "Tiêu đề Server trong gói tin phản hồi HTTP", "is_correct": False, "position": 2},
                    {"content": "Ghi chú ẩn trong mã nguồn HTML trang 404", "is_correct": False, "position": 3},
                    {"content": "Tính năng tự động định dạng mã JSON đẹp mắt", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q18",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Tấn công GraphQL Batching Brute-Force",
                "question_type": "SINGLE_CHOICE",
                "content": "Giải pháp bảo vệ backend nào sau đây có khả năng ngăn chặn triệt để kỹ thuật tấn công đoán mã PIN/OTP bằng GraphQL Batching/Aliases?",
                "explanation": "Phân tích và tính toán Query Cost / Complexity Analysis gán trọng số điểm cho mỗi mutation/alias trong request và áp dụng Rate Limiting ở tầng ứng dụng (dựa trên IP/tài khoản) sẽ chặn đứng batching brute-force.",
                "choices": [
                    {"content": "Triển khai Query Complexity Analysis tính tổng chi phí truy vấn và giới hạn số lượng mutation tối đa trên mỗi request", "is_correct": True, "position": 1},
                    {"content": "Yêu cầu người dùng sử dụng trình duyệt Google Chrome mới nhất", "is_correct": False, "position": 2},
                    {"content": "Chuyển cơ sở dữ liệu sang dạng phân tán đa vùng", "is_correct": False, "position": 3},
                    {"content": "Đổi tên file endpoint từ /graphql sang /api", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q19",
                "difficulty": "APPLY",
                "learning_objective": "Khai thác Server-Side Request Forgery (SSRF) qua GraphQL",
                "question_type": "SINGLE_CHOICE",
                "content": "Một mutation GraphQL nhận tham số URL để tải ảnh avatar người dùng (vd: `importAvatar(url: String!)`) nếu không được kiểm tra có thể dẫn tới lỗ hổng nghiêm trọng nào?",
                "explanation": "Server-Side Request Forgery (SSRF) cho phép tin tặc yêu cầu máy chủ GraphQL gửi request HTTP tới các tài nguyên nội bộ nhạy cảm (như AWS metadata `http://169.254.169.254/latest/meta-data/`).",
                "choices": [
                    {"content": "Server-Side Request Forgery (SSRF) khai thác truy cập vào dịch vụ nội bộ hoặc Cloud Metadata Service", "is_correct": True, "position": 1},
                    {"content": "Buffer Overflow tràn bộ nhớ đệm card đồ họa", "is_correct": False, "position": 2},
                    {"content": "Clickjacking chiếm đoạt con trỏ chuột người dùng", "is_correct": False, "position": 3},
                    {"content": "Race condition trong luồng nén file ZIP", "is_correct": False, "position": 4},
                ]
            },
            {
                "code": "FIN_Q20",
                "difficulty": "UNDERSTAND",
                "learning_objective": "Kiến trúc phòng thủ GraphQL Defense-in-Depth",
                "question_type": "SINGLE_CHOICE",
                "content": "Trong mô hình phòng thủ theo chiều sâu (Defense-in-Depth) cho hệ thống GraphQL doanh nghiệp, lớp kiểm tra phân quyền (Authorization) bắt buộc phải được đặt ở đâu?",
                "explanation": "Kiểm tra quyền truy cập (Authorization) bắt buộc phải nằm ở tầng Business Logic / Resolvers hoặc Data Service layer bên dưới, tuyệt đối không được chỉ kiểm tra ở tầng ngoài API Gateway.",
                "choices": [
                    {"content": "Tại từng hàm Resolver và tầng Data Business Logic tương ứng với từng thực thể dữ liệu", "is_correct": True, "position": 1},
                    {"content": "Chỉ kiểm tra duy nhất một lần tại trang đăng nhập ban đầu", "is_correct": False, "position": 2},
                    {"content": "Đặt trên trình duyệt phía Client bằng mã JavaScript", "is_correct": False, "position": 3},
                    {"content": "Giao hoàn toàn cho nhà cung cấp dịch vụ mạng Wi-Fi chịu trách nhiệm", "is_correct": False, "position": 4},
                ]
            }
        ]
    }
