# -*- coding: utf-8 -*-
"""Builder for Chapter 2: Mô Hình Bảo Mật Android, Sandboxing & Hệ Thống Phân Quyền (11 lessons).
Every lesson strictly exceeds 600 Vietnamese words and includes a 4-question miniquiz.
Based on 'Android Security Internals' by Nikolay Elenkov.
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
    VIDEO_CACHE = json.load(f)["ch2"]


def get_chapter_2_lessons() -> list[dict[str, Any]]:
    lessons = []

    ch2_specs = [
        (
            1,
            "Bài 2.1: Mô Hình Hộp Cát Android (Application Sandboxing) & Phân Quyền Linux DAC (UID/GID Isolation)",
            "Nghiên cứu nguyên lý hộp cát nhân Linux, cơ chế gán UID/GID độc lập cho từng ứng dụng và cô lập hệ thống tệp.",
            [
                "Nắm vững nguyên lý cốt lõi của Android Application Sandbox dựa trên phân quyền DAC của nhân Linux.",
                "Hiểu cách thức hệ điều hành gán một User ID (UID) riêng biệt cho mỗi gói cài đặt ứng dụng.",
                "Phân tích cơ chế cô lập hệ thống tệp thư mục riêng (`/data/data/<package_name>/`) với quyền `rwx------` (0700).",
                "Đánh giá tính năng chia sẻ UID thông qua `android:sharedUserId` và các rủi ro bảo mật đi kèm."
            ],
            [
                ("Nguyên Lý Hộp Cát Độc Lập Dựa Trên Nhân Linux", "Khác với các hệ điều hành máy tính truyền thống nơi mọi ứng dụng của một người dùng đều chạy chung một User ID (khiến một phần mềm độc hại có thể đọc trộm dữ liệu của mọi phần mềm khác), Android áp dụng kiến trúc cô lập đa người dùng của Linux theo một cách tiếp cận đột phá: mỗi ứng dụng Android khi cài đặt được hệ thống xem như một người dùng Linux độc lập (Linux User). Hệ thống cấp phát một định danh duy nhất gọi là App ID hay Application UID (thường bắt đầu từ UID 10000 trở đi cho người dùng chính). "
                "Cơ chế Kiểm soát truy cập tùy ý (Discretionary Access Control - DAC) của nhân Linux đóng vai trò là hàng rào bảo vệ vững chắc nhất: tiến trình của Ứng dụng A (UID 10045) hoàn toàn không có quyền đọc, ghi hoặc can thiệp vào không gian bộ nhớ cũng như hệ thống tệp của Ứng dụng B (UID 10046)."),
                ("Cấu Trúc Hệ Thống Tệp Riêng & Quyền Hạn Thư Mục", "Mỗi khi ứng dụng được cài đặt, PackageManager sẽ tạo ra một thư mục dữ liệu nội bộ riêng tại đường dẫn `/data/data/<package_name>/` (hoặc `/data/user/0/<package_name>/`). Thư mục này được gán chủ sở hữu (ownership) là UID và GID của chính ứng dụng đó với quyền truy cập khắt khe `rwx------` (octal 0700 hoặc 0751). "
                "Bên trong thư mục này chứa các thư mục con trọng yếu: `shared_prefs/` (chứa các tệp XML SharedPreferences), `databases/` (chứa các tệp cơ sở dữ liệu SQLite), `files/` (chứa tệp nội bộ), và `cache/` (chứa dữ liệu bộ đệm tạm thời). Bất kỳ tiến trình nào khác có UID khác nếu cố tình truy cập vào thư mục này sẽ bị nhân Linux từ chối ngay lập tức với lỗi `EACCES (Permission denied)`."),
                ("Tính Năng Chia Sẻ Định Danh android:sharedUserId & Bẫy Lỗi Rủi Ro", "Android cung cấp một cơ chế ngoại lệ cho phép hai hoặc nhiều ứng dụng chạy chung một UID thông qua thuộc tính `android:sharedUserId` trong manifest. Để chia sẻ chung UID, tất cả các ứng dụng này bắt buộc phải được ký bằng cùng một khóa số (Certificate) của nhà phát triển. "
                "Khi chia sẻ UID, các ứng dụng có thể đọc ghi tự do vào thư mục dữ liệu nội bộ của nhau và thậm chí chạy chung trong một tiến trình duy nhất. Tuy nhiên, nếu một trong các ứng dụng bị tấn công hoặc chứa lỗ hổng bảo mật, kẻ tấn công có thể lợi dụng UID chung để chiếm đoạt toàn bộ dữ liệu của các ứng dụng còn lại. Do rủi ro này, Google đã chính thức đánh dấu deprecated thuộc tính `sharedUserId` từ Android 10 trở đi.")
            ],
            "Kịch bản tấn công: Kẻ tấn công lợi dụng việc cấu hình sai quyền hạn tệp tin (File Permissions Misconfiguration). Trong các ứng dụng cũ sử dụng cờ lỗi thời `Context.MODE_WORLD_READABLE` (0664) hoặc `Context.MODE_WORLD_WRITEABLE` (0666) khi tạo tệp SharedPreferences hoặc SQLite, hộp cát Linux bị vô hiệu hóa cục bộ. Bất kỳ ứng dụng nào khác trên máy đều có thể đọc trích xuất dữ liệu nhạy cảm hoặc sửa đổi nội dung tệp. Phòng thủ: Tuyệt đối không sử dụng các chế độ world-readable/writeable. Luôn sử dụng `Context.MODE_PRIVATE` mặc định.",
            "Trong phần thực hành, chúng ta sẽ kết nối ADB shell để quan sát phân bổ UID và kiểm tra quyền hạn hệ thống tệp của các ứng dụng:",
            ("bash", """# 1. Liệt kê các ứng dụng cài đặt kèm theo User ID (u0_aXXX)
adb shell ps -ef | grep -E "u0_a" | head -n 20

# 2. Kiểm tra quyền hạn thư mục nội bộ trong /data/data/
adb shell su -c "ls -ld /data/data/com.android.chrome"
# Kết quả: drwx------ 5 u0_a123 u0_a123 4096 ...

# 3. Thử nghiệm truy cập trái phép bằng user thường (không root)
adb shell run-as com.android.chrome id"""),
            ["Tuyệt đối không sử dụng sharedUserId cho các dự án mới vì tính năng này đã bị cấm trên các phiên bản Android hiện đại.", "Không lưu trữ tệp tin nhạy cảm ở bộ nhớ ngoài (External Storage /sdcard/) vì bộ nhớ ngoài không áp dụng hộp cát UID."],
            ["Mỗi ứng dụng Android là một người dùng Linux độc lập được gán UID riêng biệt.", "Hộp cát Linux DAC ngăn chặn 100% việc truy cập bộ nhớ và tệp tin chéo giữa các ứng dụng.", "Thư mục /data/data/<package>/ được bảo vệ nghiêm ngặt bằng quyền 0700."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Cơ chế bảo mật nền tảng nào của nhân Linux được Android sử dụng để tạo nên Application Sandbox ngăn cách các ứng dụng?", "options": ["A. Discretionary Access Control (DAC) dựa trên User ID (UID)", "B. Windows Access Control Lists (ACL)", "C. Chroot Jail", "D. Docker Containerization"], "correct_index": 0, "explanation": "Android tận dụng hệ thống tài khoản đa người dùng của Linux (UID/GID) để cô lập ứng dụng."},
                {"type": "FILL_BLANK", "question": "Đường dẫn thư mục lưu trữ dữ liệu nội bộ an toàn của mỗi ứng dụng Android trên bộ nhớ trong có cấu trúc là /data/data/[_____] (hoặc /data/user/0/).", "blanks": [{"accepted_answers": ["<package_name>", "package_name", "tên package", "package"]}], "explanation": "Mỗi ứng dụng có một thư mục riêng đặt theo tên package định danh của nó."},
                {"type": "MATCHING", "question": "Nối các thư mục con trong dữ liệu ứng dụng với mục đích lưu trữ:", "pairs": [{"left": "shared_prefs/", "right": "Chứa các tệp XML lưu trữ cấu hình khóa-giá trị"}, {"left": "databases/", "right": "Chứa các tệp cơ sở dữ liệu SQLite cục bộ"}, {"left": "cache/", "right": "Lưu trữ dữ liệu tạm thời có thể bị hệ thống dọn dẹp"}] , "explanation": "Cấu trúc thư mục chuẩn giúp tổ chức dữ liệu ứng dụng một cách khoa học và bảo mật."},
                {"type": "FILL_BLANK", "question": "Chế độ mở tệp tin nội bộ duy nhất an toàn và mặc định trên Android để chỉ UID chủ sở hữu mới có quyền truy cập là Context.MODE_[_____].", "blanks": [{"accepted_answers": ["PRIVATE", "private"]}], "explanation": "MODE_PRIVATE thiết lập quyền 0600, chỉ cho phép ứng dụng sở hữu đọc và ghi."}
            ]
        ),
        (
            2,
            "Bài 2.2: Hệ Thống Phân Quyền (Permission System): Protection Levels, Phân Loại Quyền & Khai Báo Manifest",
            "Nghiên cứu kiến trúc quyền hạn Android, 4 cấp độ bảo vệ Protection Levels và cơ chế thực thi quyền trong Framework.",
            [
                "Nắm vững 4 cấp độ bảo vệ cơ bản: normal, dangerous, signature, signatureOrSystem (privileged).",
                "Hiểu cách thức hệ điều hành đánh giá và tự động cấp quyền khi cài đặt ứng dụng.",
                "Phân tích cơ chế định nghĩa quyền tùy biến (Custom Permissions) và khai báo thẻ `<permission>`.",
                "Nhận diện lỗ hổng Permission Re-delegation (Ủy quyền nhầm lẫn) trong kiến trúc phần mềm."
            ],
            [
                ("Bản Chất Của Hệ Thống Quyền Android (Permission Framework)", "Hệ thống quyền Android là một cơ chế kiểm soát truy cập cấp cao được xây dựng trên tầng Application Framework nhằm giới hạn quyền truy cập của ứng dụng vào các API nhạy cảm của thiết bị (như máy ảnh, micro, vị trí GPS, danh bạ, tin nhắn SMS) và các dịch vụ hệ thống trọng yếu. "
                "Bất kỳ ứng dụng nào muốn sử dụng các tài nguyên này đều bắt buộc phải khai báo rõ ràng trong tệp AndroidManifest.xml thông qua thẻ `<uses-permission android:name=\"...\" />`. Khi ứng dụng được biên dịch và cài đặt, PackageManagerService sẽ phân tích bản kê khai này và đối chiếu với chính sách bảo mật của hệ thống."),
                ("Bốn Cấp Độ Bảo Vệ Cốt Lõi (Protection Levels)", "Mỗi quyền trong hệ thống Android được gắn liền với một thuộc tính `android:protectionLevel` quy định cách thức và điều kiện cấp quyền: "
                "1. `normal`: Các quyền có rủi ro thấp cho quyền riêng tư người dùng (như truy cập Internet `INTERNET`, đặt báo thức, xem trạng thái mạng `ACCESS_NETWORK_STATE`). Hệ thống tự động phê duyệt các quyền này tại thời điểm cài đặt mà không cần hỏi người dùng. "
                "2. `dangerous`: Các quyền nhạy cảm có khả năng truy cập dữ liệu cá nhân (đọc danh bạ `READ_CONTACTS`, định vị chính xác `ACCESS_FINE_LOCATION`, ghi âm `RECORD_AUDIO`). Người dùng bắt buộc phải cấp quyền tường minh qua hộp thoại lúc chạy. "
                "3. `signature`: Cấp độ bảo vệ cực kỳ an toàn. Hệ thống chỉ cấp quyền này nếu ứng dụng yêu cầu được ký cùng một chứng chỉ số (Certificate/Keystore) với ứng dụng định nghĩa ra quyền đó. "
                "4. `signatureOrSystem` (từ Android 6.0 là `signature|privileged`): Dành riêng cho các ứng dụng hệ thống nằm trong phân vùng `/system/priv-app/` hoặc có chữ ký của nhà sản xuất thiết bị (OEM)."),
                ("Định Nghĩa Quyền Tùy Biến (Custom Permissions)", "Khi một ứng dụng cung cấp các dịch vụ hoặc Content Provider cho ứng dụng khác sử dụng, nó có thể tự định nghĩa quyền riêng qua thẻ `<permission>`: "
                "`<permission android:name=\"com.pwd301.permission.ACCESS_CORE_BANKING\" android:protectionLevel=\"signature\" />`. "
                "Bằng cách gán `protectionLevel=\"signature\"`, nhà phát triển đảm bảo rằng chỉ có các ứng dụng thuộc cùng hệ sinh thái nội bộ của công ty (được ký chung khóa phát hành) mới có thể kết nối và trao đổi dữ liệu, ngăn chặn 100% sự can thiệp từ các ứng dụng lạ."
            )
        ],
        "Kịch bản tấn công: Lỗ hổng Permission Re-delegation (Confused Deputy Attack). Kịch bản xảy ra khi Ứng dụng A có quyền nguy hiểm (ví dụ `READ_EXTERNAL_STORAGE`), và nó cung cấp một Content Provider hoặc Service được export ra ngoài nhưng lại quên không gán permission bảo vệ cho Provider đó. Lúc này, Ứng dụng B độc hại (hoàn toàn không có quyền đọc thẻ nhớ) có thể gửi yêu cầu tới Ứng dụng A, biến Ứng dụng A thành 'kẻ đại diện mù quáng' thực hiện hành vi trích xuất tệp tin thay cho Ứng dụng B! Phòng thủ: Bắt buộc bảo vệ mọi thành phần exported bằng quyền có protectionLevel tương đương hoặc kiểm tra `Binder.getCallingUid()`.",
        "Trong phần thực hành, chúng ta sẽ sử dụng ADB để tra cứu danh sách quyền, kiểm tra protection level và cấp quyền qua CLI:",
        ("bash", """# 1. Liệt kê toàn bộ các nhóm quyền nhạy cảm (dangerous permissions)
