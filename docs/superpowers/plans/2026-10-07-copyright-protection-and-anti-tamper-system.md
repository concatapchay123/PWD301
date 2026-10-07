# Kế Hoạch Hiện Thực Hóa: Thanh Trừng Toàn Diện Logic Cũ, Mã Hóa Luồng HLS/AES-128, Thủy Ấn Động Pháp Chứng & Kiểm Soát Tiến Độ Zero-Trust (TASK-085)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xóa sạch toàn bộ logic, tài liệu, mô tả và hành vi cũ về việc phân phối video MP4 thô và cơ chế tin tưởng client khi tính tiến độ bài giảng trên toàn hệ thống; thiết lập kiến trúc bảo vệ bản quyền đa tầng mới gồm: Chuyển mã và phát luồng phân mảnh HLS mã hóa AES-128 với token ngắn hạn, Thủy ấn động pháp chứng (Dynamic Forensic Watermark) mang định danh học viên chống quay lén, Lớp giáp Client Armor chống can thiệp DOM và bẫy DevTools (F12/Debugger), và Công cụ kiểm soát tiến độ thời gian thực (Server-Authoritative Wall-Clock Heartbeat) triệt tiêu 100% nguy cơ bypass.

**Architecture:** 
- **Backend (Pure Headless REST API)**: Python 3.12, Flask, SQLAlchemy, Microsoft SQL Server, FFmpeg CLI pipeline chuyển mã phân đoạn HLS (.m3u8 + .ts) mã hóa AES-128, Short-lived HMAC/JWT Video Key Exchange endpoint, Wall-Clock Time Progress Engine xóa bỏ hoàn toàn lỗ hổng nhảy cóc `seconds_spent`, và Security Audit Event dispatching.
- **Frontend (Single-DOM SPA)**: Vanilla JS (ES6+), Hls.js client, Tailwind CSS, DOMPurify. Component `VideoArmor` độc lập phụ trách: Thủy ấn động ngẫu nhiên đa tọa độ, MutationObserver giám sát tính toàn vẹn của thẻ DOM (tự tái tạo và bật Blackout màn hình đen khi bị can thiệp), DevTools Bouncer bẫy debugger/phím tắt, và Visibility/Blur tracking tự tạm dừng khi rời màn hình.

**Tech Stack:** Python 3.12, Flask, SQLAlchemy, Microsoft SQL Server, FFmpeg, Hls.js, Vanilla JS (ES6+), Tailwind CSS, Pytest, Node test runner.

**Spec & Source of Truth:**
- `docs/intent/copyright-protection.md` (Bản tuyên bố mục tiêu đã được phê duyệt qua `/grill-me`).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/04_LESSON_AND_PROGRESS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md` (Bổ sung Invariant 25).
- `AGENTS.md` (Cập nhật Invariant bảo vệ bản quyền & Zero-Trust).

---

## Global Constraints & Invariants

1. **Pure Headless Backend**: Không sinh template Jinja `*.html` hay thư mục preview tĩnh giả lập. Mọi phản hồi API đều chuẩn hóa qua phong bì JSON `{"success": true/false, "data": ..., "error": ...}`.
2. **Zero-Trust Server Authority (Anti-Bypass Iron Law)**: Không bao giờ tin tưởng các con số tiến độ client gửi lên (`view_fraction: 1.0` hay `is_completed: true`). Tiến độ chỉ được công nhận khi tích lũy đủ thời gian thực (Wall-Clock Time) $\ge$ `minimum_completion_seconds` thông qua chuỗi nhịp tim (Heartbeat) xác thực máy chủ.
3. **Fail-Closed Video Privacy**: File video gốc (.mp4) của bài giảng được khóa kín hoàn toàn trong lưu trữ private; nghiêm cấm phục vụ download thô trực tiếp cho học viên qua URL `/student/files/<id>/download`. Mọi lượt xem bắt buộc giải mã qua luồng HLS mã hóa AES-128.
4. **Dynamic Forensic Watermark Immutability**: Mọi màn hình phát video bắt buộc hiển thị thủy ấn động (`[MSSV/Họ tên] • [Email] • [IP] • [Timestamp]`) trôi ngẫu nhiên trên khung hình. Mọi nỗ lực can thiệp DOM hoặc ẩn thẻ Watermark đều kích hoạt ngay lập tức chế độ Blackout (màn hình đen) và ghi log `AuditEvent`.
5. **Zero Obsolete Workflows & Clean Memory**: Trước khi viết mã sản phẩm, bắt buộc thanh trừng và viết lại toàn bộ tài liệu đặc tả, comment mã nguồn và mô tả luồng cũ liên quan đến phân phối MP4 thô và logic nhảy cóc tiến độ.

---

## Review Focus & Anti-Regression Points

1. **Thanh trừng bộ nhớ & logic cũ:** Đảm bảo không còn bất kỳ dòng tài liệu hoặc comment nào mô tả video bài học tải về trực tiếp hoặc client có thể tự hoàn thành bài học khi xem $\ge 90\%$ mà không cần thời gian thực.
2. **Xóa lỗ hổng nhảy cóc tiến độ trong `lesson_service.py`:** Triệt tiêu hoàn toàn đoạn code tự động gán `progress.seconds_spent = min_completion_seconds` khi `view_fraction >= 0.90`.
3. **Bảo mật khóa HLS:** Endpoint cấp phát khóa giải mã AES-128 (`/video/key`) phải kiểm tra quyền ghi danh của học viên, token có thời hạn ngắn (60 giây), và header `Cache-Control: private, no-store`.
4. **Chống can thiệp Client (Client Armor):** Đảm bảo `MutationObserver` hoạt động tin cậy, không thể bị bypass bằng cách inspect element hoặc xóa node khỏi DOM.
5. **Tương thích YouTube Embed:** Áp dụng lớp phủ Dynamic Watermark và bẫy chuyển tab cho cả video nhúng ngoài để bảo vệ tính công bằng học thuật.

---

### Task 0: Thanh Trừng Toàn Diện Logic Cũ, Bộ Nhớ Cũ & Thiết Lập Bất Biến Vĩnh Viễn

**Files:**
- Create: `docs/intent/copyright-protection.md`
- Modify: `tasks/CURRENT.md`
- Modify: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/04_LESSON_AND_PROGRESS.md`
- Modify: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: Thỏa thuận phỏng vấn `/grill-me` và chỉ đạo thanh trừng toàn diện của người dùng.
- Produces: Hệ thống tài liệu đặc tả chuẩn xác, khóa chặt Invariant 25 vào hợp đồng hoạt động của agent để không bao giờ tái hiện logic cũ.

