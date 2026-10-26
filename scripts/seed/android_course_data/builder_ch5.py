# -*- coding: utf-8 -*-
"""Builder for Chapter 5: Mật Mã Học, Lưu Trữ An Toàn & Khai Thác Lỗ Hổng Nâng Cao (12 lessons).
Every lesson strictly exceeds 600 Vietnamese words and includes a 4-question miniquiz.
Based on 'Android Security Internals' by Nikolay Elenkov and OWASP Mobile Security Standard.
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
    VIDEO_CACHE = json.load(f)["ch5"]


def get_chapter_5_lessons() -> list[dict[str, Any]]:
    lessons = []

    ch5_specs = [
        (
            1,
            "Bài 5.1: Kiến Trúc Mật Mã Học Android: Java Cryptography Architecture (JCA), JCE & BoringSSL Provider",
            "Nghiên cứu kiến trúc mật mã học của Android, các nhà cung cấp dịch vụ mật mã Security Providers và thuật toán chuẩn.",
            [
                "Nắm vững kiến trúc Java Cryptography Architecture (JCA) và Java Cryptography Extension (JCE).",
                "Hiểu vai trò của các Security Provider trong Android: AndroidKeyStore, AndroidOpenSSL/Conscrypt, BouncyCastle.",
                "Phân tích nguyên nhân BouncyCastle bị hạn chế và sự thay thế của Conscrypt (BoringSSL).",
                "Khởi tạo và sử dụng các đối tượng Cipher, KeyGenerator, MessageDigest, và Signature chuẩn mực."
            ],
            [
                ("Kiến Trúc Mật Mã Học Phân Tầng JCA/JCE", "Hệ điều hành Android kế thừa kiến trúc mật mã học của Java (JCA/JCE) với thiết kế dạng plugin dựa trên khái niệm 'Nhà cung cấp bảo mật' (Security Provider). "
                "Thay vì gắn chặt ứng dụng vào một thư viện thuật toán cụ thể, JCA cung cấp các lớp giao diện cấp cao trừu tượng (`Cipher`, `KeyStore`, `Mac`, `Signature`, `SecureRandom`). Khi ứng dụng yêu cầu thực hiện một phép tính mã hóa (ví dụ: `Cipher.getInstance(\"AES/GCM/NoPadding\")`), hệ thống sẽ duyệt qua danh sách các Provider đã đăng ký theo thứ tự ưu tiên để chọn ra thư viện phù hợp nhất."),
                ("Sự Chuyển Dịch Từ BouncyCastle Sang Conscrypt (BoringSSL)", "Trước Android 4.4, hệ thống sử dụng phiên bản rút gọn của thư viện Java mã nguồn mở `BouncyCastle`. Tuy nhiên, vì BouncyCastle được viết hoàn toàn bằng Java, hiệu năng mã hóa chậm chạp và không tận dụng được tập lệnh tăng tốc phần cứng của vi xử lý ARM (ARMv8 Cryptographic Extensions). "
                "Từ Android 4.4 và chính thức từ Android 7.0, Google đưa `Conscrypt` trở thành Provider mặc định có độ ưu tiên cao nhất. Conscrypt là lớp vỏ bọc Java (Java Wrapper) cho thư viện mã máy C/C++ `BoringSSL` (nhánh rẽ bảo mật của OpenSSL do Google phát triển). Nhờ đó, tốc độ mã hóa AES và băm SHA-256 tăng vọt từ 5 đến 10 lần và tiết kiệm pin tối đa."),
                ("Các Thực Hành Mã Hóa Bắt Buộc Trong Android", "Khi lập trình mật mã trên Android, lập trình viên phải tuân thủ nghiêm ngặt các nguyên tắc sau: "
                "1. Không bao giờ chỉ định Provider BouncyCastle cho các phép toán đối xứng. "
                "2. Luôn sử dụng nguồn sinh số ngẫu nhiên an toàn `java.security.SecureRandom` (được kết nối trực tiếp với `/dev/urandom` của nhân Linux), tuyệt đối cấm sử dụng `java.util.Random`. "
                "3. Tuyệt đối cấm sử dụng các thuật toán đã lỗi thời và bị bẻ gãy: MD5, SHA-1, DES, 3DES, RC4, và chế độ AES/ECB.")
            ],
            "Kịch bản tấn công: Khai thác lỗ hổng sinh số ngẫu nhiên dự đoán được (Weak Pseudorandom Number Generator - PRNG). Ứng dụng tạo mã OTP hoặc khóa phiên bằng `java.util.Random` với seed dựa trên `System.currentTimeMillis()`. Kẻ tấn công biết khoảng thời gian yêu cầu được gửi, thực hiện vét cạn không gian seed chỉ trong vài giây và tính toán chính xác mã OTP mà không cần nhìn trộm màn hình! Phòng thủ: Bắt buộc sử dụng `SecureRandom` cho mọi mục đích bảo mật.",
            "Trong phần thực hành, chúng ta sẽ liệt kê danh sách toàn bộ các Security Provider đã đăng ký trên thiết bị Android:",
            ("kotlin", """// Liệt kê các Cryptographic Providers trên Android
val providers = Security.getProviders()
for (provider in providers) {
    println("Provider: ${provider.name} (v${provider.version}) - ${provider.info}")
    // In một số dịch vụ hỗ trợ nổi bật
    val services = provider.services.take(5)
    for (service in services) {
        println("  -> ${service.type}: ${service.algorithm}")
    }
}"""),
            ["Không bao giờ truyền seed cố định vào SecureRandom vì sẽ làm mất tính ngẫu nhiên an toàn.", "Luôn chỉ định rõ ràng chế độ hoạt động và đệm (ví dụ AES/GCM/NoPadding thay vì chỉ viết AES)."],
            ["JCA cung cấp khung trừu tượng hóa cho các thuật toán mật mã học trên Android.", "Conscrypt (BoringSSL) là Provider mặc định mang lại hiệu năng tối đa nhờ tăng tốc phần cứng.", "SecureRandom kết nối với /dev/urandom là nguồn sinh số ngẫu nhiên mật mã chuẩn mực."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Lớp sinh số ngẫu nhiên an toàn mật mã nào trong Java/Android bắt buộc phải sử dụng cho việc tạo khóa, muối và vector khởi tạo (IV)?", "options": ["A. java.security.SecureRandom", "B. java.util.Random", "C. Math.random()", "D. System.currentTimeMillis()"], "correct_index": 0, "explanation": "SecureRandom trích xuất entropy từ /dev/urandom của Linux Kernel, chống dự đoán 100%."},
                {"type": "FILL_BLANK", "question": "Nhà cung cấp bảo mật mặc định hiệu năng cao dựa trên BoringSSL của Google trong Android hiện đại có tên là [_____].", "blanks": [{"accepted_answers": ["Conscrypt", "conscrypt"]}], "explanation": "Conscrypt tăng tốc mã hóa bằng cách gọi trực tiếp thư viện C BoringSSL."},
                {"type": "MATCHING", "question": "Nối lớp trừu tượng JCA với chức năng mã hóa:", "pairs": [{"left": "Cipher", "right": "Thực hiện mã hóa và giải mã dữ liệu đối xứng/bất đối xứng"}, {"left": "KeyGenerator", "right": "Sinh các khóa đối xứng bí mật (như AES, DES)"}, {"left": "MessageDigest", "right": "Tính toán giá trị băm một chiều (như SHA-256, SHA-512)"}] , "explanation": "Các lớp JCA chuẩn hóa toàn bộ các tác vụ mật mã học cơ bản."},
                {"type": "FILL_BLANK", "question": "Chế độ mã hóa AES không an toàn nhất tuyệt đối bị cấm sử dụng vì để lộ mẫu hình ảnh và cấu trúc dữ liệu là chế độ [_____] (Electronic Codebook).", "blanks": [{"accepted_answers": ["ECB", "ecb"]}], "explanation": "ECB mode mã hóa từng khối độc lập không có IV, gây lộ cấu trúc dữ liệu rõ."}
            ]
        ),
        (
            2,
            "Bài 5.2: Hệ Thống Kho Khóa Bảo Mật Android Keystore: Hardware-Backed Keys & Keymaster HAL",
            "Nghiên cứu kiến trúc Android Keystore Provider, nguyên lý khóa không thể trích xuất (Non-exportable Keys) và Keymaster HAL.",
            [
                "Nắm vững nguyên lý cốt lõi của Android Keystore Provider: khóa không bao giờ rời khỏi vùng an toàn.",
                "Hiểu cách thức hệ điều hành ủy thác các phép toán mật mã cho Hardware Security Module / TEE.",
                "Lập trình tạo và sử dụng khóa đối xứng AES-GCM trong Android Keystore.",
                "Phân biệt kho khóa ứng dụng AndroidKeyStore với tệp kho khóa phần mềm BouncyCastle (BKS)."
            ],
            [
                ("Tại Sao Cần Android Keystore?", "Trong các hệ thống truyền thống, khi một ứng dụng tạo một khóa mã hóa (ví dụ khóa AES 256-bit), khóa này được lưu trữ trong không gian bộ nhớ của tiến trình. Nếu thiết bị bị Root hoặc tiến trình bị đính kèm Frida, kẻ tấn công có thể đọc trích xuất trực tiếp mảng byte của khóa từ RAM. "
                "Để giải quyết triệt để vấn đề này, Android cung cấp `Android Keystore Provider`. Điểm đặc biệt của Keystore là: khóa bí mật được sinh ra và lưu trữ vĩnh viễn bên trong phần cứng an toàn độc lập (TEE hoặc Secure Element). Ứng dụng chỉ nắm giữ một con trỏ định danh (Alias): khóa KHÔNG BAO GIỜ rời khỏi vùng an toàn và KHÔNG THỂ trích xuất ra ngoài!"),
                ("Cơ Chế Ủy Thác Phép Toán Mật Mã (Keymaster / KeyMint HAL)", "Khi ứng dụng cần mã hóa hoặc ký số, nó không tự tính toán trong tiến trình của mình. Thay vào đó, ứng dụng gửi dữ liệu cần xử lý vào Android Keystore thông qua giao diện Keymaster HAL (hoặc KeyMint trên Android 12+). "
                "Keymaster chuyển gói tin vào phần cứng an toàn; chip bảo mật thực hiện phép tính mã hóa bên trong một môi trường cách ly vật lý hoàn toàn, sau đó chỉ trả về kết quả bản mã (Ciphertext) cho ứng dụng. Ngay cả khi toàn bộ nhân Linux bị chiếm quyền Root, kẻ tấn công vẫn không thể đánh cắp được khóa bí mật!"),
                ("Cấu Hình Thuộc Tính Khóa KeyGenParameterSpec", "Lập trình viên sử dụng `KeyGenParameterSpec.Builder` để quy định chặt chẽ phạm vi sử dụng của khóa: "
                "Mục đích sử dụng: `PURPOSE_ENCRYPT | PURPOSE_DECRYPT`. "
                "Chế độ khối: `BLOCK_MODE_GCM`. "
                "Đệm: `ENCRYPTION_PADDING_NONE`. "
                "Yêu cầu xác thực: `setUserAuthenticationRequired(true)` (chỉ cho phép dùng khóa sau khi người dùng quét vân tay hợp lệ trong vòng 30 giây).")
            ],
            "Kịch bản tấn công: Kẻ tấn công có quyền Root chạy script dump bộ nhớ RAM. Nếu ứng dụng sử dụng Android Keystore, kẻ tấn công lục tung toàn bộ heap nhưng không tìm thấy bất kỳ mảng byte nào của khóa AES! Kẻ tấn công chỉ thấy chuỗi alias `\"my_secret_key_alias\"`. Kẻ tấn công cố tình gọi Keystore để giải mã nhưng bị hệ thống từ chối vì chưa quét vân tay của chủ máy. Phòng thủ: Luôn lưu trữ khóa mã hóa dữ liệu người dùng trong Android Keystore.",
            "Trong phần thực hành, chúng ta sẽ lập trình sinh khóa AES-GCM an toàn trong Android Keystore:",
            ("kotlin", """// Khởi tạo khóa AES-256 trong Android Keystore
val keyGenerator = KeyGenerator.getInstance(
    KeyProperties.KEY_ALGORITHM_AES,
    "AndroidKeyStore"
)

