# KỊCH BẢN PHIM GIỚI THIỆU SẢN PHẨM PWD301 LMS (VIDEO STORYBOARD)
**Tác phẩm:** PWD301 LMS Launch Film — "Learning Reimagined"  
**Tổng thời lượng:** 70.0 giây (Chuẩn Master 60–75s)  
**Tốc độ nhịp:** 129 BPM (1 beat = 0.465s, 1 bar = 1.86s, 1/2 beat = 0.232s)  
**Độ phân giải:** 1920 × 1080 @ 60fps  
**Phong cách nghệ thuật:** Apple Product Film + Modern SaaS Launch + Technical Motion Graphics  
**Bảo đảm tính xác thực:** 100% màn hình, route và tính năng đến từ mã nguồn thực tế của dự án.  

---

## BẢNG PHÂN CẢNH TỔNG THỂ (MASTER SCENE BREAKDOWN)

```
00.0s       04.5s       10.0s       15.5s       21.5s       28.5s       35.5s       42.5s       49.5s       56.5s       62.5s       65.5s    70.0s
|--- SC-01 ---|--- SC-02 ---|--- SC-03 ---|--- SC-04 ---|--- SC-05 ---|--- SC-06 ---|--- SC-07 ---|--- SC-08 ---|--- SC-09 ---|--- SC-10 ---|--SC-11--|--- SC-12 ---|
    INTRO       STUDENT      CATALOG      LESSON       EXAMS        AI TUTOR    INSTRUCTOR    MATRIX       ADMIN      TELEMETRY    3D ORBIT      OUTRO
```

---

## CHI TIẾT 12 PHÂN CẢNH CHUẨN XÁC

### PHÂN CẢNH 01: INTRO HOOK & CỔNG KHỞI TẠO (00.0s – 04.5s)
- **Thời lượng:** 4.5 giây
- **Màu sắc sân khấu:** Dark Obsidian Slate (`#141414` $\rightarrow$ `#1E293B`)
- **Vai trò:** Hệ thống / Nhận diện thương hiệu
- **Route thực tế:** `#/auth` (Cổng đăng nhập Warm Editorial)
- **Hero Object:** Khối trụ Kinetic 3D Typography xoay tròn quanh trục Y với chữ kim loại phản chiếu và viền neon lime; chuyển tiếp mượt mà vào Thẻ đăng nhập Warm Editorial của PWD301.
- **Tương tác UI:** Form đăng nhập tự động hiển thị, 4 tiêu chí kiểm tra mật khẩu (Password checklist) sáng xanh ngọc, nhãn chuyển đổi vai trò nhanh.
- **Camera & Chuyển động:** Camera orbit từ góc thấp đẩy thẳng vào tâm (Z-push) với gia tốc `expo.out`, khung hình HUD 4 góc `[ ]` khóa chặt bố cục.
- **Typography:**
  - Dòng chính: `LEARNING REIMAGINED.` (Heavy Sans 96px)
  - Dòng phụ: `One Platform. Everything.` (Serif Italic 36px)
  - Micro-metadata: `SECURE · FAST · INTUITIVE`
- **Thiết kế âm thanh:** Reverse whoosh tăng dần tần số cao $\rightarrow$ Cú giáng Sub-bass impact cực mạnh tại `01.5s` $\rightarrow$ Digital glitch riser chuyển cảnh tại `03.8s`.
- **Chuyển cảnh:** Hard cut trên nhịp Downbeat sang màu xanh hoàng gia.

---

### PHÂN CẢNH 02: TỔNG QUAN SINH VIÊN — STUDENT COMMAND CENTER (04.5s – 10.0s)
- **Thời lượng:** 5.5 giây
- **Màu sắc sân khấu:** Royal Blue (`#1E3A8A` $\rightarrow$ `#2563EB`)
- **Vai trò:** Sinh viên (STUDENT)
- **Route thực tế:** `#/student/dashboard`
- **Hero Object:** Cửa sổ giao diện Dashboard thật của PWD301 lơ lửng trong không gian 3D (`rotateY(-8deg) rotateX(4deg)`).
- **Tương tác UI:** Thẻ "Tiếp tục học" khóa học `CS101` sáng nhẹ, thanh tiến độ 75% nạp đầy; 3 thẻ chỉ số KPI (Khóa học đang học: 3, Hoàn thành: 2, Chuỗi học tập: 14 ngày) nhảy số liên tục theo beat; huy hiệu bài thi sắp diễn ra nhấp nháy thu hút sự chú ý.
- **Camera & Chuyển động:** Camera từ góc rộng perspective trôi chậm về phía trước, zoom nhẹ làm nổi bật thẻ khóa học trọng tâm.
- **Typography:**
  - Dòng chính: `STUDENT` (Heavy Sans Bold 84px)
  - Dòng phụ: `Command Center` (Electric Lime Sans 48px)
  - Micro-metadata: `01 // 05 · METRICS · COURSES · EXAMS`
