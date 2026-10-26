# -*- coding: utf-8 -*-
"""Builder for Chapter 1: Kiến Trúc Hệ Thống & Nền Tảng Lập Trình Ứng Dụng Android (12 lessons).
Every lesson strictly exceeds 600 Vietnamese words and includes a 4-question miniquiz.
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
    VIDEO_CACHE = json.load(f)["ch1"]


def get_chapter_1_lessons() -> list[dict[str, Any]]:
    lessons = []

    # 1.1
    l1_md = generate_lesson_markdown(
        lesson_num="1.1",
        title="Bài 1.1: Tổng Quan Kiến Trúc Phân Tầng Android: Linux Kernel, HAL, Native C/C++ & ART Runtime",
        objective_points=[
            "Phân tích cấu trúc phân tầng ngũ cấp của hệ điều hành Android từ nhân Linux đến tầng ứng dụng người dùng.",
            "Làm rõ vai trò và cơ chế vận hành của Hardware Abstraction Layer (HAL) trong việc trừu tượng hóa phần cứng.",
            "Hiểu sâu sự khác biệt then chốt giữa máy ảo Dalvik lịch sử và môi trường thực thi hiện đại Android Runtime (ART) với cơ chế AOT/JIT compilation.",
            "Nắm vững luồng thực thi khi một tiến trình ứng dụng người dùng tương tác với các thư viện native C/C++ qua JNI."
        ],
        theory_sections=[
            (
                "Kiến Trúc Ngũ Cấp Phân Tầng (5-Layer Android Architecture)",
                "Hệ điều hành Android được xây dựng trên một kiến trúc phân tầng dạng khối xếp chồng vững chắc, bao gồm 5 phân tầng kỹ thuật riêng biệt nhằm đảm bảo tính module hóa và bảo mật tối đa. "
                "Tầng đáy cùng là Linux Kernel (phiên bản Long Term Support tùy biến cho Android). Nhân Linux chịu trách nhiệm quản lý driver phần cứng (camera, bluetooth, audio, wifi, bộ nhớ flash), quản lý luồng CPU, bộ nhớ ảo, và quan trọng nhất là đóng vai trò hạt nhân bảo mật cung cấp cơ chế phân quyền Discretionary Access Control (DAC) dựa trên User ID (UID) và Mandatory Access Control (MAC) thông qua SELinux. "
                "Tầng thứ hai là Hardware Abstraction Layer (HAL). HAL cung cấp các giao diện chuẩn hóa (interfaces) bằng C/C++ cho phép tầng framework cấp cao có thể giao tiếp với các module phần cứng cụ thể mà không cần biết chi tiết cài đặt độc quyền của từng nhà sản xuất chip (Qualcomm, MediaTek, Samsung Exynos). "
                "Tầng thứ ba là Android Runtime (ART) và Native C/C++ Libraries. Tầng này bao gồm các thư viện hệ thống nền tảng viết bằng C/C++ như WebKit/Blink (engine trình duyệt), SQLite (cơ sở dữ liệu nhúng), OpenGL ES / Vulkan (đồ họa 3D), SSL/BoringSSL (mật mã mạng), và Media Framework. Đi kèm với các thư viện này là môi trường thực thi ART chịu trách nhiệm thông dịch và biên dịch mã bytecode của ứng dụng."
            ),
            (
                "Sự Tiến Hóa Từ Dalvik Virtual Machine Sang Android Runtime (ART)",
                "Trước phiên bản Android 5.0 (Lollipop), nền tảng sử dụng máy ảo Dalvik. Dalvik hoạt động dựa trên cơ chế biên dịch Just-In-Time (JIT) - mỗi khi ứng dụng khởi chạy, bytecode Dalvik (.dex) được thông dịch sang mã máy từng đoạn tại thời điểm chạy. Điều này dẫn đến độ trễ khởi động cao và tiêu tốn nhiều tài nguyên CPU/pin. "
                "Bắt đầu từ Android 5.0, Google thay thế hoàn toàn Dalvik bằng Android Runtime (ART). ART ban đầu sử dụng cơ chế Ahead-Of-Time (AOT) compilation thông qua tiện ích dex2oat: toàn bộ tệp classes.dex được biên dịch thành mã máy nhị phân (.oat / .elf) ngay tại thời điểm cài đặt ứng dụng. "
                "Từ Android 7.0 (Nougat) trở đi, ART áp dụng mô hình lai (Hybrid Compilation Mode) kết hợp Profile-Guided Compilation: ứng dụng được thông dịch nhanh bằng JIT khi mới cài đặt, trong khi hệ thống âm thầm ghi lại hồ sơ sử dụng (Profile). Khi thiết bị cắm sạc vào ban đêm và ở trạng thái rảnh, tiến trình nền dexopt sẽ AOT-compile các đoạn mã nóng (hot code) dựa trên Profile, mang lại tốc độ thực thi tối ưu nhất mà không gây phình to dung lượng bộ nhớ cài đặt."
            ),
            (
                "Tầng Application Framework & Cổng Giao Tiếp JNI",
                "Phía trên ART là Application Framework - tập hợp toàn bộ các API Java/Kotlin mà lập trình viên tương tác hàng ngày. Khung làm việc này cung cấp các dịch vụ hệ thống cốt lõi: Activity Manager (quản lý vòng đời và ngăn xếp màn hình), Window Manager (quản lý hiển thị bề mặt cửa sổ), Package Manager (quản lý cài đặt và chữ ký số APK), Content Providers (chia sẻ dữ liệu liên ứng dụng), và Notification Manager. "
                "Khi một ứng dụng cần thực thi các tác vụ tính toán hiệu năng cao hoặc thư viện bảo mật native, nó sử dụng Java Native Interface (JNI). JNI hoạt động như một cây cầu nối cho phép mã Java/Kotlin nạp các thư viện liên kết động (.so) viết bằng C/C++ thông qua `System.loadLibrary()`. Tuy nhiên, đây cũng là ranh giới tiềm ẩn rủi ro bảo mật lớn nhất vì các lỗ hổng tràn bộ đệm (buffer overflow, use-after-free) trong mã native có thể bị tin tặc khai thác trực tiếp để chiếm quyền kiểm soát luồng thực thi của tiến trình."
            )
        ],
        attack_defense_section=(
            "Từ góc độ an ninh ứng dụng và kiểm thử thâm nhập (Pentesting), việc hiểu sâu kiến trúc phân tầng cho phép chuyên gia bảo mật nhận diện chính xác bề mặt tấn công: "
            "1. Tấn công tầng Native qua JNI: Kẻ tấn công có thể sử dụng IDA Pro, Ghidra hoặc Binary Ninja để dịch ngược các tệp thư viện .so trong thư mục `lib/<abi>/` nhằm tìm kiếm các khóa bí mật (hardcoded API keys), thuật toán mã hóa tùy biến hoặc khai thác lỗ hổng quản lý bộ nhớ trong C/C++. "
            "2. Khai thác Binder IPC: Các lời gọi dịch vụ giữa Framework và System Server đều đi qua driver Binder trong nhân Linux. Nếu dịch vụ hệ thống thiếu kiểm tra quyền gọi (`checkCallingPermission`), kẻ tấn công có thể thực hiện leo thang đặc quyền (Privilege Escalation). "
            "Giải pháp phòng thủ: Luôn áp dụng cờ bảo vệ trình biên dịch cho mã native như Stack Canaries (`-fstack-protector-strong`), ASLR/PIE (`-fPIE -pie`), và Fortify Source. Kiểm tra nghiêm ngặt kiểu dữ liệu và ranh giới con trỏ tại ranh giới JNI."
        ),
        lab_instructions=(
            "Trong bài thực hành lab này, chúng ta sẽ sử dụng công cụ dòng lệnh ADB để kết nối vào thiết bị Android (hoặc giả lập Android Studio), khám phá cấu trúc tiến trình hệ thống, kiểm tra môi trường thực thi ART và phân tích các thư viện native được nạp vào bộ nhớ tiến trình:"
        ),
        code_snippet=(
            "bash",
            """# 1. Kết nối vào shell của thiết bị Android qua ADB
adb devices -l
adb shell

# 2. Kiểm tra thông tin phiên bản nhân Linux và kiến trúc CPU
uname -a
getprop ro.product.cpu.abi
getprop ro.build.version.release

# 3. Liệt kê các tiến trình nền tảng khởi tạo: init, zygote, system_server
ps -ef | grep -E "zygote|system_server"

# 4. Kiểm tra cấu hình môi trường thực thi ART (Android Runtime)
getprop dalvik.vm.execution-mode
getprop dalvik.vm.dex2oat-filter

