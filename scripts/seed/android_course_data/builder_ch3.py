# -*- coding: utf-8 -*-
"""Builder for Chapter 3: Dịch Ngược, Phân Tích Tĩnh & Kiểm Thử Thành Phần Ứng Dụng (13 lessons).
Every lesson strictly exceeds 600 Vietnamese words and includes a 4-question miniquiz.
Based on 'Learning Pentesting for Android Devices' by Aditya Gupta.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.android_course_data.common import (
    count_vietnamese_words,
    generate_lesson_markdown,
    validate_lesson_data,
)

# Load cached YouTube videos
VIDEOS_PATH = Path(__file__).resolve().parent.parent / "android_videos.json"
with open(VIDEOS_PATH, "r", encoding="utf-8") as f:
    VIDEO_CACHE = json.load(f)["ch3"]


def get_chapter_3_lessons() -> list[dict[str, Any]]:
    lessons = []

    ch3_specs = [
        (
            1,
            "Bài 3.1: Thiết Lập Môi Trường Dịch Ngược: JADX-GUI, Apktool, Baksmali, Ghidra & Bytecode Viewer",
            "Nghiên cứu bộ công cụ phân tích tĩnh đỉnh cao cho ứng dụng Android, kỹ thuật dịch ngược bytecode và cấu hình lab.",
            [
                "Nắm vững quy trình dịch ngược tệp APK từ mã nhị phân trở về mã nguồn Java giả định.",
                "Làm chủ JADX-GUI trong việc điều hướng, tìm kiếm chuỗi ký tự và theo dõi dòng dữ liệu (Cross-References).",
                "Hiểu cách thức Apktool phân rã APK thành mã trung gian Smali và giải mã tệp tài nguyên XML.",
                "Sử dụng Ghidra / IDA Pro để dịch ngược và phân tích các tệp thư viện liên kết động C/C++ (.so)."
            ],
            [
                ("Quy Trình Dịch Ngược APK Tiêu Chuẩn (Reverse Engineering Pipeline)", "Dịch ngược ứng dụng Android là kỹ năng nền tảng hàng đầu của một chuyên gia đánh giá an ninh di động. Quy trình này bao gồm 2 nhánh chính: "
                "Nhánh 1: Dịch ngược mã nguồn cao cấp (Dex-to-Java): Công cụ hàng đầu hiện nay là `JADX`. JADX nhận đầu vào là tệp APK, AAR hoặc DEX, trực tiếp phân tích cấu trúc cây cú pháp trừu tượng (AST) và tái tạo lại mã nguồn Java/Kotlin gần như nguyên bản. JADX-GUI cung cấp giao diện trực quan hỗ trợ tìm kiếm toàn cục, tìm kiếm cách sử dụng phương thức (Find Usages / Xrefs), và giải mã các chuỗi bị che giấu. "
                "Nhánh 2: Phân rã mã trung gian có thể tái đóng gói (Dex-to-Smali): Sử dụng `Apktool`. Apktool sử dụng thư viện `baksmali` để dịch ngược `classes.dex` thành mã assembler Smali, đồng thời giải mã tệp nhị phân `AndroidManifest.xml` và `resources.arsc` trở lại định dạng văn bản gốc."),
                ("Phân Tích Thư Viện Native Với NSA Ghidra", "Nhiều ứng dụng ngân hàng và bảo mật chuyển các hàm kiểm tra tính toàn vẹn, thuật toán mã hóa tùy biến hoặc kết nối C2 sang thư viện native C/C++ (`.so`) để gây khó khăn cho việc dịch ngược. Để phân tích các thư viện này, chuyên gia bảo mật sử dụng Ghidra - bộ công cụ dịch ngược mã máy mã nguồn mở do Cơ quan An ninh Quốc gia Hoa Kỳ (NSA) phát triển. Ghidra cung cấp Decompiler mạnh mẽ có khả năng khôi phục mã máy ARM64 hoặc x86_64 thành mã C giả, cho phép theo dõi các hàm JNI export như `Java_com_example_NativeLib_verifyLicense()`."),
                ("Các Kỹ Thuật Chống Dịch Ngược (Anti-Reversing Defenses)", "Các nhà phát triển chuyên nghiệp triển khai các biện pháp làm rối mã nguồn: R8/ProGuard (đổi tên biến, hàm thành các ký tự vô nghĩa), DexGuard / Arxan (mã hóa chuỗi ký tự, làm rối luồng điều khiển Control Flow Flattening), và kiểm tra tính toàn vẹn của tệp APK lúc chạy. Một chuyên gia pentest phải thành thạo việc đọc hiểu mã sau khi bị làm rối và sử dụng script tự động để bẻ khóa cơ chế bảo vệ.")
            ],
            "Kịch bản tấn công: Kẻ tấn công tải APK từ Internet, nạp vào JADX-GUI và tìm kiếm các chuỗi nhạy cảm: `\"api_key\"`, `\"aws_secret\"`, `\"firebase_url\"`, `\"private_key\"`. Rất nhiều ứng dụng vô tình lưu trữ các khóa bí mật kết nối cơ sở dữ liệu đám mây trực tiếp trong mã Java! Kẻ tấn công trích xuất các khóa này để chiếm đoạt toàn bộ máy chủ backend. Phòng thủ: Tuyệt đối không bao giờ hardcode khóa bí mật trong mã nguồn ứng dụng client; mọi dữ liệu nhạy cảm phải được cấp phát động thông qua phiên đăng nhập được chứng thực từ Backend API.",
            "Trong phần thực hành, chúng ta sẽ sử dụng Apktool để giải nén APK và sử dụng JADX-CLI để xuất mã nguồn Java ra đĩa:",
            ("bash", """# 1. Phân rã APK thành mã Smali và tài nguyên bằng Apktool
apktool d app-target.apk -o decoded_app

# 2. Xuất toàn bộ mã nguồn Java từ APK sang thư mục nguồn bằng JADX
jadx --deobf -d jadx_sources app-target.apk

# 3. Sử dụng Ghidra ở chế độ Headless để phân tích tệp thư viện .so
analyzeHeadless /tmp/ghidra_proj MyProj -import decoded_app/lib/arm64-v8a/libnative.so"""),
            ["Không bao giờ tin tưởng mã nguồn sau decompile là chính xác 100% so với mã gốc vì trình dịch ngược có thể gặp lỗi suy luận cú pháp.", "Kiểm tra kỹ các chuỗi ký tự được mã hóa Base64 hoặc XOR trong mã nguồn."],
            ["JADX-GUI tái tạo mã nguồn Java giả định với giao diện đồ họa trực quan.", "Apktool phân rã mã thành định dạng Smali phục vụ cho việc chỉnh sửa và vá nhị phân.", "Ghidra dịch ngược mã máy của các thư viện native C/C++ thành mã C giả."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Công cụ mã nguồn mở phổ biến nhất hiện nay được sử dụng để dịch ngược tệp classes.dex trực tiếp thành mã nguồn Java/Kotlin dễ đọc kèm giao diện GUI là gì?", "options": ["A. JADX / JADX-GUI", "B. Wireshark", "C. Nmap", "D. Metasploit"], "correct_index": 0, "explanation": "JADX là công cụ chuẩn mực toàn cầu để dịch ngược và phân tích mã nguồn Android."},
                {"type": "FILL_BLANK", "question": "Tiện ích dòng lệnh dùng để phân rã APK thành mã hợp ngữ trung gian Smali và giải nén tài nguyên XML nhị phân có tên là [_____].", "blanks": [{"accepted_answers": ["Apktool", "apktool"]}], "explanation": "Apktool giải nén APK thành mã Smali và đóng gói lại sau khi chỉnh sửa."},
                {"type": "MATCHING", "question": "Nối công cụ dịch ngược với định dạng đầu ra chuyên trách:", "pairs": [{"left": "JADX", "right": "Tái tạo mã nguồn giả lập ngôn ngữ Java cấp cao"}, {"left": "Apktool (baksmali)", "right": "Phân rã thành mã hợp ngữ Dalvik Smali và tài nguyên XML"}, {"left": "Ghidra", "right": "Dịch ngược mã máy nhị phân ELF (.so) thành mã C giả"}] , "explanation": "Mỗi công cụ đóng vai trò mắt xích trong chuỗi phân tích tĩnh toàn diện."},
                {"type": "FILL_BLANK", "question": "Kỹ thuật biến đổi cấu trúc mã nguồn, đổi tên các lớp, hàm và thuộc tính thành các ký tự vô nghĩa để gây khó khăn cho việc dịch ngược được gọi là làm [_____] mã nguồn (Obfuscation).", "blanks": [{"accepted_answers": ["rối", "rối mã nguồn", "làm rối"]}], "explanation": "Obfuscation (làm rối) là kỹ thuật phòng vệ phổ biến sử dụng R8 hoặc ProGuard."}
            ]
        ),
        (
            2,
            "Bài 3.2: Ngôn Ngữ Hướng Tập Lệnh Smali: Cú Pháp Opcodes, Thanh Ghi (Registers) & Luồng Điều Khiển",
            "Nghiên cứu hợp ngữ Dalvik Bytecode định dạng Smali, kiến trúc máy ảo hướng thanh ghi và giải mã luồng rẽ nhánh.",
            [
                "Hiểu sâu kiến trúc máy ảo hướng thanh ghi (Register-Based Architecture) của Dalvik/ART.",
                "Làm chủ hệ thống định danh kiểu dữ liệu trong Smali: `I`, `Z`, `V`, `Ljava/lang/String;`.",
                "Phân biệt thanh ghi cục bộ (v-registers) và thanh ghi tham số hàm (p-registers).",
                "Đọc hiểu các tập lệnh Opcodes phổ biến: `const`, `move`, `invoke-virtual`, `if-eqz`, `return-void`."
            ],
            [
                ("Kiến Trúc Máy Ảo Hướng Thanh Ghi (Register-Based VM)", "Khác với máy ảo Java tiêu chuẩn (JVM) vốn hoạt động dựa trên ngăn xếp toán hạng (Stack-Based Architecture - nơi mọi phép tính đều phải push và pop qua stack), máy ảo Dalvik/ART của Android được thiết kế theo kiến trúc hướng thanh ghi (Register-Based Architecture). Kiến trúc này mô phỏng sát sao vi xử lý phần cứng thực tế (ARM), cho phép lưu trữ trực tiếp các biến trong các thanh ghi ảo, giảm thiểu số lượng lệnh cần thực thi và tăng tốc độ xử lý trên thiết bị di động."),
                ("Quy Ước Định Danh Thanh Ghi v và p", "Trong một phương thức Smali, có 2 cách đặt tên thanh ghi: 1. Thanh ghi cục bộ (`v0`, `v1`, `v2`...): dùng để lưu trữ các biến tạm thời trong hàm. 2. Thanh ghi tham số (`p0`, `p1`, `p2`...): dùng để tiếp nhận các tham số truyền vào hàm. "
                "Quy tắc vàng: Đối với các phương thức không tĩnh (non-static method), thanh ghi `p0` LUÔN LUÔN là con trỏ tham chiếu `this` của đối tượng hiện tại! Tham số thứ nhất của hàm sẽ bắt đầu từ `p1`, tham số thứ hai là `p2`. Đối với phương thức tĩnh (static method), `p0` sẽ là tham số đầu tiên."),
                ("Cú Pháp Smali & Các Opcodes Cốt Lõi", "Mỗi dòng lệnh Smali bao gồm một mã tác vụ (Opcode) kèm theo các thanh ghi tham số: "
                "`const/4 v0, 0x1`: Nạp giá trị số nguyên 1 (hoặc true) vào thanh ghi v0. "
                "`invoke-virtual {p0, v0}, Lcom/example/MyClass;->checkAccess(Z)Z`: Gọi phương thức checkAccess của đối tượng this với tham số trong v0. "
                "`move-result v0`: Nhận kết quả trả về từ lệnh gọi hàm trước đó và lưu vào v0. "
                "`if-eqz v0, :cond_0`: Lệnh rẽ nhánh có điều kiện - nếu giá trị trong v0 bằng 0 (false), nhảy đến nhãn `:cond_0`. "
                "`return v0`: Trả về giá trị trong thanh ghi v0.")
            ],
            "Kịch bản tấn công: Đọc hiểu logic kiểm tra bản quyền hoặc xác thực sinh trắc học trong Smali. Kẻ tấn công giải nén APK bằng Apktool, tìm đến hàm `isUserAdmin()` hoặc `verifyPassword()`. Hàm này thường kết thúc bằng lệnh kiểm tra kết quả `if-nez v0, :cond_pass`. Kẻ tấn công chỉ cần đổi lệnh thành `if-eqz v0, :cond_pass` hoặc chèn trực tiếp `const/4 v0, 0x1` ngay trước lệnh `return v0` để bẻ khóa hoàn toàn cơ chế bảo vệ! Phòng thủ: Sử dụng kiểm tra toàn vẹn chữ ký APK kết hợp dịch chuyển logic xác thực quan trọng lên máy chủ Backend.",
            "Trong phần thực hành, chúng ta sẽ phân tích một đoạn mã Smali thực tế và theo dõi trạng thái các thanh ghi:",
            ("smali", """.method public isPremiumUser()Z
    .registers 2

    .prologue
    # Thanh ghi p0 là con trỏ 'this'
    # v0 là thanh ghi cục bộ
    iget-boolean v0, p0, Lcom/pwd301/User;->isSubscribed:Z

    # Nếu isSubscribed là true (khác 0), nhảy tới cond_premium
    if-nez v0, :cond_free

    const/4 v0, 0x1
    return v0

    :cond_free
    const/4 v0, 0x0
    return v0