- **Thiết kế âm thanh:** Bass hit khi vào cảnh, tiếng click số đếm tăng dần, whoosh quét không gian khi camera tiến gần.
- **Chuyển cảnh:** Trượt đẩy ngang (Lateral Slide Push) theo phách mạnh sang phải.

---

### PHÂN CẢNH 03: KHÁM PHÁ & TÌM KIẾM KHÓA HỌC — DISCOVER COURSES (10.0s – 15.5s)
- **Thời lượng:** 5.5 giây
- **Màu sắc sân khấu:** Pure Warm Canvas (`#FAF9F5` với khung sân khấu Indigo `#1E1B4B`)
- **Vai trò:** Sinh viên (STUDENT)
- **Route thực tế:** `#/student/catalog`
- **Hero Object:** Khung danh mục khóa học với thanh tìm kiếm thông minh và lưới card khóa học thực tế (`CS101`, `CS201`, `CS301`).
- **Tương tác UI:** Con trỏ chuột mô phỏng (Simulated SVG Cursor) lướt vào ô tìm kiếm, click tạo hiệu ứng gợn sóng (ripple ping); gõ nhanh "Python"; lưới khóa học lọc tức thì và làm nổi bật khóa `CS101 - Lập Trình Web Cơ Bản Với Python & Flask` kèm nhãn "ĐÃ GHI DANH".
- **Camera & Chuyển động:** Camera góc nhìn từ trên nghiêng nhẹ (`rotateX(8deg)`), phóng đại (macro zoom) vào thanh tìm kiếm rồi dạt sang card kết quả.
- **Typography:**
  - Dòng chính: `DISCOVER` (Heavy Sans 84px)
  - Dòng phụ: `Instant Search` (Editorial Script Italic 44px)
  - Micro-metadata: `REALTIME · FILTER · CATALOG`
- **Thiết kế âm thanh:** Click chuột tinh tế, tiếng gõ phím cơ học vi mô, tiếng kick bass trầm khi card khóa học được highlight.
- **Chuyển cảnh:** Zoom dive lao thẳng vào hình bìa khóa học CS101.

---

### PHÂN CẢNH 04: TRẢI NGHIỆM HỌC TẬP CHUYÊN SÂU — DEEP LEARNING (15.5s – 21.5s)
- **Thời lượng:** 6.0 giây
- **Màu sắc sân khấu:** Warm Emerald (`#064E3B` $\rightarrow$ `#059669`)
- **Vai trò:** Sinh viên (STUDENT)
- **Route thực tế:** `#/student/courses/detail` $\rightarrow$ `#/student/courses/1/lessons/1`
- **Hero Object:** Bàn điều khiển khóa học (Course Console) mở bung cây đề cương (Syllabus tree) và Trình đọc bài giảng không xao nhãng (Distraction-Free Reader).
- **Tương tác UI:** Cụm chương 1 bung mở với hiệu ứng easing mềm mại; mở bài giảng "Tổng quan kiến trúc Flask"; khối mã nguồn đen bóng với highlight cú pháp; khung video bài giảng nhúng sẵn; chuột bấm nút "Đánh dấu đã hoàn thành" $\rightarrow$ chuyển sang dấu tick xanh ngọc lục bảo.
- **Camera & Chuyển động:** Góc nhìn chính diện phẳng (Flat Focus) kết hợp hiệu ứng trượt cuộn thị sai (Parallax scroll) giữa thanh bên và nội dung đọc.
- **Typography:**
  - Dòng chính: `LEARN` (Heavy Sans 84px)
  - Dòng phụ: `Your Own Pace` (Warm Italic Serif 46px)
  - Micro-metadata: `MARKDOWN · CODE BLOCKS · ATTACHMENTS`