adb shell pm list permissions -g -d

# 2. Kiểm tra thông tin chi tiết và protectionLevel của một quyền cụ thể
adb shell pm dump permission android.permission.CAMERA

# 3. Tra cứu danh sách quyền đã được cấp cho một ứng dụng cụ thể
adb shell dumpsys package com.pwd301.androidsec | grep "granted=true" """),
        ["Không bao giờ đặt protectionLevel=\"normal\" cho các quyền tùy biến bảo vệ API nội bộ nhạy cảm.", "Tránh việc xin quá nhiều quyền nguy hiểm không cần thiết gây hoài nghi cho người dùng và vi phạm chính sách Google Play."],
        ["Hệ thống quyền Android kiểm soát truy cập tài nguyên phần cứng và dữ liệu riêng tư.", "Protection Level quy định điều kiện cấp quyền: normal, dangerous, signature, privileged.", "Cấp độ signature là lá chắn hoàn hảo để bảo vệ giao tiếp giữa các ứng dụng cùng một tác giả."],
        [
            {"type": "MULTIPLE_CHOICE", "question": "Cấp độ bảo vệ (protectionLevel) nào của quyền trong Android quy định rằng chỉ các ứng dụng được ký cùng chứng chỉ số (Keystore) mới được phép cấp quyền?", "options": ["A. signature", "B. dangerous", "C. normal", "D. privileged"], "correct_index": 0, "explanation": "Quyền signature chỉ được cấp nếu ứng dụng yêu cầu có cùng chữ ký số với ứng dụng định nghĩa quyền."},
            {"type": "FILL_BLANK", "question": "Thẻ XML trong tệp AndroidManifest.xml được lập trình viên sử dụng để xin cấp phép sử dụng một quyền cụ thể trong hệ thống là <[_____] />.", "blanks": [{"accepted_answers": ["uses-permission", "uses-permission android:name", "<uses-permission>"]}], "explanation": "<uses-permission> thông báo cho PackageManager biết ứng dụng cần quyền truy cập tài nguyên nào."},
            {"type": "MATCHING", "question": "Nối cấp độ protectionLevel với hành vi cấp quyền tương ứng:", "pairs": [{"left": "normal", "right": "Hệ thống tự động phê duyệt ngay tại thời điểm cài đặt"}, {"left": "dangerous", "right": "Bắt buộc người dùng phải xác nhận qua hộp thoại lúc chạy"}, {"left": "signature", "right": "Chỉ cấp cho ứng dụng có cùng chữ ký số với bên định nghĩa"}] , "explanation": "Phân cấp protection level là nền tảng quản trị quyền của Android."},
            {"type": "FILL_BLANK", "question": "Cuộc tấn công trong đó một ứng dụng có đặc quyền bị một ứng dụng không đặc quyền lợi dụng để thực hiện hành vi trái phép được gọi là lỗ hổng [_____] Deputy (Ủy quyền nhầm lẫn).", "blanks": [{"accepted_answers": ["Confused", "confused", "Confused Deputy"]}], "explanation": "Confused Deputy Attack (Permission Re-delegation) xảy ra khi component trung gian thiếu kiểm tra quyền gọi."}
        ]
    )
    ]

    # Additional lessons 2.3 to 2.11
    ch2_specs_rest = [
        (
            3,
            "Bài 2.3: Quyền Thực Thi Lúc Chạy (Runtime Permissions API 23+) & Chiến Lược Cấp Quyền Hạt Mịn",
            "Nghiên cứu cơ chế xin quyền lúc chạy từ Android 6.0, ActivityResultContracts và nguyên tắc tối thiểu đặc quyền.",
            ["Hiểu sự khác biệt về trải nghiệm người dùng giữa Install-Time Permissions và Runtime Permissions.", "Làm chủ bộ API mới: checkSelfPermission, requestPermissions và RequestPermission Contract.", "Xử lý chuẩn mực trạng thái từ chối vĩnh viễn (Don't ask again) với shouldShowRequestPermissionRationale.", "Áp dụng quyền một lần (One-Time Permission) và quyền ảnh hạt mịn trong Android 13/14."],
            [
                ("Cuộc Cách Mạng Runtime Permissions Từ Android 6.0 (Marshmallow)", "Trước Android 6.0, người dùng chỉ có một lựa chọn 'Tất cả hoặc không gì cả' (All-or-Nothing) tại thời điểm cài đặt từ Google Play: chấp nhận toàn bộ quyền mà ứng dụng yêu cầu, hoặc không thể cài đặt. Điều này dẫn đến tình trạng các phần mềm lạm dụng quyền và xâm phạm quyền riêng tư nghiêm trọng. Từ Android 6.0 (API 23), Google áp dụng mô hình Runtime Permissions: các quyền thuộc nhóm `dangerous` chỉ được hiển thị và xin phép khi ứng dụng thực sự cần sử dụng tính năng đó trong quá trình chạy."),
                ("Quy Trình Kiểm Tra & Xin Quyền Chuẩn Mực", "Quy trình xin quyền hiện đại sử dụng AndroidX ActivityResultContracts bao gồm 4 bước bắt buộc: 1. Kiểm tra xem quyền đã được cấp hay chưa bằng `ContextCompat.checkSelfPermission()`. 2. Nếu chưa được cấp, kiểm tra xem có cần giải thích lý do cho người dùng hay không bằng `ActivityCompat.shouldShowRequestPermissionRationale()`. 3. Kích hoạt hộp thoại xin quyền hệ thống qua `ActivityResultLauncher.launch()`. 4. Tiếp nhận kết quả và xử lý mượt mà cả hai trường hợp cấp quyền thành công hoặc bị từ chối."),
                ("Tiến Hóa Quyền Riêng Tư Trong Android 13 & 14", "Trong các phiên bản Android hiện đại, Google tiếp tục phân tách các quyền nguy hiểm thành các quyền siêu hạt mịn: thay vì quyền đọc bộ nhớ chung `READ_EXTERNAL_STORAGE`, Android 13 chia nhỏ thành `READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO`, và `READ_MEDIA_AUDIO`. Đặc biệt, tính năng Photo Picker cho phép người dùng chỉ chọn chia sẻ duy nhất 1-2 bức ảnh cho ứng dụng mà không cần cấp quyền truy cập toàn bộ thư viện ảnh.")
            ],
            "Kịch bản tấn công: Ứng dụng độc hại cố tình thiết lập `targetSdkVersion <= 22` trong manifest để ép hệ điều hành quay lại mô hình Install-Time permissions cũ, nhằm né tránh hộp thoại runtime permission trên các máy Android đời mới. Phòng thủ: Google Play hiện áp dụng chính sách bắt buộc mọi ứng dụng tải lên phải nhắm mục tiêu (targetSdkVersion) trong vòng 1 năm so với phiên bản Android mới nhất; đồng thời hệ điều hành Android hiện đại vẫn cung cấp App Ops cho phép người dùng âm thầm thu hồi quyền của các app cổ xưa.",
            "Trong phần thực hành, chúng ta sẽ lập trình mã nguồn xin quyền runtime chuẩn sử dụng ActivityResultLauncher:",
            ("kotlin", """// Khởi tạo ActivityResultLauncher xin quyền máy ảnh