.end method"""),
            ["Luôn nhớ rằng trong non-static method, thanh ghi p0 luôn đại diện cho con trỏ 'this'.", "Kiểm tra kỹ số lượng .registers khai báo ở đầu hàm để không sử dụng vượt quá giới hạn thanh ghi."],
            ["Dalvik/ART hoạt động theo kiến trúc máy ảo hướng thanh ghi hiệu năng cao.", "Thanh ghi v lưu biến cục bộ, thanh ghi p tiếp nhận tham số truyền vào hàm.", "Hiểu rõ các opcodes rẽ nhánh điều kiện là chìa khóa để phân tích và vá nhị phân."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Trong một phương thức không tĩnh (non-static method) viết bằng mã Smali, thanh ghi nào luôn được hệ thống gán cố định đại diện cho tham chiếu 'this' của đối tượng hiện tại?", "options": ["A. p0", "B. v0", "C. p1", "D. v1"], "correct_index": 0, "explanation": "Trong non-static method, p0 luôn trỏ đến chính instance của đối tượng (this)."},
                {"type": "FILL_BLANK", "question": "Ký tự viết tắt đại diện cho kiểu dữ liệu luận lý Boolean (đúng/sai) trong quy ước định danh kiểu của Smali là chữ cái in hoa [_____].", "blanks": [{"accepted_answers": ["Z", "z"]}], "explanation": "Trong Smali, Z đại diện cho Boolean, I đại diện cho Integer, V đại diện cho Void."},
                {"type": "MATCHING", "question": "Nối ký tự định danh kiểu Smali với kiểu dữ liệu tương ứng:", "pairs": [{"left": "I", "right": "Kiểu số nguyên 32-bit (int)"}, {"left": "Z", "right": "Kiểu luận lý Boolean (true/false)"}, {"left": "V", "right": "Kiểu trả về rỗng không có giá trị (void)"}, {"left": "Ljava/lang/String;", "right": "Đối tượng chuỗi ký tự String"}] , "explanation": "Quy ước định danh kiểu trong Smali tương tự như quy ước trong JVM Bytecode."},
                {"type": "FILL_BLANK", "question": "Mã lệnh opcode trong Smali dùng để kiểm tra nếu giá trị trong thanh ghi bằng 0 (false) thì nhảy tới nhãn chỉ định là if-[_____].", "blanks": [{"accepted_answers": ["eqz", "EQZ"]}], "explanation": "if-eqz (if equal to zero) rẽ nhánh khi thanh ghi có giá trị bằng 0."}
            ]
        ),
        (
            3,
            "Bài 3.3: Kỹ Thuật Vá Mã Nguồn Nhị Phân (Binary Patching): Bẻ Khóa Logic & Đóng Gói Lại APK",
            "Nghiên cứu quy trình sửa đổi bytecode Smali, chèn mã theo dõi, tái đóng gói bằng Apktool và ký số lại APK.",
            [
                "Làm chủ quy trình 4 bước của kỹ thuật Binary Patching: Decompile -> Patch -> Recompile -> Sign.",
                "Kỹ thuật chèn lệnh ghi log hệ thống (Log Injection) trực tiếp vào mã Smali để trích xuất khóa bí mật lúc chạy.",
                "Sửa đổi các luồng kiểm tra logic để vượt qua màn hình đăng nhập hoặc kiểm tra Root.",
                "Sử dụng công cụ `zipalign` và `apksigner` để hoàn thiện gói cài đặt có thể cài đặt được."
            ],
            [
                ("Quy Trình 4 Bước Của Kỹ Thuật Vá Nhị Phân (Binary Patching)", "Binary Patching (vá mã nhị phân) là kỹ thuật can thiệp và sửa đổi trực tiếp mã thực thi của ứng dụng mà không cần mã nguồn gốc ban đầu. Quy trình thực hiện bao gồm 4 bước nghiêm ngặt: "
                "Bước 1 (Decompile): Sử dụng `apktool d target.apk` để phân rã ứng dụng thành thư mục chứa mã Smali và tài nguyên. "
                "Bước 2 (Patch): Định vị tệp Smali chứa hàm kiểm tra logic cần bẻ khóa, chỉnh sửa các lệnh rẽ nhánh hoặc ép giá trị trả về. "
                "Bước 3 (Recompile): Đóng gói lại thư mục thành tệp APK mới bằng `apktool b -o patched_unsigned.apk`. "
                "Bước 4 (Align & Sign): Bắt buộc căn chỉnh tối ưu bộ nhớ 4-byte bằng `zipalign`, sau đó ký số bằng chứng chỉ số tự tạo thông qua `apksigner`."),
                ("Kỹ Thuật Chèn Lệnh Log Để Trích Xuất Dữ Liệu (Log Injection)", "Khi ứng dụng sử dụng các thuật toán giải mã phức tạp mà phân tích tĩnh bằng mắt thường quá tốn thời gian, chuyên gia pentest có thể chèn một dòng lệnh gọi hàm `android.util.Log.d()` ngay tại điểm dữ liệu vừa được giải mã trong Smali: "
                "`invoke-static {v0, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I`. "
                "Khi ứng dụng đã vá được cài đặt và khởi chạy, khóa giải mã hoặc mật khẩu sẽ tự động được in ra cửa sổ Logcat của ADB một cách rõ ràng!"),
                ("Căn Chỉnh Bộ Nhớ 4-Byte Bằng Zipalign", "Hệ điều hành Android yêu cầu tất cả các tài nguyên không nén trong tệp APK phải được căn chỉnh ranh giới bộ nhớ theo bội số của 4-byte (4-byte alignment) so với điểm bắt đầu tệp. Công cụ `zipalign` quét tệp APK và sắp xếp lại các trường nhị phân. Nếu bỏ qua bước zipalign, hệ thống sẽ không thể sử dụng kỹ thuật `mmap()` để nạp trực tiếp tài nguyên vào RAM, dẫn đến việc ứng dụng tiêu tốn nhiều bộ nhớ hơn hoặc bị từ chối cài đặt trên các phiên bản Android mới.")
            ],
            "Kịch bản tấn công: Bẻ khóa tính năng kiểm tra thiết bị Root (Root Detection Bypass). Ứng dụng ngân hàng có hàm `isDeviceRooted()` kiểm tra sự tồn tại của tệp nhị phân `/system/bin/su`. Kẻ tấn công dùng Apktool giải nén, tìm đến hàm `isDeviceRooted()Z`, thay thế toàn bộ thân hàm bằng hai dòng lệnh ngắn gọn: `const/4 v0, 0x0` và `return v0`. Sau khi đóng gói và ký lại, ứng dụng chạy trơn tru trên mọi máy đã Root mà không hề phát hiện ra! Phòng thủ: Kết hợp nhiều kỹ thuật kiểm tra Root đa tầng ở tầng native C/C++, kiểm tra tính toàn vẹn của chữ ký APK và sử dụng RASP (Runtime Application Self-Protection).",
            "Trong phần thực hành, chúng ta sẽ thực thi chuỗi lệnh hoàn chỉnh để đóng gói, căn chỉnh và ký số lại một APK:",
            ("bash", """# 1. Đóng gói lại thư mục thành APK chưa ký
apktool b decoded_app -o app_patched_raw.apk

# 2. Căn chỉnh tối ưu hóa bộ nhớ 4-byte bằng zipalign
zipalign -v -p 4 app_patched_raw.apk app_patched_aligned.apk

# 3. Tạo một kho khóa phát hành tự ký nếu chưa có
keytool -genkeypair -v -keystore test.keystore -alias testalias -keyalg RSA -keysize 2048 -validity 10000 -storepass password123 -keypass password123 -dname "CN=Tester"

# 4. Ký số APK với apksigner (hỗ trợ Scheme v2 và v3)
apksigner sign --ks test.keystore --ks-pass pass:password123 --out app_final_signed.apk app_patched_aligned.apk

# 5. Cài đặt APK đã vá lên thiết bị qua ADB
adb install -r app_final_signed.apk"""),
            ["Luôn chạy zipalign TRƯỚC KHI ký số bằng apksigner (nếu chạy sau sẽ làm hỏng chữ ký Scheme v2).", "Kiểm tra kỹ nhật ký build của Apktool để kịp thời sửa các lỗi định dạng tài nguyên XML."],
            ["Vá nhị phân Smali cho phép sửa đổi luồng thực thi và bẻ khóa các cơ chế kiểm tra cục bộ.", "Chèn mã Log là phương thức cực kỳ hiệu quả để thu thập dữ liệu nhạy cảm lúc chạy.", "Quy trình zipalign và apksigner là bắt buộc để tạo ra bản APK hoàn chỉnh."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Công cụ nào trong Android SDK bắt buộc phải được thực thi để căn chỉnh dữ liệu theo ranh giới 4-byte trước khi tiến hành ký số tệp APK bằng apksigner?", "options": ["A. zipalign", "B. aapt2", "C. d8", "D. dx"], "correct_index": 0, "explanation": "zipalign căn chỉnh các tài nguyên không nén theo bội số 4-byte để tối ưu hóa mmap bộ nhớ."},
                {"type": "FILL_BLANK", "question": "Tiện ích dòng lệnh của Java JDK được sử dụng để tạo mới một tệp kho khóa (Keystore) chứa cặp khóa mã hóa RSA/ECDSA là [_____].", "blanks": [{"accepted_answers": ["keytool", "keytool.exe"]}], "explanation": "keytool quản lý các kho khóa số và chứng chỉ bảo mật."},
                {"type": "MATCHING", "question": "Nối các bước trong quy trình Binary Patching theo thứ tự chuẩn:", "pairs": [{"left": "Bước 1", "right": "Phân rã APK thành mã Smali bằng apktool d"}, {"left": "Bước 2", "right": "Sửa đổi luồng logic trong các tệp mã nguồn .smali"}, {"left": "Bước 3", "right": "Tái đóng gói thư mục thành APK bằng apktool b"}, {"left": "Bước 4", "right": "Căn chỉnh bộ nhớ với zipalign và ký số bằng apksigner"}] , "explanation": "Tuân thủ đúng thứ tự 4 bước bảo đảm APK sau khi vá có thể cài đặt và chạy bình thường."},
                {"type": "FILL_BLANK", "question": "Nếu chạy lệnh zipalign SAU KHI đã ký số bằng apksigner (Scheme v2), chữ ký số của APK sẽ bị [_____] và không thể cài đặt được.", "blanks": [{"accepted_answers": ["hỏng", "vô hiệu hóa", "hủy", "mất hiệu lực", "lỗi"]}], "explanation": "Scheme v2 ký toàn bộ file nhị phân, zipalign thay đổi byte nhị phân sẽ làm hỏng chữ ký."},
            ]
        ),
        (
            4,
            "Bài 3.4: Kiểm Thử An Ninh Thành Phần Activity: Exported Activities & Activity Hijacking",
            "Nghiên cứu bề mặt tấn công của các Activity công khai, rủi ro điều hướng trái phép và tấn công cướp màn hình.",
            [
                "Hiểu sâu quy tắc xác định một Activity có bị Export hay không dựa trên `android:exported` và Intent Filter.",
                "Sử dụng công cụ `adb shell am start` để kích hoạt trực tiếp các Activity nội bộ bị lộ lọt.",
                "Phân tích lỗ hổng vượt qua màn hình xác thực (Authentication Bypass) do Exported Activity.",
                "Áp dụng các biện pháp làm cứng: khóa cờ exported, thiết lập permission và kiểm tra Intent Caller."
            ],
            [
                ("Quy Tắc Xác Định Trạng Thái Exported Của Activity", "Một Activity được xem là 'Exported' (công khai ra ngoài) khi bất kỳ ứng dụng nào khác trên thiết bị cũng có thể gửi Intent để khởi chạy nó. Thuộc tính `android:exported` trong AndroidManifest.xml quy định trực tiếp trạng thái này: "
                "Nếu `android:exported=\"true\"`: Activity mở công khai cho toàn thế giới. "
                "Nếu `android:exported=\"false\"`: Activity bị khóa chặt trong nội bộ ứng dụng. "
                "Quy tắc ngầm định nguy hiểm: Trước Android 12, nếu một Activity KHÔNG khai báo thuộc tính `android:exported`, nhưng bên trong nó CÓ chứa ít nhất một thẻ `<intent-filter>`, hệ điều hành sẽ tự động mặc định coi nó là `android:exported=\"true\"`! Điều này dẫn đến hàng ngàn ứng dụng vô tình phơi bày các màn hình nội bộ nhạy cảm ra ngoài."),
                ("Khai Thác Lỗ Hổng Authentication Bypass", "Nhiều ứng dụng phân tách luồng nghiệp vụ thành nhiều màn hình: `LoginActivity` -> `PinVerificationActivity` -> `DashboardActivity`. Giả định sai lầm của lập trình viên là người dùng bắt buộc phải đi tuần tự từ màn hình đăng nhập mới tới được trang chủ. "
                "Tuy nhiên, nếu `DashboardActivity` bị đặt cờ `android:exported=\"true\"` và không kiểm tra trạng thái token phiên đăng nhập trong hàm `onCreate()`, kẻ tấn công có thể sử dụng lệnh ADB hoặc viết một ứng dụng độc hại gửi Intent trực tiếp đến `DashboardActivity`, vượt qua hoàn toàn bước nhập mật khẩu và mã OTP!"),
                ("Tấn Công Activity Hijacking & Phishing Overlay", "Khi một Activity có cơ chế điều hướng lỏng lẻo hoặc sử dụng `launchMode=\"singleTask\"`, ứng dụng độc hại có thể khởi chạy một màn hình giả mạo đè lên ngăn xếp để lừa người dùng nhập mật khẩu. Nguy hiểm hơn, nếu Activity trả về dữ liệu nhạy cảm qua `setResult()`, kẻ tấn công có thể lắng nghe kết quả trả về thông qua `startActivityForResult()`.")
            ],
            "Kịch bản tấn công: Kẻ tấn công sử dụng lệnh `adb shell am start -n com.victim.app/.admin.AdminPanelActivity` để kích hoạt giao diện quản trị viên bị lộ lọt. Nếu màn hình này không có cơ chế xác thực quyền, kẻ tấn công có thể nhấn các nút chức năng để xóa dữ liệu hoặc cấp quyền hệ thống. Phòng thủ: Luôn khóa toàn bộ Activity nội bộ bằng `android:exported=\"false\"`. Từ Android 12+, thuộc tính `android:exported` bắt buộc phải được khai báo tường minh cho mọi component có chứa intent-filter.",
            "Trong phần thực hành, chúng ta sẽ sử dụng ADB Activity Manager (am) để kiểm thử việc kích hoạt Activity trái phép:",
            ("bash", """# 1. Liệt kê toàn bộ các Activity được khai báo trong manifest bằng aapt2