- **Thiết kế âm thanh:** Tiếng mở accordion êm dịu, tiếng lật trang kỹ thuật số, âm chuông hoàn thành (Completion chime).
- **Chuyển cảnh:** Quét nhanh Glitch sweep báo hiệu chuyển sang chế độ bài thi.

---

### PHÂN CẢNH 05: BÀI THI TẬP TRUNG & CHẤM ĐIỂM TỨC THÌ — SECURE ASSESSMENTS (21.5s – 28.5s)
- **Thời lượng:** 7.0 giây
- **Màu sắc sân khấu:** Deep Tech Navy (`#020617` $\rightarrow$ `#0F172A`)
- **Vai trò:** Sinh viên (STUDENT)
- **Route thực tế:** `#/student/assessments/waiting-room` $\rightarrow$ `#/student/assessments/attempt` $\rightarrow$ `#/student/assessments/results`
- **Hero Object:** Bàn thi tập trung Fullscreen Focus Mode với đồng hồ đếm ngược của máy chủ, bảng điều hướng 10 câu hỏi và phiếu điểm số 9.5/10.
- **Tương tác UI:** Đồng hồ đếm ngược nhấp nháy; bảng câu hỏi bên trái hiện số 1 đến 10; chuột chọn đáp án trắc nghiệm "B) Microframework nhẹ"; ô số 1 lập tức chuyển sang màu xanh ngọc xác nhận đã lưu (Autosave); nhấn nút "Nộp bài" $\rightarrow$ Bảng kết quả bung nở vòng tròn điểm số tăng tốc từ 0 lên 9.5 kèm huy hiệu "ĐẠT".
- **Camera & Chuyển động:** Cận cảnh kịch tính (Dramatic Macro) vào khối câu hỏi, camera kéo lùi ra xa khi điểm số 9.5 xuất hiện.
- **Typography:**
  - Dòng chính: `ASSESS` (Heavy Sans 84px)
  - Dòng phụ: `Server-Authoritative` (JetBrains Mono 40px)
  - Micro-metadata: `SINGLE ACTIVE LEASE · AUTOSAVE · INSTANT RESULTS`
- **Thiết kế âm thanh:** Nhịp đập căng thẳng của đồng hồ, tiếng click cơ học đanh gọn khi chọn đáp án, tiếng sub-impact chấn động khi nộp bài, hợp âm hân hoan khi điểm số bừng sáng.
- **Chuyển cảnh:** Đổi màu nền cực mạnh từ Navy sang Tím vũ trụ huyền ảo.

---

### PHÂN CẢNH 06: TRỢ LÝ HỌC TẬP THÔNG MINH — BẠCH TUỘC AI (28.5s – 35.5s)
- **Thời lượng:** 7.0 giây
- **Màu sắc sân khấu:** Cosmic Violet / Galactic Purple (`#1E1B4B` $\rightarrow$ `#3B0764`)
- **Vai trò:** Sinh viên / Trợ lý AI
- **Route thực tế:** `#/student/ai-assistant` & Floating AI Tutor
- **Hero Object:** Biểu tượng Bạch tuộc AI phát quang tím; Khung hội thoại AI thông minh; Quả cầu hạt 3D Particle Cloud xoay tít bên phải khung hình.
- **Tương tác UI:** Bong bóng AI mở ra; ô nhập Prompt tự động gõ: "Giải thích cơ chế Session trong Flask?"; Bạch tuộc trợ lí AI phản hồi dạng văn bản streaming mượt mà, phân tích trích dẫn chuẩn xác từ giáo trình khóa học CS101.
- **Camera & Chuyển động:** Camera dạt từ phải sang trái; quả cầu hạt 3D xoay đa chiều tạo độ sâu trường ảnh (Depth of Field).
- **Typography:**
  - Dòng chính: `ASK AI` (Heavy Sans 84px)
  - Dòng phụ: `Bạch Tuộc Trợ Lí AI` (Neon Purple Script 48px)
  - Micro-metadata: `COURSE-GROUNDED RAG · CONTEXT AWARE`
- **Thiết kế âm thanh:** Tiếng năng lượng tương lai dâng trào (Digital energy riser), âm thanh hạt lấp lánh (Particle shimmer), tiếng gõ ký tự streaming, tiếng bass êm dịu khi câu trả lời hoàn tất.
- **Chuyển cảnh:** Flash swipe cực nhanh chuyển sang phân hệ Giảng viên.