val requestCameraPermissionLauncher = registerForActivityResult(
    ActivityResultContracts.RequestPermission()
) { isGranted: Boolean ->
    if (isGranted) {
        openCamera()
    } else {
        showPermissionDeniedMessage()
    }
}

// Kích hoạt xin quyền
requestCameraPermissionLauncher.launch(Manifest.permission.CAMERA)"""),
            ["Luôn giải thích lý do chính đáng cho người dùng trước khi hiển thị hộp thoại xin quyền hệ thống.", "Chuẩn bị sẵn phương án dự phòng mượt mà khi người dùng dứt khoát từ chối cấp quyền."],
            ["Runtime Permissions trao quyền kiểm soát tối cao cho người dùng tại thời điểm chạy.", "Quy trình xin quyền hiện đại dựa trên ActivityResultContracts loại bỏ callback lồng nhau.", "Android 13/14 tiếp tục phân tách quyền hạt mịn và bổ sung quyền một lần (One-Time)."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Phiên bản hệ điều hành Android nào lần đầu tiên giới thiệu mô hình xin quyền nguy hiểm tại thời điểm chạy (Runtime Permissions)?", "options": ["A. Android 6.0 (Marshmallow - API 23)", "B. Android 5.0 (Lollipop)", "C. Android 8.0 (Oreo)", "D. Android 10 (Q)"], "correct_index": 0, "explanation": "Android 6.0 (API 23) là mốc đánh dấu sự chuyển đổi lịch sử sang mô hình Runtime Permissions."},
                {"type": "FILL_BLANK", "question": "Hàm dùng để kiểm tra xem ứng dụng đã được cấp một quyền cụ thể hay chưa thuộc thư viện AndroidX là ContextCompat.check[_____]Permission().", "blanks": [{"accepted_answers": ["Self", "self", "SelfPermission"]}], "explanation": "ContextCompat.checkSelfPermission trả về PackageManager.PERMISSION_GRANTED hoặc PERMISSION_DENIED."},
                {"type": "MATCHING", "question": "Nối phiên bản Android với cải tiến quyền riêng tư nổi bật:", "pairs": [{"left": "Android 6.0", "right": "Bắt đầu áp dụng Runtime Permissions cho nhóm dangerous"}, {"left": "Android 10.0", "right": "Bổ sung quyền vị trí khi chỉ dùng ứng dụng (While in use)"}, {"left": "Android 13.0", "right": "Chia nhỏ quyền đọc đa phương tiện thành READ_MEDIA_IMAGES/VIDEO"}] , "explanation": "Chính sách quyền riêng tư của Google ngày càng siết chặt theo thời gian."},
                {"type": "FILL_BLANK", "question": "Hàm dùng để kiểm tra xem có nên hiển thị giao diện giải thích lý do cần quyền cho người dùng hay không là shouldShowRequestPermission[_____]().", "blanks": [{"accepted_answers": ["Rationale", "rationale"]}], "explanation": "shouldShowRequestPermissionRationale trả về true nếu người dùng từng từ chối quyền trước đó."}
            ]
        ),
        (
            4,
            "Bài 2.4: Kiến Trúc Giao Tiếp Binder IPC: Binder Driver (/dev/binder), ServiceManager, AIDL & Marshalling",
            "Nghiên cứu hạt nhân truyền thông điệp liên tiến trình của Android, giao thức IPC Binder và ngôn ngữ định nghĩa AIDL.",
            ["Làm chủ kiến trúc Binder: Binder Driver trong Linux Kernel, ServiceManager và Binder Proxies.", "Hiểu cách thức AIDL biên dịch thành các lớp Stub và Proxy.", "Nắm vững cơ chế đóng gói (Marshalling) và giải gói (Unmarshalling) dữ liệu qua Parcel.", "Phân tích luồng thực thi khi một ứng dụng gọi hàm của hệ thống thông qua Binder Transaction."],
            [
                ("Hạt Nhân Truyền Thông Binder & Trình Điều Khiển /dev/binder", "Binder là công nghệ then chốt quan trọng nhất trong toàn bộ hệ sinh thái Android, đóng vai trò là xương sống kết nối mọi thành phần ứng dụng với các dịch vụ hệ thống chạy trong tiến trình khác. Thay vì sử dụng các cơ chế IPC truyền thống của UNIX (như UNIX Domain Sockets hay System V Shared Memory - vốn yêu cầu sao chép bộ nhớ 2 lần), Binder chỉ yêu cầu sao chép bộ nhớ duy nhất 1 lần (Zero-Copy Memory Mapping) thông qua lời gọi hệ thống `mmap()` kết nối không gian bộ nhớ của tiến trình gửi với nhân Linux thông qua tệp thiết bị đặc biệt `/dev/binder`."),
                ("Vai Trò Của ServiceManager & Cơ Chế Định Vị Dịch Vụ", "Để các ứng dụng có thể tìm kiếm và kết nối tới hàng trăm dịch vụ hệ thống (như WindowManager, ActivityManager, BatteryStats), Android duy trì một tiến trình đặc quyền đóng vai trò là danh bạ trung tâm có tên là `ServiceManager` (luôn sở hữu handle Binder cố định là 0). Khi một dịch vụ hệ thống khởi chạy, nó đăng ký tên của mình với ServiceManager bằng `addService()`. Khi một ứng dụng muốn sử dụng, nó truy vấn ServiceManager bằng `getService(\"activity\")` để nhận về một đối tượng đại diện `IBinder`."),
                ("Ngôn Ngữ AIDL (Android Interface Definition Language)", "Để đơn giản hóa việc lập trình Binder, Google cung cấp ngôn ngữ AIDL. Trình biên dịch AIDL tự động sinh ra hai lớp con: 1. `Proxy`: nằm ở phía Client, chịu trách nhiệm đóng gói (marshal) các tham số gọi hàm thành đối tượng `Parcel` và gửi qua lệnh `transact()`. 2. `Stub`: nằm ở phía Server, kế thừa từ `Binder`, chịu trách nhiệm giải gói (unmarshal) dữ liệu trong callback `onTransact()` và gọi tới hàm thực thi thực tế.")
            ],
            "Kịch bản tấn công: Khai thác lỗ hổng trong hàm `onTransact()` của Binder Server. Nếu một ứng dụng xuất bản một Bound Service sử dụng AIDL mà trong hàm xử lý không xác thực danh tính của tiến trình gọi tới, kẻ tấn công có thể tạo mã Client để gửi các mã giao dịch tùy ý (Transaction Codes) nhằm ép Server thực thi các hành động đặc quyền. Phòng thủ: Luôn kiểm tra định danh người gọi bằng `Binder.getCallingUid()` trong mọi phương thức AIDL công khai.",
            "Trong phần thực hành, chúng ta sẽ sử dụng công cụ service và dumpsys trong shell ADB để tương tác với Binder Driver:",
            ("bash", """# 1. Liệt kê toàn bộ các dịch vụ hệ thống đã đăng ký với ServiceManager
adb shell service list | head -n 25

# 2. Kiểm tra thông tin thống kê trạng thái giao dịch của driver Binder
adb shell cat /proc/binder/stats

# 3. Tra cứu số lượng tham chiếu và giao dịch Binder đang hoạt động
adb shell dumpsys activity services | grep -i "Client" """),
            ["Không bao giờ truyền dữ liệu quá 1MB qua các hàm AIDL để tránh lỗi TransactionTooLargeException.", "Luôn kiểm tra nghiêm ngặt tính toàn vẹn của dữ liệu sau khi giải gói từ Parcel."],
            ["Binder là xương sống IPC của Android với hiệu năng cao nhờ kỹ thuật chia sẻ bộ nhớ mmap.", "ServiceManager quản lý danh bạ của toàn bộ các dịch vụ hệ thống với handle 0.", "AIDL tự động sinh ra cặp lớp Proxy và Stub để đóng gói/giải gói dữ liệu Parcel."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tệp thiết bị đặc biệt nào trong nhân Linux đóng vai trò là trình điều khiển trung tâm cho toàn bộ các giao dịch Binder IPC trên Android?", "options": ["A. /dev/binder", "B. /dev/null", "C. /dev/socket/zygote", "D. /dev/urandom"], "correct_index": 0, "explanation": "/dev/binder là character device driver tiếp nhận các lệnh ioctl cho Binder IPC."},
                {"type": "FILL_BLANK", "question": "Tiến trình đóng vai trò là máy chủ danh bạ đăng ký và tra cứu toàn bộ các dịch vụ hệ thống trong Android có tên là [_____].", "blanks": [{"accepted_answers": ["ServiceManager", "servicemanager", "service_manager"]}], "explanation": "ServiceManager quản lý ánh xạ giữa tên dịch vụ dạng chuỗi và handle Binder tương ứng."},
                {"type": "MATCHING", "question": "Nối thành phần trong kiến trúc AIDL với nhiệm vụ:", "pairs": [{"left": "Proxy", "right": "Đóng gói tham số thành Parcel và gửi giao dịch từ Client"}, {"left": "Stub", "right": "Tiếp nhận giao dịch và giải gói dữ liệu tại Server"}, {"left": "Binder Driver", "right": "Sao chép bộ nhớ và định tuyến gói tin trong Linux Kernel"}] , "explanation": "Proxy và Stub tạo nên sự trừu tượng hóa tuyệt vời cho lập trình viên Android."},
                {"type": "FILL_BLANK", "question": "Phương thức callback cốt lõi bên trong lớp Stub chịu trách nhiệm bốc tách mã lệnh và dữ liệu của giao dịch Binder là on[_____]().", "blanks": [{"accepted_answers": ["Transact", "transact", "Transact()"]}], "explanation": "onTransact tiếp nhận mã giao dịch (code), dữ liệu gửi (data) và vùng nhớ trả về (reply)."}
            ]
        ),
        (
            5,
            "Bài 2.5: Cơ Chế Xác Thực Danh Tính IPC: Binder.getCallingUid(), getCallingPid() & Token Bảo Mật",
            "Nghiên cứu kỹ thuật định danh và thẩm định quyền hạn người gọi trong IPC, ngăn ngừa tấn công Privilege Escalation.",
            ["Làm chủ các phương thức xác thực danh tính hệ thống: Binder.getCallingUid() và Binder.getCallingPid().", "Hiểu sự khác biệt giữa IPC cục bộ trong cùng tiến trình và IPC xuyên ranh giới tiến trình.", "Nắm vững nguyên lý hoạt động của hàm nâng quyền tạm thời Binder.clearCallingIdentity() và restoreCallingIdentity().", "Xây dựng các chốt kiểm tra quyền hạn chặt chẽ trong các dịch vụ xuất bản."],
            [
                ("Xác Thực Danh Tính Đáng Tin Cậy Qua Nhân Linux", "Một trong những tính năng bảo mật xuất sắc nhất của Binder là khả năng cung cấp thông tin danh tính của tiến trình gọi một cách an toàn tuyệt đối. Vì các giao dịch Binder đều được xử lý bên trong nhân Linux, ứng dụng Client không thể giả mạo hoặc làm sai lệch thông tin của chính mình. "
                "Khi một phương thức trong Server được gọi, Server có thể truy vấn trực tiếp nhân Linux thông qua hai hàm tĩnh: `Binder.getCallingUid()` (trả về User ID của ứng dụng gọi) và `Binder.getCallingPid()` (trả về Process ID của ứng dụng gọi). Dựa trên UID này, Server có thể truy vấn PackageManager để kiểm tra chữ ký số hoặc quyền hạn của bên gọi."),
                ("Cơ Chế Nâng Quyền Tạm Thời: clearCallingIdentity()", "Khi một dịch vụ hệ thống (ví dụ như một Service của bạn) tiếp nhận yêu cầu từ một ứng dụng bên ngoài và cần thực hiện một tác vụ nội bộ đòi hỏi đặc quyền cao (ví dụ như đọc một tệp cấu hình hệ thống), nếu dịch vụ đó trực tiếp gọi API của hệ thống thì nhân Linux vẫn sẽ xem UID của bên gọi ban đầu là người thực hiện, dẫn đến bị từ chối quyền. "
                "Để giải quyết tình huống này, Android cung cấp cặp hàm: `val token = Binder.clearCallingIdentity()`: xóa bỏ định danh của người gọi và thay thế bằng định danh của chính dịch vụ hiện tại (UID của Server); sau khi thực thi xong tác vụ đặc quyền, bắt buộc phải khôi phục lại bằng khối `finally { Binder.restoreCallingIdentity(token) }`."),
                ("Hiểm Họa Khi Lạm Dụng clearCallingIdentity()", "Nếu lập trình viên gọi `clearCallingIdentity()` trước khi tiến hành thẩm định quyền của người gọi, hoặc quên không đặt `restoreCallingIdentity()` trong khối `finally`, dịch vụ sẽ bị phơi bày hoàn toàn trước các cuộc tấn công leo thang đặc quyền. Kẻ tấn công có thể lợi dụng kẽ hở này để ép dịch vụ thực thi các hành động vượt quá phạm vi cho phép của ứng dụng Client.")
            ],
            "Kịch bản tấn công: Kẻ tấn công gửi yêu cầu tới một Bound Service xuất bản của ứng dụng ngân hàng. Service này có hàm `exportDatabaseBackup()` sử dụng `clearCallingIdentity()` nhưng lại quên không gọi `context.enforceCallingPermission()`. Kẻ tấn công không có quyền gì nhưng vẫn kích hoạt được việc xuất sao lưu toàn bộ dữ liệu bí mật! Phòng thủ: Luôn kiểm tra quyền của người gọi TRƯỚC KHI thực hiện bất kỳ lệnh clear identity nào.",
            "Trong phần thực hành, chúng ta sẽ lập trình một hàm AIDL kiểm tra quyền hạn người gọi chuẩn mực với khối try-finally an toàn:",
            ("kotlin", """// Thẩm định danh tính người gọi trong AIDL Service