- [ ] **Step 1: Khởi tạo tài liệu tuyên bố mục tiêu `docs/intent/copyright-protection.md`**
  Ghi nhận đầy đủ Statement of Intent: Outcome, User, Why now, Success, Constraints, Out of scope, và Kiến trúc 4 tầng phòng thủ đã được phê duyệt.
- [ ] **Step 2: Viết tài liệu tuyên bố xóa bỏ (Decommissioning & Purge Declaration) trong `tasks/CURRENT.md`**
  Ghi nhận rõ ràng việc bãi bỏ vĩnh viễn:
  1. *Cũ*: Phân phối video MP4 thô qua `<video src="...">` và link tải trực tiếp `/student/files/<id>/download?disposition=inline`. *Mới*: Phân phối luồng phân mảnh HLS mã hóa AES-128 qua short-lived token.
  2. *Cũ*: Lỗ hổng cho phép client tự gửi `view_fraction >= 0.90` để nhảy cóc `seconds_spent = minimum_completion_seconds` mà không cần thời gian thực. *Mới*: Xóa sạch logic nhảy cóc này! Bắt buộc thời gian thực tích lũy $\ge$ `minimum_completion_seconds` qua nhịp tim (Heartbeat) xác thực máy chủ.
  3. *Cũ*: Không có thủy ấn định danh học viên. *Mới*: Thủy ấn động pháp chứng trôi ngẫu nhiên kèm `MutationObserver` tự bảo vệ thẻ.
  4. *Cũ*: Không phát hiện DevTools hoặc can thiệp client. *Mới*: Client Armor (bẫy debugger, bẫy phím tắt, bẫy blur/visibility).
- [ ] **Step 3: Cập nhật `04_LESSON_AND_PROGRESS.md`, `06_NON_NEGOTIABLE_INVARIANTS.md` và `AGENTS.md`**
  - Cập nhật quy tắc Lesson Completion trong `04_LESSON_AND_PROGRESS.md`.
  - Bổ sung Invariant 25 vào `06_NON_NEGOTIABLE_INVARIANTS.md` và mục 10 của `AGENTS.md`.
- [ ] **Step 4: Commit**
  ```bash
  git add tasks/CURRENT.md docs/intent/ docs/system/ AGENTS.md
  git commit -m "docs(invariants): permanently purge obsolete video and progress workflows and record TASK-085 copyright invariants"
  ```

---

### Task 1: Backend Zero-Trust Progress Heartbeat Engine & Xóa Bỏ Lỗ Hổng Nhảy Cóc Tiến Độ