---

### PHÂN CẢNH 07: BÀN LÀM VIỆC GIẢNG VIÊN — INSTRUCTOR STUDIO (35.5s – 42.5s)
- **Thời lượng:** 7.0 giây
- **Màu sắc sân khấu:** Crimson Coral Red (`#991B1B` $\rightarrow$ `#DC2626`)
- **Vai trò:** Giảng viên (INSTRUCTOR)
- **Route thực tế:** `#/instructor/dashboard` & `#/instructor/courses/manage` & `#/instructor/courses/1/lessons/new`
- **Hero Object:** Bảng điều khiển giảng viên với 4 thẻ chỉ số và Trình biên soạn đề cương khóa học dạng cây (Curriculum Builder).
- **Tương tác UI:** 4 thẻ chỉ số (2 Khóa học, 48 Sinh viên, 1 Bài thi, 3 Bài chờ chấm) nhảy số; thao tác kéo thả tay cầm (drag handle) sắp xếp lại vị trí bài giảng mượt mà; tải lên tài liệu đính kèm với nhãn kiểm tra virus an toàn.
- **Camera & Chuyển động:** Góc nghiêng 3D isometric (`rotateY(10deg) rotateX(6deg)`), camera lia ngang qua các nhánh chương mục.
- **Typography:**
  - Dòng chính: `TEACH` (Heavy Sans 84px)
  - Dòng phụ: `Curriculum Studio` (Warm Amber Script 46px)
  - Micro-metadata: `STRUCTURE · REORDER · VIRUS-SCANNED MEDIA`
- **Thiết kế âm thanh:** Tiếng bass punch đanh thép, tiếng kéo thả vật lý (Drag sound), tiếng xác nhận tải tệp thành công.
- **Chuyển cảnh:** Cắt nhanh vào trung tâm khảo thí.

---

### PHÂN CẢNH 08: XƯỞNG KHẢO THÍ & MA TRẬN ĐỀ THI — EXAM MATRIX (42.5s – 49.5s)
- **Thời lượng:** 7.0 giây
- **Màu sắc sân khấu:** Cyber Neon Lime (`#365314` $\rightarrow$ `#65A30D`)
- **Vai trò:** Giảng viên (INSTRUCTOR)
- **Route thực tế:** `#/instructor/exams/hub` & `#/instructor/exams/matrix`
- **Hero Object:** Trung tâm khảo thí với 4 phương thức tạo đề và Lưới ma trận độ khó Bloom (Nhận biết, Thông hiểu, Vận dụng).
- **Tương tác UI:** 4 thẻ tạo đề (Thủ công, Tương tác AI, Nhập Excel, Nhập Moodle XML) xuất hiện so le; chuyển vào Ma trận đề thi; thanh trượt tỉ lệ câu hỏi được điều chỉnh, tổng điểm tự động cân bằng 100% trong nháy mắt.
- **Camera & Chuyển động:** Macro zoom cận cảnh vào các ô ma trận Bloom, quét góc máy từ trái sang phải làm nổi bật sự chính xác khoa học.
- **Typography:**
  - Dòng chính: `CREATE` (Heavy Sans 84px)
  - Dòng phụ: `Exam Matrix` (Cyber Lime 48px)
  - Micro-metadata: `BLOOM TAXONOMY · 4 INGESTION METHODS`
- **Thiết kế âm thanh:** Loạt tiếng click kỹ thuật số theo nhịp phách, tiếng whoosh chuyển từ Hub sang Matrix, tiếng gõ kim loại khi tổng điểm chạm 100%.
- **Chuyển cảnh:** Trượt dọc xuống phân hệ Quản trị viên.

---

