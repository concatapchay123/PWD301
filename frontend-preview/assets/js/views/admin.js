/**
 * PWD301 — Admin Views
 * Governance, Security Center, Audit Logs, System Health & Sensitive Actions
 */

(function () {
  'use strict';

  window.PWD = window.PWD || {};
  window.PWD.views = window.PWD.views || {};

  const adminViews = {
    // 1. Executive Academic Operations Dashboard (Redesigned High-Clarity SaaS)
    dashboard() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const health = store.admin.systemHealth;
      const tel = store.admin.serverTelemetry || {
        hostname: 'srv-master-prod01.pwd301.edu.vn',
        datacenter: 'FPT Complex Hà Nội (Node-01)',
        uptime: '45 ngày 18 giờ liên tục (99.99%)',
        cpu: { model: 'Intel Xeon Gold 6330 (16 vCPU @ 3.1 GHz)', usagePercent: 26.8, loadAvg: '1.12, 1.25, 1.08', temp: '47°C' },
        ram: { totalGB: 32, usedGB: 14.2, availableGB: 17.8, usagePercent: 44.4, cacheGB: 6.8, swapUsedGB: 1.1, swapTotalGB: 8.0 },
        disk: { name: 'NVMe Gen4 Enterprise SSD RAID-10', totalGB: 1024, usedGB: 418, usagePercent: 40.8, readSpeed: '48.2 MB/s', writeSpeed: '22.4 MB/s', iops: 5120 },
        network: { interface: '10GbE SFP+ Fiber Uplink', downloadSpeed: '142.6 Mbps', uploadSpeed: '385.2 Mbps', peakCapacity: '10 Gbps', latency: '3.2 ms', packetsPerSec: '28.5k pkt/s', packetLoss: '0.00%' }
      };

      const dlVal = (tel.network.downloadSpeed || '').replace(/\s*Mbps/i, '');
      const ulVal = (tel.network.uploadSpeed || '').replace(/\s*Mbps/i, '');

      // Pending items queue
      const pendingInstructors = store.admin.instructorApplications || [];
      const pendingCourse = store.courses.find(c => c.code === 'DSD401') || { 
        code: 'DSD401', 
        title: 'Thiết kế Hệ thống Phân tán (Distributed Systems)', 
        instructorName: 'Trần Hoàng Nam', 
        status: 'pending_approval' 
      };
      const suspendedUser = store.admin.users.find(u => u.status === 'suspended') || {
        id: 'u_user5',
        name: 'Hoàng Bảo Ngọc',
        email: 'ngoc.hb@demo.local',
        suspensionReason: 'Phát hiện hành vi gian lận nộp bài thi ngày 20/08/2026.'
      };

      const pendingCourseCount = pendingCourse.status === 'pending_approval' ? 1 : 0;
      const totalUrgentCount = pendingInstructors.length + pendingCourseCount + (suspendedUser ? 1 : 0);

      // LMS Aggregations
      const publishedCourses = store.courses.filter(c => c.status === 'published');
      const totalStudentsCount = 1280;
      const activeInstructorsCount = 34;
      const completedAssessmentsCount = 892;

      return `
        <div class="admin-dashboard-wrapper">
          
          <!-- ===================================================================
               1. SERVER HARDWARE RESOURCES & NETWORK BANDWIDTH MONITOR (HERO)
               =================================================================== -->
          <div class="admin-welcome-hero admin-telemetry-hero">
            <!-- Top strip: Server node info & quick actions -->
            <div class="telemetry-node-strip">
              <div class="d-flex align-items-center gap-2.5">
                <div class="telemetry-header-icon" title="Hạ tầng máy chủ trung tâm & Giám sát trực tiếp">
                  ${cmp.icon('server')}
                </div>
                <div>
                  <div class="d-flex align-items-center flex-wrap gap-2 mb-1">
                    <h2 class="m-0 fw-bold text-slate-900" style="font-size: 16px; letter-spacing: -0.01em;">
                      Tài nguyên Máy chủ & Băng thông Mạng
                    </h2>
                    <span class="hero-status-pill">
                      <span class="live-pulse-dot"></span> Node-01 • Sẵn sàng
                    </span>
                  </div>
                  <div class="d-flex align-items-center flex-wrap gap-2 text-caption text-muted" style="font-size: 11.5px;">
                    <span class="font-monospace text-slate-700 fw-semibold">${tel.hostname}</span>
                    <span class="text-slate-300">•</span>
                    <span>${tel.datacenter}</span>
                    <span class="text-slate-300">•</span>
                    <span class="text-success font-monospace fw-medium">${tel.uptime}</span>
                  </div>
                </div>
              </div>

              <!-- Quick Action Toolbar -->
              <div class="d-flex align-items-center gap-2">
                <a href="#/admin/system-health" class="telemetry-btn">
                  ${cmp.icon('activity')} Sức khỏe DV
                </a>
                <a href="#/admin/storage" class="telemetry-btn">
                  ${cmp.icon('database')} Lưu trữ & Backup
                </a>
                <button id="btn-refresh-dash" class="telemetry-btn telemetry-btn-primary" onclick="PWD.views.admin.refreshDashboardData()" title="Làm mới thông số tài nguyên máy chủ">
                  <span id="icon-refresh-dash" class="me-1">${cmp.icon('refresh')}</span> Làm mới
                </button>
              </div>
            </div>

            <!-- 4 Hardware & Network Resource Metric Cards -->
            <div class="row g-3">
              <!-- 1. CPU Processor Metric -->
              <div class="col-xl-3 col-md-6">
                <div class="telemetry-metric-card">
                  <div>
                    <div class="telemetry-card-header">
                      <div class="d-flex align-items-center gap-2">
                        <div class="telemetry-icon-box cpu">${cmp.icon('cpu')}</div>
                        <span class="telemetry-card-title">Vi xử lý CPU</span>
                      </div>
                      <span class="telemetry-pill-badge" style="color: #2563eb; background: rgba(37,99,235,0.08);">
                        ${tel.cpu.temp}
                      </span>
                    </div>

                    <div class="telemetry-value-row">
                      <span class="telemetry-main-value">${tel.cpu.usagePercent}%</span>
                      <span class="telemetry-sub-value">16 vCPU @ 3.1GHz</span>
                    </div>

                    <div class="telemetry-progress-track">
                      <div class="telemetry-progress-bar cpu" style="width: ${tel.cpu.usagePercent}%;"></div>
                    </div>
                  </div>

                  <div class="telemetry-card-footer">
                    <div class="telemetry-footer-row">
                      <span class="telemetry-footer-label">Tải trung bình:</span>
                      <span class="telemetry-footer-val">${tel.cpu.loadAvg}</span>
                    </div>
                    <div class="telemetry-footer-sub" title="${tel.cpu.model}">
                      ${tel.cpu.model}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 2. RAM Memory Metric -->
              <div class="col-xl-3 col-md-6">
                <div class="telemetry-metric-card">
                  <div>
                    <div class="telemetry-card-header">
                      <div class="d-flex align-items-center gap-2">
                        <div class="telemetry-icon-box ram">${cmp.icon('server')}</div>
                        <span class="telemetry-card-title">Bộ nhớ RAM</span>
                      </div>
                      <span class="telemetry-pill-badge" style="color: #4f46e5; background: rgba(99,102,241,0.08);">
                        ${tel.ram.usagePercent}%
                      </span>
                    </div>

                    <div class="telemetry-value-row">
                      <span class="telemetry-main-value">${tel.ram.usedGB}<span style="font-size: 13px; font-weight: normal; color: var(--slate-500);"> / ${tel.ram.totalGB} GB</span></span>
                      <span class="telemetry-sub-value text-success">Trống ${tel.ram.availableGB} GB</span>
                    </div>

                    <div class="telemetry-progress-track">
                      <div class="telemetry-progress-bar ram" style="width: ${tel.ram.usagePercent}%;"></div>
                    </div>
                  </div>

                  <div class="telemetry-card-footer">
                    <div class="telemetry-footer-row">
                      <span class="telemetry-footer-label">Cache / Swap:</span>
                      <span class="telemetry-footer-val">${tel.ram.cacheGB} GB • Swap ${tel.ram.swapUsedGB} GB</span>
                    </div>
                    <div class="telemetry-footer-sub" title="DDR4 ECC (Swap: ${tel.ram.swapUsedGB} GB / ${tel.ram.swapTotalGB} GB)">
                      DDR4 ECC • Swap ${tel.ram.swapUsedGB}/${tel.ram.swapTotalGB} GB
                    </div>
                  </div>
                </div>
              </div>

              <!-- 3. NVMe SSD Storage Metric -->
              <div class="col-xl-3 col-md-6">
                <div class="telemetry-metric-card">
                  <div>
                    <div class="telemetry-card-header">
                      <div class="d-flex align-items-center gap-2">
                        <div class="telemetry-icon-box disk">${cmp.icon('database')}</div>
                        <span class="telemetry-card-title">Ổ cứng SSD</span>
                      </div>
                      <span class="telemetry-pill-badge" style="color: #059669; background: rgba(16,185,129,0.08);">
                        ${tel.disk.iops} IOPS
                      </span>
                    </div>

                    <div class="telemetry-value-row">
                      <span class="telemetry-main-value">${tel.disk.usedGB}<span style="font-size: 13px; font-weight: normal; color: var(--slate-500);"> / ${tel.disk.totalGB} GB</span></span>
                      <span class="telemetry-sub-value">${tel.disk.usagePercent}% dùng</span>
                    </div>

                    <div class="telemetry-progress-track">
                      <div class="telemetry-progress-bar disk" style="width: ${tel.disk.usagePercent}%;"></div>
                    </div>
                  </div>

                  <div class="telemetry-card-footer">
                    <div class="telemetry-footer-row">
                      <span class="telemetry-footer-label">Tốc độ Đọc/Ghi:</span>
                      <span class="telemetry-footer-val" style="white-space: nowrap;">R: ${tel.disk.readSpeed} • W: ${tel.disk.writeSpeed}</span>
                    </div>
                    <div class="telemetry-footer-sub" title="${tel.disk.name}">
                      ${tel.disk.name}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 4. Network Bandwidth Metric -->
              <div class="col-xl-3 col-md-6">
                <div class="telemetry-metric-card">
                  <div>
                    <div class="telemetry-card-header">
                      <div class="d-flex align-items-center gap-2">
                        <div class="telemetry-icon-box network">${cmp.icon('wifi')}</div>
                        <span class="telemetry-card-title">Băng thông Mạng</span>
                      </div>
                      <span class="telemetry-pill-badge" style="color: #0891b2; background: rgba(6,182,212,0.08);">
                        ${tel.network.latency} RTT
                      </span>
                    </div>

                    <div class="telemetry-value-row">
                      <div class="telemetry-main-value" style="font-size: 15px; line-height: 1.2; white-space: nowrap;">
                        <span style="color: #0284c7;">↓ ${dlVal}</span>
                        <span class="text-slate-400 mx-1" style="font-weight: 300;">/</span>
                        <span style="color: #2563eb;">↑ ${ulVal}</span>
                        <span style="font-size: 11px; font-weight: normal; color: var(--slate-500); margin-left: 2px;">Mbps</span>
                      </div>
                      <span class="telemetry-sub-value badge badge-neutral" style="font-size: 10px; padding: 2px 6px;">${tel.network.peakCapacity}</span>
                    </div>

                    <div class="telemetry-progress-track">
                      <div class="telemetry-progress-bar network" style="width: 58%;"></div>
                    </div>
                  </div>

                  <div class="telemetry-card-footer">
                    <div class="telemetry-footer-row">
                      <span class="telemetry-footer-label">Lưu lượng / Loss:</span>
                      <span class="telemetry-footer-val">${tel.network.packetsPerSec} • Loss ${tel.network.packetLoss}</span>
                    </div>
                    <div class="telemetry-footer-sub" title="${tel.network.interface}">
                      ${tel.network.interface}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ===================================================================
               2. ACTION CENTER: HÀNG ĐỢI PHÊ DUYỆT CẤP BÁCH (TRIAGE HUB)
               =================================================================== -->
          ${totalUrgentCount > 0 ? `
            <div class="action-triage-card">
              <div class="action-triage-header">
                <div class="d-flex align-items-center gap-2">
                  <span class="text-warning">${cmp.icon('alertTriangle')}</span>
                  <span class="fw-bold text-slate-900" style="font-size: 15px;">Hàng đợi Cần Xử lý Ngay (Action Triage Hub)</span>
                </div>
                <span class="badge badge-warning" style="font-size: 12.5px; padding: 4px 10px;">
                  ${totalUrgentCount} yêu cầu đang chờ Admin quyết định
                </span>
              </div>

              <div class="p-3">
                <div class="row g-3 align-items-stretch">
                  <!-- Cột 1: Hồ sơ Giảng viên Chờ Tuyển Dụng -->
                  <div class="col-lg-6 d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <span class="fw-semibold text-slate-800" style="font-size: 13px;">
                        ${cmp.icon('graduation')} Đơn Đăng ký Giảng viên (${pendingInstructors.length})
                      </span>
                      <a href="#/admin/instructor-approvals" class="text-caption text-primary text-decoration-none">Xem toàn bộ →</a>
                    </div>

                    ${pendingInstructors.length > 0 ? `
                      <div class="triage-col-list">
                        ${pendingInstructors.map(app => `
                          <div class="triage-unit-box">
                            <div class="d-flex justify-content-between align-items-start gap-2">
                              <div>
                                <div class="fw-bold text-slate-900" style="font-size: 13.5px;">${app.name}</div>
                                <div class="text-caption text-muted">${app.email} • ${app.department}</div>
                                <div class="mt-1">
                                  <span class="badge" style="background: rgba(37,99,235,0.1); color: #2563eb; font-size: 11px;">
                                    Chuyên môn: ${app.expertise}
                                  </span>
                                </div>
                              </div>
                              <div class="d-flex gap-1 flex-shrink-0">
                                <button class="btn btn-ghost btn-sm px-2 py-1 text-danger" onclick="PWD.views.admin.quickRejectInstructor('${app.id}')" title="Từ chối">
                                  Từ chối
                                </button>
                                <button class="btn btn-primary btn-sm px-3 py-1" onclick="PWD.views.admin.quickApproveInstructor('${app.id}')">
                                  ${cmp.icon('checkCircle')} Phê duyệt
                                </button>
                              </div>
                            </div>
                          </div>
                        `).join('')}
                      </div>
                    ` : `
                      <div class="p-3 text-center text-muted bg-light rounded flex-grow-1 d-flex align-items-center justify-content-center" style="font-size: 13px;">
                        ${cmp.icon('checkCircle')} Không còn đơn đăng ký giảng viên nào chờ duyệt.
                      </div>
                    `}
                  </div>

                  <!-- Cột 2: Duyệt Khóa học Sửa Đổi Lớn & Khiếu Nại Kỷ Luật -->
                  <div class="col-lg-6 d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <span class="fw-semibold text-slate-800" style="font-size: 13px;">
                        ${cmp.icon('book')} Giáo trình & Khiếu nại Học vụ (${pendingCourseCount + (suspendedUser ? 1 : 0)})
                      </span>
                      <a href="#/admin/course-review" class="text-caption text-primary text-decoration-none">Trung tâm xét duyệt →</a>
                    </div>

                    <div class="triage-col-list">
                      ${pendingCourse.status === 'pending_approval' ? `
                        <div class="triage-unit-box" style="border-left: 3px solid #6366f1;">
                          <div class="d-flex justify-content-between align-items-start gap-2">
                            <div>
                              <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="badge" style="background: #4f46e5; color: #fff; font-weight: 700; font-size: 11px;">${pendingCourse.code}</span>
                                <strong class="text-slate-900" style="font-size: 13.5px;">${pendingCourse.title}</strong>
                              </div>
                              <div class="text-caption text-muted">
                                Giảng viên đề xuất: <strong>${pendingCourse.instructorName}</strong>
                              </div>
                              <div class="mt-1">
                                <span class="badge" style="background: rgba(99,102,241,0.1); color: #6366f1; font-size: 11px;">
                                  Đề xuất: Cập nhật 40% syllabus (Raft Consensus)
                                </span>
                              </div>
                            </div>
                            <div class="d-flex gap-1 flex-shrink-0">
                              <a href="#/admin/course-review" class="btn btn-secondary btn-sm px-2 py-1">So sánh Diff</a>
                              <button class="btn btn-primary btn-sm px-2 py-1" onclick="PWD.views.admin.quickApproveCourse('${pendingCourse.code}')">
                                ${cmp.icon('checkCircle')} Ban hành
                              </button>
                            </div>
                          </div>
                        </div>
                      ` : ''}

                      ${suspendedUser ? `
                        <div class="triage-unit-box" style="border-left: 3px solid #ef4444; background: rgba(239,68,68,0.03);">
                          <div class="d-flex justify-content-between align-items-start gap-2">
                            <div>
                              <div class="fw-bold text-danger" style="font-size: 13.5px;">Khiếu nại Đình chỉ Tài khoản</div>
                              <div class="text-caption text-muted">${suspendedUser.name} (${suspendedUser.email})</div>
                              <div class="mt-1">
                                <span class="badge" style="background: rgba(239,68,68,0.1); color: #ef4444; font-size: 11px;">
                                  Lý do: Đơn xin phúc khảo thi cử ngày 20/08
                                </span>
                              </div>
                            </div>
                            <div class="d-flex gap-1 flex-shrink-0">
                              <a href="#/admin/user-detail/${suspendedUser.id}" class="btn btn-outline-danger btn-sm px-2 py-1">
                                Xem xét & Phúc khảo
                              </a>
                            </div>
                          </div>
                        </div>
                      ` : ''}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ` : `
            <div class="p-3 rounded-3 bg-white border border-slate-200 d-flex align-items-center justify-content-between">
              <div class="d-flex align-items-center gap-2 text-success">
                ${cmp.icon('checkCircle')}
                <span class="fw-semibold text-slate-800" style="font-size: 14px;">Mọi yêu cầu phê duyệt giảng viên và khóa học đã được giải quyết xong!</span>
              </div>
              <span class="badge badge-success">Không có tồn đọng</span>
            </div>
          `}

          <!-- ===================================================================
               3. EXECUTIVE KPI BENTO GRID (4 CORE EDUCATIONAL METRICS)
               =================================================================== -->
          <div class="row g-3">
            <!-- Metric 1: Tổng Sinh viên / Học viên -->
            <div class="col-xl-3 col-sm-6">
              <div class="admin-kpi-card">
                <div>
                  <div class="d-flex justify-content-between align-items-center">
                    <span class="text-caption text-muted fw-semibold text-uppercase" style="letter-spacing: 0.05em;">Học viên Hoạt động</span>
                    <div class="kpi-icon-wrap accent-blue">${cmp.icon('users')}</div>
                  </div>
                  <div class="kpi-metric-number">${totalStudentsCount.toLocaleString('vi-VN')}</div>
                  <div class="d-flex align-items-center gap-2">
                    <span class="kpi-trend-pill trend-up">↑ +12.5%</span>
                    <span class="text-caption text-muted">so với tháng trước</span>
                  </div>
                  <div class="kpi-progress-bar">
                    <div class="kpi-progress-fill fill-blue" style="width: 96%;"></div>
                  </div>
                </div>
                <div class="d-flex justify-content-between text-caption text-muted pt-2 border-top border-slate-100">
                  <span>Tài khoản kích hoạt:</span>
                  <strong class="text-slate-800">96.2%</strong>
                </div>
              </div>
            </div>

            <!-- Metric 2: Khóa học Đào tạo -->
            <div class="col-xl-3 col-sm-6">
              <div class="admin-kpi-card">
                <div>
                  <div class="d-flex justify-content-between align-items-center">
                    <span class="text-caption text-muted fw-semibold text-uppercase" style="letter-spacing: 0.05em;">Khóa học Vận hành</span>
                    <div class="kpi-icon-wrap accent-emerald">${cmp.icon('book')}</div>
                  </div>
                  <div class="kpi-metric-number">18</div>
                  <div class="d-flex align-items-center gap-2">
                    <span class="kpi-trend-pill trend-up">14 Đang mở</span>
                    <span class="text-caption text-muted">1 chờ duyệt • 3 nháp</span>
                  </div>
                  <div class="kpi-progress-bar">
                    <div class="kpi-progress-fill fill-emerald" style="width: 78%;"></div>
                  </div>
                </div>
                <div class="d-flex justify-content-between text-caption text-muted pt-2 border-top border-slate-100">
                  <span>Lượt ghi danh tích lũy:</span>
                  <strong class="text-slate-800">3,420 lượt</strong>
                </div>
              </div>
            </div>

            <!-- Metric 3: Đội ngũ Giảng viên -->
            <div class="col-xl-3 col-sm-6">
              <div class="admin-kpi-card">
                <div>
                  <div class="d-flex justify-content-between align-items-center">
                    <span class="text-caption text-muted fw-semibold text-uppercase" style="letter-spacing: 0.05em;">Đội ngũ Giảng dạy</span>
                    <div class="kpi-icon-wrap accent-amber">${cmp.icon('graduation')}</div>
                  </div>
                  <div class="kpi-metric-number">${activeInstructorsCount}</div>
                  <div class="d-flex align-items-center gap-2">
                    <span class="kpi-trend-pill trend-neutral">${pendingInstructors.length} chờ tuyển</span>
                    <span class="text-caption text-muted">trên 5 bộ môn</span>
                  </div>
                  <div class="kpi-progress-bar">
                    <div class="kpi-progress-fill fill-amber" style="width: 92%;"></div>
                  </div>
                </div>
                <div class="d-flex justify-content-between text-caption text-muted pt-2 border-top border-slate-100">
                  <span>Đánh giá giảng dạy:</span>
                  <strong class="text-warning">4.85 / 5.0 ⭐</strong>
                </div>
              </div>
            </div>

            <!-- Metric 4: Đánh giá & Khảo sát -->
            <div class="col-xl-3 col-sm-6">
              <div class="admin-kpi-card">
                <div>
                  <div class="d-flex justify-content-between align-items-center">
                    <span class="text-caption text-muted fw-semibold text-uppercase" style="letter-spacing: 0.05em;">Đánh giá & Bài thi</span>
                    <div class="kpi-icon-wrap accent-violet">${cmp.icon('checkCircle')}</div>
                  </div>
                  <div class="kpi-metric-number">${completedAssessmentsCount}</div>
                  <div class="d-flex align-items-center gap-2">
                    <span class="kpi-trend-pill trend-up">↑ 84.6% Đạt</span>
                    <span class="text-caption text-muted">kỳ thi giữa kỳ</span>
                  </div>
                  <div class="kpi-progress-bar">
                    <div class="kpi-progress-fill fill-violet" style="width: 85%;"></div>
                  </div>
                </div>
                <div class="d-flex justify-content-between text-caption text-muted pt-2 border-top border-slate-100">
                  <span>Bài luận chờ chấm:</span>
                  <strong class="text-slate-800">18 bài</strong>
                </div>
              </div>
            </div>
          </div>

          <!-- ===================================================================
               4. ANALYTICS: XU HƯỚNG TƯƠNG TÁC & PHÂN BỔ ĐÀO TẠO
               =================================================================== -->
          <div class="row g-3">
            <!-- Biểu đồ Xu hướng Tương tác Đào tạo (8 Cột) -->
            <div class="col-lg-8">
              <div class="admin-panel-card">
                <div class="admin-panel-header">
                  <div>
                    <div class="fw-bold text-slate-900" style="font-size: 15px;">
                      Xu hướng Ghi danh & Hoàn thành Bài học
                    </div>
                    <div class="text-caption text-muted">Số lượt sinh viên ghi danh mới kết hợp nhịp độ học tập qua các tuần</div>
                  </div>
                  <div class="d-flex align-items-center gap-1">
                    <button class="chart-filter-btn" onclick="PWD.views.admin.filterAnalytics('7d')">7 ngày</button>
                    <button class="chart-filter-btn active" onclick="PWD.views.admin.filterAnalytics('30d')">30 ngày qua</button>
                    <button class="chart-filter-btn" onclick="PWD.views.admin.filterAnalytics('term')">Kỳ Fall 2026</button>
                  </div>
                </div>

                <div class="p-3">
                  <!-- Metrics summary strip -->
                  <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 p-2 px-3 rounded mb-3" style="background: var(--slate-50); border: 1px solid var(--slate-200);">
                    <div class="d-flex align-items-center gap-4">
                      <div>
                        <div class="text-caption text-muted">Trung bình học tập:</div>
                        <strong class="text-primary font-monospace" style="font-size: 15px;">+248 lượt/ngày</strong>
                      </div>
                      <div class="border-start border-slate-200 ps-4">
                        <div class="text-caption text-muted">Tỷ lệ tương tác đều đặn:</div>
                        <strong class="text-success font-monospace" style="font-size: 15px;">76.8%</strong>
                      </div>
                    </div>
                    <div class="d-flex align-items-center gap-3 text-caption">
                      <span class="d-flex align-items-center gap-1">
                        <span style="display:inline-block; width:10px; height:10px; background:#2563eb; border-radius:2px;"></span>
                        Ghi danh mới
                      </span>
                      <span class="d-flex align-items-center gap-1">
                        <span style="display:inline-block; width:10px; height:3px; background:#10b981; border-radius:2px;"></span>
                        Bài hoàn thành (Curve)
                      </span>
                    </div>
                  </div>

                  <!-- Pure SVG High-Clarity Learning Activity Chart -->
                  <svg class="chart-svg-container" viewBox="0 0 700 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                      <linearGradient id="enrollBarGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#3b82f6"/>
                        <stop offset="100%" stop-color="#1d4ed8"/>
                      </linearGradient>
                      <linearGradient id="lessonsAreaGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#10b981" stop-opacity="0.35"/>
                        <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
                      </linearGradient>
                    </defs>

                    <!-- Horizontal Grid Lines -->
                    <line x1="40" y1="20" x2="680" y2="20" stroke="var(--slate-200)" stroke-dasharray="3 3"/>
                    <text x="15" y="24" fill="var(--slate-400)" font-size="11" font-family="sans-serif">400</text>

                    <line x1="40" y1="70" x2="680" y2="70" stroke="var(--slate-200)" stroke-dasharray="3 3"/>
                    <text x="15" y="74" fill="var(--slate-400)" font-size="11" font-family="sans-serif">250</text>

                    <line x1="40" y1="120" x2="680" y2="120" stroke="var(--slate-200)" stroke-dasharray="3 3"/>
                    <text x="15" y="124" fill="var(--slate-400)" font-size="11" font-family="sans-serif">100</text>

                    <line x1="40" y1="165" x2="680" y2="165" stroke="var(--slate-300)" stroke-width="1"/>
                    <text x="22" y="169" fill="var(--slate-400)" font-size="11" font-family="sans-serif">0</text>

                    <!-- Bar Group: New Enrollments -->
                    <!-- Week 1 -->
                    <rect x="75" y="105" width="28" height="60" rx="4" fill="url(#enrollBarGrad)" opacity="0.9"/>
                    <text x="89" y="184" text-anchor="middle" fill="var(--slate-500)" font-size="11.5">Tuần 1</text>
                    <text x="89" y="98" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="600">42</text>

                    <!-- Week 2 -->
                    <rect x="175" y="85" width="28" height="80" rx="4" fill="url(#enrollBarGrad)" opacity="0.9"/>
                    <text x="189" y="184" text-anchor="middle" fill="var(--slate-500)" font-size="11.5">Tuần 2</text>
                    <text x="189" y="78" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="600">65</text>

                    <!-- Week 3 -->
                    <rect x="275" y="95" width="28" height="70" rx="4" fill="url(#enrollBarGrad)" opacity="0.9"/>
                    <text x="289" y="184" text-anchor="middle" fill="var(--slate-500)" font-size="11.5">Tuần 3</text>
                    <text x="289" y="88" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="600">58</text>

                    <!-- Week 4 -->
                    <rect x="375" y="65" width="28" height="100" rx="4" fill="url(#enrollBarGrad)" opacity="0.9"/>
                    <text x="389" y="184" text-anchor="middle" fill="var(--slate-500)" font-size="11.5">Tuần 4</text>
                    <text x="389" y="58" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="600">84</text>

                    <!-- Week 5 -->
                    <rect x="475" y="75" width="28" height="90" rx="4" fill="url(#enrollBarGrad)" opacity="0.9"/>
                    <text x="489" y="184" text-anchor="middle" fill="var(--slate-500)" font-size="11.5">Tuần 5</text>
                    <text x="489" y="68" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="600">72</text>

                    <!-- Week 6 (Current) -->
                    <rect x="575" y="45" width="28" height="120" rx="4" fill="url(#enrollBarGrad)" opacity="0.95"/>
                    <text x="589" y="184" text-anchor="middle" fill="var(--slate-800)" font-weight="600" font-size="11.5">Hiện tại</text>
                    <text x="589" y="38" text-anchor="middle" fill="#2563eb" font-size="12" font-weight="700">112</text>

                    <!-- Spline Line: Completed Lesson Sessions -->
                    <path d="M 89 125 C 139 95, 139 90, 189 75 C 239 60, 239 80, 289 65 C 339 50, 339 40, 389 35 C 439 30, 439 45, 489 40 C 539 35, 539 25, 589 22" 
                          fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round"/>

                    <!-- Area Under Curve -->
                    <path d="M 89 125 C 139 95, 139 90, 189 75 C 239 60, 239 80, 289 65 C 339 50, 339 40, 389 35 C 439 30, 439 45, 489 40 C 539 35, 539 25, 589 22 L 589 165 L 89 165 Z" 
                          fill="url(#lessonsAreaGrad)"/>

                    <!-- Data dots on Curve -->
                    <circle cx="89" cy="125" r="4" fill="#10b981" stroke="#fff" stroke-width="2"/>
                    <circle cx="189" cy="75" r="4" fill="#10b981" stroke="#fff" stroke-width="2"/>
                    <circle cx="289" cy="65" r="4" fill="#10b981" stroke="#fff" stroke-width="2"/>
                    <circle cx="389" cy="35" r="4" fill="#10b981" stroke="#fff" stroke-width="2"/>
                    <circle cx="489" cy="40" r="4" fill="#10b981" stroke="#fff" stroke-width="2"/>
                    <circle cx="589" cy="22" r="5" fill="#10b981" stroke="#fff" stroke-width="2"/>
                  </svg>
                </div>
              </div>
            </div>

            <!-- Phân bổ Học viên theo Nhóm Chuyên môn (4 Cột) -->
            <div class="col-lg-4">
              <div class="admin-panel-card">
                <div class="admin-panel-header">
                  <div>
                    <div class="fw-bold text-slate-900" style="font-size: 15px;">Phân bổ Chuyên môn</div>
                    <div class="text-caption text-muted">Tỷ lệ theo lĩnh vực công nghệ</div>
                  </div>
                  <span class="badge badge-neutral">4 Chuyên ngành</span>
                </div>

                <div class="p-3">
                  <!-- Category 1: Web Dev -->
                  <div class="discipline-item">
                    <div class="discipline-header">
                      <span class="fw-semibold text-slate-800">Lập trình Web & Fullstack</span>
                      <strong class="text-slate-900">42% <span class="text-muted fw-normal">(538 SV)</span></strong>
                    </div>
                    <div class="discipline-track">
                      <div class="discipline-bar" style="width: 42%; background: #2563eb;"></div>
                    </div>
                  </div>

                  <!-- Category 2: AI & Data -->
                  <div class="discipline-item">
                    <div class="discipline-header">
                      <span class="fw-semibold text-slate-800">Khoa học Dữ liệu & AI</span>
                      <strong class="text-slate-900">28% <span class="text-muted fw-normal">(358 SV)</span></strong>
                    </div>
                    <div class="discipline-track">
                      <div class="discipline-bar" style="width: 28%; background: #8b5cf6;"></div>
                    </div>
                  </div>

                  <!-- Category 3: System & Cloud -->
                  <div class="discipline-item">
                    <div class="discipline-header">
                      <span class="fw-semibold text-slate-800">Kiến trúc Hệ thống & Cloud</span>
                      <strong class="text-slate-900">18% <span class="text-muted fw-normal">(230 SV)</span></strong>
                    </div>
                    <div class="discipline-track">
                      <div class="discipline-bar" style="width: 18%; background: #10b981;"></div>
                    </div>
                  </div>

                  <!-- Category 4: UI/UX Design -->
                  <div class="discipline-item">
                    <div class="discipline-header">
                      <span class="fw-semibold text-slate-800">Thiết kế Giao diện UI/UX</span>
                      <strong class="text-slate-900">12% <span class="text-muted fw-normal">(154 SV)</span></strong>
                    </div>
                    <div class="discipline-track">
                      <div class="discipline-bar" style="width: 12%; background: #f59e0b;"></div>
                    </div>
                  </div>

                  <div class="mt-4 p-3 rounded-2" style="background: var(--slate-50); border: 1px solid var(--slate-200); font-size: 12.5px;">
                    <div class="d-flex align-items-center gap-2 mb-1">
                      <span class="text-primary">${cmp.icon('checkCircle')}</span>
                      <strong class="text-slate-900">Hiệu quả tuyển sinh:</strong>
                    </div>
                    <div class="text-muted">
                      Nhóm ngành Web & AI chiếm 70% tổng nhu cầu đào tạo trong kỳ học này.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ===================================================================
               5. OPERATIONAL CURRICULUM PERFORMANCE & AUDIT ACTIVITY STREAM
               =================================================================== -->
          <div class="row g-3">
            <!-- Cột 7: Khóa học Tiêu biểu & Sĩ số Lớp -->
            <div class="col-lg-7">
              <div class="admin-panel-card">
                <div class="admin-panel-header">
                  <div>
                    <div class="fw-bold text-slate-900" style="font-size: 15px;">Khóa học Trọng điểm & Sĩ số Lớp</div>
                    <div class="text-caption text-muted">Theo dõi tỷ lệ lấp đầy sĩ số và chất lượng đào tạo</div>
                  </div>
                  <a href="#/admin/course-review" class="btn btn-ghost btn-sm text-primary fw-medium">
                    Toàn bộ môn học →
                  </a>
                </div>

                <div class="p-0 table-responsive">
                  <table class="lms-compact-table">
                    <thead>
                      <tr>
                        <th>Khóa học</th>
                        <th>Giảng viên</th>
                        <th>Sĩ số (Đã ghi danh)</th>
                        <th>Đánh giá</th>
                        <th class="text-end">Trạng thái</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${store.courses.slice(0, 5).map(c => {
                        const percent = c.capacity > 0 ? Math.round((c.enrolledCount / c.capacity) * 100) : 0;
                        return `
                          <tr>
                            <td>
                              <div class="d-flex align-items-center gap-2">
                                <span class="badge font-monospace" style="background: rgba(37,99,235,0.1); color: #2563eb; font-weight: 700;">
                                  ${c.code}
                                </span>
                                <span class="fw-semibold text-slate-900" style="font-size: 13px;" title="${c.title}">
                                  ${c.title.length > 30 ? c.title.substring(0, 30) + '...' : c.title}
                                </span>
                              </div>
                            </td>
                            <td>
                              <span class="text-slate-700" style="font-size: 12.5px;">${c.instructorName || 'Chưa gán'}</span>
                            </td>
                            <td style="min-width: 140px;">
                              <div class="d-flex justify-content-between text-caption mb-1">
                                <span class="fw-medium text-slate-800">${c.enrolledCount} / ${c.capacity}</span>
                                <span class="text-muted font-monospace">${percent}%</span>
                              </div>
                              <div style="height: 5px; background: var(--slate-100); border-radius: 9999px; overflow: hidden;">
                                <div style="width: ${percent}%; height: 100%; background: ${percent > 80 ? '#10b981' : percent > 40 ? '#3b82f6' : '#94a3b8'};"></div>
                              </div>
                            </td>
                            <td>
                              <span class="text-warning fw-semibold" style="font-size: 12.5px;">⭐ ${c.rating || '4.8'}</span>
                            </td>
                            <td class="text-end">
                              <span class="badge ${c.status === 'published' ? 'badge-success' : c.status === 'pending_approval' ? 'badge-warning' : 'badge-neutral'}">
                                ${c.status === 'published' ? 'Đang mở' : c.status === 'pending_approval' ? 'Chờ duyệt' : 'Bản nháp'}
                              </span>
                            </td>
                          </tr>
                        `;
                      }).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <!-- Cột 5: Dòng Thời gian Hoạt động & Nhật ký Hệ thống (Audit Stream) -->
            <div class="col-lg-5">
              <div class="admin-panel-card">
                <div class="admin-panel-header">
                  <div>
                    <div class="fw-bold text-slate-900" style="font-size: 15px;">Dòng Sự kiện Vận hành Gần đây</div>
                    <div class="text-caption text-muted">Nhật ký audit tác vụ quản trị và bảo mật</div>
                  </div>
                  <a href="#/admin/audit-log" class="btn btn-ghost btn-sm text-primary fw-medium">
                    Nhật ký đầy đủ →
                  </a>
                </div>

                <div class="admin-timeline-list">
                  <!-- Event 1: Role Update -->
                  <div class="admin-timeline-item">
                    <div class="timeline-icon-dot" style="background: rgba(37,99,235,0.1); color: #2563eb;">
                      ${cmp.icon('user')}
                    </div>
                    <div class="timeline-content-box">
                      <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-bold text-slate-900" style="font-size: 13px;">Cấp quyền Quản trị Nội dung</span>
                        <span class="text-caption text-muted font-monospace">12:45 Hôm nay</span>
                      </div>
                      <div class="text-caption text-muted">
                        <strong>Lê Thu Hà (Admin)</strong> cấp quyền Quản trị Ngân hàng câu hỏi cho GV <em>Vũ Đức Thịnh</em>.
                      </div>
                    </div>
                  </div>

                  <!-- Event 2: Assessment Published -->
                  <div class="admin-timeline-item">
                    <div class="timeline-icon-dot" style="background: rgba(16,185,129,0.1); color: #10b981;">
                      ${cmp.icon('checkCircle')}
                    </div>
                    <div class="timeline-content-box">
                      <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-bold text-slate-900" style="font-size: 13px;">Xuất bản Đề thi Giữa kỳ</span>
                        <span class="text-caption text-muted font-monospace">11:20 Hôm nay</span>
                      </div>
                      <div class="text-caption text-muted">
                        GV <strong>Trần Hoàng Nam</strong> xuất bản đề thi PWD301 và kích hoạt khóa bảo mật thời gian.
                      </div>
                    </div>
                  </div>

                  <!-- Event 3: Disciplinary Action -->
                  <div class="admin-timeline-item">
                    <div class="timeline-icon-dot" style="background: rgba(239,68,68,0.1); color: #ef4444;">
                      ${cmp.icon('alertTriangle')}
                    </div>
                    <div class="timeline-content-box">
                      <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-bold text-danger" style="font-size: 13px;">Tạm ngưng Tài khoản Thi</span>
                        <span class="text-caption text-muted font-monospace">09:12 Hôm nay</span>
                      </div>
                      <div class="text-caption text-muted">
                        Đình chỉ tạm thời học viên <strong>Hoàng Bảo Ngọc</strong> do nghi vấn gian lận thi cử.
                      </div>
                    </div>
                  </div>

                  <!-- Event 4: AI Security Guardrail -->
                  <div class="admin-timeline-item">
                    <div class="timeline-icon-dot" style="background: rgba(139,92,246,0.1); color: #8b5cf6;">
                      ${cmp.icon('shield')}
                    </div>
                    <div class="timeline-content-box">
                      <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-bold text-slate-900" style="font-size: 13px;">AI Guardrail Ngăn chặn Injection</span>
                        <span class="text-caption text-muted font-monospace">03:14 Sáng nay</span>
                      </div>
                      <div class="text-caption text-muted">
                        Tường lửa AI vô hiệu hóa thành công 1 nỗ lực Jailbreak "Ignore previous instructions".
                      </div>
                    </div>
                  </div>

                  <!-- Event 5: Automated Backup -->
                  <div class="admin-timeline-item">
                    <div class="timeline-icon-dot" style="background: rgba(100,116,139,0.1); color: #64748b;">
                      ${cmp.icon('database')}
                    </div>
                    <div class="timeline-content-box">
                      <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-bold text-slate-900" style="font-size: 13px;">Sao lưu Hệ thống Định kỳ</span>
                        <span class="text-caption text-muted font-monospace">Hôm qua 16:30</span>
                      </div>
                      <div class="text-caption text-muted">
                        Bản sao lưu toàn vẹn 4.2 GB đã được nén và mã hóa thành công vào kho lưu trữ an toàn.
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ===================================================================
               6. COMPACT SYSTEM RELIABILITY STRIP (REPLACES NOISY SERVER HARDWARE)
               =================================================================== -->
          <div class="system-summary-strip">
            <div class="d-flex align-items-center gap-3">
              <div class="d-flex align-items-center gap-2">
                <span class="live-pulse-dot"></span>
                <span class="fw-bold text-slate-900" style="font-size: 13.5px;">Hạ tầng Đào tạo:</span>
                <span class="badge badge-success" style="font-size: 12px;">100% Sẵn sàng • Uptime 99.98%</span>
              </div>
            </div>

            <!-- 4 Essential Service Status Chips -->
            <div class="d-flex flex-wrap align-items-center gap-2">
              <div class="infra-metric-chip" title="Cơ sở dữ liệu quan hệ">
                ${cmp.icon('database')}
                <span>Cơ sở dữ liệu: <strong class="text-slate-900">4ms • Tải 18%</strong></span>
              </div>
              <div class="infra-metric-chip" title="Tiến trình xử lý nền">
                ${cmp.icon('clock')}
                <span>Celery Workers: <strong class="text-slate-900">3 hoạt động</strong></span>
              </div>
              <div class="infra-metric-chip" title="Trợ lý thông minh AI">
                ${cmp.icon('sparkles')}
                <span>Gemini RAG: <strong class="text-slate-900">320ms • Sẵn sàng</strong></span>
              </div>
              <div class="infra-metric-chip" title="Quét tệp an toàn">
                ${cmp.icon('shield')}
                <span>Quét tài liệu: <strong class="text-slate-900">1,420 tệp an toàn</strong></span>
              </div>
            </div>

            <!-- Link to Dedicated In-Depth NOC / SOC Page -->
            <div>
              <a href="#/admin/system-health" class="btn btn-sm btn-outline-primary fw-medium px-3 py-1">
                Chi tiết Giám sát Hạ tầng (NOC) →
              </a>
            </div>
          </div>

        </div>
      `;
    },

    // -------------------------------------------------------------------------
    // DASHBOARD QUICK ACTIONS & EVENT HANDLERS
    // -------------------------------------------------------------------------
    filterAnalytics(range) {
      const btns = document.querySelectorAll('.chart-filter-btn');
      btns.forEach(b => b.classList.remove('active'));
      if (event && event.target) {
        event.target.classList.add('active');
      }
      const label = range === '7d' ? '7 ngày gần nhất' : range === '30d' ? '30 ngày qua' : 'Học kỳ Fall 2026';
      if (window.PWD.components) {
        window.PWD.components.showToast(`Đã lọc dữ liệu biểu đồ phân tích theo: ${label}`, 'info');
      }
    },

    exportKPISummary() {
      if (window.PWD.components) {
        window.PWD.components.showToast('Đang xuất báo cáo tổng hợp KPI đào tạo và vận hành (PDF / Excel)...', 'info');
        setTimeout(() => {
          window.PWD.components.showToast('Báo cáo "PWD301_Academic_KPI_Fall2026.pdf" đã được tạo thành công!', 'success');
        }, 600);
      }
    },

    refreshDashboardData() {
      const icon = document.getElementById('icon-refresh-dash');
      if (icon) icon.classList.add('refresh-spin-anim');

      // Randomly fluctuate hardware & network telemetry values slightly for live simulation
      const store = window.PWD.store.state;
      if (store.admin && store.admin.serverTelemetry) {
        const tel = store.admin.serverTelemetry;
        // CPU jitter
        const cpuDelta = (Math.random() * 4 - 2);
        tel.cpu.usagePercent = Math.max(12, Math.min(88, +(tel.cpu.usagePercent + cpuDelta).toFixed(1)));

        // RAM jitter
        const ramDelta = (Math.random() * 0.6 - 0.3);
        tel.ram.usedGB = Math.max(10, Math.min(28, +(tel.ram.usedGB + ramDelta).toFixed(1)));
        tel.ram.usagePercent = +((tel.ram.usedGB / tel.ram.totalGB) * 100).toFixed(1);
        tel.ram.availableGB = +(tel.ram.totalGB - tel.ram.usedGB).toFixed(1);

        // Network jitter
        tel.network.downloadSpeed = `${(130 + Math.random() * 28).toFixed(1)} Mbps`;
        tel.network.uploadSpeed = `${(360 + Math.random() * 45).toFixed(1)} Mbps`;
        tel.network.latency = `${(2.6 + Math.random() * 1.2).toFixed(1)} ms`;
        tel.network.packetsPerSec = `${(26 + Math.random() * 5).toFixed(1)}k pkt/s`;
      }

      setTimeout(() => {
        if (window.PWD.components) {
          window.PWD.components.showToast('Đã làm mới thông số tài nguyên phần cứng máy chủ & băng thông mạng!', 'success');
        }
        window.PWD.router.handleRouting();
      }, 400);
    },

    refreshTelemetry() {
      // Kept for backward compatibility
      if (window.PWD.components) {
        window.PWD.components.showToast('Đã đồng bộ telemetry hệ thống.', 'success');
      }
      window.PWD.router.handleRouting();
    },

    quickApproveInstructor(appId) {
      const store = window.PWD.store.state;
      const idx = store.admin.instructorApplications.findIndex(a => a.id === appId);
      if (idx !== -1) {
        const app = store.admin.instructorApplications[idx];
        store.admin.instructorApplications.splice(idx, 1);
        window.PWD.store.persist();
        window.PWD.components.showToast(`Đã phê duyệt đơn đăng ký giảng viên của: ${app.name}!`, 'success');
        window.PWD.router.handleRouting();
      }
    },

    quickRejectInstructor(appId) {
      const store = window.PWD.store.state;
      const idx = store.admin.instructorApplications.findIndex(a => a.id === appId);
      if (idx !== -1) {
        const app = store.admin.instructorApplications[idx];
        store.admin.instructorApplications.splice(idx, 1);
        window.PWD.store.persist();
        window.PWD.components.showToast(`Đã từ chối đơn của ứng viên: ${app.name}.`, 'info');
        window.PWD.router.handleRouting();
      }
    },

    quickApproveCourse(courseCode) {
      const store = window.PWD.store.state;
      const course = store.courses.find(c => c.code === courseCode);
      if (course) {
        course.status = 'published';
        window.PWD.store.persist();
      }
      window.PWD.components.showToast(`Đã phê duyệt và ban hành giáo trình môn ${courseCode} thành công!`, 'success');
      window.PWD.router.handleRouting();
    },


    // 2. User Management (Scenario 10: Suspend & Reactivate)
    users() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Quản lý Người dùng',
          subtitle: 'Danh sách tài khoản sinh viên, giảng viên và quản trị viên',
          primaryAction: `<a href="#/admin/course-reassignment" class="btn btn-secondary btn-sm">Chuyển quyền khóa học</a>`
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Họ và tên</th>
                  <th>Email</th>
                  <th>Vai trò</th>
                  <th>Trạng thái</th>
                  <th>Ngày tham gia</th>
                  <th class="text-end">Hành động</th>
                </tr>
              </thead>
              <tbody>
                ${store.admin.users.map(u => `
                  <tr>
                    <td>
                      <div class="fw-medium">${u.name}</div>
                      <div class="text-caption text-muted">ID: ${u.id}</div>
                    </td>
                    <td>${u.email}</td>
                    <td>
                      <span class="badge ${u.role === 'ADMIN' ? 'badge-danger' : u.role === 'INSTRUCTOR' ? 'badge-warning' : 'badge-neutral'}">
                        ${u.role}
                      </span>
                    </td>
                    <td>
                      ${u.status === 'active' ? cmp.badge('success', 'Hoạt động') : cmp.badge('danger', 'Tạm ngưng')}
                    </td>
                    <td class="text-caption">${u.joinedAt}</td>
                    <td class="text-end">
                      <div class="table-actions">
                        <a href="#/admin/user-detail/${u.id}" class="btn btn-ghost btn-sm" title="Chi tiết">${cmp.icon('eye')}</a>
                        ${u.status === 'active' ? `
                          <button class="btn btn-outline-danger btn-sm" onclick="PWD.views.admin.openSuspendModal('${u.id}', '${u.name}')">
                            Khóa tài khoản
                          </button>
                        ` : `
                          <button class="btn btn-secondary btn-sm" onclick="PWD.views.admin.reactivateUser('${u.id}')">
                            Kích hoạt lại
                          </button>
                        `}
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 6. Suspension Modal Trigger (Scenario 10)
    openSuspendModal(userId, userName) {
      window.PWD.components.openSensitiveActionModal({
        title: `Tạm ngưng tài khoản: ${userName}`,
        actionDescription: `
          Tài khoản sau khi tạm ngưng sẽ bị <strong>hủy bỏ phiên làm việc ngay lập tức</strong> và không thể đăng nhập cho đến khi quản trị viên mở khóa.
        `,
        requiredPhrase: 'TẠM NGƯNG TÀI KHOẢN',
        confirmButtonText: 'Xác nhận khóa tài khoản',
        onConfirm: ({ reason }) => {
          window.PWD.store.suspendUser(userId, reason);
          window.PWD.components.showToast(`Đã tạm ngưng tài khoản ${userName} và lưu Audit Log.`, 'success');
          window.PWD.router.handleRouting();
        }
      });
    },

    reactivateUser(userId) {
      window.PWD.store.reactivateUser(userId);
      window.PWD.components.showToast('Đã kích hoạt lại tài khoản thành công.', 'success');
      window.PWD.router.handleRouting();
    },

    // 3. User Detail
    userDetail(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const u = store.admin.users.find(x => x.id === params.id) || store.admin.users[0];

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: `Chi tiết Tài khoản: ${u.name}`,
            subtitle: `ID: ${u.id} • Vai trò: ${u.role}`,
            breadcrumbs: [
              { label: 'Người dùng', href: '#/admin/users' },
              { label: u.name, href: `#/admin/user-detail/${u.id}` }
            ]
          })}

          <div class="card mb-4">
            <div class="card-header">
              <h5 class="sub-title m-0">Thông tin định danh</h5>
            </div>
            <div class="card-body">
              <div class="row g-3 mb-3">
                <div class="col-sm-6">
                  <div class="text-caption text-muted">Họ và tên</div>
                  <div class="fw-medium">${u.name}</div>
                </div>
                <div class="col-sm-6">
                  <div class="text-caption text-muted">Địa chỉ email</div>
                  <div class="fw-medium">${u.email}</div>
                </div>
              </div>

              <div class="row g-3 mb-3">
                <div class="col-sm-6">
                  <div class="text-caption text-muted">Trạng thái hoạt động</div>
                  <div class="mt-1">${u.status === 'active' ? cmp.badge('success', 'Đang hoạt động') : cmp.badge('danger', 'Đang bị tạm ngưng')}</div>
                </div>
                <div class="col-sm-6">
                  <div class="text-caption text-muted">Ngày đăng ký</div>
                  <div class="fw-medium">${u.joinedAt}</div>
                </div>
              </div>

              ${u.suspensionReason ? `
                <div class="alert-card alert-card-danger mt-3">
                  <span style="flex-shrink:0;">${cmp.icon('alertTriangle')}</span>
                  <div>
                    <strong>Lý do tạm ngưng:</strong>
                    <div class="text-caption mt-1">${u.suspensionReason}</div>
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    },

    // 4. Instructor Approvals
    instructorApprovals() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Duyệt Đơn Đăng ký Giảng viên',
          subtitle: 'Xét duyệt hồ sơ chuyên môn của các ứng viên giảng dạy mới'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Họ và tên</th>
                  <th>Khoa / Đơn vị</th>
                  <th>Chuyên môn giảng dạy</th>
                  <th>Ngày nộp</th>
                  <th class="text-end">Quyết định</th>
                </tr>
              </thead>
              <tbody>
                ${store.admin.instructorApplications.map(app => `
                  <tr>
                    <td>
                      <div class="fw-medium">${app.name}</div>
                      <div class="text-caption text-muted">${app.email}</div>
                    </td>
                    <td>${app.department}</td>
                    <td>${app.expertise}</td>
                    <td class="text-caption">${app.submittedAt}</td>
                    <td class="text-end">
                      <div class="table-actions">
                        <button class="btn btn-primary btn-sm" onclick="PWD.components.showToast('Phê duyệt hồ sơ giảng viên thành công!', 'success')">Chấp thuận</button>
                        <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Từ chối hồ sơ.', 'info')">Từ chối</button>
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 5. Role Management
    roleManagement() {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Phân quyền & Vai trò (RBAC)',
            subtitle: 'Cấu trúc quyền hạn hệ thống PWD301'
          })}

          <div class="card">
            <div class="card-body p-0">
              <table class="app-table">
                <thead>
                  <tr>
                    <th>Vai trò</th>
                    <th>Phạm vi quyền hạn</th>
                    <th>Ghi chú</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><span class="badge badge-neutral">STUDENT</span></td>
                    <td>Khám phá khóa học, ghi danh, học bài, làm bài thi, xem kết quả, dùng AI Assistant.</td>
                    <td class="text-caption text-muted">Quyền mặc định khi đăng ký tài khoản.</td>
                  </tr>
                  <tr>
                    <td><span class="badge badge-warning">INSTRUCTOR</span></td>
                    <td>Quản lý khóa học, soạn bài giảng, ngân hàng câu hỏi, tạo đề thi, chấm bài tự luận.</td>
                    <td class="text-caption text-muted">Bao gồm toàn bộ quyền của Student.</td>
                  </tr>
                  <tr>
                    <td><span class="badge badge-danger">ADMIN</span></td>
                    <td>Quản trị người dùng, duyệt giảng viên, kiểm soát an ninh, audit log, sao lưu & phục hồi.</td>
                    <td class="text-caption text-muted">Bao gồm quyền Instructor + Student; Không có impersonate.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      `;
    },

    // 7. Course Review (Material Change Approval)
    courseReview() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Kiểm duyệt Thay đổi Khóa học',
          subtitle: 'Phê duyệt các thay đổi lớn về đề cương môn học đã xuất bản'
        })}

        <div class="card">
          <div class="card-body p-4">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <span class="text-caption fw-bold text-primary">DSD401</span>
                <h4 class="sub-title mb-1">Thiết kế Hệ thống Phân tán (Distributed Systems)</h4>
                <div class="text-caption text-muted">Giảng viên: Trần Hoàng Nam • Gửi duyệt ngày 06/09/2026</div>
              </div>
              <span class="badge badge-warning">Chờ Admin duyệt</span>
            </div>

            <div class="p-3 bg-slate-50 border border-slate-200 rounded mb-4">
              <div class="fw-medium text-slate-800 mb-1">Ghi chú thay đổi của giảng viên:</div>
              <p class="text-caption text-slate-600 m-0">
                "Cập nhật 40% syllabus môn học, bổ sung chuyên đề Raft Consensus Algorithm và điều chỉnh cấu trúc tính điểm tổng kết môn."
              </p>
            </div>

            <div class="d-flex gap-2">
              <button class="btn btn-primary btn-sm" onclick="PWD.components.showToast('Đã phê duyệt thay đổi khóa học DSD401!', 'success')">Phê duyệt áp dụng</button>
              <button class="btn btn-secondary btn-sm" onclick="PWD.components.showToast('Yêu cầu giảng viên chỉnh sửa lại nội dung.', 'info')">Yêu cầu hiệu chỉnh</button>
            </div>
          </div>
        </div>
      `;
    },

    // 8. Course Reassignment (Scenario 11)
    courseReassignment() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const instructors = store.admin.users.filter(u => u.role === 'INSTRUCTOR');

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Chuyển quyền Quản lý Khóa học (Course Reassignment)',
            subtitle: 'Chuyển quyền sở hữu và phụ trách môn học sang giảng viên khác'
          })}

          <div class="card">
            <div class="card-body">
              <form onsubmit="event.preventDefault(); PWD.views.admin.handleReassign();">
                <div class="form-group mb-3">
                  <label class="form-label">Chọn khóa học cần chuyển quyền <span class="required">*</span></label>
                  <select id="reassign-course" class="form-select form-select-sm">
                    ${store.courses.map(c => `
                      <option value="${c.id}">${c.code} — ${c.title} (Hiện tại: ${c.instructorName})</option>
                    `).join('')}
                  </select>
                </div>

                <div class="form-group mb-3">
                  <label class="form-label">Giảng viên tiếp nhận mới <span class="required">*</span></label>
                  <select id="reassign-instructor" class="form-select form-select-sm">
                    ${instructors.map(ins => `
                      <option value="${ins.id}">${ins.name} (${ins.email})</option>
                    `).join('')}
                  </select>
                </div>

                <div class="form-group mb-4">
                  <label class="form-label">Lý do điều chuyển bắt buộc <span class="required">*</span></label>
                  <textarea id="reassign-reason" class="form-control form-control-sm" rows="3" required placeholder="Ghi rõ căn cứ quyết định chuyển quyền để lưu vào Audit Log..."></textarea>
                </div>

                <div class="d-flex justify-content-between border-top border-slate-200 pt-3">
                  <a href="#/admin/users" class="btn btn-secondary btn-sm">Hủy bỏ</a>
                  <button type="submit" class="btn btn-primary btn-sm">Xác nhận chuyển quyền</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    handleReassign() {
      const courseId = document.getElementById('reassign-course')?.value;
      const newInstId = document.getElementById('reassign-instructor')?.value;
      const reason = document.getElementById('reassign-reason')?.value || 'Điều chuyển nhân sự giảng dạy';

      window.PWD.store.reassignCourseOwner(courseId, newInstId, reason);
      window.PWD.components.showToast('Đã chuyển quyền sở hữu khóa học và ghi nhận vào Audit Log!', 'success');
      window.PWD.router.navigate('#/admin/audit-log');
    },

    // 9. Security Center
    securityCenter() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Trung tâm Bảo mật Hệ thống',
          subtitle: 'Giám sát phòng thủ, bảo vệ phiên và ngăn ngừa gian lận thi cử'
        })}

        <div class="row g-3 mb-4">
          <div class="col-md-4">${cmp.statCard('Chính sách Cookie', 'HttpOnly + SameSite=Lax', 'Phòng chống XSS & CSRF', 'shield')}</div>
          <div class="col-md-4">${cmp.statCard('Kiểm soát phiên thi', 'Single Active Lease', 'Chống làm bài đồng thời', 'lock')}</div>
          <div class="col-md-4">${cmp.statCard('Bảo vệ AI Assistant', 'Prompt-Injection Guard', 'Ngăn chặn rò rỉ prompt', 'sparkles')}</div>
        </div>

        <div class="card">
          <div class="card-header">
            <h5 class="sub-title m-0">Các cơ chế bảo vệ cốt lõi đang kích hoạt</h5>
          </div>
          <div class="card-body p-0">
            <ul class="list-group list-group-flush">
              <li class="list-group-item d-flex align-items-center gap-3 py-3">
                <span class="text-success">${cmp.icon('checkCircle')}</span>
                <div>
                  <div class="fw-medium">Không lưu JWT vào LocalStorage cho giao diện Web (Invariant 1)</div>
                  <div class="text-caption text-muted">Toàn bộ phiên làm việc của trình duyệt sử dụng Flask Cookie Session an toàn.</div>
                </div>
              </li>
              <li class="list-group-item d-flex align-items-center gap-3 py-3">
                <span class="text-success">${cmp.icon('checkCircle')}</span>
                <div>
                  <div class="fw-medium">Cơ chế khóa đề thi khi đã có sinh viên bắt đầu làm (Invariant 14)</div>
                  <div class="text-caption text-muted">Bảo toàn vẹn cấu trúc câu hỏi và thang điểm số.</div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      `;
    },

    // 10. Security Events
    securityEvents() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Nhật ký Sự kiện An ninh',
          subtitle: 'Theo dõi các hành vi đáng ngờ và các cuộc tấn công bị ngăn chặn'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Thời điểm</th>
                  <th>Loại sự kiện</th>
                  <th>Mức độ</th>
                  <th>Mô tả chi tiết</th>
                  <th>Địa chỉ IP</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                ${store.admin.securityEvents.map(sec => `
                  <tr>
                    <td class="text-caption">${sec.timestamp}</td>
                    <td class="fw-medium">${sec.type}</td>
                    <td><span class="badge ${sec.severity === 'high' ? 'badge-danger' : 'badge-warning'}">${sec.severity.toUpperCase()}</span></td>
                    <td class="text-caption">${sec.details}</td>
                    <td class="font-monospace text-caption">${sec.ip}</td>
                    <td>${cmp.badge('success', 'Đã chặn')}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 11. AI Security
    aiSecurity() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Giám sát An toàn AI (Prompt-Injection Monitoring)',
          subtitle: 'Ngăn chặn tấn công chiếm quyền điều khiển prompt và lạm dụng trợ lý ảo'
        })}

        <div class="card mb-4">
          <div class="card-header">
            <h5 class="sub-title m-0">Chính sách Bảo vệ Trợ lý AI</h5>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-6">
                <div class="p-3 bg-slate-50 border border-slate-200 rounded">
                  <div class="fw-medium text-slate-900 mb-1">Quy định truy xuất RAG (Invariant 20)</div>
                  <p class="text-caption text-muted m-0">RAG chỉ truy xuất dữ liệu từ các khóa học đang mở mà học viên đã ghi danh. Tuyệt đối không truy xuất tài liệu lưu trữ lịch sử hoặc tài liệu bản nháp.</p>
                </div>
              </div>
              <div class="col-md-6">
                <div class="p-3 bg-slate-50 border border-slate-200 rounded">
                  <div class="fw-medium text-slate-900 mb-1">Tự động hủy ngữ cảnh hội thoại (Invariant 21)</div>
                  <p class="text-caption text-muted m-0">Toàn bộ nội dung trò chuyện của học viên với AI sẽ tự động hủy sạch khỏi RAM sau 5 phút không hoạt động để bảo vệ quyền riêng tư.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 12. Audit Log
    auditLog() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Nhật ký Kiểm toán Hệ thống (Audit Log)',
          subtitle: 'Bản ghi bất biến (Immutable Audit Trail) ghi lại mọi thao tác nhạy cảm'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Thời điểm</th>
                  <th>Người thực hiện</th>
                  <th>Hành động</th>
                  <th>Đối tượng</th>
                  <th>Chi tiết</th>
                  <th>Kết quả</th>
                </tr>
              </thead>
              <tbody>
                ${store.admin.auditEvents.map(aud => `
                  <tr>
                    <td class="text-caption" style="white-space: nowrap;">${aud.timestamp}</td>
                    <td class="fw-medium">${aud.actor}</td>
                    <td><span class="badge badge-info">${aud.action}</span></td>
                    <td class="text-caption">${aud.target}</td>
                    <td class="text-caption" style="max-width: 320px;">${aud.details}</td>
                    <td>${cmp.badge('success', aud.status)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 13. Audit Detail
    auditDetail(params) {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const aud = store.admin.auditEvents[0];

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: `Chi tiết Bản ghi Kiểm toán: ${aud.id}`,
            subtitle: `Thời điểm: ${aud.timestamp}`,
            breadcrumbs: [
              { label: 'Audit Log', href: '#/admin/audit-log' },
              { label: aud.id, href: `#/admin/audit-detail/${aud.id}` }
            ]
          })}

          <div class="card">
            <div class="card-body">
              <pre class="bg-slate-900 text-slate-100 p-3 rounded text-caption font-monospace">${JSON.stringify(aud, null, 2)}</pre>
            </div>
          </div>
        </div>
      `;
    },

    // 14. Storage Monitoring
    storage() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Giám sát Dung lượng Lưu trữ',
          subtitle: 'Quản lý tài nguyên lưu trữ bài giảng, video và thư mục cách ly ClamAV'
        })}

        <div class="row g-3 mb-4">
          <div class="col-md-4">${cmp.statCard('Dung lượng đã dùng', '142.5 GB / 500 GB', '28.5% quota', 'database')}</div>
          <div class="col-md-4">${cmp.statCard('Tệp tin bài giảng', '1,420 tệp', 'Slide, PDF, ZIP', 'fileText')}</div>
          <div class="col-md-4">${cmp.statCard('Tệp cách ly mã độc', '1 tệp', 'lab_assignment.docm', 'shield')}</div>
        </div>
      `;
    },

    // 15. File / Scanner Status
    scannerStatus() {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Trạng thái Máy quét ClamAV',
            subtitle: 'Chính sách bảo mật Fail-Closed: tệp chưa quét không được phép kích hoạt'
          })}

          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center gap-3 mb-3">
                <span class="text-success">${cmp.icon('checkCircle')}</span>
                <div>
                  <div class="fw-bold">ClamAV Antivirus Daemon đang hoạt động</div>
                  <div class="text-caption text-muted">Cập nhật mẫu virus mới nhất lúc 04:00 hôm nay.</div>
                </div>
              </div>
              <p class="text-caption text-slate-600 m-0">
                Toàn bộ các tệp tin người dùng tải lên được đẩy vào hàng đợi quét trước khi lưu trữ chính thức. Nếu máy quét gặp sự cố, hệ thống áp dụng cơ chế fail-closed (từ chối kích hoạt tệp) để đảm bảo an toàn tuyệt đối.
              </p>
            </div>
          </div>
        </div>
      `;
    },

    // 16. Background Jobs
    jobs() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Tiến trình Chạy nền (Celery Jobs)',
          subtitle: 'Theo dõi hàng đợi đồng bộ điểm, tính toán ma trận và nén dữ liệu'
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Tên tiến trình</th>
                  <th>Tiến độ</th>
                  <th>Trạng thái</th>
                  <th>Thời gian bắt đầu</th>
                </tr>
              </thead>
              <tbody>
                ${store.admin.backgroundJobs.map(job => `
                  <tr>
                    <td class="fw-medium">${job.name}</td>
                    <td>${cmp.progressBar(job.progress, job.status === 'completed')}</td>
                    <td>
                      ${job.status === 'completed' ? cmp.badge('success', 'Hoàn tất') : job.status === 'running' ? cmp.badge('info', 'Đang chạy') : cmp.badge('neutral', 'Chờ xử lý')}
                    </td>
                    <td class="text-caption">${job.startedAt || 'Chưa bắt đầu'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 17. System Health (Interactive Degraded Toggle for Demo - Scenario 12)
    systemHealth() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;
      const h = store.admin.systemHealth;

      return `
        ${cmp.pageHeader({
          title: 'Sức khỏe Dịch vụ Hệ thống',
          subtitle: 'Kiểm tra độ trễ, tải xử lý và trạng thái kết nối các dịch vụ'
        })}

        <div class="p-3 mb-4 bg-slate-100 border border-slate-300 rounded d-flex justify-content-between align-items-center">
          <span class="fw-bold text-slate-700">Mô phỏng sự cố dịch vụ (Demo Control):</span>
          <button class="btn btn-sm ${h.scanner.status === 'healthy' ? 'btn-secondary' : 'btn-danger'}" onclick="PWD.views.admin.toggleHealthDegraded()">
            ${h.scanner.status === 'healthy' ? 'Mô phỏng: Dịch vụ Scanner bị suy giảm (Degraded)' : 'Khôi phục: Toàn bộ dịch vụ Khỏe mạnh (Healthy)'}
          </button>
        </div>

        <div class="row g-4">
          <div class="col-md-6">
            <div class="card">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <h5 class="sub-title m-0">${h.database.name}</h5>
                  ${cmp.badge('success', 'Healthy')}
                </div>
                <div class="text-caption text-muted">Độ trễ: 4ms • Tải CPU: 18% • Bộ nhớ: 4.2 GB</div>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <h5 class="sub-title m-0">${h.workers.name}</h5>
                  ${cmp.badge('success', 'Healthy')}
                </div>
                <div class="text-caption text-muted">Active Workers: 4 • Queue Size: 0 • Tác vụ chạy nền bình thường</div>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <h5 class="sub-title m-0">${h.scanner.name}</h5>
                  ${cmp.badge(h.scanner.status === 'healthy' ? 'success' : 'warning', h.scanner.status.toUpperCase())}
                </div>
                <div class="text-caption text-muted">
                  ${h.scanner.status === 'healthy' ? 'Hoạt động bình thường • Quét 1,420 tệp an toàn' : 'Cảnh báo: Thời gian quét bị trễ 45s do tải cao (Degraded)'}
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <h5 class="sub-title m-0">${h.geminiRag.name}</h5>
                  ${cmp.badge('success', 'Healthy')}
                </div>
                <div class="text-caption text-muted">Thời gian phản hồi API: 320ms • Quota sử dụng: 18%</div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    toggleHealthDegraded() {
      const h = window.PWD.store.state.admin.systemHealth.scanner;
      h.status = h.status === 'healthy' ? 'degraded' : 'healthy';
      window.PWD.store.persist();
      window.PWD.components.showToast(`Trạng thái máy quét đã chuyển thành: ${h.status.toUpperCase()}`, 'info');
      window.PWD.router.handleRouting();
    },

    // 18. Backup History
    backupHistory() {
      const store = window.PWD.store.state;
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Sao lưu & Phục hồi Dữ liệu',
          subtitle: 'Quản lý các bản sao lưu hệ thống toàn vẹn định kỳ',
          primaryAction: `<button class="btn btn-primary btn-sm" onclick="PWD.views.admin.createBackup()">+ Tạo bản sao lưu mới</button>`
        })}

        <div class="card">
          <div class="card-body p-0">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Tên bản sao lưu</th>
                  <th>Dung lượng</th>
                  <th>Loại</th>
                  <th>Thời điểm tạo</th>
                  <th>Trạng thái</th>
                  <th class="text-end">Phục hồi</th>
                </tr>
              </thead>
              <tbody>
                ${store.admin.backups.map(bk => `
                  <tr>
                    <td class="fw-medium font-monospace">${bk.filename}</td>
                    <td>${bk.size}</td>
                    <td class="text-caption">${bk.type}</td>
                    <td class="text-caption">${bk.createdAt}</td>
                    <td>${cmp.badge('success', 'Thành công')}</td>
                    <td class="text-end">
                      <button class="btn btn-outline-danger btn-sm" onclick="PWD.views.admin.openRestoreModal('${bk.id}', '${bk.filename}')">
                        Phục hồi dữ liệu
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    createBackup() {
      window.PWD.store.createBackupRun();
      window.PWD.components.showToast('Đã khởi tạo thành công bản sao lưu thủ công mới!', 'success');
      window.PWD.router.handleRouting();
    },

    // 20. Restore Confirmation UI (Scenario 12: Sensitive Action)
    openRestoreModal(bkId, filename) {
      window.PWD.components.openSensitiveActionModal({
        title: `Phục hồi hệ thống từ bản sao lưu: ${filename}`,
        actionDescription: `
          <strong>CẢNH BÁO TỐI KHẨN CẤP:</strong> Thao tác phục hồi sẽ đưa toàn bộ cơ sở dữ liệu về thời điểm sao lưu. 
          Mọi dữ liệu sinh viên nộp bài sau thời điểm này sẽ bị ghi đè. Hệ thống sẽ tạm dừng hoạt động trong thời gian nạp lại dữ liệu.
        `,
        requiredPhrase: 'KHÔI PHỤC DỮ LIỆU',
        confirmButtonText: 'Xác nhận khôi phục hệ thống',
        onConfirm: ({ reason }) => {
          window.PWD.store.restoreSystemBackup(bkId, reason);
          window.PWD.components.showToast('Phục hồi dữ liệu thành công! Bản ghi đã được ghi vào Audit Log.', 'success');
          window.PWD.router.navigate('#/admin/audit-log');
        }
      });
    },

    // 21. Alerts Center
    alerts() {
      const cmp = window.PWD.components;

      return `
        ${cmp.pageHeader({
          title: 'Trung tâm Cảnh báo Kỹ thuật',
          subtitle: 'Các cảnh báo bất thường về hiệu năng và an ninh hệ thống'
        })}

        <div class="card">
          <div class="card-body p-0">
            <ul class="list-group list-group-flush">
              <li class="list-group-item p-4 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-3">
                  <span class="text-warning">${cmp.icon('alertTriangle')}</span>
                  <div>
                    <div class="fw-medium">Cảnh báo tải dung lượng lưu trữ thư mục tạm</div>
                    <div class="text-caption text-muted">Dung lượng bộ đệm video bài giảng đạt 78% ngưỡng cảnh báo.</div>
                  </div>
                </div>
                <span class="text-caption text-muted">15 phút trước</span>
              </li>
            </ul>
          </div>
        </div>
      `;
    },

    // 22. Settings & Demo Reset
    settings() {
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Cài đặt Hệ thống & Tùy chọn Demo',
            subtitle: 'Tham số cấu hình phiên làm việc và công cụ quản lý dữ liệu demo'
          })}

          <div class="card mb-4">
            <div class="card-header">
              <h5 class="sub-title m-0">Cấu hình thời gian & Bảo mật</h5>
            </div>
            <div class="card-body">
              <div class="form-group mb-3">
                <label class="form-label">Thời gian hết hạn phiên làm việc (Session Timeout)</label>
                <input type="text" class="form-control form-control-sm" value="30 phút không hoạt động" readonly>
              </div>
              <div class="form-group mb-0">
                <label class="form-label">Giới hạn dung lượng tệp tin tải lên</label>
                <input type="text" class="form-control form-control-sm" value="Tài liệu: 50MB • Video bài giảng: 1GB" readonly>
              </div>
            </div>
          </div>

          <!-- Reset Demo Data Action -->
          <div class="card border-danger">
            <div class="card-header bg-danger-subtle">
              <h5 class="sub-title m-0 text-danger">Quản lý Dữ liệu Mẫu Demo (Reset Demo Data)</h5>
            </div>
            <div class="card-body">
              <p class="text-caption text-slate-700 mb-3">
                Đặt lại toàn bộ dữ liệu demo (khóa học, bài nộp, ngân hàng câu hỏi, kiểm toán) về trạng thái hạt giống ban đầu (Initial Seed).
              </p>
              <button class="btn btn-outline-danger btn-sm" onclick="PWD.views.admin.confirmResetDemo()">
                Đặt lại toàn bộ dữ liệu demo
              </button>
            </div>
          </div>
        </div>
      `;
    },

    confirmResetDemo() {
      window.PWD.components.openConfirmModal({
        title: 'Đặt lại dữ liệu demo',
        message: 'Bạn có chắc chắn muốn xóa dữ liệu chỉnh sửa cục bộ và đưa hệ thống về trạng thái mẫu ban đầu?',
        confirmText: 'Đặt lại ngay',
        confirmBtnClass: 'btn-danger',
        onConfirm: () => {
          window.PWD.store.resetDemoData();
          window.location.reload();
        }
      });
    },

    // 23. Admin Profile
    profile() {
      const user = window.PWD.store.getCurrentUser() || window.PWD.store.state.personas.admin;
      const cmp = window.PWD.components;

      return `
        <div class="content-narrow">
          ${cmp.pageHeader({
            title: 'Hồ sơ Quản trị viên',
            subtitle: 'Thông tin tài khoản quyền Root'
          })}

          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center gap-3 mb-4">
                <div class="topbar-brand-mark fs-4" style="width: 54px; height: 54px; background: var(--color-danger);">${user.avatar}</div>
                <div>
                  <h4 class="sub-title m-0">${user.name}</h4>
                  <div class="text-caption text-muted">${user.email} • Vai trò: Quản trị viên Tối cao</div>
                </div>
              </div>

              <div class="form-group mb-3">
                <label class="form-label">Tài khoản Quản trị viên</label>
                <input type="text" class="form-control form-control-sm" value="${user.email}" readonly>
              </div>
              <div class="form-group mb-0">
                <label class="form-label">Cấp độ bảo mật</label>
                <input type="text" class="form-control form-control-sm" value="Root Administrator (Full RBAC Access)" readonly>
              </div>
            </div>
          </div>
        </div>
      `;
    }
  };

  window.PWD.views.admin = adminViews;
})();