val keyGenParameterSpec = KeyGenParameterSpec.Builder(
    "MY_SECURE_VAULT_KEY",
    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
)
    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
    .setKeySize(256)
    .setUserAuthenticationRequired(false) // Có thể bật yêu cầu vân tay
    .build()

keyGenerator.init(keyGenParameterSpec)
val secretKey = keyGenerator.generateKey()"""),
            ["Luôn sử dụng provider \"AndroidKeyStore\" khi gọi KeyStore.getInstance().", "Thiết lập kích thước khóa chuẩn AES-256 để đảm bảo độ an toàn lâu dài."],
            ["Android Keystore lưu trữ khóa bảo mật trong phần cứng và không thể trích xuất.", "Keymaster / KeyMint HAL điều phối việc tính toán mật mã bên trong vùng an toàn.", "Khóa có thể ràng buộc chặt chẽ với điều kiện xác thực sinh trắc học của người dùng."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tên định danh Provider chuẩn mực trong Android bắt buộc phải truyền vào hàm KeyStore.getInstance() để sử dụng kho khóa bảo mật phần cứng là gì?", "options": ["A. AndroidKeyStore", "B. BouncyCastle", "C. SunJCE", "D. HardwareVault"], "correct_index": 0, "explanation": "AndroidKeyStore là tên định danh hệ thống của kho khóa phần cứng Android."},
                {"type": "FILL_BLANK", "question": "Giao diện tầng trừu tượng phần cứng (HAL) chịu trách nhiệm kết nối giữa Framework và chip bảo mật Keystore trên Android 12+ có tên là Key[_____].", "blanks": [{"accepted_answers": ["Mint", "mint", "KeyMint"]}], "explanation": "KeyMint thay thế cho chuẩn Keymaster cũ từ phiên bản Android 12."},
                {"type": "MATCHING", "question": "Nối thuộc tính KeyGenParameterSpec với ý nghĩa:", "pairs": [{"left": "PURPOSE_ENCRYPT", "right": "Cho phép khóa thực hiện thao tác mã hóa dữ liệu"}, {"left": "BLOCK_MODE_GCM", "right": "Chỉ định chế độ mã hóa khối Galois/Counter Mode xác thực"}, {"left": "setUserAuthenticationRequired", "right": "Ràng buộc việc sử dụng khóa với xác thực sinh trắc học"}] , "explanation": "Khóa trong Keystore được kiểm soát chặt chẽ bằng chính sách sử dụng."},
                {"type": "FILL_BLANK", "question": "Tên chuỗi định danh duy nhất do lập trình viên đặt để tham chiếu tới một khóa cụ thể bên trong Android Keystore được gọi là [_____] (Alias).", "blanks": [{"accepted_answers": ["Alias", "alias", "key alias"]}], "explanation": "Key Alias là tên đại diện cho khóa được lưu trữ trong Keystore."}
            ]
        ),
        (
            3,
            "Bài 5.3: Môi Trường Thực Thi Tin Cậy (TEE), ARM TrustZone & Chip Bảo Mật Độc Lập StrongBox",
            "Nghiên cứu kiến trúc bảo mật vật lý ARM TrustZone, hệ điều hành TEE OS và chip phần cứng chống can thiệp StrongBox.",
            [
                "Hiểu sâu kiến trúc phân chia thế giới vật lý của ARM TrustZone: Normal World (REE) vs. Secure World (TEE).",
                "Phân tích cơ chế chuyển đổi ngữ cảnh an toàn qua lệnh SMC (Secure Monitor Call).",
                "Hiểu sự khác biệt giữa TEE (dùng chung CPU) và Dedicated Secure Element (StrongBox - chip độc lập).",
                "Khai thác thuộc tính `setIsStrongBoxBacked(true)` trên các dòng máy hỗ trợ phần cứng cao cấp."
            ],
            [
                ("Kiến Trúc ARM TrustZone: Hai Thế Giới Song Song", "Trên các bộ vi xử lý kiến trúc ARM hiện đại (Snapdragon, MediaTek, Exynos), công nghệ ARM TrustZone phân chia toàn bộ phần cứng thành hai thế giới vật lý hoàn toàn cách ly: "
                "1. Normal World (Rich Execution Environment - REE): Nơi chạy hệ điều hành Android thông thường (nhân Linux, ứng dụng, driver). REE có bề mặt tấn công rộng lớn và có thể bị Root. "
                "2. Secure World (Trusted Execution Environment - TEE): Chạy một hệ điều hành siêu nhỏ, tối giản và biệt lập (ví dụ Trusty OS của Google hoặc QSEE của Qualcomm). "
                "Ngăn cách giữa hai thế giới là bộ điều khiển Secure Monitor. Hệ điều hành Android trong Normal World hoàn toàn không có quyền đọc, ghi hoặc truy cập vào bộ nhớ RAM của Secure World!"),
                ("Cơ Chế Chuyển Đổi Ngữ Cảnh Qua Lệnh SMC (Secure Monitor Call)", "Khi Android cần thực hiện một phép tính nhạy cảm (như xác thực mẫu vân tay hoặc ký số bằng khóa trong Keystore), CPU sẽ thực thi lệnh hợp ngữ đặc biệt `SMC` (Secure Monitor Call). "
                "Lệnh này lập tức tạm ngưng toàn bộ hệ điều hành Android, chuyển trạng thái phần cứng sang Secure World. Hệ điều hành TEE OS tiếp nhận dữ liệu, thực thi tính toán bảo mật trong vùng nhớ được mã hóa phần cứng, sau đó trả lại kết quả và chuyển quyền điều khiển lại cho Android."),
                ("StrongBox Keymaster: Đỉnh Cao Bảo Mật Phần Cứng", "Từ Android 9.0, Google nâng cấp tiêu chuẩn bảo vệ phần cứng lên một tầm cao mới thông qua `StrongBox`. "
                "Trong khi TEE vẫn chia sẻ chung CPU và bộ nhớ với hệ điều hành chính, StrongBox là một con chip bảo mật chuyên dụng độc lập hoàn toàn (Dedicated Hardware Security Module / Secure Element - như chip Titan M trên Google Pixel hoặc Knox Vault trên Samsung Galaxy). "
                "Chip StrongBox có CPU riêng, RAM riêng, bộ nhớ flash chống can thiệp vật lý (Tamper-Resistant Storage), và bộ sinh số ngẫu nhiên thực TRNG. Nó có khả năng chống lại các cuộc tấn công vật lý tinh vi như tấn công rò rỉ kênh phụ (Side-Channel Attack), tiêm lỗi điện áp (Fault Injection) hoặc soi kính hiển vi điện tử.")
            ],
            "Kịch bản tấn công: Kẻ tấn công trích xuất chip flash của điện thoại và nạp firmware đã bị can thiệp. Khi thiết bị khởi động, kẻ tấn công tìm cách giải mã dữ liệu người dùng. Tuy nhiên, vì khóa mã hóa nằm hoàn toàn bên trong chip bảo mật StrongBox độc lập, và chip này chỉ mở khóa khi nhập đúng mã PIN hợp lệ, kẻ tấn công hoàn toàn bất lực. Phòng thủ: Khi sinh khóa quan trọng, lập trình viên gọi `builder.setIsStrongBoxBacked(true)` để ép buộc lưu trữ trong chip StrongBox nếu phần cứng hỗ trợ.",
            "Trong phần thực hành, chúng ta sẽ kiểm tra xem thiết bị có hỗ trợ chip bảo mật StrongBox hay không thông qua PackageManager:",
            ("kotlin", """// Kiểm tra hỗ trợ phần cứng StrongBox trên thiết bị
val hasStrongBox = context.packageManager.hasSystemFeature(
    PackageManager.FEATURE_STRONGBOX_KEYSTORE
)

println("Thiết bị hỗ trợ chip bảo mật StrongBox: $hasStrongBox")

// Khởi tạo khóa yêu cầu StrongBox
val builder = KeyGenParameterSpec.Builder(
    "STRONGBOX_SIGNING_KEY",
    KeyProperties.PURPOSE_SIGN
)
    .setDigests(KeyProperties.DIGEST_SHA256)
    .setSignaturePaddings(KeyProperties.SIGNATURE_PADDING_RSA_PKCS1)

if (hasStrongBox) {
    builder.setIsStrongBoxBacked(true)
}"""),
            ["Luôn kiểm tra feature FEATURE_STRONGBOX_KEYSTORE trước khi gán setIsStrongBoxBacked(true) để tránh crash trên các thiết bị không có chip riêng.", "Hiểu rằng tốc độ xử lý của StrongBox chậm hơn TEE một chút do băng thông bus giao tiếp độc lập."],
            ["ARM TrustZone phân tách phần cứng thành Normal World (Android) và Secure World (TEE).", "Lệnh SMC chuyển đổi ngữ cảnh an toàn giữa hai thế giới vật lý.", "StrongBox là chip bảo mật chuyên dụng độc lập chống can thiệp vật lý cao cấp nhất."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Lệnh hợp ngữ đặc biệt nào của kiến trúc vi xử lý ARM được sử dụng để chuyển đổi ngữ cảnh từ Normal World sang Secure World (TEE)?", "options": ["A. SMC (Secure Monitor Call)", "B. SVC (Supervisor Call)", "C. NOP (No Operation)", "D. HVC (Hypervisor Call)"], "correct_index": 0, "explanation": "SMC (Secure Monitor Call) kích hoạt chuyển đổi ngữ cảnh an toàn trong ARM TrustZone."},
                {"type": "FILL_BLANK", "question": "Hệ điều hành siêu nhỏ, bảo mật cao mã nguồn mở do Google phát triển chạy bên trong môi trường TEE có tên là [_____] OS.", "blanks": [{"accepted_answers": ["Trusty", "trusty", "Trusty OS"]}], "explanation": "Trusty OS là hệ điều hành TEE chuẩn mực cho các thiết bị Android."},
                {"type": "MATCHING", "question": "Nối công nghệ bảo mật phần cứng với đặc điểm kiến trúc:", "pairs": [{"left": "ARM TrustZone", "right": "Phân chia không gian CPU thành Normal World và Secure World"}, {"left": "TEE (Trusted Execution Env)", "right": "Môi trường thực thi bảo mật chia sẻ chung vi xử lý chính"}, {"left": "StrongBox (Secure Element)", "right": "Chip bảo mật độc lập hoàn toàn có CPU và RAM riêng biệt"}] , "explanation": "Các cấp độ bảo vệ phần cứng từ thấp đến cao bảo đảm an ninh đa tầng."},
                {"type": "FILL_BLANK", "question": "Thuộc tính phương thức của KeyGenParameterSpec.Builder dùng để yêu cầu lưu trữ khóa trong chip bảo mật độc lập là setIs[_____]Backed(true).", "blanks": [{"accepted_answers": ["StrongBox", "strongbox", "Strongbox"]}], "explanation": "setIsStrongBoxBacked(true) chỉ định sử dụng chip Secure Element độc lập."}
            ]
        ),
        (
            4,
            "Bài 5.4: Xác Thực Sinh Trắc Học An Toàn (BiometricPrompt) & Ràng Buộc Khóa CryptoObject",
            "Nghiên cứu khung xác thực sinh trắc học hiện đại BiometricPrompt, CryptoObject và chống bypass bằng Frida.",
            [
                "Hiểu sự tiến hóa từ FingerprintManager cũ kỹ sang chuẩn mực bảo mật mới BiometricPrompt.",
                "Làm chủ 3 cấp độ xác thực sinh trắc học: BIOMETRIC_STRONG (Class 3), BIOMETRIC_WEAK, và DEVICE_CREDENTIAL.",
                "Kỹ thuật ràng buộc bắt buộc (Cryptographic Binding) giữa sinh trắc học và Cipher qua đối tượng `BiometricPrompt.CryptoObject`.",
                "Phân tích lỗ hổng Biometric Bypass khi chỉ kiểm tra kết quả callback boolean thuần túy."
            ],
            [
                ("Sự Tiến Hóa Lên BiometricPrompt Của AndroidX", "Trước Android 9.0, mỗi nhà sản xuất tự thiết kế giao diện quét vân tay riêng hoặc sử dụng `FingerprintManager` rời rạc. Điều này dẫn đến sự phân mảnh và các lỗ hổng giao diện (Overlay attacks). "
                "Google chuẩn hóa toàn bộ hệ sinh thái bằng thư viện `androidx.biometric.BiometricPrompt`. BiometricPrompt cung cấp một hộp thoại hệ thống thống nhất, an toàn, hỗ trợ cả vân tay, nhận diện khuôn mặt 3D và quét mống mắt. "
                "Hệ thống phân loại phần cứng sinh trắc học thành 3 cấp độ: 1. `BIOMETRIC_STRONG` (Class 3): Tỷ lệ chấp nhận sai (FAR) < 1/50.000 và tỷ lệ giả mạo (SAR) < 7%, đủ điều kiện thực hiện giao dịch tài chính. 2. `BIOMETRIC_WEAK` (Class 2): Nhận diện khuôn mặt 2D. 3. `DEVICE_CREDENTIAL`: Mở khóa bằng mã PIN, mật khẩu hoặc hình vẽ của máy."),
                ("Hiểm Họa Khi Chỉ Kiểm Tra Callback onAuthenticationSucceeded()", "Rất nhiều ứng dụng ngân hàng mắc phải một sai lầm bảo mật nghiêm trọng: "
                "Lập trình viên hiển thị `BiometricPrompt`, và khi người dùng quét vân tay thành công, hệ thống gọi callback `onAuthenticationSucceeded(result)`. Bên trong callback, lập trình viên đơn giản viết: "
                "`isUserLoggedIn = true; openHomeScreen();`. "
                "Hậu quả: Kẻ tấn công chỉ cần viết một dòng script Frida hook phương thức `onAuthenticationSucceeded()` và tự động kích hoạt callback này mà KHÔNG CẦN bất kỳ dấu vân tay nào! Toàn bộ cơ chế xác thực sinh trắc học bị bẻ khóa hoàn toàn trong 1 giây!"),
                ("Ràng Buộc Khóa Mật Mã Bắt Buộc Với CryptoObject", "Để chống lại 100% các cuộc tấn công hook callback, ứng dụng BẮT BUỘC phải sử dụng cơ chế Ràng buộc mật mã (Cryptographic Binding) với `CryptoObject`: "
                "1. Khởi tạo một đối tượng `Cipher` sử dụng khóa được lưu trong Android Keystore với thuộc tính `setUserAuthenticationRequired(true)`. Lúc này, khóa đang ở trạng thái bị khóa cứng trong phần cứng TEE. "
                "2. Đóng gói Cipher vào đối tượng `BiometricPrompt.CryptoObject(cipher)`. "
                "3. Truyền CryptoObject vào hàm `biometricPrompt.authenticate(promptInfo, cryptoObject)`. "
                "Khi người dùng quét vân tay hợp lệ, chip TEE sẽ mở khóa Cipher. Trong `onAuthenticationSucceeded`, ứng dụng lấy `result.cryptoObject.cipher` để giải mã token phiên lưu trong máy. Nếu kẻ tấn công dùng Frida để giả mạo callback, `cryptoObject` sẽ là null hoặc Cipher vẫn bị khóa, dẫn đến việc giải mã token thất bại! Kẻ tấn công hoàn toàn không thể đăng nhập được!")
            ],
            "Kịch bản tấn công: Kẻ tấn công sử dụng script Frida phổ biến `fingerprint-bypass.js` để hook `BiometricPrompt.AuthenticationCallback.onAuthenticationSucceeded`. Đối với các ứng dụng không sử dụng CryptoObject, màn hình chuyển tiền lập tức mở ra. Nhưng đối với ứng dụng có CryptoObject, ứng dụng bị crash ngay lập tức với lỗi `IllegalBlockSizeException: Key not authenticated`. Phòng thủ: Tuyệt đối không bao giờ tin tưởng callback sinh trắc học nếu không gắn kết với CryptoObject.",
            "Trong phần thực hành, chúng ta sẽ lập trình luồng xác thực sinh trắc học an toàn tuyệt đối với CryptoObject:",
            ("kotlin", """// Khởi tạo BiometricPrompt an toàn với CryptoObject