aapt2 dump xmltree app-target.apk --file AndroidManifest.xml | grep -i "activity"

# 2. Thử nghiệm gửi Intent kích hoạt trực tiếp màn hình chuyển tiền
adb shell am start -n com.backend.androidsec/.ui.TransferMoneyActivity

# 3. Kích hoạt Activity kèm theo dữ liệu Extra truyền trong Bundle
adb shell am start -n com.backend.androidsec/.ui.UserProfileActivity --es "USER_ROLE" "ADMIN" """),
            ["Luôn khai báo tường minh android:exported=\"false\" cho tất cả các Activity không cần tương tác từ bên ngoài.", "Trong onCreate(), luôn kiểm tra tính hợp lệ của token phiên đăng nhập trước khi hiển thị dữ liệu nhạy cảm."],
            ["Exported Activity cho phép bất kỳ ứng dụng nào kích hoạt mà không cần tương tác người dùng.", "Lỗ hổng Authentication Bypass xảy ra khi Activity đích thiếu kiểm tra trạng thái xác thực.", "Lệnh am start của ADB là công cụ kiểm thử bề mặt tấn công Activity hiệu quả."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Lệnh dòng lệnh nào của tiện ích Activity Manager (am) trong ADB shell được sử dụng để khởi chạy trực tiếp một Activity cụ thể trên thiết bị?", "options": ["A. am start -n <package>/<activity>", "B. am launch <activity>", "C. pm start <activity>", "D. service call activity"], "correct_index": 0, "explanation": "am start -n kích hoạt một component Activity thông qua Intent tường minh."},
                {"type": "FILL_BLANK", "question": "Từ phiên bản Android [_____], Google bắt buộc mọi thành phần có chứa intent-filter đều phải khai báo thuộc tính android:exported một cách tường minh.", "blanks": [{"accepted_answers": ["12", "Android 12", "API 31"]}], "explanation": "Android 12 (API 31) siết chặt bảo mật, cấm việc suy diễn ngầm định cờ exported."},
                {"type": "MATCHING", "question": "Nối thuộc tính android:exported với phạm vi truy cập:", "pairs": [{"left": "android:exported=\"false\"", "right": "Chỉ các thành phần trong cùng ứng dụng mới có quyền khởi chạy"}, {"left": "android:exported=\"true\"", "right": "Mọi ứng dụng trên thiết bị đều có thể gửi Intent kích hoạt"}, {"left": "android:permission", "right": "Yêu cầu bên gọi phải được cấp quyền chỉ định mới được truy cập"}] , "explanation": "Quản trị cờ exported là bài học vỡ lòng trong an ninh ứng dụng Android."},
                {"type": "FILL_BLANK", "question": "Phương thức kiểm tra trạng thái xác thực người dùng bắt buộc phải được đặt trong hàm callback on[_____]() của mọi Activity nhạy cảm.", "blanks": [{"accepted_answers": ["Create", "create", "Create()", "Resume", "resume"]}], "explanation": "onCreate() hoặc onResume() là nơi thẩm định phiên làm việc trước khi vẽ giao diện."}
            ]
        ),
        (
            5,
            "Bài 3.5: Kiểm Thử An Ninh Dịch Vụ: Unprotected Services & Trực Tiếp Thực Thi Tác Vụ Đặc Quyền",
            "Nghiên cứu rủi ro từ các Service chạy ngầm bị mở công khai, thực thi tác vụ trái phép và chiếm đoạt IPC.",
            [
                "Hiểu cơ chế hoạt động của các Service bị exported và rủi ro bị kích hoạt ngầm từ bên ngoài.",
                "Sử dụng lệnh `adb shell am startservice` để gửi Intent độc hại tới Service mục tiêu.",
                "Phân tích kịch bản tấn công DoS và thực thi tác vụ nặng làm cạn kiệt tài nguyên thiết bị.",
                "Thiết lập cơ chế kiểm tra chữ ký số (Signature Protection) cho các Service nội bộ."
            ],
            [
                ("Bề Mặt Tấn Công Của Dịch Vụ Nền (Service Attack Surface)", "Tương tự như Activity, Service cũng có thể bị xuất bản ra ngoài thông qua thuộc tính `android:exported=\"true\"`. Tuy nhiên, Service nguy hiểm hơn rất nhiều vì nó hoạt động hoàn toàn trong nền không có giao diện hiển thị. Người dùng hoàn toàn không hay biết một Service độc hại đang được kích hoạt và chạy ngầm trên thiết bị của mình. "
                "Nếu một Service thực hiện các tác vụ nhạy cảm (như tải về bản cập nhật tệp tin, xóa bộ đệm, gửi dữ liệu phân tích, hoặc xử lý giao dịch) mà mở công khai mà không có cơ chế bảo vệ, bất kỳ ứng dụng độc hại nào cũng có thể gửi Intent để kích hoạt Service đó bất cứ lúc nào."),
                ("Kịch Bản Tấn Công Từ Chối Dịch Vụ (DoS) & Cạn Kiệt Pin", "Một ứng dụng độc hại có thể liên tục gửi hàng ngàn Intent kích hoạt một Exported Service thực hiện các tác vụ tính toán nặng hoặc đọc ghi đĩa liên tục. Hành vi này làm nghẽn hàng đợi thông điệp, tiêu tốn 100% dung lượng CPU và làm cạn kiệt pin của thiết bị chỉ trong thời gian ngắn, gây ra hiện tượng quá nhiệt và treo máy."),
                ("Bảo Vệ Dịch Vụ Bằng Signature Permission", "Để các ứng dụng nội bộ có thể kết nối với Service của nhau mà không bị bên thứ ba nhòm ngó, phương án tối ưu duy nhất là thiết lập một quyền bảo vệ có `protectionLevel=\"signature\"`: "
                "`<service android:name=\".SyncService\" android:exported=\"true\" android:permission=\"com.backend.permission.SYNC_DATA\" />`. "
                "Hệ điều hành sẽ tự động kiểm tra chữ ký của ứng dụng gửi Intent: nếu không khớp với chữ ký của ứng dụng cung cấp Service, Intent sẽ bị chặn đứng lập tức tại nhân Linux.")
            ],
            "Kịch bản tấn công: Kẻ tấn công phát hiện một ứng dụng ví điện tử có Service mang tên `PaymentProcessService` bị đặt cờ `android:exported=\"true\"`. Kẻ tấn công tạo một ứng dụng chạy ngầm, gửi Intent chứa các tham số chuyển tiền giả mạo: `adb shell am startservice -n com.victim.wallet/.PaymentProcessService --es \"TO_ACC\" \"123456\" --ef \"AMOUNT\" 500000`. Nếu Service thiếu kiểm tra xác thực, tiền sẽ bị chuyển đi tự động! Phòng thủ: Khóa ngay cờ `android:exported=\"false\"` và không bao giờ thực hiện giao dịch tài chính chỉ dựa trên tham số Intent.",
            "Trong phần thực hành, chúng ta sẽ sử dụng ADB để kiểm tra và gửi Intent kích hoạt Service mục tiêu:",
            ("bash", """# 1. Liệt kê các Service đang chạy trên hệ thống
adb shell dumpsys activity services | grep -E "ServiceRecord" | head -n 15

# 2. Thử nghiệm gửi Intent kích hoạt Started Service qua ADB
adb shell am startservice -n com.backend.androidsec/.service.BackgroundSyncService --es "ACTION" "FULL_WIPE"

