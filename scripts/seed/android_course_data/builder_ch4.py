# -*- coding: utf-8 -*-
"""Builder for Chapter 4: Phân Tích Động, Bắt Gói Mạng & Vượt Rào Bảo Mật (12 lessons).
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
    VIDEO_CACHE = json.load(f)["ch4"]


def get_chapter_4_lessons() -> list[dict[str, Any]]:
    lessons = []

    ch4_specs = [
        (
            1,
            "Bài 4.1: Thiết Lập Môi Trường Phân Tích Động: Android Studio AVD, Genymotion, Magisk & ADB",
            "Nghiên cứu kiến trúc phòng lab phân tích động chuyên nghiệp, cấu hình máy ảo Android x86/ARM và kỹ thuật Root máy.",
            [
                "Nắm vững sự khác biệt giữa thiết bị vật lý thật và máy ảo giả lập (AVD, Genymotion, Corellium) trong pentesting.",
                "Lựa chọn phiên bản Android và kiến trúc CPU tối ưu cho phân tích bảo mật (Google APIs vs Google Play system images).",
                "Hiểu cơ chế Root không can thiệp phân vùng hệ thống (Systemless Root) của Magisk và MagiskSU.",
                "Sử dụng ADB ở chế độ Root (`adb root`) và gỡ bỏ bảo vệ phân vùng bằng `adb remount`."
            ],
            [
                ("Xây Dựng Phòng Lab Phân Tích Động Tiêu Chuẩn", "Phân tích động (Dynamic Analysis) là phương pháp quan sát, can thiệp và kiểm thử ứng dụng trong khi nó đang thực sự chạy trên hệ điều hành. Để thực hiện, chuyên gia pentest cần một môi trường kiểm thử có thể kiểm soát 100%: "
                "1. Android Virtual Device (AVD - Android Studio): Giải pháp chính thống, ổn định và miễn phí. Bí quyết then chốt: Luôn chọn System Image có nhãn `Google APIs` thay vì `Google Play`. Bản `Google Play` là phiên bản sản xuất bị khóa chặt, cấm hoàn toàn lệnh `adb root`. Bản `Google APIs` cho phép chuyển đổi sang quyền root dễ dàng. "
                "2. Genymotion: Máy ảo Android thương mại dựa trên VirtualBox/QEMU, tốc độ phản hồi cực nhanh, hỗ trợ sẵn tính năng chuyển đổi Root và cài đặt OpenGAPPS chỉ bằng một cú nhấp chuột."),
                ("Công Nghệ Systemless Root Của Magisk", "Trước đây, các công cụ Root (như SuperSU) can thiệp trực tiếp bằng cách ghi tệp thực thi `su` vào phân vùng `/system/bin/` hoặc `/system/xbin/`. Việc này làm hỏng chữ ký dm-verity và khiến các cơ chế bảo mật (như SafetyNet / Play Integrity) phát hiện ngay lập tức. "
                "Magisk giải quyết bài toán này bằng công nghệ Systemless Root: Magisk chỉnh sửa tệp `boot.img` và nạp một overlay ảo vào bộ nhớ RAM khi khởi động. Các tệp tin hệ thống nguyên bản trên đĩa flash hoàn toàn không bị thay đổi, trong khi ứng dụng Magisk Manager vẫn có thể cấp quyền Root linh hoạt cho các tiến trình kiểm thử."),
                ("Các Lệnh Quản Trị ADB Trọng Yếu Trong Lab", "Để phục vụ kiểm thử, chuyên gia pentest sử dụng các lệnh ADB đặc quyền: "
                "`adb root`: Khởi động lại daemon `adbd` trên thiết bị với quyền hạn Root (UID 0). "
                "`adb disable-verity`: Vô hiệu hóa cơ chế kiểm tra toàn vẹn dm-verity của nhân Linux. "
                "`adb remount`: Gắn kết lại (remount) các phân vùng hệ thống (`/system`, `/vendor`) từ chế độ Chỉ Đọc (Read-Only) sang chế độ Cho Phép Ghi (Read-Write), cho phép cài đặt các chứng chỉ số CA hoặc công cụ native.")
            ],
            "Kịch bản tấn công: Kẻ tấn công cài đặt ứng dụng mục tiêu lên thiết bị đã Root, sau đó sử dụng quyền Root để đọc trực tiếp các tệp SharedPreferences, giải nén cơ sở dữ liệu SQLite cục bộ, hoặc đính kèm trình gỡ lỗi jdb để theo dõi bộ nhớ. Phòng thủ: Ứng dụng ngân hàng phải tích hợp các giải pháp phát hiện Root (Root Detection) đa tầng, kết hợp kiểm tra tệp tin `su`, kiểm tra thuộc tính hệ thống `ro.build.tags`, và gọi Google Play Integrity API.",
            "Trong phần thực hành, chúng ta sẽ kết nối AVD, chuyển đổi quyền root và kiểm tra trạng thái phân vùng hệ thống:",
            ("bash", """# 1. Khởi động lại daemon ADB với quyền root
adb root

# 2. Vô hiệu hóa dm-verity để cho phép ghi dữ liệu hệ thống
adb disable-verity
adb reboot
adb wait-for-device
adb root

# 3. Gắn kết lại phân vùng /system với quyền đọc ghi (Read-Write)
adb remount