val promptInfo = BiometricPrompt.PromptInfo.Builder()
    .setTitle("Xác thực sinh trắc học an toàn")
    .setSubtitle("Quét vân tay để ký số giao dịch chuyển tiền")
    .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
    .setNegativeButtonText("Hủy bỏ")
    .build()

val biometricPrompt = BiometricPrompt(this, executor, 
    object : BiometricPrompt.AuthenticationCallback() {
        override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
            super.onAuthenticationSucceeded(result)
            // Lấy Cipher đã được TEE mở khóa hợp lệ
            val authenticatedCipher = result.cryptoObject?.cipher
            if (authenticatedCipher != null) {
                // Giải mã dữ liệu phiên an toàn
                val decryptedToken = authenticatedCipher.doFinal(encryptedSecret)
                proceedTransaction(decryptedToken)
            }
        }
    }
)

// Kích hoạt xác thực kèm đối tượng CryptoObject
biometricPrompt.authenticate(promptInfo, BiometricPrompt.CryptoObject(secureCipher))"""),
            ["Tuyệt đối không sử dụng BiometricPrompt mà không truyền CryptoObject trong các ứng dụng tài chính.", "Đảm bảo cờ setUserAuthenticationRequired(true) được kích hoạt khi sinh khóa trong Keystore."],
            ["BiometricPrompt là chuẩn xác thực sinh trắc học thống nhất và an toàn của Android.", "Chỉ có cấp độ BIOMETRIC_STRONG mới đủ điều kiện bảo mật cho các giao dịch tài chính.", "Ràng buộc mật mã bằng CryptoObject là phương thức duy nhất chống lại tấn công Hooking Bypass."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Đối tượng nào bắt buộc phải được truyền vào phương thức BiometricPrompt.authenticate() để đảm bảo việc giải mã dữ liệu gắn kết với phần cứng và chống lại việc giả mạo callback bằng Frida?", "options": ["A. BiometricPrompt.CryptoObject", "B. Bundle", "C. Intent", "D. SignatureCallback"], "correct_index": 0, "explanation": "CryptoObject ràng buộc trực tiếp Cipher với phần cứng sinh trắc học TEE."},
                {"type": "FILL_BLANK", "question": "Cấp độ sinh trắc học mạnh nhất (Class 3) đáp ứng đầy đủ tiêu chuẩn bảo mật cho các giao dịch ngân hàng có tên hằng số là BIOMETRIC_[_____].", "blanks": [{"accepted_answers": ["STRONG", "strong"]}], "explanation": "BIOMETRIC_STRONG yêu cầu cảm biến vân tay hoặc khuôn mặt 3D có tỷ lệ SAR < 7%."},
                {"type": "MATCHING", "question": "Nối cấp độ sinh trắc học với công nghệ phần cứng:", "pairs": [{"left": "BIOMETRIC_STRONG", "right": "Cảm biến vân tay điện dung/siêu âm hoặc quét khuôn mặt 3D ToF"}, {"left": "BIOMETRIC_WEAK", "right": "Nhận diện khuôn mặt 2D bằng camera trước thông thường"}, {"left": "DEVICE_CREDENTIAL", "right": "Mã PIN, mật khẩu hoặc mẫu hình vẽ bảo vệ màn hình khóa"}] , "explanation": "Phân cấp bảo mật giúp nhà phát triển lựa chọn phương thức xác thực phù hợp."},
                {"type": "FILL_BLANK", "question": "Phương thức callback được gọi khi người dùng quét vân tay thành công trên BiometricPrompt là onAuthentication[_____]().", "blanks": [{"accepted_answers": ["Succeeded", "succeeded", "Succeeded()"]}], "explanation": "onAuthenticationSucceeded nhận về kết quả xác thực kèm đối tượng CryptoObject."}
            ]
        ),
        (
            5,
            "Bài 5.5: Triển Khai Mã Hóa Bất Đối Xứng RSA / ECDSA & Ký Số Điện Tử Xác Thực Giao Dịch",
            "Nghiên cứu mật mã học bất đối xứng, đường cong Elliptic Curve (ECDSA), chữ ký điện tử chống chối bỏ trong ứng dụng tài chính.",
            [
                "Nắm vững nguyên lý mật mã khóa công khai (Public-Key Cryptography): Khóa công khai (Public Key) và Khóa riêng (Private Key).",
                "So sánh thuật toán RSA kinh điển và đường cong Elliptic Curve (ECDSA) về hiệu năng và kích thước khóa.",
                "Lập trình quy trình Ký số điện tử (Digital Signature) tạo bằng chứng chống chối bỏ (Non-repudiation).",
                "Bảo vệ khóa riêng tư Private Key bên trong chip bảo mật Android Keystore."
            ],
            [
                ("Mật Mã Học Khóa Công Khai (Asymmetric Cryptography)", "Mật mã bất đối xứng sử dụng một cặp khóa có quan hệ toán học mật thiết: Khóa công khai (Public Key) có thể chia sẻ rộng rãi cho bất kỳ ai, dùng để mã hóa dữ liệu hoặc kiểm tra chữ ký số; Khóa riêng tư (Private Key) được giữ bí mật tuyệt đối bên trong chip bảo mật của thiết bị, dùng để giải mã hoặc tạo chữ ký số. "
                "Hai ứng dụng cốt lõi của mật mã bất đối xứng trên Android: 1. Mã hóa tin nhắn bí mật; 2. Tạo chữ ký số điện tử (Digital Signature) xác nhận giao dịch chuyển tiền."),
                ("So Sánh Thuật Toán RSA Và Elliptic Curve (ECDSA)", "1. Thuật toán RSA: Dựa trên độ khó toán học của việc phân tích một số nguyên khổng lồ thành thừa số nguyên tố. Để đạt mức độ an toàn tiêu chuẩn hiện nay, RSA đòi hỏi kích thước khóa tối thiểu là 2048-bit hoặc 4096-bit. Nhược điểm: Kích thước khóa lớn, tốc độ tính toán chậm và tiêu tốn nhiều pin di động. "
                "2. Thuật toán ECDSA (Elliptic Curve Digital Signature Algorithm): Dựa trên bài toán logarit rời rạc trên đường cong Elliptic (chuẩn NIST P-256 / secp256r1). Một khóa ECDSA 256-bit cung cấp mức độ an toàn tương đương với một khóa RSA 3072-bit, nhưng kích thước chữ ký nhỏ hơn nhiều và tốc độ tạo chữ ký nhanh gấp 10 lần! Vì vậy, ECDSA là lựa chọn hàng đầu cho các ứng dụng ngân hàng di động thế hệ mới."),
                ("Quy Trình Tạo Chữ Ký Điện Tử Chống Chối Bỏ", "Để xác nhận giao dịch chuyển tiền 100 triệu đồng: "
                "Bước 1: Ứng dụng gom toàn bộ thông tin giao dịch (`Tài khoản gửi + Tài khoản nhận + Số tiền + Dấu thời gian + Nonce`) thành một chuỗi văn bản JSON. "
                "Bước 2: Hệ thống tính toán mã băm SHA-256 của chuỗi văn bản. "
                "Bước 3: Sử dụng Private Key trong Keystore (sau khi đã quét vân tay) để ký lên giá trị băm, tạo ra chuỗi chữ ký số Base64. "
                "Bước 4: Gửi giao dịch kèm chữ ký lên Backend. Máy chủ sử dụng Public Key của người dùng để xác minh: nếu chữ ký hợp lệ, giao dịch được phê duyệt và người dùng không thể chối bỏ hành vi của mình (Non-repudiation).")
            ],
            "Kịch bản tấn công: Tấn công phát lại giao dịch (Replay Attack). Kẻ tấn công bắt gói tin chữ ký hợp lệ của giao dịch chuyển tiền 1 triệu đồng, sau đó gửi lại gói tin đó 100 lần lên máy chủ để rút cạn tiền của nạn nhân! Phòng thủ: Bắt buộc chèn một giá trị ngẫu nhiên dùng một lần (Cryptographic Nonce) do máy chủ sinh ra và thời gian hết hạn (Timestamp) vào nội dung chuỗi ký để đảm bảo chữ ký chỉ có hiệu lực duy nhất một lần.",
            "Trong phần thực hành, chúng ta sẽ lập trình tạo cặp khóa ECDSA trong Keystore và thực hiện ký số chuỗi dữ liệu giao dịch:",
            ("kotlin", """// Khởi tạo cặp khóa ECDSA secp256r1 trong Keystore