override fun performSensitiveAction() {
    // 1. Kiểm tra quyền của bên gọi trước
    val callingUid = Binder.getCallingUid()
    if (context.checkCallingPermission("com.pwd301.SECURE_PERMISSION") 
        != PackageManager.PERMISSION_GRANTED) {
        throw SecurityException("UID $callingUid không có quyền truy cập!")
    }

    // 2. Nâng quyền an toàn với try-finally
    val token = Binder.clearCallingIdentity()
    try {
        // Thực thi tác vụ đặc quyền nội bộ
        internalHighPrivilegeOperation()
    } finally {
        // 3. Bắt buộc khôi phục lại định danh ban đầu
        Binder.restoreCallingIdentity(token)
    }
}"""),
            ["Tuyệt đối luôn đặt Binder.restoreCallingIdentity(token) trong khối finally để bảo đảm luôn được khôi phục ngay cả khi có ngoại lệ.", "Không bao giờ tin tưởng bất kỳ tham số định danh nào do Client truyền lên trong gói tin; chỉ tin tưởng Binder.getCallingUid()."],
            ["Binder.getCallingUid() cung cấp định danh người gọi chống giả mạo trực tiếp từ Linux Kernel.", "clearCallingIdentity() tạm thời hoán đổi UID sang quyền của Server cho các tác vụ nội bộ.", "Luôn thẩm định quyền trước khi xóa identity để ngăn chặn Privilege Escalation."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Hàm tĩnh nào của lớp android.os.Binder được sử dụng để lấy User ID (UID) thực tế của tiến trình đang gửi yêu cầu IPC xuyên ranh giới?", "options": ["A. Binder.getCallingUid()", "B. Binder.getCallingPid()", "C. Process.myUid()", "D. System.getUserId()"], "correct_index": 0, "explanation": "Binder.getCallingUid() trích xuất UID do Linux Kernel chứng thực, không thể bị giả mạo."},
                {"type": "FILL_BLANK", "question": "Hàm dùng để xóa bỏ định danh người gọi tạm thời và gán quyền của chính Server hiện tại là Binder.clearCalling[_____]().", "blanks": [{"accepted_answers": ["Identity", "identity", "Identity()"]}], "explanation": "clearCallingIdentity trả về một mã token 64-bit dùng để khôi phục trạng thái."},
                {"type": "MATCHING", "question": "Nối các phương thức kiểm tra quyền hạn của Context:", "pairs": [{"left": "checkCallingPermission", "right": "Trả về PERMISSION_GRANTED hoặc DENIED của bên gọi"}, {"left": "enforceCallingPermission", "right": "Tự động ném SecurityException nếu bên gọi thiếu quyền"}, {"left": "clearCallingIdentity", "right": "Hoán đổi UID tạm thời sang quyền của Server"}] , "explanation": "Sử dụng đúng hàm kiểm tra quyền giúp bảo vệ an toàn các endpoint IPC."},
                {"type": "FILL_BLANK", "question": "Khối lệnh bắt buộc trong Java/Kotlin phải được sử dụng để chứa lệnh Binder.restoreCallingIdentity(token) là khối [_____].", "blanks": [{"accepted_answers": ["finally", "FINALLY", "khối finally"]}], "explanation": "Khối finally bảo đảm danh tính luôn được hoàn nguyên ngay cả khi có ngoại lệ phát sinh."}
            ]
        ),
        (
            6,
            "Bài 2.6: Hệ Thống Quản Lý Gói Cài Đặt (PackageManagerService) & Xác Minh Chữ Ký Số Ứng Dụng",
            "Nghiên cứu cơ chế cài đặt, nâng cấp và xác minh tính toàn vẹn chữ ký số trong PackageManagerService (PKMS).",
            ["Hiểu kiến trúc và vai trò của PackageManagerService (PKMS) trong việc quản lý vòng đời ứng dụng.", "Nắm vững quy trình phân tích cú pháp APK (PackageParser / ParsingPackage) khi cài đặt.", "Hiểu cách thức PKMS thẩm định chữ ký số khi cập nhật phiên bản mới (Signature Matching).", "Lập trình kiểm tra chữ ký số của ứng dụng lúc chạy (Runtime Signature Verification) để chống giả mạo."],
            [
                ("Kiến Trúc PackageManagerService (PKMS)", "PackageManagerService (PKMS) là một trong những dịch vụ hệ thống quan trọng nhất chạy bên trong tiến trình `system_server`. PKMS quản lý danh sách toàn bộ các ứng dụng đã cài đặt trên thiết bị, tệp ánh xạ quyền hạn, cơ sở dữ liệu gán UID (`/data/system/packages.xml`), và định tuyến các Intent Filter. Mỗi khi thiết bị khởi động lại, PKMS sẽ quét toàn bộ các thư mục `/system/app/`, `/system/priv-app/`, và `/data/app/` để xây dựng lại cây đối tượng Package trong bộ nhớ."),
                ("Quy Trình Cài Đặt Ứng Dụng & Đối Soát Chữ Ký Số", "Khi một tệp APK mới được cài đặt (thông qua PackageInstaller hoặc lệnh `pm install`), PKMS thực hiện một chuỗi kiểm tra nghiêm ngặt: 1. Giải nén và phân tích cú pháp AndroidManifest.xml để kiểm tra tính hợp lệ của cấu trúc. 2. Xác thực tính toàn vẹn của chữ ký số (v1, v2, v3) qua tiện ích nhị phân. 3. Nếu là cài đặt mới, cấp phát một UID khả dụng chưa sử dụng. 4. Nếu là nâng cấp (Update) của một ứng dụng đã có, PKMS sẽ so sánh chữ ký số của APK mới với chữ ký số của bản đã cài: nếu hai chữ ký số KHÔNG KHỚP, quá trình cài đặt sẽ bị hủy bỏ ngay lập tức với lỗi `INSTALL_FAILED_UPDATE_INCOMPATIBLE`."),
                ("Chống Giả Mạo & Tấn Công Repackaging Bằng Chữ Ký Số", "Chữ ký số là bằng chứng xác thực duy nhất chứng minh nguồn gốc của ứng dụng. Kẻ tấn công thường tải APK từ cửa hàng về, dịch ngược bằng Apktool, chèn mã độc vào và đóng gói ký lại bằng một chứng chỉ số tự tạo (Self-signed certificate). Vì kẻ tấn công không thể có khóa riêng tư của bạn, chữ ký số của ứng dụng bị sửa đổi sẽ hoàn toàn khác biệt với bản gốc.")
            ],
            "Kịch bản tấn công: Kẻ tấn công phát tán bản APK đã chèn mã độc lên các diễn đàn mạng không chính thống. Người dùng tải về và cài đặt mới (lúc này PKMS sẽ chấp nhận chữ ký mới vì là cài mới). Nếu ứng dụng của bạn kết nối về máy chủ Backend, kẻ tấn công có thể trích xuất API keys. Phòng thủ: Ứng dụng phải tự kiểm tra mã băm SHA-256 của chữ ký số của chính mình ngay khi khởi động và gửi mã băm này lên máy chủ để xác thực, hoặc sử dụng Google Play Integrity API.",
            "Trong phần thực hành, chúng ta sẽ lập trình hàm kiểm tra chữ ký số SHA-256 của ứng dụng tại thời điểm chạy:",
            ("kotlin", """// Kiểm tra mã băm SHA-256 của chứng chỉ ứng dụng