### PHÂN CẢNH 09: THẨM ĐỊNH & QUẢN TRỊ HỌC VỤ — GOVERNANCE (49.5s – 56.5s)
- **Thời lượng:** 7.0 giây
- **Màu sắc sân khấu:** Deep Slate Charcoal (`#0F172A` $\rightarrow$ `#1E293B`)
- **Vai trò:** Quản trị viên (ADMIN)
- **Route thực tế:** `#/admin/governance?tab=users` & `#/admin/courses/review`
- **Hero Object:** Bảng dữ liệu quản trị tài khoản đa vai trò và Cổng thẩm định khóa học chờ duyệt (`CS301`).
- **Tương tác UI:** Bảng danh sách người dùng lọc tức thì theo vai trò "GIẢNG VIÊN"; chuyển sang Trang thẩm định khóa học `CS301`; Admin kiểm tra đề cương và nhấn nút "Phê duyệt" (Approve) $\rightarrow$ Thông báo thành công xanh ngọc và trạng thái khóa học lập tức chuyển thành `PUBLISHED`.
- **Camera & Chuyển động:** Góc nhìn chính diện phẳng trang trọng, vững chãi, thể hiện sự kiểm soát toàn diện và tính bảo mật nghiêm ngặt.
- **Typography:**
  - Dòng chính: `CONTROL` (Heavy Sans 84px)
  - Dòng phụ: `Total Governance` (Warm Silver Italic 46px)
  - Micro-metadata: `USER ACCESS · ROLE ASSIGNMENT · COURSE APPROVAL`
- **Thiết kế âm thanh:** Tiếng gõ trầm uy quyền, tiếng lia mượt của bảng dữ liệu, tiếng click cơ học chắc chắn khi phê duyệt, âm thanh thành công.
- **Chuyển cảnh:** Chuyển động trượt vào trung tâm đo lường phần cứng.

---

### PHÂN CẢNH 10: VẬN HÀNH & ĐO LƯỜNG THỰC TẾ — AUTHENTIC TELEMETRY (56.5s – 62.5s)
- **Thời lượng:** 6.0 giây
- **Màu sắc sân khấu:** High-Tech Cyan Obsidian (`#022C22` $\rightarrow$ `#064E3B`)
- **Vai trò:** Quản trị viên (ADMIN)
- **Route thực tế:** `#/admin/operations`
- **Hero Object:** Bảng điều khiển vận hành với các biểu đồ chỉ số phần cứng thực tế trích xuất từ `psutil` (CPU, RAM, Ổ cứng, Nhật ký cách ly tệp ClamAV).
- **Tương tác UI:** Đường biểu đồ CPU vẽ sóng thời gian thực; đồng hồ đo RAM chuyển động kim đo đúng thông số máy chủ thật; nhật ký kiểm tra bảo mật tệp tin trượt xuống cho thấy 100% tệp độc hại bị cách ly an toàn.
- **Camera & Chuyển động:** Góc nhìn HUD cong 3D (`rotateY(-6deg)`), nền lưới tọa độ phát sáng nhẹ.
- **Typography:**
  - Dòng chính: `INSIGHTS` (Heavy Sans 84px)
  - Dòng phụ: `Authentic Telemetry` (JetBrains Mono Cyan 42px)
  - Micro-metadata: `AUTHENTIC PSUTIL TELEMETRY · FAIL-CLOSED SECURITY`
- **Thiết kế âm thanh:** Tiếng rung máy tính số hóa (Digital server hum), tiếng quét telemetry tần số cao, tiếng bass đánh theo đỉnh sóng biểu đồ.
- **Chuyển cảnh:** Thu nhỏ toàn bộ các màn hình về không gian 3D đa chiều.

---

### PHÂN CẢNH 11: HỆ SINH THÁI ĐA CHIỀU — 3D ECOSYSTEM ORBIT (62.5s – 65.5s)
- **Thời lượng:** 3.0 giây
- **Màu sắc sân khấu:** Chuyển động đa sắc chớp nhoáng (Blue $\rightarrow$ Green $\rightarrow$ Purple $\rightarrow$ Crimson $\rightarrow$ Slate)
- **Vai trò:** Toàn bộ hệ sinh thái (Student, Instructor, Admin, AI)
- **Route thực tế:** Lắp ghép 6 màn hình đại diện (Dashboard, Attempt, Lesson, AI, Matrix, Operations)
- **Hero Object:** 6 cửa sổ màn hình thật xếp thành khối trụ 3D xoay vòng quanh tâm camera với độ phản chiếu bóng sàn chân thực.
- **Tương tác UI:** Các màn hình xoay tròn với tốc độ cao, hiển thị trọn vẹn sức mạnh liên hoàn của hệ thống.
- **Camera & Chuyển động:** Camera orbit tốc độ cao kéo lùi dần, mở rộng góc nhìn toàn cảnh vũ trụ LMS.
- **Typography:**
  - Dòng chính: `ONE PLATFORM.` (Heavy Bold 96px)
  - Dòng phụ: `All In One Ecosystem.` (Serif Italic 48px)