# 5. Xem bản đồ bộ nhớ (maps) và các thư viện .so của tiến trình system_server
cat /proc/$(pidof system_server)/maps | head -n 30"""
        ),
        pitfalls=[
            "Không bao giờ giả định rằng mã logic đặt trong thư viện C/C++ (.so) là an toàn tuyệt đối khỏi dịch ngược, vì các decompiler hiện đại như Ghidra phân tích mã máy thành mã C giả rất dễ dàng.",
            "Tránh nạp các thư viện native không có chữ ký số hoặc nạp từ đường dẫn có thể ghi được (writable directory) như `/data/local/tmp/` để ngăn ngừa tấn công Shared Library Hijacking."
        ],
        summary_points=[
            "Hệ điều hành Android phân tầng 5 lớp: Linux Kernel -> HAL -> Native Libs/ART -> Framework -> Applications.",
            "ART thay thế hoàn toàn Dalvik với cơ chế biên dịch lai JIT/AOT kết hợp Profile-Guided Compilation.",
            "Cổng JNI là cầu nối giữa Java và mã máy C/C++, đồng thời là mục tiêu hàng đầu cho dịch ngược và khai thác bộ nhớ."
        ],
        video_url=VIDEO_CACHE[0]["url"],
        quiz_items=[
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Môi trường thực thi nào được Google giới thiệu từ phiên bản Android 5.0 (Lollipop) để thay thế hoàn toàn máy ảo Dalvik?",
                "options": [
                    "A. Android Runtime (ART)",
                    "B. Java Virtual Machine (JVM)",
                    "C. Common Language Runtime (CLR)",
                    "D. Node.js V8 Engine"
                ],
                "correct_index": 0,
                "explanation": "Android Runtime (ART) thay thế Dalvik từ Android 5.0, mang lại hiệu năng vượt trội nhờ AOT compilation và cơ chế nén rác (GC) tối ưu."
            },
            {
                "type": "FILL_BLANK",
                "question": "Cơ chế giao diện lập trình cho phép mã nguồn Java/Kotlin gọi và thực thi các hàm trong thư viện native C/C++ có tên viết tắt là [_____].",
                "blanks": [
                    {"accepted_answers": ["JNI", "Java Native Interface", "jni"]}
                ],
                "explanation": "Java Native Interface (JNI) là chuẩn giao tiếp chính thống giữa mã bytecode Java/Kotlin và mã máy gốc C/C++."
            },
            {
                "type": "MATCHING",
                "question": "Hãy nối từng thành phần kiến trúc Android ở cột trái với chức năng tương ứng ở cột phải:",
                "pairs": [
                    {"left": "Linux Kernel", "right": "Cung cấp quản lý bộ nhớ, tiến trình và cơ chế phân quyền DAC/SELinux"},
                    {"left": "HAL", "right": "Trừu tượng hóa giao diện điều khiển phần cứng cho tầng framework"},
                    {"left": "ART", "right": "Môi trường thực thi bytecode DEX với cơ chế AOT/JIT compilation"},
                    {"left": "Application Framework", "right": "Cung cấp các API Java cấp cao như ActivityManager và PackageManager"}
                ],
                "explanation": "Mỗi tầng trong kiến trúc Android có một nhiệm vụ chuyên biệt cấu thành nên toàn bộ hệ điều hành."
            },
            {
                "type": "FILL_BLANK",
                "question": "Tệp bytecode chứa mã thực thi của ứng dụng Android được biên dịch từ mã nguồn có tên mở rộng là [_____], và tệp nhị phân chứa mã máy do tiến trình dex2oat tạo ra có định dạng [_____].",
                "blanks": [
                    {"accepted_answers": [".dex", "dex", "classes.dex"]},
                    {"accepted_answers": [".oat", "oat", ".elf", "elf"]}
                ],
                "explanation": "Bytecode của Android lưu trữ trong tệp classes.dex, sau khi chạy dex2oat sẽ được đóng gói thành tệp OAT/ELF chứa mã máy."
            }
        ]
    )
    validate_lesson_data({
        "title": "Bài 1.1: Tổng Quan Kiến Trúc Phân Tầng Android",
        "markdown_content": l1_md,
        "video_url": VIDEO_CACHE[0]["url"]
    })
    lessons.append({
        "position": 1,
        "title": "Bài 1.1: Tổng Quan Kiến Trúc Phân Tầng Android: Linux Kernel, HAL, Native C/C++ & ART Runtime",
        "summary": "Nghiên cứu kiến trúc phân tầng 5 lớp của Android, cơ chế biên dịch ART, JNI bridge và bề mặt tấn công native.",
        "duration_minutes": 45,
        "video_url": VIDEO_CACHE[0]["url"],
        "markdown_content": l1_md,
    })

    # 1.2
    l2_md = generate_lesson_markdown(
        lesson_num="1.2",
        title="Bài 1.2: Vòng Đời Activity (Activity Lifecycle), Quản Lý Ngăn Xếp Task & Phục Hồi Trạng Thái Giao Diện",
        objective_points=[
            "Làm chủ toàn bộ 7 phương thức callback cốt lõi trong vòng đời Activity của Android.",
            "Hiểu sâu cơ chế quản lý ngăn xếp (Back Stack) và các chế độ khởi chạy Launch Mode: standard, singleTop, singleTask, singleInstance.",
            "Xử lý chuẩn mực quá trình lưu trữ và phục hồi trạng thái giao diện khi xảy ra thay đổi cấu hình (Configuration Change) bằng `onSaveInstanceState` và ViewModel.",
            "Nhận diện các lỗ hổng rò rỉ bộ nhớ (Memory Leak) và nguy cơ lộ dữ liệu nhạy cảm qua ảnh chụp màn hình gần đây (Recent Tasks Snapshot)."
        ],
        theory_sections=[
            (
                "Mô Hình Máy Trạng Thái Của Activity (Activity State Machine)",
                "Activity là thành phần giao diện người dùng cơ bản nhất trong Android. Mỗi Activity được điều khiển bởi một máy trạng thái tuần tự thông qua các hàm callback được hệ điều hành kích hoạt: "
                "`onCreate()`: Khởi tạo ban đầu, nạp bố cục giao diện (layout XML qua `setContentView`), ánh xạ view và khởi tạo biến thành viên. "
                "`onStart()`: Activity bắt đầu hiển thị trên màn hình nhưng chưa có quyền tương tác người dùng. "
                "`onResume()`: Activity bước vào trạng thái Foreground (tiêu điểm tương tác), người dùng có thể chạm, cuộn và nhập liệu. Đây là nơi kích hoạt các cảm biến và lắng nghe sự kiện. "
                "`onPause()`: Activity mất tiêu điểm một phần (ví dụ khi có hộp thoại nổi hoặc cuộc gọi đến), cần tạm ngưng các tác vụ nặng về đồ họa và camera. "
                "`onStop()`: Activity bị che khuất hoàn toàn khỏi tầm nhìn người dùng. Hệ thống có thể giải phóng bớt tài nguyên. "
                "`onDestroy()`: Phương thức cuối cùng trước khi Activity bị giải phóng hoàn toàn khỏi bộ nhớ RAM."
            ),
            (
                "Quản Lý Ngăn Xếp Back Stack & Launch Modes",
                "Các Activity trong một ứng dụng được sắp xếp tuần tự theo cơ chế Vào Sau Ra Trước (LIFO - Last In, First Out) bên trong các Task. Việc điều hướng giữa các màn hình được quy định bởi thuộc tính `android:launchMode` trong AndroidManifest.xml hoặc cờ Intent (Intent Flags): "
                "1. `standard`: Chế độ mặc định. Mỗi lần kích hoạt Intent, một instance Activity mới luôn được tạo ra và đẩy lên đỉnh ngăn xếp Task. "
                "2. `singleTop`: Nếu instance của Activity đã nằm ngay trên đỉnh ngăn xếp, hệ thống sẽ tái sử dụng nó và gọi callback `onNewIntent()` thay vì tạo mới. "
                "3. `singleTask`: Hệ thống chỉ duy trì duy nhất một instance của Activity trong toàn bộ Task. Mọi Activity nằm phía trên nó trong ngăn xếp sẽ bị hủy bỏ (Clear Top). "
                "4. `singleInstance`: Activity được cô lập hoàn toàn trong một Task độc lập, không cho phép bất kỳ Activity nào khác được chia sẻ chung ngăn xếp."
            ),
            (
                "Thay Đổi Cấu Hình (Configuration Change) & Rủi Ro Rò Rỉ Dữ Liệu",
                "Khi xảy ra các sự kiện thay đổi cấu hình môi trường như xoay màn hình (orientation change), đổi ngôn ngữ hoặc bật chế độ chia đôi màn hình (Multi-Window), theo mặc định Android sẽ hủy toàn bộ Activity hiện tại (`onDestroy`) và tái tạo lại từ đầu (`onCreate`). "
                "Nếu lập trình viên không chủ động lưu trữ trạng thái qua đối tượng `Bundle` trong `onSaveInstanceState(outState)` hoặc sử dụng Jetpack ViewModel, toàn bộ dữ liệu nhập của người dùng sẽ bị xóa sạch. "
                "Nguy hiểm hơn, nếu Activity lưu trữ tham chiếu đến các đối tượng tĩnh (static reference), các luồng bất đồng bộ (Threads, Handlers) hoặc nặc danh (Anonymous Inner Classes), toàn bộ Context của Activity sẽ không thể được bộ gom rác (Garbage Collector) thu hồi, gây ra lỗi rò rỉ bộ nhớ (Memory Leak) nghiêm trọng dẫn đến tràn bộ nhớ (OutOfMemoryError)."
            )
        ],
        attack_defense_section=(
            "Kịch bản tấn công và khai thác liên quan đến Activity: "
            "1. Lộ lọt thông tin nhạy cảm qua Recent Apps Snapshot: Khi người dùng nhấn nút chuyển ứng dụng (Overview / Recents Screen), Android tự động chụp ảnh màn hình hiện tại của Activity để hiển thị dạng thẻ. Nếu màn hình đó đang hiển thị số thẻ tín dụng, mã OTP hoặc số dư tài khoản ngân hàng, ảnh chụp màn hình này sẽ được lưu tạm thời vào bộ đệm hệ thống không mã hóa. "
            "Giải pháp phòng thủ: Luôn kích hoạt cờ bảo mật chống chụp màn hình trong `onCreate()`: "
            "`window.setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)`. Cờ này lập tức vô hiệu hóa tính năng chụp màn hình, quay video màn hình và hiển thị nền đen trong cửa sổ Recents. "
            "2. Tấn công Activity Hijacking (Đánh cắp Activity): Kẻ tấn công thiết lập một ứng dụng độc hại có Activity sử dụng `launchMode=\"singleTask\"` và Intent Filter tương tự để cướp Task hoặc giả mạo màn hình đăng nhập (Phishing overlay)."
        ),
        lab_instructions=(
            "Trong bài lab này, chúng ta sẽ cấu hình Activity an toàn với cờ FLAG_SECURE, quản lý vòng đời đúng chuẩn và sử dụng ADB để kiểm tra cây phân cấp ngăn xếp Task trên thiết bị thật:"
        ),
        code_snippet=(
            "kotlin",
            """// Mã nguồn Activity bảo mật: MainActivity.kt
package com.backend.androidsec

import android.os.Bundle
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import com.backend.androidsec.databinding.ActivityMainBinding

class SecureBankingActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 1. Kích hoạt FLAG_SECURE ngăn chặn chụp màn hình và Task Snapshot rò rỉ
        window.setFlags(
            WindowManager.LayoutParams.FLAG_SECURE,
            WindowManager.LayoutParams.FLAG_SECURE
        )

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 2. Khôi phục trạng thái từ Bundle nếu có
        savedInstanceState?.let { bundle ->
            val cachedAccount = bundle.getString("SESSION_ACCOUNT_ID")
            binding.tvAccount.text = cachedAccount ?: "Khách vãng lai"
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        // Lưu tạm thời thông tin định danh UI không nhạy cảm
        outState.putString("SESSION_ACCOUNT_ID", binding.tvAccount.text.toString())
    }
}"""
        ),
        pitfalls=[
            "Tuyệt đối không lưu mật khẩu hoặc khóa AES đối xứng vào đối tượng Bundle trong onSaveInstanceState vì Bundle có thể bị ghi xuống disk tạm thời dưới dạng unencrypted parcel.",
            "Không giữ tham chiếu Activity Context trong các đối tượng Singleton dài hạn để tránh rò rỉ toàn bộ cây phân cấp View."
        ],
        summary_points=[
            "Activity chuyển qua 7 trạng thái vòng đời từ onCreate đến onDestroy.",
            "Cờ WindowManager.LayoutParams.FLAG_SECURE là lá chắn bắt buộc cho mọi màn hình xử lý dữ liệu tài chính/xác thực.",
            "Quản lý Launch Mode đúng đắn giúp ngăn chặn tấn công Activity Hijacking và Task Injection."
        ],
        video_url=VIDEO_CACHE[1]["url"],
        quiz_items=[
            {
                "type": "MULTIPLE_CHOICE",
                "question": "Cờ WindowManager nào bắt buộc phải thiết lập để vô hiệu hóa tính năng chụp ảnh màn hình và ngăn hệ thống tạo snapshot trong cửa sổ ứng dụng gần đây (Recent Apps)?",
                "options": [
                    "A. WindowManager.LayoutParams.FLAG_SECURE",
                    "B. WindowManager.LayoutParams.FLAG_FULLSCREEN",
                    "C. WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON",
                    "D. WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED"
                ],
                "correct_index": 0,
                "explanation": "FLAG_SECURE ngăn không cho hệ thống và ứng dụng thứ ba chụp ảnh màn hình hoặc xem nội dung trong cửa sổ ứng dụng gần đây."
            },
            {
                "type": "FILL_BLANK",
                "question": "Phương thức callback nào trong vòng đời Activity được gọi khi Activity bắt đầu bước vào trạng thái tương tác trực tiếp (Foreground) với người dùng?",
                "blanks": [
                    {"accepted_answers": ["onResume", "onResume()", "onresume"]}
                ],
                "explanation": "onResume() là thời điểm Activity có đầy đủ tiêu điểm tương tác và nằm ở đỉnh ngăn xếp hiển thị."
            },
            {
                "type": "MATCHING",
                "question": "Hãy nối từng Launch Mode của Activity với hành vi quản lý ngăn xếp Task tương ứng:",
                "pairs": [
                    {"left": "standard", "right": "Luôn tạo một instance Activity mới đẩy lên đỉnh ngăn xếp"},
                    {"left": "singleTop", "right": "Tái sử dụng instance hiện tại nếu nó đang nằm ngay đỉnh ngăn xếp"},
                    {"left": "singleTask", "right": "Chỉ duy trì 1 instance trong Task, hủy mọi Activity nằm phía trên"},
                    {"left": "singleInstance", "right": "Chạy độc quyền trong một Task riêng biệt không chia sẻ"}
                ],
                "explanation": "Hiểu rõ 4 launchMode giúp kiểm soát điều hướng và phòng chống tấn công điều hướng độc hại."
            },
            {
                "type": "FILL_BLANK",
                "question": "Để bảo toàn dữ liệu nhập liệu của người dùng khi thiết bị xoay màn hình, lập trình viên lưu trạng thái vào đối tượng [_____] thông qua callback onSaveInstanceState, hoặc sử dụng thành phần kiến trúc [_____].",
                "blanks": [
                    {"accepted_answers": ["Bundle", "bundle", "đối tượng bundle"]},
                    {"accepted_answers": ["ViewModel", "viewmodel", "AndroidViewModel"]}
                ],
                "explanation": "Dữ liệu được lưu trữ dạng key-value trong Bundle hoặc duy trì liên tục trong ViewModel xuyên suốt chu kỳ sống của Activity."
            }
        ]
    )
    validate_lesson_data({
        "title": "Bài 1.2: Vòng Đời Activity",
        "markdown_content": l2_md,
        "video_url": VIDEO_CACHE[1]["url"]
    })
    lessons.append({
        "position": 2,
        "title": "Bài 1.2: Vòng Đời Activity (Activity Lifecycle), Quản Lý Ngăn Xếp Task & Phục Hồi Trạng Thái Giao Diện",
        "summary": "Nghiên cứu chu kỳ sống Activity, ngăn xếp Task, cờ bảo mật FLAG_SECURE và kỹ thuật chống rò rỉ bộ nhớ.",
        "duration_minutes": 45,
        "video_url": VIDEO_CACHE[1]["url"],
        "markdown_content": l2_md,
    })

    # Generate remaining lessons for Chapter 1 (1.3 to 1.12)
    ch1_specs = [
        (
            3,
            "Bài 1.3: Dịch Vụ Nền (Services): Started Service, Bound Service, Foreground Service & ANR Defense",
            "Nghiên cứu kiến trúc Services trong Android, kỹ thuật chạy nền dài hạn, kết nối Binder và cơ chế chống treo ứng dụng ANR.",
            [
                "Phân biệt rõ ràng giữa Started Service, Bound Service và Foreground Service.",
                "Nắm vững giới hạn chạy nền (Background Execution Limits) khắt khe từ Android 8.0 trở lên.",
                "Hiểu cơ chế vận hành của thông báo đính kèm bắt buộc trong Foreground Service.",
                "Phân tích nguyên nhân và giải pháp triệt tiêu lỗi Application Not Responding (ANR)."
            ],
            [
                ("Phân Loại Ba Hình Thái Dịch Vụ Android", "Service là thành phần ứng dụng không có giao diện trực quan, chịu trách nhiệm thực thi các tác vụ nền dài hạn. Started Service được kích hoạt qua `startService(Intent)` và chạy độc lập cho đến khi tự gọi `stopSelf()`. Bound Service hoạt động theo mô hình Client-Server thông qua `bindService()`, trả về một interface IBinder để các thành phần khác giao tiếp hai chiều. Foreground Service là dịch vụ có mức độ ưu tiên cao nhất, bắt buộc phải hiển thị một thông báo thường trực (Ongoing Notification) trên thanh trạng thái để người dùng nhận biết rõ ràng ứng dụng đang tiêu thụ tài nguyên."),
                ("Giới Hạn Chạy Nền Từ Android 8.0 & Worker Migration", "Nhằm bảo vệ thời lượng pin và tối ưu hóa bộ nhớ, từ Android 8.0 (API 26), hệ thống cấm các ứng dụng ở trạng thái background tự ý gọi `startService()`. Nếu cố tình thực thi, hệ thống sẽ ném ngoại lệ `IllegalStateException`. Thay vào đó, nhà phát triển phải chuyển sang sử dụng `startForegroundService()` kèm lệnh `startForeground()` trong vòng 5 giây, hoặc di chuyển các tác vụ định kỳ sang WorkManager và JobScheduler."),
                ("Cơ Chế Phát Hiện ANR & Phân Bổ Luồng Riêng Biệt", "Mặc dù Service là tác vụ chạy nền, mặc định nó vẫn chạy trên luồng chính UI (Main Thread). Nếu Service thực hiện các thao tác tốn thời gian như truy vấn cơ sở dữ liệu, đọc ghi tập tin lớn hoặc gọi API mạng, Main Thread sẽ bị nghẽn. Nếu Main Thread bị chặn quá 5 giây (đối với tương tác chạm) hoặc 20 giây (đối với BroadcastReceiver), hệ điều hành sẽ kích hoạt hộp thoại ANR (Application Not Responding) cho phép người dùng buộc dừng ứng dụng.")
            ],
            "Kịch bản tấn công: Khai thác dịch vụ không được bảo vệ (Exported Service). Nếu một Service đặt cờ `android:exported=\"true\"` mà không thiết lập permission kiểm soát, bất kỳ ứng dụng độc hại nào trên cùng thiết bị cũng có thể gửi Intent kích hoạt dịch vụ hoặc kết nối IPC để chiếm đoạt tài nguyên. Phòng thủ: Luôn đặt `android:exported=\"false\"` cho các Service nội bộ. Với dịch vụ công khai, bắt buộc khai báo `android:permission` với cấp độ bảo vệ `signature`.",
            "Trong phần thực hành, chúng ta sẽ xây dựng một Foreground Service chuẩn mực với Channel Notification và sử dụng ADB dumpsys để kiểm tra trạng thái tiến trình:",
            ("kotlin", """// Khởi tạo Foreground Service an toàn
val intent = Intent(context, SecureDownloadService::class.java)
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
    context.startForegroundService(intent)
} else {
    context.startService(intent)
}"""),
            ["Không bao giờ thực thi tác vụ I/O chặn (blocking I/O) trực tiếp trên luồng chính của Service.", "Đảm bảo gọi startForeground() trong vòng 5 giây sau khi gọi startForegroundService() để tránh lỗi crash hệ thống."],
            ["Foreground Service đòi hỏi notification liên tục để bảo đảm tính minh bạch với người dùng.", "Background Limits từ Android 8.0 yêu cầu chuyển dịch tác vụ sang WorkManager.", "Dịch vụ nội bộ bắt buộc phải khóa cờ android:exported=\"false\"."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Từ Android 8.0 (API 26), loại dịch vụ nền nào bắt buộc phải hiển thị thông báo liên tục (ongoing notification) nếu muốn chạy tác vụ dài hạn?", "options": ["A. Foreground Service", "B. Background Service", "C. IntentService", "D. Bound Service"], "correct_index": 0, "explanation": "Foreground Service thông báo minh bạch cho người dùng và được hệ thống cấp độ ưu tiên tiến trình cao."},
                {"type": "FILL_BLANK", "question": "Hộp thoại cảnh báo treo ứng dụng do luồng giao diện chính bị chặn quá thời gian quy định có tên viết tắt là [_____].", "blanks": [{"accepted_answers": ["ANR", "anr", "Application Not Responding"]}], "explanation": "ANR (Application Not Responding) xuất hiện khi Main UI Thread bị block quá 5 giây đối với input events."},
                {"type": "MATCHING", "question": "Nối loại Service với đặc tính vận hành:", "pairs": [{"left": "Started Service", "right": "Khởi chạy qua startService và hoạt động độc lập cho đến khi stopSelf"}, {"left": "Bound Service", "right": "Cung cấp giao diện IBinder tương tác hai chiều Client-Server"}, {"left": "Foreground Service", "right": "Được ưu tiên cao và bắt buộc hiển thị Notification liên tục"}] , "explanation": "Mỗi loại dịch vụ phục vụ một mục đích kiến trúc khác nhau."},
                {"type": "FILL_BLANK", "question": "Để bảo vệ Service nội bộ không bị ứng dụng thứ ba tùy tiện kích hoạt, thuộc tính trong thẻ manifest bắt buộc gán là android:exported=\"[_____]\".", "blanks": [{"accepted_answers": ["false", "FALSE"]}], "explanation": "android:exported=\"false\" ngăn chặn các tiến trình bên ngoài gửi Intent đến dịch vụ."}
            ]
        ),
        (
            4,
            "Bài 1.4: Bộ Thu Phát Sóng (Broadcast Receivers), Quản Lý Intent Filters & Bảo Mật Phát Sóng",
            "Nghiên cứu cơ chế gửi nhận thông điệp toàn hệ thống qua Broadcast Receivers, bảo mật Intent và chống nghe lén thông tin.",
            [
                "Phân biệt Static Receivers (khai báo manifest) và Dynamic Receivers (đăng ký qua mã nguồn).",
                "Hiểu cơ chế vận hành của Normal Broadcast, Ordered Broadcast và LocalBroadcastManager.",
                "Nhận diện lỗ hổng nghe lén Broadcast (Broadcast Sniffing) và giả mạo phát sóng (Broadcast Injection).",
                "Thiết lập Permission bảo vệ phát sóng hai chiều giữa ứng dụng phát và nhận."
            ],
            [
                ("Bản Chất Kiến Trúc Của Broadcast Receiver", "Broadcast Receiver là thành phần cho phép ứng dụng đăng ký lắng nghe các sự kiện phát thanh từ hệ thống (như pin yếu, cắm sạc, bật chế độ máy bay, khởi động xong hệ điều hành) hoặc từ các ứng dụng khác. Có 2 cách đăng ký: Static (trong AndroidManifest.xml) và Dynamic (thông qua `context.registerReceiver()`). Từ Android 8.0, Google hạn chế hầu hết các implicit broadcast đăng ký qua manifest nhằm tiết kiệm pin."),
                ("Phân Loại Cơ Chế Phát Sóng", "Android cung cấp 2 phương thức phát sóng chính: Normal Broadcast (`sendBroadcast`): mọi receiver nhận thông điệp đồng thời không theo thứ tự, không thể ngăn chặn gói tin. Ordered Broadcast (`sendOrderedBroadcast`): thông điệp được chuyển tuần tự theo mức ưu tiên `android:priority`. Mỗi receiver có thể xử lý, chỉnh sửa dữ liệu hoặc gọi `abortBroadcast()` để ngắt toàn bộ chuỗi phát sóng."),
                ("Nguy Cơ Nghe Lén & Giả Mạo Phát Sóng", "Khi phát sóng một Intent công khai không có đích đến cụ thể (implicit broadcast), mọi ứng dụng cài đặt trên thiết bị đều có thể đăng ký receiver để nghe lén dữ liệu nhạy cảm (như mã OTP, token phiên, vị trí GPS). Ngược lại, nếu một receiver mở công khai mà không kiểm tra người gửi, kẻ tấn công có thể giả mạo Intent để kích hoạt các hành vi trái phép.")
            ],
            "Kịch bản tấn công: Kẻ tấn công tạo một ứng dụng độc hại có Receiver với priority cực cao (999) trong Ordered Broadcast để cướp và chỉnh sửa dữ liệu trước khi đến ứng dụng chính thống. Phòng thủ: Sử dụng Explicit Intent (chỉ định rõ tên package và class đích). Khi truyền thông nội bộ, luôn ưu tiên sử dụng EventBus hoặc StateFlow/SharedFlow thay cho Broadcast toàn hệ thống. Nếu cần phát sóng liên ứng dụng, phải gán quyền bảo vệ `sendBroadcast(intent, \"com.backend.CUSTOM_PERMISSION\")`.",
            "Trong phần thực hành, chúng ta sẽ đăng ký một Dynamic Receiver an toàn với cờ RECEIVER_NOT_EXPORTED theo chuẩn Android 14+:",
            ("kotlin", """// Đăng ký Dynamic Receiver an toàn