val kpg = KeyPairGenerator.getInstance(
    KeyProperties.KEY_ALGORITHM_EC,
    "AndroidKeyStore"
)

kpg.initialize(
    KeyGenParameterSpec.Builder("TRANSACTION_SIGNING_KEY", KeyProperties.PURPOSE_SIGN)
        .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
        .setDigests(KeyProperties.DIGEST_SHA256)
        .setUserAuthenticationRequired(true)
        .build()
)

val keyPair = kpg.generateKeyPair()

// Tạo chữ ký số với SHA256withECDSA
val signature = Signature.getInstance("SHA256withECDSA").apply {
    initSign(keyPair.private)
    update(transactionPayload.toByteArray(Charsets.UTF_8))
}
val signatureBytes = signature.sign()"""),
            ["Luôn chèn Server Nonce vào dữ liệu ký để ngăn chặn 100% tấn công Replay Attack.", "Ưu tiên sử dụng thuật toán EC secp256r1 thay cho RSA để tiết kiệm pin và tối ưu hiệu năng."],
            ["Mật mã bất đối xứng bảo đảm tính xác thực và chống chối bỏ cho các giao dịch trực tuyến.", "ECDSA 256-bit mang lại hiệu năng vượt trội và kích thước khóa gọn nhẹ so với RSA.", "Khóa Private Key được bảo vệ vĩnh viễn trong phần cứng Keystore của thiết bị."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Đường cong Elliptic tiêu chuẩn nào được khuyến nghị sử dụng rộng rãi nhất trong Android Keystore để tạo chữ ký số ECDSA an toàn tương đương RSA 3072-bit?", "options": ["A. secp256r1 (NIST P-256)", "B. Curve25519", "C. secp256k1", "D. BrainpoolP256r1"], "correct_index": 0, "explanation": "secp256r1 (NIST P-256) là chuẩn đường cong elliptic chính thống trong Android Keystore."},
                {"type": "FILL_BLANK", "question": "Tính chất an toàn thông tin bảo đảm rằng bên gửi không thể phủ nhận việc mình đã tạo ra và gửi thông điệp giao dịch được gọi là tính chống [_____] (Non-repudiation).", "blanks": [{"accepted_answers": ["chối bỏ", "chối", "Non-repudiation"]}], "explanation": "Non-repudiation (chống chối bỏ) được thực hiện thông qua chữ ký số sử dụng Private Key."},
                {"type": "MATCHING", "question": "Nối thuật toán chữ ký số với đặc tính kỹ thuật:", "pairs": [{"left": "RSA 2048-bit", "right": "Dựa trên phân tích thừa số nguyên tố, kích thước khóa lớn"}, {"left": "ECDSA 256-bit", "right": "Dựa trên logarit đường cong elliptic, tốc độ nhanh, tiết kiệm pin"}, {"left": "Server Nonce", "right": "Giá trị ngẫu nhiên dùng 1 lần chống tấn công phát lại Replay"}] , "explanation": "Hiểu rõ thuật toán giúp kiến trúc sư hệ thống lựa chọn giải pháp tối ưu."},
                {"type": "FILL_BLANK", "question": "Lớp Java trong gói java.security được sử dụng để tạo và xác thực chữ ký điện tử số là java.security.[_____].", "blanks": [{"accepted_answers": ["Signature", "signature"]}], "explanation": "Lớp Signature quản lý quá trình băm và ký số dữ liệu."},
            ]
        ),
        (
            6,
            "Bài 5.6: Mã Hóa Khối Đối Xứng Chuẩn: AES-256-GCM, Quản Lý Vector Khởi Tạo (IV / Nonce) & Chống Tái Sử Dụng",
            "Nghiên cứu thuật toán mã hóa khối đối xứng AES, chế độ Galois/Counter Mode (GCM) và thảm họa khi tái sử dụng IV.",
            [
                "Nắm vững cấu trúc và nguyên lý mã hóa của Tiêu chuẩn Mã hóa Nâng cao (AES) với độ dài khóa 128/256-bit.",
                "Hiểu cơ chế Mã hóa đi kèm Xác thực (Authenticated Encryption with Associated Data - AEAD) trong chế độ GCM.",
                "Phân tích thảm họa rò rỉ khóa bí mật khi tái sử dụng Vector khởi tạo (IV Reuse Catastrophe).",
                "Lập trình quy trình mã hóa và giải mã an toàn tuyệt đối với mảng byte `[12-byte IV + Ciphertext + 16-byte Auth Tag]`."
            ],
            [
                ("Tiêu Chuẩn Mã Hóa Nâng Cao (AES) & Chế Độ GCM", "Advanced Encryption Standard (AES) là thuật toán mã hóa khối đối xứng tiêu chuẩn toàn cầu được Viện Tiêu chuẩn và Công nghệ Quốc gia Hoa Kỳ (NIST) phê chuẩn. AES xử lý các khối dữ liệu cố định 128-bit (16 byte) với các độ dài khóa 128, 192 hoặc 256-bit. "
                "Trong các chế độ mã hóa cũ (như CBC), mã hóa chỉ đảm bảo tính bí mật (Confidentiality) mà không đảm bảo tính toàn vẹn (Integrity), dẫn đến các cuộc tấn công thay đổi nội dung bản mã hoặc tấn công giải mã đệm (Padding Oracle Attack). "
                "Để khắc phục, chuẩn mực hiện đại quy định sử dụng chế độ Galois/Counter Mode (GCM) - một dạng Mã hóa đi kèm Xác thực (AEAD). GCM vừa mã hóa dữ liệu tốc độ cao theo chế độ đếm (Counter), vừa tự động sinh ra một Mã xác thực thông điệp 128-bit (Authentication Tag). Nếu bất kỳ byte nào trong bản mã bị kẻ tấn công sửa đổi, quá trình giải mã sẽ lập tức thất bại!"),
                ("Thảm Họa Tái Sử Dụng Vector Khởi Tạo (Nonce / IV Reuse)", "Chế độ AES-GCM yêu cầu một Vector khởi tạo (Initialization Vector - IV / Nonce) có kích thước chuẩn là 96-bit (12 byte). "
                "Quy tắc vàng bất biến của mật mã học: Với cùng một khóa bí mật, IV TUYỆT ĐỐI KHÔNG BAO GIỜ ĐƯỢC TÁI SỬ DỤNG hai lần! "
                "Nếu lập trình viên mắc sai lầm sử dụng một IV cố định (Hardcoded IV) hoặc sinh IV theo quy luật tuần tự, kẻ tấn công có thể thực hiện phép toán XOR giữa hai bản mã để triệt tiêu hoàn toàn lớp mã hóa, trích xuất dữ liệu bản rõ và thậm chí tính toán ngược lại khóa xác thực của máy chủ (Authentication Key Recovery Attack)!"),
                ("Định Dạng Đóng Gói Bản Mã Chuẩn An Toàn", "Vì IV không phải là thông tin bí mật (chỉ yêu cầu là duy nhất), cách thức chuẩn mực để lưu trữ tệp mã hóa là đóng gói IV đi kèm ngay đầu tệp: "
                "`Mảng dữ liệu xuất ra = [12-byte IV ngẫu nhiên] + [Dữ liệu mã hóa + 16-byte GCM Tag]`. "
                "Khi giải mã, ứng dụng chỉ cần đọc 12 byte đầu tiên để làm IV nạp vào Cipher, phần còn lại đưa vào hàm `doFinal()` để giải mã.")
            ],
            "Kịch bản tấn công: Kẻ tấn công phát hiện ứng dụng nhắn tin bí mật sử dụng AES-GCM nhưng lại cố định IV là `123456789012`. Kẻ tấn công bắt hai gói tin mã hóa của hai người dùng gửi đi. Bằng cách thực hiện phép XOR giữa hai bản mã, kẻ tấn công đọc được toàn bộ nội dung cuộc trò chuyện mà không cần biết khóa giải mã! Phòng thủ: Luôn sinh IV ngẫu nhiên 12-byte mới cho MỖI LẦN mã hóa bằng `SecureRandom` hoặc để Android Keystore tự động sinh IV.",
            "Trong phần thực hành, chúng ta sẽ lập trình hàm mã hóa và giải mã AES-256-GCM chuẩn mực không tái sử dụng IV:",
            ("kotlin", """// Mã hóa an toàn với AES-256-GCM
