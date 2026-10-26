"""Assessment builder for Android Security Master Course (AND801).

Generates:
- 5 Chapter Quizzes (10 questions each = 50 questions)
- 1 Final Comprehensive Exam (20 questions with shuffle_choices=True and shuffle_questions=True)
Total: 70 detailed questions with explanations and choices.
"""

from typing import Any


def get_all_assessments_data() -> list[dict[str, Any]]:
    """Return assessment metadata and associated questions."""

    ch1_questions = [
        {
            "content": "Kiến trúc hệ điều hành Android được xây dựng trên nền tảng nhân (kernel) hệ điều hành nào?",
            "difficulty": "REMEMBER",
            "learning_objective": "Nhận biết nhân Linux trong kiến trúc Android",
            "explanation": "Android sử dụng nhân Linux (Linux Kernel) tùy biến làm lớp trừu tượng phần cứng, quản lý bộ nhớ, tiến trình và bảo mật.",
            "choices": [
                {"content": "A. Nhân Linux (Linux Kernel)", "is_correct": True},
                {"content": "B. Nhân FreeBSD / Mach Kernel", "is_correct": False},
                {"content": "C. Nhân Windows NT", "is_correct": False},
                {"content": "D. Nhân XNU Hybrid Kernel", "is_correct": False},
            ],
        },
        {
            "content": "Tiến trình gốc (parent process) nào trong Android chịu trách nhiệm nạp trước toàn bộ các lớp framework và sinh ra các tiến trình ứng dụng con thông qua kỹ thuật fork()?",
            "difficulty": "REMEMBER",
            "learning_objective": "Hiểu vai trò của tiến trình Zygote",
            "explanation": "Zygote là tiến trình gốc khởi động máy ảo ART, tải sẵn framework classes và tạo tiến trình ứng dụng mới bằng cách gọi fork() giúp tiết kiệm RAM.",
            "choices": [
                {"content": "A. Zygote", "is_correct": True},
                {"content": "B. init", "is_correct": False},
                {"content": "C. system_server", "is_correct": False},
                {"content": "D. servicemanager", "is_correct": False},
            ],
        },
        {
            "content": "Công nghệ biên dịch mã nguồn nào được máy ảo Android Runtime (ART) giới thiệu từ Android 5.0 để biên dịch toàn bộ mã DEX thành mã máy AOT trước khi ứng dụng chạy?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Phân biệt cơ chế biên dịch AOT và JIT trong ART",
            "explanation": "ART giới thiệu cơ chế Ahead-Of-Time (AOT) compilation thông qua tiện ích dex2oat để biên dịch bytecode thành mã máy nhị phân (.oat/.elf).",
            "choices": [
                {"content": "A. Ahead-Of-Time (AOT) Compilation", "is_correct": True},
                {"content": "B. Just-In-Time (JIT) Compilation thuần túy", "is_correct": False},
                {"content": "C. Dalvik Bytecode Interpreter", "is_correct": False},
                {"content": "D. Transpiler LLVM to Java", "is_correct": False},
            ],
        },
        {
            "content": "Thành phần ứng dụng Android nào thực hiện các tác vụ nền kéo dài mà không cung cấp giao diện đồ họa người dùng?",
            "difficulty": "REMEMBER",
            "learning_objective": "Phân loại 4 thành phần ứng dụng Android cốt lõi",
            "explanation": "Service chạy ngầm để thực hiện các thao tác dài hạn như tải tệp, phát nhạc, đồng bộ dữ liệu mà không có giao diện hiển thị.",
            "choices": [
                {"content": "A. Service", "is_correct": True},
                {"content": "B. Activity", "is_correct": False},
                {"content": "C. BroadcastReceiver", "is_correct": False},
                {"content": "D. ContentProvider", "is_correct": False},
            ],
        },
        {
            "content": "Phương thức nào trong vòng đời Activity được gọi ngay trước khi Activity hiển thị và sẵn sàng tương tác trực tiếp với người dùng (tiến vào Foreground)?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Làm chủ vòng đời Activity Lifecycle",
            "explanation": "onResume() được gọi khi Activity chuyển sang trạng thái hoạt động trên cùng (Foreground) và nhận sự kiện tương tác từ người dùng.",
            "choices": [
                {"content": "A. onResume()", "is_correct": True},
                {"content": "B. onStart()", "is_correct": False},
                {"content": "C. onCreate()", "is_correct": False},
                {"content": "D. onPause()", "is_correct": False},
            ],
        },
        {
            "content": "Thuộc tính nào trong tệp cấu hình AndroidManifest.xml quyết định một thành phần ứng dụng có thể được gọi bởi các ứng dụng bên thứ ba hay không?",
            "difficulty": "APPLY",
            "learning_objective": "Cấu hình an toàn thuộc tính android:exported",
            "explanation": "android:exported=\"true\" cho phép ứng dụng bên ngoài kích hoạt thành phần; gán \"false\" giúp giới hạn thành phần chỉ hoạt động nội bộ.",
            "choices": [
                {"content": "A. android:exported", "is_correct": True},
                {"content": "B. android:enabled", "is_correct": False},
                {"content": "C. android:permission", "is_correct": False},
                {"content": "D. android:process", "is_correct": False},
            ],
        },
        {
            "content": "Cơ chế bảo vệ nào giúp tránh tình trạng rò rỉ bộ nhớ (Memory Leak) khi truyền đối tượng Fragment vào một Thread hoặc Coroutine bất đồng bộ?",
            "difficulty": "APPLY",
            "learning_objective": "Quản lý vòng đời an toàn và tránh rò rỉ bộ nhớ",
            "explanation": "Sử dụng viewLifecycleOwner kết hợp với lifecycleScope tự động hủy coroutine khi view của Fragment bị hủy, ngăn chặn Memory Leak.",
            "choices": [
                {"content": "A. Sử dụng viewLifecycleOwner.lifecycleScope", "is_correct": True},
                {"content": "B. Giữ tham chiếu tĩnh (static reference) của Activity Context", "is_correct": False},
                {"content": "C. Tạo Thread mới không kiểm tra isAdded()", "is_correct": False},
                {"content": "D. Gọi System.gc() liên tục trong onPause()", "is_correct": False},
            ],
        },
        {
            "content": "Tệp kê khai bắt buộc phải có trong mọi ứng dụng Android để khai báo quyền hạn, thành phần và phiên bản SDK là gì?",
            "difficulty": "REMEMBER",
            "learning_objective": "Cấu trúc tệp AndroidManifest.xml",
            "explanation": "AndroidManifest.xml là tệp mô tả gốc chứa toàn bộ siêu dữ liệu kiến trúc của một ứng dụng Android.",
            "choices": [
                {"content": "A. AndroidManifest.xml", "is_correct": True},
                {"content": "B. build.gradle.kts", "is_correct": False},
                {"content": "C. proguard-rules.pro", "is_correct": False},
                {"content": "D. settings.gradle", "is_correct": False},
            ],
        },
        {
            "content": "Thành phần nào cung cấp giao diện chuẩn hóa (dựa trên URI `content://`) để chia sẻ dữ liệu có cấu trúc giữa các ứng dụng một cách an toàn?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Hiểu kiến trúc ContentProvider",
            "explanation": "ContentProvider là cơ chế chuẩn trong Android để đóng gói và cung cấp quyền truy cập bảng dữ liệu qua giao diện ContentResolver URI.",
            "choices": [
                {"content": "A. ContentProvider", "is_correct": True},
                {"content": "B. IntentFilter", "is_correct": False},
                {"content": "C. SharedPreferences", "is_correct": False},
                {"content": "D. Room Database Trực Tiếp", "is_correct": False},
            ],
        },
        {
            "content": "Trong kiến trúc Android hiện đại, công cụ biên dịch tối ưu hóa mã nguồn (Minification, Obfuscation, Dead code stripping) mặc định của Google là gì?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Nhận biết công cụ tối ưu hóa R8 / D8",
            "explanation": "R8 là công cụ thu nhỏ và làm rối mã nguồn mặc định được tích hợp trong Android Gradle Plugin, thay thế cho ProGuard.",
            "choices": [
                {"content": "A. R8 Compiler", "is_correct": True},
                {"content": "B. ProGuard 4.0 Legacy", "is_correct": False},
                {"content": "C. DexGuard Commercial", "is_correct": False},
                {"content": "D. Jack and Jill Toolchain", "is_correct": False},
            ],
        },
    ]

    ch2_questions = [
        {
            "content": "Nguyên lý cách ly cốt lõi của Android Application Sandbox dựa trên tính năng nào của nhân Linux?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Mô hình Sandbox dựa trên Linux UID/GID",
            "explanation": "Mỗi ứng dụng Android khi cài đặt được cấp phát một User ID (UID) duy nhất trong Linux, cô lập tài nguyên tệp và bộ nhớ của ứng dụng đó.",
            "choices": [
                {"content": "A. Gán mỗi ứng dụng một Linux UID/GID riêng biệt", "is_correct": True},
                {"content": "B. Chạy mỗi ứng dụng trong một Docker container riêng", "is_correct": False},
                {"content": "C. Mã hóa toàn bộ mã nguồn Java bằng mật mã AES", "is_correct": False},
                {"content": "D. Giới hạn số lượng luồng thực thi trong máy ảo", "is_correct": False},
            ],
        },
        {
            "content": "Cấp độ bảo vệ quyền hạn (protectionLevel) nào chỉ cho phép các ứng dụng được ký bởi cùng một chứng chỉ số của nhà phát triển sử dụng?",
            "difficulty": "REMEMBER",
            "learning_objective": "Phân loại permission protectionLevel trong Android",
            "explanation": "protectionLevel=\"signature\" giới hạn quyền hạn chỉ cấp cho ứng dụng được ký cùng Developer Signing Key.",
            "choices": [
                {"content": "A. signature", "is_correct": True},
                {"content": "B. normal", "is_correct": False},
                {"content": "C. dangerous", "is_correct": False},
                {"content": "D. signatureOrSystem", "is_correct": False},
            ],
        },
        {
            "content": "Trình điều khiển thiết bị nhân Linux (Kernel Driver) đặc biệt nào đóng vai trò xương sống cho cơ chế truyền thông liên tiến trình (IPC) trong Android?",
            "difficulty": "REMEMBER",
            "learning_objective": "Xác định Binder IPC Kernel Driver",
            "explanation": "/dev/binder là trình điều khiển thiết bị IPC của Android, triển khai bộ nhớ chia sẻ và chuyển đổi dữ liệu an toàn giữa các tiến trình.",
            "choices": [
                {"content": "A. /dev/binder", "is_correct": True},
                {"content": "B. /dev/ashmem", "is_correct": False},
                {"content": "C. /dev/ion", "is_correct": False},
                {"content": "D. /dev/null", "is_correct": False},
            ],
        },
        {
            "content": "Cơ chế nào được Binder sử dụng để xác thực danh tính người gọi IPC nhằm ngăn chặn việc giả mạo danh tính từ phía ứng dụng khách?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Xác thực danh tính gọi Binder IPC",
            "explanation": "Binder.getCallingUid() và Binder.getCallingPid() được kernel Binder gán trực tiếp, phía client không thể can thiệp hay giả mạo.",
            "choices": [
                {"content": "A. Binder.getCallingUid() và Binder.getCallingPid()", "is_correct": True},
                {"content": "B. Gửi chuỗi JWT token trong Intent payload", "is_correct": False},
                {"content": "C. Đọc tên package từ Context.getPackageName()", "is_correct": False},
                {"content": "D. Kiểm tra trường Authorization trong HTTP Header", "is_correct": False},
            ],
        },
        {
            "content": "Hệ thống kiểm soát truy cập bắt buộc (MAC) nào được Android tích hợp từ phiên bản 4.4 và kích hoạt chế độ Enforcing trên toàn bộ thiết bị từ Android 5.0?",
            "difficulty": "REMEMBER",
            "learning_objective": "Nhận biết kiến trúc SELinux trên Android",
            "explanation": "SELinux (Security-Enhanced Linux) áp dụng chính sách Type Enforcement để giới hạn hành vi của mọi tiến trình ngay cả khi tiến trình đó có quyền root.",
            "choices": [
                {"content": "A. SELinux (Security-Enhanced Linux)", "is_correct": True},
                {"content": "B. AppArmor", "is_correct": False},
                {"content": "C. Windows Defender SmartScreen", "is_correct": False},
                {"content": "D. grsecurity PAX", "is_correct": False},
            ],
        },
        {
            "content": "Lệnh dòng lệnh nào trên Android cho phép kiểm tra ngữ cảnh bảo mật SELinux context của một tiến trình hoặc tệp tin?",
            "difficulty": "APPLY",
            "learning_objective": "Kiểm tra ngữ cảnh SELinux bằng dòng lệnh",
            "explanation": "Tùy chọn -Z (ví dụ: `ps -A -Z` hoặc `ls -laZ`) hiển thị nhãn SELinux (user:role:type:mls) của đối tượng.",
            "choices": [
                {"content": "A. ps -A -Z hoặc ls -laZ", "is_correct": True},
                {"content": "B. uname -a", "is_correct": False},
                {"content": "C. top -n 1", "is_correct": False},
                {"content": "D. chmod 777", "is_correct": False},
            ],
        },
        {
            "content": "Khai báo nào trong AndroidManifest.xml cho phép hai ứng dụng khác nhau có thể chạy chung trong cùng một tiến trình Linux và truy cập trực tiếp dữ liệu của nhau?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Hiểu cơ chế sharedUserId và rủi ro",
            "explanation": "android:sharedUserId cho phép các ứng dụng ký cùng khóa dùng chung một UID và không gian dữ liệu.",
            "choices": [
                {"content": "A. android:sharedUserId", "is_correct": True},
                {"content": "B. android:process", "is_correct": False},
                {"content": "C. android:sharedLibrary", "is_correct": False},
                {"content": "D. android:multiProcess", "is_correct": False},
            ],
        },
        {
            "content": "Từ phiên bản Android 10 (API 29), cơ chế lưu trữ nào được áp dụng bắt buộc nhằm ngăn chặn việc ứng dụng đọc tự do tệp tin của ứng dụng khác trong bộ nhớ ngoài?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Nắm vững cơ chế Scoped Storage",
            "explanation": "Scoped Storage cô lập quyền truy cập tệp ngoài vào thư mục riêng của ứng dụng và yêu cầu sử dụng MediaStore/SAF cho các tệp chung.",
            "choices": [
                {"content": "A. Scoped Storage", "is_correct": True},
                {"content": "B. Full Disk Encryption", "is_correct": False},
                {"content": "C. Adoptable Storage", "is_correct": False},
                {"content": "D. Encrypted Virtual Disk", "is_correct": False},
            ],
        },
        {
            "content": "Loại quyền hạn (Permission Group) nào bắt buộc phải yêu cầu sự đồng ý tường minh của người dùng tại thời điểm chạy (Runtime Permission Dialog) từ Android 6.0?",
            "difficulty": "REMEMBER",
            "learning_objective": "Phân biệt Dangerous vs Normal Permissions",
            "explanation": "Dangerous Permissions (như CAMERA, READ_CONTACTS, ACCESS_FINE_LOCATION) phải được cấp phép lúc chạy bởi người dùng.",
            "choices": [
                {"content": "A. Dangerous Permissions", "is_correct": True},
                {"content": "B. Normal Permissions", "is_correct": False},
                {"content": "C. Signature Permissions", "is_correct": False},
                {"content": "D. Install-time Permissions", "is_correct": False},
            ],
        },
        {
            "content": "Chính sách SELinux đang ở trạng thái nào khi hệ thống chỉ ghi lại log vi phạm vào dmesg/audit mà KHÔNG thực sự ngăn chặn hành động trái phép?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Phân biệt SELinux Permissive vs Enforcing",
            "explanation": "Permissive mode chỉ giám sát và ghi log cảnh báo; Enforcing mode thực sự chặn đứng hành vi vi phạm chính sách.",
            "choices": [
                {"content": "A. Permissive Mode", "is_correct": True},
                {"content": "B. Enforcing Mode", "is_correct": False},
                {"content": "C. Disabled Mode", "is_correct": False},
                {"content": "D. Strict Mode", "is_correct": False},
            ],
        },
    ]

    ch3_questions = [
        {
            "content": "Định dạng tệp nào được sử dụng để đóng gói toàn bộ mã bytecode DEX, tài nguyên và chứng chỉ số của một ứng dụng Android trước khi cài đặt lên thiết bị?",
            "difficulty": "REMEMBER",
            "learning_objective": "Cấu trúc gói phần mềm APK",
            "explanation": "APK (Android Package) thực chất là một tệp lưu trữ nén định dạng ZIP chứa classes.dex, resources.arsc, AndroidManifest.xml và chữ ký số.",
            "choices": [
                {"content": "A. APK (Android Package)", "is_correct": True},
                {"content": "B. JAR (Java Archive)", "is_correct": False},
                {"content": "C. IPA (iOS App Store Package)", "is_correct": False},
                {"content": "D. EXE (Windows Executable)", "is_correct": False},
            ],
        },
        {
            "content": "Công cụ dòng lệnh mã nguồn mở nào là chuẩn mực hàng đầu để dịch ngược và lắp ráp lại (disassemble & reassemble) tệp APK về dạng mã trung gian Smali?",
            "difficulty": "REMEMBER",
            "learning_objective": "Sử dụng công cụ Apktool trong dịch ngược",
            "explanation": "Apktool giải mã tệp tài nguyên XML nhị phân và dịch ngược classes.dex thành mã hợp ngữ Smali, đồng thời cho phép đóng gói lại (rebuild).",
            "choices": [
                {"content": "A. Apktool", "is_correct": True},
                {"content": "B. ProGuard", "is_correct": False},
                {"content": "C. Wireshark", "is_correct": False},
                {"content": "D. ADB Server", "is_correct": False},
            ],
        },
        {
            "content": "Trong ngôn ngữ hợp ngữ Smali của máy ảo Dalvik/ART, thanh ghi lưu trữ con trỏ tham chiếu đến chính đối tượng hiện tại (tương đương `this` trong Java) là gì?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Cú pháp Smali và thanh ghi tham số",
            "explanation": "Trong phương thức non-static, tham số đầu tiên p0 luôn lưu trữ tham chiếu đến đối tượng `this`.",
            "choices": [
                {"content": "A. p0", "is_correct": True},
                {"content": "B. v0", "is_correct": False},
                {"content": "C. r0", "is_correct": False},
                {"content": "D. ebp", "is_correct": False},
            ],
        },
        {
            "content": "Lệnh hợp ngữ Smali nào thực hiện việc so sánh hai thanh ghi và nhảy đến nhãn đích nếu giá trị của thanh ghi bằng 0?",
            "difficulty": "APPLY",
            "learning_objective": "Kỹ thuật patch mã Smali rẽ nhánh",
            "explanation": "if-eqz vA, :label nhảy tới nhãn :label nếu giá trị trong thanh ghi vA bằng 0.",
            "choices": [
                {"content": "A. if-eqz vA, :label", "is_correct": True},
                {"content": "B. if-nez vA, :label", "is_correct": False},
                {"content": "C. goto :label", "is_correct": False},
                {"content": "D. return-void", "is_correct": False},
            ],
        },
        {
            "content": "Công cụ phân tích tĩnh có giao diện đồ họa GUI phổ biến nhất giúp chuyển đổi tệp DEX/APK trực tiếp về mã nguồn Java dễ đọc là gì?",
            "difficulty": "REMEMBER",
            "learning_objective": "Sử dụng công cụ JADX-GUI",
            "explanation": "JADX-GUI dịch ngược mã bytecode DEX thành mã nguồn Java tường minh kèm tính năng tìm kiếm tham chiếu và biểu thức chính quy mạnh mẽ.",
            "choices": [
                {"content": "A. JADX-GUI", "is_correct": True},
                {"content": "B. OllyDbg", "is_correct": False},
                {"content": "C. Nmap", "is_correct": False},
                {"content": "D. Metasploit Console", "is_correct": False},
            ],
        },
        {
            "content": "Lỗ hổng bảo mật nào xảy ra khi một Activity công khai (`exported=true`) nhận một Intent từ ứng dụng ngoài và khởi chạy trực tiếp Intent đó mà không qua xác thực?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Phát hiện lỗ hổng Intent Redirection / Intent Injection",
            "explanation": "Intent Redirection xảy ra khi ứng dụng chuyển tiếp trực tiếp một Intent không tin cậy để truy cập các thành phần nội bộ nhạy cảm.",
            "choices": [
                {"content": "A. Intent Redirection / Intent Injection", "is_correct": True},
                {"content": "B. Buffer Overflow", "is_correct": False},
                {"content": "C. SQL Injection trong URL", "is_correct": False},
                {"content": "D. Cross-Site Scripting (XSS)", "is_correct": False},
            ],
        },
        {
            "content": "Cờ nào trong AndroidManifest.xml nếu bị bật `android:allowBackup=\"true\"` sẽ cho phép kẻ tấn công trích xuất toàn bộ dữ liệu nội bộ của ứng dụng qua lệnh `adb backup`?",
            "difficulty": "APPLY",
            "learning_objective": "Cấu hình an toàn sao lưu dữ liệu allowBackup",
            "explanation": "android:allowBackup=\"true\" cho phép sao lưu dữ liệu sandbox qua ADB; cần tắt (false) hoặc cấu hình backup_rules loại bỏ dữ liệu nhạy cảm.",
            "choices": [
                {"content": "A. android:allowBackup", "is_correct": True},
                {"content": "B. android:debuggable", "is_correct": False},
                {"content": "C. android:extractNativeLibs", "is_correct": False},
                {"content": "D. android:hardwareAccelerated", "is_correct": False},
            ],
        },
        {
            "content": "Phương thức kiểm thử tự động toàn diện tích hợp kiểm tra cả mã nguồn APK, phát hiện thư viện bên thứ ba chứa lỗ hổng và đánh giá điểm CVSS là nền tảng nào?",
            "difficulty": "REMEMBER",
            "learning_objective": "Quét tự động với Mobile Security Framework (MobSF)",
            "explanation": "MobSF (Mobile Security Framework) là giải pháp kiểm thử bảo mật tự động mã nguồn mở hàng đầu cho Android và iOS.",
            "choices": [
                {"content": "A. Mobile Security Framework (MobSF)", "is_correct": True},
                {"content": "B. SonarQube Standard", "is_correct": False},
                {"content": "C. Nessus Vulnerability Scanner", "is_correct": False},
                {"content": "D. Wireshark Network Analyzer", "is_correct": False},
            ],
        },
        {
            "content": "Kỹ thuật nào được các lập trình viên sử dụng để làm khó quá trình phân tích tĩnh bằng cách thay đổi cấu trúc mã nguồn, đổi tên lớp/phương thức thành các ký tự vô nghĩa (a, b, c)?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Khái niệm làm rối mã nguồn Obfuscation",
            "explanation": "Code Obfuscation (Làm rối mã) xóa bỏ siêu dữ liệu tên gọi và biến đổi luồng điều khiển nhằm chống lại dịch ngược.",
            "choices": [
                {"content": "A. Code Obfuscation (Làm rối mã nguồn)", "is_correct": True},
                {"content": "B. Code Refactoring (Tái cấu trúc mã)", "is_correct": False},
                {"content": "C. Code Formatting (Định dạng mã chuẩn)", "is_correct": False},
                {"content": "D. Unit Testing (Viết kiểm thử tự động)", "is_correct": False},
            ],
        },
        {
            "content": "Lệnh nào được sử dụng sau khi chỉnh sửa tệp Smali và đóng gói lại APK bằng Apktool để căn chỉnh giới hạn 4-byte (4-byte alignment) trước khi ký số?",
            "difficulty": "APPLY",
            "learning_objective": "Quy trình căn chỉnh zipalign gói APK",
            "explanation": "zipalign đảm bảo toàn bộ tài nguyên không nén được căn lề 4 byte so với đầu tệp, giúp hệ thống mmap trực tiếp vào bộ nhớ RAM.",
            "choices": [
                {"content": "A. zipalign -p -f -v 4 app-unsigned.apk app-aligned.apk", "is_correct": True},
                {"content": "B. apksigner sign --ks my.keystore app.apk", "is_correct": False},
                {"content": "C. adb install -r app.apk", "is_correct": False},
                {"content": "D. keytool -genkey -v -keystore my.keystore", "is_correct": False},
            ],
        },
    ]

    ch4_questions = [
        {
            "content": "Khung công cụ can thiệp động (Dynamic Binary Instrumentation Framework) phổ biến nhất hiện nay cho phép tiêm mã JavaScript vào tiến trình lúc chạy là gì?",
            "difficulty": "REMEMBER",
            "learning_objective": "Nhận biết công cụ Frida",
            "explanation": "Frida sử dụng engine JavaScript (V8 hoặc QuickJS) được tiêm vào tiến trình để hook hàm, ghi đè logic và trích xuất dữ liệu lúc chạy.",
            "choices": [
                {"content": "A. Frida", "is_correct": True},
                {"content": "B. Xposed Framework Legacy", "is_correct": False},
                {"content": "C. Valgrind", "is_correct": False},
                {"content": "D. Wireshark Capture", "is_correct": False},
            ],
        },
        {
            "content": "Trong Frida Java Bridge, phương thức nào được gọi để bắt buộc luồng thực thi chạy trong ngữ cảnh máy ảo Android VM trước khi tương tác với các lớp Java?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Sử dụng API Java.perform() trong Frida",
            "explanation": "Java.perform(function() { ... }) bảo đảm luồng hiện tại được gắn (attached) vào môi trường máy ảo Java VM.",
            "choices": [
                {"content": "A. Java.perform()", "is_correct": True},
                {"content": "B. Java.use()", "is_correct": False},
                {"content": "C. Java.choose()", "is_correct": False},
                {"content": "D. Java.cast()", "is_correct": False},
            ],
        },
        {
            "content": "Cú pháp Frida nào cho phép thay thế hoàn toàn việc thực thi của phương thức `isDeviceRooted()` trên lớp `com.backend.SecurityCheck` để luôn trả về giá trị false?",
            "difficulty": "APPLY",
            "learning_objective": "Kỹ thuật ghi đè hàm (Method Overwriting) bằng Frida",
            "explanation": "Gán `targetClass.isDeviceRooted.implementation = function() { return false; };` ghi đè hoàn toàn nội dung hàm đích.",
            "choices": [
                {"content": "A. targetClass.isDeviceRooted.implementation = function() { return false; };", "is_correct": True},
                {"content": "B. targetClass.isDeviceRooted.hook = false;", "is_correct": False},
                {"content": "C. targetClass.isDeviceRooted = function() { return null; };", "is_correct": False},
                {"content": "D. Java.override('com.backend.SecurityCheck', 'isDeviceRooted', false);", "is_correct": False},
            ],
        },
        {
            "content": "Cơ chế bảo mật nào trong ứng dụng Android ràng buộc chặt chẽ chứng chỉ SSL/TLS hoặc mã băm Public Key của máy chủ nhằm triệt tiêu tấn công Man-in-the-Middle (MitM)?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Khái niệm và vai trò của SSL/TLS Pinning",
            "explanation": "SSL/TLS Pinning chỉ chấp nhận khóa công khai đã được xác định trước, ngăn chặn việc kẻ tấn công cài chứng chỉ CA giả mạo để đọc trộm HTTPS.",
            "choices": [
                {"content": "A. SSL/TLS Pinning (Ghim chứng chỉ số)", "is_correct": True},
                {"content": "B. Dynamic Proxy Forwarding", "is_correct": False},
                {"content": "C. Cleartext HTTP Traffic", "is_correct": False},
                {"content": "D. DNS over HTTPS (DoH)", "is_correct": False},
            ],
        },
        {
            "content": "Từ phiên bản Android 7.0 (API 24), tệp cấu hình bảo mật mạng nào cho phép nhà phát triển khai báo các chứng chỉ số người dùng (User CA) được tin cậy trong môi trường kiểm thử?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Cấu hình Network Security Config trong Android",
            "explanation": "res/xml/network_security_config.xml cho phép định nghĩa các chứng chỉ tin cậy (System, User) và cấu hình cấm lưu lượng văn bản rõ (cleartext).",
            "choices": [
                {"content": "A. network_security_config.xml", "is_correct": True},
                {"content": "B. strings.xml", "is_correct": False},
                {"content": "C. security_policies.json", "is_correct": False},
                {"content": "D. webview_whitelist.xml", "is_correct": False},
            ],
        },
        {
            "content": "Công cụ dòng lệnh dựa trên nền tảng Frida cung cấp giao diện tương tác tức thì (CLI) để bypass SSL Pinning, Root Detection và dò tìm vùng nhớ mà không cần viết script là gì?",
            "difficulty": "REMEMBER",
            "learning_objective": "Sử dụng công cụ Objection",
            "explanation": "Objection là bộ công cụ mobile security testing runtime exploration dựa trên Frida do SensePost phát triển.",
            "choices": [
                {"content": "A. Objection", "is_correct": True},
                {"content": "B. Burp Suite Professional", "is_correct": False},
                {"content": "C. Ghidra SRE", "is_correct": False},
                {"content": "D. IDA Pro", "is_correct": False},
            ],
        },
        {
            "content": "Dấu hiệu nào trong hệ thống tệp Android thường được các ứng dụng kiểm tra để phát hiện xem thiết bị đã bị chiếm quyền quản trị tối cao (Root) hay chưa?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Cơ chế phát hiện Root (Root Detection)",
            "explanation": "Sự hiện diện của tệp thực thi /system/bin/su, /system/xbin/su hoặc các ứng dụng quản lý root như Magisk là dấu hiệu chính của thiết bị đã root.",
            "choices": [
                {"content": "A. Tồn tại tệp nhị phân 'su' trong /system/bin hoặc /system/xbin", "is_correct": True},
                {"content": "B. Tồn tại thư mục /sdcard/Download", "is_correct": False},
                {"content": "C. Màn hình thiết bị có độ phân giải Full HD", "is_correct": False},
                {"content": "D. Ứng dụng có kết nối Internet qua Wi-Fi", "is_correct": False},
            ],
        },
        {
            "content": "Khi một ứng dụng kiểm tra tính toàn vẹn chữ ký số lúc chạy bằng cách so sánh mã băm SHA-256 của chữ ký với chuỗi cố định, kỹ thuật can thiệp động nào có thể vượt qua kiểm tra này?",
            "difficulty": "APPLY",
            "learning_objective": "Bypass Signature Verification lúc chạy",
            "explanation": "Hook hàm getPackageInfo() hoặc GET_SIGNING_CERTIFICATES bằng Frida để trả về chuỗi byte của chữ ký số hợp lệ gốc.",
            "choices": [
                {"content": "A. Dùng Frida hook PackageManager.getPackageInfo() để trả về chữ ký số gốc", "is_correct": True},
                {"content": "B. Đổi tên tệp APK trên máy tính", "is_correct": False},
                {"content": "C. Tắt kết nối Internet của thiết bị", "is_correct": False},
                {"content": "D. Khởi động lại thiết bị vào chế độ Safe Mode", "is_correct": False},
            ],
        },
        {
            "content": "Lệnh nào trong tiện ích objection cho phép tự động vô hiệu hóa toàn bộ cơ chế SSL Pinning của hầu hết các thư viện mạng (OkHttp, TrustManager) chỉ bằng 1 dòng lệnh?",
            "difficulty": "APPLY",
            "learning_objective": "Lệnh bypass SSL pinning trong objection",
            "explanation": "Lệnh `android sslpinning disable` trong console của Objection tự động tiêm hook vào các triển khai TrustManager phổ biến.",
            "choices": [
                {"content": "A. android sslpinning disable", "is_correct": True},
                {"content": "B. bypass all certs", "is_correct": False},
                {"content": "C. network proxy set burp", "is_correct": False},
                {"content": "D. memory dump ssl_keys", "is_correct": False},
            ],
        },
        {
            "content": "Để chặn bắt lưu lượng mạng của ứng dụng sử dụng Flutter trên Android bằng Burp Suite, kỹ thuật nào bắt buộc phải thực hiện vì Flutter tự nhúng BoringSSL và bỏ qua proxy hệ thống?",
            "difficulty": "APPLY",
            "learning_objective": "Chặn bắt gói tin mạng Flutter qua Frida Hooking",
            "explanation": "Flutter bỏ qua cấu hình proxy của hệ thống; chuyên gia phải hook hàm ssl_crypto_x509_session_verify_cert_chain trong libflutter.so.",
            "choices": [
                {"content": "A. Dùng Frida hook hàm xác minh chứng chỉ native trong libflutter.so", "is_correct": True},
                {"content": "B. Chỉ cần nhập địa chỉ IP Proxy vào cài đặt Wi-Fi", "is_correct": False},
                {"content": "C. Bật chế độ máy bay (Airplane Mode)", "is_correct": False},
                {"content": "D. Cài đặt chứng chỉ Burp Suite vào kho người dùng", "is_correct": False},
            ],
        },
    ]

    ch5_questions = [
        {
            "content": "Hệ thống quản lý khóa mật mã phần cứng chuyên dụng trên Android bảo đảm rằng khóa bí mật không bao giờ bị xuất ra ngoài vùng nhớ ứng dụng là gì?",
            "difficulty": "REMEMBER",
            "learning_objective": "Hệ thống Android Keystore Provider",
            "explanation": "Android Keystore lưu trữ khóa bí mật trong phần cứng an toàn (TEE hoặc Secure Element/StrongBox), ngăn chặn việc trích xuất khóa ngay cả khi máy bị Root.",
            "choices": [
                {"content": "A. Android Keystore Provider", "is_correct": True},
                {"content": "B. SharedPreferences XML", "is_correct": False},
                {"content": "C. SQLite Database unencrypted", "is_correct": False},
                {"content": "D. Build.gradle BuildConfig", "is_correct": False},
            ],
        },
        {
            "content": "Thuật toán mã hóa đối xứng khối hiện đại nào được khuyến nghị sử dụng kết hợp với chế độ xác thực tính toàn vẹn (Authenticated Encryption) trong Android?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Lựa chọn chế độ mã hóa an toàn AES-GCM",
            "explanation": "AES ở chế độ Galois/Counter Mode (GCM) với NoPadding cung cấp cả tính bảo mật (confidentiality) và xác thực toàn vẹn (authenticity).",
            "choices": [
                {"content": "A. AES/GCM/NoPadding", "is_correct": True},
                {"content": "B. AES/ECB/PKCS5Padding", "is_correct": False},
                {"content": "C. DES/CBC/PKCS5Padding", "is_correct": False},
                {"content": "D. RC4 Stream Cipher", "is_correct": False},
            ],
        },
        {
            "content": "Mô-đun phần cứng bảo mật độc lập cao cấp nhất trên các thiết bị Android từ phiên bản 9.0 (với CPU, RAM và bộ nhớ flash cách ly hoàn toàn vật lý) có tên là gì?",
            "difficulty": "REMEMBER",
            "learning_objective": "Phân biệt TEE và StrongBox Keymaster",
            "explanation": "StrongBox Keymaster là mô-đun phần cứng bảo mật riêng biệt (Secure Element/HSM) đạt chuẩn bảo mật phần cứng cao hơn TEE thông thường.",
            "choices": [
                {"content": "A. StrongBox Keymaster (Dedicated Hardware HSM)", "is_correct": True},
                {"content": "B. ARM TrustZone TEE", "is_correct": False},
                {"content": "C. Snapdragon GPU Core", "is_correct": False},
                {"content": "D. eMMC Main Flash Memory", "is_correct": False},
            ],
        },
        {
            "content": "Khi cấu hình khóa Keystore với cờ `setUserAuthenticationRequired(true)`, thao tác nào là bắt buộc để mở khóa và sử dụng khóa mật mã?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Ràng buộc khóa Keystore với xác thực sinh trắc học",
            "explanation": "Người dùng phải xác thực sinh trắc học thành công (vân tay, khuôn mặt) qua BiometricPrompt để kích hoạt khóa Keystore tạm thời.",
            "choices": [
                {"content": "A. Xác thực sinh trắc học (vân tay/khuôn mặt) hoặc mã PIN/Pattern của thiết bị", "is_correct": True},
                {"content": "B. Gửi mã OTP xác nhận qua tin nhắn SMS", "is_correct": False},
                {"content": "C. Nhập lại mật khẩu email của tài khoản Google", "is_correct": False},
                {"content": "D. Khởi động lại thiết bị Android", "is_correct": False},
            ],
        },
        {
            "content": "Hàm dẫn xuất khóa an toàn từ mật khẩu người dùng (Password-Based Key Derivation Function) được NIST và OWASP khuyến nghị sử dụng với số vòng lặp tối thiểu 120.000 vòng là gì?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Áp dụng hàm dẫn xuất khóa an toàn PBKDF2/Argon2",
            "explanation": "PBKDF2 (hoặc Argon2) kết hợp với muối ngẫu nhiên (Salt) và hàng trăm ngàn vòng lặp làm chậm đáng kể các cuộc tấn công vét cạn (brute-force).",
            "choices": [
                {"content": "A. PBKDF2WithHmacSHA256", "is_correct": True},
                {"content": "B. MD5 Cryptographic Hash", "is_correct": False},
                {"content": "C. SHA-1 Single Pass", "is_correct": False},
                {"content": "D. Base64 Encoding Scheme", "is_correct": False},
            ],
        },
        {
            "content": "Chuẩn mở rộng bảo mật bắt buộc của luồng OAuth 2.0 Authorization Code dành cho ứng dụng di động loại bỏ Client Secret và chống chiếm đoạt token là gì?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Tiêu chuẩn OAuth 2.0 PKCE",
            "explanation": "PKCE (Proof Key for Code Exchange) sử dụng code_verifier và code_challenge để bảo vệ luồng xác thực trên các client công khai.",
            "choices": [
                {"content": "A. PKCE (Proof Key for Code Exchange)", "is_correct": True},
                {"content": "B. Implicit Grant Flow", "is_correct": False},
                {"content": "C. HTTP Basic Authentication", "is_correct": False},
                {"content": "D. Digest Authentication", "is_correct": False},
            ],
        },
        {
            "content": "Cờ trình biên dịch Clang NDK nào chèn Stack Canaries vào đầu các hàm chứa mảng bộ đệm để phát hiện và ngăn chặn lỗ hổng tràn bộ đệm ngăn xếp?",
            "difficulty": "APPLY",
            "learning_objective": "Cấu hình cờ biên dịch bảo vệ bộ nhớ NDK",
            "explanation": "-fstack-protector-strong là cờ biên dịch tiêu chuẩn chèn canary vào ngăn xếp để phát hiện hành vi ghi đè return address.",
            "choices": [
                {"content": "A. -fstack-protector-strong", "is_correct": True},
                {"content": "B. -O3", "is_correct": False},
                {"content": "C. -fno-exceptions", "is_correct": False},
                {"content": "D. -std=c++11", "is_correct": False},
            ],
        },
        {
            "content": "Giải pháp bảo mật tích hợp trực tiếp vào ứng dụng để tự động phát hiện Frida, Debugger, can thiệp bộ nhớ và chủ động tự sát tiến trình lúc chạy có tên viết tắt là gì?",
            "difficulty": "REMEMBER",
            "learning_objective": "Khái niệm và vai trò của RASP",
            "explanation": "RASP (Runtime Application Self-Protection) là công nghệ phòng vệ chủ động giám sát môi trường thực thi lúc chạy của ứng dụng.",
            "choices": [
                {"content": "A. RASP (Runtime Application Self-Protection)", "is_correct": True},
                {"content": "B. WAF (Web Application Firewall)", "is_correct": False},
                {"content": "C. SIEM (Security Information and Event Management)", "is_correct": False},
                {"content": "D. IDS (Intrusion Detection System)", "is_correct": False},
            ],
        },
        {
            "content": "Cấp độ bảo đảm an ninh nào trong tiêu chuẩn quốc tế OWASP MASVS (Mobile Application Security Verification Standard) quy định các yêu cầu chống dịch ngược và kháng can thiệp?",
            "difficulty": "REMEMBER",
            "learning_objective": "Phân loại các cấp độ trong OWASP MASVS",
            "explanation": "MASVS-R (Resilience Against Reverse Engineering and Tampering) quy định các yêu cầu làm rối mã nguồn, chống debug và phát hiện can thiệp.",
            "choices": [
                {"content": "A. MASVS-R", "is_correct": True},
                {"content": "B. MASVS-L1", "is_correct": False},
                {"content": "C. MASVS-L2", "is_correct": False},
                {"content": "D. MASVS-Zero", "is_correct": False},
            ],
        },
        {
            "content": "Chỉ thị ProGuard/R8 nào được sử dụng để loại bỏ triệt để toàn bộ các câu lệnh ghi nhật ký `android.util.Log` nhằm ngăn ngừa rò rỉ dữ liệu trong bản phát hành?",
            "difficulty": "APPLY",
            "learning_objective": "Cấu hình ProGuard xóa log trong release",
            "explanation": "-assumenosideeffects class android.util.Log { ... } chỉ thị trình tối ưu hóa xóa bỏ các lời gọi ghi log vì chúng không có tác dụng phụ.",
            "choices": [
                {"content": "A. -assumenosideeffects class android.util.Log { ... }", "is_correct": True},
                {"content": "B. -keep class android.util.Log { *; }", "is_correct": False},
                {"content": "C. -dontshrink", "is_correct": False},
                {"content": "D. -ignorewarnings", "is_correct": False},
            ],
        },
    ]

    final_questions = [
        # Ch1 (4 questions)
        {
            "content": "Thành phần cốt lõi nào trong hệ điều hành Android chịu trách nhiệm quản lý toàn bộ các dịch vụ hệ thống (System Services) như ActivityManagerService và PackageManagerService?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Vai trò của tiến trình system_server trong Android",
            "explanation": "system_server là tiến trình khởi tạo và điều phối toàn bộ các dịch vụ cốt lõi của nền tảng Android.",
            "choices": [
                {"content": "A. system_server", "is_correct": True},
                {"content": "B. zygote64", "is_correct": False},
                {"content": "C. surfaceflinger", "is_correct": False},
                {"content": "D. installd", "is_correct": False},
            ],
        },
        {
            "content": "Khi người dùng ấn nút Back hoặc điều hướng thoát khỏi ứng dụng, phương thức nào trong vòng đời Activity được gọi cuối cùng trước khi tiến trình bị hủy hoàn toàn khỏi RAM?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Vòng đời Activity: kết thúc tại onDestroy",
            "explanation": "onDestroy() là phương thức dọn dẹp tài nguyên cuối cùng được gọi trước khi Activity bị giải phóng.",
            "choices": [
                {"content": "A. onDestroy()", "is_correct": True},
                {"content": "B. onStop()", "is_correct": False},
                {"content": "C. onPause()", "is_correct": False},
                {"content": "D. onRestart()", "is_correct": False},
            ],
        },
        {
            "content": "Thành phần ứng dụng nào lắng nghe các thông điệp sự kiện phát rộng toàn hệ thống (như BOOT_COMPLETED, BATTERY_LOW)?",
            "difficulty": "REMEMBER",
            "learning_objective": "Nhận biết BroadcastReceiver",
            "explanation": "BroadcastReceiver nhận và xử lý các Intent phát rộng từ hệ điều hành hoặc các ứng dụng khác.",
            "choices": [
                {"content": "A. BroadcastReceiver", "is_correct": True},
                {"content": "B. ContentProvider", "is_correct": False},
                {"content": "C. Bound Service", "is_correct": False},
                {"content": "D. FragmentManager", "is_correct": False},
            ],
        },
        {
            "content": "Cấu hình an toàn nào trong tệp build.gradle.kts của mô-đun ứng dụng cần được bật để kích hoạt công cụ tối ưu hóa và làm rối mã nguồn R8 trong bản phát hành?",
            "difficulty": "APPLY",
            "learning_objective": "Bật tính năng minifyEnabled trong Gradle",
            "explanation": "isMinifyEnabled = true (hoặc minifyEnabled true trong Groovy) kích hoạt R8 để xóa mã rác và làm rối tên lớp.",
            "choices": [
                {"content": "A. isMinifyEnabled = true", "is_correct": True},
                {"content": "B. isDebuggable = true", "is_correct": False},
                {"content": "C. isShrinkResources = false", "is_correct": False},
                {"content": "D. multiDexEnabled = false", "is_correct": False},
            ],
        },

        # Ch2 (4 questions)
        {
            "content": "Nếu hai ứng dụng trên cùng một thiết bị Android có các Linux UID khác nhau, theo mô hình Sandbox, ứng dụng này có thể đọc trực tiếp tệp tin trong thư mục dữ liệu nội bộ (/data/data/<pkg>) của ứng dụng kia không?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Quyền truy cập tệp tin trong Android Sandbox",
            "explanation": "Không thể. Quyền phân quyền tệp tin của Linux (0700 hoặc 0751) chỉ cho phép chủ sở hữu UID đọc/ghi vào thư mục riêng.",
            "choices": [
                {"content": "A. Hoàn toàn không thể, vì nhân Linux chặn truy cập dựa trên sự khác biệt UID", "is_correct": True},
                {"content": "B. Có thể đọc được nếu cả hai ứng dụng cùng sử dụng ngôn ngữ Kotlin", "is_correct": False},
                {"content": "C. Luôn luôn đọc được vì cùng nằm trên một ổ đĩa flash", "is_correct": False},
                {"content": "D. Đọc được nếu người dùng cấp quyền READ_EXTERNAL_STORAGE", "is_correct": False},
            ],
        },
        {
            "content": "Cơ chế nào cho phép Service bên thứ ba yêu cầu ứng dụng gọi IPC phải có một quyền hạn cụ thể trước khi thực thi lệnh?",
            "difficulty": "APPLY",
            "learning_objective": "Thực thi kiểm tra quyền hạn Binder IPC",
            "explanation": "Phương thức Context.enforceCallingOrSelfPermission() kiểm tra quyền hạn của tiến trình gọi và ném ngoại lệ SecurityException nếu vi phạm.",
            "choices": [
                {"content": "A. Context.enforceCallingOrSelfPermission()", "is_correct": True},
                {"content": "B. Thread.sleep()", "is_correct": False},
                {"content": "C. Intent.setAction()", "is_correct": False},
                {"content": "D. System.exit(0)", "is_correct": False},
            ],
        },
        {
            "content": "Cấu trúc cơ bản của một nhãn bảo mật SELinux Security Context (ví dụ: `u:r:untrusted_app:s0:c512,c768`) gồm những thành phần nào theo thứ tự?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Cấu trúc nhãn SELinux",
            "explanation": "Nhãn SELinux tuân theo cú pháp chuẩn: user:role:type:level (trong đó type là trọng tâm của Type Enforcement).",
            "choices": [
                {"content": "A. user:role:type:level", "is_correct": True},
                {"content": "B. domain:process:thread:core", "is_correct": False},
                {"content": "C. group:owner:permission:mask", "is_correct": False},
                {"content": "D. protocol:host:port:path", "is_correct": False},
            ],
        },
        {
            "content": "Quyền hạn nào dưới đây thuộc nhóm Quyền bình thường (Normal Permission) và được tự động cấp phép tại thời điểm cài đặt mà không cần hỏi người dùng?",
            "difficulty": "REMEMBER",
            "learning_objective": "Phân loại quyền android.permission.INTERNET",
            "explanation": "android.permission.INTERNET thuộc nhóm Normal Permission, hệ thống tự động cấp quyền mà không hiển thị hộp thoại Runtime Permission.",
            "choices": [
                {"content": "A. android.permission.INTERNET", "is_correct": True},
                {"content": "B. android.permission.CAMERA", "is_correct": False},
                {"content": "C. android.permission.RECORD_AUDIO", "is_correct": False},
                {"content": "D. android.permission.ACCESS_FINE_LOCATION", "is_correct": False},
            ],
        },

        # Ch3 (4 questions)
        {
            "content": "Khi dịch ngược tệp classes.dex bằng công cụ JADX-GUI, kết quả đầu ra hiển thị ở định dạng mã nguồn nào?",
            "difficulty": "REMEMBER",
            "learning_objective": "Phân biệt đầu ra của JADX vs Apktool",
            "explanation": "JADX dịch ngược bytecode DEX thành mã nguồn Java cấp cao (High-level Java source code).",
            "choices": [
                {"content": "A. Mã nguồn Java cấp cao (Java Source Code)", "is_correct": True},
                {"content": "B. Hợp ngữ Smali", "is_correct": False},
                {"content": "C. Mã nhị phân máy tính ARM64", "is_correct": False},
                {"content": "D. Mã nguồn C++ Native", "is_correct": False},
            ],
        },
        {
            "content": "Kỹ thuật sửa đổi tệp Smali sau đó đóng gói lại và ký số mới (Repackaging) thường được các nhà phân tích an ninh sử dụng để làm gì?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Mục đích của việc patch mã Smali",
            "explanation": "Patch mã Smali cho phép vượt qua các kiểm tra bảo mật (bỏ qua xác thực, bỏ qua root check) hoặc chèn mã log theo dõi hành vi ứng dụng.",
            "choices": [
                {"content": "A. Chèn mã nhật ký, bẻ khóa logic kiểm tra bản quyền hoặc gỡ bỏ các chốt chặn an ninh", "is_correct": True},
                {"content": "B. Giúp ứng dụng chạy nhanh hơn trên các thiết bị đời cũ", "is_correct": False},
                {"content": "C. Giảm kích thước tệp APK xuống một nửa", "is_correct": False},
                {"content": "D. Tăng thời lượng pin cho thiết bị", "is_correct": False},
            ],
        },
        {
            "content": "Lỗ hổng SQL Injection có thể xuất hiện trong thành phần nào của Android nếu chuỗi truy vấn được ghép trực tiếp bằng phép cộng chuỗi mà không dùng tham số?",
            "difficulty": "APPLY",
            "learning_objective": "Phát hiện SQL Injection trong ContentProvider / SQLite",
            "explanation": "ContentProvider truy vấn SQLiteDatabase thông qua phép cộng chuỗi lỏng lẻo dễ bị tấn công SQLi qua tham số selection.",
            "choices": [
                {"content": "A. ContentProvider / SQLiteOpenHelper", "is_correct": True},
                {"content": "B. JobScheduler", "is_correct": False},
                {"content": "C. NotificationManager", "is_correct": False},
                {"content": "D. WorkManager", "is_correct": False},
            ],
        },
        {
            "content": "Cơ chế ký số APK Scheme v2 và v3 có ưu điểm gì vượt trội so với JAR Signing Scheme (v1) truyền thống?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Bảo vệ toàn vẹn APK với Signature Scheme v2/v3",
            "explanation": "APK Signature Scheme v2 bảo vệ toàn bộ tệp nhị phân APK, phát hiện mọi hành vi can thiệp hay sửa đổi bất kỳ byte nào trong tệp.",
            "choices": [
                {"content": "A. Bảo vệ toàn bộ tệp APK, chống lại việc chèn hoặc sửa đổi tệp mà không cần giải nén", "is_correct": True},
                {"content": "B. Cho phép tệp APK chạy được trên hệ điều hành iOS", "is_correct": False},
                {"content": "C. Tự động mã hóa tệp APK bằng mật khẩu người dùng", "is_correct": False},
                {"content": "D. Không yêu cầu nhà phát triển phải tạo Keystore", "is_correct": False},
            ],
        },

        # Ch4 (4 questions)
        {
            "content": "Lệnh dòng lệnh Frida nào cho phép kết nối vào tiến trình đang chạy của ứng dụng dựa trên tên package (Spawn mode) để hook mã ngay từ thời điểm khởi động?",
            "difficulty": "APPLY",
            "learning_objective": "Sử dụng cờ -f trong frida CLI",
            "explanation": "frida -U -f <package_name> -l script.js kích hoạt chế độ Spawn, tạm dừng ứng dụng tại tiến trình khởi động để nạp hook trước khi mã chính chạy.",
            "choices": [
                {"content": "A. frida -U -f <package_name> -l script.js", "is_correct": True},
                {"content": "B. frida-ps -U", "is_correct": False},
                {"content": "C. adb shell am start", "is_correct": False},
                {"content": "D. frida-server -D", "is_correct": False},
            ],
        },
        {
            "content": "Lỗ hổng nào phát sinh khi ứng dụng kích hoạt chế độ cho phép WebSettings thực thi JavaScript và vô tình để lộ interface Java ra ngoài môi trường web?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Lỗ hổng WebView JavaScriptInterface Injection",
            "explanation": "addJavascriptInterface trên các phiên bản cũ (trước Android 4.2) hoặc cấu hình không an toàn cho phép mã độc web thực thi mã Java tùy ý.",
            "choices": [
                {"content": "A. WebView JavaScriptInterface Remote Code Execution", "is_correct": True},
                {"content": "B. Stack-based Buffer Overflow", "is_correct": False},
                {"content": "C. Local Privilege Escalation qua Kernel", "is_correct": False},
                {"content": "D. Denial of Service do cạn kiệt pin", "is_correct": False},
            ],
        },
        {
            "content": "Để phát hiện xem ứng dụng có đang bị công cụ Frida gắn kết vào tiến trình hay không, mô-đun phòng vệ RASP thường đọc tệp tin đặc biệt nào trong thư mục `/proc`?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Kỹ thuật phát hiện Frida qua /proc/self/maps",
            "explanation": "Tệp /proc/self/maps liệt kê các thư viện chia sẻ trong bộ nhớ; sự xuất hiện của 'frida-agent.so' là bằng chứng ứng dụng đang bị hook.",
            "choices": [
                {"content": "A. /proc/self/maps và /proc/self/status", "is_correct": True},
                {"content": "B. /proc/cpuinfo", "is_correct": False},
                {"content": "C. /proc/version", "is_correct": False},
                {"content": "D. /proc/meminfo", "is_correct": False},
            ],
        },
        {
            "content": "Kỹ thuật nào cho phép chuyển hướng lưu lượng mạng của toàn bộ thiết bị Android qua máy chủ proxy Burp Suite ở tầng nhân Linux mà không phụ thuộc vào cấu hình Wi-Fi?",
            "difficulty": "APPLY",
            "learning_objective": "Kỹ thuật iptables Transparent Proxying",
            "explanation": "Sử dụng iptables với bảng PREROUTING/OUTPUT và lệnh REDIRECT cho phép chuyển tiếp toàn bộ gói tin TCP cổng 80/443 sang Burp Suite.",
            "choices": [
                {"content": "A. Quy tắc iptables REDIRECT kết hợp Transparent Proxy", "is_correct": True},
                {"content": "B. Khởi động lại router Wi-Fi", "is_correct": False},
                {"content": "C. Bật Bluetooth tethering", "is_correct": False},
                {"content": "D. Đổi DNS trên điện thoại sang 8.8.8.8", "is_correct": False},
            ],
        },

        # Ch5 (4 questions)
        {
            "content": "Ưu điểm bảo mật lớn nhất của việc tạo và lưu trữ khóa mật mã trong Android Keystore so với việc lưu trữ trong tệp cơ sở dữ liệu là gì?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Bản chất an ninh của Android Keystore",
            "explanation": "Khóa trong Keystore được quản lý bởi phần cứng cách ly (TEE/SE); vật liệu khóa không thể bị xuất ra ngoài bộ nhớ ứng dụng.",
            "choices": [
                {"content": "A. Vật liệu khóa không thể bị trích xuất khỏi phần cứng bảo mật ngay cả khi thiết bị bị Root", "is_correct": True},
                {"content": "B. Giúp ứng dụng tiết kiệm dung lượng lưu trữ trên thẻ nhớ", "is_correct": False},
                {"content": "C. Tự động đồng bộ hóa khóa lên máy chủ của bên thứ ba", "is_correct": False},
                {"content": "D. Khóa có thể được chia sẻ cho tất cả các ứng dụng khác cùng đọc", "is_correct": False},
            ],
        },
        {
            "content": "Tại sao chế độ mã hóa khối AES/ECB (Electronic Codebook) tuyệt đối bị cấm sử dụng trong các hệ thống an ninh hiện đại?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Nguy cơ bảo mật của chế độ AES/ECB",
            "explanation": "ECB mã hóa các khối văn bản rõ giống nhau thành các khối bản mã giống nhau, làm lộ cấu trúc và hình mẫu của dữ liệu gốc.",
            "choices": [
                {"content": "A. ECB không sử dụng Vector khởi tạo (IV), các khối dữ liệu giống nhau sinh ra bản mã giống hệt nhau làm lộ mô hình dữ liệu", "is_correct": True},
                {"content": "B. ECB có tốc độ tính toán quá chậm", "is_correct": False},
                {"content": "C. ECB chỉ hỗ trợ độ dài khóa 64-bit", "is_correct": False},
                {"content": "D. ECB làm tăng kích thước tệp lên gấp 10 lần", "is_correct": False},
            ],
        },
        {
            "content": "Trong tiêu chuẩn bảo mật di động toàn cầu OWASP MASVS, miền kiểm soát MASVS-STORAGE yêu cầu điều gì đối với dữ liệu nhạy cảm của người dùng?",
            "difficulty": "UNDERSTAND",
            "learning_objective": "Tiêu chuẩn OWASP MASVS-STORAGE",
            "explanation": "Dữ liệu nhạy cảm (thông tin cá nhân, token, khóa) phải được mã hóa bằng thuật toán an toàn trước khi lưu vào bộ nhớ cục bộ.",
            "choices": [
                {"content": "A. Dữ liệu nhạy cảm phải được mã hóa bảo vệ và không lưu trong các vùng nhớ công khai hay bộ nhớ ngoài không an toàn", "is_correct": True},
                {"content": "B. Bắt buộc phải lưu trữ toàn bộ dữ liệu trên thẻ nhớ MicroSD", "is_correct": False},
                {"content": "C. Phải xuất toàn bộ dữ liệu ra tệp văn bản rõ để sao lưu", "is_correct": False},
                {"content": "D. Cho phép các ứng dụng khác tự do truy cập cơ sở dữ liệu để chia sẻ", "is_correct": False},
            ],
        },
        {
            "content": "Giải pháp nào là lựa chọn chuẩn mực hàng đầu để lưu trữ cặp khóa-giá trị nhạy cảm (như Auth Token, API Secrets) trên Android một cách an toàn và dễ sử dụng?",
            "difficulty": "APPLY",
            "learning_objective": "Sử dụng EncryptedSharedPreferences từ AndroidX Security",
            "explanation": "EncryptedSharedPreferences (thuộc AndroidX Security Library) tự động mã hóa cả khóa và giá trị bằng AES-GCM bảo vệ bởi Android Keystore.",
            "choices": [
                {"content": "A. EncryptedSharedPreferences (AndroidX Security Library)", "is_correct": True},
                {"content": "B. SharedPreferences thông thường với Context.MODE_PRIVATE", "is_correct": False},
                {"content": "C. Lưu chuỗi rõ vào tệp văn bản trong /sdcard/secrets.txt", "is_correct": False},
                {"content": "D. Ghi khóa vào thuộc tính android:tag của View giao diện", "is_correct": False},
            ],
        },
    ]

    return [
        {
            "chapter_index": 1,
            "title": "Kiểm Tra Đánh Giá Năng Lực Chương 1: Kiến Trúc Nền Tảng & Thành Phần Android",
            "description": "Bài kiểm tra trắc nghiệm 10 câu hỏi đánh giá mức độ hiểu biết về nhân Linux, ART Runtime, Zygote, AndroidManifest và 4 thành phần ứng dụng cơ bản.",
            "type": "QUIZ",
            "time_limit_minutes": 15,
            "passing_percent": 70.0,
            "shuffle_questions": True,
            "shuffle_choices": True,
            "questions": ch1_questions,
        },
        {
            "chapter_index": 2,
            "title": "Kiểm Tra Đánh Giá Năng Lực Chương 2: Mô Hình An Ninh Android, Quyền Hạn & Binder IPC",
            "description": "Bài kiểm tra 10 câu hỏi bao quát Sandbox UID/GID, Android Permissions, Binder IPC Driver, SELinux Policies và bảo vệ ranh giới tiến trình.",
            "type": "QUIZ",
            "time_limit_minutes": 15,
            "passing_percent": 70.0,
            "shuffle_questions": True,
            "shuffle_choices": True,
            "questions": ch2_questions,
        },
        {
            "chapter_index": 3,
            "title": "Kiểm Tra Đánh Giá Năng Lực Chương 3: Phân Tích Tĩnh APK & Dịch Ngược Mã Nguồn",
            "description": "Bài kiểm tra 10 câu hỏi về cấu trúc APK/AAB, Dalvik Bytecode, Smali Syntax, Apktool, JADX-GUI, Khai thác Intent Injection và Quét lỗ hổng MobSF.",
            "type": "QUIZ",
            "time_limit_minutes": 15,
            "passing_percent": 70.0,
            "shuffle_questions": True,
            "shuffle_choices": True,
            "questions": ch3_questions,
        },
        {
            "chapter_index": 4,
            "title": "Kiểm Tra Đánh Giá Năng Lực Chương 4: Phân Tích Động, Frida Hooking & Vượt Rào Bảo Mật",
            "description": "Bài kiểm tra 10 câu hỏi về thiết lập Lab Android Pentest, Frida Architecture, Javascript API Hooking, Bypass SSL Pinning, Root Detection và Objection.",
            "type": "QUIZ",
            "time_limit_minutes": 15,
            "passing_percent": 70.0,
            "shuffle_questions": True,
            "shuffle_choices": True,
            "questions": ch4_questions,
        },
        {
            "chapter_index": 5,
            "title": "Kiểm Tra Đánh Giá Năng Lực Chương 5: Mật Mã Học, Keystore, TEE & Phòng Vệ RASP",
            "description": "Bài kiểm tra 10 câu hỏi về JCA/JCE, Android Keystore, TEE/StrongBox, Biometric Authentication, OAuth 2.0 PKCE, RASP và Tiêu chuẩn OWASP MASVS.",
            "type": "QUIZ",
            "time_limit_minutes": 15,
            "passing_percent": 70.0,
            "shuffle_questions": True,
            "shuffle_choices": True,
            "questions": ch5_questions,
        },
        {
            "chapter_index": None,
            "title": "Đề Thi Đánh Giá Năng Lực Toàn Diện Chuyên Gia An Ninh Android (Final Assessment)",
            "description": "Đề thi tốt nghiệp toàn diện 20 câu hỏi tổng hợp kiến thức từ cả 5 chương. Yêu cầu làm bài nghiêm túc, đảo ngẫu nhiên thứ tự câu hỏi và phương án đáp án.",
            "type": "FINAL",
            "time_limit_minutes": 45,
            "passing_percent": 80.0,
            "shuffle_questions": True,
            "shuffle_choices": True,
            "questions": final_questions,
        },
    ]