**Files:**
- Modify: `src/pwd301/services/lesson_service.py`
- Modify: `src/pwd301/blueprints/api_lessons/routes.py`
- Test: `tests/unit/test_lesson_wall_clock_progress.py` (New test file)
- Test: `tests/api/test_lesson_api.py`

**Interfaces:**
- Consumes: `actor` (User), `lesson_id`, `seconds_increment` (int), `view_fraction` (float), `client_event_id` (str).
- Produces: `LessonProgress` được tính toán thuần túy dựa trên thời gian thực tích lũy, bẻ gãy 100% nỗ lực gửi payload gian lận; phát sinh `AuditEvent` nếu phát hiện gian lận nhịp tim.

- [ ] **Step 1: Viết test fail `tests/unit/test_lesson_wall_clock_progress.py`**
  - Test `test_cannot_bypass_minimum_duration_with_high_view_fraction`: Học viên gửi `view_fraction=1.0` với `seconds_increment=1` vào bài học có `minimum_completion_seconds=300` -> Bài học không được đánh dấu `completed_at`, `seconds_spent` chỉ tăng 1 giây, không nhảy lên 300 giây.
  - Test `test_heartbeat_pace_anomaly_detected`: Học viên gửi ping với tốc độ bất thường hoặc spam ping gian lận -> Ghi nhận sự kiện kiểm toán `AuditEvent` và không tích lũy thời gian gian lận.
  - Test `test_legitimate_heartbeat_accumulation_completes_lesson`: Học viên tích lũy đủ các nhịp tim hợp lệ đạt $\ge$ `minimum_completion_seconds` và $\ge$ `viewed_fraction_required` -> Bài học hoàn thành chuẩn xác.
- [ ] **Step 2: Chạy test để đảm bảo test fail**
  ```bash
  pytest tests/unit/test_lesson_wall_clock_progress.py
  ```
- [ ] **Step 3: Xóa bỏ hoàn toàn mã nguồn lỗ hổng nhảy cóc trong `lesson_service.py`**
  - Xóa bỏ đoạn mã tại dòng 1656-1664 trong `src/pwd301/services/lesson_service.py` (đoạn tự động gán `progress.seconds_spent = min_completion_seconds` khi `view_fraction >= 0.90`).
  - Bổ sung cơ chế xác thực nhịp tim Wall-Clock Time: Kiểm tra khoảng cách thời gian thực (`elapsed_time`) so với `seconds_increment`, phòng chống replay và spam ping.
  - Ghi nhận `AuditEvent` với action `LESSON_PROGRESS_ANOMALY` khi phát hiện nhịp tim bất thường.
- [ ] **Step 4: Chạy lại test suite để đảm bảo test pass**
  ```bash
  pytest tests/unit/test_lesson_wall_clock_progress.py tests/api/test_lesson_api.py
  ```
- [ ] **Step 5: Commit**
  ```bash
  git add src/pwd301/services/lesson_service.py tests/
  git commit -m "fix(security): eliminate video progress jump loophole and enforce server-authoritative wall-clock heartbeat"
  ```

---

### Task 2: Dịch Vụ Chuyển Mã HLS Phân Mảnh Mã Hóa AES-128 & Khóa Phân Phối Video Thô

**Files:**
- Create: `src/pwd301/services/video_drm_service.py`
- Modify: `src/pwd301/services/background_job_service.py`
- Modify: `src/pwd301/blueprints/student/routes.py`
- Modify: `src/pwd301/services/file_service.py`
- Test: `tests/unit/test_video_drm_service.py` (New test file)
- Test: `tests/api/test_video_drm_api.py` (New test file)

**Interfaces:**
- `video_drm_service.transcode_to_encrypted_hls(input_path, output_dir, key_uri)`: Sử dụng FFmpeg cắt video thành các chunk `.ts` 4s, mã hóa AES-128.
- `video_drm_service.generate_short_lived_key_token(student_user_id, lesson_id)`: Tạo HMAC token có hạn 60s cho key request.
- `video_drm_service.verify_key_token(token, student_user_id, lesson_id)`: Xác thực token hợp lệ.
- Route `/student/courses/<course_id>/lessons/<lesson_id>/video/playlist.m3u8`: Phục vụ manifest phân đoạn.
- Route `/student/courses/<course_id>/lessons/<lesson_id>/video/key`: Phục vụ khóa AES-128 với token hợp lệ.
- Route `/student/courses/<course_id>/lessons/<lesson_id>/video/segments/<segment_name>`: Phục vụ chunk mã hóa `.ts`.