val filter = IntentFilter("com.backend.ACTION_SECURE_EVENT")
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
    context.registerReceiver(myReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
} else {
    context.registerReceiver(myReceiver, filter)
}"""),
            ["Không bao giờ truyền dữ liệu nhạy cảm qua Implicit Broadcast.", "Từ Android 14, mọi dynamic receiver bắt buộc phải khai báo cờ RECEIVER_EXPORTED hoặc RECEIVER_NOT_EXPORTED."],
            ["Broadcast Receivers tiếp nhận các thông điệp sự kiện của hệ thống và ứng dụng.", "Ordered Broadcast cho phép kiểm soát thứ tự và ngắt thông điệp bằng abortBroadcast().", "Explicit Intent và custom permission là phương thức phòng vệ cốt lõi."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Phương thức phát sóng nào cho phép các Receiver tiếp nhận thông điệp theo thứ tự ưu tiên và có quyền ngắt thông điệp bằng abortBroadcast()?", "options": ["A. Ordered Broadcast", "B. Normal Broadcast", "C. Sticky Broadcast", "D. Local Broadcast"], "correct_index": 0, "explanation": "sendOrderedBroadcast phát thông điệp tuần tự theo cờ priority và cho phép receiver gọi abortBroadcast()."},
                {"type": "FILL_BLANK", "question": "Từ Android 14 (API 34), khi đăng ký Dynamic Receiver nội bộ, cờ ngữ cảnh bắt buộc phải truyền vào hàm registerReceiver là Context.RECEIVER_[_____].", "blanks": [{"accepted_answers": ["NOT_EXPORTED", "not_exported", "RECEIVER_NOT_EXPORTED"]}], "explanation": "Context.RECEIVER_NOT_EXPORTED đảm bảo receiver chỉ nhận broadcast từ chính ứng dụng của mình."},
                {"type": "MATCHING", "question": "Nối loại broadcast với đặc tính tương ứng:", "pairs": [{"left": "Explicit Broadcast", "right": "Chỉ định đích danh Component hoặc Package nhận gói tin"}, {"left": "Implicit Broadcast", "right": "Phát tán rộng rãi theo Intent Filter và hành động Action"}, {"left": "Ordered Broadcast", "right": "Truyền tuần tự theo mức ưu tiên android:priority"}] , "explanation": "Phân biệt các kiểu phát sóng giúp bảo vệ dữ liệu trong luồng IPC."},
                {"type": "FILL_BLANK", "question": "Hàm dùng để hủy bỏ hoàn toàn việc chuyển tiếp gói tin trong Ordered Broadcast có tên là [_____]Broadcast().", "blanks": [{"accepted_answers": ["abort", "abortBroadcast", "Abort"]}], "explanation": "abortBroadcast() ngăn chặn các receiver phía sau tiếp nhận thông điệp."}
            ]
        ),
        (
            5,
            "Bài 1.5: Nhà Cung Cấp Nội Dung (Content Providers), Khai Thác SQLite & Lỗ Hổng SQL Injection",
            "Nghiên cứu cơ chế chia sẻ dữ liệu liên ứng dụng qua Content Providers, cấu trúc URI và kỹ thuật phòng thủ SQL Injection trong SQLite.",
            [
                "Nắm vững kiến trúc Content Provider và cơ chế ánh xạ Content URI (`content://`).",
                "Hiểu cách thức phân quyền hạt mịn (Granular URI Permissions) bằng cờ `grantUriPermissions`.",
                "Phân tích lỗ hổng SQL Injection trên Android SQLite khi sử dụng nối chuỗi truy vấn thô.",
                "Áp dụng Room Persistence Library và Parameterized Queries để bảo đảm an toàn dữ liệu."
            ],
            [
                ("Kiến Trúc Content Provider & Mô Hình URI", "Content Provider là cơ chế chuẩn hóa của Android cho phép chia sẻ dữ liệu có cấu trúc giữa các ứng dụng độc lập một cách an toàn. Mọi tài nguyên trong Provider được định danh qua một Content URI có định dạng chuẩn: `content://<authority>/<path>/<id>`. Trong đó, `authority` là tên định danh duy nhất (thường là package name kèm đuôi `.provider`), `path` xác định bảng hoặc loại dữ liệu, và `id` trỏ đến bản ghi cụ thể."),
                ("Cơ Chế Phân Quyền Hạt Mịn (Granular URI Permissions)", "Một trong những điểm mạnh nhất của Content Provider là khả năng cấp quyền truy cập tạm thời cho các ứng dụng khác mà không cần cấp toàn bộ quyền truy cập dữ liệu. Thông qua cờ Intent `FLAG_GRANT_READ_URI_PERMISSION` và `FLAG_GRANT_WRITE_URI_PERMISSION`, ứng dụng chủ quản có thể ủy quyền cho một Activity hoặc Service của ứng dụng khác đọc/ghi duy nhất một tệp tin hoặc bản ghi cụ thể. Quyền này tự động thu hồi khi ngăn xếp Task kết thúc."),
                ("Lỗ Hổng SQL Injection Trong Tầng Lưu Trữ SQLite", "Nhiều ứng dụng Android sử dụng SQLiteDatabase trực tiếp và tạo câu lệnh SQL bằng cách nối chuỗi thô: `rawQuery(\"SELECT * FROM users WHERE name = '\" + input + \"'\", null)`. Kẻ tấn công có thể chèn các ký tự điều khiển (`' OR '1'='1`) để vượt qua cơ chế xác thực hoặc trích xuất toàn bộ bảng dữ liệu. Khi Content Provider bị exported và dính lỗi SQLi, bất kỳ ứng dụng độc hại nào trên máy cũng có thể khai thác để cướp dữ liệu.")
            ],
            "Kịch bản tấn công: Khai thác SQL Injection trong Content Provider bằng công cụ Drozer hoặc script Java: kẻ tấn công gửi truy vấn URI với tham số projection hoặc selection chứa cú pháp injection: `content://com.victim.provider/users?projection=*`. Phòng thủ: Tuyệt đối không nối chuỗi trong `query()`, `update()`, `delete()`. Sử dụng tham số thay thế `?` với selectionArgs. Chuyển đổi toàn bộ tầng dữ liệu sang Jetpack Room ORM - nơi mọi truy vấn đều được kiểm tra an toàn cú pháp tại thời điểm biên dịch.",
            "Trong phần thực hành, chúng ta sẽ cấu hình Content Provider an toàn và kiểm tra truy vấn tham số hóa trong SQLite:",
            ("kotlin", """// Truy vấn an toàn với selectionArgs
val projection = arrayOf("id", "username", "email")
val selection = "username = ? AND status = ?"
val selectionArgs = arrayOf(userInputUsername, "ACTIVE")

val cursor = contentResolver.query(
    UserContract.CONTENT_URI,
    projection,
    selection,
    selectionArgs,
    "created_at DESC"
)"""),
            ["Không bao giờ ghép trực tiếp chuỗi nhập liệu của người dùng vào mệnh đề WHERE hoặc SELECTION.", "Kiểm tra kỹ thuộc tính android:grantUriPermissions để không vô tình mở rộng quyền truy cập toàn bộ cây dữ liệu."],
            ["Content Provider chuẩn hóa việc chia sẻ dữ liệu liên ứng dụng qua Content URI.", "Cờ grantUriPermissions cung cấp ủy quyền hạt mịn tạm thời theo phiên.", "Luôn sử dụng tham số hóa truy vấn hoặc Jetpack Room để triệt tiêu SQL Injection."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tiền tố chuẩn bắt buộc (Scheme) trong chuỗi Uniform Resource Identifier (URI) để định danh tài nguyên của Content Provider là gì?", "options": ["A. content://", "B. http://", "C. file://", "D. android://"], "correct_index": 0, "explanation": "Mọi Content URI của Android đều bắt đầu bằng scheme 'content://' theo quy ước hệ thống."},
                {"type": "FILL_BLANK", "question": "Kỹ thuật bảo mật cốt lõi để ngăn ngừa hoàn toàn lỗ hổng SQL Injection khi thực hiện truy vấn cơ sở dữ liệu là sử dụng câu truy vấn có [_____] (Parameterized Query) thay vì nối chuỗi.", "blanks": [{"accepted_answers": ["tham số hóa", "tham số", "parameterized", "tham số hoá"]}], "explanation": "Truy vấn tham số hóa phân tách rạch ròi giữa câu lệnh thực thi và dữ liệu đầu vào."},
                {"type": "MATCHING", "question": "Nối các phần trong chuỗi URI content://com.backend.provider/accounts/123:", "pairs": [{"left": "content://", "right": "Scheme chuẩn của Content Provider"}, {"left": "com.backend.provider", "right": "Authority duy nhất định danh Provider"}, {"left": "accounts", "right": "Path xác định bảng hoặc tập hợp tài nguyên"}, {"left": "123", "right": "ID định danh bản ghi dữ liệu cụ thể"}] , "explanation": "Cấu trúc URI phân tầng giúp định vị chính xác dữ liệu trong hệ thống."},
                {"type": "FILL_BLANK", "question": "Cờ Intent dùng để cấp quyền đọc tạm thời cho một URI cụ thể tới ứng dụng khác có tên là FLAG_GRANT_[_____]_URI_PERMISSION.", "blanks": [{"accepted_answers": ["READ", "read"]}], "explanation": "FLAG_GRANT_READ_URI_PERMISSION ủy quyền đọc hạt mịn cho Intent đích mà không cần cấp quyền vĩnh viễn."}
            ]
        ),
        (
            6,
            "Bài 1.6: Giải Phẫu Tập Tin Gói Cài Đặt APK: classes.dex, resources.arsc & AndroidManifest.xml",
            "Nghiên cứu cấu trúc nhị phân của tập tin APK, cơ chế đóng gói tài nguyên và phân tích manifest chuyên sâu.",
            [
                "Nắm vững cấu trúc định dạng tệp ZIP của APK và các thư mục cốt lõi.",
                "Hiểu vai trò của classes.dex, resources.arsc, res/ và assets/.",
                "Giải mã tệp AndroidManifest.xml nhị phân và các thẻ cấu hình an ninh trọng yếu.",
                "Phân tích cơ chế nạp lớp đa tệp Multidex khi ứng dụng vượt quá giới hạn 65.536 phương thức."
            ],
            [
                ("Cấu Trúc Tệp Nén APK (Android Package Format)", "Tệp APK về bản chất là một tệp nén định dạng chuẩn ZIP được ký số điện tử. Khi giải nén một tệp APK, chúng ta sẽ thấy cấu trúc thư mục bao gồm: "
                "`classes.dex`: Tệp bytecode Dalvik/ART được biên dịch từ toàn bộ mã nguồn Java/Kotlin của dự án. "
                "`resources.arsc`: Bảng tài nguyên nhị phân được biên dịch trước (pre-compiled binary resources), chứa ánh xạ ID (R.id, R.string) tới các giá trị chuỗi, màu sắc và style. "
                "`AndroidManifest.xml`: Tệp bản kê khai nhị phân (AXML) mô tả thông tin ứng dụng, quyền hạn, thành phần và điều kiện phần cứng. "
                "`res/`: Thư mục chứa các tài nguyên chưa được nén thành arsc như layout XML, drawable PNG/SVG nhị phân. "
                "`assets/`: Chứa các tệp tĩnh nguyên bản được nạp qua AssetManager (như font chữ, mô hình AI, cấu hình JSON). "
                "`lib/`: Chứa các thư viện liên kết động native (.so) phân chia theo kiến trúc vi xử lý (arm64-v8a, armeabi-v7a, x86_64). "
                "`META-INF/`: Chứa chữ ký số của nhà phát triển (MANIFEST.MF, CERT.SF, CERT.RSA)."),
                ("Định Dạng classes.dex & Cơ Chế Multidex", "Mỗi tệp classes.dex được thiết kế với bảng chỉ mục phương thức sử dụng số nguyên 16-bit. Do đó, một tệp DEX chỉ có thể tham chiếu tối đa 65.536 phương thức (64K reference limit). Khi ứng dụng lớn dần và tích hợp nhiều thư viện bên thứ ba, số lượng phương thức vượt quá 64K sẽ buộc hệ thống phải kích hoạt chế độ Multidex, tạo ra `classes2.dex`, `classes3.dex`. ART nạp các tệp dex này tuần tự vào PathClassLoader."),
                ("Tệp Bản Kê Khai AndroidManifest.xml Nhị Phân", "Khi biên dịch bằng công cụ AAPT2 (Android Asset Packaging Tool), tệp manifest dạng văn bản được chuyển đổi thành định dạng nhị phân mã hóa AXML nhằm tối ưu hóa dung lượng và tốc độ phân tích cú pháp của hệ thống. Tệp này chứa các cờ bảo mật sống còn: `android:debuggable` (cho phép đính kèm debugger), `android:allowBackup` (cho phép sao lưu dữ liệu qua ADB), và `android:usesCleartextTraffic` (cho phép truyền thông HTTP không mã hóa).")
            ],
            "Kịch bản tấn công: Kẻ tấn công sử dụng Apktool để giải nén APK thành mã Smali và khôi phục AndroidManifest.xml dạng văn bản. Nếu ứng dụng để cờ `android:allowBackup=\"true\"`, kẻ tấn công có quyền cắm cáp USB và chạy lệnh `adb backup` để sao chép toàn bộ cơ sở dữ liệu SQLite, SharedPreferences chứa token đăng nhập của người dùng về máy tính cá nhân mà không cần quyền Root! Phòng thủ: Luôn đặt `android:allowBackup=\"false\"` trong manifest trừ khi có kiến trúc sao lưu đám mây tùy biến an toàn.",
            "Trong phần thực hành, chúng ta sẽ sử dụng tiện ích aapt2 và unzip để kiểm tra cấu trúc APK thực tế:",
            ("bash", """# 1. Liệt kê nội dung tệp APK dạng ZIP