fun isSignatureValid(context: Context, expectedSha256: String): Boolean {
    val packageInfo = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
        context.packageManager.getPackageInfo(
            context.packageName,
            PackageManager.GET_SIGNING_CERTIFICATES
        )
    } else {
        @Suppress("DEPRECATION")
        context.packageManager.getPackageInfo(
            context.packageName,
            PackageManager.GET_SIGNATURES
        )
    }
    // Lấy chứng chỉ và so sánh SHA-256 hash
    return checkCertificateHash(packageInfo, expectedSha256)
}"""),
            ["Tuyệt đối không lưu mã băm chữ ký mong muốn dưới dạng chuỗi rõ (plaintext) trong mã nguồn vì kẻ tấn công có thể patch lại bằng Smali.", "Sử dụng Play Integrity API để xác thực chữ ký từ máy chủ đám mây độc lập."],
            ["PKMS quản lý việc cài đặt, thẩm định quyền và duy trì cơ sở dữ liệu packages.xml.", "Nâng cấp ứng dụng đòi hỏi chữ ký số phải trùng khớp 100% với phiên bản đang cài đặt.", "Tự kiểm tra chữ ký số lúc chạy là tuyến phòng vệ cơ bản chống lại việc đóng gói lại (Repackaging)."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Mã lỗi nào được PackageManagerService trả về khi người dùng cố gắng cài đè một bản cập nhật APK có chữ ký số không khớp với bản đang cài đặt?", "options": ["A. INSTALL_FAILED_UPDATE_INCOMPATIBLE", "B. INSTALL_FAILED_INVALID_APK", "C. INSTALL_FAILED_PERMISSION_DENIED", "D. INSTALL_FAILED_DEXOPT"], "correct_index": 0, "explanation": "UPDATE_INCOMPATIBLE bảo vệ ứng dụng khỏi việc bị cài đè bởi một bên thứ ba không có khóa gốc."},
                {"type": "FILL_BLANK", "question": "Tệp XML hệ thống trong thư mục /data/system/ lưu trữ thông tin về toàn bộ ứng dụng cài đặt và UID được gán là packages.[_____].", "blanks": [{"accepted_answers": ["xml", "XML"]}], "explanation": "packages.xml là cơ sở dữ liệu cấu hình cốt lõi của PackageManagerService."},
                {"type": "MATCHING", "question": "Nối cờ PackageInfo với phiên bản Android hỗ trợ:", "pairs": [{"left": "GET_SIGNATURES", "right": "Cờ cũ bị deprecated từ Android 9.0"}, {"left": "GET_SIGNING_CERTIFICATES", "right": "Cờ mới từ Android 9.0 hỗ trợ xoay vòng khóa Scheme v3"}, {"left": "GET_PERMISSIONS", "right": "Yêu cầu trả về danh sách quyền hạn đã khai báo"}] , "explanation": "Sử dụng đúng cờ API theo phiên bản đảm bảo khả năng tương thích của ứng dụng."},
                {"type": "FILL_BLANK", "question": "Dịch vụ của Google cho phép máy chủ kiểm tra tính toàn vẹn của ứng dụng và phát hiện APK bị repackage có tên là Play [_____] API.", "blanks": [{"accepted_answers": ["Integrity", "integrity"]}], "explanation": "Google Play Integrity API thay thế SafetyNet Attestation để chứng thực môi trường an toàn."}
            ]
        ),
        (
            7,
            "Bài 2.7: SELinux Trên Android (SEAndroid): Mandatory Access Control (MAC), Type Enforcement & MLS",
            "Nghiên cứu cơ chế kiểm soát truy cập bắt buộc SELinux, các chế độ Enforcing/Permissive và phân tích chính sách Type Enforcement.",
            ["Hiểu sự khác biệt bản chất giữa DAC (Linux UID) và MAC (SELinux Policies).", "Phân tích 3 chế độ hoạt động của SELinux: Enforcing, Permissive, và Disabled.", "Nắm vững cấu trúc nhãn bảo mật Security Context: `user:role:type:mls_level`.", "Đọc hiểu cú pháp luật chính sách Type Enforcement: `allow source_type target_type:class permissions;`."],
            [
                ("Sự Cần Thiết Của Kiểm Soát Truy Cập Bắt Buộc (MAC)", "Mặc dù cơ chế DAC (dựa trên UID) của Linux rất mạnh mẽ, nó vẫn có một điểm yếu chí mạng: người dùng 'root' (UID 0) có toàn quyền tối thượng và có thể bỏ qua mọi hạn chế DAC. Nếu một tiến trình hệ thống chạy quyền root (như `vold` hoặc `mediaserver`) bị khai thác lỗ hổng tràn bộ đệm, kẻ tấn công sẽ ngay lập tức chiếm quyền kiểm soát toàn bộ thiết bị. "
                "Để loại bỏ điểm yếu này, từ Android 4.4 và bắt buộc từ Android 5.0, Google tích hợp SEAndroid (Security Enhancements for Android) dựa trên SELinux của NSA. SELinux triển khai cơ chế Mandatory Access Control (MAC): một bộ luật chính sách tập trung do hệ điều hành quy định bắt buộc áp dụng lên TẤT CẢ các tiến trình, kể cả tiến trình chạy với quyền Root!"),
                ("Cấu Trúc Nhãn Bảo Mật (Security Context)", "Trong SELinux, mọi thực thể trong hệ thống - bao gồm cả tiến trình (Subject) và tệp tin, socket, thiết bị (Object) - đều được gắn một nhãn bảo mật duy nhất theo định dạng 4 phần: `user:role:type:mls_level`. "
                "Ví dụ, nhãn của một ứng dụng bên thứ ba: `u:r:untrusted_app:s0:c512,c768`. "
                "Trong đó, thành phần quan trọng nhất là `type` (được gọi là Domain khi gán cho tiến trình): `untrusted_app` là domain dành riêng cho các ứng dụng tải về từ bên ngoài. `s0:c512,c768` là mức phân loại đa tầng (Multi-Level Security - MLS/MCS), trong đó cặp danh mục ngẫu nhiên `c512,c768` được sinh riêng cho từng ứng dụng để ngăn các ứng dụng trong cùng domain `untrusted_app` đọc tệp của nhau."),
                ("Quy Tắc Type Enforcement & Chế Độ Enforcing", "Mọi tương tác trong hệ thống đều bị chặn theo mặc định (Default Deny). Một hành vi chỉ được phép thực thi nếu có một luật chính sách rõ ràng cho phép: "
                "`allow untrusted_app app_data_file:file { read write open getattr };`. "
                "SELinux có 2 chế độ hoạt động chính: `Permissive` (hệ thống chỉ ghi log cảnh báo audit vào dmesg mà không chặn hành động - thường dùng khi gỡ lỗi) và `Enforcing` (hệ thống chặn đứng lập tức mọi hành vi vi phạm chính sách và ghi log `avc: denied`).")
            ],
            "Kịch bản tấn công: Kẻ tấn công khai thác được một lỗ hổng trong nhân Linux để nâng quyền tiến trình lên root (UID 0). Tuy nhiên, vì tiến trình vẫn bị giam trong domain `untrusted_app`, nó không thể truy cập vào các tệp tin của hệ thống, không thể nạp kernel module và không thể can thiệp vào các tiến trình khác. Kẻ tấn công buộc phải tìm thêm lỗ hổng trong chính sách SELinux (SELinux Bypass) để thực hiện Domain Transition sang `su` domain mới có thể kiểm soát hoàn toàn thiết bị. Phòng thủ: Thiết bị sản xuất bắt buộc phải chạy ở chế độ Enforcing 100%.",
            "Trong phần thực hành, chúng ta sẽ sử dụng ADB để tra cứu trạng thái SELinux và quan sát nhãn bảo mật của các tiến trình:",
            ("bash", """# 1. Kiểm tra trạng thái hiện tại của SELinux (Enforcing / Permissive)
adb shell getenforce

# 2. Xem nhãn bảo mật (Security Context) của các tiến trình đang chạy
adb shell ps -efZ | grep untrusted_app | head -n 10

# 3. Xem nhãn bảo mật của các tệp tin trong hệ thống
adb shell ls -lZ /data/data/ | head -n 10