fun encryptAesGcm(plaintext: ByteArray, secretKey: SecretKey): ByteArray {
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    cipher.init(Cipher.ENCRYPT_MODE, secretKey)
    val iv = cipher.iv // Tự động sinh 12-byte IV ngẫu nhiên an toàn
    val ciphertextWithTag = cipher.doFinal(plaintext)
    
    // Đóng gói: 12-byte IV + Ciphertext
    return ByteBuffer.allocate(iv.size + ciphertextWithTag.size)
        .put(iv)
        .put(ciphertextWithTag)
        .array()
}"""),
            ["Tuyệt đối không bao giờ sử dụng IV cố định hoặc tái sử dụng IV với cùng một khóa AES-GCM.", "Kích thước chuẩn tối ưu nhất cho IV trong AES-GCM luôn luôn là 12 byte (96-bit)."],
            ["AES-256-GCM cung cấp khả năng mã hóa đi kèm xác thực toàn vẹn dữ liệu (AEAD).", "Authentication Tag 128-bit phát hiện ngay lập tức mọi hành vi sửa đổi bản mã.", "Bảo đảm tính ngẫu nhiên và duy nhất của IV là nguyên tắc sống còn của AES-GCM."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Kích thước độ dài tối ưu theo chuẩn khuyến nghị của NIST dành cho Vector khởi tạo (IV / Nonce) trong chế độ mã hóa khối AES-GCM là bao nhiêu byte?", "options": ["A. 12 byte (96-bit)", "B. 16 byte (128-bit)", "C. 8 byte (64-bit)", "D. 32 byte (256-bit)"], "correct_index": 0, "explanation": "12 byte (96-bit) là kích thước chuẩn mực giúp GCM tối ưu tốc độ và không cần băm IV."},
                {"type": "FILL_BLANK", "question": "Khái niệm mật mã học chỉ cơ chế vừa mã hóa bảo mật vừa tạo chữ ký xác thực tính toàn vẹn dữ liệu được viết tắt là [_____] (Authenticated Encryption with Associated Data).", "blanks": [{"accepted_answers": ["AEAD", "aead"]}], "explanation": "AEAD là chuẩn mã hóa hiện đại thay thế cho các chế độ mã hóa khối cũ."},
                {"type": "MATCHING", "question": "Nối thành phần gói dữ liệu AES-GCM với kích thước tiêu chuẩn:", "pairs": [{"left": "Vector khởi tạo (IV)", "right": "12 byte ngẫu nhiên duy nhất cho mỗi gói tin"}, {"left": "Authentication Tag", "right": "16 byte (128-bit) đảm bảo tính toàn vẹn dữ liệu"}, {"left": "Độ dài khóa AES mạnh nhất", "right": "32 byte (256-bit) chống lại siêu máy tính"}] , "explanation": "Cấu trúc gói tin nhị phân chuẩn hóa giúp việc giải mã dễ dàng và tin cậy."},
                {"type": "FILL_BLANK", "question": "Hậu quả thảm họa khi tái sử dụng cùng một cặp (Key, IV) trong mã hóa AES-GCM là làm mất tính bí mật và cho phép kẻ tấn công thực hiện phép toán [_____] để khôi phục dữ liệu.", "blanks": [{"accepted_answers": ["XOR", "xor", "Xor"]}], "explanation": "Phép toán XOR giữa hai bản mã có cùng Counter làm triệt tiêu dòng khóa (keystream)."}
            ]
        ),
        (
            7,
            "Bài 5.7: Cơ Chế Dẫn Xuất Khóa Mật Khẩu An Toàn: PBKDF2, Argon2 & Scrypt Chống Vét Cạn",
            "Nghiên cứu các thuật toán dẫn xuất khóa từ mật khẩu (KDF), phòng chống tấn công dò mật khẩu bằng phần cứng GPU/ASIC.",
            [
                "Hiểu lý do tại sao các hàm băm thông thường (MD5, SHA-256) tuyệt đối không được dùng để băm mật khẩu.",
                "Làm chủ cơ chế kéo dài khóa (Key Stretching) và muối ngẫu nhiên (Salt) trong thuật toán PBKDF2.",
                "Phân tích sức mạnh chống tấn công phần cứng GPU của thuật toán khó về bộ nhớ (Memory-Hard) Argon2 và Scrypt.",
                "Lập trình dẫn xuất khóa mã hóa AES từ chuỗi mật khẩu người dùng nhập vào."
            ],
            [
                ("Tại Sao Các Hàm Băm SHA-256 Không Đủ An Toàn Để Lưu Mật Khẩu?", "Nhiều lập trình viên nghĩ rằng việc lưu trữ mật khẩu dưới dạng `SHA-256(password)` hoặc `SHA-256(password + salt)` là đủ an toàn. Đây là một quan niệm sai lầm chết người! "
                "Các thuật toán băm họ SHA (SHA-1, SHA-256, SHA-512) được thiết kế có chủ đích để tính toán CỰC KỲ NHANH nhằm phục vụ việc kiểm tra tính toàn vẹn của các tệp tin hàng gigabyte. Với các dàn máy đào tiền ảo hoặc máy tính gắn nhiều card đồ họa GPU cao cấp (như RTX 4090), kẻ tấn công có thể thử hàng chục tỷ giá trị băm mỗi giây! Một mật khẩu 8 ký tự thông thường sẽ bị bẻ khóa chỉ trong vài phút thông qua các bảng băm tính sẵn (Rainbow Tables) hoặc tấn công vét cạn (Brute-force)."),
                ("Cơ Chế Kéo Dài Khóa Của PBKDF2 (Password-Based Key Derivation Function 2)", "Để biến mật khẩu yếu của con người thành một khóa mã hóa mạnh mẽ, mật mã học sử dụng các hàm dẫn xuất khóa (KDF). Chuẩn mực tiêu chuẩn là `PBKDF2`: "
                "1. Muối ngẫu nhiên (Cryptographic Salt): Bắt buộc sinh một mảng byte ngẫu nhiên tối thiểu 16 byte cho mỗi người dùng để triệt tiêu hoàn toàn bảng Rainbow Table. "
                "2. Số vòng lặp kéo dài thời gian (Iteration Count): Thay vì băm 1 lần, PBKDF2 lặp lại thuật toán băm (HMAC-SHA256) hàng trăm ngàn lần (khuyến nghị tối thiểu từ 100.000 đến 600.000 vòng lặp). Việc này khiến mỗi phép kiểm tra mật khẩu mất khoảng 100 miligiây trên CPU điện thoại (người dùng không nhận thấy độ trễ), nhưng làm kẻ tấn công mất hàng trăm năm nếu muốn vét cạn hàng tỷ mật khẩu!"),
                ("Các Thuật Toán Khó Về Bộ Nhớ Thế Hệ Mới: Argon2 & Scrypt", "Điểm yếu của PBKDF2 là nó chỉ tiêu tốn CPU mà tiêu thụ rất ít bộ nhớ RAM, cho phép kẻ tấn công chế tạo các chip phần cứng chuyên dụng (ASIC/FPGA) để bẻ khóa song song hàng triệu luồng. "
                "Để giải quyết, các thuật toán KDF thế hệ mới như `Argon2` (người chiến thắng cuộc thi Password Hashing Competition) và `Scrypt` được thiết kế theo nguyên lý Khó về bộ nhớ (Memory-Hard): mỗi phép tính băm bắt buộc phải chiếm dụng hàng chục megabyte bộ nhớ RAM. Kẻ tấn công không thể chế tạo chip ASIC giá rẻ có đủ dung lượng RAM khổng lồ, triệt tiêu hoàn toàn ưu thế tấn công bằng phần cứng tùy biến.")
            ],
            "Kịch bản tấn công: Cơ sở dữ liệu ứng dụng bị rò rỉ. Kẻ tấn công sử dụng công cụ `Hashcat` trên dàn máy tính 8 GPU để bẻ khóa danh sách mật khẩu băm bằng SHA-256. Trong 1 giờ, 80% mật khẩu người dùng bị giải mã. Nhưng đối với các tài khoản được băm bằng PBKDF2 với 310.000 vòng lặp, Hashcat chỉ có thể thử vài ngàn mật khẩu mỗi ngày, bảo vệ an toàn cho người dùng. Phòng thủ: Luôn sử dụng PBKDF2WithHmacSHA256 với số vòng lặp tối thiểu 120.000 vòng kết hợp muối 128-bit.",
            "Trong phần thực hành, chúng ta sẽ lập trình dẫn xuất một khóa bí mật SecretKeySpec từ mật khẩu người dùng bằng PBKDF2:",
            ("kotlin", """// Dẫn xuất khóa AES-256 an toàn từ mật khẩu người dùng
fun deriveKeyFromPassword(password: CharArray, salt: ByteArray): SecretKey {
    val iterationCount = 120_000 // Tối thiểu 120.000 vòng lặp
    val keyLengthBits = 256
    
    val spec = PBEKeySpec(password, salt, iterationCount, keyLengthBits)
    val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
    val keyBytes = factory.generateSecret(spec).encoded
    
    // Trả về khóa chuẩn AES
    return SecretKeySpec(keyBytes, "AES")
}"""),
            ["Tuyệt đối luôn sinh Salt ngẫu nhiên bằng SecureRandom cho mỗi người dùng, không bao giờ dùng chung Salt.", "Bắt buộc sử dụng số vòng lặp iteration count tối thiểu 100.000 vòng."],
            ["Các hàm băm thông thường (SHA-256) không an toàn cho mật khẩu vì tính toán quá nhanh.", "PBKDF2 kéo dài thời gian tính toán bằng cơ chế lặp hàng trăm ngàn vòng kết hợp muối.", "Argon2 và Scrypt là các thuật toán Memory-Hard chống lại tấn công vét cạn bằng GPU/ASIC."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Số lượng vòng lặp (Iteration count) tối thiểu được tổ chức OWASP khuyến nghị sử dụng khi cấu hình hàm dẫn xuất khóa PBKDF2WithHmacSHA256 hiện nay là bao nhiêu?", "options": ["A. Tối thiểu 120.000 vòng", "B. 1.000 vòng", "C. 10 vòng", "D. 500 vòng"], "correct_index": 0, "explanation": "OWASP khuyến nghị tối thiểu 120.000 vòng lặp cho PBKDF2-HMAC-SHA256 để chống brute-force."},
                {"type": "FILL_BLANK", "question": "Mảng byte ngẫu nhiên duy nhất được tạo ra cho mỗi người dùng để ghép vào mật khẩu trước khi băm nhằm triệt tiêu bảng Rainbow Table được gọi là [_____] (Salt).", "blanks": [{"accepted_answers": ["Muối", "muối", "Salt", "salt"]}], "explanation": "Cryptographic Salt đảm bảo hai người dùng có cùng mật khẩu sẽ sinh ra hai mã băm hoàn toàn khác nhau."},
                {"type": "MATCHING", "question": "Nối thuật toán dẫn xuất khóa với đặc tính phòng thủ:", "pairs": [{"left": "PBKDF2", "right": "Chuẩn mực NIST, tiêu tốn CPU bằng cách lặp hàm HMAC nhiều lần"}, {"left": "Argon2", "right": "Người chiến thắng cuộc thi PHC, tiêu tốn cả CPU và bộ nhớ RAM"}, {"left": "SHA-256 thuần túy", "right": "Không an toàn cho mật khẩu vì tốc độ tính toán quá nhanh trên GPU"}] , "explanation": "Lựa chọn đúng KDF bảo vệ an toàn cho kho dữ liệu xác thực của hệ thống."},
                {"type": "FILL_BLANK", "question": "Thuật toán băm mật khẩu thế hệ mới chiến thắng giải thưởng Password Hashing Competition (PHC) là [_____] (Argon2).", "blanks": [{"accepted_answers": ["Argon2", "argon2", "Argon2id"]}], "explanation": "Argon2 (đặc biệt là biến thể Argon2id) là tiêu chuẩn vàng chống lại các cuộc tấn công phần cứng."}
            ]
        ),
        (
            8,
            "Bài 5.8: Kiểm Thử An Ninh Xác Thực API: OAuth 2.0 PKCE, JSON Web Token (JWT) & Quản Lý Refresh Token",
            "Nghiên cứu kiến trúc xác thực API di động, tiêu chuẩn OAuth 2.0 Authorization Code với PKCE và rủi ro lưu trữ JWT.",
            [
                "Hiểu sâu lỗ hổng của luồng OAuth Implicit Flow truyền thống và lý do bị cấm trên di động.",
                "Làm chủ cơ chế Proof Key for Code Exchange (PKCE) với code_verifier và code_challenge.",
                "Phân tích cấu trúc 3 phần của JSON Web Token (Header, Payload, Signature) và các lỗ hổng xác thực chữ ký.",
                "Quản lý vòng đời Access Token ngắn hạn và lưu trữ bảo mật Refresh Token trong Keystore."
            ],
            [
                ("Cuộc Cách Mạng OAuth 2.0 PKCE Trên Ứng Dụng Di Động", "Trong kiến trúc ứng dụng di động kết nối Backend, việc truyền trực tiếp tài khoản mật khẩu của người dùng lên API là một thiết kế rủi ro cao. Tiêu chuẩn vàng được áp dụng là `OAuth 2.0`. "
                "Tuy nhiên, ứng dụng di động là một Public Client (không thể bảo vệ bí mật Client Secret an toàn vì client có thể bị dịch ngược). Luồng Authorization Code truyền thống dễ bị tấn công chiếm đoạt Authorization Code qua Deep Link. "
                "Để giải quyết triệt để, chuẩn mở rộng RFC 7636 ra đời: `Proof Key for Code Exchange (PKCE)`. PKCE loại bỏ hoàn toàn việc sử dụng Client Secret, thay vào đó client tự sinh một mã ngẫu nhiên bí mật `code_verifier` và dẫn xuất mã băm `code_challenge = SHA256(code_verifier)`. Kẻ tấn công dù có cướp được mã Authorization Code cũng không thể đổi lấy token vì không nắm giữ `code_verifier`!"),
                ("Giải Phẫu JSON Web Token (JWT) & Các Lỗ Hổng Nguy Hiểm", "JSON Web Token (JWT) là định dạng token xác thực không trạng thái (stateless) phổ biến nhất, gồm 3 phần phân tách bằng dấu chấm: `Header.Payload.Signature`. "
                "Các lỗ hổng phổ biến cần kiểm thử: "
                "1. Tấn công thuật toán `\"alg\": \"none\"`: Máy chủ thiếu kiểm tra lỏng lẻo chấp nhận các token không có chữ ký số. "
                "2. Tấn công nhầm lẫn thuật toán (Key Confusion Attack): Máy chủ sử dụng khóa công khai RSA để xác minh token HMAC-SHA256. "
                "3. Lộ lọt thông tin nhạy cảm trong Payload: Payload chỉ được mã hóa Base64URL chứ KHÔNG hề được mã hóa bí mật; bất kỳ ai cũng có thể giải mã và đọc được các trường dữ liệu."),
                ("Chiến Lược Quản Lý Vòng Đời Token Hai Tầng", "Để cân bằng giữa trải nghiệm người dùng và an toàn bảo mật, hệ thống áp dụng cơ chế 2 token: "
                "1. `Access Token`: Có thời hạn sống rất ngắn (từ 5 đến 15 phút), dùng để gọi các API tài nguyên. Nếu bị lộ, thiệt hại bị giới hạn trong khoảng thời gian ngắn. "
                "2. `Refresh Token`: Có thời hạn dài (từ vài tuần đến vài tháng), chỉ dùng duy nhất để xin cấp lại Access Token mới. Refresh Token bắt buộc phải được mã hóa và lưu trữ bên trong `EncryptedSharedPreferences` bảo vệ bởi Android Keystore.")
            ],
            "Kịch bản tấn công: Kẻ tấn công dịch ngược APK, tìm thấy Refresh Token của người dùng được lưu trữ dưới dạng chuỗi rõ trong tệp SharedPreferences. Kẻ tấn công copy token này sang máy tính và liên tục gọi API để sinh ra Access Token mới vô thời hạn, duy trì quyền kiểm soát tài khoản nạn nhân ngay cả khi nạn nhân đổi mật khẩu! Phòng thủ: Bắt buộc mã hóa Refresh Token bằng Keystore và máy chủ phải triển khai cơ chế Xoay vòng Refresh Token (Refresh Token Rotation) - hủy bỏ toàn bộ phiên nếu phát hiện một token cũ bị tái sử dụng.",
            "Trong phần thực hành, chúng ta sẽ sử dụng thư viện AppAuth-Android để cấu hình luồng đăng nhập OAuth 2.0 PKCE an toàn:",
            ("kotlin", """// Cấu hình OAuth 2.0 với PKCE bằng thư viện AppAuth