unzip -l app-release.apk | head -n 25

# 2. Trích xuất thông tin cấu hình từ AndroidManifest.xml nhị phân bằng aapt2
aapt2 dump badging app-release.apk

# 3. Đếm số lượng phương thức trong tệp classes.dex (kiểm tra giới hạn 64K)
dexdump -f classes.dex | grep method_ids_size"""),
            ["Tuyệt đối không để cờ android:debuggable=\"true\" trong bản phát hành production vì nó cho phép bất kỳ ai đính kèm jdb/Frida vào tiến trình.", "Kiểm tra kỹ cờ android:allowBackup để tránh rò rỉ dữ liệu qua cáp sạc công cộng."],
            ["Tệp APK là kho lưu trữ ZIP chứa mã thực thi classes.dex, tài nguyên resources.arsc và manifest nhị phân.", "Giới hạn 64K phương thức được giải quyết thông qua cơ chế Multidex.", "Cờ debuggable và allowBackup là hai lỗ hổng phổ biến nhất trong cấu hình manifest."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tệp nào trong cấu trúc gói cài đặt APK chứa toàn bộ mã bytecode Dalvik/ART đã được biên dịch từ mã nguồn Java/Kotlin?", "options": ["A. classes.dex", "B. resources.arsc", "C. AndroidManifest.xml", "D. MANIFEST.MF"], "correct_index": 0, "explanation": "classes.dex chứa bytecode nhị phân được máy ảo ART thực thi."},
                {"type": "FILL_BLANK", "question": "Giới hạn tối đa số lượng phương thức mà một tệp DEX đơn lẻ có thể tham chiếu trước khi cần kích hoạt Multidex là [_____] phương thức.", "blanks": [{"accepted_answers": ["65536", "65.536", "64K", "64k", "65,536"]}], "explanation": "Giới hạn 65.536 bắt nguồn từ việc sử dụng trường 16-bit để đánh chỉ mục method references."},
                {"type": "MATCHING", "question": "Nối các thành phần trong tệp APK với nhiệm vụ của chúng:", "pairs": [{"left": "classes.dex", "right": "Chứa mã bytecode đã biên dịch của ứng dụng"}, {"left": "resources.arsc", "right": "Bảng tài nguyên nhị phân ánh xạ ID và giá trị giao diện"}, {"left": "lib/<abi>/", "right": "Thư mục chứa các tệp thư viện liên kết động C/C++ (.so)"}, {"left": "META-INF/", "right": "Thư mục chứa chữ ký số và chứng chỉ bảo mật của APK"}] , "explanation": "Mỗi thư mục trong APK đảm nhiệm một vai trò thiết yếu cho việc cài đặt và thực thi."},
                {"type": "FILL_BLANK", "question": "Cờ cấu hình trong thẻ <application> của manifest nếu đặt bằng 'true' sẽ cho phép người dùng trích xuất toàn bộ dữ liệu ứng dụng qua lệnh adb backup là android:[_____].", "blanks": [{"accepted_answers": ["allowBackup", "allowbackup", "allowBackup=\"true\""]}], "explanation": "android:allowBackup là cờ kiểm soát tính năng sao lưu dữ liệu qua ADB."}
            ]
        )
    ]

    # Additional lessons 1.7 to 1.12 to reach exactly 12 lessons
    ch1_specs_rest = [
        (
            7,
            "Bài 1.7: Giao Tiếp Liên Tiến Trình (IPC): Intent, Bundle & Khung Tuần Tự Hóa Parcelable vs Serializable",
            "Nghiên cứu cơ chế IPC qua Intent, so sánh hiệu năng giữa Parcelable và Serializable, phòng chống Deserialization Attacks.",
            ["Hiểu cách thức Intent và Bundle đóng gói dữ liệu truyền qua ranh giới tiến trình.", "Nắm vững nguyên lý hoạt động của Parcelable và sự khác biệt với Java Serializable.", "Phân tích rủi ro bảo mật từ các lỗ hổng chuyển đổi dữ liệu không an toàn (Insecure Deserialization).", "Tối ưu hóa kích thước TransactionTooLargeException trong giao tiếp Binder."],
            [
                ("Bản Chất Của Giao Tiếp IPC Qua Intent", "Trong hệ điều hành Android, mỗi ứng dụng chạy trong một không gian địa chỉ bộ nhớ ảo độc lập do nhân Linux bảo vệ. Khi một Activity muốn gửi dữ liệu sang một Activity khác hoặc một Service, dữ liệu không thể truyền qua tham chiếu con trỏ bộ nhớ trực tiếp mà bắt buộc phải tuần tự hóa (marshal) thành chuỗi byte, gửi qua driver Binder trong nhân Linux, rồi giải tuần tự hóa (unmarshal) tại tiến trình đích."),
                ("So Sánh Parcelable Và Java Serializable", "Java Serializable là cơ chế tuần tự hóa tiêu chuẩn của ngôn ngữ Java, sử dụng Reflection để đọc cấu trúc lớp tại thời điểm chạy. Điều này tạo ra rác bộ nhớ lớn và tốc độ rất chậm. Ngược lại, Parcelable là giải pháp độc quyền được Google thiết kế riêng cho Android. Parcelable yêu cầu lập trình viên định nghĩa rõ ràng cách thức ghi (`writeToParcel`) và đọc (`createFromParcel`), giúp dữ liệu được sao chép trực tiếp vào bộ nhớ phẳng mà không cần reflection, mang lại hiệu năng cao hơn gấp 10 lần."),
                ("Giới Hạn Bộ Đệm Binder & TransactionTooLargeException", "Tất cả các giao dịch IPC sử dụng Binder (bao gồm truyền Bundle qua Intent) đều chia sẻ chung một vùng bộ đệm giao dịch có kích thước tối đa 1 MB cho mỗi tiến trình. Nếu ứng dụng cố gắng gửi một mảng byte ảnh chụp lớn hoặc danh sách dữ liệu hàng nghìn bản ghi qua Intent, hệ thống sẽ ngay lập tức ném ra lỗi `TransactionTooLargeException` làm ứng dụng bị crash đột ngột.")
            ],
            "Kịch bản tấn công: Tấn công Insecure Deserialization xảy ra khi ứng dụng sử dụng Java `Serializable` để giải tuần tự hóa các đối tượng phức tạp nhận từ Intent bên ngoài. Kẻ tấn công có thể chèn các chuỗi Gadget Chains để thực thi mã tùy ý (RCE). Phòng thủ: Luôn ưu tiên sử dụng Parcelable. Kiểm tra nghiêm ngặt kiểu dữ liệu khi đọc từ Intent: `intent.getParcelableExtra()`. Tuyệt đối không truyền các đối tượng dữ liệu nhạy cảm hoặc tệp tin kích thước lớn qua Intent; thay vào đó hãy lưu vào tệp bảo mật và chỉ truyền URI ủy quyền.",
            "Trong phần thực hành, chúng ta sẽ lập trình lớp dữ liệu Parcelable an toàn và đo đạc kích thước gói tin Parcel:",
            ("kotlin", """// Khai báo Parcelable tối ưu với @Parcelize