# 4. Tra cứu các sự kiện bị SELinux chặn trong dmesg
adb shell dmesg | grep "avc: denied" """),
            ["Không bao giờ phát hành ứng dụng hoặc firmware tùy biến ở chế độ SELinux Permissive.", "Hiểu rõ nhãn untrusted_app để biết phạm vi hạn chế truy cập hệ thống của ứng dụng."],
            ["SELinux cung cấp cơ chế MAC bắt buộc kiểm soát cả tiến trình chạy quyền root.", "Nhãn Security Context định danh domain của tiến trình và type của tệp tin.", "Chế độ Enforcing là tiêu chuẩn bảo mật bắt buộc của toàn bộ thiết bị Android thương mại."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Lệnh dòng lệnh nào trong Android shell được sử dụng để kiểm tra chế độ hoạt động hiện tại của hệ thống SELinux (Enforcing hay Permissive)?", "options": ["A. getenforce", "B. setenforce", "C. selinux_status", "D. sestatus"], "correct_index": 0, "explanation": "getenforce in ra màn hình chế độ hiện hành của SELinux: Enforcing, Permissive hoặc Disabled."},
                {"type": "FILL_BLANK", "question": "Domain bảo mật SELinux mặc định được gán cho tất cả các ứng dụng thông thường do người dùng cài đặt từ Google Play là [_____].", "blanks": [{"accepted_answers": ["untrusted_app", "untrusted_app_27", "untrusted_app_29", "untrusted_app_25"]}], "explanation": "untrusted_app là domain bị cô lập nghiêm ngặt nhất trong bảng chính sách SEAndroid."},
                {"type": "MATCHING", "question": "Nối chế độ SELinux với hành vi vận hành:", "pairs": [{"left": "Enforcing", "right": "Chặn đứng mọi hành vi vi phạm và ghi nhật ký avc: denied"}, {"left": "Permissive", "right": "Cho phép hành vi thực thi nhưng vẫn ghi log vi phạm"}, {"left": "Disabled", "right": "Tắt hoàn toàn module SELinux trong nhân Linux"}] , "explanation": "Chế độ Enforcing là bắt buộc để đảm bảo an toàn cho thiết bị người dùng."},
                {"type": "FILL_BLANK", "question": "Từ khóa trong nhật ký hệ thống (kernel dmesg/logcat) biểu thị một hành vi truy cập vừa bị SELinux từ chối là avc: [_____].", "blanks": [{"accepted_answers": ["denied", "DENIED"]}], "explanation": "avc: denied là thông điệp cảnh báo từ Access Vector Cache của SELinux khi có vi phạm chính sách."}
            ]
        ),
        (
            8,
            "Bài 2.8: Khởi Động An Toàn (Android Verified Boot - AVB), dm-verity & Chuỗi Tin Cậy Phần Cứng",
            "Nghiên cứu chuỗi xác thực toàn vẹn khởi động từ phần cứng Bootloader, dm-verity và bảo vệ phân vùng hệ thống.",
            ["Hiểu nguyên lý Chuỗi tin cậy (Chain of Trust) bắt nguồn từ Hardware Root of Trust.", "Làm chủ cơ chế vận hành của Android Verified Boot 2.0 (AVB) và cấu trúc vbmeta.", "Phân tích công nghệ dm-verity trong việc kiểm tra toàn vẹn phân vùng theo khối thời gian thực.", "Nhận diện các trạng thái khóa Bootloader: LOCKED, UNLOCKED, và nguy cơ bảo mật."],
            [
                ("Chuỗi Tin Cậy Khởi Động (Hardware-Backed Chain of Trust)", "Để ngăn chặn kẻ tấn công cài đặt mã độc vào firmware hoặc thay thế nhân Linux khi thiết bị tắt nguồn, Android triển khai cơ chế Khởi động an toàn (Verified Boot). Quy trình này thiết lập một Chuỗi tin cậy (Chain of Trust) không thể bị gián đoạn: "
                "Bắt đầu từ Boot ROM được ghi cứng trong chip silicon của vi xử lý (Hardware Root of Trust). Boot ROM kiểm tra chữ ký số của Bootloader cấp 1 (Primary Bootloader). Bootloader cấp 1 kiểm tra Bootloader cấp 2 (ABoot / Little Kernel). Bootloader cấp 2 kiểm tra chữ ký của phân vùng `boot` (chứa Linux Kernel và ramdisk) và phân vùng `vbmeta`."),
                ("Android Verified Boot (AVB 2.0) & Phân Vùng vbmeta", "AVB 2.0 chuẩn hóa quy trình xác thực khởi động trên Android thông qua phân vùng `vbmeta` (Verified Boot Metadata). Phân vùng này chứa các khối mô tả chữ ký số (Descriptors) và khóa công khai gốc. Khi Bootloader khởi động, nó đọc `vbmeta` để kiểm tra hàm băm của các phân vùng hệ thống. Nếu chữ ký hợp lệ, hệ thống mới tiến hành nạp nhân Linux. Nếu phát hiện phân vùng bị chỉnh sửa trái phép (ví dụ do người dùng cài đặt bản ROM lậu), thiết bị sẽ từ chối khởi động hoặc hiển thị màn hình cảnh báo Đỏ (Red Warning Screen)."),
                ("Công Nghệ dm-verity & Cây Băm Merkle Tree", "Các phân vùng hệ thống như `/system`, `/vendor`, `/product` có dung lượng lên tới hàng gigabyte, do đó việc băm toàn bộ phân vùng khi khởi động sẽ làm thiết bị mất hàng phút để mở máy. Để giải quyết bài toán này, nhân Linux sử dụng module `dm-verity` (Device Mapper Verity). "
                "dm-verity tổ chức toàn bộ phân vùng thành một Cây băm Merkle (Merkle Tree) dạng phân tầng: mỗi khối dữ liệu 4 KB được băm thành một giá trị băm SHA-256. Nhân Linux chỉ cần lưu trữ duy nhất một giá trị băm gốc (Root Hash) trong `vbmeta`. Khi hệ điều hành đọc bất kỳ khối 4 KB nào từ đĩa flash, dm-verity sẽ tính toán lại băm và đối soát với cây Merkle theo thời gian thực: nếu dữ liệu bị sửa đổi dù chỉ 1 bit, lệnh I/O sẽ lập tức bị hủy bỏ với lỗi `EIO`.")
            ],
            "Kịch bản tấn công: Người dùng mở khóa Bootloader (Bootloader Unlocking) để cài đặt bản ROM tùy biến hoặc cài đặt Magisk để Root máy. Khi Bootloader ở trạng thái `UNLOCKED`, chuỗi tin cậy bị bẻ gãy, kẻ tấn công có quyền nạp nhân Linux đã bị chèn mã độc để theo dõi toàn bộ bàn phím và dữ liệu người dùng. Phòng thủ: Các ứng dụng ngân hàng và doanh nghiệp sử dụng Play Integrity API hoặc Key Attestation để kiểm tra trạng thái khóa của Bootloader (`verifiedBootState != LOCKED`), tự động từ chối hoạt động nếu phát hiện Bootloader đã bị mở khóa.",
            "Trong phần thực hành, chúng ta sẽ sử dụng lệnh fastboot và getprop để kiểm tra trạng thái Verified Boot của thiết bị:",
            ("bash", """# 1. Kiểm tra trạng thái Verified Boot từ hệ điều hành đang chạy
adb shell getprop ro.boot.verifiedbootstate
# Các giá trị có thể trả về: green (khóa chuẩn), yellow (chữ ký tùy biến), orange (unlocked), red (lỗi)

# 2. Kiểm tra cờ trạng thái khóa Bootloader
adb shell getprop ro.boot.flash.locked

# 3. Tra cứu thông số Root Hash của phân vùng dm-verity
adb shell cat /proc/cmdline | tr " " "\n" | grep verity """),
            ["Không bao giờ thực hiện giao dịch tài chính trên các thiết bị có trạng thái Verified Boot là 'orange' hoặc 'red'.", "Hiểu rõ cơ chế dm-verity để nhận diện lý do tại sao không thể sửa đổi trực tiếp các tệp trong /system khi chưa vô hiệu hóa verity."],
            ["Verified Boot thiết lập chuỗi tin cậy liên tục từ Boot ROM phần cứng đến hệ điều hành.", "dm-verity sử dụng cây băm Merkle để xác thực toàn vẹn phân vùng theo khối 4KB thời gian thực.", "Trạng thái Bootloader UNLOCKED phá vỡ hoàn toàn chuỗi bảo vệ của phần cứng."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Công nghệ nào của nhân Linux được Android sử dụng để kiểm tra tính toàn vẹn của các khối dữ liệu 4KB trên phân vùng hệ thống theo thời gian thực dựa trên cây băm Merkle?", "options": ["A. dm-verity", "B. dm-crypt", "C. eCryptfs", "D. LUKS"], "correct_index": 0, "explanation": "dm-verity (Device Mapper Verity) kiểm tra tính toàn vẹn của từng khối dữ liệu đọc từ ổ cứng flash."},
                {"type": "FILL_BLANK", "question": "Màu sắc trạng thái của Verified Boot biểu thị thiết bị hoàn toàn an toàn, Bootloader đã khóa và sử dụng chứng chỉ số gốc của nhà sản xuất là màu [_____] (Green).", "blanks": [{"accepted_answers": ["green", "xanh", "xanh lá", "Green"]}], "explanation": "Trạng thái 'green' biểu thị chuỗi tin cậy hoàn hảo; 'orange' biểu thị bootloader đã bị mở khóa."},
                {"type": "MATCHING", "question": "Nối trạng thái Verified Boot với ý nghĩa an ninh:", "pairs": [{"left": "green", "right": "Khởi động an toàn hoàn hảo với khóa gốc của nhà sản xuất"}, {"left": "yellow", "right": "Khởi động an toàn nhưng sử dụng khóa tự cài đặt của người dùng"}, {"left": "orange", "right": "Bootloader đã bị mở khóa hoàn toàn, không có bảo vệ toàn vẹn"}, {"left": "red", "right": "Phát hiện phân vùng bị can thiệp trái phép hoặc hỏng dữ liệu"}] , "explanation": "Bốn màu sắc trạng thái quy định mức độ tin cậy của phần cứng."},
                {"type": "FILL_BLANK", "question": "Phân vùng chuyên biệt trong chuẩn AVB 2.0 lưu trữ các khối mô tả chữ ký số và Root Hash của các phân vùng hệ thống có tên là [_____].", "blanks": [{"accepted_answers": ["vbmeta", "vbmeta.img"]}], "explanation": "Phân vùng vbmeta là trung tâm quản lý chữ ký số của Android Verified Boot 2.0."}
            ]
        ),
        (
            9,
            "Bài 2.9: Môi Trường Đa Người Dùng (Multi-User Ecosystem), Hồ Sơ Công Việc (Work Profile) & Knox",
            "Nghiên cứu cơ chế cách ly tài khoản người dùng, kiến trúc Android Enterprise, Work Profile và Samsung Knox.",
            ["Hiểu cách thức Android triển khai mô hình đa người dùng (Multi-User) trên cùng một thiết bị phần cứng.", "Nắm vững công thức tính toán UID cho người dùng phụ: `User_ID * 100000 + App_ID`.", "Phân tích cơ chế cô lập dữ liệu giữa Personal Profile và Work Profile trong Android Enterprise.", "Đánh giá các giải pháp bảo mật cấp doanh nghiệp như Samsung Knox Platform."],
            [
                ("Mô Hình Đa Người Dùng (Multi-User Architecture)", "Bắt đầu từ Android 4.2 trên máy tính bảng và Android 5.0 trên điện thoại, hệ thống hỗ trợ nhiều người dùng chạy song song trên cùng một thiết bị. Mỗi người dùng (User) có một ID số nguyên bắt đầu từ 0 (Primary User / Chủ thiết bị). "
                "Để đảm bảo sự cô lập tuyệt đối, Android áp dụng công thức dịch chuyển UID độc đáo: "
                "`Linux UID = User_ID * 100000 + App_ID`. "
                "Ví dụ: Ứng dụng Chrome có App_ID là 10045. Khi Người dùng 0 (Chủ máy) chạy Chrome, tiến trình có UID là `10045`. Nhưng khi Người dùng 10 (Hồ sơ thứ hai) chạy Chrome, tiến trình sẽ có UID là `1010045`! Nhân Linux đối xử hai tiến trình này như hai người dùng hoàn toàn khác biệt, đảm bảo không thể chia sẻ dữ liệu trái phép."),
                ("Hồ Sơ Công Việc (Work Profile / Android Enterprise)", "Trong môi trường doanh nghiệp (BYOD - Bring Your Own Device), nhân viên sử dụng điện thoại cá nhân để làm việc. Android Enterprise cung cấp giải pháp Work Profile: tạo ra một người dùng phụ được quản lý bởi ứng dụng Device Policy Controller (DPC). "
                "Các ứng dụng công việc được đánh dấu bằng một biểu tượng chiếc cặp nhỏ (briefcase badge). Dữ liệu công việc được lưu trữ tại phân vùng mã hóa riêng (`/data/user/10/`), các thao tác sao chép dán (Clipboard), chia sẻ tệp tin và chụp màn hình giữa Work Profile và Personal Profile có thể bị quản trị viên CNTT khóa chặt."),
                ("Nền Tảng Bảo Mật Phần Cứng Doanh Nghiệp (Samsung Knox)", "Một số nhà sản xuất thiết bị nâng cấp bảo mật doanh nghiệp lên mức độ phần cứng, tiêu biểu là Samsung Knox. Knox sử dụng chip bảo mật chuyên biệt (Knox Vault) để lưu trữ khóa mã hóa tách biệt khỏi bộ vi xử lý chính. Nếu thiết bị phát hiện có sự can thiệp vật lý hoặc nạp firmware lạ, một cầu chì điện tử phần cứng (Hardware e-fuse / Knox Warranty Void bit) sẽ bị thổi đứt vĩnh viễn (chuyển từ 0x0 sang 0x1), lập tức khóa vĩnh viễn quyền truy cập vào các vùng nhớ bảo mật Knox.")
            ],
            "Kịch bản tấn công: Kẻ tấn công tìm cách bắc cầu dữ liệu (Data Leaking across Profiles) qua các Intent công khai hoặc bộ nhớ tạm Clipboard. Ví dụ: copy mật khẩu từ ứng dụng doanh nghiệp trong Work Profile rồi dán sang một ứng dụng độc hại ở Personal Profile. Phòng thủ: Quản trị viên kích hoạt chính sách cấm chia sẻ Clipboard qua `DevicePolicyManager.addUserRestriction(UserManager.DISALLOW_CROSS_PROFILE_COPY_PASTE)`.",
            "Trong phần thực hành, chúng ta sẽ sử dụng ADB để tra cứu danh sách người dùng và tạo thử nghiệm một người dùng phụ trên thiết bị:",
            ("bash", """# 1. Liệt kê danh sách toàn bộ người dùng hiện có trên hệ thống