- [ ] **Step 1: Viết test fail `tests/unit/test_video_drm_service.py` & `tests/api/test_video_drm_api.py`**
  - Test tạo và xác thực short-lived key token: token hết hạn sau 60s hoặc sai user/lesson bị từ chối.
  - Test route lấy key: sinh viên chưa ghi danh hoặc thiếu token bị `403 Forbidden`; sinh viên hợp lệ nhận đúng 16-byte AES key kèm header `Cache-Control: private, no-store`.
  - Test khóa tải file thô: sinh viên gọi download file bài học dạng video với `disposition=inline` hoặc `attachment` bị từ chối tải trực tiếp tệp gốc (chuyển hướng sang luồng HLS).
- [ ] **Step 2: Chạy test để đảm bảo test fail**
  ```bash
  pytest tests/unit/test_video_drm_service.py tests/api/test_video_drm_api.py
  ```
- [ ] **Step 3: Hiện thực hóa `video_drm_service.py` và các API endpoints**
  - Xây dựng logic chuyển mã HLS mã hóa AES-128 sử dụng `ffmpeg.exe`.
  - Cung cấp cơ chế sinh khóa ngẫu nhiên và mã hóa phân đoạn.
  - Đăng ký các endpoints phục vụ playlist, key và segments trong `blueprints/student/routes.py`.
  - Tích hợp cấm tải tệp video thô vào `file_service.py` và route download file của học viên.
  - Thêm worker job handler `VIDEO_TRANSCODE` trong `background_job_service.py`.
- [ ] **Step 4: Chạy lại test suite để đảm bảo test pass**
  ```bash
  pytest tests/unit/test_video_drm_service.py tests/api/test_video_drm_api.py
  ```
- [ ] **Step 5: Commit**
  ```bash
  git add src/pwd301/services/video_drm_service.py src/pwd301/services/background_job_service.py src/pwd301/blueprints/student/routes.py tests/
  git commit -m "feat(drm): implement encrypted HLS AES-128 transcoding pipeline and tokenized key distribution"
  ```

---

### Task 3: Phát Triển Dynamic Forensic Watermark & Client Armor (Chống Can Thiệp DOM & DevTools)

**Files:**
- Create: `frontend/assets/js/components/video-armor.js`
- Test: `tests/frontend/video_armor.test.js` (New test file)

**Interfaces:**
- `VideoArmor.mount(containerElement, options)`:
  - `options.user`: `{ studentId, fullName, email }`
  - `options.onSecurityViolation(violationType)`: Callback gửi cảnh báo về máy chủ khi phát hiện can thiệp DOM hoặc DevTools.
  - `options.isExternalEmbed`: boolean (áp dụng cho iframe YouTube/Vimeo).
- Quản lý 4 lớp phòng thủ: Dynamic Watermark, MutationObserver, DevTools Bouncer, Visibility/Blur Tracker.

- [ ] **Step 1: Viết test fail `tests/frontend/video_armor.test.js`**
  - Test hiển thị đầy đủ thông tin học viên trên phần tử Watermark.
  - Test trôi ngẫu nhiên tọa độ (drift animation / position change) theo chu kỳ.
  - Test `MutationObserver`: Giả lập xóa node Watermark hoặc sửa CSS `display: none` -> Hệ thống tự động tái tạo node và kích hoạt callback vi phạm bảo mật.
  - Test bẫy phím tắt: Chặn phím `PrintScreen`, xóa clipboard.
- [ ] **Step 2: Chạy test để đảm bảo test fail**
  ```bash
  node --test tests/frontend/video_armor.test.js
  ```
- [ ] **Step 3: Hiện thực hóa mô-đun `frontend/assets/js/components/video-armor.js`**
  - Cài đặt lớp phủ Watermark động với font chữ thanh mảnh, độ mờ dịu (`opacity: 0.18`), trôi nổi ngẫu nhiên 4 góc và trung tâm.
  - Cài đặt `MutationObserver` gắn chặt vào container: giám sát thay đổi subtree, attributes và node removals; tự động khôi phục cấu trúc DOM và kích hoạt màn hình đen (Blackout) nếu phát hiện can thiệp bất hợp pháp.
  - Cài đặt DevTools Bouncer: bẫy `debugger` timing định kỳ để phát hiện Developer Tools được mở; kích hoạt Blackout và thông báo học viên đóng công cụ kiểm tra.
  - Cài đặt bẫy `visibilitychange` và `window.blur`: tự động pause video khi học viên rời tab/chuyển cửa sổ.
- [ ] **Step 4: Chạy lại test suite để đảm bảo test pass**
  ```bash
  node --test tests/frontend/video_armor.test.js
  ```