@Parcelize
data class UserSession(
    val userId: String,
    val role: String,
    val tokenHash: String
) : Parcelable"""),
            ["Không bao giờ truyền Bitmap hoặc dữ liệu nhị phân dung lượng lớn qua Intent Bundle.", "Tránh sử dụng Java Serializable thuần túy cho các giao tiếp IPC công khai."],
            ["Parcelable tối ưu hóa hiệu năng IPC cho Android nhờ triệt tiêu Reflection.", "Bộ đệm giao dịch Binder giới hạn tối đa 1 MB cho toàn bộ tiến trình.", "Kiểm soát chặt chẽ kiểu dữ liệu nhận từ Intent để ngăn chặn Deserialization Flaws."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Giao diện tuần tự hóa dữ liệu nào được Google thiết kế chuyên biệt cho Android để đạt hiệu năng IPC cao hơn nhiều lần so với Java Serializable?", "options": ["A. Parcelable", "B. JSONSerializable", "C. Externalizable", "D. XMLMarshal"], "correct_index": 0, "explanation": "Parcelable được tối ưu hóa cho bộ nhớ phẳng của Android IPC, không sử dụng reflection."},
                {"type": "FILL_BLANK", "question": "Ngoại lệ runtime xuất hiện khi dữ liệu truyền qua Intent Bundle vượt quá giới hạn bộ đệm Binder (khoảng 1 MB) có tên là [_____]Exception.", "blanks": [{"accepted_answers": ["TransactionTooLarge", "TransactionTooLargeException"]}], "explanation": "TransactionTooLargeException xảy ra khi kích thước Parcel vượt quá giới hạn 1MB của Binder buffer."},
                {"type": "MATCHING", "question": "Nối cơ chế tuần tự hóa với đặc điểm:", "pairs": [{"left": "Parcelable", "right": "Đặc thù Android, tốc độ cao, không dùng reflection"}, {"left": "Java Serializable", "right": "Chuẩn Java, sử dụng reflection, tốc độ chậm hơn"}, {"left": "Binder Buffer", "right": "Giới hạn dung lượng giao dịch tối đa 1 MB"}] , "explanation": "Lựa chọn công nghệ tuần tự hóa ảnh hưởng lớn đến hiệu năng và an toàn ứng dụng."},
                {"type": "FILL_BLANK", "question": "Annotation của Kotlin Android Extensions giúp tự động sinh mã Parcelable mà không cần viết boilerplate thủ công là @[_____].", "blanks": [{"accepted_answers": ["Parcelize", "parcelize"]}], "explanation": "@Parcelize tự động sinh implementation cho Parcelable một cách tối ưu và an toàn."}
            ]
        ),
        (
            8,
            "Bài 1.8: Quản Lý Tiến Trình Ứng Dụng, Máy Ảo Zygote & Quy Trình Khởi Tạo Ứng Dụng",
            "Nghiên cứu kiến trúc phân nhánh tiến trình từ Zygote, chuỗi khởi động init -> zygote -> system_server và phân bổ tài nguyên.",
            ["Làm chủ quy trình khởi tạo tiến trình ứng dụng thông qua phân nhánh (forking) từ Zygote daemon.", "Hiểu cơ chế Copy-on-Write (CoW) trong việc tối ưu hóa chia sẻ bộ nhớ RAM giữa các ứng dụng.", "Phân tích vai trò điều phối của tiến trình system_server và ActivityManagerService.", "Đánh giá các mức độ ưu tiên tiến trình (OOM Adj score) và hành vi thu hồi bộ nhớ."],
            [
                ("Tiến Trình Mẹ Zygote & Cơ Chế Khởi Động Nhanh", "Để giảm thiểu thời gian khởi động ứng dụng và tiết kiệm bộ nhớ RAM, Android không khởi chạy máy ảo ART từ con số không cho mỗi ứng dụng mới. Thay vào đó, trong quá trình khởi động hệ thống, tiến trình `init` khởi tạo tiến trình mẹ có tên là `zygote`. Zygote nạp sẵn vào bộ nhớ toàn bộ các lớp của Android Framework cốt lõi và các tài nguyên dùng chung, sau đó lắng nghe các yêu cầu khởi tạo qua Unix Domain Socket (`/dev/socket/zygote`)."),
                ("Cơ Chế Copy-On-Write (CoW) & Phân Nhánh Tiến Trình", "Khi người dùng nhấn vào biểu tượng ứng dụng, `system_server` gửi yêu cầu phân nhánh tới Zygote. Zygote thực thi lời gọi hệ thống `fork()` của Linux để tạo ra một tiến trình con là bản sao chính xác của chính nó. Nhờ cơ chế Copy-on-Write (CoW) của nhân Linux, các trang bộ nhớ chứa framework dùng chung không bị nhân bản mà được chia sẻ đọc giữa hàng chục ứng dụng, chỉ khi nào một ứng dụng sửa đổi dữ liệu thì trang bộ nhớ đó mới được cấp phát riêng."),
                ("Phân Cấp Tiến Trình & Trình Thu Hồi Bộ Nhớ Low Memory Killer (LMK)", "Android phân loại các tiến trình theo mức độ quan trọng giảm dần thông qua chỉ số OOM Adjustment (oom_adj/oom_score_adj): 1. Foreground Process (tiến trình đang tương tác trực tiếp), 2. Visible Process (tiến trình hiển thị nhưng không có tiêu điểm), 3. Service Process (tiến trình dịch vụ nền), 4. Cached Process (tiến trình lưu tạm trong bộ nhớ đệm). Khi bộ nhớ vật lý cạn kiệt, trình điều khiển LMK sẽ tự động tiêu diệt các tiến trình có điểm oom_score_adj cao nhất để bảo vệ hệ thống.")
            ],
            "Kịch bản tấn công: Phân tích quyền hạn tiến trình sau phân nhánh: Khi Zygote fork một tiến trình ứng dụng mới, nó phải thực hiện hạ đặc quyền ngay lập tức bằng cách gọi `setuid()` và `setgid()` để chuyển từ quyền root (UID 0) sang UID định danh riêng của ứng dụng (ví dụ UID 10123), đồng thời thiết lập môi trường sandbox SELinux. Nếu tiến trình hệ thống gặp lỗ hổng không hạ quyền thành công, ứng dụng có thể chạy với quyền root. Phòng thủ: Luôn kiểm tra tính toàn vẹn của tiến trình bằng cách xác minh UID thực tế qua `android.os.Process.myUid()`.",
            "Trong phần thực hành, chúng ta sẽ sử dụng ADB để tra cứu thông tin tiến trình Zygote và phân tích điểm OOM Score của ứng dụng:",
            ("bash", """# 1. Kiểm tra tiến trình zygote và zygote64
adb shell ps -A | grep zygote

# 2. Xem điểm oom_score_adj của một ứng dụng đang chạy
PID=$(adb shell pidof com.android.chrome)
adb shell cat /proc/$PID/oom_score_adj

# 3. Quan sát dung lượng bộ nhớ chia sẻ Clean/Dirty của ứng dụng
adb shell dumpsys meminfo com.android.chrome"""),
            ["Không bao giờ khởi tạo các tiến trình con bằng Runtime.getRuntime().exec() tùy tiện vì làm tăng đột biến mức tiêu thụ RAM.", "Hiểu rõ cơ chế LMK để không lưu trữ dữ liệu phiên quan trọng duy nhất trong bộ nhớ biến tạm."],
            ["Zygote nạp sẵn Framework và fork tiến trình mới nhanh chóng nhờ Copy-on-Write.", "system_server là trung tâm điều phối mọi dịch vụ cốt lõi của Android.", "Low Memory Killer (LMK) quản lý bộ nhớ dựa trên điểm số oom_adj."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tiến trình hệ thống nào trong Android chịu trách nhiệm nạp sẵn các lớp Framework và phân nhánh (fork) các tiến trình ứng dụng người dùng?", "options": ["A. Zygote", "B. init", "C. system_server", "D. kthreadd"], "correct_index": 0, "explanation": "Zygote là tiến trình daemon khởi tạo môi trường máy ảo và phân nhánh mọi app process."},
                {"type": "FILL_BLANK", "question": "Cơ chế quản lý bộ nhớ của nhân Linux cho phép các tiến trình con chia sẻ chung các trang bộ nhớ đọc của tiến trình mẹ và chỉ cấp phát khi có chỉnh sửa có tên viết tắt là [_____].", "blanks": [{"accepted_answers": ["CoW", "COW", "Copy-on-Write", "Copy on Write"]}], "explanation": "Copy-on-Write (CoW) giúp tiết kiệm hàng trăm megabyte RAM khi fork ứng dụng từ Zygote."},
                {"type": "MATCHING", "question": "Nối nhóm tiến trình với mức độ ưu tiên thu hồi của Low Memory Killer:", "pairs": [{"left": "Foreground Process", "right": "Đang tương tác trực tiếp, mức ưu tiên bảo vệ cao nhất"}, {"left": "Service Process", "right": "Đang chạy tác vụ nền, chỉ bị giải phóng khi thiếu RAM"}, {"left": "Cached Process", "right": "Ứng dụng ở trạng thái chờ, bị tiêu diệt đầu tiên khi cạn bộ nhớ"}] , "explanation": "LMK tự động dọn dẹp các tiến trình Cached trước để duy trì độ mượt của Foreground App."},
                {"type": "FILL_BLANK", "question": "Chỉ số được hệ điều hành gán cho mỗi tiến trình để quyết định thứ tự tiêu diệt khi cạn kiệt bộ nhớ có tên tệp trong /proc/<pid>/ là [_____].", "blanks": [{"accepted_answers": ["oom_score_adj", "oom_adj"]}], "explanation": "oom_score_adj quy định điểm phạt thu hồi bộ nhớ từ -1000 đến 1000."}
            ]
        ),
        (
            9,
            "Bài 1.9: Lập Trình Bất Đồng Bộ Trong Android: Coroutines, HandlerThread & WorkManager",
            "Nghiên cứu các mô hình xử lý bất đồng bộ hiện đại trong Kotlin, lập lịch tác vụ nền tin cậy với WorkManager.",
            ["Làm chủ Kotlin Coroutines: Dispatchers (Main, IO, Default), CoroutineScope và Structured Concurrency.", "Hiểu cơ chế Looper, MessageQueue và Handler trong việc giao tiếp giữa các luồng.", "Xây dựng các tác vụ chạy nền định kỳ đảm bảo tính sống sót với WorkManager.", "Phòng chống rò rỉ bộ nhớ khi thực thi các tác vụ mạng bất đồng bộ."],
            [
                ("Mô Hình Lập Trình Bất Đồng Bộ Với Kotlin Coroutines", "Trong phát triển Android hiện đại, Kotlin Coroutines là chuẩn mực không thể thay thế để xử lý các tác vụ bất đồng bộ mà không làm nghẽn luồng chính. Coroutines là các 'luồng nhẹ' (lightweight threads) cho phép tạm dừng (suspend) và tiếp tục (resume) mà không chiếm dụng tài nguyên hệ điều hành. Cơ chế Structured Concurrency đảm bảo rằng mọi Coroutine đều phải được khởi chạy trong một CoroutineScope cụ thể (như `viewModelScope` hoặc `lifecycleScope`), tự động hủy bỏ khi vòng đời kết thúc."),
                ("Kiến Trúc Looper, Handler & MessageQueue", "Mỗi luồng xử lý giao diện trong Android được gắn kết với một `Looper`. Looper duy trì một hàng đợi tin nhắn `MessageQueue` và liên tục lặp tuần hoàn để bốc tách các tác vụ (`Runnable` hoặc `Message`) gửi tới từ các luồng khác thông qua đối tượng `Handler`. Hiểu rõ cơ chế này giúp lập trình viên điều phối việc chuyển kết quả từ luồng tính toán nền về luồng giao diện một cách an toàn."),
                ("Lập Lịch Tác Vụ Bền Bỉ Với WorkManager", "Khi ứng dụng cần thực thi các tác vụ nền đòi hỏi tính đảm bảo cao (ngay cả khi ứng dụng bị tắt hoặc thiết bị khởi động lại - ví dụ như đồng bộ hóa nhật ký kiểm toán, tải dữ liệu phân tích), WorkManager là giải pháp duy nhất được khuyến nghị. WorkManager tự động lựa chọn cơ chế tối ưu dựa trên phiên bản Android (JobScheduler trên API 23+, hoặc AlarmManager + BroadcastReceiver trên bản cũ) và tuân thủ các điều kiện ràng buộc khắt khe (chỉ chạy khi có mạng Wifi hoặc đang cắm sạc).")
            ],
            "Kịch bản tấn công: Khai thác luồng chạy ngầm không được kiểm soát: Nếu ứng dụng khởi chạy các luồng Java `Thread` hoặc `AsyncTask` cũ kỹ mà không gắn kết với vòng đời, tác vụ sẽ tiếp tục chạy ngầm vô thời hạn, tiêu tốn pin, làm lộ dữ liệu hoặc tiếp tục gửi yêu cầu mạng chứa token đã hết hạn. Phòng thủ: Chuyển đổi 100% sang Kotlin Coroutines với Structured Concurrency. Đặt timeout nghiêm ngặt cho mọi tác vụ I/O qua `withTimeout(5000L)`.",
            "Trong phần thực hành, chúng ta sẽ viết một Coroutine Worker đồng bộ dữ liệu an toàn có ràng buộc mạng:",
            ("kotlin", """// Khởi tạo WorkRequest với ràng buộc mạng an toàn
val constraints = Constraints.Builder()
    .setRequiredNetworkType(NetworkType.UNMETERED)
    .setRequiresCharging(true)
    .build()

val syncWork = OneTimeWorkRequestBuilder<AuditSyncWorker>()
    .setConstraints(constraints)
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 15, TimeUnit.MINUTES)
    .build()