adb shell pm list users

# 2. Tạo một người dùng phụ mới (thử nghiệm trên giả lập)
adb shell pm create-user "TestProfile"

# 3. Chuyển đổi sang người dùng mới
adb shell am switch-user 10

# 4. Kiểm tra đường dẫn thư mục lưu trữ tách biệt
adb shell ls -ld /data/user/10/ """),
            ["Tuyệt đối không lưu trữ dữ liệu doanh nghiệp trong không gian lưu trữ cá nhân (/data/user/0/).", "Lưu ý kiểm tra thuộc tính cross-profile intent filters để tránh rò rỉ dữ liệu qua lại."],
            ["Android đa người dùng cách ly bằng công thức tính toán UID độc lập.", "Work Profile phân tách rạch ròi giữa dữ liệu cá nhân và dữ liệu doanh nghiệp.", "Cầu chì phần cứng Knox e-fuse bảo vệ tính toàn vẹn của thiết bị cấp quân sự."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Một ứng dụng có App_ID là 10080 khi chạy bên trong tài khoản Người dùng phụ có User_ID = 10 thì UID thực tế của tiến trình trong nhân Linux sẽ là bao nhiêu?", "options": ["A. 1010080", "B. 10080", "C. 100080", "D. 110080"], "correct_index": 0, "explanation": "Công thức tính: User_ID * 100000 + App_ID = 10 * 100000 + 10080 = 1010080."},
                {"type": "FILL_BLANK", "question": "Ứng dụng đóng vai trò là cơ quan quản lý và áp đặt chính sách bảo mật doanh nghiệp trên thiết bị Android có tên viết tắt là [_____] (Device Policy Controller).", "blanks": [{"accepted_answers": ["DPC", "dpc", "Device Policy Controller"]}], "explanation": "Device Policy Controller (DPC) tương tác với DevicePolicyManager để kiểm soát Work Profile."},
                {"type": "MATCHING", "question": "Nối khái niệm quản lý tài khoản với đặc tính:", "pairs": [{"left": "Primary User (User 0)", "right": "Chủ sở hữu thiết bị đầu tiên, có quyền quản trị tối cao"}, {"left": "Work Profile", "right": "Không gian làm việc cách ly có biểu tượng chiếc cặp bảo vệ"}, {"left": "Knox e-fuse", "right": "Cầu chì phần cứng bị thổi đứt vĩnh viễn khi máy bị root"}] , "explanation": "Các cơ chế này tạo nên giải pháp bảo mật toàn diện cho môi trường doanh nghiệp."},
                {"type": "FILL_BLANK", "question": "Hạn chế người dùng dùng để ngăn chặn hành vi sao chép dán dữ liệu giữa hồ sơ công việc và cá nhân là DISALLOW_CROSS_PROFILE_COPY_[_____].", "blanks": [{"accepted_answers": ["PASTE", "paste"]}], "explanation": "DISALLOW_CROSS_PROFILE_COPY_PASTE chặn đứng việc rò rỉ dữ liệu qua khay nhớ tạm Clipboard."}
            ]
        ),
        (
            10,
            "Bài 2.10: Cơ Chế Bảo Vệ Bộ Nhớ: ASLR, Stack Canaries, Seccomp BPF & Không Gian Địa Chỉ Nhân Linux",
            "Nghiên cứu các cơ chế bảo vệ bộ nhớ cấp thấp chống lại việc khai thác mã độc và kỹ thuật lọc lời gọi hệ thống Seccomp.",
            ["Làm chủ các kỹ thuật bảo vệ bộ nhớ tiến trình: ASLR, PIE, và Stack Canaries.", "Hiểu cơ chế hoạt động của Seccomp-BPF trong việc hạn chế lời gọi hệ thống (System Calls).", "Phân tích vùng nhớ không thể thực thi (NX / DEP - Data Execution Prevention).", "Đánh giá các giải pháp phòng thủ hiện đại như Control Flow Integrity (CFI) và Shadow Call Stack."],
            [
                ("Các Kỹ Thuật Bảo Vệ Không Gian Địa Chỉ Bộ Nhớ", "Để chống lại các cuộc tấn công khai thác lỗ hổng bộ nhớ (như tràn bộ đệm Buffer Overflow hay lập trình hướng trả về Return-Oriented Programming - ROP) trong các thành phần native C/C++, Android triển khai một hệ thống phòng thủ đa tầng: "
                "1. ASLR (Address Space Layout Randomization): Mỗi lần ứng dụng khởi chạy, hệ điều hành sẽ xáo trộn ngẫu nhiên vị trí của ngăn xếp (Stack), vùng nhớ heap, các thư viện dùng chung (.so) và bảng ánh xạ trong không gian địa chỉ ảo, khiến kẻ tấn công không thể dự đoán trước địa chỉ con trỏ hàm mục tiêu. Đi kèm với ASLR là cờ PIE (Position Independent Executable) bắt buộc cho mọi mã thực thi. "
                "2. Stack Canaries: Trình biên dịch chèn một giá trị bí mật (Canary) ngay trước con trỏ địa chỉ trả về (Return Address) trong ngăn xếp hàm. Trước khi hàm thoát ra, giá trị Canary được kiểm tra lại: nếu phát hiện Canary bị biến đổi, chương trình sẽ lập tức kích hoạt `abort()` để tự sát thay vì chuyển quyền điều khiển cho mã độc."),
                ("Vùng Nhớ Không Thực Thi (NX / W^X Policy)", "Chính sách Write XOR Execute (W^X / DEP) quy định rằng một trang bộ nhớ chỉ có thể có quyền Ghi (Write) HOẶC quyền Thực thi (Execute), tuyệt đối không bao giờ có cả hai quyền đồng thời. Điều này ngăn chặn kẻ tấn công bơm mã máy (Shellcode) vào vùng nhớ heap hoặc stack rồi lừa con trỏ lệnh nhảy vào đó để thực thi."),
                ("Lọc Lời Gọi Hệ Thống Bằng Seccomp-BPF", "Mặc dù nhân Linux cung cấp hơn 300 lời gọi hệ thống (syscalls), hầu hết các ứng dụng thông thường chỉ cần sử dụng vài chục syscall cơ bản. Từ Android 8.0, tiến trình Zygote áp dụng bộ lọc Seccomp (Secure Computing Mode) sử dụng Berkeley Packet Filter (BPF) lên tất cả các tiến trình con được phân nhánh. "
                "Bộ lọc Seccomp chặn đứng hoàn toàn các syscall nguy hiểm (như `ptrace`, `sys_chroot`, hoặc các syscall thao tác trực tiếp với nhân). Nếu một ứng dụng cố tình phát lệnh syscall bị cấm, nhân Linux sẽ ngay lập tức gửi tín hiệu `SIGSYS` tiêu diệt tiến trình.")
            ],
            "Kịch bản tấn công: Kẻ tấn công phát hiện một lỗ hổng Use-After-Free trong engine trình duyệt WebView (C++). Kẻ tấn công tìm cách vượt qua ASLR bằng cách khai thác một lỗ hổng rò rỉ địa chỉ bộ nhớ (Memory Leakage Bug) để tính toán vị trí cơ sở của `libc.so`, sau đó xây dựng chuỗi ROP Chain. Tuy nhiên, khi chuỗi ROP cố gắng gọi syscall cấm để vô hiệu hóa sandbox, Seccomp-BPF lập tức ngắt tiến trình! Phòng thủ: Biên dịch mã nguồn native với đầy đủ cờ bảo vệ: `-fstack-protector-all`, `-D_FORTIFY_SOURCE=2`, và kích hoạt Clang Control Flow Integrity (CFI).",
            "Trong phần thực hành, chúng ta sẽ kiểm tra cấu hình ASLR và trạng thái Seccomp của tiến trình Android qua ADB shell:",
            ("bash", """# 1. Kiểm tra mức độ ngẫu nhiên hóa của ASLR trong nhân Linux
adb shell cat /proc/sys/kernel/randomize_va_space
# Giá trị 2 biểu thị ASLR đầy đủ (Full Randomization cho Stack, Heap và Mappings)

# 2. Kiểm tra bộ lọc Seccomp của một tiến trình ứng dụng
PID=$(adb shell pidof com.android.chrome)
adb shell cat /proc/$PID/status | grep -i Seccomp
# Seccomp: 2 biểu thị chế độ SECCOMP_MODE_FILTER đang kích hoạt chặt chẽ