val serviceConfig = AuthorizationServiceConfiguration(
    Uri.parse("https://auth.backend.com/oauth/authorize"),
    Uri.parse("https://auth.backend.com/oauth/token")
)

val authRequest = AuthorizationRequest.Builder(
    serviceConfig,
    "CLIENT_ID_MOBILE",
    ResponseTypeValues.CODE,
    Uri.parse("com.backend.androidsec://oauth2callback")
)
    .setCodeVerifier(CodeVerifierUtil.generateRandomCodeVerifier())
    .setScope("openid profile email")
    .build()"""),
            ["Không bao giờ nhúng Client Secret cố định trong mã nguồn ứng dụng di động.", "Luôn kiểm tra thời hạn hết hạn (exp claim) của JWT trước khi gửi yêu cầu mạng."],
            ["OAuth 2.0 với PKCE là tiêu chuẩn bảo mật bắt buộc cho các ứng dụng di động Public Client.", "JWT Payload chỉ là chuỗi Base64 rõ và không bao giờ được chứa thông tin bí mật.", "Mô hình Access Token ngắn hạn kết hợp lưu trữ bảo vệ Refresh Token tối ưu hóa an ninh hệ thống."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Chuẩn mở rộng bảo mật bắt buộc của OAuth 2.0 dành cho ứng dụng di động loại bỏ việc sử dụng Client Secret và chống chiếm đoạt mã Authorization Code có tên viết tắt là gì?", "options": ["A. PKCE (Proof Key for Code Exchange)", "B. SAML 2.0", "C. OpenID Connect Core", "D. Kerberos"], "correct_index": 0, "explanation": "PKCE (RFC 7636) bảo vệ luồng Authorization Code trên các ứng dụng di động."},
                {"type": "FILL_BLANK", "question": "Định dạng mã thông báo xác thực không trạng thái bao gồm 3 phần Header, Payload và Signature phân tách bởi dấu chấm có tên viết tắt là [_____].", "blanks": [{"accepted_answers": ["JWT", "jwt", "Json Web Token"]}], "explanation": "JSON Web Token (JWT) là chuẩn token phổ biến nhất trong các REST API."},
                {"type": "MATCHING", "question": "Nối loại Token với đặc tính vòng đời:", "pairs": [{"left": "Access Token", "right": "Thời hạn sống rất ngắn (5-15 phút), dùng để gọi API tài nguyên"}, {"left": "Refresh Token", "right": "Thời hạn dài, lưu trữ bảo mật trong Keystore, dùng để cấp lại Access Token"}, {"left": "Code Verifier", "right": "Chuỗi ngẫu nhiên bí mật sinh bởi client trong luồng OAuth PKCE"}] , "explanation": "Phân chia rõ ràng vai trò token giúp hệ thống vừa an toàn vừa mượt mà."},
                {"type": "FILL_BLANK", "question": "Thuật toán giả mạo nguy hiểm trong JWT Header khiến máy chủ bỏ qua việc kiểm tra chữ ký số là \"alg\": \"[_____]\".", "blanks": [{"accepted_answers": ["none", "NONE"]}], "explanation": "Lỗ hổng \"none\" algorithm là lỗi logic kinh điển trong các thư viện xác thực JWT cũ."}
            ]
        ),
        (
            9,
            "Bài 5.9: Lỗ Hổng Tràn Bộ Đệm & Khai Thác Lỗi Quản Lý Bộ Nhớ Trong Thư Viện Native C/C++",
            "Nghiên cứu các lỗ hổng quản lý bộ nhớ nguy hiểm trong mã native JNI, tràn bộ đệm Buffer Overflow và khai thác ROP.",
            [
                "Hiểu cơ chế tương tác bộ nhớ giữa máy ảo ART và không gian địa chỉ bản địa (Native Memory).",
                "Phân tích lỗ hổng tràn bộ đệm ngăn xếp (Stack-based Buffer Overflow) khi sử dụng các hàm không an toàn (`strcpy`, `sprintf`).",
                "Hiểu cơ chế lỗ hổng Sử dụng bộ nhớ sau giải phóng (Use-After-Free) và Ghi đè con trỏ hàm.",
                "Áp dụng các cờ biên dịch làm cứng bộ nhớ trong Android NDK: Stack Protector, ASLR/PIE, và Clang Sanitizers."
            ],
            [
                ("Bản Chất Của Lỗ Hổng Bộ Nhớ Trong Mã Native JNI", "Trong khi mã nguồn Java và Kotlin được máy ảo ART quản lý bộ nhớ tự động với bộ gom rác (Garbage Collector) - giúp triệt tiêu hầu hết các lỗi quản lý bộ nhớ cơ bản - các thư viện native C/C++ biên dịch qua Android NDK lại cấp quyền quản lý bộ nhớ thủ công trực tiếp cho lập trình viên (`malloc`, `free`, con trỏ). "
                "Nếu lập trình viên không kiểm tra kích thước vùng đệm trước khi sao chép dữ liệu, kẻ tấn công có thể gửi các gói tin có dung lượng vượt quá kích thước được cấp phát để ghi đè lên các ô nhớ lân cận, phá vỡ luồng điều khiển của chương trình."),
                ("Các Dạng Lỗ Hổng Bộ Nhớ Phổ Biến", "1. Tràn bộ đệm ngăn xếp (Stack Buffer Overflow): Xảy ra khi sử dụng các hàm C cổ điển không giới hạn độ dài như `strcpy()`, `strcat()`, `gets()`, `sprintf()`. Dữ liệu thừa sẽ tràn qua vùng đệm và ghi đè trực tiếp lên con trỏ địa chỉ trả về (Saved Return Address) trên stack. Khi hàm kết thúc, CPU sẽ nhảy con trỏ lệnh vào địa chỉ do kẻ tấn công điều khiển! "
                "2. Use-After-Free (UAF): Xảy ra khi một con trỏ tiếp tục được sử dụng sau khi vùng nhớ mà nó trỏ tới đã bị giải phóng bằng `free()`. Kẻ tấn công có thể cấp phát một đối tượng mới vào đúng vị trí ô nhớ đó để đánh lừa luồng thực thi. "
                "3. Integer Overflow: Tràn số nguyên dẫn đến việc cấp phát vùng nhớ quá nhỏ (`malloc(len)`), sau đó sao chép lượng dữ liệu lớn gây tràn heap."),
                ("Kỹ Thuật Xây Dựng ROP Chain & Vượt Rào NX/ASLR", "Trên các hệ thống Android hiện đại có bảo vệ NX (không thể thực thi mã trên stack) và ASLR (địa chỉ bị xáo trộn), kẻ tấn công sử dụng kỹ thuật Lập trình hướng trả về (Return-Oriented Programming - ROP). "
                "Kẻ tấn công không bơm shellcode mới mà tìm kiếm các đoạn mã máy sẵn có kết thúc bằng lệnh `RET` (gọi là các ROP Gadgets) nằm rải rác bên trong các thư viện hệ thống như `libc.so`. Bằng cách sắp xếp các địa chỉ gadget lên ngăn xếp bị tràn, kẻ tấn công ghép nối chúng thành một chuỗi lệnh hoàn chỉnh để gọi hàm `system(\"/system/bin/sh\")` nhằm thực thi mã tùy ý!")
            ],
            "Kịch bản tấn công: Ứng dụng xử lý hình ảnh sử dụng thư viện C++ native `libimage_filter.so` để giải mã tệp ảnh tùy biến. Kẻ tấn công tạo một tệp ảnh chứa tiêu đề kích thước giả mạo gây tràn bộ đệm heap trong hàm giải mã. Khi nạn nhân mở ứng dụng, ứng dụng tự động thực thi mã khai thác và cấp quyền shell cho tin tặc! Phòng thủ: Thay thế 100% các hàm C không an toàn bằng các hàm có kiểm soát kích thước (`strncpy`, `snprintf`). Bật đầy đủ các cờ bảo vệ trình biên dịch Clang trong `CMakeLists.txt`.",
            "Trong phần thực hành, chúng ta sẽ cấu hình tệp build CMake an toàn với các cờ bảo vệ bộ nhớ cao cấp nhất:",
            ("cmake", """# CMakeLists.txt bảo mật cho Android NDK
cmake_minimum_required(VERSION 3.22.1)
project("securenativelib")

# Bật các cờ bảo vệ bộ nhớ bắt buộc
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fstack-protector-strong -D_FORTIFY_SOURCE=2 -fPIE")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fstack-protector-strong -D_FORTIFY_SOURCE=2 -fPIE")

# Bật Control Flow Integrity (CFI) để chống tấn công ROP
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=cfi -fvisibility=hidden")