WorkManager.getInstance(context).enqueue(syncWork)"""),
            ["Không bao giờ sử dụng GlobalScope để khởi chạy Coroutines vì nó phá vỡ Structured Concurrency và dễ gây leak.", "Luôn sử dụng Dispatchers.IO cho các tác vụ truy vấn database hoặc gọi mạng."],
            ["Kotlin Coroutines mang lại giải pháp bất đồng bộ nhẹ và an toàn vòng đời.", "Looper và Handler là hạ tầng truyền thông điệp liên luồng của Android.", "WorkManager là công cụ chuẩn để lập lịch các tác vụ chạy nền bền bỉ."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Coroutine Dispatcher nào trong Kotlin Android được chỉ định chuyên trách cho việc đọc ghi tệp, truy vấn cơ sở dữ liệu và gọi API mạng?", "options": ["A. Dispatchers.IO", "B. Dispatchers.Main", "C. Dispatchers.Default", "D. Dispatchers.Unconfined"], "correct_index": 0, "explanation": "Dispatchers.IO tối ưu cho các tác vụ I/O chặn nhờ duy trì một thread pool linh hoạt."},
                {"type": "FILL_BLANK", "question": "Thư viện thành phần Jetpack dùng để lập lịch các tác vụ nền bền vững, đảm bảo thực thi ngay cả khi thiết bị khởi động lại là [_____].", "blanks": [{"accepted_answers": ["WorkManager", "workmanager"]}], "explanation": "WorkManager là giải pháp chuẩn hóa cho các tác vụ nền deferrable và guaranteed execution."},
                {"type": "MATCHING", "question": "Nối thành phần điều phối luồng với chức năng tương ứng:", "pairs": [{"left": "Looper", "right": "Duy trì vòng lặp tuần hoàn bốc tin nhắn từ MessageQueue"}, {"left": "Handler", "right": "Gửi và xử lý Message/Runnable giữa các luồng"}, {"left": "CoroutineScope", "right": "Quản lý ranh giới vòng đời và hủy bỏ tự động các tác vụ bất đồng bộ"}] , "explanation": "Mỗi thành phần đóng vai trò mấu chốt trong xử lý luồng của Android."},
                {"type": "FILL_BLANK", "question": "Nguyên lý kiến trúc của Coroutines yêu cầu mọi luồng con phải gắn kết với phạm vi cha để tránh rò rỉ tác vụ được gọi là [_____] Concurrency.", "blanks": [{"accepted_answers": ["Structured", "structured"]}], "explanation": "Structured Concurrency bảo đảm việc hủy bỏ và xử lý ngoại lệ theo cấu trúc cây phân cấp."}
            ]
        ),
        (
            10,
            "Bài 1.10: Kiến Trúc Ứng Dụng Hiện Đại: MVVM, MVI & Quản Lý Trạng Thái Với StateFlow & LiveData",
            "Nghiên cứu kiến trúc Model-View-ViewModel, phân tách mối quan tâm (Separation of Concerns) và dòng dữ liệu một chiều UDF.",
            ["Hiểu sâu nguyên lý phân tách tầng giữa UI Layer, Domain Layer và Data Layer theo Google Architecture Guide.", "Nắm vững cơ chế vận hành của ViewModel và vòng đời tồn tại xuyên suốt Configuration Changes.", "So sánh StateFlow (Kotlin Coroutines) và LiveData (Jetpack) trong quản lý trạng thái.", "Thiết lập luồng dữ liệu một chiều (Unidirectional Data Flow - UDF) an toàn."],
            [
                ("Nguyên Lý Kiến Trúc Phân Tách Tầng (Layered Architecture)", "Một ứng dụng Android chất lượng cao phải tuân thủ triệt để nguyên tắc Phân tách mối quan tâm (Separation of Concerns). Kiến trúc đề xuất của Google chia ứng dụng thành 3 phân tầng rõ rệt: 1. UI Layer (gồm Activity/Fragment và ViewModel) chịu trách nhiệm hiển thị dữ liệu và tiếp nhận tương tác người dùng; 2. Domain Layer (tùy chọn, gồm các UseCase) đóng gói các quy tắc nghiệp vụ phức tạp; 3. Data Layer (gồm Repositories và Data Sources) quản lý việc lấy dữ liệu từ mạng hoặc cơ sở dữ liệu cục bộ."),
                ("Vai Trò Của ViewModel & Vòng Đời Tồn Tại", "ViewModel là thành phần then chốt lưu trữ và quản lý dữ liệu liên quan đến giao diện người dùng. Điểm đặc biệt của ViewModel là vòng đời của nó được gắn kết với `ViewModelStore`, cho phép nó sống sót qua các sự kiện Configuration Change (như xoay màn hình). Trong khi Activity bị hủy và tạo lại, ViewModel vẫn giữ nguyên trạng thái trong bộ nhớ, loại bỏ hoàn toàn việc phải gọi lại API mạng tốn kém."),
                ("Dòng Dữ Liệu Một Chiều (UDF) Với StateFlow", "Trong mô hình MVI/MVVM hiện đại, dòng dữ liệu một chiều (Unidirectional Data Flow) là chìa khóa để triệt tiêu các lỗi bất đồng bộ trạng thái: Trạng thái (UI State) chảy xuống các thành phần hiển thị, trong khi Sự kiện người dùng (UI Events/Intents) chảy ngược lên ViewModel. `StateFlow` là một State-holder Observable Flow hiệu năng cao, luôn giữ một giá trị trạng thái hiện tại và chỉ phát thông báo khi giá trị thay đổi.")
            ],
            "Kịch bản tấn công: Rò rỉ trạng thái xác thực người dùng trong ViewModel: Nếu ViewModel lưu trữ token phiên đăng nhập hoặc thông tin tài khoản mà không được dọn dẹp khi người dùng nhấn 'Đăng xuất', instance ViewModel của Activity kế tiếp có thể vô tình tái sử dụng trạng thái cũ nếu scope không được giải phóng. Phòng thủ: Luôn cung cấp phương thức `clearSessionState()` trong ViewModel và dọn dẹp các luồng `Job` khi `onCleared()` được kích hoạt.",
            "Trong phần thực hành, chúng ta sẽ xây dựng một ViewModel an toàn sử dụng StateFlow với trạng thái UI niêm phong (Sealed Interface):",
            ("kotlin", """// Khởi tạo UI State bất biến với Sealed Interface
sealed interface LoginUiState {
    object Idle : LoginUiState
    object Loading : LoginUiState
    data class Success(val userId: String) : LoginUiState
    data class Error(val message: String) : LoginUiState
}

class LoginViewModel : ViewModel() {
    private val _uiState = MutableStateFlow<LoginUiState>(LoginUiState.Idle)
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()
}"""),
            ["Không bao giờ truyền tham chiếu Activity Context hoặc View vào trong ViewModel vì sẽ gây Memory Leak nghiêm trọng.", "Sử dụng asStateFlow() để che giấu MutableStateFlow khỏi việc bị chỉnh sửa trái phép từ tầng UI."],
            ["Kiến trúc phân tầng phân định rạch ròi trách nhiệm giữa UI, Domain và Data.", "ViewModel sống sót qua xoay màn hình, bảo vệ trạng thái UI liền mạch.", "StateFlow và Sealed Class xây dựng luồng dữ liệu một chiều UDF an toàn."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Thành phần kiến trúc nào của Android Jetpack được thiết kế để lưu trữ dữ liệu UI và sống sót qua các sự kiện thay đổi cấu hình (Configuration Change)?", "options": ["A. ViewModel", "B. Activity", "C. Fragment", "D. BroadcastReceiver"], "correct_index": 0, "explanation": "ViewModel tồn tại liên tục xuyên suốt quá trình Activity bị hủy và tạo lại do xoay màn hình."},
                {"type": "FILL_BLANK", "question": "Mô hình kiến trúc đảm bảo dữ liệu trạng thái chỉ chảy theo một hướng duy nhất từ ViewModel xuống UI có tên viết tắt là [_____] (Unidirectional Data Flow).", "blanks": [{"accepted_answers": ["UDF", "udf"]}], "explanation": "Unidirectional Data Flow (UDF) giúp trạng thái giao diện nhất quán và dễ kiểm thử."},
                {"type": "MATCHING", "question": "Nối phân tầng kiến trúc với nhiệm vụ tương ứng:", "pairs": [{"left": "UI Layer", "right": "Hiển thị dữ liệu lên màn hình và gửi sự kiện người dùng"}, {"left": "Domain Layer", "right": "Đóng gói các quy tắc nghiệp vụ độc lập trong các UseCase"}, {"left": "Data Layer", "right": "Quản lý truy xuất dữ liệu từ Local Database và Remote API"}] , "explanation": "Sự phân tách tầng giúp ứng dụng dễ mở rộng, bảo trì và kiểm thử tự động."},
                {"type": "FILL_BLANK", "question": "Phương thức callback được gọi tự động khi ViewModel chuẩn bị bị hủy hoàn toàn khỏi bộ nhớ là on[_____]().", "blanks": [{"accepted_answers": ["Cleared", "cleared", "Cleared()"]}], "explanation": "onCleared() là nơi giải phóng các tài nguyên, đóng coroutine scope và ngắt kết nối listeners."}
            ]
        ),
        (
            11,
            "Bài 1.11: Thiết Kế Giao Diện Đa Thiết Bị, Bố Cục Thích Ứng & Ràng Buộc ViewBinding",
            "Nghiên cứu kỹ thuật thiết kế giao diện đa kích thước màn hình, bảo mật ViewBinding và phòng chống Clickjacking.",
            ["Làm chủ kỹ thuật thiết kế Responsive Layout sử dụng ConstraintLayout và Jetpack Compose.", "Hiểu cơ chế vận hành an toàn kiểu dữ liệu (Type-Safety) của ViewBinding so với findViewById.", "Nhận diện và phòng chống tấn công chèn lớp phủ độc hại (Overlay Attack / Clickjacking).", "Kiểm soát quyền vẽ đè hệ thống SYSTEM_ALERT_WINDOW."],
            [
                ("Tiến Hóa Trong Thiết Kế Giao Diện Android", "Hệ sinh thái thiết bị Android vô cùng đa dạng với hàng ngàn kích thước màn hình, từ điện thoại thông minh, máy tính bảng, màn hình gập (foldables) đến Android TV và ô tô (Android Auto). Để đảm bảo trải nghiệm đồng nhất, nhà phát triển sử dụng hệ thống đơn vị đo độc lập điểm ảnh `dp` (density-independent pixels) và `sp` (scale-independent pixels cho font chữ), kết hợp với các bộ điều phối bố cục như `ConstraintLayout` hoặc giao diện khai báo hiện đại `Jetpack Compose`."),
                ("ViewBinding & Tính Toàn Vẹn Kiểu Dữ Liệu", "Trước đây, lập trình viên sử dụng `findViewById()` hoặc thư viện ButterKnife để ánh xạ giao diện XML. Cách làm này tiềm ẩn rủi ro ném lỗi `NullPointerException` tại thời điểm chạy nếu ID của View không tồn tại trong bố cục hiện tại. ViewBinding giải quyết triệt để vấn đề này bằng cách tự động sinh ra một lớp Binding tương ứng với mỗi tệp layout XML, cung cấp các tham chiếu có kiểm tra kiểu dữ liệu tĩnh (Null-Safety và Type-Safety) ngay tại thời điểm biên dịch."),
                ("Mối Đe Dọa Tấn Công Lớp Phủ (Overlay / Tapjacking Attack)", "Một trong những kỹ thuật tấn công giao diện nguy hiểm nhất trên Android là Tapjacking (Clickjacking). Ứng dụng độc hại xin quyền vẽ đè màn hình (`SYSTEM_ALERT_WINDOW`) và tạo ra một cửa sổ trong suốt hoặc hiển thị giao diện giả mạo (như một trò chơi hấp dẫn) đè ngay phía trên màn hình xác thực tài chính của ứng dụng ngân hàng. Khi người dùng bấm vào các nút trong trò chơi, cú chạm thực chất xuyên qua lớp phủ và xác nhận chuyển tiền trên ứng dụng ngân hàng phía dưới!")
            ],
            "Kịch bản tấn công: Kẻ tấn công tạo cửa sổ Overlay dạng `TYPE_APPLICATION_OVERLAY` che khuất cảnh báo bảo mật. Phòng thủ: Từ Android 12+, hệ thống tự động chặn các cú chạm không tin cậy đi qua lớp phủ. Đối với các phiên bản thấp hơn, nhà phát triển bắt buộc phải bật cờ chống đè cho View nhạy cảm: `view.filterTouchesWhenObscured = true`, hoặc ghi đè callback `onFilterTouchEventForSecurity(event)` để từ chối mọi sự kiện chạm khi phát hiện cờ `MotionEvent.FLAG_WINDOW_IS_OBSCURED`.",
            "Trong phần thực hành, chúng ta sẽ cấu hình ViewBinding và kích hoạt bộ lọc bảo mật chống Tapjacking:",
            ("kotlin", """// Bảo vệ nút xác thực chuyển tiền khỏi Tapjacking