# 3. Xem bản đồ bộ nhớ để quan sát các vùng nhớ W^X
adb shell cat /proc/$PID/maps | head -n 20 """),
            ["Luôn kích hoạt cờ bảo vệ bộ nhớ trong tệp cấu hình CMake / Android.mk.", "Kiểm tra kỹ các thư viện native của bên thứ ba để đảm bảo chúng được biên dịch với cờ PIE."],
            ["ASLR và PIE xáo trộn không gian bộ nhớ, gây khó khăn cho việc xây dựng ROP chain.", "Stack Canaries phát hiện và triệt tiêu ngay lập tức hành vi ghi đè ngăn xếp.", "Seccomp-BPF hạn chế tối đa bề mặt tấn công vào nhân Linux bằng cách chặn các syscall nguy hiểm."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Giá trị của tham số hạt nhân /proc/sys/kernel/randomize_va_space bằng bao nhiêu biểu thị rằng cơ chế ASLR đang được kích hoạt ở mức độ ngẫu nhiên hóa tối đa?", "options": ["A. 2", "B. 0", "C. 1", "D. 3"], "correct_index": 0, "explanation": "Giá trị 2 là mức độ ASLR toàn diện nhất, ngẫu nhiên hóa stack, VDSO page, shared memory và heap."},
                {"type": "FILL_BLANK", "question": "Cơ chế bảo vệ ngăn xếp chèn một giá trị bí mật trước con trỏ địa chỉ trả về để phát hiện tràn bộ đệm có tên là Stack [_____].", "blanks": [{"accepted_answers": ["Canary", "canary", "Canaries", "canaries"]}], "explanation": "Stack Canary hoạt động như một cảm biến phát hiện hành vi ghi đè ngăn xếp."},
                {"type": "MATCHING", "question": "Nối công nghệ bảo vệ bộ nhớ với nguyên lý phòng thủ:", "pairs": [{"left": "ASLR", "right": "Xáo trộn ngẫu nhiên vị trí các phân vùng trong bộ nhớ ảo"}, {"left": "W^X (DEP)", "right": "Một vùng nhớ chỉ có thể có quyền Ghi HOẶC Thực thi, không đồng thời"}, {"left": "Seccomp-BPF", "right": "Hạn chế danh sách các lời gọi hệ thống syscall được phép gọi"}] , "explanation": "Sự kết hợp của nhiều tầng phòng thủ tạo nên pháo đài bảo vệ bộ nhớ vững chắc."},
                {"type": "FILL_BLANK", "question": "Tín hiệu hệ thống do nhân Linux phát ra để tiêu diệt ngay lập tức tiến trình cố tình thực thi một syscall bị cấm bởi Seccomp là SIG[_____].", "blanks": [{"accepted_answers": ["SYS", "sys", "SIGSYS"]}], "explanation": "SIGSYS (Bad System Call) lập tức chấm dứt tiến trình vi phạm bộ lọc Seccomp."}
            ]
        ),
        (
            11,
            "Bài 2.11: Cơ Chế Cập Nhật Hệ Thống Liền Mạch (A/B Seamless Updates) & Phân Vùng Động Dynamic Partitions",
            "Nghiên cứu kiến trúc cập nhật kép A/B Seamless Updates, khôi phục khi lỗi (Rollback Prevention) và phân vùng siêu cấp Super Partition.",
            ["Hiểu kiến trúc phân vùng kép (A/B Partitions) cho phép cập nhật hệ điều hành không gián đoạn.", "Nắm vững cơ chế chuyển đổi trạng thái boot: Successful, Unbootable và Rollback Protection.", "Phân tích cấu trúc Phân vùng động (Dynamic Partitions / Super Partition) từ Android 10.", "Đánh giá các kỹ thuật phòng thủ chống hạ cấp phiên bản (Anti-Rollback Defense)."],
            [
                ("Cuộc Cách Mạng Cập Nhật Hệ Thống Liền Mạch (A/B System Updates)", "Trước Android 7.0, việc cập nhật hệ điều hành (OTA Update) là một trải nghiệm phiền toái: thiết bị phải khởi động lại vào chế độ Recovery, hiển thị biểu tượng Android mở bụng và người dùng không thể sử dụng điện thoại trong suốt 15-30 phút. Nếu quá trình cập nhật gặp sự cố (như mất điện hoặc lỗi dữ liệu), thiết bị có nguy cơ bị biến thành 'cục gạch' (Hard Brick). "
                "Từ Android 7.0, Google giới thiệu A/B (Seamless) System Updates: hệ thống duy trì hai bộ phân vùng song song (Slot A và Slot B) bao gồm `boot_a/boot_b`, `system_a/system_b`, và `vendor_a/vendor_b`. Trong khi người dùng vẫn đang sử dụng bình thường trên Slot A, hệ điều hành sẽ âm thầm tải và ghi dữ liệu cập nhật mới vào Slot B trong nền."),
                ("Quy Trình Chuyển Đổi Slot & Bảo Vệ Chống Lỗi (Self-Healing)", "Khi quá trình ghi dữ liệu nền vào Slot B hoàn tất, người dùng chỉ cần khởi động lại máy. Bootloader sẽ chuyển cờ ưu tiên khởi động sang Slot B. "
                "Sau khi nạp xong, tiến trình `update_engine` phải liên lạc với framework để đánh giá xem hệ thống có hoạt động ổn định hay không. Nếu hệ thống khởi động thành công, Slot B được đánh dấu là `successful`. "
                "Nếu xảy ra lỗi crash nghiêm trọng (Kernel Panic hoặc Bootloop), Bootloader sẽ đếm số lần khởi động thất bại: sau 3 lần thử không thành công, hệ thống sẽ tự động quay lui (Rollback) 100% về Slot A trước đó. Người dùng hoàn toàn an toàn và thiết bị không bao giờ bị brick!"),
                ("Phân Vùng Động (Dynamic Partitions) & Cấu Trúc Super Partition", "Từ Android 10, để tối ưu hóa không gian lưu trữ và linh hoạt phân bổ kích thước phân vùng, Google giới thiệu Dynamic Partitions. Thay vì chia cứng các phân vùng thành kích thước cố định từ lúc xuất xưởng, một phân vùng vật lý khổng lồ có tên là `super` được tạo ra. Bên trong `super`, trình điều khiển Device Mapper của nhân Linux (`dm-linear`) sẽ linh hoạt cấp phát kích thước cho các phân vùng con (`system`, `vendor`, `product`) theo nhu cầu thực tế của từng bản cập nhật OTA.")
            ],
            "Kịch bản tấn công: Kẻ tấn công cố tình hạ cấp firmware (Downgrade Attack) về một phiên bản hệ điều hành cũ hơn có chứa lỗ hổng bảo mật nghiêm trọng đã biết, nhằm mục đích khai thác lỗ hổng đó để bẻ khóa thiết bị. Phòng thủ: Cơ chế Anti-Rollback Protection của AVB sử dụng một bộ đếm số phiên bản (Security Patch Rollback Index) được ghi vào vùng nhớ phần cứng an toàn (Replay Protected Memory Block - RPMB). Nếu Bootloader phát hiện bản cập nhật có Rollback Index nhỏ hơn giá trị trong phần cứng, nó sẽ từ chối nạp firmware ngay lập tức.",
            "Trong phần thực hành, chúng ta sẽ sử dụng ADB và fastboot để kiểm tra slot hiện tại và cấu hình phân vùng động của thiết bị:",
            ("bash", """# 1. Kiểm tra slot hiện tại đang hoạt động (_a hay _b)
adb shell getprop ro.boot.slot_suffix

# 2. Xem thông tin phân vùng super và dung lượng dynamic partitions
adb shell lpdump

# 3. Tra cứu trạng thái cập nhật OTA của update_engine
adb shell dumpsys update_engine """),
            ["Không bao giờ cố gắng hạ cấp thiết bị khi chưa kiểm tra chính sách Rollback Index của nhà sản xuất.", "Hiểu rõ cơ chế A/B để kiểm tra chính xác phân vùng đang được nạp khi thực hiện phân tích pháp y số (Digital Forensics)."],
            ["A/B System Updates cho phép cập nhật hệ điều hành ngầm mà không gây gián đoạn sử dụng.", "Cơ chế tự động rollback về slot cũ bảo vệ thiết bị hoàn toàn khỏi nguy cơ bootloop.", "Anti-Rollback bảo vệ thiết bị khỏi các cuộc tấn công hạ cấp firmware độc hại."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Thuộc tính hệ thống nào trong Android được sử dụng để kiểm tra xem thiết bị hiện đang khởi động từ Slot A hay Slot B trong kiến trúc cập nhật liền mạch?", "options": ["A. ro.boot.slot_suffix", "B. ro.boot.slot", "C. ro.system.active_slot", "D. ro.build.slot_id"], "correct_index": 0, "explanation": "ro.boot.slot_suffix trả về chuỗi '_a' hoặc '_b' biểu thị slot đang hoạt động."},
                {"type": "FILL_BLANK", "question": "Tên phân vùng vật lý khổng lồ được giới thiệu từ Android 10 chứa các phân vùng động (Dynamic Partitions) co giãn kích thước là [_____].", "blanks": [{"accepted_answers": ["super", "super.img", "Super"]}], "explanation": "Phân vùng 'super' chứa system, vendor, product được quản lý linh hoạt bởi dm-linear."},
                {"type": "MATCHING", "question": "Nối khái niệm cập nhật hệ thống với chức năng tương ứng:", "pairs": [{"left": "A/B Updates", "right": "Cập nhật hệ điều hành trong nền và chuyển đổi slot khi khởi động lại"}, {"left": "Dynamic Partitions", "right": "Phân bổ dung lượng linh hoạt cho các phân vùng bên trong partition super"}, {"left": "Anti-Rollback", "right": "Ngăn chặn việc nạp firmware cũ có chứa lỗ hổng bảo mật"}] , "explanation": "Kiến trúc cập nhật hiện đại vừa an toàn vừa tối ưu không gian lưu trữ."},
                {"type": "FILL_BLANK", "question": "Tiến trình daemon trong hệ thống Android chịu trách nhiệm tải về và ghi gói tin cập nhật OTA vào slot đối diện trong nền có tên là [_____].", "blanks": [{"accepted_answers": ["update_engine", "UpdateEngine"]}], "explanation": "update_engine là tiến trình nền tảng thực thi quy trình cập nhật A/B OTA."}
            ]
        )
    ]

    for spec in ch2_specs + ch2_specs_rest:
        pos, title, summary, objs, theory, attack_def, lab_text, code_snp, pitfalls, summaries, quiz = spec
        vid_idx = (pos - 1) % len(VIDEO_CACHE)
        vurl = VIDEO_CACHE[vid_idx]["url"]

        md_content = generate_lesson_markdown(
            lesson_num=f"2.{pos}",
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