# 3. Quan sát nhật ký Logcat để xem phản ứng của dịch vụ
adb shell logcat -s "BackgroundSyncService" """),
            ["Không bao giờ đặt cờ android:exported=\"true\" cho các Service thực hiện logic ghi hoặc xóa dữ liệu.", "Luôn kiểm tra tính hợp lệ của tham số trong onStartCommand()."],
            ["Unprotected Services là mục tiêu nguy hiểm vì chúng hoạt động hoàn toàn âm thầm trong nền.", "Tấn công Service có thể dẫn đến rò rỉ dữ liệu, thực thi tác vụ trái phép hoặc từ chối dịch vụ DoS.", "Cấp độ bảo vệ signature là chốt chặn bắt buộc cho các dịch vụ liên ứng dụng nội bộ."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Lệnh dòng lệnh nào trong ADB shell được sử dụng để gửi một Intent kích hoạt Started Service chạy ngầm trên thiết bị?", "options": ["A. am startservice", "B. am launch-service", "C. pm start-service", "D. service start"], "correct_index": 0, "explanation": "am startservice gửi một Intent tới phương thức onStartCommand() của Service mục tiêu."},
                {"type": "FILL_BLANK", "question": "Thuộc tính bắt buộc trong tệp manifest để ngăn chặn hoàn toàn việc các ứng dụng khác kích hoạt Service nội bộ là android:exported=\"[_____]\".", "blanks": [{"accepted_answers": ["false", "FALSE"]}], "explanation": "android:exported=\"false\" cô lập dịch vụ trong nội bộ gói ứng dụng."},
                {"type": "MATCHING", "question": "Nối loại lỗ hổng Service với hậu quả:", "pairs": [{"left": "Exported Service không bảo vệ", "right": "Bị ứng dụng độc hại kích hoạt thực thi tác vụ ngoài ý muốn"}, {"left": "Service xử lý I/O trên Main Thread", "right": "Gây nghẽn giao diện và xuất hiện hộp thoại lỗi ANR"}, {"left": "Thiếu kiểm tra tham số Intent", "right": "Dẫn đến thực thi lệnh độc hại hoặc tấn công logic"}] , "explanation": "Bảo vệ tầng Service đòi hỏi kiểm soát cả ranh giới IPC lẫn quản lý luồng xử lý."},
                {"type": "FILL_BLANK", "question": "Phương thức callback trong Service tiếp nhận Intent và dữ liệu tham số truyền vào mỗi lần gọi startService() là onStart[_____]().", "blanks": [{"accepted_answers": ["Command", "command", "Command()"]}], "explanation": "onStartCommand tiếp nhận Intent, cờ flags và startId của dịch vụ."}
            ]
        ),
        (
            6,
            "Bài 3.6: Kiểm Thử An Ninh Broadcast Receivers: Nghe Lén Dữ Liệu & Giả Mạo Phát Sóng (Broadcast Injection)",
            "Nghiên cứu các cuộc tấn công nhắm vào bộ thu phát sóng, kỹ thuật Broadcast Injection và rò rỉ thông tin cá nhân.",
            [
                "Hiểu cơ chế phát hiện các Broadcast Receiver bị mở công khai trong AndroidManifest.xml.",
                "Sử dụng công cụ `adb shell am broadcast` để gửi thông điệp phát sóng giả mạo.",
                "Phân tích lỗ hổng Broadcast Sniffing khi ứng dụng phát tán dữ liệu nhạy cảm qua Implicit Broadcast.",
                "Áp dụng cờ phân quyền bảo mật hai chiều (Sender/Receiver Permissions) để ngăn chặn tấn công."
            ],
            [
                ("Bề Mặt Tấn Công Của Broadcast Receivers", "Broadcast Receiver đóng vai trò là một cổng giao tiếp mở tiếp nhận thông tin từ thế giới bên ngoài. Hai mối đe dọa an ninh lớn nhất đối với Broadcast Receiver bao gồm: "
                "1. Tấn công Giả mạo phát sóng (Broadcast Injection): Nếu một Receiver được cấu hình để lắng nghe các sự kiện nhạy cảm (ví dụ như lệnh cập nhật cấu hình, thông báo người dùng đăng nhập thành công, hoặc yêu cầu xóa bộ đệm) mà mở công khai không kiểm tra nguồn gửi, kẻ tấn công có thể dễ dàng gửi Intent giả mạo để kích hoạt các hành vi nguy hiểm đó. "
                "2. Tấn công Nghe lén phát sóng (Broadcast Sniffing): Xảy ra khi ứng dụng phát đi một thông điệp chứa thông tin bí mật (như mã xác thực, tọa độ GPS, số điện thoại) thông qua cơ chế phát sóng mở (Implicit Broadcast). Mọi ứng dụng có mặt trên thiết bị đều có thể bí mật đăng ký Receiver để thu thập dữ liệu này."),
                ("Kiểm Thử Với Lệnh am broadcast Của ADB", "Công cụ Activity Manager trong ADB cung cấp lệnh `am broadcast` cực kỳ mạnh mẽ cho phép chuyên gia pentest mô phỏng bất kỳ sự kiện phát sóng nào: "
                "`adb shell am broadcast -a com.victim.action.RESET_PASSWORD --es \"NEW_PASS\" \"123456\"`. "
                "Nếu Receiver tiếp nhận và xử lý tham số mà không có bất kỳ bước xác thực nào, ứng dụng sẽ bị bẻ khóa logic ngay lập tức."),
                ("Phòng Thủ Bằng Cơ Chế Bảo Mật Hai Chiều", "Để bảo đảm an toàn tuyệt đối, nhà phát triển phải áp dụng cơ chế bảo vệ hai chiều: "
                "Phía phát (Sender): Chỉ định rõ ràng permission bảo vệ khi gửi: `sendBroadcast(intent, \"com.backend.RECEIVER_PERM\")`. Chỉ các Receiver có quyền này mới nhận được gói tin. "
                "Phía nhận (Receiver): Khai báo thuộc tính `android:permission` trong thẻ `<receiver>` để yêu cầu bên gửi phải có quyền mới được phép truyền thông điệp tới.")
            ],
            "Kịch bản tấn công: Kẻ tấn công tạo một ứng dụng độc hại đăng ký lắng nghe hành động `android.provider.Telephony.SMS_RECEIVED`. Khi tin nhắn mã OTP ngân hàng được gửi tới máy, ứng dụng độc hại đọc ngay mã OTP và gửi về máy chủ tin tặc trước khi người dùng kịp đọc! Phòng thủ: Từ các phiên bản Android hiện đại, quyền đọc SMS được Google quản lý vô cùng khắt khe và các ứng dụng ngân hàng chuyển sang sử dụng SMS Retriever API (tự động điền mã OTP mà không cần cấp quyền đọc SMS).",
            "Trong phần thực hành, chúng ta sẽ sử dụng ADB để kiểm thử phát sóng giả mạo tới một Receiver mục tiêu:",
            ("bash", """# 1. Liệt kê các Broadcast Receiver đã đăng ký trong hệ thống
adb shell dumpsys activity broadcasts | grep -E "ReceiverList" | head -n 15

# 2. Gửi một Broadcast giả mạo thông báo sự kiện kích hoạt tài khoản
adb shell am broadcast -a com.backend.androidsec.ACTION_ACCOUNT_VERIFIED --ez "IS_VERIFIED" true

# 3. Theo dõi Logcat xem Receiver có xử lý thông điệp giả mạo hay không
adb shell logcat -s "AccountReceiver" """),
            ["Không bao giờ truyền dữ liệu cá nhân, mật khẩu hoặc mã OTP qua Implicit Broadcast.", "Sử dụng SMS Retriever API thay vì xin quyền READ_SMS trực tiếp."],
            ["Broadcast Injection cho phép kẻ tấn công giả mạo các sự kiện kích hoạt hành vi trong ứng dụng.", "Broadcast Sniffing làm lộ lọt dữ liệu nhạy cảm truyền qua Implicit Broadcast.", "Bảo vệ hai chiều bằng custom permission cấp độ signature là giải pháp chuẩn mực."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Lệnh dòng lệnh nào trong ADB shell được sử dụng để phát một thông điệp Broadcast với hành động (action) chỉ định tới hệ thống?", "options": ["A. am broadcast -a <action>", "B. am send-broadcast", "C. pm broadcast", "D. service broadcast"], "correct_index": 0, "explanation": "am broadcast -a <action> gửi Intent phát thanh tới toàn bộ các Receiver phù hợp."},
                {"type": "FILL_BLANK", "question": "Hành vi một ứng dụng độc hại lén lút đăng ký lắng nghe và thu thập các thông điệp chứa dữ liệu nhạy cảm phát tán công khai được gọi là Broadcast [_____] (Nghe lén).", "blanks": [{"accepted_answers": ["Sniffing", "sniffing", "nghe lén"]}], "explanation": "Broadcast Sniffing khai thác tính chất công khai của Implicit Broadcast."},
                {"type": "MATCHING", "question": "Nối vai trò bảo vệ trong phát sóng Broadcast:", "pairs": [{"left": "Sender Permission", "right": "Bên phát chỉ định quyền bắt buộc bên nhận phải có"}, {"left": "Receiver Permission", "right": "Bên nhận chỉ định quyền bắt buộc bên phát phải sở hữu"}, {"left": "SMS Retriever API", "right": "Tự động đọc OTP an toàn mà không cần cấp quyền READ_SMS"}] , "explanation": "Bảo vệ hai chiều đảm bảo chỉ các bên tin cậy mới có thể giao tiếp."},
                {"type": "FILL_BLANK", "question": "Tham số cờ trong lệnh am broadcast dùng để truyền một giá trị Boolean (đúng/sai) vào Intent Extra là --e[_____].", "blanks": [{"accepted_answers": ["z", "Z", "--ez"]}], "explanation": "--ez truyền tham số kiểu boolean, trong khi --es truyền kiểu string, --ei truyền kiểu integer."}
            ]
        ),
        (
            7,
            "Bài 3.7: Kiểm Thử An Ninh Content Providers: Khai Thác Path Traversal & Trích Xuất Dữ Liệu Tệp Nhạy Cảm",
            "Nghiên cứu các lỗ hổng nghiêm trọng trong Content Provider, tấn công duyệt đường dẫn tệp (Directory Traversal) và rò rỉ tệp tin.",
            [
                "Hiểu cơ chế vận hành của hàm `openFile()` trong Content Provider để chia sẻ tệp tin.",
                "Phân tích lỗ hổng Directory / Path Traversal khi không kiểm tra ký tự `../` trong URI.",
                "Sử dụng công cụ `adb shell content` để truy vấn và trích xuất dữ liệu từ Content Provider bị hở.",
                "Áp dụng phương pháp làm sạch đường dẫn (Path Sanitization) với `File.getCanonicalPath()`."
            ],
            [
                ("Chia Sẻ Tệp Tin Qua Content Provider & Hàm openFile()", "Bên cạnh việc chia sẻ dữ liệu bảng tương tự như cơ sở dữ liệu, Content Provider còn cung cấp cơ chế chia sẻ tệp tin trực tiếp thông qua việc ghi đè phương thức `openFile(Uri uri, String mode)`. Phương thức này nhận vào một Content URI và trả về một đối tượng `ParcelFileDescriptor` đại diện cho tệp tin trên đĩa. "
                "Ví dụ: Ứng dụng cung cấp URI `content://com.victim.provider/files/report.pdf`, hàm `openFile()` sẽ ánh xạ chuỗi `report.pdf` vào thư mục nội bộ: `File(\"/data/data/com.victim/files/\", uri.getLastPathSegment())`."),
                ("Cơ Chế Lỗ Hổng Path Traversal (Duyệt Đường Dẫn)", "Lỗ hổng chết người xuất hiện khi lập trình viên tin tưởng hoàn toàn vào tham số đường dẫn do người dùng truyền vào mà không kiểm tra làm sạch. Kẻ tấn công có thể chèn các chuỗi ký tự duyệt thư mục cha (`../` hoặc `%2e%2e%2f`): "
                "`content://com.victim.provider/files/..%2F..%2Fshared_prefs%2Fuser_credentials.xml`. "
                "Hàm `openFile()` sẽ ghép chuỗi thành: "
                "`/data/data/com.victim/files/../../shared_prefs/user_credentials.xml`, tương đương với đường dẫn `/data/data/com.victim/shared_prefs/user_credentials.xml`! "
                "Lúc này, kẻ tấn công có thể đọc được toàn bộ cơ sở dữ liệu, khóa riêng tư hoặc tệp tin cấu hình nội bộ của ứng dụng mà không cần quyền Root!"),
                ("Làm Sạch Đường Dẫn Bằng Canonical Path", "Để triệt tiêu hoàn toàn lỗ hổng Path Traversal, nhà phát triển bắt buộc phải giải quyết các đường dẫn tương đối thành đường dẫn chuẩn tuyệt đối bằng hàm `file.getCanonicalPath()`, sau đó kiểm tra xem đường dẫn tuyệt đối đó có bắt đầu bằng thư mục gốc hợp lệ hay không: "
                "`if (!targetFile.getCanonicalPath().startsWith(baseDir.getCanonicalPath())) throw SecurityException(\"Phát hiện tấn công Path Traversal!\");`.")
            ],
            "Kịch bản tấn công: Kẻ tấn công sử dụng lệnh `adb shell content read --uri content://com.victim.provider/..%2Fdatabases%2Fbanking.db > leaked_banking.db`. Toàn bộ cơ sở dữ liệu SQLite chứa lịch sử giao dịch và số dư của người dùng bị tải về máy kẻ tấn công chỉ trong một giây! Phòng thủ: Sử dụng Jetpack FileProvider chính thức của Android thay vì tự viết Content Provider chia sẻ tệp tùy biến. FileProvider có sẵn cơ chế bảo vệ chống Path Traversal nghiêm ngặt.",
            "Trong phần thực hành, chúng ta sẽ sử dụng công cụ content trong ADB để kiểm tra và truy vấn Content Provider mục tiêu:",
            ("bash", """# 1. Truy vấn toàn bộ bảng dữ liệu từ một Content Provider bị lộ lọt
adb shell content query --uri content://com.backend.androidsec.provider/users

# 2. Thử nghiệm đọc tệp tin qua Content URI
adb shell content read --uri content://com.backend.androidsec.provider/avatar.png > avatar.png