- **Thiết kế âm thanh:** 4 nhịp staccato kick liên hoàn dồn dập (`62.5s`, `63.2s`, `64.0s`, `64.8s`) tạo đà năng lượng đỉnh điểm.
- **Chuyển cảnh:** Toàn bộ các màn hình 3D co rút cực nhanh về tâm thành Logo PWD301.

---

### PHÂN CẢNH 12: ĐẠI KẾT THƯƠNG HIỆU — MASTER BRAND OUTRO (65.5s – 70.0s)
- **Thời lượng:** 4.5 giây
- **Màu sắc sân khấu:** Dark Elegant Obsidian (`#121212`)
- **Vai trò:** Nhận diện thương hiệu cốt lõi
- **Hero Object:** Logo PWD301 LMS nổi khối kim loại với biểu tượng Bạch tuộc AI; vạch kẻ vàng tươi; dòng chữ URL terminal tự động gõ.
- **Tương tác UI:** Thanh gạch vàng chạy từ trái sang phải; các nút pill danh mục (Khóa học, Khảo thí, Giảng dạy, Bạch tuộc AI) hiện lên; dòng chữ URL gõ từng ký tự: `— pwd301.local/` kèm con trỏ nhấp nháy `_`; các hạt bụi ánh sao trôi nhẹ trong bóng đêm.
- **Camera & Chuyển động:** Camera lùi dần rất chậm và vững chãi, căn giữa hoàn hảo.
- **Typography:**
  - Tiêu đề thương hiệu: `PWD301 LMS` (Heavy Bold 100px)
  - Vạch nhấn vàng: `border-b-4 border-yellow-400`
  - Slogan: `Nền Tảng Học Tập & Khảo Thí Thế Hệ Mới` (Warm Serif Italic 40px)
  - Tagline vòm: `TEACH · LEARN · GROW`
- **Thiết kế âm thanh:** Cú giáng Sub-bass impact rung chuyển tại `65.8s`, hợp âm ngân vang sâu thẳm kéo dài cho đến khi fade out sang đen ở `70.0s`.
- **Chuyển cảnh:** Fade to Black kết thúc hoàn hảo bộ phim.

---

## TỔNG KẾT BẢNG MÀU SÂN KHẤU (COLOR WORLDS SYNC)
| Phân cảnh | Tên màn hình | Màu chủ đạo sân khấu | Ý nghĩa ngữ cảnh |
| :---: | :--- | :--- | :--- |
| **01** | Intro Hook | Charcoal Obsidian `#141414` | Cánh cổng bí ẩn, công nghệ cao |
| **02** | Student Dashboard | Royal Blue `#1E3A8A` / `#2563EB` | Khởi đầu học tập, năng lượng tích cực |
| **03** | Course Catalog | Pure Warm `#FAF9F5` / Indigo `#1E1B4B` | Sự tinh tế, tối giản Warm Editorial |
| **04** | Lesson Reader | Warm Emerald `#064E3B` / `#059669` | Tập trung sâu, đọc hiểu tri thức |
| **05** | Attempt Console | Tech Navy `#020617` / `#0F172A` | Khảo thí bảo mật, tập trung cao độ |
| **06** | Bạch tuộc AI | Cosmic Purple `#1E1B4B` / `#3B0764` | Trí tuệ nhân tạo, tương lai số |
| **07** | Instructor Studio | Crimson Coral `#991B1B` / `#DC2626` | Nhiệt huyết giảng dạy, sáng tạo |
| **08** | Exam Matrix | Cyber Lime `#365314` / `#65A30D` | Chính xác, khoa học giáo dục Bloom |
| **09** | Admin Governance | Slate Charcoal `#0F172A` / `#1E293B` | Thẩm quyền, an toàn và bảo mật |
| **10** | Authentic Telemetry | High-Tech Cyan `#022C22` / `#064E3B` | Giám sát máy chủ thực tế |
| **11** | 3D Orbit | Multi-spectrum Pulse | Hội tụ hệ sinh thái toàn diện |
| **12** | Brand Outro | Obsidian Dark `#121212` | Đẳng cấp cao cấp, bền vững |