add_library(securenativelib SHARED native-lib.cpp)"""),
            ["Tuyệt đối không bao giờ sử dụng các hàm C nguy hiểm: strcpy, sprintf, gets trong mã native.", "Kích hoạt cờ -fstack-protector-strong và -D_FORTIFY_SOURCE=2 trong mọi dự án NDK."],
            ["Mã native C/C++ là ranh giới tiềm ẩn các lỗ hổng quản lý bộ nhớ nguy hiểm nhất.", "Tràn bộ đệm ghi đè địa chỉ trả về cho phép kẻ tấn công chiếm quyền điều khiển CPU.", "Cờ bảo vệ Stack Canaries, ASLR/PIE và Clang CFI là lá chắn phòng thủ bắt buộc cho NDK."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Hàm thao tác chuỗi nguy hiểm nào trong ngôn ngữ C/C++ tuyệt đối bị cấm sử dụng vì không kiểm tra giới hạn kích thước bộ đệm đích và là nguyên nhân hàng đầu gây tràn bộ đệm stack?", "options": ["A. strcpy", "B. strncpy", "C. snprintf", "D. memcpy_s"], "correct_index": 0, "explanation": "strcpy sao chép chuỗi cho đến khi gặp ký tự null mà không kiểm tra kích thước đích."},
                {"type": "FILL_BLANK", "question": "Kỹ thuật khai thác mã độc tận dụng các đoạn mã máy có sẵn kết thúc bằng lệnh RET trong bộ nhớ để vượt qua cơ chế bảo vệ W^X/DEP có tên viết tắt là [_____] (Return-Oriented Programming).", "blanks": [{"accepted_answers": ["ROP", "rop"]}], "explanation": "Return-Oriented Programming (ROP) là kỹ thuật khai thác bộ nhớ tiên tiến nhất hiện nay."},
                {"type": "MATCHING", "question": "Nối cờ trình biên dịch Clang NDK với cơ chế bảo vệ:", "pairs": [{"left": "-fstack-protector-strong", "right": "Chèn Stack Canaries bảo vệ các hàm có mảng bộ đệm"}, {"left": "-D_FORTIFY_SOURCE=2", "right": "Kiểm tra kích thước bộ đệm thời gian chạy cho các hàm bộ nhớ"}, {"left": "-fsanitize=cfi", "right": "Kiểm tra tính toàn vẹn luồng điều khiển (Control Flow Integrity)"}] , "explanation": "Kích hoạt đầy đủ các cờ bảo vệ trình biên dịch giúp ngăn chặn hầu hết các exploit bộ nhớ."},
                {"type": "FILL_BLANK", "question": "Lỗ hổng an ninh bộ nhớ xuất hiện khi chương trình tiếp tục sử dụng con trỏ sau khi vùng nhớ tương ứng đã bị giải phóng được gọi là Use-[_____]-Free.", "blanks": [{"accepted_answers": ["After", "after", "After-Free"]}], "explanation": "Use-After-Free (UAF) là lỗ hổng nghiêm trọng cho phép chiếm quyền kiểm soát luồng thực thi."}
            ]
        ),
        (
            10,
            "Bài 5.10: Đánh Giá An Ninh Ứng Dụng Đa Nền Tảng: Flutter, React Native & Kiểm Thử Hermit Engine",
            "Nghiên cứu kiến trúc ứng dụng lai đa nền tảng, bóc tách tệp bundle JavaScript, dịch ngược Dart Snapshot và bypass bảo mật.",
            [
                "Hiểu sự khác biệt về mặt kiến trúc giữa ứng dụng Android Native thuần túy và ứng dụng Đa nền tảng (Cross-Platform).",
                "Phân tích ứng dụng React Native: bóc tách tệp JavaScript bundle (`index.android.bundle`) và dịch ngược Hermes Bytecode.",
                "Phân tích ứng dụng Flutter: kiến trúc Dart AOT Snapshot (`libapp.so`) và kỹ thuật dịch ngược bằng Darter/Frida.",
                "Nhận diện các thách thức kiểm thử bảo mật mạng và SSL Pinning trên các nền tảng lai."
            ],
            [
                ("Sự Trỗi Dậy Của Các Khung Phát Triển Đa Nền Tảng", "Trong phát triển phần mềm hiện đại, các framework đa nền tảng như `React Native` (Meta) và `Flutter` (Google) chiếm tỷ trọng rất lớn vì cho phép chia sẻ mã nguồn giữa Android và iOS. "
                "Tuy nhiên, kiến trúc của các ứng dụng này hoàn toàn khác biệt với ứng dụng Android Java/Kotlin truyền thống: lớp mã nguồn Java chỉ đóng vai trò là một cái vỏ mỏng (Thin Native Wrapper), toàn bộ logic nghiệp vụ thực tế được đóng gói trong một môi trường thực thi hoàn toàn tách biệt."),
                ("Phân Tích An Ninh Ứng Dụng React Native & Hermes Engine", "Ứng dụng React Native đóng gói toàn bộ logic bằng JavaScript. "
                "Trong các phiên bản cũ, mã nguồn nằm trong tệp văn bản rõ `assets/index.android.bundle`. Chuyên gia bảo mật chỉ cần mở tệp này bằng VS Code hoặc công cụ beautifier để đọc toàn bộ mã nguồn, thuật toán mã hóa và các endpoint API! "
                "Trên các phiên bản hiện đại, Meta sử dụng `Hermes Engine`: mã JavaScript được biên dịch trước thành Hermes Bytecode nhị phân (tệp bundle bắt đầu bằng magic bytes `c6 1f bc 03`). Để phân tích, chuyên gia sử dụng công cụ dịch ngược `hbctool` để khôi phục Hermes Bytecode trở lại mã JavaScript."),
                ("Phân Tích An Ninh Ứng Dụng Flutter & Dart AOT", "Flutter là nền tảng phức tạp và thử thách nhất đối với các chuyên gia dịch ngược. Flutter biên dịch toàn bộ mã Dart thành mã máy AOT nhị phân được đóng gói bên trong thư viện native `lib/arm64-v8a/libapp.so`. "
                "Tệp `libapp.so` không sử dụng chuẩn JNI thông thường và không có các hàm export rõ ràng. Toàn bộ các cấu trúc đối tượng và bảng phương thức được quản lý bởi Dart Runtime Snapshot. Để phân tích, chuyên gia sử dụng các script Frida chuyên dụng (như `frida-flutter`) để quét cấu trúc bảng đối tượng và hook vào các hàm Dart lúc chạy."),
                ("Thách Thức Bắt Gói Mạng Trên Flutter", "Như đã đề cập ở Bài 4.7, Flutter hoàn toàn bỏ qua cấu hình proxy của hệ điều hành Android và không sử dụng kho chứng chỉ của hệ thống. Ứng dụng Flutter tự nhúng thư viện `BoringSSL` riêng. Vì vậy, khi cấu hình proxy trên WiFi, Burp Suite hoàn toàn không bắt được bất kỳ gói tin nào của Flutter! Chuyên gia bắt buộc phải sử dụng iptables redirect hoặc dùng Frida hook hàm native trong `libflutter.so` mới có thể chặn bắt lưu lượng.")
            ],
            "Kịch bản tấn công: Kẻ tấn công tải APK React Native, trích xuất tệp `index.android.bundle`. Mặc dù ứng dụng có làm rối một phần, kẻ tấn công dễ dàng tìm thấy toàn bộ các hàm gọi API thanh toán và các khóa cấu hình Firebase nhúng trong mã JavaScript. Phòng thủ: Kích hoạt Hermes compilation, làm rối mã nguồn JavaScript bằng Jscrambler hoặc Obfuscator.io, và không lưu trữ secret keys trên client.",
            "Trong phần thực hành, chúng ta sẽ kiểm tra xem một tệp APK thuộc nền tảng nào và trích xuất tệp bundle:",
            ("bash", """# 1. Nhận diện nền tảng công nghệ của APK
unzip -l target.apk | grep -E "libflutter.so|index.android.bundle|libhermes.so"

# 2. Nếu là React Native, trích xuất và định dạng lại tệp JavaScript bundle
unzip -p target.apk "assets/index.android.bundle" > app_bundle.js
head -n 30 app_bundle.js

# 3. Sử dụng công cụ hbctool để dịch ngược Hermes Bytecode (nếu có)
hbctool disasm target.apk/assets/index.android.bundle ./hermes_disasm"""),
            ["Không bao giờ giả định rằng mã JavaScript hoặc Dart là an toàn khỏi dịch ngược.", "Luôn nhớ rằng Flutter tự đóng gói ngăn xếp mạng riêng và bỏ qua proxy WiFi thông thường."],
            ["React Native đóng gói mã nguồn trong tệp JavaScript bundle hoặc Hermes Bytecode.", "Flutter biên dịch mã máy Dart AOT nhúng trong thư viện native libapp.so.", "Kiểm thử mạng Flutter đòi hỏi kỹ thuật hook native BoringSSL hoặc chuyển tiếp iptables."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tệp thư viện native C/C++ nào trong gói APK Flutter chứa toàn bộ mã nguồn Dart đã được biên dịch thành mã máy AOT của ứng dụng?", "options": ["A. lib/arm64-v8a/libapp.so", "B. lib/arm64-v8a/libflutter.so", "C. classes.dex", "D. assets/flutter_assets"], "correct_index": 0, "explanation": "libapp.so chứa toàn bộ logic nghiệp vụ ứng dụng Flutter đã biên dịch AOT."},
                {"type": "FILL_BLANK", "question": "Engine máy ảo JavaScript được Meta tối ưu hóa riêng cho React Native giúp biên dịch mã nguồn thành bytecode nhị phân có tên là [_____] (Hermes).", "blanks": [{"accepted_answers": ["Hermes", "hermes", "Hermes Engine"]}], "explanation": "Hermes Engine cải thiện thời gian khởi động và hiệu năng bộ nhớ cho React Native."},
                {"type": "MATCHING", "question": "Nối nền tảng đa nền tảng với định dạng mã nguồn đóng gói:", "pairs": [{"left": "React Native truyền thống", "right": "Tệp văn bản JavaScript bundle (index.android.bundle)"}, {"left": "React Native hiện đại", "right": "Mã nhị phân Hermes Bytecode (.hbc)"}, {"left": "Flutter", "right": "Mã máy nhị phân Dart AOT trong thư viện native libapp.so"}] , "explanation": "Mỗi nền tảng đòi hỏi bộ công cụ và kỹ thuật phân tích tĩnh riêng biệt."},
                {"type": "FILL_BLANK", "question": "Lý do lưu lượng mạng của Flutter mặc định không bị Burp Suite chặn bắt là vì Flutter tự nhúng thư viện mạng riêng có tên là Boring[_____] và bỏ qua proxy hệ thống.", "blanks": [{"accepted_answers": ["SSL", "ssl", "BoringSSL"]}], "explanation": "BoringSSL nhúng trong libflutter.so không đọc cấu hình proxy Wi-Fi của Android."}
            ]
        ),
        (
            11,
            "Bài 5.11: Phòng Vệ Chủ Động Lúc Chạy: RASP (Runtime Application Self-Protection), Chống Can Thiệp & Anti-Frida",
            "Nghiên cứu kiến trúc phòng thủ chủ động RASP, phát hiện Hooking, quét bộ nhớ tiến trình và kỹ thuật tự bảo vệ ứng dụng.",
            [
                "Hiểu nguyên lý hoạt động của giải pháp Phòng vệ ứng dụng lúc chạy (Runtime Application Self-Protection - RASP).",
                "Phân tích các kỹ thuật phát hiện Frida: quét cổng TCP 27042, quét bản đồ bộ nhớ `/proc/self/maps`, và kiểm tra ptrace.",
                "Kỹ thuật phát hiện Hooking và can thiệp mã nhị phân: Prologue Verification và kiểm tra chữ ký hàm.",
                "Thiết kế cơ chế tự hủy và khóa phiên khi phát hiện mối đe dọa an ninh nghiêm trọng (Fail-Closed Architecture)."
            ],
            [
                ("Khái Niệm Phòng Vệ Ứng Dụng Lúc Chạy (RASP)", "Trong mô hình bảo mật truyền thống, ứng dụng là một thực thể thụ động hoàn toàn phụ thuộc vào hệ điều hành. Khi thiết bị bị Root hoặc bị tin tặc đính kèm công cụ can thiệp động, ứng dụng hoàn toàn không hay biết. "
                "Runtime Application Self-Protection (RASP) là công nghệ biến ứng dụng thành một thực thể phòng thủ chủ động: ứng dụng được tích hợp sẵn các bộ cảm biến giám sát liên tục môi trường thực thi lúc chạy, tự động phát hiện các hành vi bất thường và chủ động phản ứng (tự sát tiến trình, xóa sạch dữ liệu bí mật trong RAM, hoặc khóa tài khoản) mà không cần sự can thiệp của con người."),
                ("Các Kỹ Thuật Phát Hiện Frida Cốt Lõi", "Một mô-đun RASP chuyên nghiệp triển khai các chốt chặn phát hiện Frida đa tầng: "
                "1. Quét cổng kết nối: Thử kết nối TCP vào cổng cục bộ `127.0.0.1:27042` hoặc gửi gói tin D-Bus handshake. Nếu có dịch vụ phản hồi, frida-server đang chạy. "
                "2. Quét bản đồ bộ nhớ (`/proc/self/maps` và `/proc/self/task/`): Đọc danh sách các tệp thư viện được nạp vào tiến trình. Nếu phát hiện các chuỗi ký tự nhạy cảm như `frida-agent.so`, `frida-gadget.so`, `linjector`, hoặc các thư viện không có nguồn gốc rõ ràng, kích hoạt cảnh báo ngay lập tức. "
                "3. Kiểm tra TracerPid: Đọc tệp `/proc/self/status`. Trường `TracerPid` bình thường có giá trị bằng 0. Nếu `TracerPid > 0`, chứng tỏ đang có một tiến trình khác (như gdb hoặc frida-server qua ptrace) đang theo dõi và kiểm soát ứng dụng!"),
                ("Phát Hiện Hooking Bằng Prologue Verification", "Khi các công cụ hook (như Frida hoặc Xposed) can thiệp vào một hàm C/C++ native, chúng bắt buộc phải ghi đè 4 đến 8 byte đầu tiên của hàm bằng lệnh nhảy (`LDR PC, [PC, #0]` hoặc `B <addr>`). "
                "Kỹ thuật Prologue Verification: Ứng dụng đọc trực tiếp các byte mở đầu của các hàm hệ thống nhạy cảm (như `open`, `read`, `strcmp`, `ptrace`). Nếu các byte mở đầu không trùng khớp với mã máy gốc chuẩn của trình biên dịch, ứng dụng phát hiện hàm đã bị hook và lập tức tự chấm dứt tiến trình bằng lời gọi `exit(0)` hoặc `kill(getpid(), SIGKILL)`.")
            ],
            "Kịch bản tấn công: Kẻ tấn công cố gắng đính kèm Frida vào ứng dụng ngân hàng tích hợp RASP. Ngay khi luồng V8 engine vừa nạp vào bộ nhớ, luồng giám sát nền của RASP phát hiện tệp `frida-agent.so` trong `/proc/self/maps`. RASP lập tức ghi đè toàn bộ mảng byte của khóa mã hóa trong RAM bằng số 0, sau đó gọi `android.os.Process.killProcess(android.os.Process.myPid())`. Kẻ tấn công hoàn toàn không kịp thực thi bất kỳ lệnh nào! Phòng thủ: RASP là giải pháp phòng vệ bắt buộc đối với các ứng dụng tài chính cấp độ cao.",
            "Trong phần thực hành, chúng ta sẽ lập trình một hàm kiểm tra phát hiện Frida và TracerPid bằng mã C++ native:",
            ("cpp", """// Phát hiện Debugger và Frida qua TracerPid trong /proc/self/status
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>