# 3. Chèn một bản ghi dữ liệu mới vào Provider công khai
adb shell content insert --uri content://com.backend.androidsec.provider/users --bind username:s:hacker --bind role:s:admin"""),
            ["Tuyệt đối không tự viết logic openFile() thủ công; luôn sử dụng androidx.core.content.FileProvider.", "Luôn kiểm tra File.getCanonicalPath() để chống lại kỹ thuật bypass đường dẫn tương đối."],
            ["Lỗ hổng Path Traversal trong Content Provider cho phép trích xuất các tệp tin hệ thống nội bộ.", "Ký tự ../ nếu không được lọc bỏ sẽ làm sai lệch phạm vi thư mục truy cập.", "androidx.core.content.FileProvider là giải pháp chuẩn mực để chia sẻ tệp an toàn."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Phương thức nào của lớp java.io.File bắt buộc phải sử dụng để giải quyết toàn bộ các ký tự đường dẫn tương đối (như ../) thành đường dẫn tuyệt đối chuẩn nhằm ngăn chặn Path Traversal?", "options": ["A. getCanonicalPath()", "B. getAbsolutePath()", "C. getPath()", "D. getName()"], "correct_index": 0, "explanation": "getCanonicalPath() chuẩn hóa đường dẫn, loại bỏ các ký tự ../ và symbolic links."},
                {"type": "FILL_BLANK", "question": "Lớp thành phần có sẵn trong thư viện AndroidX được Google khuyến nghị sử dụng thay thế việc tự viết Content Provider chia sẻ tệp là [_____] (FileProvider).", "blanks": [{"accepted_answers": ["FileProvider", "androidx.core.content.FileProvider"]}], "explanation": "FileProvider cấu hình an toàn qua tệp XML và chống 100% tấn công duyệt thư mục."},
                {"type": "MATCHING", "question": "Nối lệnh công cụ content trong ADB với chức năng:", "pairs": [{"left": "content query", "right": "Đọc và trích xuất dữ liệu dạng bảng từ Provider"}, {"left": "content read", "right": "Tải về luồng dữ liệu tệp nhị phân thông qua openFile()"}, {"left": "content insert", "right": "Chèn một bản ghi dữ liệu mới vào cơ sở dữ liệu của Provider"}] , "explanation": "Công cụ content trong ADB là vũ khí kiểm thử đắc lực cho Content Provider."},
                {"type": "FILL_BLANK", "question": "Chuỗi ký tự điều hướng thư mục cha được tin tặc sử dụng trong tấn công Directory Traversal là hai dấu chấm kèm dấu gạch chéo: [_____].", "blanks": [{"accepted_answers": ["../", "..\\", "..%2F", "%2e%2e%2f"]}], "explanation": "../ được sử dụng để lùi về thư mục cha phía trên."}
            ]
        ),
        (
            8,
            "Bài 3.8: Lỗ Hổng Lưu Trữ Dữ Liệu Cục Bộ Không An Toàn: SharedPreferences, SQLite & Bộ Nhớ Ngoài",
            "Nghiên cứu các vị trí lưu trữ dữ liệu trên Android, nguy cơ rò rỉ thông tin đăng nhập và kỹ thuật kiểm toán dữ liệu cục bộ.",
            [
                "Nắm vững các vị trí lưu trữ cục bộ: SharedPreferences, Internal Storage, SQLite Database và External Storage.",
                "Phân tích rủi ro khi lưu trữ mật khẩu, khóa bí mật hoặc token dạng văn bản rõ (Plaintext) trên đĩa.",
                "Hiểu cơ chế hoạt động của tính năng sao lưu tự động Android Auto Backup và rủi ro rò rỉ dữ liệu.",
                "Áp dụng thư viện Jetpack EncryptedSharedPreferences và SQLCipher để mã hóa dữ liệu nghỉ (Data at Rest)."
            ],
            [
                ("Các Vị Trí Lưu Trữ Dữ Liệu Trên Thiết Bị Android", "Hệ điều hành Android cung cấp nhiều giải pháp lưu trữ dữ liệu cục bộ phục vụ cho các mục đích khác nhau: "
                "1. `SharedPreferences`: Lưu trữ các cặp khóa-giá trị (Key-Value) dưới dạng tệp XML trong `/data/data/<package>/shared_prefs/`. "
                "2. `SQLite Database`: Lưu trữ dữ liệu quan hệ có cấu trúc trong `/data/data/<package>/databases/`. "
                "3. `Internal Storage Files`: Các tệp tin nhị phân trong `/data/data/<package>/files/`. "
                "4. `External Storage`: Bộ nhớ chia sẻ dùng chung tại `/sdcard/` hoặc `/storage/emulated/0/`."),
                ("Hiểm Họa Lưu Trữ Dữ Liệu Rõ (Insecure Data Storage)", "Rất nhiều lập trình viên mắc phải sai lầm chết người: lưu trữ mật khẩu tài khoản, số thẻ tín dụng, mã PIN, hoặc Access Token dạng chuỗi rõ (Plaintext) vào SharedPreferences hoặc SQLite. Lập trình viên thường ngây thơ tin rằng vì hộp cát Linux bảo vệ thư mục `/data/data/`, dữ liệu sẽ an toàn tuyệt đối. "
                "Tuy nhiên, dữ liệu này có thể bị đánh cắp dễ dàng qua nhiều kịch bản: 1. Thiết bị bị Root bởi người dùng hoặc phần mềm độc hại; 2. Tính năng `adb backup` được kích hoạt; 3. Dữ liệu sao lưu đám mây không mã hóa; 4. Thiết bị bị thất lạc hoặc kẻ tấn công trích xuất chip flash vật lý (Chip-off Forensics)."),
                ("Giải Pháp Mã Hóa Dữ Liệu Nghỉ (Data at Rest Encryption)", "Để bảo vệ dữ liệu cục bộ, mọi thông tin nhạy cảm bắt buộc phải được mã hóa trước khi ghi xuống đĩa: "
                "Đối với SharedPreferences: Sử dụng `EncryptedSharedPreferences` thuộc thư viện Jetpack Security, tự động mã hóa cả tên khóa (Key) bằng AES-SIV-256 và giá trị (Value) bằng AES-GCM-256. "
                "Đối với cơ sở dữ liệu: Sử dụng `SQLCipher` - tiện ích mở rộng mã hóa toàn bộ trang đĩa của SQLite sử dụng thuật toán AES-256 với cơ chế dẫn xuất khóa PBKDF2.")
            ],
            "Kịch bản tấn công: Kẻ tấn công cắm cáp USB vào điện thoại của nạn nhân khi màn hình đã mở khóa, gõ lệnh `adb backup -f backup.ab com.victim.bank`. Sau đó kẻ tấn công sử dụng công cụ `Android Backup Extractor` (abe.jar) để giải nén tệp `.ab` thành tệp `.tar`. Mở tệp `shared_prefs.xml`, toàn bộ tên đăng nhập, mật khẩu và token truy cập hiện ra nguyên vẹn! Phòng thủ: Đặt `android:allowBackup=\"false\"` trong manifest và mã hóa 100% dữ liệu nhạy cảm bằng EncryptedSharedPreferences.",
            "Trong phần thực hành, chúng ta sẽ kiểm tra tệp SharedPreferences bằng ADB và lập trình mã hóa an toàn với Jetpack Security:",
            ("kotlin", """// Khởi tạo EncryptedSharedPreferences an toàn
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val securePreferences = EncryptedSharedPreferences.create(
    context,
    "secret_vault",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)

// Ghi dữ liệu nhạy cảm (được mã hóa tự động)
securePreferences.edit().putString("AUTH_TOKEN", userJwtToken).apply()"""),
            ["Không bao giờ lưu trữ mật khẩu hoặc mã PIN dạng chuỗi rõ trong SharedPreferences.", "Luôn cấu hình tệp res/xml/backup_rules.xml để loại trừ các tệp dữ liệu nhạy cảm khỏi quá trình sao lưu tự động."],
            ["Lưu trữ dữ liệu dạng rõ là một trong những lỗ hổng phổ biến nhất trong OWASP Mobile Top 10.", "Hộp cát Linux không đủ để bảo vệ dữ liệu trước thiết bị đã Root hoặc adb backup.", "EncryptedSharedPreferences và SQLCipher là tiêu chuẩn mã hóa dữ liệu nghỉ bắt buộc."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Thư viện thành phần nào thuộc Android Jetpack Security được khuyến nghị sử dụng để lưu trữ các cặp khóa-giá trị nhạy cảm được mã hóa AES tự động thay thế cho SharedPreferences truyền thống?", "options": ["A. EncryptedSharedPreferences", "B. SecureStorageManager", "C. VaultPreferences", "D. CryptoPrefs"], "correct_index": 0, "explanation": "EncryptedSharedPreferences mã hóa cả key (AES-SIV) và value (AES-GCM) an toàn tuyệt đối."},
                {"type": "FILL_BLANK", "question": "Tiện ích mở rộng mã hóa toàn bộ cơ sở dữ liệu SQLite theo khối bằng thuật toán AES-256 phổ biến nhất trên Android có tên là [_____].", "blanks": [{"accepted_answers": ["SQLCipher", "sqlcipher"]}], "explanation": "SQLCipher cung cấp khả năng mã hóa trong suốt cho SQLite database."},
                {"type": "MATCHING", "question": "Nối công nghệ mã hóa với mục đích bảo vệ:", "pairs": [{"left": "MasterKey (Android Keystore)", "right": "Quản lý khóa chính được bảo vệ bởi phần cứng an toàn"}, {"left": "AES-256-GCM", "right": "Mã hóa giá trị dữ liệu đảm bảo cả tính bảo mật và toàn vẹn"}, {"left": "AES-256-SIV", "right": "Mã hóa tên khóa (Key) đảm bảo tính tất định và chống rò rỉ"}] , "explanation": "Jetpack Security kết hợp hài hòa giữa các chuẩn mã hóa tiên tiến nhất."},
                {"type": "FILL_BLANK", "question": "Định dạng tệp tin lưu trữ dữ liệu SharedPreferences mặc định trong thư mục /data/data/<package>/shared_prefs/ là tệp có đuôi mở rộng .[_____].", "blanks": [{"accepted_answers": ["xml", "XML"]}], "explanation": "SharedPreferences lưu trữ dữ liệu dưới dạng các thẻ XML phân cấp key-value."}
            ]
        ),
        (
            9,
            "Bài 3.9: Phân Tích Tĩnh Tự Động Với Mobile Security Framework (MobSF) & Đánh Giá Rủi Ro",
            "Nghiên cứu công cụ kiểm thử tự động MobSF, quét lỗ hổng mã nguồn, phân tích quyền hạn và xuất báo cáo kiểm toán bảo mật.",
            [
                "Hiểu kiến trúc và quy trình quét tự động của Mobile Security Framework (MobSF).",
                "Phân tích báo cáo đánh giá rủi ro an ninh (Security Scorecard / CVSS Score) do MobSF tạo ra.",
                "Nhận diện các cảnh báo tự động: cấu hình manifest lỏng lẻo, thuật toán mã hóa lỗi thời, API độc hại.",
                "Tích hợp MobSF vào đường ống CI/CD DevSecOps để quét mã độc tự động trước khi xuất bản."
            ],
            [
                ("Tổng Quan Về Mobile Security Framework (MobSF)", "Mobile Security Framework (MobSF) là một nền tảng kiểm thử an ninh ứng dụng di động tự động toàn diện hàng đầu thế giới, hỗ trợ cả hệ điều hành Android (APK, AAB, mã nguồn ZIP) và iOS (IPA). MobSF thực hiện cả phân tích tĩnh (Static Analysis) và phân tích động (Dynamic Analysis). "
                "Trong chế độ phân tích tĩnh, MobSF tự động giải nén APK, phân tích manifest, dịch ngược mã nguồn sang Java và Smali, sau đó áp dụng hàng trăm bộ luật kiểm tra (Rulesets) để phát hiện các lỗ hổng bảo mật phổ biến theo chuẩn OWASP Mobile Top 10 và MASTG."),
                ("Các Hạng Mục Đánh Giá Cốt Lõi Trong Báo Cáo MobSF", "Báo cáo phân tích tĩnh của MobSF cung cấp cái nhìn 360 độ về tình trạng an ninh của ứng dụng: "
                "1. Security Score: Điểm số an ninh tổng thể từ 0 đến 100 dựa trên số lượng lỗ hổng nghiêm trọng tìm thấy. "
                "2. Manifest Analysis: Đánh giá chi tiết các cờ `debuggable`, `allowBackup`, các Activity/Service bị exported không có quyền bảo vệ. "
                "3. Code Analysis: Quét mã nguồn tìm kiếm các thuật toán mã hóa yếu (MD5, SHA1, DES, ECB mode), tạo số ngẫu nhiên dự đoán được (`java.util.Random`), và các URL máy chủ không an toàn (`http://`). "
                "4. Hardcoded Secrets: Trích xuất các chuỗi khóa bí mật, token API, và địa chỉ email nhúng trong mã nguồn."),
                ("Tích Hợp DevSecOps & Tự Động Hóa Quét Lỗ Hổng", "Trong quy trình phát triển phần mềm hiện đại, việc kiểm thử thủ công sau khi ứng dụng đã hoàn thiện thường quá muộn màng và tốn kém. MobSF cung cấp hệ thống REST API hoàn chỉnh cho phép tích hợp trực tiếp vào quy trình CI/CD (GitHub Actions, GitLab CI). Mỗi khi lập trình viên tạo Pull Request hoặc tạo bản build mới, hệ thống CI sẽ tự động gửi APK lên MobSF để quét: nếu điểm an ninh dưới 80 hoặc phát hiện lỗ hổng nghiêm trọng (High Severity), tiến trình build sẽ tự động bị từ chối sáp nhập.")
            ],
            "Kịch bản tấn công: Chuyên gia đánh giá bảo mật (Penetration Tester) nhận tệp APK từ khách hàng. Thay vì phân tích thủ công từng tệp, chuyên gia tải APK lên MobSF. Chỉ sau 3 phút, MobSF phát hiện ứng dụng sử dụng thuật toán mã hóa `AES/ECB/PKCS5Padding` với khóa cố định nhúng trong mã, đồng thời có một Content Provider mở công khai bị dính lỗ hổng SQLi. Chuyên gia sử dụng thông tin này để xây dựng kịch bản khai thác PoC thực tế. Phòng thủ: Định kỳ tự quét ứng dụng bằng MobSF trong mỗi chu kỳ Sprint phát triển.",
            "Trong phần thực hành, chúng ta sẽ khởi chạy MobSF qua Docker và sử dụng REST API cURL để gửi tệp APK lên phân tích:",
            ("bash", """# 1. Khởi chạy MobSF container trên máy tính kiểm thử
docker run -it --rm -p 8000:8000 opensecurity/mobsf:latest

# 2. Tải tệp APK lên MobSF thông qua REST API (sử dụng API Key)
curl -F "file=@app-release.apk" http://localhost:8000/api/v1/upload -H "Authorization: <YOUR_MOBSF_API_KEY>"

# 3. Kích hoạt phân tích tĩnh tự động
curl -X POST --url http://localhost:8000/api/v1/scan -d "hash=<HASH_RETURNED>" -H "Authorization: <YOUR_MOBSF_API_KEY>"

# 4. Tải báo cáo kiểm toán bảo mật định dạng PDF / JSON
curl -X POST --url http://localhost:8000/api/v1/report_json -d "hash=<HASH_RETURNED>" -H "Authorization: <YOUR_MOBSF_API_KEY>" > report.json"""),
            ["Luôn kiểm tra kỹ các cảnh báo false-positive (dương tính giả) trong báo cáo MobSF trước khi đưa ra kết luận.", "Bảo mật khóa API của MobSF trong hệ thống CI/CD."],
            ["MobSF là công cụ quét an ninh tự động hàng đầu cho ứng dụng di động Android và iOS.", "Báo cáo phân tích tĩnh chỉ ra chính xác dòng mã có nguy cơ bảo mật và cấu hình lỗi.", "Tích hợp MobSF vào CI/CD hiện thực hóa quy trình DevSecOps chuyển dịch an ninh về phía sớm (Shift-Left Security)."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Khung kiểm thử an ninh ứng dụng di động tự động mã nguồn mở phổ biến nhất hỗ trợ cả phân tích tĩnh và động cho Android/iOS có tên viết tắt là gì?", "options": ["A. MobSF", "B. Metasploit", "C. Nessus", "D. BurpSuite"], "correct_index": 0, "explanation": "MobSF (Mobile Security Framework) là tiêu chuẩn vàng cho kiểm thử di động tự động."},
                {"type": "FILL_BLANK", "question": "Khái niệm trong kỹ nghệ phần mềm chỉ việc đưa các bước kiểm tra an ninh bảo mật vào các giai đoạn sớm nhất của chu trình phát triển được gọi là Shift-[_____] Security.", "blanks": [{"accepted_answers": ["Left", "left", "Shift-Left"]}], "explanation": "Shift-Left Security giúp phát hiện và vá lỗi ngay trong quá trình lập trình."},
                {"type": "MATCHING", "question": "Nối hạng mục phân tích của MobSF với nội dung kiểm tra:", "pairs": [{"left": "Manifest Analysis", "right": "Đánh giá các cờ exported, permissions và thuộc tính bảo mật APK"}, {"left": "Code Analysis", "right": "Quét tìm thuật toán mã hóa yếu, hàm rủi ro và lỗi logic"}, {"left": "Hardcoded Secrets", "right": "Trích xuất API keys, token truy cập và mật khẩu nhúng trong code"}] , "explanation": "Phân tích đa diện giúp nhà phát triển khắc phục triệt để mọi bề mặt tấn công."},
                {"type": "FILL_BLANK", "question": "Chế độ mã hóa khối AES không an toàn bị MobSF cảnh báo nghiêm trọng do không sử dụng vector khởi tạo (IV) và để lộ mẫu dữ liệu là AES/[_____]/PKCS5Padding.", "blanks": [{"accepted_answers": ["ECB", "ecb"]}], "explanation": "ECB (Electronic Codebook) mode tuyệt đối bị cấm sử dụng vì để lộ cấu trúc dữ liệu."}
            ]
        ),
        (
            10,
            "Bài 3.10: Phát Hiện Khóa Bí Mật Ẩn (Hardcoded Secrets, API Keys & Salts) Bằng Regex & TruffleHog",
            "Nghiên cứu kỹ thuật săn lùng các khóa bảo mật bị bỏ quên trong mã nguồn, công thức Entropy và công cụ TruffleHog.",
            [
                "Hiểu nguy cơ thảm họa an ninh khi các khóa bí mật (Secret Keys) bị lộ lọt trong mã nguồn client.",
                "Làm chủ các mẫu biểu thức chính quy (Regex Patterns) để tìm kiếm API keys của Google, AWS, Firebase, Stripe.",
                "Hiểu nguyên lý Shannon Entropy trong việc phát hiện các chuỗi ngẫu nhiên có độ ngẫu độ cao.",
                "Sử dụng công cụ TruffleHog và GitGuardian để rà soát kho lưu trữ mã nguồn tự động."
            ],
            [
                ("Hiểm Họa Từ Các Khóa Bí Mật Nhúng Cứng (Hardcoded Secrets)", "Trong quá trình lập trình, để nhanh chóng thử nghiệm các tính năng, lập trình viên thường khai báo trực tiếp các khóa API, Secret Token, hoặc mật khẩu cơ sở dữ liệu ngay trong mã nguồn: "
                "`val AWS_SECRET_KEY = \"AKIAIOSFODNN7EXAMPLE\"`. "
                "Sau đó, mã nguồn này được biên dịch vào tệp APK và phát hành công khai. Vì APK có thể được dịch ngược dễ dàng bởi bất kỳ ai chỉ trong vài giây, toàn bộ các khóa bí mật này sẽ bị phơi bày. Kẻ tấn công có thể sử dụng các khóa này để truy cập thẳng vào hạ tầng đám mây của doanh nghiệp, đánh cắp cơ sở dữ liệu hàng triệu khách hàng hoặc tiêu tốn hàng chục ngàn USD chi phí điện toán đám mây."),
                ("Kỹ Thuật Tìm Kiếm Bằng Regex & Dấu Hiệu Đặc Trưng", "Nhiều nhà cung cấp dịch vụ đám mây thiết kế định dạng khóa của họ với các tiền tố (Prefix) đặc thù. Chuyên gia pentest sử dụng các biểu thức chính quy (Regex) để quét toàn bộ thư mục mã nguồn sau khi dịch ngược: "
                "Google API Key: `AIza[0-9A-Za-z-_]{35}`. "
                "AWS Access Key ID: `AKIA[0-9A-Z]{16}`. "
                "Firebase Database URL: `https://[a-z0-9-]+\\.firebaseio\\.com`. "
                "Stripe Live Secret Key: `sk_live_[0-9a-zA-Z]{24}`."),
                ("Thuật Toán Shannon Entropy & Công Cụ TruffleHog", "Các khóa mật mã (như khóa AES 256-bit hoặc RSA Private Key) thường là các chuỗi ngẫu nhiên không có tiền tố cố định. Để phát hiện chúng, các công cụ chuyên nghiệp như `TruffleHog` sử dụng thuật toán tính toán Độ hỗn loạn thông tin (Shannon Entropy). "
                "Một chuỗi văn bản thông thường (như tiếng Anh hay tiếng Việt) có độ entropy thấp (dưới 3.0), trong khi một chuỗi mật mã ngẫu nhiên cao (Base64 hoặc Hex) sẽ có độ entropy rất cao (trên 4.5). Bằng cách quét entropy, TruffleHog có thể phát hiện chính xác các khóa bí mật ngay cả khi chúng được đặt tên biến ngụy trang khéo léo.")
            ],
            "Kịch bản tấn công: Kẻ tấn công dịch ngược APK của một ứng dụng gọi xe, tìm thấy khóa bí mật Firebase Secret Token. Kẻ tấn công sử dụng công cụ cURL gửi yêu cầu trực tiếp tới `https://app-database.firebaseio.com/.json?auth=<SECRET_TOKEN>`. Vì khóa này có quyền Root Database, toàn bộ thông tin vị trí tài xế, số điện thoại khách hàng và doanh thu bị trích xuất sạch sẽ. Phòng thủ: Xóa bỏ 100% các khóa bí mật khỏi ứng dụng client. Áp dụng kiến trúc Proxy Backend hoặc sử dụng Firebase App Check.",
            "Trong phần thực hành, chúng ta sẽ sử dụng grep và TruffleHog để quét tìm các khóa bí mật trong thư mục mã nguồn dịch ngược:",
            ("bash", """# 1. Tìm kiếm các khóa Google API Key bằng biểu thức chính quy Regex
grep -E -r "AIza[0-9A-Za-z-_]{35}" decoded_app/

# 2. Tìm kiếm các khóa AWS Access Key
grep -E -r "AKIA[0-9A-Z]{16}" decoded_app/

# 3. Sử dụng công cụ TruffleHog quét toàn bộ thư mục bằng thuật toán Entropy
trufflehog filesystem decoded_app/ --json > secrets_found.json"""),
            ["Không bao giờ commit tệp google-services.json hoặc các tệp cấu hình chứa secret vào Git công khai.", "Luôn giới hạn quyền hạn (Scope Restriction) cho các khóa API công khai trên bảng điều khiển của nhà cung cấp."],
            ["Hardcoded Secrets trong APK là nguyên nhân dẫn đến các vụ rò rỉ dữ liệu đám mây nghiêm trọng nhất.", "Biểu thức chính quy Regex nhận diện các khóa API có định dạng cấu trúc chuẩn.", "Thuật toán Shannon Entropy phát hiện các chuỗi khóa mật mã có độ ngẫu nhiên cao."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tiền tố (Prefix) đặc trưng luôn bắt đầu bằng 4 ký tự nào trong định dạng mã khóa định danh truy cập AWS Access Key ID của Amazon Web Services?", "options": ["A. AKIA", "B. AIza", "C. sk_live", "D. Bearer"], "correct_index": 0, "explanation": "Các khóa AWS Access Key ID tiêu chuẩn luôn bắt đầu bằng tiền tố AKIA hoặc ASIA."},
                {"type": "FILL_BLANK", "question": "Đại lượng đo lường mức độ hỗn loạn và tính ngẫu nhiên của một chuỗi ký tự được sử dụng để phát hiện khóa mã hóa có tên là Shannon [_____].", "blanks": [{"accepted_answers": ["Entropy", "entropy"]}], "explanation": "Shannon Entropy đo lường tính ngẫu nhiên của chuỗi dữ liệu nhị phân."},
                {"type": "MATCHING", "question": "Nối nhà cung cấp dịch vụ với định dạng khóa nhận diện:", "pairs": [{"left": "Google API Key", "right": "Bắt đầu bằng tiền tố AIza kèm 35 ký tự ngẫu nhiên"}, {"left": "AWS Access Key", "right": "Bắt đầu bằng tiền tố AKIA kèm 16 ký tự in hoa"}, {"left": "Stripe Live Secret", "right": "Bắt đầu bằng tiền tố sk_live_"}] , "explanation": "Nắm vững định dạng khóa giúp xây dựng bộ quy tắc lọc rò rỉ hiệu quả."},
                {"type": "FILL_BLANK", "question": "Công cụ mã nguồn mở phổ biến dùng để quét và phát hiện các khóa bí mật nhúng trong thư mục và lịch sử Git là Truffle[_____].", "blanks": [{"accepted_answers": ["Hog", "hog", "TruffleHog"]}], "explanation": "TruffleHog là công cụ tiêu chuẩn quét secret dựa trên regex và entropy."}
            ]
        ),
        (
            11,
            "Bài 3.11: Phân Tích Lỗ Hổng Deep Link & App Links: Chiếm Đoạt Phiên & Khai Thác URL Tùy Biến",
            "Nghiên cứu cơ chế liên kết sâu Custom Scheme và Android App Links, tấn công URL Spoofing và đánh cắp mã OTP OAuth.",
            [
                "Hiểu sự khác biệt bản chất giữa Custom URL Schemes (`myapp://`) và Android App Links (`https://`).",
                "Phân tích lỗ hổng chiếm đoạt liên kết sâu (Deep Link Hijacking) khi nhiều ứng dụng cùng đăng ký chung Scheme.",
                "Cơ chế xác thực tính sở hữu tên miền qua Digital Asset Links (`assetlinks.json`).",
                "Khai thác và phòng thủ kịch bản đánh cắp mã Authorization Code trong luồng đăng nhập OAuth 2.0."
            ],
            [
                ("Bản Chất Của Liên Kết Sâu (Deep Linking)", "Deep Linking là kỹ thuật cho phép người dùng nhấp vào một đường liên kết trên trang web hoặc tin nhắn để mở trực tiếp một màn hình cụ thể bên trong ứng dụng Android đã cài đặt. Có 2 cơ chế chính: "
                "1. Custom URL Scheme: Sử dụng scheme tự đặt, ví dụ: `mybank://transfer?to=123&amount=1000`. "
                "2. Android App Links (từ Android 6.0): Sử dụng scheme chuẩn `https://`, ví dụ: `https://mybank.com/transfer`. "
                "Cả hai cơ chế này đều được khai báo bên trong thẻ `<intent-filter>` của Activity với thẻ `<data>`."),
                ("Hiểm Họa Chiếm Đoạt Custom Scheme (Deep Link Hijacking)", "Điểm yếu chí mạng của Custom Scheme (`mybank://`) là hệ điều hành Android hoàn toàn KHÔNG có cơ chế kiểm tra tính sở hữu duy nhất của scheme! Bất kỳ ứng dụng nào cũng có thể khai báo cùng một scheme `mybank://` trong manifest của nó. "
                "Khi người dùng nhấp vào liên kết, Android sẽ hiển thị hộp thoại hỏi người dùng muốn mở bằng ứng dụng nào (Disambiguation Dialog). Nếu ứng dụng độc hại đánh lừa được người dùng, toàn bộ tham số trong URL (bao gồm mã xác thực OAuth Authorization Code hoặc mã Token nhạy cảm) sẽ được chuyển thẳng vào tay kẻ tấn công!"),
                ("Giải Pháp Bảo Mật Toàn Diện Với Android App Links", "Để triệt tiêu hoàn toàn rủi ro chiếm đoạt, Android giới thiệu Android App Links với thuộc tính `android:autoVerify=\"true\"`. "
                "Khi ứng dụng được cài đặt, hệ thống sẽ tự động gửi yêu cầu HTTPS đến máy chủ tên miền chính thống: `https://mybank.com/.well-known/assetlinks.json`. "
                "Tệp `assetlinks.json` trên máy chủ chứa mã băm SHA-256 của chữ ký số của ứng dụng hợp pháp. Chỉ khi chữ ký số trùng khớp hoàn toàn, hệ thống mới cấp quyền độc quyền mở liên kết `https://mybank.com/*` mà không hiển thị bất kỳ hộp thoại lựa chọn nào.")
            ],
            "Kịch bản tấn công: Đánh cắp mã OTP trong luồng đăng nhập OAuth PKCE. Ứng dụng ngân hàng cấu hình redirect_uri là `mybank://oauth/callback`. Kẻ tấn công tạo một ứng dụng độc hại có cùng scheme. Khi người dùng đăng nhập thành công trên trình duyệt, trình duyệt kích hoạt chuyển hướng về URL: `mybank://oauth/callback?code=AUTH_SECRET_CODE`. Ứng dụng độc hại cướp Intent và gửi mã về máy chủ tin tặc để đổi lấy Access Token! Phòng thủ: Bắt buộc chuyển đổi toàn bộ luồng OAuth sang Android App Links xác thực bằng `assetlinks.json`.",
            "Trong phần thực hành, chúng ta sẽ sử dụng lệnh am start để kích hoạt và kiểm thử Deep Link mục tiêu:",
            ("bash", """# 1. Gửi một Deep Link kích hoạt màn hình ứng dụng qua ADB
adb shell am start -a android.intent.action.VIEW -d "mybank://payment?amount=1000000&recipient=attacker"

# 2. Kiểm tra trạng thái xác minh App Links của tên miền
adb shell pm get-app-links com.backend.androidsec

# 3. Tra cứu tệp assetlinks.json công khai của tên miền chính thống
curl -s https://mybank.com/.well-known/assetlinks.json | jq . """),
            ["Tuyệt đối không sử dụng Custom URL Schemes cho các luồng xác thực nhạy cảm hoặc giao dịch tài chính.", "Luôn xác minh tệp assetlinks.json trả về mã HTTP 200 và Content-Type là application/json."],
            ["Custom URL Schemes không có bảo vệ sở hữu và dễ dàng bị chiếm đoạt (Deep Link Hijacking).", "Android App Links sử dụng assetlinks.json để chứng thực quyền sở hữu tên miền duy nhất.", "Bắt buộc sử dụng App Links cho mọi luồng đăng nhập OAuth 2.0 và thanh toán trực tuyến."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Thuộc tính nào trong thẻ <intent-filter> của AndroidManifest.xml bắt buộc phải thiết lập bằng 'true' để hệ điều hành tự động xác thực tên miền thông qua tệp assetlinks.json?", "options": ["A. android:autoVerify", "B. android:exported", "C. android:verified", "D. android:secureLink"], "correct_index": 0, "explanation": "android:autoVerify=\"true\" kích hoạt quy trình xác thực App Links của Android."},
                {"type": "FILL_BLANK", "question": "Đường dẫn chuẩn trên máy chủ web lưu trữ tệp cấu hình xác thực quyền sở hữu ứng dụng Android là /.well-known/assetlinks.[_____].", "blanks": [{"accepted_answers": ["json", "JSON"]}], "explanation": "assetlinks.json chứa thông tin package name và SHA-256 fingerprint của chứng chỉ ứng dụng."},
                {"type": "MATCHING", "question": "Nối loại Deep Link với đặc tính bảo mật:", "pairs": [{"left": "Custom Scheme (myapp://)", "right": "Không có kiểm tra sở hữu, dễ bị giả mạo và chiếm đoạt Intent"}, {"left": "Android App Links (https://)", "right": "Chứng thực tên miền qua assetlinks.json, độc quyền mở link"}, {"left": "OAuth PKCE", "right": "Cơ chế bảo vệ luồng đăng nhập chống chặn bắt Authorization Code"}] , "explanation": "Lựa chọn đúng công nghệ liên kết sâu bảo vệ người dùng khỏi tấn công lừa đảo."},
                {"type": "FILL_BLANK", "question": "Cơ chế tấn công trong đó một ứng dụng độc hại đăng ký cùng Custom Scheme để đánh cắp tham số chuyển hướng được gọi là Deep Link [_____] (Chiếm đoạt).", "blanks": [{"accepted_answers": ["Hijacking", "hijacking", "chiếm đoạt"]}], "explanation": "Deep Link Hijacking đe dọa các luồng xác thực không sử dụng App Links."}
            ]
        ),
        (
            12,
            "Bài 3.12: An Ninh Khung Giao Diện Nhúng WebView: Lỗ Hổng Cross-Site Scripting (XSS) & Giao Diện Javascript",
            "Nghiên cứu kiến trúc nhúng trình duyệt WebView, nguy cơ thực thi mã từ xa qua addJavascriptInterface và phòng thủ XSS.",
            [
                "Nắm vững nguyên lý hoạt động của thành phần Android WebView và các thiết lập WebSettings nguy hiểm.",
                "Phân tích lỗ hổng RCE kinh điển CVE-2012-6636 qua hàm `addJavascriptInterface()` trên Android < 4.2.",
                "Hiểu cơ chế bảo vệ của annotation `@JavascriptInterface` trên các phiên bản Android hiện đại.",
                "Cấu hình an toàn: vô hiệu hóa nạp tệp cục bộ (`setAllowFileAccess`), bật Safe Browsing và lọc URL."
            ],
            [
                ("Thành Phần Nhúng Trình Duyệt WebView", "WebView là một thành phần giao diện đặc biệt của Android cho phép ứng dụng nhúng một trình duyệt web hoàn chỉnh (dựa trên engine Chromium/Blink) trực tiếp vào Activity. WebView được sử dụng rộng rãi để hiển thị các trang điều khoản dịch vụ, cổng thanh toán hoặc xây dựng các ứng dụng lai (Hybrid Apps như Cordova, Capacitor). "
                "Mặc dù tiện lợi, WebView là một trong những thành phần có bề mặt tấn công phức tạp nhất vì nó là cầu nối trung gian giữa môi trường Web không đáng tin cậy và các API native đầy quyền lực của hệ điều hành."),
                ("Hiểm Họa Thực Thi Mã Từ Xa Qua addJavascriptInterface()", "Để mã JavaScript trong trang web có thể gọi các hàm Java của ứng dụng, nhà phát triển sử dụng phương thức: "
                "`webView.addJavascriptInterface(new WebAppInterface(), \"AndroidBridge\")`. "
                "Trên các phiên bản Android trước 4.2, do cơ chế Java Reflection không được kiểm soát, mã JavaScript độc hại trong trang web có thể lợi dụng đối tượng cầu nối này để truy cập vào lớp `java.lang.Runtime` và thực thi các lệnh shell hệ thống tùy ý (Remote Code Execution - RCE)! "
                "Từ Android 4.2 (API 17), Google bổ sung annotation `@JavascriptInterface`: chỉ các hàm nào được gắn annotation này một cách tường minh mới được phép gọi từ JavaScript."),
                ("Các Cấu Hình Nguy Hiểm Cần Loại Bỏ", "Nhiều ứng dụng vô tình bật các cấu hình lỏng lẻo: "
                "`webSettings.setAllowFileAccess(true)`: cho phép WebView đọc các tệp cục bộ trên thiết bị qua scheme `file://`. "
                "`webSettings.setAllowFileAccessFromFileURLs(true)` và `setAllowUniversalAccessFromFileURLs(true)`: cho phép mã JavaScript trong tệp HTML cục bộ bỏ qua chính sách cùng nguồn gốc (Same-Origin Policy - SOP) để đánh cắp toàn bộ tệp tin trong thư mục `/data/data/`!")
            ],
            "Kịch bản tấn công: Kẻ tấn công tìm thấy lỗ hổng XSS trên website hiển thị trong WebView của ứng dụng. Kẻ tấn công bơm mã JavaScript độc hại gọi hàm cầu nối: `AndroidBridge.getUserSessionToken()`. Mã JavaScript trích xuất token phiên của người dùng và gửi về máy chủ tin tặc. Phòng thủ: Luôn kiểm tra tên miền (Domain Whitelisting) trong callback `shouldOverrideUrlLoading()`. Chỉ nạp các trang web tin cậy nội bộ và vô hiệu hóa hoàn toàn `setAllowFileAccess(false)`.",
            "Trong phần thực hành, chúng ta sẽ cấu hình một WebView an toàn theo tiêu chuẩn bảo mật hiện đại:",
            ("kotlin", """// Cấu hình WebView bảo mật chuẩn
webView.settings.apply {
    javaScriptEnabled = true // Chỉ bật nếu thực sự cần thiết
    allowFileAccess = false  // Vô hiệu hóa truy cập tệp tin cục bộ
    allowContentAccess = false
    setSupportZoom(false)
}

webView.webViewClient = object : WebViewClient() {
    override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
        val url = request?.url.toString()
        // Kiểm tra Whitelist tên miền nghiêm ngặt
        return if (url.startsWith("https://trusted.mybank.com/")) {
            false // Cho phép nạp trong WebView
        } else {
            // Chuyển hướng các liên kết ngoài ra trình duyệt hệ thống độc lập
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            context.startActivity(intent)
            true
        }
    }
}"""),
            ["Tuyệt đối không bao giờ bật setAllowUniversalAccessFromFileURLs(true).", "Luôn gắn annotation @JavascriptInterface cho các hàm cầu nối và giới hạn tối đa quyền hạn của chúng."],
            ["WebView là cầu nối rủi ro cao giữa môi trường Web và các API native của hệ điều hành.", "addJavascriptInterface từng là lỗ hổng RCE kinh điển nếu thiếu annotation bảo vệ.", "Luôn kiểm tra Domain Whitelist và vô hiệu hóa quyền đọc tệp cục bộ file://."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Annotation nào trong mã nguồn Java/Kotlin bắt buộc phải gắn trên các phương thức cầu nối từ Android 4.2 trở lên để cho phép JavaScript gọi hàm một cách an toàn?", "options": ["A. @JavascriptInterface", "B. @WebMethod", "C. @ExportedFunction", "D. @JsBridge"], "correct_index": 0, "explanation": "@JavascriptInterface đánh dấu tường minh các hàm được phép gọi từ JavaScript engine."},
                {"type": "FILL_BLANK", "question": "Phương thức cài đặt của WebSettings dùng để vô hiệu hóa hoàn toàn khả năng đọc các tệp cục bộ thông qua scheme file:// là setAllowFile[_____](false).", "blanks": [{"accepted_answers": ["Access", "access", "Access(false)"]}], "explanation": "setAllowFileAccess(false) chặn đứng các cuộc tấn công đánh cắp tệp tin nội bộ qua WebView."},
                {"type": "MATCHING", "question": "Nối cấu hình WebView với mức độ rủi ro:", "pairs": [{"left": "setAllowUniversalAccessFromFileURLs(true)", "right": "Cực kỳ nguy hiểm, cho phép JavaScript bỏ qua SOP đọc mọi tệp tin"}, {"left": "shouldOverrideUrlLoading Whitelist", "right": "Bảo mật cao, chỉ cho phép nạp các tên miền tin cậy được phê duyệt"}, {"left": "setJavaScriptEnabled(false)", "right": "An toàn tối đa cho các trang chỉ hiển thị văn bản tĩnh"}] , "explanation": "Cấu hình WebSettings quyết định trực tiếp khả năng phòng thủ của WebView."},
                {"type": "FILL_BLANK", "question": "Chính sách bảo mật cơ bản của trình duyệt web ngăn chặn mã script từ nguồn này truy cập tài nguyên của nguồn khác có tên viết tắt là [_____] (Same-Origin Policy).", "blanks": [{"accepted_answers": ["SOP", "sop"]}], "explanation": "Same-Origin Policy (SOP) là nền tảng bảo mật của World Wide Web."}
            ]
        ),
        (
            13,
            "Bài 3.13: Kiểm Thử Lỗ Hổng Nối Tệp Gói Cài Đặt (Zip Slip Vulnerability) Khi Giải Nén Dữ Liệu Tải Về",
            "Nghiên cứu lỗ hổng giải nén tệp tin độc hại Zip Slip, kỹ thuật ghi đè tệp hệ thống và phương pháp phòng thủ đường dẫn.",
            [
                "Hiểu bản chất của lỗ hổng Zip Slip (Path Traversal in Archive Extraction).",
                "Phân tích cách thức kẻ tấn công chế tạo tệp nén ZIP độc hại chứa các đường dẫn tương đối `../../`.",
                "Hậu quả khi tệp độc hại ghi đè lên các thư viện native (.so) hoặc tệp cơ sở dữ liệu nội bộ.",
                "Lập trình thuật toán giải nén an toàn với kiểm tra Canonical Path nghiêm ngặt."
            ],
            [
                ("Bản Chất Của Lỗ Hổng Zip Slip", "Rất nhiều ứng dụng Android có tính năng tải về một tệp nén ZIP từ máy chủ (như gói tài nguyên giao diện, dữ liệu bản đồ ngoại tuyến hoặc bản cập nhật nội dung) và tiến hành giải nén tự động vào bộ nhớ trong của ứng dụng. "
                "Lỗ hổng Zip Slip xuất hiện khi ứng dụng đọc thuộc tính `ZipEntry.getName()` từ tệp nén và trực tiếp nối chuỗi với thư mục đích để tạo tệp xuất ra: "
                "`File destinationFile = new File(targetDir, zipEntry.getName());`. "
                "Nếu tệp ZIP được chế tạo bởi kẻ tấn công, trường tên tệp bên trong có thể chứa các ký tự duyệt đường dẫn: `../../../../lib/arm64/libcore.so`!"),
                ("Hậu Quả Khi Bị Khai Thác Zip Slip", "Khi quá trình giải nén diễn ra, thay vì ghi tệp vào thư mục đích quy định, luồng ghi sẽ nhảy ngược ra khỏi thư mục đích và ghi đè trực tiếp lên bất kỳ tệp tin nào trong hộp cát của ứng dụng mà tiến trình có quyền ghi. "
                "Kẻ tấn công có thể: "
                "1. Ghi đè tệp SharedPreferences hoặc cơ sở dữ liệu SQLite để thay đổi trạng thái đăng nhập. "
                "2. Ghi đè lên một tệp thư viện liên kết động native `.so` trong thư mục `lib/` hoặc tệp bytecode `.dex`: khi ứng dụng khởi chạy lần tiếp theo, mã độc do kẻ tấn công chèn vào thư viện sẽ được thực thi với toàn bộ quyền hạn của ứng dụng (Remote Code Execution - RCE)!"),
                ("Thuật Toán Giải Nén An Toàn Chống Zip Slip", "Để phòng thủ triệt để, lập trình viên bắt buộc phải kiểm tra đường dẫn tuyệt đối của tệp đích trước khi thực hiện ghi dữ liệu: "
                "```kotlin\nval destFile = File(destinationDir, zipEntry.name)\nval canonicalPath = destFile.canonicalPath\nif (!canonicalPath.startsWith(destinationDir.canonicalPath + File.separator)) {\n    throw SecurityException(\"Phát hiện tệp tin Zip Slip độc hại: \" + zipEntry.name)\n}\n```\n"
                "Nếu phát hiện đường dẫn tệp vượt ra ngoài thư mục đích, ứng dụng phải lập tức hủy bỏ quá trình giải nén và xóa bỏ toàn bộ tệp tạm thời.")
            ],
            "Kịch bản tấn công: Kẻ tấn công thực hiện tấn công Man-in-the-Middle (MitM) hoặc chiếm đoạt máy chủ Content Delivery Network (CDN) phân phối gói tài nguyên game/ứng dụng. Kẻ tấn công thay thế tệp `assets.zip` bằng một tệp zip độc hại chứa đường dẫn ghi đè lên tệp `classes.dex`. Khi nạn nhân mở ứng dụng, ứng dụng tự động tải bản zip, giải nén ghi đè mã thực thi và bị chiếm quyền điều khiển hoàn toàn! Phòng thủ: Luôn kiểm tra mã băm SHA-256 của tệp ZIP trước khi giải nén và áp dụng thuật toán kiểm tra Canonical Path.",
            "Trong phần thực hành, chúng ta sẽ lập trình một hàm giải nén an toàn và thử nghiệm quét tệp ZIP độc hại:",
            ("kotlin", """// Hàm giải nén ZIP an toàn chống Zip Slip
fun unzipSafely(zipFile: File, targetDirectory: File) {
    val canonicalTargetDir = targetDirectory.canonicalPath
    ZipInputStream(BufferedInputStream(FileInputStream(zipFile))).use { zis ->
        var entry = zis.nextEntry
        while (entry != null) {
            val newFile = File(targetDirectory, entry.name)
            val canonicalDestPath = newFile.canonicalPath
            
            // Chốt chặn kiểm tra Zip Slip bắt buộc
            if (!canonicalDestPath.startsWith(canonicalTargetDir + File.separator)) {
                throw SecurityException("Cảnh báo an ninh: Tệp ZipEntry vi phạm đường dẫn: ${entry.name}")
            }
            
            if (entry.isDirectory) {
                newFile.mkdirs()
            } else {
                newFile.parentFile?.mkdirs()
                FileOutputStream(newFile).use { fos -> zis.copyTo(fos) }
            }
            zis.closeEntry()
            entry = zis.nextEntry
        }
    }
}"""),
            ["Luôn kiểm tra canonicalDestPath.startsWith(canonicalTargetDir + File.separator) cho MỌI ZipEntry.", "Xác thực chữ ký số hoặc mã băm SHA-256 của gói tệp nén trước khi cho phép giải nén."],
            ["Zip Slip là lỗ hổng duyệt thư mục nghiêm trọng xảy ra trong quá trình giải nén tệp tin.", "Kẻ tấn công có thể ghi đè thư viện native hoặc bytecode để thực thi mã tùy ý (RCE).", "Kiểm tra Canonical Path là tuyến phòng thủ bắt buộc khi xử lý các định dạng lưu trữ (ZIP, TAR)."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Hậu quả an ninh nghiêm trọng nhất có thể xảy ra khi một ứng dụng Android bị khai thác thành công lỗ hổng Zip Slip trong quá trình giải nén là gì?", "options": ["A. Ghi đè thư viện native (.so) hoặc bytecode dẫn đến thực thi mã tùy ý (RCE)", "B. Làm tăng đột biến kích thước màn hình", "C. Tự động bật chế độ máy bay", "D. Giảm độ sáng màn hình"], "correct_index": 0, "explanation": "Zip Slip cho phép ghi đè các tệp thực thi nội bộ, dẫn đến chiếm quyền điều khiển ứng dụng."},
                {"type": "FILL_BLANK", "question": "Tên gọi quốc tế của lỗ hổng bảo mật liên quan đến việc duyệt đường dẫn tùy ý khi giải nén các tệp nén là Zip [_____].", "blanks": [{"accepted_answers": ["Slip", "slip", "Zip Slip"]}], "explanation": "Zip Slip được phát hiện rộng rãi bởi Snyk và ảnh hưởng đến hàng ngàn thư viện giải nén."},
                {"type": "MATCHING", "question": "Nối các thành phần trong thuật toán phòng thủ Zip Slip:", "pairs": [{"left": "File.canonicalPath", "right": "Chuẩn hóa và loại bỏ toàn bộ các ký tự ../ trong đường dẫn"}, {"left": "startsWith(targetDir)", "right": "Đảm bảo tệp đích bắt buộc phải nằm bên trong thư mục chỉ định"}, {"left": "SHA-256 Checksum", "right": "Xác thực tính toàn vẹn của tệp ZIP trước khi giải nén"}] , "explanation": "Bộ ba giải pháp bảo đảm an toàn tuyệt đối cho quy trình giải nén dữ liệu."},
                {"type": "FILL_BLANK", "question": "Hàm của đối tượng java.util.zip.ZipEntry dùng để lấy tên và đường dẫn của tệp tin con bên trong kho nén là get[_____]().", "blanks": [{"accepted_answers": ["Name", "name", "Name()"]}], "explanation": "getName() trả về chuỗi đường dẫn do người tạo tệp nén quy định (có thể chứa ../ độc hại)."}
            ]
        )
    ]

    for spec in ch3_specs:
        pos, title, summary, objs, theory, attack_def, lab_text, code_snp, pitfalls, summaries, quiz = spec
        vid_idx = (pos - 1) % len(VIDEO_CACHE)
        vurl = VIDEO_CACHE[vid_idx]["url"]

        md_content = generate_lesson_markdown(
            lesson_num=f"3.{pos}",
            title=title,
            objective_points=objs,
            theory_sections=theory,
            attack_defense_section=attack_def,
            lab_instructions=lab_text,
            code_snippet=code_snp,
            pitfalls=pitfalls,
            summary_points=summaries,
            video_url=vurl,
            quiz_items=quiz,
        )

        validate_lesson_data({
            "title": title,
            "markdown_content": md_content,
            "video_url": vurl
        })

        lessons.append({
            "position": pos,
            "title": title,
            "summary": summary,
            "duration_minutes": 45,
            "video_url": vurl,
            "markdown_content": md_content,
        })

    return lessons
