"""Builder for Chapter 4: Lập Trình Vũ Khí Tấn Công & Tự Động Hóa An Ninh Mạng Với Rust.
Source book: Black_Hat_Rust.pdf (12 lessons).
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

CHAPTER_4_INFO = {
    "title": "Chương 4: Lập Trình Vũ Khí Tấn Công & Tự Động Hóa An Ninh Mạng Với Rust",
    "source_file": "Black_Hat_Rust.pdf",
    "position": 4,
}


def get_chapter_4_lessons() -> list[dict]:
    lessons = []

    configs = [
        (
            1,
            "Bài 4.1: Tại Sao Rust Là Ngôn Ngữ Tối Thượng Cho Vũ Khí Tấn Công & Kiểm Thử Xâm Nhập?",
            "Phân tích sự dịch chuyển từ C/C++ và Python sang Rust trong vũ khí tấn công mạng: Hiệu năng phần cứng trần, an toàn bộ nhớ và khả năng biên dịch chéo độc lập.",
            "https://www.youtube.com/watch?v=E3zDspItq-w",
            [
                "Hiểu rõ lý do vì sao cộng đồng an ninh tấn công và các nhóm APT chuyển dịch mạnh mẽ sang ngôn ngữ Rust.",
                "So sánh ưu nhược điểm giữa Rust với C/C++, Go và Python trong phát triển công cụ an ninh mạng.",
                "Nắm vững các đặc tính cốt lõi: Tự do khỏi Garbage Collector, tốc độ ngang ngửa C và cơ chế Static Linking."
            ],
            [
                (
                    "Cuộc Cách Mạng Rust Trong Thế Giới Hacker Mũ Đen",
                    "Trong nhiều thập kỷ, thế giới kiểm thử xâm nhập và phát triển mã độc bị chi phối bởi hai thái cực: Một bên là các ngôn ngữ cấp cao như Python/Ruby: Rất dễ viết, phát triển nhanh, nhưng chậm chạp về hiệu năng, ngốn bộ nhớ và đòi hỏi môi trường máy nạn nhân phải cài sẵn trình thông dịch Python (hoặc phải đóng gói bằng PyInstaller cồng kềnh dễ bị antivirus bắt chữ ký). Bên còn lại là C/C++: Tốc độ tối đa, tương tác trực tiếp với API hệ điều hành Windows Win32, nhưng là cơn ác mộng về các lỗi quản lý bộ nhớ (Buffer Overflow, Use-After-Free) khiến công cụ dễ bị crash bất ngờ giữa chiến dịch. Rust ra đời giải quyết triệt để sự giằng xé này: Cung cấp tốc độ và quyền kiểm soát phần cứng thô ngang ngửa C/C++, nhưng sở hữu cơ chế an toàn bộ nhớ tuyệt đối tại thời điểm biên dịch (Compile-time Memory Safety) mà không cần bộ thu gom rác (Garbage Collector)."
                ),
                (
                    "Những Ưu Điểm Độc Tôn Của Rust Cho Công Cụ Tấn Công",
                    "1. Biên Dịch Tĩnh Độc Lập (Static Linking): Trình biên dịch `rustc` có thể đóng gói toàn bộ thư viện phụ thuộc vào một tệp nhị phân `.exe` hoặc ELF duy nhất. Tệp này có thể chạy ngay lập tức trên máy nạn nhân mà không yêu cầu cài đặt bất kỳ dependency nào. 2. Biên Dịch Chéo Thần Tốc (Cross-Compilation): Từ một máy tính Linux, bạn có thể dễ dàng biên dịch ra nhị phân Windows PE x64, macOS Mach-O, hoặc firmware ARM router chỉ bằng một câu lệnh `--target`. 3. Khó Bị Dịch Ngược (Hard to Reverse Engineer): Mã nhị phân biên dịch từ Rust có cấu trúc luồng điều khiển và quản lý bộ nhớ tối ưu hóa rất phức tạp, khiến các công cụ dịch ngược truyền thống (như Ghidra, IDA Pro) gặp nhiều khó khăn trong việc phân tích tự động."
                ),
                (
                    "Sự Trỗi Dậy Của Mã Độc Bằng Rust Trong Thực Tế",
                    "Từ năm 2021 đến nay, các nhóm tội phạm mạng hàng đầu thế giới (như BlackCat/ALPHV, Hive, RustDown) đã chuyển đổi toàn bộ mã nguồn Ransomware của mình sang Rust. Các báo cáo phân tích cho thấy ransomware viết bằng Rust có tốc độ mã hóa file nhanh gấp 3 đến 5 lần so với các thế hệ trước và vượt qua hầu hết các hệ thống EDR dựa trên chữ ký tĩnh."
                )
            ],
            "Kịch bản đối đầu: So Sánh Tốc Độ Quét Cổng Giữa Python Và Rust: Một script quét cổng viết bằng Python socket thông thường mất khoảng 2 phút để quét 1,000 cổng. Trong khi đó, một công cụ quét viết bằng Rust sử dụng lập trình bất đồng bộ Tokio (như RustScan) có thể quét trọn vẹn 65,535 cổng của mục tiêu chỉ trong chưa đầy 3 giây!",
            "Thực hành kiểm tra môi trường Rust và biên dịch chương trình Hello Hacker đầu tiên:",
            ("bash", """# 1. Kiểm tra phiên bản trình biên dịch Rust và trình quản lý gói Cargo
rustc --version
cargo --version

# 2. Khởi tạo một dự án binary mới cho công cụ an ninh
cargo new blackhat_tool --bin
cd blackhat_tool

# 3. Biên dịch chương trình ở chế độ tối ưu hóa Release (bỏ qua debug symbols)
cargo build --release
ls -lh target/release/blackhat_tool"""),
            ["Không biên dịch công cụ tấn công ở chế độ Debug vì tệp nhị phân sẽ chứa đầy đủ đường dẫn thư mục và thông tin cá nhân của bạn.", "Luôn sử dụng cờ `--release` và cấu hình `strip = true` trong Cargo.toml để loại bỏ ký hiệu nhị phân."],
            ["Rust kết hợp hoàn hảo giữa tốc độ của C và sự an toàn bộ nhớ không cần Garbage Collector.", "Tính năng Static Linking và Cross-compilation là lợi thế sống còn cho công cụ pentest.", "Mã nhị phân Rust gây khó khăn lớn cho công tác dịch ngược và phát hiện mã độc."],
            [
                {"question": "Đặc tính nào của Rust giúp công cụ tấn công có thể chạy ngay trên máy nạn nhân mà không cần cài đặt thêm thư viện phụ thuộc?", "type": "MULTIPLE_CHOICE", "options": ["Garbage Collection", "Static Linking (Biên dịch tĩnh)", "JIT Compilation", "Dynamic Interpreting"], "correct_index": 1, "explanation": "Static Linking đóng gói toàn bộ thư viện vào một file thực thi duy nhất."},
                {"question": "Rust sử dụng bộ thu gom rác (Garbage Collector) chạy nền giống như Java và Go để quản lý bộ nhớ?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Rust quản lý bộ nhớ thông qua cơ chế Ownership tại thời điểm biên dịch, hoàn toàn không có Garbage Collector."},
                {"question": "Trình quản lý gói và hệ thống xây dựng dự án chính thức của ngôn ngữ Rust có tên là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Cargo", "cargo"]}], "explanation": "Cargo."}
            ]
        ),
        (
            2,
            "Bài 4.2: Cài Đặt Môi Trường Phát Triển Rust Cho Hacker & Cấu Hình Cargo Tối Ưu",
            "Thiết lập môi trường phát triển vũ khí mạng chuyên nghiệp: Cài đặt Rustup, cấu hình Cross-Compilation sang Windows từ Linux, và tối ưu hóa tệp nhị phân bằng cờ LTO.",
            "https://www.youtube.com/watch?v=11raTwzQVn4",
            [
                "Nắm vững quy trình cài đặt và quản lý toolchain Rust bằng `rustup`.",
                "Thực hành cấu hình biên dịch chéo từ Linux sang Windows PE bằng `mingw-w64`.",
                "Làm chủ các tùy chọn tối ưu hóa trong `Cargo.toml`: LTO (Link-Time Optimization), CodeGen-Units và Strip."
            ],
            [
                (
                    "Quản Lý Toolchain Bằng Rustup",
                    "Trong phát triển công cụ tấn công, việc quản lý các phiên bản trình biên dịch là rất quan trọng vì một số kỹ thuật tiêm mã nâng cao có thể yêu cầu các tính năng thử nghiệm chỉ có trên kênh `nightly`. Công cụ chính thức **rustup** cho phép lập trình viên dễ dàng chuyển đổi giữa các kênh phát hành: Stable (Ổn định), Beta, và Nightly. Chỉ với một dòng lệnh, bạn có thể bổ sung các kiến trúc mục tiêu mới (Targets) để biên dịch sang Windows, ARM, hoặc WebAssembly."
                ),
                (
                    "Biên Dịch Chéo Sang Windows (Cross-compiling to Windows)",
                    "Hầu hết các chuyên gia an ninh và hacker đều sử dụng máy trạm phát triển Linux (Kali Linux, Arch, Ubuntu). Tuy nhiên, hơn 90% mục tiêu tấn công doanh nghiệp lại là hệ điều hành Windows. Thay vì phải mở máy ảo Windows để biên dịch mã nguồn, Rust hỗ trợ biên dịch chéo trực tiếp từ Linux sang tệp nhị phân `.exe` của Windows bằng cách cài đặt target `x86_64-pc-windows-gnu` kết hợp với bộ công cụ GNU Mingw-w64."
                ),
                (
                    "Tối Ưu Hóa Kích Thước & Ẩn Danh Nhị Phân (Binary Stripping & LTO)",
                    "Mặc định, tệp thực thi của Rust có kích thước khá lớn (khoảng 3-5MB cho một chương trình đơn giản) do chứa thông tin gỡ lỗi và bảng ký hiệu. Để thu nhỏ kích thước xuống chỉ còn vài trăm KB và loại bỏ hoàn toàn các chuỗi đường dẫn nhạy cảm trên máy của bạn (như `/home/hacker/secret_project`), chúng ta cấu hình phần `[profile.release]` trong tệp `Cargo.toml`: Bật `opt-level = 'z'` (tối ưu kích thước); Bật `lto = true` (Link-Time Optimization); Thiết lập `codegen-units = 1` và `strip = true`."
                )
            ],
            "Kịch bản thực chiến: Giảm Kích Thước Nhị Phân Payload: Một tệp nhị phân Rust gốc nặng 4.2 MB sau khi áp dụng cấu hình LTO và strip đã giảm xuống chỉ còn 310 KB. Tệp nhỏ giúp việc phát tán qua mạng nhanh hơn gấp 10 lần và giảm thiểu dung lượng ghi log mạng.",
            "Thực hành cấu hình tệp Cargo.toml tối ưu hóa tối đa kích thước nhị phân cho công cụ an ninh:",
            ("toml", """# Cấu hình Cargo.toml tối ưu cho Red Team tooling
