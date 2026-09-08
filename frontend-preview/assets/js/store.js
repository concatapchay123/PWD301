/**
 * PWD301 — Online Course Management Platform
 * Central Mock Store & Reactive State Engine
 * Strictly client-side mock data; No real secrets; Zero backend dependency.
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};

  const STORAGE_KEY = 'pwd301_demo_store_v2';
  const PERSPECTIVE_KEY = 'pwd301_demo_perspective';

  function getInitialSeedData() {
    return {
      currentPerspective: 'student', // 'public', 'student', 'instructor', 'admin'
      
      personas: {
        student: { id: 'u_student', name: 'Nguyễn Minh Anh', email: 'student@demo.local', role: 'STUDENT', avatar: 'MA' },
        instructor: { id: 'u_instructor', name: 'Trần Hoàng Nam', email: 'instructor@demo.local', role: 'INSTRUCTOR', avatar: 'HN' },
        admin: { id: 'u_admin', name: 'Lê Thu Hà', email: 'admin@demo.local', role: 'ADMIN', avatar: 'TH' }
      },

      courses: [
        {
          id: 'c1',
          code: 'PWD301',
          title: 'Lập trình Web với Python & Flask',
          instructorId: 'u_instructor',
          instructorName: 'Trần Hoàng Nam',
          category: 'Phát triển Web',
          status: 'published', // 'published', 'draft', 'pending_approval', 'archived'
          capacity: 60,
          enrolledCount: 38,
          prerequisites: [],
          description: 'Khóa học cốt lõi về kiến trúc ứng dụng web, templating Jinja2, CSRF protection, SQLAlchemy ORM và xác thực phân quyền người dùng.',
          completionRule: 'Hoàn thành 100% bài học và đạt tối thiểu 6.0 điểm kiểm tra giữa kỳ.',
          lessonsCount: 6,
          enrolled: true,
          progress: 50, // student progress percent
          materialApprovalRequired: false,
          fptPattern: 'emerald-grid',
          fptBadgeColor: '#ff4d00',
          rating: 4.8,
          ratingCount: '18.420 xếp hạng',
          bestseller: true,
          isPremium: true,
          price: '249.000 đ',
          originalPrice: '1.580.000 đ',
          totalDuration: '33,5 giờ',
          studentsCount: '16.538',
          wishlisted: false,
          thumbGradient: 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%)',
          iconName: 'code'
        },
        {
          id: 'c2',
          code: 'FED102',
          title: 'HTML5, CSS3 & Thiết kế Giao diện Web Hiện đại',
          instructorId: 'u_instructor',
          instructorName: 'Trần Hoàng Nam',
          category: 'Frontend',
          status: 'published',
          capacity: 80,
          enrolledCount: 72,
          prerequisites: [],
          description: 'Nắm vững Semantic HTML, Flexbox, CSS Grid, Responsive Design và Design Systems chuẩn mực không dùng framework cồng kềnh.',
          completionRule: 'Hoàn thành tất cả bài thực hành CSS.',
          lessonsCount: 8,
          enrolled: true,
          progress: 100, // completed
          completedAt: '2026-08-15',
          fptPattern: 'blue-rings',
          fptBadgeColor: '#ea580c',
          rating: 4.9,
          ratingCount: '32.150 xếp hạng',
          bestseller: true,
          isPremium: true,
          price: '259.000 đ',
          originalPrice: '1.620.000 đ',
          totalDuration: '42,0 giờ',
          studentsCount: '38.200',
          wishlisted: true,
          thumbGradient: 'linear-gradient(135deg, #ea580c 0%, #f97316 50%, #fbbf24 100%)',
          iconName: 'layout'
        },
        {
          id: 'c3',
          code: 'DBA201',
          title: 'Cơ sở dữ liệu Nâng cao & Tối ưu hóa SQL',
          instructorId: 'u_teacher2',
          instructorName: 'Vũ Đức Thịnh',
          category: 'Dữ liệu',
          status: 'published',
          capacity: 40,
          enrolledCount: 15,
          prerequisites: ['c1'], // Requires c1 to be completed first!
          description: 'Thiết kế lược đồ quan hệ chuẩn hóa, phân vùng bảng, đánh chỉ mục B-Tree và phân tích query execution plan tối ưu.',
          completionRule: 'Hoàn thành bài tập thiết kế Schema và bài thi trắc nghiệm.',
          lessonsCount: 7,
          enrolled: false,
          progress: 0,
          fptPattern: 'grey-tartan',
          fptBadgeColor: '#d97706',
          rating: 4.7,
          ratingCount: '9.430 xếp hạng',
          bestseller: false,
          isPremium: true,
          price: '249.000 đ',
          originalPrice: '1.060.000 đ',
          totalDuration: '28,5 giờ',
          studentsCount: '9.850',
          wishlisted: false,
          thumbGradient: 'linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #2dd4bf 100%)',
          iconName: 'database'
        },
        {
          id: 'c4',
          code: 'ARC302',
          title: 'Kiến trúc Microservices & Docker Thực chiến',
          instructorId: 'u_instructor',
          instructorName: 'Trần Hoàng Nam',
          category: 'Hệ thống',
          status: 'draft',
          capacity: 45,
          enrolledCount: 0,
          prerequisites: ['c1'],
          description: 'Đóng gói ứng dụng với Docker, thiết kế Service Mesh, Event-driven communication và xử lý giao dịch phân tán Saga pattern.',
          completionRule: 'Triển khai thành công cụm 3 microservices qua docker-compose.',
          lessonsCount: 5,
          enrolled: false,
          progress: 0,
          fptPattern: 'pink-polygon',
          fptBadgeColor: '#e11d48',
          rating: 4.6,
          ratingCount: '5.120 xếp hạng',
          bestseller: false,
          isPremium: true,
          price: '289.000 đ',
          originalPrice: '1.800.000 đ',
          totalDuration: '36,0 giờ',
          studentsCount: '5.400',
          wishlisted: false,
          thumbGradient: 'linear-gradient(135deg, #db2777 0%, #ec4899 50%, #f472b6 100%)',
          iconName: 'server'
        },
        {
          id: 'c5',
          code: 'DSD401',
          title: 'Thiết kế Hệ thống Phân tán (Distributed Systems)',
          instructorId: 'u_instructor',
          instructorName: 'Trần Hoàng Nam',
          category: 'Hệ thống',
          status: 'pending_approval',
          capacity: 35,
          enrolledCount: 20,
          prerequisites: ['c1', 'c3'],
          description: 'Nghiên cứu định lý CAP, thuật toán đồng thuận Raft, cơ chế replication và distributed caching tốc độ cao.',
          completionRule: 'Đạt điểm tối thiểu 7.0 bài luận kết thúc môn.',
          lessonsCount: 6,
          enrolled: false,
          progress: 0,
          materialApprovalRequired: true,
          approvalNote: 'Giảng viên đã thay đổi 40% nội dung syllabus và cấu trúc điểm thi, đang chờ Admin phê duyệt.',
          fptPattern: 'green-mosaic',
          fptBadgeColor: '#059669',
          rating: 4.8,
          ratingCount: '8.650 xếp hạng',
          bestseller: false,
          isPremium: true,
          price: '269.000 đ',
          originalPrice: '1.750.000 đ',
          totalDuration: '31,0 giờ',
          studentsCount: '8.210',
          wishlisted: false,
          thumbGradient: 'linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%)',
          iconName: 'cpu'
        },
        {
          id: 'c6',
          code: 'SEC204',
          title: 'Lập trình RESTful API An toàn với JWT & OAuth2',
          instructorId: 'u_teacher3',
          instructorName: 'Ngô Hải Yến',
          category: 'Bảo mật',
          status: 'published',
          capacity: 50,
          enrolledCount: 50, // FULL CAPACITY!
          prerequisites: ['c1'],
          description: 'Phòng chống các lỗ hổng OWASP Top 10, quản lý phiên làm việc bảo mật, RBAC authorization và Rate Limiting.',
          completionRule: 'Vượt qua bài lab tấn công & phòng thủ API.',
          lessonsCount: 5,
          enrolled: false,
          progress: 0,
          fptPattern: 'slate-tartan',
          fptBadgeColor: '#dc2626',
          rating: 4.9,
          ratingCount: '14.280 xếp hạng',
          bestseller: true,
          isPremium: true,
          price: '279.000 đ',
          originalPrice: '1.490.000 đ',
          totalDuration: '26,0 giờ',
          studentsCount: '14.300',
          wishlisted: false,
          thumbGradient: 'linear-gradient(135deg, #7c3aed 0%, #8b5cf6 50%, #a78bfa 100%)',
          iconName: 'shield'
        },
        {
          id: 'c7',
          code: 'AIP305',
          title: 'Trí tuệ Nhân tạo Ứng dụng & RAG Pipeline',
          instructorId: 'u_teacher4',
          instructorName: 'Đặng Quốc Huy',
          category: 'AI / ML',
          status: 'published',
          capacity: 70,
          enrolledCount: 42,
          prerequisites: [],
          description: 'Xây dựng pipeline RAG với Vector Database, Semantic Search, Chunking strategies và tích hợp mô hình ngôn ngữ lớn.',
          completionRule: 'Hoàn thành dự án trợ lý tài liệu cá nhân.',
          lessonsCount: 6,
          enrolled: false,
          progress: 0,
          fptPattern: 'cyan-diamonds',
          fptBadgeColor: '#0284c7',
          rating: 4.9,
          ratingCount: '26.890 xếp hạng',
          bestseller: true,
          isPremium: true,
          price: '289.000 đ',
          originalPrice: '1.800.000 đ',
          totalDuration: '33,5 giờ',
          studentsCount: '27.400',
          wishlisted: false,
          thumbGradient: 'linear-gradient(135deg, #4338ca 0%, #6366f1 50%, #818cf8 100%)',
          iconName: 'sparkles'
        },
        {
          id: 'c8',
          code: 'CS101-2023',
          title: 'Lập trình Cơ sở C/C++ (Lưu trữ lịch sử 2023)',
          instructorId: 'u_instructor',
          instructorName: 'Trần Hoàng Nam',
          category: 'Cơ bản',
          status: 'archived',
          capacity: 100,
          enrolledCount: 95,
          prerequisites: [],
          description: 'Khóa học nhập môn lập trình niên khóa 2023 đã đóng. Chỉ xem lại được nội dung lịch sử; không truy xuất qua AI Assistant.',
          completionRule: 'Đã hoàn tất niên khóa.',
          lessonsCount: 10,
          enrolled: true,
          progress: 100,
          completedAt: '2023-12-20',
          fptPattern: 'blue-soft-rings',
          fptBadgeColor: '#64748b',
          rating: 4.5,
          ratingCount: '4.210 xếp hạng',
          bestseller: false,
          isPremium: true,
          price: '199.000 đ',
          originalPrice: '990.000 đ',
          totalDuration: '24,0 giờ',
          studentsCount: '4.200',
          wishlisted: false,
          thumbGradient: 'linear-gradient(135deg, #334155 0%, #475569 50%, #64748b 100%)',
          iconName: 'terminal'
        }
      ],

      lessons: [
        {
          id: 'les_1',
          courseId: 'c1',
          sectionId: 'sec_1',
          sectionTitle: 'Phần 1: Tổng quan Kiến trúc Web & HTTP',
          order: 1,
          type: 'video',
          title: '1. Chu trình Request - Response của giao thức HTTP/1.1 & HTTP/2',
          duration: '35 phút',
          viewed: true,
          completed: true,
          content: `
            <p>Chào mừng bạn đến với khóa học <strong>PWD301 — Lập trình Web với Python & Flask</strong>.</p>
            <p>Trong bài học này, chúng ta tìm hiểu chu trình Request-Response của giao thức HTTP, sự khác biệt giữa các phương thức GET, POST, PUT, DELETE, cách máy chủ xử lý HTTP Headers và cơ chế hoạt động của Cookie/Session.</p>
            <h3 class="section-title mt-4">1. Chu trình HTTP Request - Response</h3>
            <p>Khi trình duyệt gửi một truy vấn tới web server, gói tin HTTP mang theo URL, Method, Headers (như Host, User-Agent, Accept) và Body (nếu có payload POST). Server phản hồi với Status Code (200 OK, 302 Found, 400 Bad Request, 403 Forbidden, 500 Internal Error) cùng nội dung render tương ứng.</p>
            <h3 class="section-title mt-4">2. Nguyên tắc Stateless và Quản lý Phiên</h3>
            <p>HTTP là giao thức stateless. Để lưu giữ ngữ cảnh đăng nhập, hệ thống phát hành Session Cookie có thuộc tính <code>HttpOnly</code> và <code>SameSite=Lax</code> để ngăn chặn triệt để tấn công XSS và CSRF.</p>
          `,
          resources: [
            { id: 'res_1', title: 'Slide_Bai_1_HTTP_Architecture.pdf', size: '2.4 MB', type: 'pdf' },
            { id: 'res_2', title: 'Sample_HTTP_Raw_Requests.txt', size: '15 KB', type: 'text' }
          ]
        },
        {
          id: 'les_2',
          courseId: 'c1',
          sectionId: 'sec_1',
          sectionTitle: 'Phần 1: Tổng quan Kiến trúc Web & HTTP',
          order: 2,
          type: 'video',
          title: '2. Khởi tạo Ứng dụng Flask & Cấu hình Application Factory Pattern',
          duration: '45 phút',
          viewed: true,
          completed: true,
          content: `
            <p>Bài học này hướng dẫn cấu trúc một dự án Flask theo kiến trúc Application Factory và Modular Blueprints để dễ mở rộng và kiểm thử.</p>
            <h3 class="section-title mt-4">1. Application Factory Pattern</h3>
            <p>Thay vì khởi tạo đối tượng <code>app = Flask(__name__)</code> toàn cục, ta sử dụng hàm <code>create_app(config_name)</code> để tạo instance độc lập cho từng môi trường Development, Testing và Production.</p>
            <h3 class="section-title mt-4">2. Tổ chức Blueprints</h3>
            <p>Tách các phân hệ chức năng: <code>auth_bp</code>, <code>course_bp</code>, <code>assessment_bp</code>, <code>admin_bp</code> thành các module riêng biệt có routes và templates riêng.</p>
          `,
          resources: [
            { id: 'res_3', title: 'Flask_Blueprint_Boilerplate.zip', size: '140 KB', type: 'archive' }
          ]
        },
        {
          id: 'les_quiz1',
          courseId: 'c1',
          sectionId: 'sec_1',
          sectionTitle: 'Phần 1: Tổng quan Kiến trúc Web & HTTP',
          order: 3,
          type: 'quiz',
          title: '3. Quick Quiz: Kiểm tra Nhanh Kiến thức HTTP & Flask cơ bản',
          duration: '15 phút',
          viewed: true,
          completed: true,
          content: `<p>Bài trắc nghiệm ngắn 5 câu củng cố kiến thức về stateless HTTP, header xác thực và mẫu thiết kế Application Factory.</p>`,
          resources: []
        },
        {
          id: 'les_3',
          courseId: 'c1',
          sectionId: 'sec_2',
          sectionTitle: 'Phần 2: Template Jinja2 & Bảo mật Biểu mẫu CSRF',
          order: 4,
          type: 'video',
          title: '4. Jinja2 Templating Engine & Kế thừa Layout (Template Inheritance)',
          duration: '40 phút',
          viewed: true,
          completed: true,
          content: `
            <p>Jinja2 cho phép phân tách hoàn toàn giữa logic nghiệp vụ Python và tầng biểu diễn giao diện.</p>
            <p>Sử dụng <code>{% extends "base.html" %}</code> và các <code>{% block content %}</code> để tái sử dụng AppShell và nhất quán toàn bộ hệ thống giao diện.</p>
          `,
          resources: [
            { id: 'res_4', title: 'Jinja2_Cheatsheet.pdf', size: '820 KB', type: 'pdf' }
          ]
        },
        {
          id: 'les_4',
          courseId: 'c1',
          sectionId: 'sec_2',
          sectionTitle: 'Phần 2: Template Jinja2 & Bảo mật Biểu mẫu CSRF',
          order: 5,
          type: 'video',
          title: '5. Xử lý Biểu mẫu với Flask-WTF & Phòng chống Tấn công CSRF',
          duration: '50 phút',
          viewed: true,
          completed: false, // current active lesson
          content: `
            <p>Bảo mật biểu mẫu web là ưu tiên hàng đầu trong các ứng dụng doanh nghiệp.</p>
            <h3 class="section-title mt-4">1. CSRF Token là gì?</h3>
            <p>CSRF Token là một chuỗi ngẫu nhiên độc nhất gắn với phiên của người dùng. Mọi POST request thay đổi dữ liệu bắt buộc phải kèm token hợp lệ.</p>
            <h3 class="section-title mt-4">2. Client-side vs Server-side Validation</h3>
            <p>Client-side validation (HTML5 / JavaScript) giúp nâng cao trải nghiệm người dùng, nhưng Server-side validation là tuyến phòng thủ bắt buộc không thể bỏ qua.</p>
          `,
          resources: [
            { id: 'res_5', title: 'Form_Validation_Security_Rules.pdf', size: '1.1 MB', type: 'pdf' },
            { id: 'res_6', title: 'CSRF_Protection_Source_Code.py', size: '4.2 KB', type: 'code' }
          ]
        },
        {
          id: 'les_res1',
          courseId: 'c1',
          sectionId: 'sec_2',
          sectionTitle: 'Phần 2: Template Jinja2 & Bảo mật Biểu mẫu CSRF',
          order: 6,
          type: 'resource',
          title: '6. Tài nguyên Khóa học - Mã nguồn & Slide Bài giảng Phần 2',
          duration: '5 phút',
          viewed: false,
          completed: false,
          content: `<p>Tổng hợp các tệp mã nguồn mẫu, biểu mẫu đăng ký có bảo mật CSRF và slide bài giảng tổng hợp.</p>`,
          resources: [
            { id: 'res_7', title: 'Full_SourceCode_Section2.zip', size: '3.8 MB', type: 'archive' }
          ]
        },
        {
          id: 'les_5',
          courseId: 'c1',
          sectionId: 'sec_3',
          sectionTitle: 'Phần 3: Mô hình hóa Dữ liệu với SQLAlchemy ORM',
          order: 7,
          type: 'video',
          title: '7. Mô hình Hóa Dữ liệu với SQLAlchemy ORM & Quản lý Migrations',
          duration: '60 phút',
          viewed: false,
          completed: false,
          content: `<p>Nội dung bài học về ánh xạ quan hệ thực thể (ORM), khóa ngoại, quan hệ 1-N, N-N và sử dụng Alembic để di trú cơ sở dữ liệu an toàn.</p>`,
          resources: [
            { id: 'res_8', title: 'SQLAlchemy_Models_Schema.sql', size: '12 KB', type: 'sql' }
          ]
        },
        {
          id: 'les_6',
          courseId: 'c1',
          sectionId: 'sec_4',
          sectionTitle: 'Phần 4: RESTful API, Phân quyền RBAC & Đánh giá Cuối khóa',
          order: 8,
          type: 'video',
          title: '8. Xây dựng RESTful API & Phân quyền Truy cập (RBAC)',
          duration: '55 phút',
          viewed: false,
          completed: false,
          content: `<p>Thiết kế các API endpoints theo chuẩn REST, kiểm soát quyền truy cập chi tiết dựa trên vai trò (Role-Based Access Control) cho Student, Instructor và Admin.</p>`,
          resources: []
        },
        {
          id: 'les_cert',
          courseId: 'c1',
          sectionId: 'sec_4',
          sectionTitle: 'Phần 4: RESTful API, Phân quyền RBAC & Đánh giá Cuối khóa',
          order: 9,
          type: 'certificate',
          title: '9. Chứng chỉ Hoàn thành Khóa học (Certificate of Completion)',
          duration: '1 phút',
          viewed: false,
          completed: false,
          content: `<p>Chứng chỉ trực tuyến được cấp tự động sau khi sinh viên hoàn thành toàn bộ bài giảng và bài thi kết thúc môn đạt từ 6.0 trở lên.</p>`,
          resources: []
        }
      ],

      questionBank: [
        {
          id: 'q1',
          type: 'single_choice', // 'single_choice', 'multi_select', 'short_answer', 'essay'
          courseId: 'c1',
          topic: 'Giao thức HTTP',
          difficulty: 'medium', // 'easy', 'medium', 'hard'
          stem: 'Thuộc tính nào của Cookie giúp ngăn chặn JavaScript phía trình duyệt (ví dụ trong tấn công XSS) đọc được nội dung Cookie phiên?',
          options: [
            { id: 'opt_1', text: 'Secure' },
            { id: 'opt_2', text: 'HttpOnly', correct: true },
            { id: 'opt_3', text: 'SameSite=Strict' },
            { id: 'opt_4', text: 'Domain' }
          ],
          points: 2.0,
          usedCount: 4,
          revision: 1
        },
        {
          id: 'q2',
          type: 'single_choice',
          courseId: 'c1',
          topic: 'Flask Framework',
          difficulty: 'easy',
          stem: 'Trong Flask, mẫu thiết kế nào được khuyến nghị để khởi tạo đối tượng ứng dụng cho phép cấu hình linh hoạt theo từng môi trường kiểm thử?',
          options: [
            { id: 'opt_5', text: 'Singleton Pattern' },
            { id: 'opt_6', text: 'Application Factory Pattern', correct: true },
            { id: 'opt_7', text: 'Observer Pattern' },
            { id: 'opt_8', text: 'Prototype Pattern' }
          ],
          points: 2.0,
          usedCount: 3,
          revision: 2
        },
        {
          id: 'q3',
          type: 'multi_select',
          courseId: 'c1',
          topic: 'Bảo mật Web',
          difficulty: 'medium',
          stem: 'Những biện pháp nào sau đây giúp phòng ngừa hữu hiệu tấn công Cross-Site Request Forgery (CSRF)? (Chọn tất cả các đáp án đúng)',
          options: [
            { id: 'opt_9', text: 'Sử dụng CSRF Token đồng bộ gắn với Form hoặc Request Header', correct: true },
            { id: 'opt_10', text: 'Thiết lập thuộc tính SameSite cho Cookie (Lax hoặc Strict)', correct: true },
            { id: 'opt_11', text: 'Chuyển toàn bộ phương thức POST sang GET' },
            { id: 'opt_12', text: 'Kiểm tra Origin và Referer Header phía máy chủ', correct: true }
          ],
          points: 2.0,
          usedCount: 2,
          revision: 1
        },
        {
          id: 'q4',
          type: 'short_answer',
          courseId: 'c1',
          topic: 'Jinja2',
          difficulty: 'easy',
          stem: 'Từ khóa nào trong Jinja2 được sử dụng ở đầu file template con để kế thừa toàn bộ khung layout từ template cha?',
          acceptedAnswers: ['extends', '{% extends %}', 'extends "base.html"'],
          sampleAnswer: 'extends',
          points: 2.0,
          usedCount: 5,
          revision: 1
        },
        {
          id: 'q5',
          type: 'essay',
          courseId: 'c1',
          topic: 'Kiến trúc Cơ sở dữ liệu',
          difficulty: 'hard',
          stem: 'Phân tích sự khác biệt giữa cơ chế lưu phiên bằng Server-side Session (kèm Cookie tham chiếu) và Client-side Stateless Token (JWT). Trong trường hợp cần thu hồi quyền ngay lập tức khi tài khoản bị khóa, giải pháp nào ưu việt hơn và tại sao?',
          rubric: 'Nêu đúng định nghĩa (2 điểm). So sánh cơ chế lưu trữ và truyền tải (3 điểm). Phân tích việc thu hồi phiên tức thời (revocation) ưu thế của Server-side session (5 điểm).',
          points: 10.0,
          usedCount: 2,
          revision: 1
        }
      ],

      assessments: [
        {
          id: 'a1',
          courseId: 'c1',
          title: 'Kiểm tra giữa kỳ — Lập trình Web Flask & Giao thức HTTP',
          durationMinutes: 45,
          totalPoints: 18.0,
          status: 'published', // 'draft', 'published', 'closed'
          timingLocked: true, // Timing controls locked once published!
          studentStarted: true, // First student has started -> questions & points locked!
          questionIds: ['q1', 'q2', 'q3', 'q4', 'q5'],
          shuffleQuestions: true,
          maxAttempts: 1,
          openAt: '2026-09-01 08:00',
          closeAt: '2026-09-30 23:59',
          description: 'Bài kiểm tra giữa kỳ đánh giá kiến thức nền tảng về HTTP, Flask Blueprint, Jinja2 và bảo mật Web.'
        },
        {
          id: 'a2',
          courseId: 'c1',
          title: 'Bài thực hành 01 — Routing & Templating Jinja2',
          durationMinutes: 30,
          totalPoints: 10.0,
          status: 'closed',
          timingLocked: true,
          studentStarted: true,
          questionIds: ['q2', 'q4'],
          score: 10.0,
          gradedAt: '2026-08-28 14:30',
          feedback: 'Bài làm xuất sắc, nắm vững cú pháp Jinja2.'
        },
        {
          id: 'a3',
          courseId: 'c1',
          title: 'Bài tập Lớn — Thiết kế Kiến trúc Hệ thống & Tự luận',
          durationMinutes: 60,
          totalPoints: 20.0,
          status: 'published',
          timingLocked: true,
          studentStarted: true,
          questionIds: ['q3', 'q5'],
          pendingGrading: true // Pending essay grading queue for instructor!
        },
        {
          id: 'a4',
          courseId: 'c4',
          title: 'Bài kiểm tra thử nghiệm — Docker & Microservices',
          durationMinutes: 45,
          totalPoints: 10.0,
          status: 'draft', // DRAFT: can add/remove questions freely
          timingLocked: false,
          studentStarted: false,
          questionIds: ['q1', 'q2']
        }
      ],

      // Active Attempt State (Simulated Engine)
      activeAttempt: {
        assessmentId: 'a1',
        attemptId: 'att_2026_901',
        startedAt: new Date().toISOString(),
        durationMinutes: 45,
        remainingSeconds: 42 * 60 + 15,
        currentQuestionIndex: 0,
        leaseState: 'owner', // 'owner', 'lost', 'takeover'
        isOffline: false,
        saveStatus: 'saved', // 'saving', 'saved', 'unsynced'
        unsyncedChangesCount: 0,
        submitted: false,
        answers: {
          q1: 'opt_2',
          q2: 'opt_6',
          q3: ['opt_9', 'opt_10'],
          q4: 'extends',
          q5: 'Server-side Session lưu toàn bộ trạng thái và thông tin xác thực trên máy chủ (hoặc Redis), trình duyệt chỉ giữ session ID mã hóa. Khi quản trị viên khóa tài khoản, server chỉ cần xóa bản ghi phiên là người dùng bị đẩy ra ngay lập tức. Ngược lại với JWT stateless, token một khi phát hành sẽ có hiệu lực đến khi hết hạn trừ khi xây dựng blacklist tốn kém.'
        }
      },

      // Submitted Results
      results: [
        {
          attemptId: 'att_completed_01',
          assessmentId: 'a2',
          courseId: 'c1',
          studentId: 'u_student',
          score: 10.0,
          maxScore: 10.0,
          submittedAt: '2026-08-28 14:15',
          gradedAt: '2026-08-28 14:30',
          regradeHistory: [
            { version: 1, score: 8.0, reason: 'Chấm điểm tự động ban đầu', timestamp: '2026-08-28 14:20', actor: 'Hệ thống' },
            { version: 2, score: 10.0, reason: 'Giảng viên công nhận thêm đáp án hợp lệ cho câu hỏi điền khuyết', timestamp: '2026-08-28 14:30', actor: 'Trần Hoàng Nam (Giảng viên)' }
          ]
        },
        {
          attemptId: 'att_pending_02',
          assessmentId: 'a3',
          courseId: 'c1',
          studentId: 'u_student',
          score: null, // Pending grading
          maxScore: 20.0,
          submittedAt: '2026-09-05 10:20',
          status: 'pending_grading',
          essayAnswers: [
            {
              questionId: 'q5',
              questionStem: 'Phân tích sự khác biệt giữa cơ chế lưu phiên bằng Server-side Session và JWT...',
              studentText: 'Server-side session ưu việt hơn trong bài toán thu hồi quyền vì dữ liệu phiên nằm dưới sự kiểm soát trực tiếp của backend...',
              assignedScore: null,
              maxPoints: 10.0,
              instructorComment: ''
            }
          ]
        }
      ],

      // Notifications Center
      notifications: [
        { id: 'notif_1', title: 'Bài kiểm tra mới mở', body: 'Bài kiểm tra giữa kỳ môn PWD301 đã mở làm bài.', read: false, time: '10 phút trước', type: 'assessment' },
        { id: 'notif_2', title: 'Thay đổi điểm số', body: 'Điểm bài thực hành 01 môn PWD301 đã được điều chỉnh lên 10.0.', read: false, time: '2 giờ trước', type: 'grade' },
        { id: 'notif_3', title: 'Thông báo lớp học', body: 'Lịch học bù chuyên đề Docker sẽ diễn ra vào sáng thứ 7 tuần tới.', read: true, time: '1 ngày trước', type: 'course' },
        { id: 'notif_4', title: 'Bảo mật tài khoản', body: 'Tài khoản của bạn vừa đăng nhập từ thiết bị mới tại Hà Nội.', read: true, time: '3 ngày trước', type: 'security' }
      ],

      // Admin Management Data
      admin: {
        users: [
          { id: 'u_student', name: 'Nguyễn Minh Anh', email: 'student@demo.local', role: 'STUDENT', status: 'active', joinedAt: '2026-01-10', coursesCount: 3 },
          { id: 'u_instructor', name: 'Trần Hoàng Nam', email: 'instructor@demo.local', role: 'INSTRUCTOR', status: 'active', joinedAt: '2025-11-04', coursesCount: 4 },
          { id: 'u_admin', name: 'Lê Thu Hà', email: 'admin@demo.local', role: 'ADMIN', status: 'active', joinedAt: '2025-09-01', coursesCount: 0 },
          { id: 'u_user4', name: 'Phạm Thanh Tùng', email: 'tung.pt@demo.local', role: 'STUDENT', status: 'active', joinedAt: '2026-02-14', coursesCount: 2 },
          { id: 'u_user5', name: 'Hoàng Bảo Ngọc', email: 'ngoc.hb@demo.local', role: 'STUDENT', status: 'suspended', joinedAt: '2026-03-01', coursesCount: 1, suspensionReason: 'Phát hiện hành vi gian lận nộp bài thi ngày 20/08/2026.' },
          { id: 'u_user6', name: 'Vũ Đức Thịnh', email: 'thinh.vd@demo.local', role: 'INSTRUCTOR', status: 'active', joinedAt: '2025-12-10', coursesCount: 2 }
        ],

        instructorApplications: [
          { id: 'app_1', name: 'Nguyễn Văn Cường', email: 'cuong.nv@external.edu.vn', department: 'Khoa Công nghệ Thông tin', expertise: 'Kiến trúc Cloud & Kubernetes', submittedAt: '2026-09-04', status: 'pending' },
          { id: 'app_2', name: 'Trần Mai Phương', email: 'phuong.tm@external.edu.vn', department: 'Bộ môn Khoa học Dữ liệu', expertise: 'Deep Learning & NLP', submittedAt: '2026-09-02', status: 'pending' }
        ],

        auditEvents: [
          { id: 'aud_1', timestamp: '2026-09-08 12:45:10', actor: 'Lê Thu Hà (Admin)', action: 'USER_ROLE_UPDATE', target: 'u_user6 (Vũ Đức Thịnh)', details: 'Cấp thêm quyền Quản trị Ngân hàng câu hỏi', status: 'SUCCESS' },
          { id: 'aud_2', timestamp: '2026-09-08 11:20:05', actor: 'Trần Hoàng Nam (Giảng viên)', action: 'ASSESSMENT_PUBLISH', target: 'a1 (Kiểm tra giữa kỳ)', details: 'Xuất bản đề thi, khóa cấu hình thời gian', status: 'SUCCESS' },
          { id: 'aud_3', timestamp: '2026-09-07 16:30:22', actor: 'Hệ thống (Cron)', action: 'SYSTEM_BACKUP_COMPLETED', target: 'backup_20260907_full.bak', details: 'Sao lưu toàn vẹn 4.2 GB dữ liệu', status: 'SUCCESS' },
          { id: 'aud_4', timestamp: '2026-09-06 09:12:40', actor: 'Lê Thu Hà (Admin)', action: 'USER_SUSPENDED', target: 'u_user5 (Hoàng Bảo Ngọc)', details: 'Tạm ngưng tài khoản do vi phạm quy chế thi', status: 'SUCCESS' }
        ],

        securityEvents: [
          { id: 'sec_1', timestamp: '2026-09-08 03:14:22', type: 'PROMPT_INJECTION_BLOCKED', severity: 'high', details: 'Phát hiện kỹ thuật Jailbreak "Ignore previous instructions" trong chat AI Assistant', ip: '14.241.12.89', blocked: true },
          { id: 'sec_2', timestamp: '2026-09-07 22:40:11', type: 'MULTIPLE_FAILED_LOGINS', severity: 'medium', details: '5 lần thử mật khẩu không chính xác liên tiếp tài khoản admin@demo.local', ip: '118.70.180.45', blocked: true },
          { id: 'sec_3', timestamp: '2026-09-06 14:05:00', type: 'MALICIOUS_FILE_QUARANTINED', severity: 'high', details: 'ClamAV phát hiện mã độc embedded macro trong tệp lab_assignment.docm', ip: '42.114.88.19', blocked: true }
        ],

        systemHealth: {
          database: { name: 'SQL Server Database', status: 'healthy', latency: '4ms', load: '18%' },
          workers: { name: 'Celery Async Workers', status: 'healthy', activeJobs: 3, queuedJobs: 0 },
          scanner: { name: 'ClamAV Antivirus Scanner', status: 'healthy', lastScan: '2 phút trước', scannedFiles: 1420 },
          geminiRag: { name: 'Gemini RAG Embedding Engine', status: 'healthy', responseTime: '320ms', dailyTokens: '184k' }
        },

        serverTelemetry: {
          hostname: 'srv-master-prod01.pwd301.edu.vn',
          datacenter: 'FPT Complex Hà Nội (Node-01)',
          uptime: '45 ngày 18 giờ liên tục (99.99%)',
          cpu: {
            model: 'Intel Xeon Gold 6330 (16 vCPU @ 3.1 GHz)',
            usagePercent: 26.8,
            loadAvg: '1.12, 1.25, 1.08',
            temp: '47°C'
          },
          ram: {
            totalGB: 32,
            usedGB: 14.2,
            availableGB: 17.8,
            usagePercent: 44.4,
            cacheGB: 6.8,
            swapUsedGB: 1.1,
            swapTotalGB: 8.0
          },
          disk: {
            name: 'NVMe Gen4 Enterprise SSD RAID-10',
            totalGB: 1024,
            usedGB: 418,
            usagePercent: 40.8,
            readSpeed: '48.2 MB/s',
            writeSpeed: '22.4 MB/s',
            iops: 5120
          },
          network: {
            interface: '10GbE SFP+ Fiber Uplink',
            downloadSpeed: '142.6 Mbps',
            uploadSpeed: '385.2 Mbps',
            peakCapacity: '10 Gbps',
            latency: '3.2 ms',
            packetsPerSec: '28.5k pkt/s',
            packetLoss: '0.00%'
          }
        },

        backgroundJobs: [
          { id: 'job_1', name: 'Đồng bộ điểm thi và tính toán phân phối', progress: 100, status: 'completed', startedAt: '10:00', completedAt: '10:02' },
          { id: 'job_2', name: 'Phân tích mã độc tài liệu tải lên gần đây', progress: 65, status: 'running', startedAt: '12:50', completedAt: null },
          { id: 'job_3', name: 'Tổng hợp báo cáo tiến độ tuần', progress: 0, status: 'queued', startedAt: null, completedAt: null }
        ],

        backups: [
          { id: 'bk_1', filename: 'pwd301_prod_20260908_0000.bak', size: '4.2 GB', type: 'Full System', createdAt: '2026-09-08 00:00', status: 'completed' },
          { id: 'bk_2', filename: 'pwd301_prod_20260907_0000.bak', size: '4.1 GB', type: 'Full System', createdAt: '2026-09-07 00:00', status: 'completed' },
          { id: 'bk_3', filename: 'pwd301_prod_20260906_0000.bak', size: '4.1 GB', type: 'Full System', createdAt: '2026-09-06 00:00', status: 'completed' }
        ]
      }
    };
  }

  class Store {
    constructor() {
      this.listeners = [];
      this.init();
    }

    init() {
      const savedPerspective = sessionStorage.getItem(PERSPECTIVE_KEY);
      const savedData = localStorage.getItem(STORAGE_KEY);
      
      if (savedData) {
        try {
          this.state = JSON.parse(savedData);
          const seed = getInitialSeedData();
          if (this.state.admin && !this.state.admin.serverTelemetry) {
            this.state.admin.serverTelemetry = seed.admin.serverTelemetry;
          }
        } catch (e) {
          console.warn('Failed to parse saved state, resetting to seed data.', e);
          this.state = getInitialSeedData();
        }
      } else {
        this.state = getInitialSeedData();
      }

      if (savedPerspective) {
        this.state.currentPerspective = savedPerspective;
      }
    }

    persist() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state));
        sessionStorage.setItem(PERSPECTIVE_KEY, this.state.currentPerspective);
      } catch (e) {
        console.warn('Storage quota exceeded or unavailable', e);
      }
      this.notify();
    }

    notify() {
      this.listeners.forEach(fn => fn(this.state));
    }

    subscribe(fn) {
      this.listeners.push(fn);
      return () => {
        this.listeners = this.listeners.filter(l => l !== fn);
      };
    }

    // Reset Demo Data
    resetDemoData() {
      localStorage.removeItem(STORAGE_KEY);
      this.state = getInitialSeedData();
      this.persist();
      if (window.PWD.components) {
        window.PWD.components.showToast('Dữ liệu demo đã được khôi phục về trạng thái ban đầu.', 'info');
      }
    }

    // Perspective Switcher
    setPerspective(role) {
      const valid = ['public', 'student', 'instructor', 'admin'];
      if (valid.includes(role)) {
        this.state.currentPerspective = role;
        sessionStorage.setItem(PERSPECTIVE_KEY, role);
        this.persist();
      }
    }

    getPerspective() {
      return this.state.currentPerspective;
    }

    getCurrentUser() {
      const p = this.state.currentPerspective;
      if (p === 'public') return null;
      return this.state.personas[p] || this.state.personas.student;
    }

    // Student Actions
    enrollCourse(courseId) {
      const course = this.state.courses.find(c => c.id === courseId);
      if (!course) return { success: false, message: 'Khóa học không tồn tại.' };

      // Check prerequisite
      if (course.prerequisites && course.prerequisites.length > 0) {
        for (const prereqId of course.prerequisites) {
          const prereqCourse = this.state.courses.find(c => c.id === prereqId);
          if (!prereqCourse || prereqCourse.progress < 100) {
            return {
              success: false,
              message: `Không đủ điều kiện: Cần hoàn thành khóa học môn tiên quyết "${prereqCourse ? prereqCourse.title : prereqId}" trước!`
            };
          }
        }
      }

      // Check capacity
      if (course.enrolledCount >= course.capacity) {
        return { success: false, message: 'Khóa học đã hết chỉ tiêu tuyển sinh (Full Capacity)!' };
      }

      course.enrolled = true;
      course.enrolledCount += 1;
      course.progress = 0;
      this.persist();
      return { success: true, message: `Ghi danh thành công khóa học: ${course.title}` };
    }

    markLessonComplete(courseId, lessonId) {
      const lesson = this.state.lessons.find(l => l.id === lessonId);
      if (lesson) {
        lesson.completed = true;
        lesson.viewed = true;
        
        // Update course progress
        const courseLessons = this.state.lessons.filter(l => l.courseId === courseId);
        const completedCount = courseLessons.filter(l => l.completed).length;
        const course = this.state.courses.find(c => c.id === courseId);
        if (course && courseLessons.length > 0) {
          course.progress = Math.round((completedCount / courseLessons.length) * 100);
        }
        this.persist();
      }
    }

    toggleLessonComplete(courseId, lessonId) {
      const lesson = this.state.lessons.find(l => l.id === lessonId);
      if (lesson) {
        lesson.completed = !lesson.completed;
        lesson.viewed = true;
        
        // Update course progress
        const courseLessons = this.state.lessons.filter(l => l.courseId === courseId);
        const completedCount = courseLessons.filter(l => l.completed).length;
        const course = this.state.courses.find(c => c.id === courseId);
        if (course && courseLessons.length > 0) {
          course.progress = Math.round((completedCount / courseLessons.length) * 100);
        }
        this.persist();
        return { completed: lesson.completed, progress: course ? course.progress : 0 };
      }
      return null;
    }

    toggleWishlist(courseId) {
      const course = this.state.courses.find(c => c.id === courseId);
      if (course) {
        course.wishlisted = !course.wishlisted;
        this.persist();
        return course.wishlisted;
      }
      return false;
    }

    // Assessment Attempt Engine State Mutations
    saveAttemptAnswer(questionId, value) {
      this.state.activeAttempt.answers[questionId] = value;
      
      if (this.state.activeAttempt.isOffline) {
        this.state.activeAttempt.saveStatus = 'unsynced';
        this.state.activeAttempt.unsyncedChangesCount += 1;
      } else {
        this.state.activeAttempt.saveStatus = 'saving';
        setTimeout(() => {
          this.state.activeAttempt.saveStatus = 'saved';
          this.persist();
        }, 300);
      }
      this.persist();
    }

    toggleAttemptOffline() {
      this.state.activeAttempt.isOffline = !this.state.activeAttempt.isOffline;
      if (!this.state.activeAttempt.isOffline && this.state.activeAttempt.unsyncedChangesCount > 0) {
        // Reconnect and reconcile
        this.state.activeAttempt.saveStatus = 'saving';
        setTimeout(() => {
          this.state.activeAttempt.saveStatus = 'saved';
          this.state.activeAttempt.unsyncedChangesCount = 0;
          this.persist();
          if (window.PWD.components) {
            window.PWD.components.showToast('Đã kết nối lại mạng. Toàn bộ câu trả lời đã được đồng bộ an toàn.', 'success');
          }
        }, 500);
      }
      this.persist();
    }

    setAttemptLeaseState(state) {
      this.state.activeAttempt.leaseState = state;
      this.persist();
    }

    takeoverAttemptLease() {
      this.state.activeAttempt.leaseState = 'owner';
      this.persist();
      if (window.PWD.components) {
        window.PWD.components.showToast('Đã chiếm lại phiên làm bài (Lease Takeover). Tiếp tục làm bài an toàn.', 'success');
      }
    }

    submitAttempt() {
      this.state.activeAttempt.submitted = true;
      this.persist();
    }

    // Instructor Actions
    createQuestion(qData) {
      const newQ = {
        id: 'q_' + Date.now(),
        revision: 1,
        usedCount: 0,
        ...qData
      };
      this.state.questionBank.unshift(newQ);
      this.persist();
      return newQ;
    }

    updateQuestionWithRevision(qId, updatedData, reason) {
      const q = this.state.questionBank.find(item => item.id === qId);
      if (!q) return null;

      q.revision = (q.revision || 1) + 1;
      Object.assign(q, updatedData);

      // Record audit
      this.state.admin.auditEvents.unshift({
        id: 'aud_' + Date.now(),
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        actor: 'Trần Hoàng Nam (Giảng viên)',
        action: 'QUESTION_CORRECTION_REVISION',
        target: q.id,
        details: `Đính chính câu hỏi lên phiên bản v${q.revision}: ${reason || 'Hiệu chỉnh đáp án'}`,
        status: 'SUCCESS'
      });

      this.persist();
      return q;
    }

    publishAssessment(assessmentId) {
      const a = this.state.assessments.find(item => item.id === assessmentId);
      if (a) {
        a.status = 'published';
        a.timingLocked = true; // Invariant 13: Timing locked after publish!
        this.persist();
      }
    }

    simulateStudentStartedAssessment(assessmentId) {
      const a = this.state.assessments.find(item => item.id === assessmentId);
      if (a) {
        a.studentStarted = true; // Invariant 14: Structure & assigned points locked!
        this.persist();
      }
    }

    gradeEssayAnswer(attemptId, questionId, score, comment) {
      const res = this.state.results.find(r => r.attemptId === attemptId);
      if (res && res.essayAnswers) {
        const essay = res.essayAnswers.find(e => e.questionId === questionId);
        if (essay) {
          essay.assignedScore = parseFloat(score);
          essay.instructorComment = comment;
          res.score = parseFloat(score);
          res.status = 'graded';
          this.persist();
        }
      }
    }

    // Admin Sensitive Actions
    suspendUser(userId, reason) {
      const user = this.state.admin.users.find(u => u.id === userId);
      if (user) {
        user.status = 'suspended';
        user.suspensionReason = reason;

        this.state.admin.auditEvents.unshift({
          id: 'aud_' + Date.now(),
          timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
          actor: 'Lê Thu Hà (Admin)',
          action: 'USER_SUSPENDED',
          target: `${user.id} (${user.name})`,
          details: `Khóa tài khoản bắt buộc: ${reason}`,
          status: 'SUCCESS'
        });

        this.persist();
        return true;
      }
      return false;
    }

    reactivateUser(userId) {
      const user = this.state.admin.users.find(u => u.id === userId);
      if (user) {
        user.status = 'active';
        user.suspensionReason = null;

        this.state.admin.auditEvents.unshift({
          id: 'aud_' + Date.now(),
          timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
          actor: 'Lê Thu Hà (Admin)',
          action: 'USER_REACTIVATED',
          target: `${user.id} (${user.name})`,
          details: 'Kích hoạt lại tài khoản người dùng',
          status: 'SUCCESS'
        });

        this.persist();
        return true;
      }
      return false;
    }

    reassignCourseOwner(courseId, newInstructorId, reason) {
      const course = this.state.courses.find(c => c.id === courseId);
      const newInst = this.state.admin.users.find(u => u.id === newInstructorId);
      if (course && newInst) {
        const oldName = course.instructorName;
        course.instructorId = newInst.id;
        course.instructorName = newInst.name;

        this.state.admin.auditEvents.unshift({
          id: 'aud_' + Date.now(),
          timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
          actor: 'Lê Thu Hà (Admin)',
          action: 'COURSE_OWNER_REASSIGNED',
          target: `${course.code} (${course.title})`,
          details: `Chuyển quyền quản lý từ ${oldName} sang ${newInst.name}. Lý do: ${reason}`,
          status: 'SUCCESS'
        });

        this.persist();
        return true;
      }
      return false;
    }

    createBackupRun() {
      const newBk = {
        id: 'bk_' + Date.now(),
        filename: `pwd301_prod_${new Date().toISOString().slice(0,10).replace(/-/g,'')}_manual.bak`,
        size: '4.3 GB',
        type: 'Thủ công (Full System)',
        createdAt: new Date().toISOString().replace('T', ' ').substring(0, 16),
        status: 'completed'
      };
      this.state.admin.backups.unshift(newBk);
      
      this.state.admin.auditEvents.unshift({
        id: 'aud_' + Date.now(),
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        actor: 'Lê Thu Hà (Admin)',
        action: 'MANUAL_BACKUP_CREATED',
        target: newBk.filename,
        details: 'Khởi tạo bản sao lưu thủ công thành công',
        status: 'SUCCESS'
      });

      this.persist();
      return newBk;
    }

    restoreSystemBackup(backupId, reason) {
      const bk = this.state.admin.backups.find(b => b.id === backupId);
      this.state.admin.auditEvents.unshift({
        id: 'aud_' + Date.now(),
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        actor: 'Lê Thu Hà (Admin)',
        action: 'SYSTEM_RESTORE_EXECUTED',
        target: bk ? bk.filename : backupId,
        details: `Phục hồi hệ thống từ bản sao lưu. Căn cứ & lý do: ${reason}`,
        status: 'SUCCESS'
      });
      this.persist();
      return true;
    }
  }

  window.PWD.store = new Store();
})();