# 4. Kiểm tra ID người dùng hiện tại trong ADB shell
adb shell id
# Kết quả mong muốn: uid=0(root) gid=0(root) groups=0(root)"""),
            ["Tuyệt đối không sử dụng AVD bản Google Play nếu bạn cần chạy lệnh adb root.", "Luôn sao lưu tệp boot.img nguyên bản trước khi thực hiện patch Magisk."],
            ["Phân tích động đòi hỏi môi trường kiểm soát có quyền Root đầy đủ.", "Bản System Image Google APIs là lựa chọn chuẩn mực cho lab kiểm thử Android Studio.", "Magisk Systemless Root cung cấp quyền root mà không làm biến đổi phân vùng vật lý."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Loại System Image nào trong Android Studio AVD cho phép chuyên gia pentest chạy thành công lệnh 'adb root' để chuyển đổi sang quyền quản trị tối cao?", "options": ["A. Google APIs System Image", "B. Google Play System Image", "C. Android Open Source Project (AOSP) không có API", "D. WearOS Image"], "correct_index": 0, "explanation": "Bản Google APIs cho phép adb root trong khi bản Google Play bị khóa sản xuất."},
                {"type": "FILL_BLANK", "question": "Công cụ Root phổ biến nhất hiện nay hoạt động theo cơ chế Systemless Root chỉnh sửa boot.img mà không thay đổi phân vùng /system có tên là [_____].", "blanks": [{"accepted_answers": ["Magisk", "magisk"]}], "explanation": "Magisk là công cụ chuẩn mực cho Android Rooting và module injection."},
                {"type": "MATCHING", "question": "Nối lệnh ADB với chức năng quản trị lab:", "pairs": [{"left": "adb root", "right": "Khởi chạy lại adbd daemon với đặc quyền root UID 0"}, {"left": "adb disable-verity", "right": "Tắt cơ chế kiểm tra toàn vẹn dm-verity của kernel"}, {"left": "adb remount", "right": "Chuyển trạng thái phân vùng hệ thống sang chế độ Read-Write"}] , "explanation": "Bộ ba lệnh này mở toang cánh cửa kiểm soát thiết bị phục vụ pentest."},
                {"type": "FILL_BLANK", "question": "Số định danh User ID (UID) của người dùng root tối cao trong nhân Linux luôn có giá trị bằng số [_____].", "blanks": [{"accepted_answers": ["0", "zero"]}], "explanation": "UID 0 là định danh đặc quyền tối thượng trong hệ điều hành Linux."},
            ]
        ),
        (
            2,
            "Bài 4.2: Cấu Hình Bắt Gói Mạng HTTP/HTTPS Chuyên Nghiệp Với Burp Suite & OWASP ZAP",
            "Nghiên cứu kỹ thuật chặn bắt lưu lượng mạng (Traffic Interception), cài đặt chứng chỉ CA người dùng và proxy trung gian.",
            [
                "Nắm vững nguyên lý tấn công Man-in-the-Middle (MitM) thông qua Proxy trung gian (Burp Suite / ZAP).",
                "Cấu hình thiết lập Proxy trên thiết bị Android trỏ về máy tính kiểm thử.",
                "Xuất và cài đặt chứng chỉ gốc Burp Suite CA (PortSwigger CA) vào kho chứng chỉ của thiết bị.",
                "Phân tích sự khác biệt giữa kho chứng chỉ Người dùng (User CA) và kho chứng chỉ Hệ thống (System CA)."
            ],
            [
                ("Nguyên Lý Chặn Bắt Lưu Lượng Bằng Proxy Trung Gian", "Để kiểm tra xem ứng dụng Android gửi những dữ liệu gì lên máy chủ Backend (API endpoints, tham số JSON, tiêu đề xác thực Authorization header), chuyên gia bảo mật thiết lập một máy chủ Proxy trung gian - tiêu biểu là `Burp Suite` hoặc `OWASP ZAP`. "
                "Thiết bị di động được cấu hình để chuyển tiếp toàn bộ lưu lượng mạng WiFi qua địa chỉ IP và cổng của Burp Suite (mặc định là `8080`). Đối với lưu lượng HTTP không mã hóa, Burp Suite có thể đọc và sửa đổi gói tin ngay lập tức. "
                "Tuy nhiên, đối với lưu lượng HTTPS (được mã hóa bằng SSL/TLS), Burp Suite phải thực hiện kỹ thuật Giả lập máy chủ (SSL Interception): Burp Suite tự sinh ra một chứng chỉ SSL giả mạo đại diện cho tên miền máy chủ (`api.mybank.com`) và ký chứng chỉ đó bằng khóa Certificate Authority (CA) riêng của chính mình."),
                ("Kho Chứng Chỉ User CA Vs. System CA (Sự Thay Đổi Từ Android 7.0)", "Trước Android 7.0 (API 24), người dùng chỉ cần tải chứng chỉ `cacert.der` của Burp Suite về máy và cài đặt qua giao diện Settings -> Security. Chứng chỉ này nằm trong kho chứng chỉ Người dùng (User Credentials store tại `/data/misc/user/0/cacerts-added/`). Ứng dụng tự động tin tưởng chứng chỉ này và Burp Suite có thể bắt gói HTTPS dễ dàng. "
                "Tuy nhiên, bắt đầu từ Android 7.0, Google áp dụng chính sách bảo vệ mặc định: các ứng dụng Android KHÔNG CÒN TIN TƯỞNG các chứng chỉ do người dùng tự cài đặt trong kho User CA nữa! Mọi kết nối HTTPS qua Burp Suite sẽ bị ứng dụng từ chối với lỗi `SSLHandshakeException: CertPathValidatorException: Trust anchor for certification path not found`."),
                ("Kỹ Thuật Đưa Chứng Chỉ Burp Vào Kho System CA", "Để vượt qua rào cản của Android 7.0+, chuyên gia pentest bắt buộc phải chuyển chứng chỉ của Burp Suite thành một chứng chỉ Hệ thống (System CA đặt tại `/system/etc/security/cacerts/`). "
                "Quy trình chuyển đổi bao gồm: 1. Tính toán giá trị băm định danh của chứng chỉ bằng OpenSSL: `openssl x509 -inform DER -in cacert.der -subject_hash_old -noout` (ra chuỗi dạng `9a5ba575`). 2. Chuyển đổi chứng chỉ sang định dạng PEM và lưu tên thành `9a5ba575.0`. 3. Sử dụng quyền Root qua ADB để đẩy tệp `9a5ba575.0` vào thư mục `/system/etc/security/cacerts/` và gán quyền `0644`. Sau khi khởi động lại máy, hệ thống sẽ xem Burp Suite như một nhà cấp chứng chỉ toàn cầu ngang hàng với DigiCert hay Let's Encrypt!")
            ],
            "Kịch bản tấn công: Kẻ tấn công thiết lập một trạm phát WiFi giả mạo (Evil Twin / Rogue AP) tại quán cà phê và thực hiện tấn công Man-in-the-Middle (MitM) đối với các ứng dụng không kiểm tra chứng chỉ máy chủ. Kẻ tấn công có thể đọc trộm toàn bộ mật khẩu và mã thẻ tín dụng truyền qua mạng. Phòng thủ: Bắt buộc triển khai kỹ thuật Ghim chứng chỉ số (SSL Pinning) - chỉ chấp nhận duy nhất một chứng chỉ máy chủ cụ thể và từ chối mọi chứng chỉ khác, kể cả chứng chỉ nằm trong System CA.",
            "Trong phần thực hành, chúng ta sẽ chuyển đổi và cài đặt chứng chỉ Burp Suite vào phân vùng hệ thống qua ADB:",
            ("bash", """# 1. Chuyển đổi chứng chỉ Burp Suite DER sang định dạng PEM
openssl x509 -inform DER -in cacert.der -out cacert.pem

# 2. Lấy hash định danh subject_hash_old
HASH=$(openssl x509 -inform PEM -subject_hash_old -in cacert.pem | head -n 1)
cp cacert.pem ${HASH}.0

# 3. Đẩy tệp chứng chỉ vào kho System CA trên Android
adb root
adb remount
adb push ${HASH}.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/${HASH}.0

# 4. Kiểm tra chứng chỉ đã xuất hiện trong danh sách tin cậy hệ thống
adb shell ls -l /system/etc/security/cacerts/${HASH}.0"""),
            ["Luôn gán quyền 0644 (chmod 644) cho tệp chứng chỉ trong /system/etc/security/cacerts/ để tránh lỗi không đọc được.", "Kiểm tra kỹ tường lửa máy tính kiểm thử để đảm bảo cổng 8080 của Burp Suite có thể kết nối từ thiết bị di động."],
            ["Burp Suite hoạt động như một proxy trung gian can thiệp lưu lượng HTTP/HTTPS.", "Từ Android 7.0, ứng dụng mặc định không tin tưởng chứng chỉ trong kho User CA.", "Đưa chứng chỉ vào kho System CA là giải pháp căn bản để chặn bắt lưu lượng mạng."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Từ phiên bản Android nào, hệ thống mặc định không còn tin tưởng các chứng chỉ số CA do người dùng tự cài đặt (User CA) cho lưu lượng HTTPS của ứng dụng?", "options": ["A. Android 7.0 (Nougat - API 24)", "B. Android 5.0 (Lollipop)", "C. Android 9.0 (Pie)", "D. Android 11.0 (R)"], "correct_index": 0, "explanation": "Android 7.0 (API 24) nâng cao bảo mật bằng cách chỉ tin tưởng System CA mặc định."},
                {"type": "FILL_BLANK", "question": "Đường dẫn thư mục hệ thống chứa toàn bộ các chứng chỉ số gốc tin cậy của Android (System CA store) là /system/etc/security/[_____]/.", "blanks": [{"accepted_answers": ["cacerts", "cacerts/"]}], "explanation": "/system/etc/security/cacerts/ lưu các chứng chỉ số được hệ thống tin cậy tuyệt đối."},
                {"type": "MATCHING", "question": "Nối công cụ mạng với nhiệm vụ tương ứng:", "pairs": [{"left": "Burp Suite", "right": "Máy chủ Proxy trung gian can thiệp và phân tích gói tin HTTP/HTTPS"}, {"left": "OpenSSL", "right": "Chuyển đổi định dạng chứng chỉ và tính toán subject_hash_old"}, {"left": "Wireshark", "right": "Phân tích gói tin tầng giao vận TCP/UDP mức thấp"}] , "explanation": "Sự kết hợp của các công cụ giúp chuyên gia kiểm soát toàn bộ lưu lượng mạng."},
                {"type": "FILL_BLANK", "question": "Định dạng tệp chứng chỉ số hệ thống của Android luôn có phần mở rộng kết thúc bằng dấu chấm kèm số [_____] (ví dụ: 9a5ba575.0).", "blanks": [{"accepted_answers": ["0", ".0"]}], "explanation": "Số 0 biểu thị chỉ mục chứng chỉ đầu tiên có cùng mã băm subject_hash."},
            ]
        ),
        (
            3,
            "Bài 4.3: Cơ Chế Bảo Mật Mạng (Network Security Config): Khai Báo Trust Anchors & Hạn Chế Cleartext Traffic",
            "Nghiên cứu tệp cấu hình an ninh mạng `network_security_config.xml`, chính sách tin cậy chứng chỉ và chặn HTTP dạng rõ.",
            [
                "Hiểu cấu trúc và vai trò của tệp cấu hình `res/xml/network_security_config.xml`.",
                "Cấu hình cho phép tin tưởng chứng chỉ Người dùng (User CA) trong môi trường gỡ lỗi (`debug-overrides`).",
                "Chặn đứng hoàn toàn lưu lượng truyền thông văn bản rõ HTTP không mã hóa (`cleartextTrafficPermitted=\"false\"`).",
                "Vá tệp Network Security Config bằng Apktool để cho phép Burp Suite bắt gói tin mà không cần quyền Root."
            ],
            [
                ("Tệp Cấu Hình An Ninh Mạng (Network Security Configuration)", "Để giúp nhà phát triển dễ dàng tùy biến chính sách bảo mật mạng mà không cần can thiệp trực tiếp vào mã nguồn Java/Kotlin, từ Android 7.0, Google giới thiệu tính năng Network Security Configuration. Tính năng này được kích hoạt thông qua thuộc tính trong manifest: "
                "`<application android:networkSecurityConfig=\"@xml/network_security_config\">`. "
                "Tệp XML này cho phép quy định: tên miền nào được phép dùng HTTP rõ, kho chứng chỉ nào được tin tưởng (System, User hoặc tệp chứng chỉ đính kèm), và cấu hình mã băm ghim chứng chỉ số (Certificate Pinning)."),
                ("Cấu Hình debug-overrides Cho Phép Bắt Gói Burp Suite", "Một trong những tính năng tuyệt vời nhất dành cho lập trình viên và kiểm thử viên là thẻ `<debug-overrides>`. Thẻ này quy định rằng: CHỈ KHI ứng dụng được biên dịch ở chế độ debug (`android:debuggable=\"true\"`), ứng dụng mới tin tưởng kho chứng chỉ Người dùng (User CA) của Burp Suite: "
                "```xml\n<network-security-config>\n    <debug-overrides>\n        <trust-anchors>\n            <certificates src=\"user\" />\n            <certificates src=\"system\" />\n        </trust-anchors>\n    </debug-overrides>\n</network-security-config>\n```\n"
                "Khi phát hành production (`debuggable=\"false\"`), cấu hình này tự động vô hiệu hóa, bảo đảm người dùng cuối an toàn tuyệt đối."),
                ("Kỹ Thuật Vá Network Security Config Khi Pentest", "Khi chuyên gia pentest gặp phải một ứng dụng không có SSL Pinning nhưng chặn Burp Suite do chính sách Android 7.0+, chuyên gia có thể sử dụng kỹ thuật vá manifest bằng Apktool: 1. Giải nén APK bằng `apktool d app.apk`. 2. Tạo tệp `res/xml/network_security_config.xml` với nội dung cho phép `<certificates src=\"user\" />` trong thẻ `<base-config>`. 3. Thêm thuộc tính `android:networkSecurityConfig` vào thẻ `<application>` trong `AndroidManifest.xml`. 4. Đóng gói lại và ký số APK! Sau khi cài đặt, ứng dụng đã vá sẽ tin tưởng 100% chứng chỉ Burp Suite trong kho User CA mà không cần thiết bị phải có quyền Root!")
            ],
            "Kịch bản tấn công: Kẻ tấn công trên cùng mạng nội bộ thực hiện nghe lén các ứng dụng vẫn bật cờ `cleartextTrafficPermitted=\"true\"`. Dữ liệu truyền qua giao thức HTTP không mã hóa (như hình ảnh đại diện, lịch sử chat) có thể bị bắt trọn vẹn bằng Wireshark. Phòng thủ: Từ Android 9.0 (API 28), cờ `cleartextTrafficPermitted` mặc định là `false`. Nhà phát triển tuyệt đối không bật cờ này cho các kết nối production.",
            "Trong phần thực hành, chúng ta sẽ cấu hình tệp network_security_config.xml hoàn chỉnh theo tiêu chuẩn của Google:",
            ("xml", """<!-- res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- 1. Mặc định cấm toàn bộ lưu lượng HTTP không mã hóa -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- 2. Chỉ cho phép tin tưởng chứng chỉ User khi debug -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
            <certificates src="system" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>"""),
            ["Không bao giờ đặt <certificates src=\"user\" /> bên trong thẻ <base-config> trong bản phát hành chính thức.", "Đảm bảo thuộc tính cleartextTrafficPermitted luôn bằng false cho toàn bộ các kết nối API."],
            ["Network Security Config chuẩn hóa chính sách tin cậy chứng chỉ mạng trên Android 7.0+.", "Thẻ debug-overrides cho phép kiểm thử an toàn trong môi trường phát triển.", "Vá Network Security Config là giải pháp hàng đầu để bắt gói tin HTTPS trên máy không có Root."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Thẻ cấu hình nào trong tệp network_security_config.xml cho phép quy định các chính sách chỉ có hiệu lực khi ứng dụng đang chạy ở chế độ gỡ lỗi (debuggable)?", "options": ["A. <debug-overrides>", "B. <base-config>", "C. <domain-config>", "D. <trust-anchors>"], "correct_index": 0, "explanation": "<debug-overrides> chỉ áp dụng khi android:debuggable=\"true\", lý tưởng cho việc kiểm thử với Burp Suite."},
                {"type": "FILL_BLANK", "question": "Thuộc tính trong thẻ <base-config> dùng để ngăn chặn hoàn toàn các kết nối mạng giao thức HTTP không mã hóa là cleartextTraffic[_____]=\"false\".", "blanks": [{"accepted_answers": ["Permitted", "permitted", "Permitted=\"false\""]}], "explanation": "cleartextTrafficPermitted=\"false\" ép buộc toàn bộ kết nối mạng phải sử dụng HTTPS."},
                {"type": "MATCHING", "question": "Nối giá trị nguồn src trong thẻ <certificates> với phạm vi tin cậy:", "pairs": [{"left": "src=\"system\"", "right": "Tin tưởng kho chứng chỉ số gốc do nhà sản xuất cài đặt"}, {"left": "src=\"user\"", "right": "Tin tưởng kho chứng chỉ do người dùng tự cài đặt thủ công"}, {"left": "src=\"@raw/my_ca\"", "right": "Tin tưởng tệp chứng chỉ nhúng trực tiếp trong thư mục res/raw/"}] , "explanation": "Cấu hình nguồn chứng chỉ linh hoạt đáp ứng mọi kiến trúc mạng doanh nghiệp."},
                {"type": "FILL_BLANK", "question": "Từ phiên bản Android [_____] (Pie - API 28), hệ điều hành mặc định cấm hoàn toàn lưu lượng truyền thông HTTP dạng rõ (cleartext traffic).", "blanks": [{"accepted_answers": ["9.0", "9", "Android 9", "API 28"]}], "explanation": "Android 9.0 siết chặt an ninh mạng, cấm HTTP rõ trên toàn bộ hệ thống."},
            ]
        ),
        (
            4,
            "Bài 4.4: Cơ Chế Ghim Chứng Chỉ Số (SSL/TLS Pinning) & Kỹ Thuật Public Key Hash Pinning (HPKP)",
            "Nghiên cứu nguyên lý ghim chứng chỉ số, so sánh Certificate Pinning và Public Key Pinning, cơ chế hoạt động của OkHttp3.",
            [
                "Hiểu sự khác biệt giữa việc kiểm tra CA chuỗi tin cậy thông thường và cơ chế Ghim chứng chỉ (Pinning).",
                "Phân biệt Ghim toàn bộ chứng chỉ (Certificate Pinning) và Ghim hàm băm khóa công khai (Public Key Pinning).",
                "Lập trình cấu hình CertificatePinner với thư viện OkHttp3 / Retrofit hiện đại.",
                "Đánh giá rủi ro ứng dụng bị tê liệt (App Brick) khi chứng chỉ hết hạn mà không có kế hoạch dự phòng (Backup Pins)."
            ],
            [
                ("Tại Sao Kiểm Tra CA Truyền Thống Vẫn Chưa Đủ An Toàn?", "Trong quy trình bắt tay TLS thông thường, ứng dụng tin tưởng bất kỳ chứng chỉ nào được ký bởi một trong hơn 150 tổ chức phát hành chứng chỉ (CA) nằm trong kho System CA của Android. Điều này dẫn đến hai lỗ hổng an ninh chí mạng: "
                "1. Nếu một CA bất kỳ trên thế giới bị tin tặc tấn công xâm nhập (như vụ bê bối DigiNotar lịch sử), kẻ tấn công có thể phát hành chứng chỉ giả mạo hợp lệ cho bất kỳ tên miền nào. "
                "2. Nếu thiết bị của người dùng bị cài chứng chỉ độc hại vào kho System CA (như khi bị Root hoặc trong mạng nội bộ công ty), lưu lượng HTTPS có thể bị giải mã hoàn toàn. "
                "Cơ chế Ghim chứng chỉ (SSL/TLS Pinning) giải quyết triệt để vấn đề này: ứng dụng được lập trình để CHỈ CHẤP NHẬN duy nhất một chứng chỉ hoặc một khóa công khai cụ thể của máy chủ backend, từ chối mọi chứng chỉ khác dù nó được ký bởi bất kỳ CA nổi tiếng nào!"),
                ("Ghim Chứng Chỉ Vs. Ghim Khóa Công Khai (Public Key Pinning)", "Có 2 kỹ thuật ghim chính: "
                "1. Certificate Pinning: Nhúng trực tiếp toàn bộ tệp chứng chỉ (`server.cer`) vào ứng dụng và so sánh mã băm SHA-256 của toàn bộ tệp. Nhược điểm: Chứng chỉ số luôn có ngày hết hạn (thường là 1 năm). Khi chứng chỉ hết hạn, máy chủ đổi chứng chỉ mới thì ứng dụng cũ của người dùng sẽ bị ngắt kết nối hoàn toàn! "
                "2. Public Key Pinning (HPKP / SPKI Pinning): Chỉ tính toán mã băm SHA-256 của Khóa công khai (Subject Public Key Info - SPKI). Khi chứng chỉ hết hạn, quản trị viên chỉ cần gia hạn chứng chỉ bằng cặp khóa cũ (CSR cũ), mã băm khóa công khai vẫn giữ nguyên và ứng dụng tiếp tục hoạt động trơn tru!"),
                ("Triển Khai Public Key Pinning Với OkHttp3", "Thư viện mạng tiêu chuẩn OkHttp3 cung cấp lớp `CertificatePinner` cho phép ghim khóa công khai cực kỳ mạnh mẽ. Mỗi quy tắc ghim bao gồm một mẫu tên miền (hostname pattern) và danh sách các mã băm SHA-256 của khóa công khai: "
                "`CertificatePinner.Builder().add(\"api.mybank.com\", \"sha256/AAAAAAAAAAAAAAAAAAAAAA=\")`. "
                "Quy tắc vàng: Luôn khai báo ít nhất một Khóa ghim chính (Primary Pin) và một Khóa ghim dự phòng (Backup Pin) để chuẩn bị cho kịch bản khẩn cấp khi khóa chính bị lộ.")
            ],
            "Kịch bản tấn công: Kẻ tấn công thiết lập Burp Suite và chuyển chứng chỉ vào kho System CA. Khi mở ứng dụng, ứng dụng tiến hành bắt tay TLS và tính toán băm khóa công khai của Burp Suite. Vì mã băm này không khớp với danh sách ghim trong CertificatePinner, OkHttp3 lập tức ngắt kết nối với lỗi `SSLPeerUnverifiedException`. Kẻ tấn công hoàn toàn không thể xem được nội dung gói tin! Phòng thủ: Luôn triển khai CertificatePinner trong OkHttp3 và có sẵn kế hoạch xoay vòng khóa ghim dự phòng trên CDN.",
            "Trong phần thực hành, chúng ta sẽ cấu hình CertificatePinner với OkHttp3 và kiểm tra mã băm SPKI:",
            ("kotlin", """// Cấu hình OkHttp3 CertificatePinner an toàn
val certificatePinner = CertificatePinner.Builder()
    .add("api.backend.com", "sha256/47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=") // Khóa chính
    .add("api.backend.com", "sha256/k2v657xBsOVe1PQR/JU7tVu5prs700CDPvfT9R3AigM=") // Khóa dự phòng
    .build()

val okHttpClient = OkHttpClient.Builder()
    .certificatePinner(certificatePinner)
    .build()"""),
            ["Tuyệt đối luôn cấu hình ít nhất một mã băm khóa dự phòng (Backup Pin) để tránh việc ứng dụng bị tê liệt khi máy chủ đổi chứng chỉ.", "Không ghim toàn bộ chứng chỉ x509 mà chỉ ghim mã băm khóa công khai (Subject Public Key Info)."],
            ["SSL Pinning là giải pháp phòng thủ tối thượng chống lại tấn công Man-in-the-Middle.", "Public Key Pinning (HPKP) tối ưu hơn Certificate Pinning vì không bị ảnh hưởng bởi ngày hết hạn chứng chỉ.", "CertificatePinner của OkHttp3 hỗ trợ cú pháp ghim sha256/... chuẩn mực."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Lớp nào trong thư viện OkHttp3 được sử dụng để định cấu hình ghim mã băm khóa công khai SHA-256 cho các tên miền máy chủ?", "options": ["A. CertificatePinner", "B. SslSocketFactory", "C. TrustManagerBuilder", "D. NetworkSecurityConfig"], "correct_index": 0, "explanation": "CertificatePinner của OkHttp3 là lớp chuẩn mực cấu hình ghim chứng chỉ."},
                {"type": "FILL_BLANK", "question": "Phần thông tin khóa công khai của chứng chỉ số được sử dụng để tính toán mã băm trong kỹ thuật HPKP có tên viết tắt là [_____] (Subject Public Key Info).", "blanks": [{"accepted_answers": ["SPKI", "spki", "Subject Public Key Info"]}], "explanation": "Subject Public Key Info (SPKI) chứa khóa công khai và thuật toán."},
                {"type": "MATCHING", "question": "Nối kỹ thuật ghim chứng chỉ với đặc tính:", "pairs": [{"left": "Certificate Pinning", "right": "Ghim toàn bộ tệp chứng chỉ, dễ bị lỗi khi chứng chỉ hết hạn"}, {"left": "Public Key Pinning", "right": "Chỉ ghim mã băm khóa công khai, sống sót qua các đợt gia hạn"}, {"left": "Backup Pin", "right": "Mã băm khóa dự phòng giúp khôi phục kết nối khi khóa chính bị lộ"}] , "explanation": "Lựa chọn chiến lược ghim phù hợp bảo đảm tính liên tục của dịch vụ."},
                {"type": "FILL_BLANK", "question": "Ngoại lệ chuẩn do OkHttp3 ném ra khi phát hiện chứng chỉ máy chủ không khớp với mã băm đã ghim là SSLPeer[_____]Exception.", "blanks": [{"accepted_answers": ["Unverified", "unverified", "UnverifiedException"]}], "explanation": "SSLPeerUnverifiedException ngắt ngay lập tức kết nối không an toàn."}
            ]
        ),
        (
            5,
            "Bài 4.5: Khung Can Thiệp Động Frida (Dynamic Instrumentation Toolkit): Frida Server, CLI & Kiến Trúc",
            "Nghiên cứu kiến trúc khung can thiệp động Frida, cài đặt frida-server trên Android và các công cụ dòng lệnh.",
            ["Làm chủ kiến trúc phân tầng của Frida: Core Engine C/C++, Google V8 JavaScript Engine và Python Bindings.", "Cài đặt và khởi chạy frida-server tương thích với kiến trúc CPU thiết bị (arm64, x86).", "Sử dụng các công cụ dòng lệnh tiện ích: frida-ps, frida-trace, frida-discover.", "Kết nối và đính kèm (Attach / Spawn) vào tiến trình Android mục tiêu."],
            [
                ("Frida - Vũ Khí Tối Thượng Của Phân Tích Động", "Frida là một bộ công cụ can thiệp mã động (Dynamic Instrumentation Toolkit) mã nguồn mở hàng đầu thế giới được xây dựng bởi Ole André Vadla Ravnås. Frida cho phép các nhà nghiên cứu an ninh bơm (inject) các đoạn mã JavaScript tùy biến trực tiếp vào không gian bộ nhớ của các tiến trình đang chạy trên Android, iOS, Windows, macOS và Linux. "
                "Khác với việc vá mã tĩnh bằng Apktool (vốn tốn thời gian và dễ bị phát hiện bởi cơ chế kiểm tra chữ ký), Frida can thiệp trực tiếp vào bộ nhớ RAM tại thời điểm chạy: không thay đổi dù chỉ 1 byte của tệp APK trên đĩa, không cần đóng gói lại, và có thể bật/tắt các đoạn mã can thiệp tức thì."),
                ("Kiến Trúc Hoạt Động Của Frida Trên Android", "Kiến trúc của Frida bao gồm 2 thành phần chính: "
                "1. `frida-server`: Một chương trình daemon viết bằng C/C++ chạy với quyền Root trên thiết bị Android mục tiêu. frida-server sử dụng lời gọi hệ thống `ptrace` để đính kèm vào tiến trình ứng dụng, khởi tạo một luồng riêng và nạp máy ảo Google V8 JavaScript Runtime vào trong không gian địa chỉ của tiến trình đó. "
                "2. `Frida Client`: Chạy trên máy tính của chuyên gia bảo mật (thông qua Python script hoặc công cụ CLI). Client giao tiếp với frida-server qua cổng TCP chuyển tiếp của ADB (mặc định là `27042`), truyền các đoạn mã JavaScript can thiệp và nhận lại dữ liệu phản hồi."),
                ("Hai Chế Độ Can Thiệp: Attach Vs. Spawn", "Frida hỗ trợ 2 chế độ kết nối vào ứng dụng: "
                "Chế độ `Attach`: Tiến trình ứng dụng đã được người dùng mở sẵn từ trước. Frida chỉ cần tìm Process ID (PID) và đính kèm vào luồng đang chạy. "
                "Chế độ `Spawn`: Frida yêu cầu hệ điều hành khởi tạo tiến trình ứng dụng ở trạng thái tạm dừng ngay tại điểm đầu vào (Early Instrumentation). Ứng dụng bị 'đóng băng' trước khi hàm `Application.onCreate()` kịp thực thi. Chế độ Spawn là bắt buộc khi cần vượt qua các cơ chế kiểm tra bảo mật khởi động sớm như Anti-Root hoặc kiểm tra chữ ký.")
            ],
            "Kịch bản tấn công: Kẻ tấn công khởi chạy frida-server trên máy ảo, sử dụng lệnh `frida -U -f com.victim.app` để spawn ứng dụng và bơm script can thiệp vào các hàm nghiệp vụ. Phòng thủ: Các giải pháp bảo mật RASP triển khai các kỹ thuật phát hiện Frida: quét cổng TCP 27042, quét các chuỗi ký tự \"frida-agent.so\" trong tệp `/proc/self/maps`, và theo dõi các luồng bất thường tạo bởi `ptrace`.",
            "Trong phần thực hành, chúng ta sẽ tải, cài đặt frida-server lên thiết bị Android và liệt kê các tiến trình đang chạy:",
            ("bash", """# 1. Xác định kiến trúc vi xử lý của thiết bị (arm64, armeabi-v7a, x86_64)
ABI=$(adb shell getprop ro.product.cpu.abi)
echo "Thiết bị sử dụng kiến trúc: $ABI"

# 2. Đẩy tệp frida-server tương ứng vào thư mục tạm và gán quyền thực thi
adb root
adb push frida-server-16.1.4-android-$ABI /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server

# 3. Khởi chạy frida-server ngầm trong nền
adb shell "/data/local/tmp/frida-server &"

# 4. Kiểm tra kết nối từ máy tính kiểm thử
frida-ps -Uai | grep -i "backend" """),
            ["Luôn đảm bảo phiên bản của thư viện Python frida trên máy tính TRÙNG KHỚP với phiên bản của frida-server trên điện thoại.", "Khởi chạy frida-server với quyền root để có thể can thiệp vào mọi tiến trình."],
            ["Frida là bộ công cụ can thiệp bộ nhớ động hàng đầu cho đánh giá an ninh di động.", "frida-server nạp máy ảo V8 JavaScript trực tiếp vào không gian bộ nhớ tiến trình ứng dụng.", "Chế độ Spawn cho phép can thiệp sớm ngay trước khi mã ứng dụng kịp thực thi."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Engine thông dịch JavaScript nào được Frida nhúng trực tiếp vào không gian bộ nhớ của tiến trình mục tiêu để thực thi các script can thiệp động?", "options": ["A. Google V8 Engine", "B. Mozilla SpiderMonkey", "C. JavaScriptCore", "D. QuickJS"], "correct_index": 0, "explanation": "Frida nhúng engine Google V8 hiệu năng cao để biên dịch và chạy script JS lúc chạy."},
                {"type": "FILL_BLANK", "question": "Chế độ khởi chạy của Frida cho phép đóng băng và can thiệp vào ứng dụng ngay tại thời điểm khởi tạo đầu tiên trước khi onCreate() chạy có tên là [_____] (Spawn).", "blanks": [{"accepted_answers": ["Spawn", "spawn"]}], "explanation": "Chế độ Spawn lý tưởng cho việc vô hiệu hóa các cơ chế phát hiện sớm."},
                {"type": "MATCHING", "question": "Nối công cụ Frida CLI với chức năng tương ứng:", "pairs": [{"left": "frida-ps -Uai", "right": "Liệt kê danh sách toàn bộ các ứng dụng đã cài đặt và đang chạy trên thiết bị USB"}, {"left": "frida-trace", "right": "Tự động tạo hook và theo dõi luồng gọi hàm của các API cụ thể"}, {"left": "frida -U -f <package>", "right": "Khởi động ứng dụng ở chế độ Spawn và đính kèm phiên tương tác"}] , "explanation": "Các công cụ dòng lệnh của Frida hỗ trợ tự động hóa việc thám sát ứng dụng."},
                {"type": "FILL_BLANK", "question": "Cổng mạng TCP mặc định mà frida-server lắng nghe kết nối điều khiển trên thiết bị Android là cổng [_____].", "blanks": [{"accepted_answers": ["27042", ":27042"]}], "explanation": "Cổng 27042 là dấu hiệu nhận diện phổ biến bị các cơ chế Anti-Frida quét tìm."}
            ]
        ),
        (
            6,
            "Bài 4.6: Lập Trình Script Frida Nâng Cao: Java.perform, Java.use, Hooking Phương Thức & Ghi Đè Logic",
            "Nghiên cứu cú pháp JavaScript API của Frida trên Android, kỹ thuật Hooking phương thức Java và thay đổi tham số trả về.",
            ["Làm chủ các khối lệnh cốt lõi của Frida: Java.perform, Java.use, và Java.choose.", "Kỹ thuật ghi đè phương thức (Method Overloading & Implementation Overwrite).", "Đọc và sửa đổi trực tiếp các tham số truyền vào hàm (Arguments Inspection & Modification).", "Ép buộc phương thức trả về giá trị mong muốn (Bypassing Checks)."],
            [
                ("Khối Lệnh Khởi Tạo Bắt Buộc: Java.perform", "Khi tương tác với môi trường máy ảo ART trên Android thông qua Frida, mọi thao tác tìm kiếm lớp và can thiệp phương thức bắt buộc phải được bọc bên trong hàm callback `Java.perform(function() { ... })`. "
                "Hàm này đảm bảo rằng luồng hiện tại của JavaScript engine đã được đính kèm (attach) an toàn vào máy ảo ART và ClassLoader chính của ứng dụng đã sẵn sàng nạp các lớp Java."),
                ("Kỹ Thuật Định Vị Lớp & Ghi Đè Phương Thức (Java.use)", "Để can thiệp vào một lớp Java cụ thể, chuyên gia bảo mật sử dụng `Java.use(\"package.ClassName\")`. Hàm này trả về một đối tượng đại diện (wrapper) cho lớp Java. "
                "Sau khi có đối tượng, ta có thể ghi đè logic của bất kỳ phương thức nào thông qua thuộc tính `.implementation`: "
                "```javascript\nval TargetClass = Java.use(\"com.backend.SecurityChecker\");\nTargetClass.isRooted.implementation = function() {\n    console.log(\"[*] Đã can thiệp hàm isRooted() -> Ép trả về false!\");\n    return false;\n};\n```\n"
                "Khi ứng dụng gọi hàm `isRooted()`, thay vì thực thi mã gốc, máy ảo ART sẽ chuyển hướng luồng điều khiển sang đoạn mã JavaScript trên, trả về ngay lập tức giá trị `false`!"),
                ("Xử Lý Nạp Chồng Phương Thức (Method Overloading) & Quét Instance", "Khi một hàm Java có nhiều phiên bản nạp chồng (Overloaded Methods - cùng tên nhưng khác kiểu tham số), Frida yêu cầu chỉ định rõ phiên bản cần can thiệp thông qua thuộc tính `.overload()`: "
                "`TargetClass.verifyUser.overload('java.lang.String', 'int').implementation = function(user, age) { ... }`. "
                "Ngoài ra, nếu muốn tìm kiếm các instance của đối tượng đang tồn tại thực tế trong vùng nhớ heap, ta sử dụng `Java.choose(\"com.backend.UserSession\", { onMatch: function(instance) { ... }, onComplete: function() {} })`.")
            ],
            "Kịch bản tấn công: Kẻ tấn công sử dụng script Frida để can thiệp vào hàm `checkPin(String pin)` của ứng dụng ví điện tử. Script ghi đè hàm để luôn trả về `true`, cho phép kẻ tấn công nhập bất kỳ mã PIN nào (kể cả 000000) cũng đăng nhập thành công vào tài khoản! Phòng thủ: Bắt buộc xác thực mã PIN và tạo chữ ký giao dịch trên phần cứng bảo mật (Android Keystore / TEE) hoặc gửi mã lên máy chủ Backend xác thực.",
            "Trong phần thực hành, chúng ta sẽ viết một script Frida hoàn chỉnh để hook hàm kiểm tra xác thực và in tham số ra màn hình:",
            ("javascript", """// Script Frida can thiệp phương thức xác thực: hook_auth.js
Java.perform(function () {
    console.log("[+] Bắt đầu nạp script can thiệp Frida...");

    var LoginManager = Java.use("com.backend.androidsec.auth.LoginManager");

    // Hook phương thức login với 2 tham số String
    LoginManager.login.overload('java.lang.String', 'java.lang.String').implementation = function (username, password) {
        console.log("[*] Phát hiện gọi hàm LoginManager.login()");
        console.log("    -> Tên đăng nhập: " + username);
        console.log("    -> Mật khẩu: " + password);

        // Gọi hàm gốc để quan sát kết quả
        var result = this.login(username, password);
        console.log("    -> Kết quả đăng nhập gốc: " + result);

        // Ép buộc kết quả trả về luôn là true (bẻ khóa xác thực)
        return true;
    };
});"""),
            ["Luôn sử dụng khối Java.perform để bảo đảm luồng đã được gắn kết với máy ảo ART.", "Sử dụng .overload() chính xác kiểu tham số khi phương thức có nạp chồng."],
            ["Java.perform là cửa ngõ khởi tạo mọi tác vụ can thiệp Java trong Frida.", "Java.use cung cấp quyền truy cập và ghi đè logic hàm qua thuộc tính .implementation.", "Frida cho phép đọc, sửa đổi tham số và thay đổi giá trị trả về trong nháy mắt."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Hàm nào trong Frida JavaScript API bắt buộc phải sử dụng để bao bọc mã can thiệp nhằm đảm bảo luồng thực thi đã được đính kèm vào máy ảo ART của Android?", "options": ["A. Java.perform(fn)", "B. Java.use(className)", "C. Java.attach(fn)", "D. Java.run(fn)"], "correct_index": 0, "explanation": "Java.perform bảo đảm môi trường máy ảo Java/ART đã sẵn sàng tương tác."},
                {"type": "FILL_BLANK", "question": "Thuộc tính của đối tượng phương thức trong Frida được gán hàm JavaScript mới để ghi đè toàn bộ logic thực thi của hàm Java là .[_____] (Implementation).", "blanks": [{"accepted_answers": ["implementation", ".implementation"]}], "explanation": "method.implementation = function() {...} thay thế thân hàm Java gốc bằng mã JS."},
                {"type": "MATCHING", "question": "Nối hàm Frida API với chức năng chuyên biệt:", "pairs": [{"left": "Java.use", "right": "Định vị và tạo đối tượng đại diện cho một lớp Java"}, {"left": "Java.choose", "right": "Quét tìm các instance đang tồn tại của lớp trong bộ nhớ heap"}, {"left": "Java.cast", "right": "Ép kiểu đối tượng sang một lớp dẫn xuất cụ thể"}] , "explanation": "Bộ ba hàm này cung cấp khả năng điều khiển toàn diện các đối tượng Java trong RAM."},
                {"type": "FILL_BLANK", "question": "Phương thức dùng để phân biệt và chỉ định phiên bản hàm cụ thể khi gặp nạp chồng phương thức (Method Overloading) trong Frida là .[_____]().", "blanks": [{"accepted_answers": ["overload", ".overload", "overload()"]}], "explanation": "overload('type1', 'type2') định danh chính xác chữ ký phương thức cần hook."}
            ]
        ),
        (
            7,
            "Bài 4.7: Vượt Rào Ghim Chứng Chỉ (SSL Pinning Bypass) Toàn Năng Bằng Frida",
            "Nghiên cứu kỹ thuật triệt tiêu SSL Pinning trên Android lúc chạy, hook TrustManager, OkHttp3 CertificatePinner và BoringSSL.",
            [
                "Hiểu cơ chế vận hành của các script Universal SSL Pinning Bypass trên Frida.",
                "Kỹ thuật hook lớp `javax.net.ssl.X509TrustManager` và làm rỗng phương thức `checkServerTrusted()`.",
                "Hooking trực tiếp phương thức `CertificatePinner.check()` của thư viện OkHttp3.",
                "Vượt rào SSL Pinning tầng Native trong thư viện BoringSSL (`SSL_CTX_set_custom_verify`)."
            ],
            [
                ("Nguyên Lý Vượt Rào SSL Pinning Lúc Chạy", "Như chúng ta đã tìm hiểu ở Bài 4.4, SSL Pinning là cơ chế bảo vệ máy chủ ngăn chặn Burp Suite bắt gói tin. Tuy nhiên, vì toàn bộ logic kiểm tra mã băm chứng chỉ đều nằm trong ứng dụng chạy trên thiết bị mà chuyên gia bảo mật có toàn quyền kiểm soát, chúng ta có thể sử dụng Frida để vô hiệu hóa hoàn toàn cơ chế kiểm tra này! "
                "Thay vì phải dịch ngược và vá mã nguồn Smali tốn nhiều công sức, script Frida can thiệp trực tiếp vào các hàm thẩm định chứng chỉ của hệ điều hành và thư viện mạng, biến mọi chứng chỉ giả mạo của Burp Suite thành hợp lệ."),
                ("Hooking Tầng Java Framework & OkHttp3", "Hầu hết các ứng dụng Android kiểm tra chứng chỉ thông qua một trong 3 tầng sau: "
                "1. Java TrustManager: Mọi kết nối TLS chuẩn đều gọi phương thức `checkServerTrusted(X509Certificate[] chain, String authType)` của interface `X509TrustManager`. Nếu chứng chỉ không hợp lệ, hàm này sẽ ném ngoại lệ `CertificateException`. Kỹ thuật bypass của Frida: Ghi đè hàm này thành một hàm rỗng (`function() {}`) không làm gì cả! Vì không có ngoại lệ nào bị ném ra, kết nối TLS được thiết lập thành công. "
                "2. Thư viện OkHttp3: Ghi đè hàm `okhttp3.CertificatePinner.check(String hostname, List peerCertificates)` thành hàm rỗng. Mọi kiểm tra mã băm SHA-256 bị bỏ qua hoàn toàn."),
                ("Vượt Rào SSL Pinning Tầng Native (BoringSSL / Flutter)", "Các ứng dụng hiện đại viết bằng Flutter, React Native hoặc thư viện C++ tùy biến (như OpenSSL/BoringSSL) không sử dụng `X509TrustManager` của Java mà tự đóng gói ngăn xếp mạng riêng. Trong trường hợp này, các script Java thông thường hoàn toàn bất lực. "
                "Để vượt qua, chuyên gia bảo mật sử dụng `Interceptor.attach()` của Frida để hook trực tiếp vào các hàm native trong thư viện `libflutter.so` hoặc `libssl.so`: tìm đến hàm `ssl_crypto_x509_session_verify_cert_chain()` hoặc `SSL_CTX_set_custom_verify()` và ép giá trị trả về luôn là `1` (thành công).")
            ],
            "Kịch bản tấn công: Chuyên gia bảo mật sử dụng script Frida Universal SSL Pinning Bypass. Ngay khi ứng dụng khởi chạy, toàn bộ lưu lượng API mã hóa HTTPS của ngân hàng lập tức hiển thị rõ ràng trên cửa sổ Burp Suite. Chuyên gia có thể phân tích cấu trúc JSON, tìm kiếm các lỗ hổng logic nghiệp vụ (IDOR, Broken Access Control) trên máy chủ Backend. Phòng thủ: Kết hợp kiểm tra phát hiện Frida (Anti-Frida) và kiểm tra tính toàn vẹn của mã bộ nhớ lúc chạy.",
            "Trong phần thực hành, chúng ta sẽ sử dụng script Frida CodeShare để vượt rào SSL Pinning chỉ bằng một lệnh:",
            ("bash", """# 1. Kích hoạt Universal SSL Pinning Bypass trực tiếp từ kho Frida CodeShare
frida --codeshare pcipolloni/universal-android-ssl-pinning-bypass-with-frida -U -f com.backend.androidsec

# 2. Hoặc sử dụng script tùy biến cục bộ qua cờ -l
frida -U -f com.backend.androidsec -l ssl_bypass.js"""),
            ["Luôn chạy script bypass với cờ -f (Spawn mode) để đảm bảo hook được thiết lập TRƯỚC KHI kết nối mạng đầu tiên được tạo ra.", "Kiểm tra kỹ xem ứng dụng có sử dụng Flutter không để chọn đúng script bypass tầng native."],
            ["Frida vô hiệu hóa SSL Pinning bằng cách ghi đè hàm checkServerTrusted và CertificatePinner.check.", "Kỹ thuật hook làm rỗng thân hàm loại bỏ hoàn toàn việc ném ngoại lệ CertificateException.", "Đối với Flutter và ứng dụng Native, bắt buộc phải can thiệp vào thư viện BoringSSL."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Phương thức nào của lớp okhttp3.CertificatePinner thường bị các script Frida can thiệp ghi đè thành hàm rỗng để vượt qua cơ chế ghim chứng chỉ số?", "options": ["A. check(String hostname, List peerCertificates)", "B. pin()", "C. verify()", "D. findMatchingPins()"], "correct_index": 0, "explanation": "CertificatePinner.check() là nơi ném ngoại lệ SSLPeerUnverifiedException nếu mã băm không khớp."},
                {"type": "FILL_BLANK", "question": "Interface chuẩn trong Java chịu trách nhiệm xác thực chuỗi chứng chỉ số máy chủ và thường bị hook làm rỗng trong Frida là X509Trust[_____].", "blanks": [{"accepted_answers": ["Manager", "manager", "X509TrustManager"]}], "explanation": "X509TrustManager kiểm tra danh sách chứng chỉ do máy chủ trả về."},
                {"type": "MATCHING", "question": "Nối công nghệ ứng dụng với vị trí thực thi SSL Pinning:", "pairs": [{"left": "Ứng dụng Android Java/Kotlin", "right": "X509TrustManager và OkHttp3 CertificatePinner"}, {"left": "Ứng dụng Flutter", "right": "Thư viện BoringSSL nhúng trong libflutter.so"}, {"left": "Ứng dụng React Native", "right": "Tầng mạng OkHttp3 của native Android wrapper"}] , "explanation": "Xác định đúng công nghệ giúp lựa chọn phương thức hook chính xác."},
                {"type": "FILL_BLANK", "question": "Kho lưu trữ mã nguồn mở trực tuyến cho phép các nhà nghiên cứu an ninh chia sẻ và tái sử dụng các script Frida kiểm thử nhanh có tên là Frida Code[_____].", "blanks": [{"accepted_answers": ["Share", "share", "CodeShare"]}], "explanation": "Frida CodeShare (codeshare.frida.re) là kho lưu trữ script cộng đồng nổi tiếng."}
            ]
        ),
        (
            8,
            "Bài 4.8: Tự Động Hóa Khám Phá Ứng Dụng Với Objection Runtime Mobile Exploration",
            "Nghiên cứu công cụ Objection dựa trên Frida, tự động hóa khám phá bộ nhớ, phá vỡ SSL Pinning và vô hiệu hóa Root Detection.",
            [
                "Hiểu vai trò của Objection như một bộ khung tự động hóa cấp cao xây dựng trên nền tảng Frida.",
                "Làm chủ các lệnh thám sát tương tác: `android hooking list classes`, `search methods`.",
                "Vượt rào SSL Pinning và Root Detection chỉ bằng 1 lệnh: `android sslpinning disable`, `android root disable`.",
                "Thao tác trực tiếp với cơ sở dữ liệu SQLite và SharedPreferences trên thiết bị lúc chạy."
            ],
            [
                ("Objection - Khung Khám Phá Ứng Dụng Di Động Toàn Diện", "Mặc dù Frida vô cùng mạnh mẽ, việc phải viết các đoạn mã JavaScript thủ công cho từng tác vụ kiểm thử lặp đi lặp lại (như dump bộ nhớ, tắt SSL Pinning, liệt kê Activities) có thể làm giảm tốc độ đánh giá an ninh. `Objection` (do SensePost phát triển) là một bộ công cụ dòng lệnh được xây dựng hoàn toàn trên nền tảng Frida, đóng gói sẵn hàng trăm kịch bản kiểm thử bảo mật di động phổ biến thành một shell tương tác cực kỳ trực quan."),
                ("Các Tính Năng Thám Sát Bộ Nhớ Của Objection", "Bên trong shell tương tác của Objection, chuyên gia pentest có thể thực thi các lệnh quyền lực: "
                "`env`: In ra toàn bộ thông tin đường dẫn thư mục nội bộ, thư mục cache, và cấu trúc gói ứng dụng. "
                "`android hooking list classes`: Liệt kê toàn bộ các lớp Java đang được nạp vào bộ nhớ tiến trình. "
                "`android hooking search methods <class> <pattern>`: Tìm kiếm nhanh các phương thức liên quan đến bảo mật (như `crypto`, `auth`, `token`). "
                "`android hooking watch class_method <method>`: Theo dõi luồng thực thi, tự động in tham số truyền vào và giá trị trả về mỗi khi hàm được gọi mà không cần viết một dòng mã hook nào!"),
                ("Tự Động Hóa Vô Hiệu Hóa Các Cơ Chế Phòng Thủ", "Objection cung cấp các lệnh 'một chạm' tích hợp sẵn các kỹ thuật bypass tiên tiến nhất: "
                "`android sslpinning disable`: Tự động tìm kiếm và vô hiệu hóa hơn 10 triển khai SSL Pinning phổ biến (OkHttp, TrustManager, PhoneGap, Appcelerator, WebView). "
                "`android root disable`: Tự động hook các hàm kiểm tra tệp tin `su`, kiểm tra thư mục cài đặt Root và các ứng dụng Superuser. "
                "`android keystore list`: Liệt kê các bí mật và khóa mã hóa lưu trữ trong Android Keystore.")
            ],
            "Kịch bản tấn công: Chuyên gia pentest khởi động ứng dụng với lệnh `objection --gadget com.victim.app explore`. Gõ lệnh `android sslpinning disable` và `android root disable`. Ngay lập tức, toàn bộ rào chắn bảo vệ của ứng dụng bị gỡ bỏ, cho phép chuyên gia tự do thám sát các endpoint API trên Burp Suite. Phòng thủ: Triển khai các biện pháp chống Objection: phát hiện các chuỗi nhãn của objection-agent và kiểm tra tính nguyên vẹn của luồng thực thi.",
            "Trong phần thực hành, chúng ta sẽ sử dụng Objection để kết nối vào ứng dụng và khám phá cơ sở dữ liệu SQLite cục bộ:",
            ("bash", """# 1. Khởi động Objection và đính kèm vào ứng dụng mục tiêu
objection --gadget com.backend.androidsec explore

# 2. Vô hiệu hóa SSL Pinning và Root Detection bên trong shell Objection
com.backend.androidsec on (Android: 13) [usb] # android sslpinning disable
com.backend.androidsec on (Android: 13) [usb] # android root disable

# 3. Liệt kê các cơ sở dữ liệu SQLite của ứng dụng và thực thi truy vấn
com.backend.androidsec on (Android: 13) [usb] # sqlite connect app_database.db
com.backend.androidsec on (Android: 13) [usb] # sqlite execute schema"""),
            ["Cần đảm bảo frida-server đang chạy trên thiết bị trước khi khởi động Objection.", "Sử dụng lệnh exit để thoát khỏi Objection một cách an toàn."],
            ["Objection tự động hóa việc thám sát bộ nhớ di động trên nền tảng Frida.", "Các lệnh android sslpinning disable và root disable gỡ bỏ rào cản chỉ trong một giây.", "Khả năng kết nối và truy vấn SQLite trực tiếp trong RAM giúp phân tích dữ liệu nhanh chóng."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Lệnh tương tác nào bên trong shell của Objection được sử dụng để tự động vô hiệu hóa toàn bộ các cơ chế ghim chứng chỉ số SSL/TLS của ứng dụng?", "options": ["A. android sslpinning disable", "B. ssl bypass", "C. disable cert_pinning", "D. network security off"], "correct_index": 0, "explanation": "android sslpinning disable là lệnh tiêu chuẩn của Objection để tắt SSL Pinning."},
                {"type": "FILL_BLANK", "question": "Công cụ thám sát an ninh di động tương tác dòng lệnh xây dựng trên nền tảng Frida do SensePost phát triển có tên là [_____].", "blanks": [{"accepted_answers": ["Objection", "objection"]}], "explanation": "Objection là công cụ thám sát bảo mật di động phổ biến bậc nhất hiện nay."},
                {"type": "MATCHING", "question": "Nối lệnh Objection với hành vi tương ứng:", "pairs": [{"left": "android root disable", "right": "Tự động hook và vô hiệu hóa các cơ chế phát hiện máy Root"}, {"left": "android hooking watch class_method", "right": "Theo dõi và in tham số cùng giá trị trả về của hàm"}, {"left": "sqlite connect", "right": "Mở kết nối và tương tác trực tiếp với cơ sở dữ liệu SQLite"}] , "explanation": "Objection đơn giản hóa quy trình kiểm thử an ninh ứng dụng phức tạp."},
                {"type": "FILL_BLANK", "question": "Lệnh trong Objection dùng để in ra toàn bộ thông tin môi trường, đường dẫn lưu trữ nội bộ và cache của ứng dụng là [_____].", "blanks": [{"accepted_answers": ["env", "ENV"]}], "explanation": "Lệnh env hiển thị thông tin cấu hình môi trường ứng dụng tức thì."}
            ]
        ),
        (
            9,
            "Bài 4.9: Vượt Rào Phát Hiện Thiết Bị Root (Root Detection Bypass) Bằng Frida & Magisk DenyList",
            "Nghiên cứu các phương pháp phát hiện máy Root phổ biến và kỹ thuật ẩn Root chuyên sâu với Magisk Zygisk & Frida.",
            [
                "Nắm vững các dấu hiệu phát hiện Root kinh điển: tệp nhị phân `su`, thư mục Superuser, cờ `test-keys`.",
                "Phân tích cơ chế kiểm tra đặc quyền thực thi lệnh: `Runtime.getRuntime().exec(\"su\")`.",
                "Sử dụng Magisk Zygisk và DenyList để ẩn dấu vết Root khỏi ứng dụng ngân hàng.",
                "Lập trình script Frida hook các hàm kiểm tra tệp tin `File.exists()` và thuộc tính hệ thống."
            ],
            [
                ("Các Kỹ Thuật Phát Hiện Root Kinh Điển Trên Android", "Để bảo vệ ứng dụng khỏi việc bị thám sát bộ nhớ, các ứng dụng tài chính triển khai cơ chế phát hiện Root thông qua các bài kiểm tra: "
                "1. Kiểm tra sự tồn tại của tệp nhị phân `su`: Quét danh sách các đường dẫn phổ biến (`/system/bin/su`, `/system/xbin/su`, `/sbin/su`, `/data/local/su`). "
                "2. Kiểm tra các gói ứng dụng quản lý Root: Tìm kiếm package name của Magisk (`com.topjohnwu.magisk`), SuperSU, Busybox. "
                "3. Kiểm tra cờ bản dựng hệ thống: Đọc thuộc tính `ro.build.tags` - nếu chứa chuỗi `test-keys` thay vì `release-keys`, thiết bị có khả năng đang chạy bản ROM tùy biến. "
                "4. Thử nghiệm thực thi lệnh `su`: Gọi `Runtime.getRuntime().exec(\"su\")` và kiểm tra luồng đầu ra."),
                ("Công Nghệ Ẩn Root Bằng Magisk DenyList & Zygisk", "Để đối phó với các ứng dụng kiểm tra Root, Magisk cung cấp công nghệ `Zygisk` (chạy mã Magisk trực tiếp trong tiến trình Zygote trước khi phân nhánh) kết hợp với tính năng `DenyList`. "
                "Khi một ứng dụng được đưa vào danh sách DenyList, Zygisk sẽ tự động hoàn nguyên (unmount) toàn bộ các phân vùng ảo và thư mục liên quan đến Magisk khỏi không gian tên (Mount Namespace) của tiến trình ứng dụng đó. Đối với ứng dụng, thiết bị xuất hiện hoàn toàn nguyên bản như một chiếc điện thoại chưa từng được Root!"),
                ("Vượt Rào Bằng Script Frida Can Thiệp Hệ Thống Tệp", "Nếu không sử dụng Magisk DenyList, chuyên gia có thể sử dụng Frida để can thiệp vào các phương thức kiểm tra: "
                "Hook `java.io.File.exists()`: Nếu đường dẫn tệp đang kiểm tra chứa từ khóa `\"su\"` hoặc `\"magisk\"`, ép giá trị trả về là `false`. "
                "Hook `java.lang.Runtime.exec()`: Nếu chuỗi lệnh chứa `\"su\"`, ném ra ngoại lệ `IOException` giả lập như tệp không tồn tại.")
            ],
            "Kịch bản tấn công: Kẻ tấn công cài đặt script Frida Root Bypass. Ứng dụng ngân hàng khởi chạy, thực hiện 10 bài kiểm tra Root liên tiếp nhưng tất cả đều bị Frida lừa trả về `false`. Ứng dụng tin tưởng môi trường an toàn và cho phép kẻ tấn công tiếp tục sử dụng các công cụ thám sát bộ nhớ. Phòng thủ: Sử dụng Google Play Integrity API với cấp độ phần cứng (Hardware-Backed Attestation) - cơ chế này kiểm tra trực tiếp qua chip TPM/TEE và không thể bị đánh lừa bởi các script hook trong không gian người dùng.",
            "Trong phần thực hành, chúng ta sẽ viết script Frida hook kiểm tra tệp tin File.exists để vượt qua kiểm tra Root:",
            ("javascript", """// Script Frida Root Detection Bypass
Java.perform(function () {
    var File = Java.use("java.io.File");
    
    // Hook phương thức File.exists()
    File.exists.implementation = function () {
        var path = this.getAbsolutePath();
        if (path.indexOf("/system/bin/su") !== -1 || 
            path.indexOf("/system/xbin/su") !== -1 ||
            path.indexOf("magisk") !== -1) {
            console.log("[*] Phát hiện kiểm tra tệp Root: " + path + " -> Giả mạo KHÔNG TỒN TẠI");
            return false;
        }
        return this.exists();
    };
});"""),
            ["Cấu hình Magisk đổi tên ứng dụng quản lý (Hide the Magisk app) để tránh bị phát hiện qua package name.", "Ưu tiên sử dụng Zygisk DenyList kết hợp mô-đun Shamiko để ẩn Root ở tầng nhân hệ thống."],
            ["Phát hiện Root dựa trên việc quét tệp nhị phân su, package quản lý và thực thi lệnh shell.", "Magisk DenyList cô lập không gian tên mount namespace để ẩn hoàn toàn dấu vết Root.", "Hardware-Backed Play Integrity API là giải pháp phòng thủ tối thượng chống lại Root."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tệp nhị phân thực thi đặc quyền nào trong hệ thống Linux/Android luôn là mục tiêu đầu tiên bị các hàm kiểm tra Root quét tìm sự tồn tại?", "options": ["A. /system/bin/su", "B. /system/bin/sh", "C. /system/bin/ls", "D. /system/bin/ps"], "correct_index": 0, "explanation": "su (SuperUser) là tệp nhị phân cung cấp quyền root trên hệ thống Linux/Android."},
                {"type": "FILL_BLANK", "question": "Tính năng chạy mã Magisk trực tiếp bên trong tiến trình Zygote trước khi phân nhánh ứng dụng được gọi là [_____] (Zygisk).", "blanks": [{"accepted_answers": ["Zygisk", "zygisk"]}], "explanation": "Zygisk tích hợp sâu vào Zygote, cho phép module can thiệp trước khi app chạy."},
                {"type": "MATCHING", "question": "Nối kỹ thuật phát hiện Root với phương pháp bypass:", "pairs": [{"left": "Kiểm tra tệp nhị phân su bằng File.exists", "right": "Hook File.exists() ép trả về false nếu đường dẫn chứa su"}, {"left": "Kiểm tra thuộc tính ro.build.tags", "right": "Hook SystemProperties.get ép trả về release-keys"}, {"left": "Thực thi Runtime.getRuntime().exec(\"su\")", "right": "Hook Runtime.exec ném ngoại lệ IOException giả lập không tìm thấy"}] , "explanation": "Mỗi cơ chế kiểm tra đều có kỹ thuật hook tương ứng để hóa giải."},
                {"type": "FILL_BLANK", "question": "Tính năng tích hợp trong Magisk Manager cho phép chỉ định danh sách các ứng dụng bị ẩn dấu vết Root có tên là Deny[_____].", "blanks": [{"accepted_answers": ["List", "list", "DenyList"]}], "explanation": "DenyList chỉ định các ứng dụng mục tiêu cần ẩn môi trường root."}
            ]
        ),
        (
            10,
            "Bài 4.10: Kiểm Thử Tương Tác Giữa Các Thành Phần Với Drozer: Khai Thác IPC & Tìm Kiếm Lỗ Hổng",
            "Nghiên cứu khung kiểm thử an ninh Drozer, rà soát lỗ hổng thành phần Android và tấn công khai thác tự động.",
            [
                "Hiểu kiến trúc Client-Server của bộ khung kiểm thử an ninh toàn diện Drozer.",
                "Cài đặt Drozer Agent trên thiết bị và kết nối Drozer Console qua cổng chuyển tiếp ADB (31415).",
                "Quét tự động bề mặt tấn công của gói ứng dụng: `run app.package.attacksurface`.",
                "Khai thác các lỗ hổng Content Provider (SQLi, Directory Traversal) và Broadcast Receivers bằng Drozer."
            ],
            [
                ("Khung Kiểm Thử An Ninh Drozer (MWR InfoSecurity)", "Drozer (tiền thân là Mercury) là một khung kiểm thử an ninh toàn diện và chuyên nghiệp dành cho Android do MWR InfoSecurity phát triển. Điểm độc đáo của Drozer là nó đóng vai trò như một 'ứng dụng độc hại thông thường' (không có quyền root) được cài đặt trên thiết bị (dưới dạng `drozer-agent.apk`). "
                "Bằng cách tương tác từ góc nhìn của một ứng dụng bên thứ ba không có đặc quyền, Drozer cho phép chuyên gia pentest xác định chính xác xem một ứng dụng mục tiêu có bị phơi bày các lỗ hổng IPC (như rò rỉ dữ liệu qua Content Provider hoặc kích hoạt trái phép Service) cho các phần mềm độc hại khác khai thác hay không."),
                ("Kiến Trúc & Quy Trình Kết Nối Drozer", "Quy trình kết nối Drozer bao gồm: "
                "1. Drozer Agent chạy trên điện thoại, lắng nghe kết nối trên cổng TCP nội bộ `31415`. "
                "2. Sử dụng lệnh chuyển tiếp cổng của ADB: `adb forward tcp:31415 tcp:31415`. "
                "3. Chuyên gia khởi động bảng điều khiển `drozer console connect` trên máy tính. "
                "Từ bảng điều khiển này, Drozer cung cấp hàng trăm mô-đun mạnh mẽ để thám sát toàn diện hệ thống."),
                ("Các Lệnh Quét Bề Mặt Tấn Công Trọng Yếu", "Các mô-đun Drozer tiêu chuẩn: "
                "`run app.package.attacksurface <package>`: Đánh giá nhanh số lượng Activities, Services, Receivers và Content Providers bị exported. "
                "`run app.provider.finduri <package>`: Quét mã nguồn và tài nguyên để tự động tìm kiếm toàn bộ các Content URI khả dụng. "
                "`run scanner.provider.injection`: Tự động gửi các chuỗi kiểm thử SQL Injection vào tất cả các Content Provider và báo cáo lỗ hổng. "
                "`run scanner.provider.traversal`: Tự động kiểm tra lỗ hổng duyệt thư mục (Path Traversal).")
            ],
            "Kịch bản tấn công: Chuyên gia chạy lệnh `run scanner.provider.injection -a com.victim.app`. Drozer phát hiện URI `content://com.victim.app.provider/notes` bị dính lỗi SQLi. Chuyên gia gõ tiếp lệnh `run app.provider.query content://com.victim.app.provider/notes --projection \"* FROM sqlite_master;--\"` để trích xuất toàn bộ cấu trúc bảng và mật khẩu của người dùng! Phòng thủ: Khóa cờ exported và áp dụng truy vấn tham số hóa cho mọi Content Provider.",
            "Trong phần thực hành, chúng ta sẽ chuyển tiếp cổng ADB và kết nối Drozer Console để quét ứng dụng mục tiêu:",
            ("bash", """# 1. Chuyển tiếp cổng TCP của Drozer Agent qua ADB
adb forward tcp:31415 tcp:31415

# 2. Khởi động bảng điều khiển Drozer Console trên máy tính kiểm thử
drozer console connect

# 3. Quét bề mặt tấn công của ứng dụng mục tiêu
dz> run app.package.attacksurface com.backend.androidsec

# 4. Quét tự động lỗ hổng SQL Injection trên các Content Provider
dz> run scanner.provider.injection -a com.backend.androidsec"""),
            ["Đảm bảo Drozer Agent trên điện thoại đã được bật công tắc Embedded Server trước khi kết nối.", "Sử dụng môi trường ảo Python 2.7 hoặc bản Drozer Python 3 tùy chỉnh tương thích."],
            ["Drozer kiểm thử an ninh Android từ góc nhìn của một ứng dụng bên thứ ba không có quyền root.", "Lệnh app.package.attacksurface cung cấp bức tranh toàn cảnh về các component bị lộ lọt.", "Mô-đun quét tự động của Drozer phát hiện nhanh chóng các lỗ hổng SQLi và Path Traversal."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Mô-đun nào của Drozer được sử dụng để quét và thống kê số lượng thành phần (Activities, Services, Receivers, Providers) bị exported công khai của một gói ứng dụng?", "options": ["A. run app.package.attacksurface", "B. run app.package.info", "C. run app.component.list", "D. run scanner.misc.check"], "correct_index": 0, "explanation": "app.package.attacksurface tóm tắt bề mặt tấn công ngoại vi của ứng dụng."},
                {"type": "FILL_BLANK", "question": "Cổng mạng TCP mặc định được Drozer Agent sử dụng để lắng nghe kết nối từ Drozer Console qua adb forward là cổng [_____].", "blanks": [{"accepted_answers": ["31415", ":31415"]}], "explanation": "Cổng 31415 là cổng kết nối tiêu chuẩn của giao thức Drozer IPC."},
                {"type": "MATCHING", "question": "Nối mô-đun Drozer với mục tiêu kiểm thử:", "pairs": [{"left": "scanner.provider.injection", "right": "Tự động phát hiện lỗ hổng SQL Injection trên các Content Provider"}, {"left": "scanner.provider.traversal", "right": "Tự động kiểm tra lỗ hổng Directory Traversal đọc tệp tin"}, {"left": "app.activity.start", "right": "Khởi chạy trực tiếp một Activity bị exported từ shell Drozer"}] , "explanation": "Hệ thống mô-đun phong phú của Drozer giúp tự động hóa quá trình pentest."},
                {"type": "FILL_BLANK", "question": "Tiền tố ký tự dấu nhắc lệnh trong môi trường tương tác của Drozer Console là [_____]>.", "blanks": [{"accepted_answers": ["dz", "DZ"]}], "explanation": "dz> là dấu nhắc lệnh mặc định trong Drozer CLI."},
            ]
        ),
        (
            11,
            "Bài 4.11: Trích Xuất Bộ Nhớ Lúc Chạy (Runtime Memory Dumping): Thu Thập Khóa Mật Mã & Fridump",
            "Nghiên cứu kỹ thuật kết xuất bộ nhớ tiến trình lúc chạy, phân tích chuỗi nhạy cảm trong RAM và công cụ Fridump.",
            [
                "Hiểu cấu trúc bản đồ bộ nhớ tiến trình qua `/proc/<pid>/maps` và `/proc/<pid>/mem`.",
                "Nguy cơ rò rỉ dữ liệu nhạy cảm lưu tạm trong heap (mật khẩu, token, khóa giải mã AES).",
                "Sử dụng công cụ `Fridump` để trích xuất toàn bộ dữ liệu bộ nhớ tiến trình sang đĩa.",
                "Phân tích bộ nhớ bằng tiện ích `strings` và áp dụng phương pháp dọn dẹp biến nhạy cảm an toàn."
            ],
            [
                ("Tại Sao Bộ Nhớ RAM Lại Là Mảnh Đất Màu Mỡ Của Tin Tặc?", "Nhiều nhà phát triển áp dụng các kỹ thuật mã hóa cực kỳ phức tạp để bảo vệ dữ liệu khi lưu trên đĩa và khi truyền qua mạng. Tuy nhiên, để ứng dụng có thể xử lý, tính toán hoặc hiển thị cho người dùng xem, dữ liệu BẮT BUỘC phải được giải mã và nạp vào bộ nhớ RAM dưới dạng rõ tại một thời điểm nào đó! "
                "Nếu kẻ tấn công có quyền Root trên thiết bị hoặc sử dụng công cụ can thiệp động, chúng có thể trích xuất (dump) toàn bộ không gian bộ nhớ của tiến trình và tìm kiếm các thông tin bí mật này một cách dễ dàng."),
                ("Cấu Trúc Bộ Nhớ Tiến Trình & Bản Đồ /proc/<pid>/maps", "Trong nhân Linux, mọi tiến trình đều có một thư mục thông tin ảo trong `/proc/<pid>/`: "
                "`/proc/<pid>/maps`: Liệt kê danh sách tất cả các dải địa chỉ bộ nhớ ảo đang được cấp phát (gồm ngăn xếp stack, heap, thư viện .so) kèm theo quyền hạn đọc ghi (`r-xp`, `rw-p`). "
                "`/proc/<pid>/mem`: Tệp nhị phân ảo đại diện cho toàn bộ nội dung bộ nhớ vật lý của tiến trình. Bằng cách đọc tệp này tại các dải địa chỉ có cờ Cho Phép Đọc (`r`), ta có thể sao chép nguyên vẹn dữ liệu trong RAM ra tệp tin."),
                ("Công Cụ Tự Động Hóa Fridump", "Công cụ mã nguồn mở `Fridump` (viết bằng Python kết hợp Frida) tự động hóa hoàn toàn quy trình này: 1. Đính kèm vào ứng dụng mục tiêu qua Frida. 2. Quét bản đồ bộ nhớ và xác định các phân vùng đọc ghi của heap. 3. Trích xuất tuần tự các khối bộ nhớ nhị phân về máy tính. 4. Chạy bộ lọc chuỗi ký tự (`strings`) để tạo ra một tệp văn bản tổng hợp chứa toàn bộ các chuỗi đọc được từ RAM.")
            ],
            "Kịch bản tấn công: Người dùng đăng nhập vào ứng dụng ngân hàng và thực hiện giao dịch chuyển tiền. Kẻ tấn công chạy Fridump để trích xuất bộ nhớ tiến trình của ứng dụng: `python fridump.py -U -s com.victim.bank`. Mở tệp `strings.txt` vừa trích xuất, kẻ tấn công tìm thấy mật khẩu đăng nhập, mã PIN giao dịch và chuỗi khóa phiên AES 256-bit nằm trơ trọi dưới dạng văn bản rõ! Phòng thủ: Không bao giờ lưu trữ mật khẩu trong đối tượng bất biến `java.lang.String`. Luôn lưu trữ trong mảng ký tự `char[]` hoặc mảng byte `byte[]` và chủ động xóa sạch dữ liệu bằng cách ghi đè số 0 (`Arrays.fill(pinArray, '0')`) ngay sau khi sử dụng xong.",
            "Trong phần thực hành, chúng ta sẽ sử dụng Fridump để kết xuất bộ nhớ ứng dụng mục tiêu và tìm kiếm chuỗi bí mật:",
            ("bash", """# 1. Chạy Fridump để trích xuất bộ nhớ và chuỗi ký tự qua cổng USB
python fridump.py -U -s com.backend.androidsec -o ./memory_dump

# 2. Tìm kiếm mật khẩu hoặc token trong tệp strings.txt thu được
grep -i -E "password|token|secret" ./memory_dump/strings.txt | head -n 25

# 3. Phân tích các khối bộ nhớ nhị phân bằng công cụ hexdump
hexdump -C ./memory_dump/0x7f12340000.dump | head -n 30"""),
            ["Tuyệt đối không lưu mật khẩu trong kiểu String vì String là bất biến (Immutable) và không thể chủ động xóa khỏi RAM cho đến khi GC chạy.", "Sử dụng char[] và gọi Arrays.fill() để xóa trắng bộ nhớ ngay lập tức sau khi dùng."],
            ["Mọi dữ liệu mã hóa đều phải trở về dạng rõ trong bộ nhớ RAM khi xử lý.", "Fridump tự động hóa việc kết xuất không gian bộ nhớ của tiến trình thông qua Frida.", "Sử dụng mảng ký tự char[] và xóa sạch bộ nhớ là kỹ thuật phòng vệ Data in Memory cốt lõi."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tại sao trong lập trình bảo mật Android, các chuyên gia khuyến cáo tuyệt đối không nên lưu trữ mật khẩu hoặc mã PIN trong đối tượng java.lang.String?", "options": ["A. Vì String là bất biến (Immutable), không thể xóa trắng bộ nhớ chủ động và sẽ tồn tại trong heap cho đến khi GC thu hồi", "B. Vì String bị giới hạn độ dài ký tự", "C. Vì String tự động mã hóa dữ liệu", "D. Vì String chỉ hỗ trợ ký tự số"], "correct_index": 0, "explanation": "Đối tượng String bất biến lưu trữ trong String Pool và không thể xóa trắng bằng mã lệnh."},
                {"type": "FILL_BLANK", "question": "Công cụ mã nguồn mở phổ biến viết bằng Python kết hợp Frida dùng để trích xuất toàn bộ bộ nhớ của tiến trình ra đĩa có tên là Fri[_____].", "blanks": [{"accepted_answers": ["dump", "Fridump", "fridump"]}], "explanation": "Fridump là công cụ dump memory di động tiêu chuẩn cho các chuyên gia pentest."},
                {"type": "MATCHING", "question": "Nối tệp trong /proc/<pid>/ với thông tin đại diện:", "pairs": [{"left": "/proc/<pid>/maps", "right": "Bản đồ hiển thị các dải địa chỉ bộ nhớ ảo và quyền hạn truy cập"}, {"left": "/proc/<pid>/mem", "right": "Tệp đại diện cho nội dung dữ liệu bộ nhớ nhị phân thực tế"}, {"left": "/proc/<pid>/cmdline", "right": "Dòng lệnh và tên tiến trình khởi chạy"}] , "explanation": "Hệ thống tệp ảo /proc cung cấp thông tin toàn diện về trạng thái tiến trình."},
                {"type": "FILL_BLANK", "question": "Phương thức của lớp java.util.Arrays được sử dụng để ghi đè số 0 nhằm xóa sạch dữ liệu nhạy cảm trong mảng char[] sau khi dùng là Arrays.[_____]().", "blanks": [{"accepted_answers": ["fill", "fill()"]}], "explanation": "Arrays.fill(array, '0') ghi đè bộ nhớ, ngăn chặn việc trích xuất mật khẩu từ RAM."}
            ]
        ),
        (
            12,
            "Bài 4.12: Can Thiệp Tầng Native C/C++ Bằng Frida: Interceptor.attach, Module.findExportByName",
            "Nghiên cứu kỹ thuật can thiệp sâu vào các thư viện nhị phân ELF (.so), hook hàm C và theo dõi con trỏ bộ nhớ.",
            [
                "Hiểu cơ chế hoạt động của Frida Interceptor trong việc can thiệp vào các hàm native C/C++.",
                "Sử dụng `Module.findExportByName()` và `Module.findBaseAddress()` để định vị hàm trong tệp `.so`.",
                "Làm chủ callback `onEnter` và `onLeave`: đọc tham số con trỏ qua `args[0]` và giá trị trả về `retval`.",
                "Kỹ thuật đọc chuỗi ký tự native bằng `Memory.readUtf8String()` và ghi đè bộ nhớ bằng `Memory.writeByteArray()`."
            ],
            [
                ("Can Thiệp Tầng Native Bằng Frida Interceptor", "Bên cạnh việc hook các phương thức Java thông qua `Java.use`, sức mạnh tối thượng thực sự của Frida nằm ở `Interceptor API`. Interceptor hoạt động ở tầng mã máy nhị phân, cho phép chuyên gia can thiệp vào bất kỳ hàm C/C++ nào trong các thư viện native (`.so`) của hệ thống (như `libc.so`, `libssl.so`) hoặc thư viện độc quyền của ứng dụng. "
                "Cơ chế vận hành: Frida ghi đè các byte lệnh đầu tiên của hàm mục tiêu bằng một lệnh nhảy (Trampoline Hook) chuyển hướng luồng điều khiển về đoạn mã của Frida, cho phép thực thi logic tùy biến trước và sau khi hàm gốc chạy."),
                ("Định Vị Hàm Trong Thư Viện Native", "Để can thiệp vào một hàm C, trước tiên ta phải xác định địa chỉ con trỏ của hàm đó trong bộ nhớ ảo: "
                "Nếu hàm được xuất bản công khai (Exported Function): Sử dụng `Module.findExportByName(\"libnative.so\", \"validateKey\")`. "
                "Nếu hàm là hàm nội bộ (Non-Exported / Static Function): Ta tìm địa chỉ cơ sở của thư viện bằng `Module.findBaseAddress(\"libnative.so\")`, sau đó cộng với độ lệch (Offset) của hàm tìm được từ Ghidra/IDA Pro: `var targetAddr = baseAddr.add(0x12a40);`."),
                ("Đọc & Ghi Bộ Nhớ Trực Tiếp Trong onEnter và onLeave", "Trong hàm `Interceptor.attach(targetAddr, { onEnter: function(args) {}, onLeave: function(retval) {} })`: "
                "`args[0]`, `args[1]`: Đại diện cho các thanh ghi tham số đầu vào (R0, R1 trên ARM32, hoặc X0, X1 trên ARM64). Chuyên gia có thể đọc chuỗi C qua `Memory.readUtf8String(args[0])`. "
                "`retval`: Đại diện cho giá trị trả về của hàm. Ta có thể ghi đè giá trị trả về bằng `retval.replace(1)` để ép hàm native trả về thành công.")
            ],
            "Kịch bản tấn công: Ứng dụng ngân hàng triển khai thuật toán kiểm tra tính toàn vẹn và giải mã dữ liệu hoàn toàn trong thư viện native `libsecurity.so` bằng C++ để chống dịch ngược Java. Kẻ tấn công sử dụng Ghidra xác định hàm native `Java_com_victim_Native_checkIntegrity()`, sau đó dùng `Interceptor.attach` để hook hàm này và ép `retval.replace(1)`. Toàn bộ hệ thống phòng thủ native bị vô hiệu hóa! Phòng thủ: Sử dụng kỹ thuật phát hiện Hook bằng cách kiểm tra tính toàn vẹn của các byte mở đầu hàm (Prologue Verification) và phát hiện lệnh nhảy lậu.",
            "Trong phần thực hành, chúng ta sẽ viết script Frida Interceptor để can thiệp hàm native strcmp trong libc:",
            ("javascript", """// Hook hàm so sánh chuỗi strcmp trong libc.so bằng Frida Interceptor
var strcmpAddr = Module.findExportByName("libc.so", "strcmp");

if (strcmpAddr) {
    Interceptor.attach(strcmpAddr, {
        onEnter: function (args) {
            var str1 = Memory.readUtf8String(args[0]);
            var str2 = Memory.readUtf8String(args[1]);
            
            // Lọc các chuỗi so sánh liên quan đến bản quyền hoặc mật khẩu
            if (str1 && str1.indexOf("LICENSE_KEY_") !== -1) {
                console.log("[*] Phát hiện strcmp so sánh khóa bản quyền:");
                console.log("    -> Chuỗi 1: " + str1);
                console.log("    -> Chuỗi 2: " + str2);
            }
        },
        onLeave: function (retval) {
            // Có thể ép buộc giá trị trả về = 0 (chuỗi trùng khớp)
        }
    });
}"""),
            ["Luôn kiểm tra con trỏ args[i] không phải là null (ptr(0)) trước khi gọi Memory.readUtf8String để tránh crash tiến trình.", "Cẩn thận khi hook các hàm hệ thống phổ biến như strcmp vì chúng được gọi hàng triệu lần mỗi giây."],
            ["Frida Interceptor can thiệp vào tầng mã máy nhị phân của các thư viện C/C++.", "Module.findExportByName và Module.findBaseAddress định vị chính xác hàm trong RAM.", "Interceptor cho phép đọc con trỏ bộ nhớ và thay thế giá trị trả về retval linh hoạt."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Hàm nào trong Frida Native API được sử dụng để đính kèm logic can thiệp vào một địa chỉ hàm nhị phân C/C++ cụ thể trong bộ nhớ?", "options": ["A. Interceptor.attach(target, callbacks)", "B. Native.hook(target)", "C. Memory.hook(target)", "D. C.intercept(target)"], "correct_index": 0, "explanation": "Interceptor.attach là API cốt lõi của Frida để hook các hàm C/C++ native."},
                {"type": "FILL_BLANK", "question": "Thuộc tính trong callback onLeave của Frida Interceptor đại diện cho giá trị trả về của hàm native và cho phép ghi đè giá trị bằng phương thức replace() là [_____].", "blanks": [{"accepted_answers": ["retval", "retVal"]}], "explanation": "retval.replace(ptr(1)) thay đổi trực tiếp thanh ghi chứa giá trị trả về của hàm."},
                {"type": "MATCHING", "question": "Nối hàm Frida Memory API với chức năng xử lý bộ nhớ:", "pairs": [{"left": "Memory.readUtf8String(ptr)", "right": "Đọc chuỗi ký tự kết thúc bằng null từ con trỏ bộ nhớ"}, {"left": "Memory.writeByteArray(ptr, bytes)", "right": "Ghi đè trực tiếp một mảng byte nhị phân vào địa chỉ bộ nhớ"}, {"left": "Module.findBaseAddress(name)", "right": "Lấy địa chỉ cơ sở nạp vào RAM của thư viện liên kết động .so"}] , "explanation": "Bộ công cụ Memory API cho phép thao tác con trỏ cấp thấp an toàn."},
                {"type": "FILL_BLANK", "question": "Mảng tham số đại diện cho các con trỏ giá trị truyền vào hàm native trong callback onEnter của Frida là [_____].", "blanks": [{"accepted_answers": ["args", "args[]"]}], "explanation": "args[0], args[1]... tương ứng với các tham số hàm native."}
            ]
        )
    ]

    for spec in ch4_specs:
        pos, title, summary, objs, theory, attack_def, lab_text, code_snp, pitfalls, summaries, quiz = spec
        vid_idx = (pos - 1) % len(VIDEO_CACHE)
        vurl = VIDEO_CACHE[vid_idx]["url"]

        md_content = generate_lesson_markdown(
            lesson_num=f"4.{pos}",
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