[package]
name = "stealth_probe"
version = "0.1.0"
edition = "2021"

[dependencies]
# Thư viện mạng và xử lý lỗi
anyhow = "1.0"

[profile.release]
opt-level = "z"         # Tối ưu hóa kích thước nhị phân tối đa
lto = true              # Bật Link-Time Optimization xuyên suốt các crate
codegen-units = 1       # Giảm số đơn vị sinh mã để tối ưu hóa tốt hơn
panic = "abort"         # Loại bỏ bảng giải cuộn ngăn xếp (stack unwinding)
strip = true            # Tự động loại bỏ toàn bộ symbols và debug info"""),
            ["Tuyệt đối không để lại cờ panic = 'unwind' trong bản release vì thông điệp panic có thể để lộ cấu trúc thư mục nội bộ máy phát triển.", "Kiểm tra kỹ tương thích của các thư viện C khi biên dịch chéo."],
            ["Rustup quản lý linh hoạt giữa các kênh Stable, Beta và Nightly.", "Biên dịch chéo sang Windows từ Linux dễ dàng thông qua Mingw-w64 target.", "Cấu hình LTO, opt-level='z' và strip=true giúp thu nhỏ nhị phân xuống tối đa."],
            [
                {"question": "Công cụ nào được sử dụng để quản lý các phiên bản và toolchain trình biên dịch Rust?", "type": "MULTIPLE_CHOICE", "options": ["Cargo", "Rustup", "Pip", "NPM"], "correct_index": 1, "explanation": "Rustup là công cụ quản lý toolchain chính thức của Rust."},
                {"question": "Tùy chọn nào trong Cargo.toml cho phép loại bỏ toàn bộ thông tin gỡ lỗi và symbols khỏi tệp nhị phân đầu ra?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["strip = true", "strip", "strip=true"]}], "explanation": "Cờ strip = true."},
                {"question": "Từ một máy tính Linux, lập trình viên Rust bắt buộc phải cài máy ảo Windows mới có thể tạo ra tệp thực thi .exe?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Rust hỗ trợ biên dịch chéo trực tiếp sang Windows (.exe) từ Linux."}
            ]
        ),
        (
            3,
            "Bài 4.3: Mô Hình An Toàn Bộ Nhớ Của Rust: Quyền Sở Hữu (Ownership) & Mượn (Borrowing)",
            "Giải mã trái tim của ngôn ngữ Rust: Ba quy tắc sở hữu (Ownership), hai quy tắc tham chiếu mượn (Borrowing) và cơ chế Borrow Checker triệt tiêu lỗi bộ nhớ.",
            "https://www.youtube.com/watch?v=E3zDspItq-w",
            [
                "Nắm vững 3 nguyên tắc vàng về Quyền sở hữu (Ownership Rules) trong Rust.",
                "Phân biệt giữa quyền sở hữu di chuyển (Move Semantics) và sao chép (Copy Trait).",
                "Làm chủ cơ chế Mượn (Borrowing) với tham chiếu bất biến (`&T`) và tham chiếu khả biến (`&mut T`)."
            ],
            [
                (
                    "Thực Trạng Lỗ Hổng An Toàn Bộ Nhớ Trong Lịch Sử",
                    "Theo các báo cáo an ninh chính thức từ Microsoft và Google Chromium, hơn **70% toàn bộ các lỗ hổng bảo mật nghiêm trọng (CVE)** được phát hiện mỗi năm đều bắt nguồn từ các lỗi an toàn bộ nhớ trong C/C++: Tràn bộ đệm (Buffer Overflow), Đọc dữ liệu sau khi giải phóng (Use-After-Free), Giải phóng bộ nhớ hai lần (Double Free), và Con trỏ rỗng (Null Pointer Dereference). Các tin tặc khai thác các lỗi này để ghi đè con trỏ lệnh và chiếm quyền điều khiển hệ thống. Rust ra đời với sứ mệnh lịch sử: Triệt tiêu 100% các lỗ hổng bộ nhớ này ngay từ khâu biên dịch mà không phải trả giá bằng hiệu năng runtime!"
                ),
                (
                    "Ba Quy Tắc Sở Hữu Bất Biến (The 3 Rules of Ownership)",
                    "Toàn bộ mô hình an toàn của Rust xoay quanh 3 quy tắc đơn giản nhưng cực kỳ chặt chẽ: 1. Mỗi giá trị trong Rust đều có một biến làm 'chủ sở hữu' (Owner) của nó. 2. Tại một thời điểm, chỉ có DUY NHẤT một chủ sở hữu cho một giá trị. 3. Khi chủ sở hữu ra khỏi phạm vi hoạt động (Scope), giá trị đó sẽ tự động bị giải phóng (Drop) khỏi bộ nhớ ngay lập tức. Không có hiện tượng rò rỉ bộ nhớ (Memory Leak), không có hiện tượng giải phóng hai lần (Double Free)!"
                ),
                (
                    "Quy Tắc Mượn Dữ Liệu (Borrowing) & Tránh Race Condition",
                    "Nếu chỉ có một chủ sở hữu, làm sao chúng ta truyền dữ liệu vào các hàm xử lý mà không làm mất dữ liệu gốc? Đó là lúc cơ chế Mượn (Borrowing) thông qua Con trỏ tham chiếu xuất hiện: Tham chiếu bất biến (`&T`): Cho phép đọc dữ liệu nhưng không được sửa. Bạn có thể có VÔ SỐ tham chiếu bất biến tại cùng một thời điểm. Tham chiếu khả biến (`&mut T`): Cho phép sửa đổi dữ liệu. Nhưng tại một thời điểm, bạn chỉ được phép có DUY NHẤT MỘT tham chiếu khả biến và KHÔNG ĐƯỢC có thêm bất kỳ tham chiếu đọc nào khác. Quy tắc này triệt tiêu hoàn toàn lỗi tương tranh dữ liệu (Data Race) trong lập trình đa luồng!"
                )
            ],
            "Kịch bản đối đầu: Lỗi Use-After-Free Biến Mất Trong Rust: Trong C, nếu bạn giải phóng một con trỏ nhưng vẫn tiếp tục đọc nó, mã độc có thể ghi đè vùng nhớ đó để leo thang đặc quyền. Trong Rust, nếu bạn cố tình sử dụng lại một biến đã bị chuyển quyền sở hữu (Moved), trình biên dịch sẽ từ chối dịch mã nguồn ngay lập tức (Compile Error), ngăn chặn lỗ hổng xuất hiện trong sản phẩm thực tế.",
            "Thực hành kiểm nghiệm cơ chế Move và Borrowing thông qua mã nguồn Rust:",
            ("rust", """fn main() {
    // 1. Khởi tạo một chuỗi dữ liệu trong bộ nhớ Heap
    let s1 = String::from("CYBER_TARGET_IP: 192.168.1.1");

    // 2. Di chuyển quyền sở hữu (Move) từ s1 sang s2
    let s2 = s1;
    // println!("{}", s1); // DÒNG NÀY SẼ GÂY LỖI BIÊN DỊCH VÌ S1 ĐÃ MẤT QUYỀN SỞ HỮU!

    println!("[+] s2 đang sở hữu dữ liệu: {}", s2);

    // 3. Mượn dữ liệu an toàn bằng tham chiếu bất biến
    let len = calculate_length(&s2);
    println!("[+] Độ dài chuỗi mượn từ s2: {} bytes", len);
}

fn calculate_length(s: &String) -> usize {
    s.len() // s chỉ là con trỏ mượn để đọc, quyền sở hữu vẫn thuộc về s2
}"""),
            ["Không bao giờ cố gắng 'đánh lừa' Borrow Checker bằng từ khóa unsafe nếu không thực sự hiểu rõ cấu trúc con trỏ cấp thấp.", "Tận dụng tính năng Clone một cách có chọn lọc khi thực sự cần sao chép dữ liệu độc lập."],
            ["Hơn 70% lỗ hổng an ninh nghiêm trọng trong C/C++ bắt nguồn từ lỗi quản lý bộ nhớ.", "Ba quy tắc Ownership và hai quy tắc Borrowing của Rust loại bỏ triệt để các lỗi bộ nhớ.", "Borrow Checker kiểm tra an toàn bộ nhớ tại thời điểm biên dịch với chi phí runtime bằng không."],
            [
                {"question": "Trong ngôn ngữ Rust, tại một thời điểm có thể có tối đa bao nhiêu chủ sở hữu (Owner) cho một giá trị?", "type": "MULTIPLE_CHOICE", "options": ["Vô số", "Chỉ duy nhất một", "Tối đa hai", "Tùy thuộc vào cấu hình"], "correct_index": 1, "explanation": "Quy tắc 2 của Ownership: Chỉ có duy nhất một chủ sở hữu tại một thời điểm."},
                {"question": "Cơ chế Borrowing của Rust cho phép có đồng thời một tham chiếu ghi (&mut T) và nhiều tham chiếu đọc (&T)?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Khi có một tham chiếu khả biến, không được phép có bất kỳ tham chiếu đọc nào khác để tránh Data Race."},
                {"question": "Bộ phận nào trong trình biên dịch Rust chịu trách nhiệm kiểm tra quy tắc mượn dữ liệu trước khi sinh mã nhị phân?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Borrow Checker", "borrow checker"]}], "explanation": "Borrow Checker."}
            ]
        ),
        (
            4,
            "Bài 4.4: Xây Dựng Công Cụ Quét Cổng TCP Siêu Tốc (Port Scanner) Đầu Tiên Bằng Rust",
            "Thực hành xây dựng công cụ trinh sát mạng đầu tiên: Lập trình Socket mạng với `std::net::TcpStream`, kỹ thuật quét đồng bộ tuần tự và phát hiện cổng mở.",
            "https://www.youtube.com/watch?v=LdQsA8XrP4s",
            [
                "Nắm vững nguyên lý quét cổng TCP Connect Scan (bắt tay 3 bước SYN-SYN/ACK-ACK).",
                "Thực hành sử dụng thư viện mạng chuẩn `std::net::TcpStream` trong Rust.",
                "Xử lý phân tích chuỗi địa chỉ IP và dải cổng mạng bằng kỹ thuật vòng lặp iterator."
            ],
            [
                (
                    "Nguyên Lý Kỹ Thuật Của TCP Connect Scan",
                    "Trong giai đoạn trinh sát (Reconnaissance) của một cuộc kiểm thử xâm nhập, quét cổng (Port Scanning) là bước bắt buộc để xác định các dịch vụ đang lắng nghe trên máy chủ mục tiêu (như Web 80/443, SSH 22, RDP 3389). Phương pháp cơ bản và đáng tin cậy nhất là **TCP Connect Scan**: Máy quét thực hiện đầy đủ quy trình bắt tay 3 bước (Three-way Handshake) của giao thức TCP: 1. Máy quét gửi gói tin `SYN` tới cổng mục tiêu. 2. Nếu cổng MỞ: Máy chủ phản hồi gói tin `SYN/ACK`. Máy quét gửi lại gói tin `ACK` để hoàn tất kết nối, sau đó lập tức gửi `RST` để đóng kết nối. 3. Nếu cổng ĐÓNG: Máy chủ phản hồi gói tin `RST` hoặc không phản hồi (Drop do tường lửa)."
                ),
                (
                    "Lập Trình Mạng Chuẩn Với Thư Viện `std::net`",
                    "Ngôn ngữ Rust cung cấp thư viện mạng chuẩn `std::net` cực kỳ mạnh mẽ và an toàn. Hàm `TcpStream::connect_timeout` cho phép thiết lập kết nối tới một `SocketAddr` với một khoảng thời gian chờ (Timeout) xác định. Nếu kết nối thành công, cổng đó được ghi nhận là MỞ. Nếu trả về lỗi (Timeout hoặc Connection Refused), cổng đó được coi là ĐÓNG."
                ),
                (
                    "Hạn Chế Của Quét Tuần Tự Đồng Bộ",
                    "Một công cụ quét cổng tuần tự đơn luồng (Single-threaded) sẽ thử từng cổng một: Cổng 1 -> đợi timeout -> Cổng 2 -> đợi timeout... Nếu mỗi cổng timeout 1 giây, việc quét 1,000 cổng sẽ mất tới 1,000 giây (hơn 16 phút)! Đây là động lực để chúng ta nâng cấp lên các kiến trúc đa luồng (Multi-threading) và bất đồng bộ (Async) trong các bài học tiếp theo."
                )
            ],
            "Kịch bản thực chiến: Trinh Sát Cổng Dịch Vụ Quản Trị Từ Xa: Chuyên gia pentest quét nhanh các cổng phổ biến (Top 10 Ports) của một dải máy chủ để tìm các cổng dịch vụ quản trị nguy hiểm như Telnet (23), VNC (5900) hoặc Redis (6379) không đặt mật khẩu.",
            "Thực hành viết chương trình quét cổng TCP cơ bản bằng Rust sử dụng std::net::TcpStream:",
            ("rust", """use std::net::{SocketAddr, TcpStream};
use std::time::Duration;

fn main() {
    let target_ip = "127.0.0.1";
    let ports_to_scan = vec![21, 22, 80, 443, 3306, 3389, 8080];
    let timeout = Duration::from_millis(500);

    println!("[*] Bắt đầu quét mục tiêu: {}", target_ip);

    for port in ports_to_scan {
        let addr: SocketAddr = format!("{}:{}", target_ip, port).parse().unwrap();
        match TcpStream::connect_timeout(&addr, timeout) {
            Ok(_) => println!("[+] CỔNG MỞ: {:<5} -> Dịch vụ đang hoạt động!", port),
            Err(_) => (), // Bỏ qua nếu cổng đóng hoặc timeout
        }
    }
    println!("[*] Quá trình quét hoàn tất.");
}"""),
            ["Luôn thiết lập tham số timeout hợp lý; nếu timeout quá ngắn có thể bỏ sót các cổng mở trên đường truyền chậm.", "Chỉ quét các hệ thống mà bạn được cấp phép bằng văn bản chính thức."],
            ["TCP Connect Scan thực hiện bắt tay 3 bước đầy đủ để xác định trạng thái cổng mạng.", "Rust cung cấp TcpStream::connect_timeout an toàn trong thư viện chuẩn std::net.", "Quét tuần tự đơn luồng quá chậm đối với các dải cổng lớn."],
            [
                {"question": "Khi một cổng TCP đang mở, máy chủ mục tiêu sẽ phản hồi gói tin nào sau khi nhận được gói SYN?", "type": "MULTIPLE_CHOICE", "options": ["RST", "FIN", "SYN/ACK", "ACK"], "correct_index": 2, "explanation": "Máy chủ phản hồi gói SYN/ACK khi cổng mở."},
                {"question": "Hàm nào trong thư viện std::net của Rust cho phép thiết lập kết nối TCP với thời gian chờ xác định?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["connect_timeout", "TcpStream::connect_timeout"]}], "explanation": "TcpStream::connect_timeout."},
                {"question": "Quét cổng đơn luồng tuần tự là phương pháp tối ưu nhất để quét toàn bộ 65,535 cổng mạng?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Quét tuần tự rất chậm, cần áp dụng đa luồng hoặc bất đồng bộ."}
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
                lesson_num=f"4.{pos}",
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

    # Lessons 4.5 to 4.12
    configs_part2 = [
        (
            5,
            "Bài 4.5: Xử Lý Lỗi Đa Tầng & Tối Ưu Hóa Hiệu Năng Quét Mạng Với anyhow & thiserror",
            "Nâng cao độ tin cậy của vũ khí mạng bằng cơ chế xử lý lỗi idiomatic của Rust: Khử bỏ panic bằng `Result<T, E>`, phân loại lỗi với `thiserror` và lan truyền lỗi bằng toán tử `?`.",
            "https://www.youtube.com/watch?v=LdQsA8XrP4s",
            [
                "Hiểu rõ triết lý xử lý lỗi tường minh trong Rust thông qua kiểu `Result` và `Option`.",
                "Phân biệt phạm vi sử dụng giữa hai thư viện chuẩn công nghiệp: `thiserror` (cho thư viện) và `anyhow` (cho ứng dụng CLI).",
                "Sử dụng thành thạo toán tử dấu hỏi `?` để lan truyền lỗi sạch sẽ mà không làm sập tiến trình."
            ],
            [
                (
                    "Triết Lý Xử Lý Lỗi Không Sập Chương Trình (No Panic Policy)",
                    "Trong các hoạt động tấn công mạng bí mật, điều cấm kỵ số 1 của một công cụ là bị sập đột ngột (Crash / Panic). Khi một chương trình C bị segmentation fault hoặc Python bị unhandled exception, hệ điều hành sẽ ghi lại vết sập trong nhật ký hệ thống (Crash Dumps, Windows Event Log), lập tức báo động cho đội ngũ SOC phát hiện cuộc tấn công. Rust tiếp cận xử lý lỗi theo cách hoàn toàn khác: Rust không có khái niệm ngoại lệ (Exceptions). Mọi hành động có khả năng thất bại (như mở file, kết nối mạng) bắt buộc phải trả về một kiểu dữ liệu **`Result<T, E>`** (chứa giá trị thành công `Ok(T)` hoặc lỗi `Err(E)`). Lập trình viên bắt buộc phải xử lý tường minh cả hai trường hợp trước khi mã nguồn có thể biên dịch thành công."
                ),
                (
                    "Bộ Đôi Hoàn Hảo: thiserror & anyhow",
                    "1. Crate `thiserror`: Được sử dụng khi bạn viết các module lõi hoặc thư viện quét mạng. `thiserror` cung cấp các macro dẫn xuất (derive macros) giúp bạn dễ dàng định nghĩa các enum lỗi tùy biến có phân cấp rõ ràng (ví dụ: `NetworkTimeout`, `PermissionDenied`, `InvalidAddress`) với chi phí bộ nhớ bằng không. 2. Crate `anyhow`: Được sử dụng ở tầng ứng dụng CLI thực thi. `anyhow::Result<T>` đóng vai trò như một bao bì tổng quát có thể bọc bất kỳ loại lỗi nào, tự động đính kèm ngữ cảnh (Context) giải thích nguyên nhân lỗi xảy ra ở bước nào mà không cần viết boilerplate code dài dòng."
                ),
                (
                    "Sức Mạnh Của Toán Tử Lan Truyền Lỗi `?`",
                    "Toán tử `?` trong Rust là một đột phá về cú pháp: Nếu biểu thức trả về `Ok(val)`, toán tử `?` sẽ bóc tách giá trị `val` để tiếp tục chạy; Nếu trả về `Err(err)`, nó sẽ tự động thoát khỏi hàm hiện tại và trả lỗi đó về cho hàm cha xử lý. Mã nguồn của bạn sẽ trở nên ngắn gọn, thanh lịch hệt như ngôn ngữ động nhưng vẫn an toàn 100%."
                )
            ],
            "Kịch bản thực tế: Xử Lý Lỗi Kết Nối Mạng Ổn Định: Khi quét hàng chục nghìn cổng mạng, hàng nghìn lỗi `ConnectionRefused` và `TimedOut` sẽ phát sinh liên tục. Việc áp dụng cơ chế xử lý lỗi chính xác giúp công cụ ghi nhận cổng đóng một cách nhẹ nhàng và tiếp tục quét các cổng khác mà không bị tràn bộ nhớ hay gián đoạn luồng thực thi.",
            "Thực hành viết module xử lý lỗi mạng tùy biến bằng thiserror và anyhow:",
            ("rust", """use thiserror::Error;
use anyhow::{Context, Result};
use std::net::TcpStream;
use std::time::Duration;

#[derive(Error, Debug)]
pub enum ScanError {
    #[error("Địa chỉ IP hoặc cổng không hợp lệ: {0}")]
    InvalidTarget(String),
    #[error("Kết nối mạng bị quá thời gian chờ (Timeout)")]
    NetworkTimeout,
}

fn scan_single_port(target: &str, port: u16) -> Result<bool> {
    let addr = format!("{}:{}", target, port);
    let stream = TcpStream::connect_timeout(&addr.parse().context("Lỗi parse địa chỉ")?, Duration::from_millis(300));
    Ok(stream.is_ok())
}

fn main() -> Result<()> {
    let is_open = scan_single_port("127.0.0.1", 80).context("Thất bại khi quét cổng 80")?;
    println!("Trạng thái cổng 80: {}", if is_open { "MỞ" } else { "ĐÓNG" });
    Ok(())
}"""),
            ["Tuyệt đối không sử dụng hàm unwrap() hoặc expect() trong mã nguồn công cụ tấn công thực chiến vì chúng sẽ gây panic khi gặp lỗi.", "Luôn sử dụng .context() của anyhow để gắn kèm ngữ cảnh gỡ lỗi có ý nghĩa."],
            ["Rust không có cơ chế Exception; mọi lỗi đều được mô hình hóa qua enum Result<T, E>.", "Toán tử ? lan truyền lỗi thanh lịch và loại bỏ mã lặp thừa.", "thiserror tạo lỗi tùy biến cho module, anyhow xử lý lỗi linh hoạt cho ứng dụng."],
            [
                {"question": "Kiểu dữ liệu cơ bản nào trong Rust được sử dụng để đại diện cho một thao tác có thể thành công hoặc thất bại?", "type": "MULTIPLE_CHOICE", "options": ["Option<T>", "Result<T, E>", "Either<L, R>", "Tuple"], "correct_index": 1, "explanation": "Result<T, E> chứa Ok(T) hoặc Err(E)."},
                {"question": "Toán tử nào trong Rust được dùng để bóc tách giá trị thành công hoặc tự động trả lỗi về hàm gọi cha?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["?", "Toán tử ?", "dấu ?"]}], "explanation": "Toán tử ?."},
                {"question": "Sử dụng hàm unwrap() trên một giá trị Err sẽ khiến chương trình Rust bị dừng đột ngột (panic)?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. unwrap() trên Err sẽ lập tức kích hoạt panic."}
            ]
        ),
        (
            6,
            "Bài 4.6: Lập Trình Đa Luồng Không Sợ Hãi (Fearless Concurrency): Channels, Mutex & Arc",
            "Chinh phục kỹ thuật lập trình song song tốc độ cao trong Rust: Kênh truyền thông điệp (MPSC Channels), con trỏ chia sẻ an toàn `Arc<T>` và khóa loại trừ tương hỗ `Mutex<T>`.",
            "https://www.youtube.com/watch?v=11raTwzQVn4",
            [
                "Hiểu rõ khẩu hiệu 'Fearless Concurrency' (Đa luồng không sợ hãi) và cơ chế Send/Sync trait của Rust.",
                "Thực hành tạo và điều phối luồng công việc bằng `std::thread::spawn`.",
                "Sử dụng mô hình chia sẻ bộ nhớ an toàn qua `Arc<Mutex<T>>` và mô hình truyền thông điệp mpsc channel."
            ],
            [
                (
                    "Tại Sao Lập Trình Đa Luồng Trong C/C++ Lại Cực Kỳ Nguy Hiểm?",
                    "Trong các ngôn ngữ truyền thống, lập trình đa luồng (Multi-threading) là vùng đất của những cơn ác mộng: Hai luồng cùng đọc và ghi vào một biến bộ nhớ chung mà không có khóa đồng bộ hóa sẽ tạo ra lỗi **Data Race (Tương tranh dữ liệu)**. Hậu quả là dữ liệu bị sai lệch ngẫu nhiên, chương trình bị sập bất thình lình và các lỗi này gần như không thể tái hiện lại trong môi trường thử nghiệm (Heisenbugs). Rust xóa bỏ hoàn toàn nỗi sợ này nhờ cơ chế **Fearless Concurrency**: Nếu mã nguồn đa luồng của bạn có nguy cơ xảy ra Data Race, trình biên dịch Rust sẽ từ chối biên dịch ngay lập tức!"
                ),
                (
                    "Mô Hình 1: Truyền Thông Điệp Qua Kênh (Message Passing / Channels)",
                    "Triết lý nổi tiếng của Rust (kế thừa từ Erlang và Go) là: *'Đừng giao tiếp bằng cách chia sẻ bộ nhớ; hãy chia sẻ bộ nhớ bằng cách giao tiếp.'* Rust cung cấp thư viện `std::sync::mpsc` (Multi-Producer, Single-Consumer): Nhiều luồng thợ (Worker Threads) thực hiện quét cổng độc lập, sau đó gửi kết quả (ví dụ: 'Cổng 80 MỞ') qua một kênh truyền thông điệp (Sender) về cho một luồng chính duy nhất (Receiver) thu thập và in kết quả ra màn hình. Không cần dùng khóa Mutex, không có nguy cơ xung đột bộ nhớ!"
                ),
                (
                    "Mô Hình 2: Chia Sẻ Bộ Nhớ An Toàn Qua Arc & Mutex",
                    "Khi bắt buộc phải chia sẻ một cấu trúc dữ liệu chung giữa nhiều luồng (ví dụ: danh sách các cổng đã quét xong), Rust yêu cầu kết hợp hai thành phần: 1. `Arc<T>` (Atomic Reference Counting): Con trỏ đếm tham chiếu an toàn luồng, cho phép nhiều luồng cùng sở hữu một vùng nhớ chung. 2. `Mutex<T>` (Mutual Exclusion): Ổ khóa loại trừ tương hỗ. Một luồng muốn đọc hoặc sửa dữ liệu bắt buộc phải gọi `.lock()`. Trình biên dịch Rust đảm bảo rằng bạn KHÔNG THỂ truy cập dữ liệu bên trong nếu chưa nắm giữ ổ khóa!"
                )
            ],
            "Kịch bản thực chiến: Tăng Tốc Độ Quét Cổng Lên Gấp 50 Lần: Bằng cách chia danh sách 1,000 cổng cho 50 luồng chạy song song trên CPU đa nhân, thời gian quét giảm từ 100 giây xuống chỉ còn 2 giây mà không xảy ra bất kỳ lỗi xung đột dữ liệu nào.",
            "Thực hành viết chương trình quét cổng đa luồng sử dụng mpsc channel trong Rust:",
            ("rust", """use std::net::{SocketAddr, TcpStream};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel();
    let target = "127.0.0.1";

    println!("[*] Khởi tạo 10 luồng quét cổng song song...");
    for port in 20..30 {
        let tx = tx.clone();
        thread::spawn(move || {
            let addr: SocketAddr = format!("{}:{}", target, port).parse().unwrap();
            if TcpStream::connect_timeout(&addr, Duration::from_millis(200)).is_ok() {
                tx.send(port).unwrap();
            }
        });
    }
    drop(tx); // Đóng sender ban đầu để receiver biết khi nào kết thúc

    for open_port in rx {
        println!("[+] PHÁT HIỆN CỔNG MỞ (ĐA LUỒNG): {}", open_port);
    }
}"""),
            ["Luôn nhớ drop bản sao sender gốc trong luồng chính để vòng lặp đọc rx không bị treo vô hạn.", "Không giữ khóa Mutex quá lâu qua các tác vụ I/O nặng vì sẽ làm nghẽn toàn bộ các luồng khác."],
            ["Rust triệt tiêu lỗi tương tranh dữ liệu (Data Race) tại thời điểm biên dịch.", "Mô hình mpsc channel truyền dữ liệu an toàn giữa các luồng không cần khóa.", "Arc<Mutex<T>> bảo vệ vùng nhớ dùng chung giữa nhiều luồng thực thi."],
            [
                {"question": "Cụm từ 'mpsc' trong thư viện kênh truyền thông điệp của Rust là viết tắt của gì?", "type": "MULTIPLE_CHOICE", "options": ["Multiple-Producer, Single-Consumer", "Multi-Process, Single-Core", "Main-Program, Sub-Channel", "Memory-Protected, Safe-Call"], "correct_index": 0, "explanation": "Multiple-Producer, Single-Consumer (Nhiều nguồn gửi, Một nguồn nhận)."},
                {"question": "Con trỏ nào trong Rust được dùng để đếm tham chiếu an toàn giữa nhiều luồng thực thi?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Arc", "arc", "Arc<T>"]}], "explanation": "Atomic Reference Counted (Arc)."},
                {"question": "Trong Rust, bạn có thể truy cập dữ liệu bên trong Mutex mà không cần gọi hàm .lock()?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Dữ liệu được bọc bên trong Mutex và bắt buộc phải lock thành công mới lấy được con trỏ dữ liệu."}
            ]
        ),
        (
            7,
            "Bài 4.7: Tăng Tốc Tối Đa Với Lập Trình Bất Đồng Bộ Async Rust & Tokio Runtime",
            "Đưa tốc độ quét mạng lên cảnh giới thượng thừa: Cơ chế Non-blocking I/O, mô hình Green Threads của Tokio Runtime, Async/Await và Stream xử lý hàng nghìn kết nối.",
            "https://www.youtube.com/watch?v=LdQsA8XrP4s",
            [
                "Nắm vững sự khác biệt cốt lõi giữa Đa luồng hệ điều hành (OS Threads) và Tác vụ bất đồng bộ (Async Tasks).",
                "Làm chủ hệ sinh thái thời gian thực Tokio Runtime và cú pháp `async/await`.",
                "Xây dựng công cụ quét cổng bất đồng bộ có khả năng xử lý đồng thời 10,000 kết nối mỗi giây."
            ],
            [
                (
                    "Giới Hạn Của OS Threads & Sự Trỗi Dậy Của Async I/O",
                    "Mặc dù đa luồng (Multi-threading) rất nhanh, mỗi luồng hệ điều hành (OS Thread) đều tiêu tốn một vùng nhớ ngăn xếp (Stack) cố định khoảng 2MB đến 8MB. Nếu bạn cố tình tạo ra 10,000 luồng để quét 10,000 cổng cùng lúc, hệ thống sẽ cạn kiệt bộ nhớ RAM ngay lập tức và CPU sẽ bị quá tải do phải liên tục chuyển đổi ngữ cảnh (Context Switching). Giải pháp tối thượng cho các tác vụ bị nghẽn mạng I/O (Network I/O Bound) là **Lập Trình Bất Đồng Bộ (Asynchronous Programming)**: Sử dụng kỹ thuật Non-blocking I/O (epoll trên Linux, kqueue trên macOS, IOCP trên Windows), một luồng duy nhất của CPU có thể quản lý và điều phối hàng trăm nghìn kết nối mạng đang chờ phản hồi cùng một lúc!"
                ),
                (
                    "Kiến Trúc Tokio Runtime: Trái Tim Của Async Rust",
                    "Rust không tích hợp sẵn bộ điều phối bất đồng bộ trong thư viện chuẩn mà chỉ cung cấp cú pháp nền tảng `Future` và `async/await`. Crate **Tokio** là runtime bất đồng bộ tiêu chuẩn công nghiệp mạnh mẽ nhất thế giới hiện nay. Tokio cung cấp: 1. Bộ lập lịch công việc thích ứng (Work-stealing Thread Pool): Tự động phân bổ các tác vụ nhẹ (Tasks) trên các nhân CPU để tối đa hóa hiệu năng. 2. Các thư viện mạng bất đồng bộ: `tokio::net::TcpStream` thay thế hoàn hảo cho `std::net::TcpStream` đồng bộ. Khi một kết nối đang chờ phản hồi từ máy chủ, luồng CPU sẽ lập tức chuyển sang xử lý kết nối khác mà không bao giờ bị nghẽn (Zero Blocking)."
                ),
                (
                    "Cơ Chế Bắn Tác Vụ Đồng Thời Với tokio::spawn & JoinSet",
                    "Trong Tokio, chúng ta sử dụng `tokio::spawn` để tạo ra một 'Green Thread' siêu nhẹ (chỉ tốn vài trăm byte bộ nhớ). Bạn có thể dễ dàng bắn ra 65,535 tác vụ quét cổng chỉ trong vài mili-giây và sử dụng `tokio::sync::Semaphore` để khống chế số lượng kết nối đồng thời nhằm tránh làm sập bảng định tuyến của router."
                )
            ],
            "Kịch bản thực chiến: Bí Quyết Đạt Tốc Độ 65,535 Cổng Trong 3 Giây: Công cụ mã nguồn mở nổi tiếng RustScan đạt được danh hiệu máy quét cổng nhanh nhất thế giới chính nhờ việc kết hợp Tokio Async với kỹ thuật Adaptive Timing: Bắn hàng chục nghìn gói tin bất đồng bộ thăm dò cực nhanh, sau đó bàn giao danh sách cổng mở cho Nmap thực hiện phân tích dịch vụ chi tiết.",
            "Thực hành viết chương trình quét cổng bất đồng bộ siêu tốc bằng Tokio:",
            ("rust", """use tokio::net::TcpStream;
use tokio::time::{timeout, Duration};

async fn scan_port(ip: &'static str, port: u16) -> Option<u16> {
    let addr = format!("{}:{}", ip, port);
    match timeout(Duration::from_millis(200), TcpStream::connect(&addr)).await {
        Ok(Ok(_)) => Some(port),
        _ => None,
    }
}

#[tokio::main]
async fn main() {
    let target = "127.0.0.1";
    println!("[*] Khởi chạy công cụ quét Async Tokio trên mục tiêu: {}", target);

    let mut tasks = vec![];
    for port in 1..=1000 {
        tasks.push(tokio::spawn(scan_port(target, port)));
    }

    for task in tasks {
        if let Ok(Some(open_port)) = task.await {
            println!("[+] CỔNG MỞ PHÁT HIỆN QUA TOKIO: {}", open_port);
        }
    }
}"""),
            ["Luôn khống chế số lượng file descriptor mở bằng Semaphore để tránh lỗi 'Too many open files' từ hệ điều hành.", "Không bao giờ chạy các tác vụ tính toán CPU nặng đồng bộ bên trong một luồng async của Tokio."],
            ["Async Rust sử dụng Non-blocking I/O để quản lý hàng nghìn kết nối mạng trên ít luồng CPU.", "Tokio Runtime là hệ sinh thái điều phối tác vụ bất đồng bộ mạnh mẽ nhất của Rust.", "Tokio::spawn tạo ra các tác vụ siêu nhẹ chỉ tốn vài trăm byte bộ nhớ."],
            [
                {"question": "Thư viện Runtime bất đồng bộ phổ biến và mạnh mẽ nhất trong hệ sinh thái Rust là gì?", "type": "MULTIPLE_CHOICE", "options": ["Tokio", "Actix", "Rayon", "AsyncStd"], "correct_index": 0, "explanation": "Tokio Runtime."},
                {"question": "Cơ chế lập trình bất đồng bộ tối ưu hóa tốt nhất cho loại tác vụ nào sau đây?", "type": "MULTIPLE_CHOICE", "options": ["Nén video 4K (CPU Bound)", "Quét hàng nghìn kết nối mạng đang chờ phản hồi (Network I/O Bound)", "Đào coin tiền mã hóa", "Giải mã băm mật khẩu"], "correct_index": 1, "explanation": "Tác vụ nghẽn I/O mạng (Network I/O Bound)."},
                {"question": "Một tác vụ bất đồng bộ (tokio task) tiêu tốn bộ nhớ RAM ngang bằng với một luồng hệ điều hành (OS thread)?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Task bất đồng bộ chỉ tốn vài trăm byte, nhẹ hơn hàng nghìn lần so với OS thread (2MB)."}
            ]
        ),
        (
            8,
            "Bài 4.8: Kiến Trúc Module Hóa Công Cụ Quét Với Trait Objects & Dynamic Dispatch",
            "Thiết kế kiến trúc mở rộng cho vũ khí mạng: Xây dựng hệ thống Plugin linh hoạt bằng Rust Trait, kỹ thuật Dispatch tĩnh vs Dispatch động (`dyn Trait`).",
            "https://www.youtube.com/watch?v=E3zDspItq-w",
            [
                "Nắm vững khái niệm Trait trong Rust (tương đương Interface trong các ngôn ngữ khác).",
                "Phân biệt giữa Phân phối tĩnh (Static Dispatch / Monomorphization) và Phân phối động (Dynamic Dispatch / `Box<dyn Trait>`).",
                "Xây dựng kiến trúc module hóa cho phép gắn thêm các plugin dò quét dịch vụ mới mà không cần sửa mã nguồn lõi."
            ],
            [
                (
                    "Tầm Quan Trọng Của Thiết Kế Kiến Trúc Module",
                    "Một công cụ an ninh mạng thực chiến không chỉ đơn thuần dừng lại ở việc kiểm tra cổng mở/đóng. Sau khi phát hiện cổng 80 mở, công cụ cần tự động kích hoạt module quét Web; sau khi phát hiện cổng 22 mở, nó cần gọi module kiểm tra phiên bản SSH; và nếu là cổng 445, nó cần kích hoạt module kiểm tra lỗ hổng SMB EternalBlue. Nếu lập trình viên sử dụng hàng chục câu lệnh `if/else` chằng chịt, mã nguồn sẽ nhanh chóng biến thành một bãi rác không thể bảo trì. Giải pháp chuyên nghiệp là xây dựng một **Hệ Thống Plugin Module Hóa dựa trên Trait**."
                ),
                (
                    "Định Nghĩa Khung Hành Vi Với Rust Trait",
                    "Trong Rust, Trait định nghĩa một tập hợp các phương thức mà một kiểu dữ liệu phải thực thi. Chúng ta có thể định nghĩa một trait `ScannerModule`: Trait này yêu cầu mọi module con (như `SshScanner`, `HttpScanner`, `FtpScanner`) phải có phương thức `name() -> &str` và phương thức `scan(&self, target: &str, port: u16) -> ScanResult`. Bất kỳ lập trình viên nào trong đội ngũ Red Team cũng có thể viết một module mới chỉ cần hiện thực hóa trait này."
                ),
                (
                    "Static Dispatch vs Dynamic Dispatch (`Box<dyn Trait>`)",
                    "Rust hỗ trợ hai phương thức đa hình: 1. Static Dispatch (Đa hình tại thời điểm biên dịch): Sử dụng Generics `<T: ScannerModule>`. Trình biên dịch tạo ra các bản sao mã máy riêng cho từng kiểu (Monomorphization), tốc độ tối đa nhưng không thể lưu trữ các kiểu khác nhau trong cùng một mảng `Vec`. 2. Dynamic Dispatch (Đa hình tại thời điểm chạy): Sử dụng con trỏ Trait Object **`Box<dyn ScannerModule>`**. Cách này cho phép lưu trữ hàng chục module quét khác nhau vào cùng một mảng danh sách `Vec<Box<dyn ScannerModule>>` và gọi phương thức thực thi linh hoạt thông qua bảng phương thức ảo (vtable)."
                )
            ],
            "Kịch bản mở rộng: Tích Hợp Module Tự Động Nhận Dạng Dịch Vụ: Khi lõi quét phát hiện cổng 21 mở, chương trình tự động duyệt qua danh sách các plugin đã đăng ký, tìm thấy `FtpModule`, kích hoạt việc bắt banner chào (Banner Grabbing) và kiểm tra tài khoản Anonymous login hoàn toàn tự động.",
            "Thực hành thiết kế hệ thống module quét mở rộng bằng Trait trong Rust:",
            ("rust", """pub trait ScannerModule {
    fn name(&self) -> &'static str;
    fn can_handle(&self, port: u16) -> bool;
    fn execute(&self, target: &str, port: u16);
}

pub struct HttpModule;
impl ScannerModule for HttpModule {
    fn name(&self) -> &'static str { "HTTP Web Probe" }
    fn can_handle(&self, port: u16) -> bool { port == 80 || port == 443 }
    fn execute(&self, target: &str, port: u16) {
        println!("[{}] Đang gửi HTTP GET request tới {}:{}", self.name(), target, port);
    }
}

fn main() {
    // Lưu trữ các module khác nhau trong cùng một mảng bằng Trait Object
    let modules: Vec<Box<dyn ScannerModule>> = vec![Box::new(HttpModule)];
    for module in &modules {
        if module.can_handle(80) {
            module.execute("192.168.1.1", 80);
        }
    }
}"""),
            ["Ưu tiên sử dụng Static Dispatch khi không cần lưu trữ danh sách đa hình để tận dụng tối ưu hóa tốc độ của compiler.", "Đảm bảo các phương thức trong Trait tuân thủ nguyên tắc Object Safety nếu muốn dùng dyn Trait."],
            ["Trait định nghĩa hợp đồng hành vi chung cho các module an ninh.", "Static Dispatch tối ưu tốc độ, Dynamic Dispatch (dyn Trait) tối ưu sự linh hoạt.", "Kiến trúc Trait Object giúp mở rộng các tính năng quét mới dễ dàng."],
            [
                {"question": "Từ khóa nào trong Rust được dùng để định nghĩa một tập hợp các phương thức hợp đồng chung (tương tự Interface)?", "type": "MULTIPLE_CHOICE", "options": ["Interface", "Trait", "Protocol", "Contract"], "correct_index": 1, "explanation": "Từ khóa trait."},
                {"question": "Cú pháp nào đại diện cho một Trait Object sử dụng cơ chế phân phối động (Dynamic Dispatch)?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["dyn Trait", "dyn", "Box<dyn Trait>"]}], "explanation": "dyn Trait hoặc Box<dyn Trait>."},
                {"question": "Sử dụng Generics và Static Dispatch trong Rust có làm phát sinh chi phí gọi hàm qua bảng ảo (vtable) lúc chạy không?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Static Dispatch sinh mã máy trực tiếp (inlining), không tốn chi phí vtable."}
            ]
        ),
        (
            9,
            "Bài 4.9: Xây Dựng Bộ Phân Tích Tham Số Dòng Lệnh CLI Mạnh Mẽ Với clap & Ghi Log An Ninh",
            "Chuyên nghiệp hóa công cụ kiểm thử: Tích hợp thư viện phân tích cú pháp dòng lệnh `clap` (Command Line Argument Parser), cấu hình cờ tùy chọn và ghi nhật ký an ninh chuẩn `env_logger`.",
            "https://www.youtube.com/watch?v=LdQsA8XrP4s",
            [
                "Làm chủ thư viện phân tích dòng lệnh số 1 trong hệ sinh thái Rust: `clap v4` sử dụng cú pháp Derive macro.",
                "Tự động tạo tài liệu hướng dẫn sử dụng (Help Menu), cờ tùy chọn (Flags) và tham số bắt buộc.",
                "Tích hợp hệ thống ghi nhật ký (Logging) đa cấp độ (Error, Warn, Info, Debug, Trace) bằng `log` và `env_logger`."
            ],
            [
                (
                    "Tầm Quan Trọng Của Giao Diện Dòng Lệnh Chuyên Nghiệp",
                    "Một công cụ an ninh mạng dù thuật toán có mạnh đến đâu nhưng nếu tham số dòng lệnh cẩu thả, khó dùng, thiếu tài liệu hướng dẫn `--help` thì sẽ không thể đưa vào quy trình tự động hóa CI/CD hoặc bàn giao cho đồng đội trong nhóm Red Team sử dụng. Giao diện dòng lệnh chuẩn mực đòi hỏi: Khả năng phân tích linh hoạt các cờ ngắn (`-t`), cờ dài (`--target`), giá trị mặc định, kiểm tra tính hợp lệ của dải cổng, và hiển thị thông báo lỗi rõ ràng khi người dùng nhập sai tham số."
                ),
                (
                    "Sức Mạnh Của Crate Clap v4 Với Derive Macro",
                    "Crate `clap` là tiêu chuẩn vàng của Rust để xây dựng CLI. Với tính năng Derive macro hiện đại, lập trình viên chỉ cần định nghĩa một cấu trúc `struct` Rust thông thường và thêm các attribute trang trí: `#[derive(Parser)]`. Clap sẽ tự động làm toàn bộ các công việc phức tạp: Phân tích cú pháp chuỗi `std::env::args()`, ép kiểu dữ liệu từ chuỗi sang số nguyên `u16` hoặc địa chỉ IP, kiểm tra giới hạn giá trị, và tự động sinh ra một trang hướng dẫn `--help` tuyệt đẹp có màu sắc trực quan!"
                ),
                (
                    "Kiến Trúc Ghi Nhật Ký An Ninh: Crate `log` & `env_logger`",
                    "Trong công cụ an ninh, bạn không nên sử dụng hàm `println!` một cách bừa bãi. Khi công cụ chạy tự động trong nền, việc in rác ra màn hình sẽ làm hỏng kết quả xuất ra dạng JSON hoặc đường ống dẫn (Pipe). Thay vào đó, chúng ta sử dụng hệ thống ghi log tiêu chuẩn với 5 cấp độ: `error!` (lỗi nghiêm trọng), `warn!` (cảnh báo nguy cơ), `info!` (thông tin tiến độ), `debug!` (thông tin chi tiết gỡ lỗi), và `trace!` (từng gói tin mạng). Người dùng có thể điều khiển mức độ hiển thị linh hoạt thông qua biến môi trường `RUST_LOG=debug`."
                )
            ],
            "Kịch bản thực chiến: Tích Hợp Công Cụ Vào Script Bash Tự Động: Nhờ giao diện dòng lệnh chuẩn POSIX của Clap và khả năng ghi log phân tách kênh `stdout` (cho kết quả sạch) và `stderr` (cho nhật ký), công cụ của bạn có thể dễ dàng ghép nối với các công cụ khác như `jq`, `grep`, `awk` trong chuỗi tự động hóa.",
            "Thực hành xây dựng cấu trúc tham số dòng lệnh hoàn chỉnh bằng clap trong Rust:",
            ("rust", """use clap::Parser;
use log::{info, warn};

#[derive(Parser, Debug)]
#[command(author = "BlackHat Rust Team", version = "1.0", about = "Công cụ quét cổng siêu tốc")]
struct CliArgs {
    /// Địa chỉ IP hoặc tên miền mục tiêu
    #[arg(short, long)]
    target: String,

    /// Cổng bắt đầu quét
    #[arg(short, long, default_value_t = 1)]
    start_port: u16,

    /// Cổng kết thúc quét
    #[arg(short, long, default_value_t = 1024)]
    end_port: u16,
}

fn main() {
    env_logger::init();
    let args = CliArgs::parse();

    info!("Bắt đầu quét mục tiêu: {}", args.target);
    println!("[+] Quét dải cổng từ {} đến {}", args.start_port, args.end_port);
}"""),
            ["Luôn cung cấp giá trị mặc định (default values) hợp lý cho các tham số không bắt buộc.", "Không in thông tin nhạy cảm vào nhật ký cấp độ info; chỉ để ở mức độ trace."],
            ["Crate clap sử dụng Derive macro tự động hóa hoàn toàn việc phân tích tham số CLI.", "Hệ thống ghi log phân tầng (error, warn, info, debug) chuyên nghiệp hơn println!.", "Biến môi trường RUST_LOG cho phép điều khiển mức độ hiển thị nhật ký linh hoạt."],
            [
                {"question": "Thư viện nào là tiêu chuẩn vàng trong Rust để phân tích tham số dòng lệnh CLI?", "type": "MULTIPLE_CHOICE", "options": ["Tokio", "Clap", "Serde", "Reqwest"], "correct_index": 1, "explanation": "Crate clap."},
                {"question": "Cấp độ ghi log nào trong crate log cung cấp thông tin chi tiết nhất về từng gói tin và luồng thực thi?", "type": "MULTIPLE_CHOICE", "options": ["error!", "warn!", "info!", "trace!"], "correct_index": 3, "explanation": "Cấp độ trace! chi tiết nhất."},
                {"question": "Sử dụng clap giúp chương trình tự động sinh ra menu hướng dẫn sử dụng (--help) mà không cần viết thủ công?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Clap tự động sinh trang help từ comment docstring."}
            ]
        ),
        (
            10,
            "Bài 4.10: Phát Triển Web Crawler Thu Thập Thông Tin Tình Báo Nguồn Mở (OSINT Spider)",
            "Xây dựng mạng nhện thu thập tình báo mạng (OSINT Spider) bằng Rust: Kỹ thuật phân tích HTML với `scraper`, trích xuất liên kết đệ quy và quản lý hàng đợi URL.",
            "https://www.youtube.com/watch?v=E3zDspItq-w",
            [
                "Nắm vững nguyên lý hoạt động của một công cụ thu thập web (Web Crawler / Spider).",
                "Sử dụng thư viện HTTP client `reqwest` bất đồng bộ để tải nội dung trang web.",
                "Thực hành trích xuất thẻ liên kết HTML, email và subdomain bằng bộ chọn CSS Selector với `scraper`."
            ],
            [
                (
                    "Vai Trò Của Web Crawling Trong Tình Báo Nguồn Mở (OSINT)",
                    "Trong giai đoạn trinh sát thông tin tình báo nguồn mở (OSINT - Open Source Intelligence), một nhiệm vụ quan trọng là vẽ bản đồ toàn bộ tài sản kỹ thuật số của tổ chức mục tiêu: Tìm kiếm các tên miền phụ (Subdomains), các tài liệu nội bộ vô tình bị rò rỉ, danh sách địa chỉ email nhân viên để phục vụ chiến dịch phishing, và các đường dẫn API ẩn. Việc nhấp chuột thủ công trên từng trang web là bất khả thi. Chuyên gia an ninh cần một công cụ thu thập tự động (Web Spider) có khả năng cào dữ liệu thần tốc và lập chỉ mục hàng triệu trang web."
                ),
                (
                    "Tại Sao Rust Là Lựa Chọn Số 1 Để Viết Web Crawler?",
                    "Các công cụ crawler viết bằng Python (như Scrapy hay BeautifulSoup) thường gặp nút thắt cổ chai nghiêm trọng về CPU khi phải phân tích cú pháp (parsing) các tài liệu HTML khổng lồ nặng hàng chục MB. Rust vượt trội nhờ hai yếu tố: 1. Thư viện `reqwest` chạy trên nền tảng Tokio bất đồng bộ có thể gửi hàng nghìn request HTTP/2 và HTTP/3 cùng lúc. 2. Crate `scraper` (dựa trên parser HTML5 `html5ever` của trình duyệt Servo) phân tích cú pháp HTML trực tiếp thành cây DOM với tốc độ mã máy cực nhanh, tiêu tốn bộ nhớ RAM chỉ bằng một phần mười so với Python."
                ),
                (
                    "Thuật Toán Thu Thập Đệ Quy & Quản Lý Tập Hợp Đã Thăm (Visited Set)",
                    "Một Spider hoạt động theo mô hình duyệt đồ thị theo chiều rộng (BFS - Breadth-First Search): 1. Hàng đợi URL cần thăm (Queue): Khởi đầu bằng URL hạt nhân (Seed URL). 2. Tập hợp các URL đã duyệt (Visited Set): Sử dụng cấu trúc băm `HashSet<String>` để lưu trữ các URL đã cào, đảm bảo công cụ không bao giờ bị rơi vào vòng lặp vô tận (Infinite Loop Trap) do các liên kết chéo tạo ra."
                )
            ],
            "Kịch bản thực chiến: Thu Thập Tự Động Địa Chỉ Email & Subdomain Doanh Nghiệp: Spider duyệt qua trang chủ của mục tiêu, tự động bóc tách toàn bộ các thẻ `<a href>` nội bộ, quét biểu thức chính quy (Regex) tìm kiếm các mẫu email `@target.com` và các tên miền con `*.target.com` để bổ sung vào hồ sơ trinh sát mục tiêu.",
            "Thực hành viết module bóc tách liên kết HTML bằng crate scraper trong Rust:",
            ("rust", """use scraper::{Html, Selector};

fn extract_links(html_content: &str) -> Vec<String> {
    let document = Html::parse_document(html_content);
    let selector = Selector::parse("a[href]").unwrap();
    let mut links = Vec::new();

    for element in document.select(&selector) {
        if let Some(href) = element.value().attr("href") {
            if href.starts_with("http") {
                links.push(href.to_string());
            }
        }
    }
    links
}

fn main() {
    let sample_html = r#"<html><body><a href="https://target.com/admin">Admin</a><a href="https://target.com/api">API</a></body></html>"#;
    let found = extract_links(sample_html);
    println!("[+] Tìm thấy {} liên kết mục tiêu: {:?}", found.len(), found);
}"""),
            ["Luôn kiểm tra và tôn trọng tệp robots.txt cũng như giới hạn tần suất request để không làm sập máy chủ mục tiêu.", "Chuẩn hóa URL (URL Normalization) để tránh việc cùng một trang web bị cào nhiều lần."],
            ["OSINT Spider tự động hóa việc thu thập tài sản số, email và tên miền phụ.", "Rust scraper phân tích cây DOM HTML5 với hiệu năng và độ an toàn vượt trội.", "HashSet quản lý danh sách URL đã thăm ngăn chặn bẫy vòng lặp vô tận."],
            [
                {"question": "Cấu trúc dữ liệu nào thường được sử dụng để theo dõi các URL đã thu thập nhằm chống lặp vòng tròn?", "type": "MULTIPLE_CHOICE", "options": ["Vec", "HashSet", "LinkedList", "BinaryHeap"], "correct_index": 1, "explanation": "HashSet cung cấp thời gian tra cứu O(1) để kiểm tra URL trùng lặp."},
                {"question": "Thư viện HTTP client bất đồng bộ tiêu chuẩn phổ biến nhất trong hệ sinh thái Rust là gì?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["reqwest", "Reqwest"]}], "explanation": "Crate reqwest."},
                {"question": "Bộ phân tích HTML5 trong Rust tiêu tốn nhiều bộ nhớ RAM hơn thư viện BeautifulSoup của Python?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Crate scraper trong Rust tiêu tốn ít bộ nhớ và chạy nhanh hơn nhiều so với Python."}
            ]
        ),
        (
            11,
            "Bài 4.11: Thu Thập Dữ Liệu Đa Luồng Với Spider Trait & Atomic Types",
            "Nâng cấp kiến trúc Spider lên cấp độ doanh nghiệp: Áp dụng các biến nguyên tử vô khóa `std::sync::atomic` (AtomicUsize, AtomicBool) để đồng bộ hóa trạng thái cào dữ liệu siêu tốc.",
            "https://www.youtube.com/watch?v=11raTwzQVn4",
            [
                "Nắm vững nguyên lý các phép toán nguyên tử cấp phần cứng (Atomic Operations) không cần khóa Mutex.",
                "Thực hành sử dụng các kiểu dữ liệu Atomic trong Rust: `AtomicUsize`, `AtomicBool` và `Ordering`.",
                "Xây dựng bộ đếm thống kê và cơ chế dừng khẩn cấp (Cancellation Token) an toàn luồng."
            ],
            [
                (
                    "Hạn Chế Của Khóa Mutex Trong Ứng Dụng Tần Suất Cao",
                    "Khi nhiều luồng thợ (Worker Threads) cùng cào dữ liệu và cần cập nhật một biến chung (ví dụ: đếm số trang web đã tải thành công `page_count += 1`), việc sử dụng `Mutex<usize>` sẽ tạo ra một điểm nghẽn hiệu năng nghiêm trọng: Mỗi khi một luồng muốn tăng biến đếm, nó phải yêu cầu hệ điều hành cấp phát khóa độc quyền. Các luồng khác buộc phải tạm dừng (Block / Sleep), làm lãng phí hàng triệu chu kỳ xung nhịp CPU. Để giải quyết triệt để, chúng ta sử dụng **Các Kiểu Dữ Liệu Nguyên Tử (Atomic Types)**."
                ),
                (
                    "Cơ Chế Khóa Cấp Phần Cứng Của Kiểu Atomic",
                    "Các biến nguyên tử (như `AtomicUsize`, `AtomicBool`) tương tác trực tiếp với các lệnh đặc biệt của vi xử lý CPU (như `LOCK XADD` trên tập lệnh x86/x64). Thay vì sử dụng ổ khóa phần mềm của hệ điều hành, CPU đảm bảo rằng việc đọc và tăng giá trị diễn ra trong một chu kỳ xung nhịp duy nhất không thể bị phân cắt (Atomic). Không có luồng nào bị block, tốc độ xử lý nhanh hơn hàng chục lần so với Mutex!"
                ),
                (
                    "Mô Hình Bộ Nhớ (Memory Ordering) Trong Rust",
                    "Khi thao tác với các biến nguyên tử, Rust yêu cầu lập trình viên chỉ định thứ tự sắp xếp bộ nhớ qua enum `Ordering`: 1. `Ordering::Relaxed`: Chỉ đảm bảo tính nguyên tử của phép toán, không ràng buộc thứ tự thực thi của các lệnh xung quanh. Rất phù hợp cho các bộ đếm số lượng trang. 2. `Ordering::SeqCst` (Sequentially Consistent): Chế độ nghiêm ngặt nhất, đảm bảo mọi luồng trên toàn hệ thống đều nhìn thấy các thao tác theo đúng thứ tự thời gian tuần tự. Phù hợp cho cờ báo dừng khẩn cấp (`AtomicBool`)."
                )
            ],
            "Kịch bản thực chiến: Cơ Chế Dừng Khẩn Cấp Bằng Cờ Nguyên Tử: Khi Spider phát hiện máy chủ mục tiêu kích hoạt cơ chế phòng vệ chống cào dữ liệu (HTTP 429 Too Many Requests), luồng phát hiện lập tức gán `is_running.store(false, Ordering::SeqCst)`. Hàng trăm luồng thợ khác ngay lập tức kiểm tra cờ này và dừng cào đồng loạt một cách êm ái mà không làm treo chương trình.",
            "Thực hành sử dụng AtomicUsize để đếm số lượng trang cào thành công không cần Mutex:",
            ("rust", """use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;

fn main() {
    // Khởi tạo bộ đếm nguyên tử chia sẻ an toàn giữa các luồng
    let counter = Arc::new(AtomicUsize::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter_clone = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                // Tăng biến đếm nguyên tử vô khóa
                counter_clone.fetch_add(1, Ordering::Relaxed);
            }
        }));
    }

    for handle in handles { handle.join().unwrap(); }
    println!("[+] Tổng số trang đã xử lý (Atomic Count): {}", counter.load(Ordering::SeqCst));
}"""),
            ["Sử dụng Ordering::Relaxed khi chỉ cần tính toán độc lập; không lạm dụng SeqCst vì có thể làm giảm nhẹ hiệu năng phần cứng.", "Không sử dụng biến thông thường không atomic giữa các luồng."],
            ["Các phép toán nguyên tử Atomic được thực thi trực tiếp tại cấp độ vi xử lý CPU.", "Loại bỏ hoàn toàn chi phí khóa và hiện tượng nghẽn luồng của Mutex.", "Thích hợp cho các bộ đếm thống kê và cờ tín hiệu dừng khẩn cấp."],
            [
                {"question": "Thao tác trên các kiểu dữ liệu nguyên tử (Atomic Types) được thực hiện ở cấp độ nào?", "type": "MULTIPLE_CHOICE", "options": ["Hệ điều hành cấp phát khóa", "Lệnh đặc biệt trực tiếp của phần cứng CPU", "Phần mềm giả lập", "Bộ nhớ ảo"], "correct_index": 1, "explanation": "Các lệnh nguyên tử được vi xử lý CPU thực thi trực tiếp."},
                {"question": "Kiểu dữ liệu nguyên tử nào trong Rust thường được dùng làm cờ hiệu dừng khẩn cấp giữa các luồng?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["AtomicBool", "atomic_bool"]}], "explanation": "AtomicBool."},
                {"question": "Sử dụng biến nguyên tử Atomic vẫn có thể làm các luồng bị dừng (blocking) chờ nhau giống như Mutex?", "type": "TRUE_FALSE", "correct_value": False, "explanation": "Sai. Các phép toán Atomic là vô khóa (Lock-free) và hoàn toàn không gây blocking."}
            ]
        ),
        (
            12,
            "Bài 4.12: Phát Triển Công Cụ Tự Động Dò Tìm Lỗ Hổng Web & Bypass WAF Bằng Rust",
            "Đóng gói vũ khí hoàn chỉnh: Tự động hóa phát hiện các lỗ hổng Web nguy hiểm (SQLi, XSS, Path Traversal), kỹ thuật xáo trộn payload và vượt tường lửa ứng dụng web WAF.",
            "https://www.youtube.com/watch?v=LdQsA8XrP4s",
            [
                "Nắm vững phương pháp tự động hóa kiểm thử lỗ hổng bảo mật ứng dụng web.",
                "Xây dựng engine kiểm thử tự động tiêm payload (Fuzzing Engine) bằng Rust.",
                "Áp dụng các kỹ thuật xáo trộn mã (Payload Mutation / Obfuscation) để bypass Web Application Firewall (WAF)."
            ],
            [
                (
                    "Nguyên Lý Của Bộ Dò Lỗ Hổng Web Tự Động (Web Vulnerability Fuzzer)",
                    "Sau khi đã có công cụ cào web bóc tách toàn bộ các tham số đầu vào (URL parameters, Form inputs, JSON bodies), bước tiếp theo của chuyên gia kiểm thử là tự động kiểm tra xem các tham số đó có bị dính các lỗ hổng bảo mật kinh điển hay không. Một Fuzzer hoạt động theo chu trình: 1. Nạp danh sách các payload kiểm thử đặc biệt. 2. Thay thế giá trị của tham số bằng payload. 3. Gửi request và phân tích phản hồi HTTP: Nếu phản hồi chứa lỗi cú pháp cơ sở dữ liệu (ví dụ: `You have an error in your SQL syntax`) -> Phát hiện lỗ hổng SQL Injection; Nếu payload phản chiếu nguyên vẹn trong HTML mà không bị mã hóa -> Phát hiện XSS; Nếu phản hồi chứa nội dung `/etc/passwd` -> Phát hiện Path Traversal / LFI."
                ),
                (
                    "Kỹ Thuật Xáo Trộn Mã Vượt Tường Lửa Ứng Dụng Web (WAF Bypass)",
                    "Các hệ thống WAF hiện đại (như Cloudflare, ModSecurity, AWS WAF) sử dụng các luật biểu thức chính quy (Regex) để chặn các payload phổ biến như `' OR '1'='1` hoặc `<script>alert(1)</script>`. Để qua mặt WAF, công cụ của chúng ta tích hợp module biến đổi payload tự động: Sử dụng kỹ thuật mã hóa ký tự URL kép (Double URL Encoding); Chèn các chú thích nội dòng của SQL (`/*%!50000SELECT*/`); Thay đổi hoa thường ngẫu nhiên (`sElEcT`); Và sử dụng các hàm thay thế tương đương không nằm trong bộ lọc."
                ),
                (
                    "Đóng Gói Nhị Phân Hoàn Chỉnh Thành Sản Phẩm Độc Lập",
                    "Toàn bộ các kiến thức từ Bài 4.1 đến Bài 4.12 được kết tinh lại: Một công cụ kiểm thử bảo mật duy nhất được biên dịch tĩnh thành một tệp nhị phân siêu nhỏ gọn, giao diện dòng lệnh Clap trực quan, tốc độ cào web Tokio bất đồng bộ hàng chục nghìn request/giây, và khả năng tự động báo cáo lỗ hổng chính xác tuyệt đối."
                )
            ],
            "Kịch bản thực chiến: Tự Động Hóa Phát Hiện Lỗ Hổng Zero-Day Trong Dự Án Doanh Nghiệp: Công cụ quét của Red Team quét qua 500 endpoint của hệ thống staging nội bộ, tự động phát hiện một endpoint API bị bỏ quên chưa qua bộ lọc WAF và trích xuất thành công phiên bản cơ sở dữ liệu qua lỗi SQLi mù (Time-based Blind SQLi).",
            "Thực hành viết hàm kiểm tra và phân tích phản hồi SQL Injection cơ bản trong Rust:",
            ("rust", """fn analyze_response(status_code: u16, body: &str) -> bool {
    // Danh sách các chuỗi lỗi cơ sở dữ liệu phổ biến
    let sql_error_signatures = [
        "you have an error in your sql syntax",
        "unclosed quotation mark after the character string",
        "microsoft ole db provider for sql server",
        "pg_query(): query failed",
    ];

    let lower_body = body.to_lowercase();
    for signature in &sql_error_signatures {
        if lower_body.contains(signature) {
            return true; // Phát hiện dấu vết lỗ hổng SQL Injection!
        }
    }
    false
}

fn main() {
    let mock_response = "HTTP 500: Database Error: You have an error in your SQL syntax near '1'";
    if analyze_response(500, mock_response) {
        println!("[!] CẢNH BÁO: Phát hiện lỗ hổng SQL Injection trên endpoint!");
    }
}"""),
            ["Luôn xin phép bằng văn bản trước khi chạy các công cụ quét lỗ hổng tự động lên bất kỳ hệ thống nào.", "Cấu hình giới hạn tốc độ request an toàn để tránh gây nghẽn dịch vụ (DoS ngoài ý muốn)."],
            ["Web Vulnerability Fuzzer tự động hóa việc tiêm payload và phân tích phản hồi.", "Kỹ thuật biến đổi payload (Obfuscation) cho phép kiểm thử tính hiệu quả của hệ thống WAF.", "Rust là ngôn ngữ hoàn hảo nhất để xây dựng các công cụ kiểm thử xâm nhập thế hệ mới."],
            [
                {"question": "Dấu hiệu nào trong phản hồi HTTP thường là bằng chứng rõ ràng nhất của lỗ hổng Error-based SQL Injection?", "type": "MULTIPLE_CHOICE", "options": ["Mã lỗi cơ sở dữ liệu hiển thị trong nội dung phản hồi", "Trang web tải nhanh hơn", "Hình ảnh bị đổi màu", "Mã trạng thái HTTP 200"], "correct_index": 0, "explanation": "Thông điệp lỗi cú pháp database hiển thị trong body phản hồi."},
                {"question": "Kỹ thuật nào làm thay đổi cấu trúc ký tự của payload để qua mặt các bộ lọc WAF mà không làm thay đổi ngữ nghĩa thực thi?", "type": "FILL_BLANK", "blanks": [{"accepted_answers": ["Obfuscation", "obfuscation", "Xáo trộn mã", "Mutation"]}], "explanation": "Payload Obfuscation / Mutation."},
                {"question": "Chạy công cụ quét lỗ hổng tự động với tốc độ quá cao có thể vô tình làm sập dịch vụ máy chủ của khách hàng?", "type": "TRUE_FALSE", "correct_value": True, "explanation": "Đúng. Tốc độ quét quá lớn có thể gây từ chối dịch vụ (DoS) ngoài ý muốn."}
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
                lesson_num=f"4.{pos}",
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
    ls = get_chapter_4_lessons()
    print(f"Generated {len(ls)} lessons for Chapter 4.")
    for l in ls:
        wc = count_vietnamese_words(l["markdown_content"])
        print(f"  - {l['title'][:40]}: {wc} words")