- [ ] **Step 5: Commit**
  ```bash
  git add frontend/assets/js/components/video-armor.js tests/frontend/video_armor.test.js
  git commit -m "feat(frontend): implement VideoArmor with dynamic forensic watermark, DOM mutation observer and devtools bouncer"
  ```

---

### Task 4: Tích Hợp Hls.js & Khớp Nối VideoArmor Vào Trình Phát Bài Học Sinh Viên

**Files:**
- Modify: `frontend/assets/js/views/student.js`
- Modify: `frontend/assets/js/controllers.js`
- Test: `tests/frontend/student_video_playback.test.js` (New test file)

**Interfaces:**
- `StudentView._renderProtectedVideoPlayer(container, lesson, user)`: Tích hợp Hls.js cho video nội bộ và iframe cho YouTube, đồng thời mount `VideoArmor` lên trên.
- Đồng bộ chu kỳ nhịp tim định kỳ 10-15s gửi về endpoint `/api/lessons/<id>/progress`.

- [ ] **Step 1: Viết test fail `tests/frontend/student_video_playback.test.js`**
  - Test render video nội bộ: Gọi API HLS manifest thay vì gán trực tiếp URL MP4 thô.
  - Test render video YouTube: Bọc iframe trong `VideoArmor` với Dynamic Watermark.
  - Test gửi nhịp tim định kỳ kèm token chống replay và kiểm tra tiến độ xem thực tế.
- [ ] **Step 2: Chạy test để đảm bảo test fail**
  ```bash
  node --test tests/frontend/student_video_playback.test.js
  ```
- [ ] **Step 3: Cập nhật `student.js` và `controllers.js`**
  - Nhập và tích hợp `VideoArmor` vào giao diện học tập của sinh viên (`renderCourseConsole` và các view bài học).
  - Tích hợp Hls.js để phát luồng HLS mã hóa, tự động kèm short-lived token trong header hoặc query param khi fetch key/segment.
  - Thay thế hoàn toàn cách hiển thị `<video src="...">` cũ bằng trình phát bảo mật mới.
  - Kết nối callback vi phạm bảo mật của `VideoArmor` với endpoint ghi nhận sự kiện `AuditEvent` trên backend.
- [ ] **Step 4: Chạy lại test suite để đảm bảo test pass**
  ```bash
  node --test tests/frontend/student_video_playback.test.js
  ```
- [ ] **Step 5: Commit**
  ```bash
  git add frontend/assets/js/views/student.js frontend/assets/js/controllers.js tests/frontend/
  git commit -m "feat(student): wire encrypted Hls player with VideoArmor and resilient heartbeat synchronization"
  ```

---

### Task 5: Tích Hợp Toàn Diện, Kiểm Thử Phòng Ngự & Báo Cáo Xác Minh Thực Nghiệm

**Files:**
- Test: `tests/api/test_copyright_defense_e2e.py` (New end-to-end security test)
- Modify: `scripts/verify.ps1` (nếu cần bổ sung test files mới)

**Interfaces:**
- Chạy toàn bộ quy trình kiểm thử từ backend đến frontend, mô phỏng các đòn tấn công thực tế:
  1. Thử tải file MP4 thô -> Bị chặn fail-closed.
  2. Thử gọi API hoàn thành bài học không qua nhịp tim -> Bị từ chối.
  3. Thử lấy key giải mã trái phép -> Bị từ chối.
  4. Thử can thiệp DOM xóa watermark -> Bị phát hiện và khôi phục.
- Chạy xác minh thực tế bằng script PowerShell kiểm thử toàn bộ hệ thống.

- [ ] **Step 1: Viết bộ test E2E `tests/api/test_copyright_defense_e2e.py`**
  Mô phỏng toàn bộ hành trình của học viên: ghi danh -> học bài -> kiểm tra DRM key -> gửi nhịp tim -> phòng ngừa gian lận -> ghi nhận sự kiện bảo mật -> hoàn thành bài học khi đạt đủ điều kiện.
- [ ] **Step 2: Chạy kiểm thử E2E**
  ```bash
  pytest tests/api/test_copyright_defense_e2e.py
  ```
- [ ] **Step 3: Chạy toàn bộ verify script của dự án**
  ```powershell
  ./scripts/verify.ps1
  ```
  Xác minh 100% test suites pass, không có regression ở bất kỳ phân hệ nào.
- [ ] **Step 4: Commit hoàn tất**
  ```bash
  git add tests/ scripts/
  git commit -m "test(security): add comprehensive end-to-end copyright protection and anti-tamper test suite"
  ```