binding.btnConfirmTransfer.apply {
    // Bật cờ tự động lọc bỏ sự kiện chạm nếu màn hình bị che khuất
    filterTouchesWhenObscured = true
    
    setOnClickListener {
        // Thực hiện giao dịch an toàn
        processSecureTransaction()
    }
}"""),
            ["Luôn kích hoạt filterTouchesWhenObscured cho các nút bấm xác nhận giao dịch nhạy cảm hoặc cấp quyền.", "Giải phóng binding trong onDestroyView() khi sử dụng Fragment để tránh rò rỉ bộ nhớ View."],
            ["ViewBinding mang lại tính an toàn kiểu dữ liệu Null-Safe cho giao diện Android.", "Tapjacking là mối đe dọa nghiêm trọng khai thác quyền vẽ đè SYSTEM_ALERT_WINDOW.", "Cờ filterTouchesWhenObscured là chốt chặn phòng thủ bắt buộc cho các thao tác tài chính."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Thuộc tính nào của View trong Android được kích hoạt để tự động từ chối sự kiện chạm người dùng khi phát hiện có cửa sổ lớp phủ (Overlay) che khuất màn hình?", "options": ["A. filterTouchesWhenObscured", "B. isClickable", "C. fitsSystemWindows", "D. keepScreenOn"], "correct_index": 0, "explanation": "filterTouchesWhenObscured = true chặn đứng các cuộc tấn công Tapjacking/Clickjacking."},
                {"type": "FILL_BLANK", "question": "Quyền đặc quyền của Android cho phép ứng dụng vẽ các cửa sổ nổi đè lên trên tất cả các ứng dụng khác có tên là android.permission.[_____].", "blanks": [{"accepted_answers": ["SYSTEM_ALERT_WINDOW", "system_alert_window"]}], "explanation": "SYSTEM_ALERT_WINDOW thường bị phần mềm độc hại khai thác để thực hiện tấn công Overlay."},
                {"type": "MATCHING", "question": "Nối đơn vị đo lường giao diện với mục đích sử dụng:", "pairs": [{"left": "dp (density-independent pixel)", "right": "Quy định kích thước và khoảng cách layout thích ứng mật độ màn hình"}, {"left": "sp (scale-independent pixel)", "right": "Quy định kích thước chữ thích ứng với cài đặt trợ năng của người dùng"}, {"left": "px (physical pixel)", "right": "Điểm ảnh vật lý thực tế trên tấm nền màn hình"}] , "explanation": "Sử dụng đúng đơn vị đo giúp giao diện hiển thị chuẩn xác trên mọi kích thước thiết bị."},
                {"type": "FILL_BLANK", "question": "Cờ sự kiện MotionEvent biểu thị rằng cú chạm đã đi xuyên qua một cửa sổ hiển thị mờ đè phía trên là MotionEvent.FLAG_WINDOW_IS_[_____].", "blanks": [{"accepted_answers": ["OBSCURED", "obscured"]}], "explanation": "FLAG_WINDOW_IS_OBSCURED báo hiệu có lớp phủ đang che chắn một phần hoặc toàn bộ nút bấm."}
            ]
        ),
        (
            12,
            "Bài 1.12: Quy Trình Biên Dịch, Ký Số APK (Signature Scheme v1, v2, v3, v4) & Khóa Bảo Mật Keystore",
            "Nghiên cứu chuỗi công cụ biên dịch D8/R8, cơ chế ký số bảo vệ toàn vẹn APK và quy trình xuất bản Google Play an toàn.",
            ["Làm chủ chuỗi công cụ hiện đại: javac/kotlinc -> D8 (dexer) -> R8 (shrinker & obfuscator).", "Phân tích sự tiến hóa của 4 thế hệ sơ đồ chữ ký số APK Signature Scheme (v1, v2, v3, v4).", "Bảo vệ tệp khóa ký số (Release Keystore) và ngăn ngừa lộ lọt mật khẩu kho khóa.", "Nhận diện các lỗ hổng giả mạo chữ ký (Janus Vulnerability) trên các phiên bản cũ."],
            [
                ("Chuỗi Công Cụ Biên Dịch & Làm Rối Mã Nguồn (D8 & R8)", "Quy trình xây dựng một tệp APK phát hành chính thức trải qua các bước kiểm tra nghiêm ngặt: Mã nguồn Kotlin/Java được biên dịch thành bytecode .class, sau đó công cụ D8 thực hiện chuyển đổi thành mã Dalvik bytecode .dex. Đồng thời, trình tối ưu hóa R8 thực hiện 4 tác vụ then chốt: Shrinking (loại bỏ mã và tài nguyên không sử dụng), Optimization (tối ưu hóa luồng lệnh), Obfuscation (làm rối tên lớp, phương thức thành các ký tự vô nghĩa a, b, c), và Pre-verification. Làm rối bằng R8/ProGuard là tuyến phòng thủ cơ bản nhất chống lại việc dịch ngược trực tiếp."),
                ("Sự Tiến Hóa Của Các Sơ Đồ Chữ Ký APK (APK Signature Schemes)", "Chữ ký số là bằng chứng xác thực danh tính nhà phát triển và bảo đảm tính toàn vẹn của ứng dụng: "
                "Scheme v1 (JAR Signature): Ký từng tệp riêng lẻ bên trong kho nén ZIP, thông tin chữ ký nằm trong `META-INF/`. Nhược điểm: Kẻ tấn công có thể chèn thêm các trường dữ liệu tùy biến vào tệp ZIP mà không làm hỏng chữ ký (điển hình là lỗ hổng Janus CVE-2017-13156). "
                "Scheme v2 (APK Signing Block): Ký toàn bộ khối nhị phân của tệp APK trước vùng nén ZIP Central Directory. Bất kỳ sự thay đổi nào đối với bất kỳ byte nào trong APK đều làm chữ ký mất hiệu lực. "
                "Scheme v3: Kế thừa v2 nhưng bổ sung tính năng Kháng kế thừa và Xoay vòng khóa ký (Key Rotation), cho phép nhà phát triển đổi khóa mới mà không làm mất liên kết nâng cấp ứng dụng. "
                "Scheme v4: Hỗ trợ truyền phát trực tuyến (Streaming APK installation qua ADB) bằng cách sử dụng cây băm Merkle Tree nhị phân riêng biệt (`.idsig`)."),
                ("Quản Lý Kho Khóa Ký Phát Hành (Release Keystore Security)", "Tệp kho khóa `.jks` hoặc `.keystore` chứa khóa riêng tư (Private Key) RSA/ECDSA tối mật của nhà phát triển. Nếu kẻ tấn công đánh cắp được tệp Keystore cùng mật khẩu, chúng có thể ký các bản cập nhật độc hại giả mạo và phân phối đè lên ứng dụng thật của hàng triệu người dùng. Tuyệt đối không bao giờ commit tệp Keystore hoặc hardcode mật khẩu trong `build.gradle`; mọi thông số phải được nạp qua biến môi trường bí mật trong hệ thống CI/CD.")
            ],
            "Kịch bản tấn công: Khai thác lỗ hổng Janus (CVE-2017-13156) trên các thiết bị Android 5.0 - 7.0: Vì APK v1 chỉ kiểm tra chữ ký của các tệp nén ZIP, kẻ tấn công ghép một tệp DEX độc hại vào đầu tệp APK (hợp lệ cho ART nhưng bị bỏ qua bởi bộ giải nén ZIP), cho phép thực thi mã độc mà vẫn vượt qua kiểm tra chữ ký! Phòng thủ: Bắt buộc kích hoạt tối thiểu APK Signature Scheme v2 và v3 trong `signingConfigs` của Gradle.",
            "Trong phần thực hành, chúng ta sẽ sử dụng công cụ apksigner của Android SDK để kiểm tra và xác thực chữ ký của tệp APK:",
            ("bash", """# 1. Kiểm tra trạng thái ký số và các phiên bản Scheme của APK
apksigner verify --verbose app-release.apk

# 2. In chi tiết chứng chỉ số, thuật toán băm SHA-256 và Issuer
apksigner verify --print-certs app-release.apk

# 3. Ký thủ công một APK với Keystore và thuật toán RSA-4096
apksigner sign --ks release-key.jks --ks-key-alias my-alias --out signed-app.apk input-app.apk"""),
            ["Không lưu trữ mật khẩu Keystore hoặc đường dẫn tệp khóa trong kho lưu trữ Git.", "Luôn kích hoạt đồng thời v2SigningEnabled true và v3SigningEnabled true trong Gradle."],
            ["R8 tối ưu hóa, loại bỏ mã thừa và làm rối mã nguồn bytecode ứng dụng.", "Signature Scheme v2 và v3 bảo vệ toàn vẹn toàn bộ tệp nhị phân APK, triệt tiêu lỗ hổng Janus.", "apksigner là công cụ chuẩn mực để kiểm tra và bảo đảm tính hợp lệ của chữ ký số."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Sơ đồ chữ ký số APK nào kiểm tra tính toàn vẹn của toàn bộ tệp nhị phân APK bằng cách chèn một APK Signing Block trước Central Directory của file ZIP?", "options": ["A. APK Signature Scheme v2", "B. JAR Signing (Scheme v1)", "C. MD5 Checksum", "D. SHA-1 Manifest"], "correct_index": 0, "explanation": "Signature Scheme v2 ký toàn bộ file nhị phân, phát hiện ngay lập tức mọi sửa đổi so với v1."},
                {"type": "FILL_BLANK", "question": "Công cụ làm rối mã nguồn và thu gọn bytecode mặc định trong chuỗi build của Android Studio hiện đại là [_____].", "blanks": [{"accepted_answers": ["R8", "r8"]}], "explanation": "R8 thay thế ProGuard làm trình biên dịch thu gọn và làm rối bytecode chính thức."},
                {"type": "MATCHING", "question": "Nối sơ đồ chữ ký số APK với đặc tính nổi bật:", "pairs": [{"left": "Scheme v1 (JAR)", "right": "Ký từng tệp riêng rẽ trong META-INF, dễ bị lỗ hổng Janus"}, {"left": "Scheme v2", "right": "Ký toàn bộ khối nhị phân APK thông qua Signing Block"}, {"left": "Scheme v3", "right": "Bổ sung cơ chế xoay vòng khóa ký số (Key Rotation)"}, {"left": "Scheme v4", "right": "Tối ưu hóa cài đặt ứng dụng dạng truyền phát trực tuyến (Streaming)"}] , "explanation": "Sự phát triển của Signature Scheme nâng cao bảo mật toàn vẹn ứng dụng Android."},
                {"type": "FILL_BLANK", "question": "Tiện ích dòng lệnh chính thức nằm trong Android SDK Build-Tools dùng để xác minh và ký số tệp APK là [_____].", "blanks": [{"accepted_answers": ["apksigner", "apksigner.bat"]}], "explanation": "apksigner là công cụ chuẩn hóa thay thế cho jarsigner để ký các scheme v2, v3, v4."}
            ]
        )
    ]

    for spec in ch1_specs + ch1_specs_rest:
        pos, title, summary, objs, theory, attack_def, lab_text, code_snp, pitfalls, summaries, quiz = spec
        vid_idx = (pos - 1) % len(VIDEO_CACHE)
        vurl = VIDEO_CACHE[vid_idx]["url"]

        md_content = generate_lesson_markdown(
            lesson_num=f"1.{pos}",
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