void checkTracerAndFrida() {
    FILE *fp = fopen("/proc/self/status", "r");
    if (!fp) return;
    
    char line[128];
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "TracerPid:", 10) == 0) {
            int tracerPid = atoi(&line[10]);
            if (tracerPid != 0) {
                // Đang bị theo dõi bởi Debugger hoặc Frida ptrace!
                fclose(fp);
                kill(getpid(), SIGKILL); // Tự sát ngay lập tức
            }
            break;
        }
    }
    fclose(fp);
}"""),
            ["Tuyệt đối không hiển thị thông báo chi tiết lý do ứng dụng bị tắt để tránh cung cấp thông tin cho kẻ tấn công.", "Đảm bảo mã kiểm tra RASP được phân tán ngẫu nhiên và làm rối mã nguồn để tránh bị patch."],
            ["RASP biến ứng dụng thành một thực thể tự vệ chủ động trong môi trường không tin cậy.", "Phát hiện Frida dựa trên quét cổng 27042, quét /proc/self/maps và theo dõi TracerPid.", "Prologue Verification phát hiện hành vi ghi đè byte mở đầu của các hàm native."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Trường thông tin nào trong tệp hệ thống /proc/self/status có giá trị lớn hơn 0 biểu thị rằng tiến trình hiện tại đang bị một debugger hoặc công cụ can thiệp động gắn kết theo dõi qua ptrace?", "options": ["A. TracerPid", "B. PPid", "C. Uid", "D. Gid"], "correct_index": 0, "explanation": "TracerPid ghi nhận Process ID của tiến trình đang debug; bình thường có giá trị bằng 0."},
                {"type": "FILL_BLANK", "question": "Khái niệm an ninh chỉ các giải pháp tự bảo vệ và phòng thủ chủ động tích hợp trực tiếp vào ứng dụng lúc chạy được viết tắt là [_____] (Runtime Application Self-Protection).", "blanks": [{"accepted_answers": ["RASP", "rasp"]}], "explanation": "RASP là công nghệ phòng vệ chủ động tiêu chuẩn cho ứng dụng di động bảo mật cao."},
                {"type": "MATCHING", "question": "Nối kỹ thuật RASP với dấu hiệu phát hiện:", "pairs": [{"left": "Kiểm tra /proc/self/maps", "right": "Tìm kiếm các chuỗi nhãn frida-agent.so hoặc xposed trong RAM"}, {"left": "Kiểm tra TracerPid", "right": "Phát hiện tiến trình đang bị đính kèm bởi gdb hoặc frida ptrace"}, {"left": "Prologue Verification", "right": "Kiểm tra các byte mở đầu hàm native có bị ghi đè lệnh nhảy hook"}] , "explanation": "Hệ thống cảm biến RASP đa tầng bảo vệ toàn diện ứng dụng."},
                {"type": "FILL_BLANK", "question": "Tín hiệu hệ thống không thể bị bỏ qua hoặc can thiệp được nhân Linux sử dụng để tiêu diệt ngay lập tức một tiến trình là SIG[_____].", "blanks": [{"accepted_answers": ["KILL", "kill", "SIGKILL"]}], "explanation": "SIGKILL (Signal 9) chấm dứt tiến trình lập tức mà không cho phép bắt ngoại lệ."}
            ]
        ),
        (
            12,
            "Bài 5.12: Tổng Kết Tiêu Chuẩn Bảo Mật OWASP MASVS / MASTG & Quy Trình Phát Hành An Toàn",
            "Nghiên cứu khung tiêu chuẩn an ninh di động toàn cầu OWASP MASVS, tài liệu MASTG và checklist xuất bản Google Play.",
            [
                "Nắm vững cấu trúc tiêu chuẩn OWASP Mobile Application Security Verification Standard (MASVS v2.0).",
                "Làm chủ 8 miền kiểm thử cốt lõi: STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE, RESILIENCE.",
                "Phân loại các cấp độ đảm bảo an ninh: MASVS-L1 (tiêu chuẩn), MASVS-L2 (nâng cao), và MASVS-R (kháng can thiệp).",
                "Hoàn thiện danh mục kiểm tra (Release Checklist) trước khi xuất bản ứng dụng lên Google Play Store."
            ],
            [
                ("Khung Tiêu Chuẩn Quốc Tế OWASP MASVS & MASTG", "Để chuẩn hóa quy trình đánh giá an ninh ứng dụng di động trên toàn thế giới, tổ chức OWASP (Open Web Application Security Project) xây dựng bộ tài liệu tiêu chuẩn: "
                "1. `MASVS` (Mobile Application Security Verification Standard): Định nghĩa các yêu cầu an ninh bắt buộc mà một ứng dụng di động phải đáp ứng. "
                "2. `MASTG` (Mobile Application Security Testing Guide): Cuốn cẩm nang toàn diện dài hơn 600 trang hướng dẫn chi tiết từng bước kiểm thử, lệnh thực thi và kịch bản khai thác cho cả Android và iOS."),
                ("Các Cấp Độ Đảm Bảo An Ninh (Security Verification Levels)", "OWASP MASVS phân loại ứng dụng thành 3 cấp độ đảm bảo: "
                "1. `MASVS-L1` (Standard Security): Cấp độ cơ bản bắt buộc cho MỌI ứng dụng di động. Tập trung vào việc lưu trữ dữ liệu an toàn, mã hóa mạng HTTPS chuẩn mực và tuân thủ các quy tắc bảo mật nền tảng Android. "
                "2. `MASVS-L2` (Defense-in-Depth): Áp dụng cho các ứng dụng xử lý dữ liệu tài chính, ngân hàng, y tế hoặc doanh nghiệp. Bổ sung các yêu cầu kiểm soát phiên đăng nhập khắt khe, xác thực sinh trắc học ràng buộc phần cứng và mã hóa đa tầng. "
                "3. `MASVS-R` (Resilience Against Reverse Engineering): Dành riêng cho các ứng dụng có tài sản trí tuệ cao hoặc đối mặt với gian lận game/tài chính. Bắt buộc triển khai làm rối mã nguồn, phát hiện Root, chống can thiệp Frida và tự bảo vệ RASP."),
                ("Checklist Xuất Bản Ứng Dụng An Toàn Lên Google Play", "Trước khi nhấn nút xuất bản ứng dụng lên Production Track của Google Play Console, đội ngũ DevSecOps phải hoàn thành bảng kiểm toán: "
                "Cờ `android:debuggable` bắt buộc là `false`. "
                "Cờ `android:allowBackup` bắt buộc là `false` (hoặc có cấu hình backup_rules an toàn). "
                "Vô hiệu hóa 100% các dòng ghi log `Log.d()`, `Log.v()` trong mã phát hành bằng quy tắc R8/ProGuard `-assumenosideeffects`. "
                "Chữ ký số bắt buộc sử dụng APK Signature Scheme v2 và v3. "
                "Không có bất kỳ khóa bí mật (Secret Keys) nào bị nhúng cứng trong mã nguồn. "
                "Quét tự động bằng MobSF đạt điểm số an ninh trên 90/100.")
            ],
            "Kịch bản tấn công: Kẻ tấn công tìm kiếm các ứng dụng không tuân thủ MASVS-L1: lưu trữ dữ liệu trong thư mục ngoài, bật cờ allowBackup và để lộ API keys. Kẻ tấn công dễ dàng khai thác chuỗi lỗ hổng để chiếm đoạt tài khoản người dùng và làm tổn hại uy tín thương hiệu doanh nghiệp. Phòng thủ: Áp dụng bảng kiểm tra OWASP MASVS làm tiêu chuẩn nghiệm thu chất lượng (Quality Gate) bắt buộc cho mọi đợt phát hành.",
            "Trong phần thực hành, chúng ta sẽ cấu hình tệp quy tắc R8 / ProGuard proguard-rules.pro an toàn để tự động xóa sạch nhật ký Logcat:",
            ("proguard", """# proguard-rules.pro - Cấu hình làm rối và bảo vệ an toàn phát hành
# 1. Loại bỏ hoàn toàn các lời gọi ghi nhật ký Logcat trong bản phát hành
-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int v(...);
    public static int d(...);
    public static int i(...);
}

# 2. Làm rối sâu tên lớp và phương thức
-repackageclasses ''
-allowaccessmodification

# 3. Giữ lại các annotation bảo mật bắt buộc
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod

# 4. Bảo vệ các interface JavaScript của WebView
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}"""),
            ["Luôn cấu hình quy tắc ProGuard loại bỏ hoàn toàn mã Log.d() và Log.v() để tránh rò rỉ dữ liệu qua Logcat.", "Áp dụng checklist OWASP MASVS cho từng tính năng mới trước khi sáp nhập vào nhánh main."],
            ["OWASP MASVS và MASTG là chuẩn mực toàn cầu cho an ninh ứng dụng di động.", "Ba cấp độ MASVS-L1, MASVS-L2 và MASVS-R định hướng chính xác mức độ bảo vệ cần thiết.", "Quy tắc ProGuard xóa nhật ký Logcat và làm rối mã nguồn là bước chuẩn bị xuất bản bắt buộc."],
            [
                {"type": "MULTIPLE_CHOICE", "question": "Tiêu chuẩn xác minh an ninh ứng dụng di động quốc tế do tổ chức OWASP ban hành có tên viết tắt chính thức là gì?", "options": ["A. OWASP MASVS", "B. OWASP ASVS", "C. ISO 27001", "D. PCI-DSS Mobile"], "correct_index": 0, "explanation": "OWASP MASVS (Mobile Application Security Verification Standard) là tiêu chuẩn bảo mật di động toàn cầu."},
                {"type": "FILL_BLANK", "question": "Cấp độ bảo đảm an ninh bổ sung trong tiêu chuẩn OWASP MASVS tập trung vào khả năng chống dịch ngược, chống can thiệp và tự bảo vệ lúc chạy có ký hiệu là MASVS-[_____].", "blanks": [{"accepted_answers": ["R", "r", "MASVS-R"]}], "explanation": "MASVS-R (Resilience) quy định các yêu cầu kháng dịch ngược và chống giả mạo."},
                {"type": "MATCHING", "question": "Nối cấp độ đảm bảo MASVS với đối tượng ứng dụng:", "pairs": [{"left": "MASVS-L1", "right": "Bảo mật cơ bản bắt buộc cho tất cả các ứng dụng di động"}, {"left": "MASVS-L2", "right": "Bảo vệ chuyên sâu cho ứng dụng tài chính, ngân hàng và y tế"}, {"left": "MASVS-R", "right": "Kháng can thiệp và tự bảo vệ chống lại việc dịch ngược bằng Frida"}] , "explanation": "Hệ thống phân cấp giúp tối ưu hóa chi phí và nguồn lực bảo mật."},
                {"type": "FILL_BLANK", "question": "Chỉ thị cấu hình ProGuard/R8 được sử dụng để tự động xóa bỏ hoàn toàn các dòng lệnh ghi log android.util.Log khỏi bản phát hành là -assume[_____]effects.", "blanks": [{"accepted_answers": ["noside", "noSide", "assumenosideeffects"]}], "explanation": "-assumenosideeffects xóa sạch các lời gọi hàm không có tác dụng phụ trong bytecode phát hành."}
            ]
        )
    ]

    for spec in ch5_specs:
        pos, title, summary, objs, theory, attack_def, lab_text, code_snp, pitfalls, summaries, quiz = spec
        vid_idx = (pos - 1) % len(VIDEO_CACHE)
        vurl = VIDEO_CACHE[vid_idx]["url"]

        md_content = generate_lesson_markdown(
            lesson_num=f"5.{pos}",
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
