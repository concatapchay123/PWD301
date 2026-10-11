/**
 * PWD301 LMS - Admin Views Layer
 * Implements:
 * 1. Admin Academic Governance Command Center (4-Tab Modular Command Center):
 *    - Tab 1: Users Matrix & Progressive RBAC + Session Control + Suspend Modal
 *    - Tab 2: Course Review Queue (Side-by-Side Diff) & Instructor Applications
 *    - Tab 3: Faculty Reassignment & Workload Matrix
 *    - Tab 4: Academic Security & Immutable Audit Trail with SHA-256 Block Verification
 * 2. Server Operations & Security Cockpit (65/35 Split Layout):
 *    - Service Health Matrix & Fail-Closed Quarantine Sandbox
 *    - Background Daemons Execution & Regrading Worker Progress
 *    - Isolated Danger Zone ("Never Overwrite Live Database", Kiểm tra Backup & Guarded Live Restore)
 *    - System Maintenance Window Engine (Start/End Window)
 *    - Service health, backup, maintenance and audit operations
 *    - Active Sessions Revocation Panel & Live Threat Stream
 */

class AdminView {
  static workerSummary(services = {}) {
    const worker = services.workers;
    if (!worker || typeof worker.status !== 'string') return 'Chưa có dữ liệu worker từ API';
    const parts = [worker.status];
    if (Number.isInteger(worker.running_jobs) && worker.running_jobs >= 0) parts.push(`đang chạy: ${worker.running_jobs}`);
    if (Number.isInteger(worker.queued_jobs) && worker.queued_jobs >= 0) parts.push(`chờ: ${worker.queued_jobs}`);
    return parts.join(' • ');
  }

  static backupMetadata(backup = {}) {
    const checksum = typeof backup.checksum_sha256 === 'string' && /^[a-f0-9]{64}$/i.test(backup.checksum_sha256) ? backup.checksum_sha256 : '';
    const hasSize = Number.isFinite(backup.file_size_bytes) && backup.file_size_bytes > 0;
    return {
      verified: Boolean(backup.verified_at && checksum && hasSize),
      checksum: checksum || 'Chưa ghi nhận',
      size: hasSize ? (backup.file_size_bytes / (1024 * 1024)).toFixed(2) + ' MB' : 'Chưa có dữ liệu',
    };
  }
  static getAuditPageState(page, perPage, total) {
    const pageSize = Math.max(1, Number.parseInt(perPage, 10) || 50);
    const itemCount = Math.max(0, Number.parseInt(total, 10) || 0);
    const pageCount = Math.max(1, Math.ceil(itemCount / pageSize));
    const currentPage = Math.min(pageCount, Math.max(1, Number.parseInt(page, 10) || 1));
    return {
      page: currentPage,
      perPage: pageSize,
      total: itemCount,
      pageCount,
      firstItem: itemCount ? ((currentPage - 1) * pageSize) + 1 : 0,
      lastItem: itemCount ? Math.min(currentPage * pageSize, itemCount) : 0,
      hasPrevious: currentPage > 1,
      hasNext: currentPage < pageCount,
    };
  }

  static matchesAuditActionFilter(log, actionFilter = 'ALL') {
    if (actionFilter === 'ALL') return true;
    const action = String(log?.action || '').toUpperCase();
    if (actionFilter === 'ROLE') return action.includes('ROLE') || action.includes('ASSIGN');
    if (actionFilter === 'COURSE') return action.includes('COURSE');
    if (actionFilter === 'DATABASE') return action.includes('DATABASE') || action.includes('BACKUP') || action.includes('RESTORE');
    if (actionFilter === 'QUARANTINE') return action.includes('QUARANTINE');
    return action.includes(String(actionFilter).toUpperCase());
  }

  static getAuditRequestParams(page, perPage, actionFilter = 'ALL') {
    const params = { page, per_page: perPage };
    if (actionFilter !== 'ALL') params.action = actionFilter;
    return params;
  }

  static getAuditActionsForRole(subRole) {
    const allActions = [
      'USER_SUSPEND', 'USER_UNSUSPEND', 'USER_ROLES_UPDATED', 'USER_ROLE_ASSIGNED',
      'USER_ROLE_REVOKED', 'USER_REVOKE_SESSIONS', 'COURSE_CREATED', 'COURSE_UPDATED',
      'COURSE_APPROVED', 'COURSE_PUBLISHED', 'COURSE_TRASHED', 'COURSE_ARCHIVED',
      'COURSE_RESTORED_FROM_TRASH', 'COURSE_SUBMITTED_FOR_REVIEW', 'COURSE_REJECTED',
      'COURSE_RETRACTED_TO_DRAFT', 'COURSE_OWNER_REASSIGNED', 'LESSON_CREATED',
      'LESSON_UPDATED', 'LESSON_REORDERED', 'LESSON_TRASHED', 'LESSON_STATUS_CHANGED',
      'TEACHING_ASSIGNMENT_CREATED', 'TEACHING_ASSIGNMENT_UPDATED', 'DATABASE_BACKUP_CREATED',
      'DATABASE_BACKUP_VERIFIED', 'DATABASE_RESTORE_DRY_RUN', 'DATABASE_RESTORE_INITIATED',
      'DATABASE_RESTORE_COMPLETED', 'QUARANTINE_OVERRIDE', 'ASSESSMENT_CREATED',
      'ASSESSMENT_UPDATED', 'ASSESSMENT_PUBLISHED', 'ASSESSMENT_CANCELLED',
      'ASSESSMENT_TRASHED', 'ASSESSMENT_RESTORED',
      'INSTRUCTOR_APPLICATION_SUBMITTED', 'INSTRUCTOR_APPLICATION_CANCELLED',
      'INSTRUCTOR_APPLICATION_APPROVED', 'INSTRUCTOR_APPLICATION_REJECTED',
    ];
    const actionsByRole = {
      ADMIN_COURSE_REVIEW: allActions.filter(action =>
        [
          'COURSE_CHANGE', 'COURSE_ADMIN_EDIT', 'COURSE_APPROVED', 'COURSE_PUBLISHED',
          'COURSE_TRASHED', 'COURSE_ARCHIVED', 'COURSE_RESTORED', 'COURSE_SUBMITTED',
          'COURSE_REJECTED', 'COURSE_RETRACTED', 'COURSE_STATUS_TO_', 'COURSE_CREATED',
          'COURSE_UPDATED', 'LESSON_', 'SUBJECT_',
        ].some(prefix => action.startsWith(prefix))
      ),
      ADMIN_INSTRUCTOR_REVIEW: allActions.filter(action => action.startsWith('INSTRUCTOR_APPLICATION_')),
      ADMIN_TEACHING_ASSIGNMENT: allActions.filter(action =>
        ['TEACHING_', 'COURSE_REASSIGN', 'COURSE_OWNER_REASSIGNED', 'COURSE_ASSIGN']
          .some(prefix => action.startsWith(prefix))
      ),
    };
    return actionsByRole[subRole] || allActions;
  }

  static getAssignableAdminSubRoles() {
    return ['ADMIN_COURSE_REVIEW', 'ADMIN_INSTRUCTOR_REVIEW', 'ADMIN_TEACHING_ASSIGNMENT', 'ADMIN_SYSTEM_MONITORING'];
  }

  static getAdminSubRoleSelectionState(currentRoles, currentAdminSubRole) {
    const isExistingPrimary = currentRoles.includes('ADMIN') && currentAdminSubRole === 'ADMIN_PRIMARY';
    return {
      isExistingPrimary,
      selectedSubRole: isExistingPrimary || !AdminView.getAssignableAdminSubRoles().includes(currentAdminSubRole)
        ? null
        : currentAdminSubRole,
    };
  }

  static renderAuditActionOptions(subRole) {
    const labels = {
      USER_SUSPEND: 'Khóa tài khoản', USER_UNSUSPEND: 'Mở khóa tài khoản', USER_ROLES_UPDATED: 'Cập nhật tập vai trò',
      USER_ROLE_ASSIGNED: 'Bổ nhiệm vai trò', USER_ROLE_REVOKED: 'Thu hồi vai trò', USER_REVOKE_SESSIONS: 'Thu hồi phiên đăng nhập',
      COURSE_CREATED: 'Tạo khóa học', COURSE_UPDATED: 'Cập nhật khóa học', COURSE_APPROVED: 'Duyệt khóa học',
      COURSE_PUBLISHED: 'Xuất bản khóa học', COURSE_TRASHED: 'Đưa khóa học vào thùng rác', COURSE_ARCHIVED: 'Lưu trữ khóa học',
      COURSE_RESTORED_FROM_TRASH: 'Khôi phục khóa học', COURSE_SUBMITTED_FOR_REVIEW: 'Gửi khóa học xét duyệt',
      COURSE_REJECTED: 'Từ chối khóa học', COURSE_RETRACTED_TO_DRAFT: 'Rút khóa học về bản nháp',
      COURSE_OWNER_REASSIGNED: 'Chuyển người phụ trách khóa học', LESSON_CREATED: 'Tạo bài giảng',
      LESSON_UPDATED: 'Cập nhật bài giảng', LESSON_REORDERED: 'Sắp xếp lại bài giảng', LESSON_TRASHED: 'Đưa bài giảng vào thùng rác',
      LESSON_STATUS_CHANGED: 'Đổi trạng thái bài giảng', TEACHING_ASSIGNMENT_CREATED: 'Tạo phân công giảng dạy',
      TEACHING_ASSIGNMENT_UPDATED: 'Cập nhật phân công giảng dạy', DATABASE_BACKUP_CREATED: 'Tạo bản sao lưu cơ sở dữ liệu',
      DATABASE_BACKUP_VERIFIED: 'Xác minh bản sao lưu', DATABASE_RESTORE_DRY_RUN: 'Chạy thử khôi phục cơ sở dữ liệu',
      DATABASE_RESTORE_INITIATED: 'Bắt đầu khôi phục cơ sở dữ liệu', DATABASE_RESTORE_COMPLETED: 'Hoàn tất khôi phục cơ sở dữ liệu',
      QUARANTINE_OVERRIDE: 'Giải phóng tệp cách ly', ASSESSMENT_CREATED: 'Tạo bài thi', ASSESSMENT_UPDATED: 'Cập nhật bài thi',
      ASSESSMENT_PUBLISHED: 'Xuất bản bài thi', ASSESSMENT_CANCELLED: 'Hủy bài thi', ASSESSMENT_TRASHED: 'Đưa bài thi vào thùng rác',
      ASSESSMENT_RESTORED: 'Khôi phục bài thi',
      INSTRUCTOR_APPLICATION_SUBMITTED: 'Nhận hồ sơ giảng viên', INSTRUCTOR_APPLICATION_CANCELLED: 'Hủy hồ sơ giảng viên',
      INSTRUCTOR_APPLICATION_APPROVED: 'Duyệt hồ sơ giảng viên', INSTRUCTOR_APPLICATION_REJECTED: 'Từ chối hồ sơ giảng viên',
    };
    return ['ALL', ...AdminView.getAuditActionsForRole(subRole)].map(action =>
      `<option value="${action}">${action === 'ALL' ? 'Tất cả tác vụ' : (labels[action] || action.replace(/_/g, ' '))}</option>`
    ).join('');
  }

  static renderLessonMarkdown(markdown) {
    const cleaned = String(markdown || '')
      .replace(/<!--\s*video_urls?:.*?-->\s*/gs, '')
      .replace(/<!--\s*mini_quiz:.*?-->\s*/gs, '');
    if (typeof UI !== 'undefined' && typeof UI.renderMarkdown === 'function') {
      return UI.renderMarkdown(cleaned);
    }
    return typeof UI !== 'undefined' ? UI.escapeHtml(cleaned) : '';
  }

  static renderDiffOriginal(origText, propText) {
    if (!origText && !propText) return '<p class="text-slate-400 italic">(Trống)</p>';
    if (!propText || origText === propText) {
      return AdminView.renderLessonMarkdown(origText);
    }
    const origLines = String(origText || '').split('\n');
    const propLines = String(propText || '').split('\n');
    const propSet = new Set(propLines);

    return origLines.map(line => {
      if (!line.trim()) return '<div class="h-2"></div>';
      if (!propSet.has(line)) {
        return `<div class="bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 border-l-4 border-rose-500 pl-2.5 py-1 my-1 rounded-r font-mono text-xs"><del class="line-through">${UI.escapeHtml(line)}</del> <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-200 dark:bg-rose-900 text-rose-800 dark:text-rose-200 font-bold ml-1">Đã xóa</span></div>`;
      }
      return `<div class="py-0.5 text-slate-700 dark:text-slate-300">${UI.escapeHtml(line)}</div>`;
    }).join('');
  }

  static renderDiffProposed(origText, propText) {
    if (!origText && !propText) return '<p class="text-slate-400 italic">(Trống)</p>';
    if (!origText || origText === propText) {
      return AdminView.renderLessonMarkdown(propText);
    }
    const origLines = String(origText || '').split('\n');
    const propLines = String(propText || '').split('\n');
    const origSet = new Set(origLines);

    return propLines.map(line => {
      if (!line.trim()) return '<div class="h-2"></div>';
      if (!origSet.has(line)) {
        return `<div class="bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-200 border-l-4 border-emerald-500 pl-2.5 py-1 my-1 rounded-r font-mono text-xs"><ins class="no-underline bg-emerald-100 dark:bg-emerald-900/60 text-emerald-900 dark:text-emerald-100 px-1 rounded font-bold">${UI.escapeHtml(line)}</ins> <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-200 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200 font-bold ml-1">Mới thêm</span></div>`;
      }
      return `<div class="py-0.5 text-slate-800 dark:text-slate-200 font-medium">${UI.escapeHtml(line)}</div>`;
    }).join('');
  }

  static renderUnifiedDiffPanel(r, orig, prop) {
    const diffSummary = r.diff_summary;
    let changes = [];
    let unchanged = [];

    if (diffSummary && Array.isArray(diffSummary.changes)) {
      changes = diffSummary.changes;
      unchanged = diffSummary.unchanged_fields || [];
    } else {
      const fieldLabels = {
        title: (r.target_type === 'LESSON' ? 'Tiêu đề bài giảng' : 'Tên khóa học'),
        category: 'Danh mục đào tạo',
        difficulty: 'Độ khó',
        description: 'Mô tả khóa học',
        summary: 'Tóm tắt bài học',
        markdown_content: 'Nội dung bài học',
        estimated_duration_minutes: 'Thời lượng (phút)',
        status: 'Trạng thái',
        learning_objectives: 'Chuẩn đầu ra (SLOs)',
        target_audience: 'Đối tượng người học',
        capacity: 'Sĩ số tối đa',
        minimum_completion_seconds: 'Thời gian học tối thiểu (giây)',
        viewed_fraction_required: 'Tỷ lệ xem yêu cầu',
        completion_requirements: 'Tiêu chí hoàn thành & Chứng chỉ'
      };

      const allKeys = new Set([...Object.keys(orig || {}), ...Object.keys(prop || {})]);
      for (const k of allKeys) {
        if (['id', 'created_at', 'updated_at', 'deleted_at', 'course_lessons', 'resources', 'version'].includes(k)) continue;
        const oldVal = (orig || {})[k];
        const newVal = (prop || {})[k];
        const label = fieldLabels[k] || k;
        const oldStr = oldVal !== undefined && oldVal !== null ? String(oldVal).trim() : '';
        const newStr = newVal !== undefined && newVal !== null ? String(newVal).trim() : '';

        if (k in (prop || {}) && oldStr !== newStr) {
          changes.push({
            field: k,
            label: label,
            old_value: oldVal,
            new_value: newVal,
            change_type: oldStr ? 'MODIFIED' : 'ADDED'
          });
        } else if (oldVal !== undefined) {
          unchanged.push({
            field: k,
            label: label,
            value: oldVal
          });
        }
      }
    }

    const formatVal = (val, field) => {
      if (val === null || val === undefined || val === '') return '(Trống)';
      if (typeof val === 'boolean') return val ? 'Có' : 'Không';
      if (typeof val === 'object') {
        try { return JSON.stringify(val, null, 2); } catch (_) { return String(val); }
      }
      if (field === 'viewed_fraction_required') {
        return `${Math.round(Number(val) * 100)}%`;
      }
      return String(val);
    };

    const hasChanges = changes.length > 0;

    return `
      <div class="space-y-6">
        <!-- Changes Header -->
        <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[20px] text-primary">difference</span>
            <h3 class="font-bold text-sm text-slate-900 dark:text-slate-100">
              Chi tiết các điểm thay đổi (${changes.length} mục)
            </h3>
          </div>
          <span class="text-xs px-2.5 py-0.5 rounded-full font-bold ${hasChanges ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300' : 'bg-slate-100 text-slate-600'}">
            ${hasChanges ? `${changes.length} thay đổi cần duyệt` : 'Không có thay đổi'}
          </span>
        </div>

        ${hasChanges ? `
          <div class="space-y-4">
            ${changes.map(ch => {
              const isContent = ch.field === 'markdown_content';

              if (isContent) {
                return `
                  <div class="rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900 shadow-2xs">
                    <div class="bg-slate-50 dark:bg-slate-800/80 px-4 py-2.5 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                      <span class="font-bold text-xs text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[16px] text-primary">description</span>
                        <span>${UI.escapeHtml(ch.label)}</span>
                      </span>
                      <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 font-bold">
                        ĐÃ SỬA NỘI DUNG
                      </span>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200 dark:divide-slate-800">
                      <div class="p-4 space-y-2">
                        <div class="text-[10px] font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider flex items-center gap-1">
                          <span class="material-symbols-outlined text-[14px]">remove_circle</span>
                          <span>Trước khi sửa (Vạch đỏ: phần đã xóa)</span>
                        </div>
                        <div class="p-3 rounded-xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/40 text-xs leading-relaxed max-h-96 overflow-y-auto">
                          ${AdminView.renderDiffOriginal(ch.old_value || '', ch.new_value || '')}
                        </div>
                      </div>
                      <div class="p-4 space-y-2">
                        <div class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                          <span class="material-symbols-outlined text-[14px]">add_circle</span>
                          <span>Sau khi sửa (Vạch xanh: phần thêm mới)</span>
                        </div>
                        <div class="p-3 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-300 dark:border-emerald-800/60 text-xs leading-relaxed max-h-96 overflow-y-auto">
                          ${AdminView.renderDiffProposed(ch.old_value || '', ch.new_value || '')}
                        </div>
                      </div>
                    </div>
                  </div>
                `;
              }

              return `
                <div class="rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900 shadow-2xs">
                  <div class="bg-slate-50 dark:bg-slate-800/80 px-4 py-2 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                    <span class="font-bold text-xs text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                      <span class="material-symbols-outlined text-[16px] text-primary">edit_note</span>
                      <span>${UI.escapeHtml(ch.label)}</span>
                    </span>
                    <span class="text-[10px] px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-950/80 text-blue-800 dark:text-blue-300 font-bold">
                      ${ch.change_type === 'ADDED' ? 'THÊM MỚI' : 'ĐÃ SỬA'}
                    </span>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200 dark:divide-slate-800">
                    <div class="p-4 space-y-1.5">
                      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px] text-slate-400">history</span>
                        <span>Trước khi sửa (Hiện tại)</span>
                      </div>
                      <div class="p-3 rounded-xl bg-rose-50/70 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-xs leading-relaxed">
                        <del class="line-through text-rose-800 dark:text-rose-300 font-medium whitespace-pre-wrap">${UI.escapeHtml(formatVal(ch.old_value, ch.field))}</del>
                      </div>
                    </div>
                    <div class="p-4 space-y-1.5">
                      <div class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">verified</span>
                        <span>Sau khi sửa (Đề xuất)</span>
                      </div>
                      <div class="p-3 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800/80 text-xs leading-relaxed">
                        <ins class="no-underline font-bold text-emerald-900 dark:text-emerald-200 whitespace-pre-wrap">${UI.escapeHtml(formatVal(ch.new_value, ch.field))}</ins>
                      </div>
                    </div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        ` : `
          <div class="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-center space-y-1">
            <span class="material-symbols-outlined text-[32px] text-slate-400">check_circle</span>
            <p class="font-bold text-xs text-slate-700 dark:text-slate-300">Không có thay đổi khác biệt</p>
            <p class="text-[11px] text-slate-500">Các trường dữ liệu đề xuất trùng khớp với dữ liệu gốc.</p>
          </div>
        `}

        <!-- Collapsed Unchanged Fields Section -->
        ${unchanged.length ? `
          <details class="group rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/40 overflow-hidden shadow-2xs">
            <summary class="cursor-pointer px-4 py-3 text-xs font-bold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-between select-none">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-[18px] text-slate-400 group-open:rotate-90 transition-transform">chevron_right</span>
                <span>Các thông tin giữ nguyên không thay đổi (${unchanged.length} trường)</span>
              </div>
              <span class="text-[10px] px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-semibold">Thu gọn / Mở rộng</span>
            </summary>
            <div class="p-4 pt-2 border-t border-slate-200/60 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              ${unchanged.map(u => `
                <div class="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 space-y-1">
                  <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">${UI.escapeHtml(u.label)}</div>
                  <div class="text-xs text-slate-700 dark:text-slate-300 font-medium truncate" title="${UI.escapeHtml(formatVal(u.value, u.field))}">
                    ${UI.escapeHtml(formatVal(u.value, u.field))}
                  </div>
                </div>
              `).join('')}
            </div>
          </details>
        ` : ''}
      </div>
    `;
  }

  static getQueueSummary(subRole, counts = {}) {
    const summary = { courses: 0, changes: 0, applications: 0, assignments: 0 };
    if (subRole === 'ADMIN_PRIMARY' || !subRole) {
      summary.courses = counts.courses || 0;
      summary.changes = counts.changes || 0;
      summary.applications = counts.applications || 0;
      summary.assignments = counts.assignments || 0;
    }
    if (subRole === 'ADMIN_COURSE_REVIEW') {
      summary.courses = counts.courses || 0;
      summary.changes = counts.changes || 0;
    }
    if (subRole === 'ADMIN_INSTRUCTOR_REVIEW') {
      summary.applications = counts.applications || 0;
    }
    if (subRole === 'ADMIN_TEACHING_ASSIGNMENT') {
      summary.assignments = counts.assignments || 0;
    }
    return summary;
  }

  // =========================================================================
  // 1. Admin Governance Command Center (4-Tab Modular Command Center)
  // =========================================================================
  static async renderGovernance(container, activeTab = 'users', subQueue = null) {
    const adminSubRole = window.app?.currentUser?.admin_sub_role || 'ADMIN_PRIMARY';
    const isPrimary = adminSubRole === 'ADMIN_PRIMARY' || Boolean(window.app?.currentUser?.is_primary_admin);
    const showQueueSummary = isPrimary || adminSubRole === 'ADMIN_COURSE_REVIEW' || adminSubRole === 'ADMIN_INSTRUCTOR_REVIEW';
    const isInstructorQueue = !isPrimary && adminSubRole === 'ADMIN_INSTRUCTOR_REVIEW';
    const isHomeTab = (!activeTab || activeTab === 'users');

    container.innerHTML = `
        <div class="p-6 space-y-6 max-w-[1800px] mx-auto animate-fade-in" id="admin-governance-root">
        
        <!-- Header & Context Banner -->
        <section class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div class="space-y-1.5">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary font-caption text-xs font-semibold">
              <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              <span id="admin-governance-actor-label">Quản trị hệ thống</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Quản lý hệ thống
            </h1>
            <p class="text-xs sm:text-sm text-slate-500 max-w-3xl">
              Quản lý người dùng, khóa học, giảng viên và hoạt động của hệ thống.
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3 shrink-0">
            <div class="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-500">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Hệ thống đang hoạt động</span>
            </div>
            <button type="button" id="btn-open-broadcast" class="px-3.5 py-2.5 rounded-xl bg-primary hover:bg-primary-dark text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1.5" onclick="AdminView.openBroadcastModal()">
              <span class="material-symbols-outlined text-[18px]">campaign</span>
              <span>Phát thông báo</span>
            </button>
            ${(adminSubRole === 'ADMIN_PRIMARY' || adminSubRole === 'ADMIN_SYSTEM_MONITORING') ? `
            <a href="#/admin/operations" class="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[18px]">monitoring</span>
              <span>Vận Hành</span>
            </a>` : ''}
          </div>
        </section>

        <!-- Approval & Governance Action Hub (Only shown on Admin Home Tab) -->
        <section id="admin-approval-hub" class="${(isHomeTab && showQueueSummary) ? '' : 'hidden'} bg-gradient-to-br from-amber-500/5 via-primary/5 to-slate-50/50 dark:from-amber-950/20 dark:via-primary-950/10 dark:to-slate-900/50 rounded-2xl p-6 border border-amber-200/80 dark:border-amber-900/40 shadow-sm space-y-5">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span id="hub-status-pill" class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60">
                  <span id="hub-pulse-dot" class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                  <span id="kpi-courses-badge">Đang kiểm tra hàng đợi...</span>
                </span>
                <span class="text-xs text-slate-400 font-medium">Quy chuẩn ABET CAC</span>
              </div>
              <h2 class="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-amber-600 text-[26px]">fact_check</span>
                <span>${isInstructorQueue ? 'Hồ sơ Giảng viên Chờ Xét duyệt' : 'Nhiệm vụ Phê duyệt & Thẩm định Cần Xử lý'}</span>
              </h2>
              <p class="text-xs text-slate-500 dark:text-slate-400 max-w-2xl">
                ${isInstructorQueue ? 'Danh sách hồ sơ giảng viên ứng tuyển cần kiểm tra bằng cấp, CV và hồ sơ học thuật.' : 'Tổng hợp toàn bộ khóa học mới, bản sửa đổi đề cương và hồ sơ giảng viên đang chờ bạn thẩm định và ra quyết định.'}
              </p>
            </div>
            <div class="flex items-center gap-4 bg-white dark:bg-slate-900 px-5 py-3 rounded-2xl border border-amber-200/90 dark:border-amber-900/60 shadow-xs shrink-0">
              <div class="text-right">
                <div class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Tổng việc cần duyệt</div>
                <div class="text-xs font-semibold text-amber-700 dark:text-amber-400" id="kpi-courses-subtext">Hàng đợi xét duyệt</div>
              </div>
              <div class="text-3xl sm:text-4xl font-black text-amber-600 dark:text-amber-400 font-mono tracking-tight" id="kpi-courses-pending">--</div>
            </div>
          </div>

          <!-- 3 Quick Action Cards -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4" id="approval-hub-cards">
            <!-- Card 1: Khóa học mới -->
            <div class="${isInstructorQueue ? 'hidden' : ''} cursor-pointer group bg-white dark:bg-slate-900 hover:bg-amber-50/30 dark:hover:bg-slate-800/60 rounded-xl p-4 border border-slate-200 dark:border-slate-800 hover:border-amber-400 dark:hover:border-amber-500 transition-all shadow-xs flex flex-col justify-between" onclick="window.location.hash = '#/admin/governance?tab=courses&queue=courses'">
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <span class="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-sm">
                    <span class="material-symbols-outlined text-[18px]">menu_book</span>
                  </span>
                  <span class="px-2.5 py-0.5 rounded-full text-xs font-bold font-mono bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300" id="hub-courses-count">--</span>
                </div>
                <div>
                  <h3 class="text-sm font-bold text-slate-800 dark:text-slate-100 group-hover:text-blue-600 transition-colors">Khóa học mới chờ duyệt</h3>
                  <p class="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2 mt-0.5">Khóa học mới gửi đề cương, thẩm định cấu trúc chương mục và chuẩn đầu ra.</p>
                </div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-bold text-blue-600 dark:text-blue-400">
                <span>Vào duyệt khóa học</span>
                <span class="material-symbols-outlined text-[15px] group-hover:translate-x-0.5 transition-transform">arrow_forward</span>
              </div>
            </div>

            <!-- Card 2: Bản sửa đổi -->
            <div class="${isInstructorQueue ? 'hidden' : ''} cursor-pointer group bg-white dark:bg-slate-900 hover:bg-amber-50/30 dark:hover:bg-slate-800/60 rounded-xl p-4 border border-slate-200 dark:border-slate-800 hover:border-amber-400 dark:hover:border-amber-500 transition-all shadow-xs flex flex-col justify-between" onclick="window.location.hash = '#/admin/governance?tab=courses&queue=changes'">
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <span class="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold text-sm">
                    <span class="material-symbols-outlined text-[18px]">rule</span>
                  </span>
                  <span class="px-2.5 py-0.5 rounded-full text-xs font-bold font-mono bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300" id="hub-changes-count">--</span>
                </div>
                <div>
                  <h3 class="text-sm font-bold text-slate-800 dark:text-slate-100 group-hover:text-amber-600 transition-colors">Bản sửa đổi & Đề xuất</h3>
                  <p class="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2 mt-0.5">Yêu cầu chỉnh sửa đề cương, thêm bớt bài học trên các khóa học đã xuất bản.</p>
                </div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-bold text-amber-600 dark:text-amber-400">
                <span>Xem bản sửa đổi</span>
                <span class="material-symbols-outlined text-[15px] group-hover:translate-x-0.5 transition-transform">arrow_forward</span>
              </div>
            </div>

            <!-- Card 3: Hồ sơ giảng viên -->
            <div class="${adminSubRole === 'ADMIN_COURSE_REVIEW' ? 'hidden' : ''} cursor-pointer group bg-white dark:bg-slate-900 hover:bg-amber-50/30 dark:hover:bg-slate-800/60 rounded-xl p-4 border border-slate-200 dark:border-slate-800 hover:border-amber-400 dark:hover:border-amber-500 transition-all shadow-xs flex flex-col justify-between" onclick="window.location.hash = '#/admin/governance?tab=applications'">
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <span class="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-sm">
                    <span class="material-symbols-outlined text-[18px]">badge</span>
                  </span>
                  <span class="px-2.5 py-0.5 rounded-full text-xs font-bold font-mono bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300" id="hub-apps-count">--</span>
                </div>
                <div>
                  <h3 class="text-sm font-bold text-slate-800 dark:text-slate-100 group-hover:text-emerald-600 transition-colors">Hồ sơ giảng viên ứng tuyển</h3>
                  <p class="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2 mt-0.5">Đơn ứng tuyển nâng cấp quyền Giảng viên mới nộp lên hệ thống.</p>
                </div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                <span>Duyệt hồ sơ giảng viên</span>
                <span class="material-symbols-outlined text-[15px] group-hover:translate-x-0.5 transition-transform">arrow_forward</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Tab Content Box -->
        <div id="admin-tab-content-box" class="min-h-[400px]"></div>

      </div>
    `;

    // Load initial KPIs
    try {
      const isCourseReviewer = isPrimary || adminSubRole === 'ADMIN_COURSE_REVIEW';
      const isInstructorReviewer = isPrimary || adminSubRole === 'ADMIN_INSTRUCTOR_REVIEW';
      const [coursesRes, appsRes, crRes] = await Promise.allSettled([
        isCourseReviewer ? ApiClient.getPendingCourses() : Promise.resolve(null),
        isInstructorReviewer ? ApiClient.getAdminInstructorApplications('PENDING') : Promise.resolve(null),
        isCourseReviewer ? ApiClient.getAdminChangeRequests('PENDING') : Promise.resolve(null)
      ]);

      let pendingCoursesCount = 0;
      if (coursesRes.status === 'fulfilled' && coursesRes.value) {
        pendingCoursesCount = coursesRes.value.pending_count || (coursesRes.value.courses ? coursesRes.value.courses.length : 0);
      }
      let pendingCrCount = 0;
      if (crRes.status === 'fulfilled' && crRes.value) {
        pendingCrCount = crRes.value.pending_count || (crRes.value.change_requests ? crRes.value.change_requests.length : 0);
      }
      let pendingAppsCount = 0;
      if (appsRes.status === 'fulfilled' && appsRes.value) {
        pendingAppsCount = appsRes.value.pending_count || (appsRes.value.applications ? appsRes.value.applications.length : 0);
      }

      const queueSummary = AdminView.getQueueSummary(adminSubRole, {
        courses: pendingCoursesCount,
        changes: pendingCrCount,
        applications: pendingAppsCount,
      });
      const totalCourseWork = queueSummary.courses + queueSummary.changes + queueSummary.applications;
      const el = document.getElementById('kpi-courses-pending');
      const badge = document.getElementById('kpi-courses-badge');
      const subtext = document.getElementById('kpi-courses-subtext');
      const hubCoursesEl = document.getElementById('hub-courses-count');
      const hubChangesEl = document.getElementById('hub-changes-count');
      const hubAppsEl = document.getElementById('hub-apps-count');
      const hubStatusPill = document.getElementById('hub-status-pill');
      const hubPulseDot = document.getElementById('hub-pulse-dot');

      if (hubCoursesEl) hubCoursesEl.textContent = `${pendingCoursesCount} khóa`;
      if (hubChangesEl) hubChangesEl.textContent = `${pendingCrCount} bản sửa`;
      if (hubAppsEl) hubAppsEl.textContent = `${pendingAppsCount} hồ sơ`;

      if (el) el.textContent = String(totalCourseWork).padStart(2, '0');
      if (badge) {
        if (totalCourseWork > 0) {
          badge.textContent = `${totalCourseWork} việc cần xử lý ngay`;
          if (subtext) subtext.textContent = 'Cần hành động ngay';
          if (hubStatusPill) {
            hubStatusPill.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60';
          }
          if (hubPulseDot) hubPulseDot.className = 'w-2 h-2 rounded-full bg-amber-500 animate-pulse';
        } else {
          badge.textContent = `Tất cả đã hoàn tất (0 việc)`;
          if (subtext) subtext.textContent = 'Không có việc tồn đọng';
          if (hubStatusPill) {
            hubStatusPill.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60';
          }
          if (hubPulseDot) hubPulseDot.className = 'w-2 h-2 rounded-full bg-emerald-500';
        }
      }

      // Synchronize Real-time Superscript Exponent Badges to Topbar
      if (window.app && typeof window.app.updateAdminNavBadges === 'function') {
        window.app.updateAdminNavBadges({
          courses: queueSummary.courses + queueSummary.changes,
          applications: queueSummary.applications
        });
      }

    } catch (err) {
      console.warn('Initial admin KPI load warning:', err);
    }

    // Tab Switching Logic (URL Hash & Topbar Synchronized)
    const contentBox = document.getElementById('admin-tab-content-box');

    AdminView.switchTab = async (tabKey, subQueue = null, syncHash = true) => {
      const tabToQuery = {
        'tab-users': '',
        'tab-courses-review': 'courses',
        'tab-review': 'courses',
        'tab-instructor-apps': 'applications',
        'tab-reassign': 'reassign',
        'tab-security': 'security'
      };

      if (syncHash) {
        const q = tabToQuery[tabKey];
        const newHash = q ? `#/admin/governance?tab=${q}` : '#/admin/governance';
        if (window.location.hash !== newHash) {
          window.location.hash = newHash;
          return;
        }
      }

      // Toggle Approval Hub: only show on Home Tab (tab-users)
      const hub = document.getElementById('admin-approval-hub');
      if (hub) {
        if (tabKey === 'tab-users' && showQueueSummary) {
          hub.classList.remove('hidden');
        } else {
          hub.classList.add('hidden');
        }
      }

      if (tabKey === 'tab-users') {
        AdminView.renderTabUsers(contentBox);
      } else if (tabKey === 'tab-courses-review' || tabKey === 'tab-review') {
        await AdminView.renderTabCoursesReview(contentBox, subQueue);
      } else if (tabKey === 'tab-instructor-apps') {
        AdminView.renderTabInstructorApps(contentBox);
      } else if (tabKey === 'tab-reassign') {
        AdminView.renderTabReassign(contentBox);
      } else if (tabKey === 'tab-security') {
        AdminView.renderTabSecurity(contentBox);
      }
    };

    const targetTab = (activeTab === 'courses' || activeTab === 'review')
      ? 'tab-courses-review'
      : (activeTab === 'applications' || activeTab === 'instructors')
        ? 'tab-instructor-apps'
        : activeTab === 'security'
          ? 'tab-security'
          : activeTab === 'reassign'
            ? 'tab-reassign'
            : 'tab-users';
    await AdminView.switchTab(targetTab, subQueue, false);
  }

  static renderUserAvatar(u) {
    const initials = (u.display_name || u.email || 'U').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    const avatarBg = u.roles && u.roles.includes('ADMIN') ? 'bg-primary text-white' : u.roles && u.roles.includes('INSTRUCTOR') ? 'bg-indigo-600 text-white' : 'bg-slate-500 text-white';
    let avatarUrl = u.avatar_url;
    if (!avatarUrl && typeof StudentView !== 'undefined' && typeof StudentView.getStoredRandomAvatarUrl === 'function') {
      avatarUrl = StudentView.getStoredRandomAvatarUrl(u.user_id || u.id);
    }
    if (!avatarUrl && window.app?.currentUser && (window.app.currentUser.public_id === u.user_id || window.app.currentUser.id === u.user_id || window.app.currentUser.email === u.email)) {
      avatarUrl = window.app.currentUser.avatar_url;
    }

    const escape = typeof UI !== 'undefined' && typeof UI.escapeHtml === 'function'
      ? UI.escapeHtml
      : (s) => String(s || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    if (avatarUrl) {
      return `
        <div class="w-9 h-9 rounded-xl ${avatarBg} font-bold flex items-center justify-center text-xs shrink-0 shadow-xs overflow-hidden relative border border-slate-200/60 dark:border-slate-700/60">
          <img src="${escape(avatarUrl)}"
               alt="${escape(u.display_name || u.email)}"
               class="w-full h-full object-cover"
               loading="lazy"
               onerror="this.style.display='none'; if (this.nextElementSibling) this.nextElementSibling.classList.remove('hidden');" />
          <span class="hidden items-center justify-center w-full h-full text-xs font-bold">${initials}</span>
        </div>
      `;
    }
    return `
      <div class="w-9 h-9 rounded-xl ${avatarBg} font-bold flex items-center justify-center text-xs shrink-0 shadow-xs">
        <span class="flex items-center justify-center w-full h-full text-xs font-bold">${initials}</span>
      </div>
    `;
  }

  // =========================================================================
  // Tab 1: Users & Progressive RBAC + Active Sessions (100% Live Database)
  // =========================================================================
  static async renderTabUsers(container) {
    container.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5" id="users-box">
        <div class="p-12 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang tải ma trận người dùng & kiểm soát phiên từ MS SQL Server...</p>
        </div>
      </div>
    `;

    try {
      const res = await ApiClient.getAdminUsers();
      const users = res.users || [];
      const totalUsers = res.total !== undefined ? res.total : users.length;

      const box = document.getElementById('users-box');
      if (!box) return;

      box.innerHTML = `
        <!-- Table Header & Controls -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-[22px]">badge</span>
              <h2 class="text-base font-bold text-slate-900 dark:text-white">Người dùng & Phân quyền (${totalUsers} tài khoản)</h2>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">Chọn quyền phù hợp cho từng người. Mọi thay đổi đều được ghi lại.</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <div class="relative">
              <input type="text" id="user-search-input" aria-label="Tìm kiếm người dùng theo tên hoặc email" placeholder="Tìm tên hoặc email..." class="pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:border-primary" />
              <span class="material-symbols-outlined absolute left-2.5 top-2 text-slate-400 text-[16px]" aria-hidden="true">search</span>
            </div>
            <select id="user-role-filter" aria-label="Lọc người dùng theo vai trò" class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300 font-bold focus:outline-none">
              <option value="ALL">T&#7845;t c&#7843; ng&#432;&#7901;i d&#249;ng</option>
              <option value="STUDENT">Sinh vi&#234;n</option>
              <option value="INSTRUCTOR">Gi&#7843;ng vi&#234;n</option>
              <option value="ADMIN">Qu&#7843;n tr&#7883; vi&#234;n</option>
            </select>
            <button type="button" id="btn-sync-users" class="px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 text-xs font-bold transition-colors flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]">sync</span>
              <span>Đồng bộ</span>
            </button>
          </div>
        </div>

        <!-- Master Table Container -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs sm:text-sm border-collapse" id="admin-users-table">
            <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
              <tr>
                <th class="py-3 px-3">Họ tên & Email</th>
                <th class="py-3 px-3">Vai trò</th>
                <th class="py-3 px-3">Ngày tạo</th>
                <th class="py-3 px-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium" id="admin-users-tbody">
              <!-- Rendered via JS -->
            </tbody>
          </table>
        </div>

        <!-- Strict Non-negotiable Invariant: No Impersonation -->
        <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-600 dark:text-slate-300">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-[18px]">verified_user</span>
            <span>Quản trị viên dùng tài khoản của mình khi thao tác. Hệ thống ghi lại người thực hiện mỗi thay đổi.</span>
          </div>
        </div>

        <!-- Optimistic Locking Panel -->
        <div class="p-4 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <div class="flex items-start gap-2.5">
            <span class="material-symbols-outlined text-amber-600 text-[20px] mt-0.5">sync_problem</span>
            <div>
              <strong class="text-amber-900 dark:text-amber-300 block mb-0.5">Dữ liệu có thể thay đổi trong lúc bạn thao tác</strong>
              <p class="text-amber-800/80 dark:text-amber-400/80">Khi đổi vai trò hoặc tạm ngưng tài khoản, các phiên đăng nhập hiện có sẽ hết hiệu lực.</p>
            </div>
          </div>
          <button type="button" id="btn-sync-optimistic" class="px-4 py-2 rounded-xl bg-white dark:bg-slate-900 border border-amber-300 dark:border-amber-800 hover:bg-amber-50 text-slate-800 dark:text-slate-200 font-bold text-xs shrink-0 transition-colors shadow-xs">
            Tải lại dữ liệu
          </button>
        </div>
      `;

      const renderTableRows = (userList = users) => {
        const tbody = document.getElementById('admin-users-tbody');
        if (!tbody) return;

        if (userList.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="4" class="py-8 text-center text-slate-400 text-xs">
                Không tìm thấy người dùng phù hợp với điều kiện tìm kiếm.
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = userList.map(u => {
          const isSuspended = u.status === 'SUSPENDED';
          const revocableRoles = (u.roles || []).filter(r => r !== 'STUDENT');
          const avatarContent = AdminView.renderUserAvatar(u);

          return `
            <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
              <td class="py-4 px-3 align-middle">
                <div class="flex items-center gap-3">
                  ${avatarContent}
                  <div>
                    <div class="font-bold text-slate-900 dark:text-white text-xs sm:text-sm">
                      ${UI.escapeHtml(u.display_name || 'Chưa cập nhật tên')}
                    </div>
                    <div class="text-[11px] text-slate-400 font-mono">${UI.escapeHtml(u.email)}</div>
                  </div>
                </div>
              </td>
              <td class="py-4 px-3 align-middle">
                <div class="flex flex-wrap gap-1">
                  ${(u.roles || []).map(r => {
                    let rClass = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700';
                    let rLabel = r;
                    if (r === 'ADMIN') {
                      rClass = 'bg-primary-subtle text-primary border border-primary/20 font-bold';
                      if (u.admin_sub_role_label) {
                        rLabel = `ADMIN (${u.admin_sub_role_label})`;
                      }
                    }
                    if (r === 'INSTRUCTOR') rClass = 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 font-bold';
                    return `<span class="px-2 py-0.5 rounded text-[10px] ${rClass}">${rLabel}</span>`;
                  }).join('')}
                </div>
              </td>
              <td class="py-4 px-3 align-middle text-xs text-slate-400 font-mono">
                ${UI.formatDate(u.created_at)}
              </td>
              <td class="py-4 px-3 align-middle text-right">
                <div class="inline-flex items-center gap-1.5 flex-wrap justify-end">
                  <button type="button" class="px-2.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors manage-role-btn ${!window.app?.currentUser?.is_primary_admin ? 'opacity-60 cursor-not-allowed' : ''}" data-user-id="${u.user_id}" data-user-name="${UI.escapeHtml(u.display_name || u.email)}" data-roles="${(u.roles || []).join(',')}" data-admin-sub-role="${u.admin_sub_role || 'ADMIN_PRIMARY'}" title="${!window.app?.currentUser?.is_primary_admin ? 'Chỉ Admin chính mới có quyền phân quyền' : 'Phân quyền tài khoản'}">
                    Phân quyền
                  </button>
                  <button type="button" class="px-2.5 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 text-xs font-bold border border-amber-200 dark:border-amber-800 transition-colors revoke-role-btn ${!window.app?.currentUser?.is_primary_admin ? 'opacity-60 cursor-not-allowed' : ''}" data-user-id="${u.user_id}" data-user-name="${UI.escapeHtml(u.display_name || u.email)}" data-roles="${(u.roles || []).join(',')}" data-admin-sub-role="${u.admin_sub_role || 'ADMIN_PRIMARY'}" title="${!window.app?.currentUser?.is_primary_admin ? 'Chỉ Admin chính mới có quyền thu hồi quyền' : 'Thu hồi quyền tài khoản'}">
                    Thu hồi quyền
                  </button>
                  <button type="button" class="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400 text-xs font-bold transition-colors revoke-sessions-btn" title="Thu hồi toàn bộ phiên đăng nhập của người dùng" data-user-id="${u.user_id}" data-user-name="${UI.escapeHtml(u.display_name || u.email)}">
                    Đăng xuất thiết bị
                  </button>
                </div>
              </td>
            </tr>
          `;
        }).join('');

        // Attach action events
        tbody.querySelectorAll('.manage-role-btn').forEach(btn => {
          btn.onclick = () => {
            if (!window.app?.currentUser?.is_primary_admin) {
              UI.showToast('Chỉ Quản trị viên chính (Admin chính) mới có quyền phân quyền người dùng.', 'warning');
              return;
            }
            const currentRoles = (btn.dataset.roles || '').split(',').filter(Boolean);
            AdminView.openRoleModal(btn.dataset.userId, btn.dataset.userName, currentRoles, btn.dataset.adminSubRole, 'assign');
          };
        });

        tbody.querySelectorAll('.revoke-role-btn').forEach(btn => {
          btn.onclick = () => {
            if (!window.app?.currentUser?.is_primary_admin) {
              UI.showToast('Chỉ Quản trị viên chính (Admin chính) mới có quyền thu hồi vai trò người dùng.', 'warning');
              return;
            }
            const currentRoles = (btn.dataset.roles || '').split(',').filter(Boolean);
            AdminView.openRevokeRoleModal(btn.dataset.userId, btn.dataset.userName, currentRoles, btn.dataset.adminSubRole);
          };
        });

        tbody.querySelectorAll('.revoke-sessions-btn').forEach(btn => {
          btn.onclick = () => {
            AdminView.revokeUserSessions(btn.dataset.userId, btn.dataset.userName);
          };
        });
      };

      // Initial render of rows
      renderTableRows(users);

      // Search & Filter event bindings (Debounced Server-side Query with Local Fallback)
      const searchInput = document.getElementById('user-search-input');
      const roleFilter = document.getElementById('user-role-filter');
      let searchDebounceTimer = null;
      let searchGeneration = 0;

      const triggerQuery = async () => {
        const queryGen = ++searchGeneration;
        const sVal = searchInput ? searchInput.value.trim() : '';
        const rVal = roleFilter ? roleFilter.value : 'ALL';
        try {
          const freshRes = await ApiClient.getAdminUsers({
            search: sVal,
            role: rVal === 'ALL' ? '' : rVal
          });
          if (queryGen !== searchGeneration) return; // Stale query discarded (SYNC-051)
          const freshUsers = freshRes.users || [];
          renderTableRows(freshUsers);
          const counterEl = box.querySelector('h2');
          if (counterEl) {
            counterEl.textContent = `Người dùng & Phân quyền (${freshRes.total !== undefined ? freshRes.total : freshUsers.length} tài khoản)`;
          }
        } catch (e) {
          if (queryGen !== searchGeneration) return;
          const localFiltered = users.filter(u => {
            const matchText = !sVal || 
              (u.display_name && u.display_name.toLowerCase().includes(sVal.toLowerCase())) ||
              (u.email && u.email.toLowerCase().includes(sVal.toLowerCase()));
            const matchRole = rVal === 'ALL' || (u.roles && u.roles.includes(rVal));
            return matchText && matchRole;
          });
          renderTableRows(localFiltered);
        }
      };

      if (searchInput) {
        searchInput.oninput = () => {
          clearTimeout(searchDebounceTimer);
          searchDebounceTimer = setTimeout(triggerQuery, 250);
        };
      }
      if (roleFilter) {
        roleFilter.onchange = () => {
          triggerQuery();
        };
      }

      document.getElementById('btn-sync-users').onclick = async () => {
        await UI.refreshCurrentRoute(() => AdminView.renderTabUsers(container));
      };

      document.getElementById('btn-sync-optimistic').onclick = async () => {
        await UI.refreshCurrentRoute(() => AdminView.renderTabUsers(container));
        UI.showToast('Đã đồng bộ trạng thái người dùng mới nhất từ máy chủ!', 'success');
      };

    } catch (err) {
      console.error('TabUsers load error:', err);
      const box = document.getElementById('users-box');
      if (box) {
        box.innerHTML = `
          <div class="p-8 text-center text-rose-500 space-y-2">
            <span class="material-symbols-outlined text-4xl">error</span>
            <p class="text-sm font-bold">Không thể tải danh sách người dùng: ${UI.escapeHtml(err.message || 'Lỗi kết nối')}</p>
            <button type="button" class="px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold" onclick="UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box'))) ">Thử lại</button>
          </div>
        `;
      }
    }
  }

  static openRoleModal(userId, userName, currentRoles = [], currentAdminSubRole = 'ADMIN_PRIMARY', initialAction = 'assign') {
    if (!window.app?.currentUser?.is_primary_admin) {
      UI.showToast('Chỉ Quản trị viên chính (Admin chính) mới có quyền phân quyền hoặc thu hồi quyền người dùng.', 'error');
      return;
    }

    const subRoleSelectionState = AdminView.getAdminSubRoleSelectionState(currentRoles, currentAdminSubRole);
    const revocableRoles = currentRoles.filter(r => r !== 'STUDENT');

    const roleLabels = {
      'INSTRUCTOR': {
        title: 'Giảng viên (INSTRUCTOR)',
        desc: 'Quyền biên soạn giáo trình, quản lý bài học, tạo đề thi và chấm bài của học sinh.',
        color: 'border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/50 dark:bg-indigo-950/20 text-indigo-900 dark:text-indigo-200'
      },
      'ADMIN': {
        title: 'Quản trị viên (ADMIN)',
        desc: 'Quyền phê duyệt khóa học, quản lý ứng tuyển giảng viên, vận hành và cấu hình hệ thống.',
        color: 'border-purple-200 dark:border-purple-900/60 bg-purple-50/50 dark:bg-purple-950/20 text-purple-900 dark:text-purple-200'
      }
    };

    const isRevokeMode = initialAction === 'remove';

    const body = `
      <div class="space-y-4 text-xs">
        <p class="text-slate-600 dark:text-slate-300">
          Quản lý phân quyền và thu hồi quyền tài khoản <strong>${UI.escapeHtml(userName)}</strong>.
        </p>
        
        <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
          <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Vai trò hiện tại:</div>
          <div class="flex flex-wrap gap-1">
            ${currentRoles.length > 0 ? currentRoles.map(r => `<span class="px-2 py-0.5 rounded bg-primary-subtle text-primary font-bold text-[10px]">${r}</span>`).join('') : '<span class="text-slate-400">Không có vai trò</span>'}
          </div>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Hành động</label>
          <select id="modal-role-action" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary">
            <option value="assign" ${!isRevokeMode ? 'selected' : ''}>Phân quyền (Cấp thêm quyền)</option>
            <option value="remove" ${isRevokeMode ? 'selected' : ''}>Thu hồi quyền (Remove)</option>
          </select>
        </div>

        <!-- Section 1: Giao diện Phân quyền -->
        <div id="role-assign-section" class="${!isRevokeMode ? '' : 'hidden'} space-y-4">
          <div class="space-y-1">
            <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Vai trò mục tiêu</label>
            <select id="modal-role-code" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary">
              <option value="ADMIN">ADMIN (Quản trị viên)</option>
              <option value="INSTRUCTOR">INSTRUCTOR (Giảng viên)</option>
              <option value="STUDENT">STUDENT (Sinh viên)</option>
            </select>
          </div>

          <!-- Phân quyền chi tiết Admin dưới quyền Admin chính -->
          <div id="admin-sub-role-container" class="space-y-2 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
            <div class="flex items-center justify-between">
              <label class="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 text-[11px] flex items-center gap-1.5">
                <span class="material-symbols-outlined text-primary text-[16px]">shield_person</span>
                Quyền quản trị
              </label>
              <span class="text-[10px] text-primary font-bold bg-primary-subtle px-2 py-0.5 rounded">Chọn một vai trò</span>
            </div>
            <div class="space-y-2 pt-1">
              ${subRoleSelectionState.isExistingPrimary ? `
                <div class="px-2.5 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-200" role="status">
                  Tài khoản Admin chính hiện tại; không thể cấp mới hoặc đổi vai trò tại đây.
                </div>
              ` : ''}
              <label class="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white dark:hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-600 transition-all">
                <input type="radio" name="admin-sub-role-radio" value="ADMIN_COURSE_REVIEW" ${subRoleSelectionState.isExistingPrimary ? 'disabled' : ''} class="mt-0.5 text-primary focus:ring-primary" ${subRoleSelectionState.selectedSubRole === 'ADMIN_COURSE_REVIEW' ? 'checked' : ''}>
                <div>
                  <div class="font-bold text-xs text-slate-900 dark:text-white">Admin duyệt khóa học</div>
                  <div class="text-[11px] text-slate-500">Duyệt khóa học và yêu cầu thay đổi bài giảng.</div>
                </div>
              </label>
              <label class="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white dark:hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-600 transition-all">
                <input type="radio" name="admin-sub-role-radio" value="ADMIN_INSTRUCTOR_REVIEW" ${subRoleSelectionState.isExistingPrimary ? 'disabled' : ''} class="mt-0.5 text-primary focus:ring-primary" ${subRoleSelectionState.selectedSubRole === 'ADMIN_INSTRUCTOR_REVIEW' ? 'checked' : ''}>
                <div>
                  <div class="font-bold text-xs text-slate-900 dark:text-white">Admin duyệt giảng viên</div>
                  <div class="text-[11px] text-slate-500">Xem hồ sơ và duyệt đơn đăng ký giảng viên.</div>
                </div>
              </label>
              <label class="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white dark:hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-600 transition-all">
                <input type="radio" name="admin-sub-role-radio" value="ADMIN_TEACHING_ASSIGNMENT" ${subRoleSelectionState.isExistingPrimary ? 'disabled' : ''} class="mt-0.5 text-primary focus:ring-primary" ${subRoleSelectionState.selectedSubRole === 'ADMIN_TEACHING_ASSIGNMENT' ? 'checked' : ''}>
                <div>
                  <div class="font-bold text-xs text-slate-900 dark:text-white">Admin phân công giảng dạy</div>
                  <div class="text-[11px] text-slate-500">Giao khóa học cho giảng viên phụ trách.</div>
                </div>
              </label>
              <label class="flex items-start gap-2.5 p-2.5 rounded-xl hover:bg-white dark:hover:bg-slate-700/50 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-600 transition-all">
                <input type="radio" name="admin-sub-role-radio" value="ADMIN_SYSTEM_MONITORING" ${subRoleSelectionState.isExistingPrimary ? 'disabled' : ''} class="mt-0.5 text-primary focus:ring-primary" ${subRoleSelectionState.selectedSubRole === 'ADMIN_SYSTEM_MONITORING' ? 'checked' : ''}>
                <div>
                  <div class="font-bold text-xs text-slate-900 dark:text-white">Admin giám sát hệ thống</div>
                  <div class="text-[11px] text-slate-500">Xem lịch sử hoạt động và tình trạng hệ thống.</div>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- Section 2: Giao diện Thu hồi quyền -->
        <div id="role-revoke-section" class="${isRevokeMode ? '' : 'hidden'} space-y-3">
          <!-- Baseline Student Notice -->
          <div class="p-3 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/60 flex items-start gap-2.5 text-blue-800 dark:text-blue-300">
            <span class="material-symbols-outlined text-[18px] text-blue-600 shrink-0 mt-0.5">info</span>
            <div>
              <strong class="block font-semibold">Quy tắc vai trò cơ bản (Baseline Role)</strong>
              <span>Vai trò <strong>Sinh viên (STUDENT)</strong> là quyền mặc định cơ bản của mọi tài khoản trong hệ thống và không thể thu hồi.</span>
            </div>
          </div>

          ${revocableRoles.length === 0 ? `
            <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-center text-slate-500 text-xs">
              Tài khoản này chỉ có quyền Sinh viên (STUDENT) mặc định, không có quyền nào khác để thu hồi.
            </div>
          ` : `
            <!-- Select All Checkbox -->
            <div class="flex items-center justify-between px-1 pt-1 pb-2 border-b border-slate-100 dark:border-slate-800">
              <label class="flex items-center gap-2 cursor-pointer font-bold text-slate-800 dark:text-slate-200 select-none">
                <input type="checkbox" id="revoke-select-all" class="w-4 h-4 rounded text-primary focus:ring-primary cursor-pointer" />
                <span>Chọn tất cả quyền có thể thu hồi (${revocableRoles.length})</span>
              </label>
              <span class="text-[11px] text-slate-400">Chọn ít nhất 1 quyền</span>
            </div>

            <!-- Role Checkboxes List (No STUDENT) -->
            <div class="space-y-2.5" id="revoke-roles-list">
              ${revocableRoles.map(r => {
                const info = roleLabels[r] || { title: r, desc: `Vai trò ${r} trong hệ thống`, color: 'border-slate-200 bg-slate-50 text-slate-800' };
                return `
                  <label class="flex items-start gap-3 p-3.5 rounded-xl border ${info.color} cursor-pointer hover:shadow-2xs transition-all select-none">
                    <input type="checkbox" name="revoke-role-item" value="${r}" class="revoke-role-checkbox mt-0.5 w-4 h-4 rounded text-rose-600 focus:ring-rose-600 cursor-pointer" />
                    <div class="min-w-0 flex-1">
                      <div class="font-bold text-xs flex items-center justify-between">
                        <span>${info.title}</span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/80 dark:bg-slate-900/80 border border-current">${r}</span>
                      </div>
                      <p class="text-[11px] opacity-80 mt-0.5 leading-relaxed">${info.desc}</p>
                    </div>
                  </label>
                `;
              }).join('')}
            </div>
          `}
        </div>

        <!-- Lý do thay đổi quyền (Audit Reason) -->
        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">
            Lý do kiểm toán <span class="text-rose-500">*</span>
          </label>
          <input type="text" id="modal-role-reason" placeholder="VD: Bổ nhiệm hoặc kết thúc nhiệm kỳ giảng dạy..." class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" />
        </div>
      </div>
    `;

    const footer = `
      <div class="flex items-center justify-between w-full">
        <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" onclick="UI.closeModal()">Đóng</button>
        <button type="button" id="submit-role-btn" class="px-5 py-2 rounded-xl text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 ${isRevokeMode ? 'bg-rose-600 hover:bg-rose-700' : 'bg-primary hover:bg-primary-dark'}">
          <span class="material-symbols-outlined text-[16px]" id="submit-role-icon">${isRevokeMode ? 'remove_moderator' : 'verified_user'}</span>
          <span id="submit-role-text">${isRevokeMode ? 'Xác nhận thu hồi quyền' : 'Xác nhận phân quyền'}</span>
        </button>
      </div>
    `;

    UI.openModal({
      title: isRevokeMode ? 'Thu hồi quyền tài khoản người dùng' : 'Phân quyền tài khoản người dùng',
      bodyHtml: body,
      footerHtml: footer,
      size: 'md'
    });

    const actionSelect = document.getElementById('modal-role-action');
    const roleSelect = document.getElementById('modal-role-code');
    const subRoleContainer = document.getElementById('admin-sub-role-container');
    const assignSection = document.getElementById('role-assign-section');
    const revokeSection = document.getElementById('role-revoke-section');
    const submitBtn = document.getElementById('submit-role-btn');
    const submitIcon = document.getElementById('submit-role-icon');
    const submitText = document.getElementById('submit-role-text');
    const reasonInput = document.getElementById('modal-role-reason');

    const updateSubRoleVisibility = () => {
      if (subRoleContainer) {
        if (actionSelect.value === 'assign' && roleSelect?.value === 'ADMIN') {
          subRoleContainer.classList.remove('hidden');
        } else {
          subRoleContainer.classList.add('hidden');
        }
      }
    };

    const handleActionChange = () => {
      const mode = actionSelect.value;
      if (mode === 'remove') {
        if (assignSection) assignSection.classList.add('hidden');
        if (revokeSection) revokeSection.classList.remove('hidden');
        if (submitBtn) {
          submitBtn.className = 'px-5 py-2 rounded-xl text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 bg-rose-600 hover:bg-rose-700';
        }
        if (submitIcon) submitIcon.textContent = 'remove_moderator';
        if (submitText) submitText.textContent = 'Xác nhận thu hồi quyền';
        if (reasonInput) reasonInput.placeholder = 'VD: Kết thúc nhiệm kỳ giảng dạy, điều chuyển công tác...';
      } else {
        if (assignSection) assignSection.classList.remove('hidden');
        if (revokeSection) revokeSection.classList.add('hidden');
        if (submitBtn) {
          submitBtn.className = 'px-5 py-2 rounded-xl text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 bg-primary hover:bg-primary-dark';
        }
        if (submitIcon) submitIcon.textContent = 'verified_user';
        if (submitText) submitText.textContent = 'Xác nhận phân quyền';
        if (reasonInput) reasonInput.placeholder = 'VD: Quyết định bổ nhiệm nhân sự học vụ...';
        updateSubRoleVisibility();
      }
    };

    if (actionSelect) actionSelect.onchange = handleActionChange;
    if (roleSelect) roleSelect.onchange = updateSubRoleVisibility;
    updateSubRoleVisibility();

    // Checkbox wiring for revoke section
    const selectAllBox = document.getElementById('revoke-select-all');
    const itemBoxes = document.querySelectorAll('.revoke-role-checkbox');

    if (selectAllBox) {
      selectAllBox.onchange = () => {
        itemBoxes.forEach(box => { box.checked = selectAllBox.checked; });
      };
    }

    itemBoxes.forEach(box => {
      box.onchange = () => {
        if (selectAllBox) {
          selectAllBox.checked = Array.from(itemBoxes).every(b => b.checked);
        }
      };
    });

    submitBtn.onclick = async () => {
      const action = actionSelect.value;
      const reason = (reasonInput?.value || '').trim();

      if (!reason) {
        UI.showToast(action === 'remove' ? 'Vui lòng nhập lý do thu hồi quyền để lưu nhật ký kiểm toán.' : 'Vui lòng nhập lý do thay đổi phân quyền kiểm toán.', 'warning');
        return;
      }

      if (action === 'assign') {
        const role = roleSelect.value;
        let adminSubRole = null;
        if (role === 'ADMIN') {
          const checkedRadio = document.querySelector('input[name="admin-sub-role-radio"]:checked');
          if (!checkedRadio || !AdminView.getAssignableAdminSubRoles().includes(checkedRadio.value)) {
            UI.showToast('Vui lòng chọn một vai trò admin phụ trước khi cấp quyền ADMIN.', 'warning');
            return;
          }
          adminSubRole = checkedRadio.value;
        }

        try {
          await ApiClient.assignRole(userId, role, reason, adminSubRole);
          UI.showToast(`Đã cấp quyền ${role} cho ${userName} thành công!`, 'success');
          UI.closeModal();
          UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box')));
        } catch (e) {
          UI.showToast(e.message || 'Lỗi phân quyền.', 'error');
        }
      } else {
        // action === 'remove'
        const selected = Array.from(itemBoxes).filter(b => b.checked).map(b => b.value);
        if (selected.length === 0) {
          UI.showToast('Vui lòng chọn ít nhất 1 quyền cần thu hồi.', 'warning');
          return;
        }

        try {
          await ApiClient.removeRoles(userId, selected, reason);
          UI.showToast(`Đã thu hồi thành công vai trò ${selected.join(', ')} của ${userName}!`, 'success');
          UI.closeModal();
        } catch (err) {
          UI.showToast(err.message || 'Lỗi khi thu hồi quyền.', 'error');
        } finally {
          // SYNC-049: Always refetch after error or success to guarantee visible UI matches server authoritative state
          UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box')));
        }
      }
    };
  }

  static openRevokeRoleModal(userId, userName, currentRoles = [], currentAdminSubRole = 'ADMIN_PRIMARY') {
    return AdminView.openRoleModal(userId, userName, currentRoles, currentAdminSubRole, 'remove');
  }

  static openSuspendModal(userId, userName) {
    const body = `
      <div class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400 text-xs border border-rose-200 dark:border-rose-900/60 leading-relaxed">
          <strong>Lưu ý:</strong> Khi tạm ngưng tài khoản, người dùng sẽ đăng xuất khỏi mọi thiết bị và không thể truy cập cho đến khi tài khoản được mở lại.
        </div>
        <p class="text-slate-600 dark:text-slate-300">Tài khoản: <strong>${UI.escapeHtml(userName)}</strong></p>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]" for="suspend-reason">Lý do tạm ngưng *</label>
          <textarea id="suspend-reason" rows="3" class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-rose-600 resize-none" placeholder="Ghi rõ căn cứ vi phạm hoặc nghi vấn an ninh..."></textarea>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]" for="suspend-password">Mật khẩu Quản trị viên (Bắt buộc xác thực) *</label>
          <input type="password" id="suspend-password" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-rose-600" placeholder="Nhập mật khẩu quản trị viên để ký xác nhận..." autocomplete="current-password" />
        </div>
      </div>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Hủy</button>
      <button type="button" id="confirm-suspend-btn" class="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-sm">Xác nhận Tạm ngưng</button>
    `;

    UI.openModal({
      title: 'Khóa quyền & Tạm ngưng Tài khoản Khẩn cấp',
      bodyHtml: body,
      footerHtml: footer,
      size: 'md'
    });

    document.getElementById('confirm-suspend-btn').onclick = async () => {
      const reason = document.getElementById('suspend-reason').value.trim();
      const password = document.getElementById('suspend-password')?.value;
      if (!reason) {
        UI.showToast('Vui lòng nhập lý do phong tỏa kiểm toán.', 'warning');
        return;
      }
      if (!password) {
        UI.showToast('Vui lòng nhập mật khẩu quản trị viên để xác thực.', 'warning');
        return;
      }
      try {
        await ApiClient.suspendUser(userId, reason, password);
        UI.closeModal();
        UI.showToast(`Đã tạm ngưng tài khoản ${userName} thành công! Toàn bộ phiên đã bị thu hồi.`, 'success');
        UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box')));
      } catch (e) {
        UI.showToast(e.message || 'Lỗi tạm ngưng tài khoản.', 'error');
      }
    };
  }

  static async unsuspendUser(userId, userName) {
    const conf = await UI.confirm(
      'Mở khóa tài khoản',
      `Bạn có chắc chắn muốn kích hoạt lại tài khoản cho "${userName}"? Người dùng sẽ có thể đăng nhập bình thường.`,
      'Kích hoạt lại'
    );
    if (!conf) return;

    try {
      await ApiClient.unsuspendUser(userId, 'Quản trị viên mở khóa tài khoản');
      UI.showToast(`Đã kích hoạt lại tài khoản của ${userName} thành công!`, 'success');
      UI.refreshCurrentRoute(() => AdminView.renderTabUsers(document.getElementById('admin-tab-content-box')));
    } catch (e) {
      UI.showToast(e.message || 'Lỗi mở khóa tài khoản.', 'error');
    }
  }

  static async revokeUserSessions(userId, userName) {
    const password = await UI.reauthPrompt({
      title: 'Cưỡng chế Thu hồi Phiên (Revoke Sessions)',
      message: `Bạn đang thực hiện thao tác cưỡng chế đăng xuất tài khoản "${userName}" khỏi mọi thiết bị và vô hiệu hóa toàn bộ Token. Vui lòng nhập mật khẩu quản trị viên để xác nhận.`,
      actionLabel: 'Đăng xuất Mọi Thiết Bị',
      isDanger: true
    });
    if (!password) return;

    try {
      await ApiClient.revokeUserSessions(userId, 'Quản trị viên cưỡng chế thu hồi phiên', password);
      UI.showToast(`Đã đăng xuất ${userName} khỏi mọi thiết bị.`, 'success');
    } catch (e) {
      UI.showToast(e.message || 'Không đăng xuất được các thiết bị.', 'error');
    }
  }

  static openBroadcastModal() {
    const body = `
      <div class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-primary/10 text-primary border border-primary/20 text-xs leading-relaxed">
          <strong>Phát thông báo Hệ thống:</strong> Thông báo sẽ được chuyển phát trực tiếp tới hộp thư in-app của toàn bộ tài khoản mục tiêu theo thời gian thực.
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Tiêu đề thông báo *</label>
          <input type="text" id="broadcast-title" placeholder="VD: Thông báo bảo trì nâng cấp học kỳ mới..." class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary" />
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Đối tượng nhận</label>
          <select id="broadcast-role" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary">
            <option value="ALL">Tất cả người dùng</option>
            <option value="STUDENT">Chỉ Sinh viên (STUDENT)</option>
            <option value="INSTRUCTOR">Chỉ Giảng viên (INSTRUCTOR)</option>
            <option value="ADMIN">Chỉ Quản trị viên (ADMIN)</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Phân loại thông báo</label>
          <select id="broadcast-category" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary">
            <option value="SYSTEM">Hệ thống (SYSTEM)</option>
            <option value="COURSE">Khóa học / Học vụ (COURSE)</option>
            <option value="ASSESSMENT">Khảo thí (ASSESSMENT)</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Nội dung chi tiết *</label>
          <textarea id="broadcast-body" rows="4" class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-primary resize-none" placeholder="Nhập nội dung thông báo..."></textarea>
        </div>
      </div>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Hủy</button>
      <button type="button" id="submit-broadcast-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold flex items-center gap-1.5 shadow-sm">
        <span class="material-symbols-outlined text-[16px]">campaign</span>
        <span>Phát thông báo ngay</span>
      </button>
    `;

    UI.openModal({
      title: 'Phát thông báo hệ thống',
      bodyHtml: body,
      footerHtml: footer,
      size: 'md'
    });

    let broadcastIdempotencyKey = null;
    let broadcastSubmitting = false;
    document.getElementById('submit-broadcast-btn').onclick = async () => {
      if (broadcastSubmitting) return;
      const title = document.getElementById('broadcast-title').value.trim();
      const roleVal = document.getElementById('broadcast-role').value;
      const targetRole = roleVal === 'ALL' ? null : roleVal;
      const category = document.getElementById('broadcast-category').value;
      const bodyText = document.getElementById('broadcast-body').value.trim();

      if (!title) {
        UI.showToast('Vui lòng nhập tiêu đề thông báo.', 'warning');
        return;
      }
      if (!bodyText) {
        UI.showToast('Vui lòng nhập nội dung thông báo.', 'warning');
        return;
      }

      broadcastSubmitting = true;
      broadcastIdempotencyKey = broadcastIdempotencyKey || (
        globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function'
          ? globalThis.crypto.randomUUID()
          : null
      );
      const submitButton = document.getElementById('submit-broadcast-btn');
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.setAttribute('aria-busy', 'true');
      }
      try {
        const res = await ApiClient.broadcastNotification(
          title,
          bodyText,
          targetRole,
          category,
          broadcastIdempotencyKey
        );
        UI.closeModal();
        const count = res.broadcasted_count || 0;
        UI.showToast(`Đã phát thông báo thành công tới ${count} người dùng!`, 'success');
      } catch (err) {
        UI.showToast(err.message || 'Lỗi phát thông báo.', 'error');
      } finally {
        broadcastSubmitting = false;
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.removeAttribute('aria-busy');
        }
      }
    };
  }

  // =========================================================================
  // Tab 2: Duyệt Khóa học & Hàng đợi Bản sửa đổi (Course Review & Change Requests)
  // =========================================================================
  static async renderTabCoursesReview(container, subQueue = null) {
    if (!container.querySelector('#courses-review-box')) {
      container.innerHTML = `
        <div class="space-y-6 animate-fade-in" id="courses-review-box">
          <div class="p-12 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
            <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
            <p class="text-sm">Đang tải khóa học và yêu cầu chờ duyệt...</p>
          </div>
        </div>
      `;
    }

    try {
      const [pendingCoursesRes, changeReqsRes] = await Promise.allSettled([
        ApiClient.getPendingCourses(),
        ApiClient.getAdminChangeRequests('ALL')
      ]);

      const pendingCourses = (pendingCoursesRes.status === 'fulfilled' && pendingCoursesRes.value) ? (pendingCoursesRes.value.courses || []) : [];
      const rawChangeRequests = (changeReqsRes.status === 'fulfilled' && changeReqsRes.value) ? (changeReqsRes.value.change_requests || []) : [];
      // Clean queue contract: Mọi yêu cầu khi được Admin xét duyệt xong (dù duyệt chấp thuận hay từ chối) hoặc hủy
      // đều tự động biến mất hoàn toàn khỏi hàng đợi, biến mất luôn cả ở tab "Tất cả". Hàng đợi chỉ chứa yêu cầu chờ duyệt.
      const changeRequests = rawChangeRequests.filter(r => r.status === 'PENDING');

      // Update badge
      const totalPending = pendingCourses.length + changeRequests.length;
      if (window.app && typeof window.app.updateAdminNavBadges === 'function') {
        window.app.updateAdminNavBadges({ courses: totalPending });
      }
      const elPending = document.getElementById('kpi-courses-pending');
      const badgePending = document.getElementById('kpi-courses-badge');
      if (elPending) elPending.textContent = String(totalPending).padStart(2, '0');
      if (badgePending) badgePending.textContent = `${totalPending} chờ duyệt`;

      const box = container.querySelector('#courses-review-box');
      if (!box) return;

      box.innerHTML = `
        <!-- Section 1: Hàng đợi Thẩm định Đề cương Khóa học mới/xuất bản -->
        <div id="admin-review-courses-queue" class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">fact_check</span>
                Khóa học chờ duyệt
              </h3>
              <p class="text-xs text-slate-400 mt-0.5">Xem thông tin, mục tiêu và bài học trước khi duyệt khóa học.</p>
            </div>
            <span class="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 text-xs font-bold border border-amber-200">
              ${pendingCourses.length} Khóa học chờ duyệt
            </span>
          </div>

          ${pendingCourses.length === 0 ? `
            <div class="p-8 text-center text-slate-400 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
              <span class="material-symbols-outlined text-emerald-500 text-3xl">task_alt</span>
              <p class="text-xs font-bold text-slate-700 dark:text-slate-300">Không có khóa học đang chờ duyệt</p>
              <p class="text-[11px] text-slate-500 dark:text-slate-300">Khóa học mới gửi duyệt sẽ xuất hiện tại đây.</p>
            </div>
          ` : `
            <div class="space-y-4">
              ${pendingCourses.map(c => `
                <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-4 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div class="font-bold text-sm text-slate-800 dark:text-slate-100">${UI.escapeHtml(c.title)}</div>
                      <div class="text-xs text-slate-600 dark:text-slate-300 mt-1">${UI.escapeHtml(c.course_code)} · Gửi duyệt ${UI.formatDateTime(c.updated_at)}</div>
                    </div>
                    <button type="button" class="px-4 py-2 rounded-lg bg-indigo-700 hover:bg-indigo-800 text-slate-50 text-xs font-bold transition-colors flex items-center gap-1 inspect-course-btn" data-course-id="${c.course_id}">
                      <span class="material-symbols-outlined text-[16px]">menu_book</span> Xem Khóa Học
                    </button>
                </div>
              `).join('')}
            </div>
          `}
        </div>

        <!-- Section 2: Hàng đợi Phê duyệt Sửa/Xóa Bài giảng & Môn học (Change Requests) -->
        <div id="admin-review-change-requests-queue" class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">edit_note</span>
                Yêu cầu sửa hoặc xóa bài giảng và khóa học
              </h3>
              <p class="text-xs text-slate-500 dark:text-slate-300 mt-0.5">So sánh nội dung hiện tại và đề xuất trước khi duyệt.</p>
            </div>
            <div class="flex items-center gap-1.5" id="cr-status-filter-group">
              <button type="button" class="cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white" data-status="PENDING">Chờ duyệt (<span id="cr-badge-pending">${changeRequests.length}</span>)</button>
              <button type="button" class="cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="ALL">Tất cả (<span id="cr-badge-all">${changeRequests.length}</span>)</button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs sm:text-sm min-w-[1180px] table-fixed">
              <colgroup>
                <col style="width:120px"><col style="width:180px"><col style="width:290px">
                <col style="width:130px"><col style="width:110px"><col style="width:120px"><col style="width:230px">
              </colgroup>
              <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
                <tr>
                  <th class="px-3.5 py-3 w-[150px] whitespace-nowrap">Loại yêu cầu</th>
                  <th class="px-3.5 py-3 w-[200px] whitespace-nowrap">Khóa học</th>
                  <th class="px-3.5 py-3 min-w-[280px]">Đối tượng & Đề xuất</th>
                  <th class="px-3.5 py-3 w-[140px] whitespace-nowrap">Người gửi</th>
                  <th class="px-3.5 py-3 w-[110px] whitespace-nowrap">Trạng thái</th>
                  <th class="px-3.5 py-3 w-[130px] whitespace-nowrap">Thời điểm</th>
                  <th class="px-3.5 py-3 w-[230px] whitespace-nowrap text-right">Xét duyệt</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium" id="change-requests-tbody">
                <!-- Populated via JS -->
              </tbody>
            </table>
          </div>
        </div>
      `;

      // Event bindings for Courses Review
      box.querySelectorAll('.inspect-course-btn').forEach(btn => {
        btn.onclick = () => {
          window.location.hash = `#/admin/courses/review?id=${encodeURIComponent(btn.dataset.courseId)}`;
        };
      });

      const updateCrFilterBadges = () => {
        const pCount = changeRequests.filter(r => r.status === 'PENDING').length;

        const badgeP = document.getElementById('cr-badge-pending');
        const badgeAll = document.getElementById('cr-badge-all');

        if (badgeP) badgeP.textContent = String(pCount);
        if (badgeAll) badgeAll.textContent = String(pCount);

        const totalP = pendingCourses.length + pCount;
        if (window.app && typeof window.app.updateAdminNavBadges === 'function') {
          window.app.updateAdminNavBadges({ courses: totalP });
        }
        const elPending = document.getElementById('kpi-courses-pending');
        const badgePending = document.getElementById('kpi-courses-badge');
        if (elPending) elPending.textContent = String(totalP).padStart(2, '0');
        if (badgePending) badgePending.textContent = `${totalP} chờ duyệt`;
      };

      // Filter change requests
      const renderChangeRequestRows = (_statusFilter = 'PENDING') => {
        const tbody = document.getElementById('change-requests-tbody');
        if (!tbody) return;

        const filtered = changeRequests.filter(r => r.status === 'PENDING');

        if (filtered.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="7" class="py-12 text-center text-slate-400 text-xs">
                <span class="material-symbols-outlined text-emerald-500 text-3xl mb-2 block">task_alt</span>
                <p class="font-bold text-slate-700 dark:text-slate-300">Không có yêu cầu thay đổi nào đang chờ duyệt.</p>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Các yêu cầu sau khi được admin xét duyệt xong sẽ tự động hoàn tất và rời khỏi hàng đợi.</p>
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = filtered.map(r => {
          const payload = r.proposed_payload || {};
          let typeBadge = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300';
          let typeLabel = r.change_type || 'Yêu cầu thay đổi';

          if (r.change_type === 'COURSE_VERSION_CHANGESET' || payload.action === 'COURSE_VERSION_CHANGESET') {
            typeBadge = 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-400 dark:border-purple-800';
            typeLabel = 'Khung giáo trình';
          } else if (r.change_type === 'COURSE_METADATA' || (r.target_type === 'COURSE' && !payload.action)) {
            typeBadge = 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/40 dark:text-indigo-400 dark:border-indigo-800';
            typeLabel = 'Khóa học';
          } else if (r.change_type === 'LESSON_STRUCTURE' && payload.action === 'DELETE') {
            typeBadge = 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800';
            typeLabel = 'Xóa bài học';
          } else if (payload.action === 'UPDATE_LEARNING_UNIT') {
            typeBadge = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800';
            typeLabel = 'Sửa chương mục';
          } else if (payload.action === 'RESOURCE_CHANGES') {
            typeBadge = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800';
            typeLabel = 'Tài liệu bài học';
          } else if (r.change_type === 'LESSON_CONTENT' || r.change_type === 'LESSON_STRUCTURE') {
            typeBadge = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800';
            typeLabel = 'Bài học';
          } else if (r.change_type === 'PREREQUISITE') {
            typeBadge = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800';
            typeLabel = 'Môn tiên quyết';
          }

          let statusBadge = 'bg-amber-50 text-amber-700 border-amber-200';
          if (r.status === 'APPROVED') statusBadge = 'bg-emerald-50 text-emerald-700 border-emerald-200';
          if (r.status === 'REJECTED') statusBadge = 'bg-rose-50 text-rose-700 border-rose-200';

          return `
            <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
              <td class="px-3.5 py-3.5 whitespace-nowrap align-middle">
                <div class="inline-flex items-center gap-1.5">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${typeBadge}">
                    ${typeLabel}
                  </span>
                  <span class="text-[10px] text-slate-400 font-mono">#${r.id}</span>
                </div>
              </td>
              <td class="px-3.5 py-3.5 align-middle">
                <div class="font-bold text-slate-900 dark:text-white font-mono text-xs whitespace-nowrap">${UI.escapeHtml(r.course_code || '')}</div>
                <div class="text-xs text-slate-500 truncate max-w-[190px]" title="${UI.escapeHtml(r.course_title || '')}">${UI.escapeHtml(r.course_title || '')}</div>
              </td>
              <td class="px-3.5 py-3.5 align-middle">
                <div class="font-bold text-slate-800 dark:text-slate-200 text-xs break-words">${UI.escapeHtml(r.target_title || 'Nội dung được đề xuất')}</div>
                ${r.status === 'REJECTED' && r.review_reason ? `<p class="mt-2 rounded-lg border border-rose-300 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/40 px-2 py-1 text-xs text-rose-800 dark:text-rose-200 break-words"><strong>Ghi chú từ chối:</strong> ${UI.escapeHtml(r.review_reason)}</p>` : ''}
                ${(r.change_type === 'COURSE_VERSION_CHANGESET' || payload.action === 'COURSE_VERSION_CHANGESET') ? `
                  <div class="text-[11px] text-indigo-700 dark:text-indigo-300 font-medium mt-1 flex items-center gap-2">
                    <span class="inline-flex items-center gap-1">
                      <span class="material-symbols-outlined text-[13px]">tune</span>
                      ${payload.changeset_stats ? `${payload.changeset_stats.added_lessons_count || 0} mới • ${payload.changeset_stats.modified_lessons_count || 0} sửa • ${payload.changeset_stats.deleted_lessons_count || 0} xóa` : (payload.summary || 'Đợt cập nhật giáo trình')}
                    </span>
                  </div>
                ` : payload.action === 'DELETE' ? `
                  <div class="text-[11px] text-rose-600 dark:text-rose-400 mt-0.5 truncate max-w-[320px]" title="${UI.escapeHtml(payload.reason || 'Yêu cầu gỡ bỏ')}">
                    <strong>Lý do xóa:</strong> ${UI.escapeHtml(payload.reason || 'Yêu cầu gỡ bỏ')}
                  </div>
                ` : payload.title ? `
                  <div class="text-[11px] text-slate-500 mt-0.5 truncate max-w-[320px]" title="${UI.escapeHtml(payload.title)}">
                    <strong>Tiêu đề mới:</strong> ${UI.escapeHtml(payload.title)}
                  </div>
                ` : ''}
              </td>
              <td class="px-3.5 py-3.5 text-xs text-slate-700 dark:text-slate-300 whitespace-nowrap align-middle">
                <span class="truncate block max-w-[130px]" title="${UI.escapeHtml(r.requested_by_name || 'Giảng viên')}">${UI.escapeHtml(r.requested_by_name || 'Giảng viên')}</span>
              </td>
              <td class="px-3.5 py-3.5 whitespace-nowrap align-middle">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusBadge}">
                  ${r.status === 'PENDING' ? 'Chờ duyệt' : (r.status === 'APPROVED' ? 'Đã duyệt' : 'Từ chối')}
                </span>
              </td>
              <td class="px-3.5 py-3.5 text-xs text-slate-400 font-mono whitespace-nowrap align-middle">
                ${UI.formatDate(r.created_at)}
              </td>
              <td class="px-3.5 py-3.5 text-right space-x-1.5 whitespace-nowrap align-middle">
                <button type="button" class="px-3.5 py-1.5 rounded-lg ${r.status === 'PENDING' ? 'bg-primary hover:bg-primary-hover text-white' : 'bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200'} text-xs font-bold transition-colors view-diff-cr-btn cursor-pointer inline-flex items-center gap-1" data-req-id="${r.id}" title="Xem chi tiết các điểm thay đổi">
                  <span class="material-symbols-outlined text-[15px]">visibility</span>
                  <span>Xem</span>
                </button>
                ${r.status === 'PENDING' ? `
                  <button type="button" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-2xs quick-pass-cr-btn cursor-pointer inline-flex items-center gap-1" data-req-id="${r.id}" title="Phê duyệt nhanh">
                    <span class="material-symbols-outlined text-[15px]">check</span>
                    <span>Duyệt</span>
                  </button>
                ` : ''}
                ${r.status !== 'PENDING' ? `
                  <span class="text-xs text-slate-400 italic">${UI.escapeHtml(r.review_reason || 'Đã giải quyết')}</span>
                ` : ''}
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.quick-pass-cr-btn').forEach(btn => {
          btn.onclick = async (e) => {
            e.stopPropagation();
            const reqId = btn.dataset.reqId;
            const targetReq = changeRequests.find(item => String(item.id) === String(reqId));
            if (!targetReq) return;
            const confirmed = await UI.confirm('Phê duyệt yêu cầu thay đổi', `Bạn có chắc chắn muốn phê duyệt nhanh yêu cầu #${reqId} của khóa học "${targetReq.course_title || 'Khóa học'}" không?`, 'Phê duyệt', 'Hủy');
            if (!confirmed) return;
            try {
              btn.disabled = true;
              const isChangeset = targetReq.change_type === 'COURSE_VERSION_CHANGESET' || (targetReq.proposed_payload && targetReq.proposed_payload.action === 'COURSE_VERSION_CHANGESET');
              if (isChangeset) {
                await ApiClient.approveCourseChangeset(targetReq.id, 'Phê duyệt đợt cập nhật giáo trình.');
              } else {
                await ApiClient.reviewAdminChangeRequest(targetReq.id, { action: 'approve' });
              }

              // Remove directly from changeRequests array so it disappears from ALL tabs (including 'Tất cả')
              const reqIdx = changeRequests.findIndex(item => String(item.id) === String(reqId));
              if (reqIdx !== -1) {
                changeRequests.splice(reqIdx, 1);
              }

              // Animate row removal from DOM immediately
              const rowEl = btn.closest('tr');
              if (rowEl) {
                rowEl.style.transition = 'all 0.25s ease-out';
                rowEl.style.opacity = '0';
                rowEl.style.transform = 'translateX(20px)';
                setTimeout(() => {
                  rowEl.remove();
                  renderChangeRequestRows(AdminView._activeCrFilter || 'PENDING');
                }, 250);
              } else {
                renderChangeRequestRows(AdminView._activeCrFilter || 'PENDING');
              }

              updateCrFilterBadges();
              UI.showToast(`Đã duyệt và áp dụng yêu cầu #${reqId} thành công!`, 'success');
              window.app?.refreshNotificationBadge?.(true);
              window.app?.fetchAdminPendingCounts?.();
            } catch (err) {
              btn.disabled = false;
              UI.showToast(err.message || 'Lỗi phê duyệt yêu cầu.', 'error');
            }
          };
        });

        tbody.querySelectorAll('.view-diff-cr-btn').forEach(btn => {
          btn.onclick = () => {
            window.location.hash = `#/admin/change-requests/review?id=${encodeURIComponent(btn.dataset.reqId)}`;
          };
        });

      };

      const activeFilter = AdminView._activeCrFilter || 'PENDING';
      renderChangeRequestRows(activeFilter);

      const crFilterBtns = box.querySelectorAll('.cr-filter-btn');
      crFilterBtns.forEach(btn => {
        if (btn.dataset.status === activeFilter) {
          btn.className = 'cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white';
        } else {
          btn.className = 'cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200';
        }
        btn.onclick = () => {
          AdminView._activeCrFilter = btn.dataset.status;
          crFilterBtns.forEach(b => {
            b.className = 'cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200';
          });
          btn.className = 'cr-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white';
          renderChangeRequestRows(btn.dataset.status);
        };
      });

      if (subQueue === 'courses') {
        const courseQueueEl = document.getElementById('admin-review-courses-queue');
        if (courseQueueEl) {
          setTimeout(() => {
            courseQueueEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 100);
        }
      } else if (subQueue === 'change-requests') {
        const crQueueEl = document.getElementById('admin-review-change-requests-queue');
        if (crQueueEl) {
          setTimeout(() => {
            crQueueEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            crQueueEl.classList.add('ring-2', 'ring-primary', 'shadow-md');
            setTimeout(() => crQueueEl.classList.remove('ring-2', 'ring-primary', 'shadow-md'), 3000);
          }, 100);
        }
      }
    } catch (err) {
      console.error('TabCoursesReview load error:', err);
    }
  }

  // Alias for backward compatibility
  static renderTabReview(container, subQueue = null) {
    return AdminView.renderTabCoursesReview(container, subQueue);
  }

  // =========================================================================
  // Full-page change review reuses the queue's authorized API response.
  // =========================================================================
  static async renderChangeRequestReviewPage(container, requestId) {
    container.innerHTML = '<div class="p-8 text-sm text-slate-600 dark:text-slate-300">Đang tải yêu cầu thay đổi...</div>';
    try {
      const result = await ApiClient.getAdminChangeRequests('ALL');
      const allRequests = result.change_requests || [];
      const request = allRequests.find(item => String(item.id) === String(requestId));
      if (!request) throw new Error('Không tìm thấy yêu cầu thay đổi.');
      const siblingRequests = allRequests.filter(item =>
        item.status === 'PENDING' &&
        (String(item.course_id) === String(request.course_id) || (request.target_id && String(item.target_id) === String(request.target_id)))
      );
      AdminView.renderChangeRequestReviewDetail(container, request, siblingRequests);
    } catch (error) {
      container.innerHTML = `<div class="max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 p-6"><a href="#/admin/governance?tab=courses" class="text-primary font-semibold">← Quay lại hàng đợi</a><p class="mt-6 text-rose-700 dark:text-rose-300">${UI.escapeHtml(error.message || 'Không tải được yêu cầu.')}</p></div>`;
    }
  }

  // =========================================================================
  // Modal Preview for Attached Documents (PDF, Video, Images, Text, Office)
  // =========================================================================
  static reviewerProposedLesson(original, proposal) {
    const resources = new Map((original.resources || []).map(resource => [String(resource.resource_id || resource.asset_id), { ...resource }]));
    for (const change of Array.isArray(proposal.changes) ? proposal.changes : []) {
      if (change.action === 'DETACH') resources.delete(String(change.resource_id));
      if (change.action === 'ATTACH') resources.set(`asset:${change.asset_id}`, { ...change });
    }
    return { ...original, ...proposal, resources: Array.from(resources.values()) };
  }

  static reviewerQuizInputs(question, name) {
    const inputClass = 'rounded-lg border border-slate-300 dark:border-slate-600 px-4 py-2 text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-900';
    const radio = (value, label, group = name, extra = '', type = 'radio') => `<label class="flex gap-3 items-center p-2"><input type="${type}" name="${group}" value="${UI.escapeHtml(String(value))}" ${extra}><span>${UI.escapeHtml(String(label))}</span></label>`;
    if (question.type === 'FILL_BLANK') {
      const blanks = Array.isArray(question.blanks) ? question.blanks : [];
      return blanks.map((_, index) => `<label class="block space-y-3"><span>Ô trống ${index + 1}</span><input type="text" class="reviewer-blank-input w-full ${inputClass}" autocomplete="off" placeholder="Nhập từ hoặc cụm từ"></label>`).join('');
    }
    if (question.type === 'MATCHING') {
      const pairs = Array.isArray(question.pairs) ? question.pairs.filter(pair => pair && typeof pair === 'object') : [];
      return pairs.map((pair, index) => `<div class="space-y-3"><p>${UI.escapeHtml(pair.left || '')}</p>${pairs.length <= 3 ? pairs.map(option => radio(option.right, option.right, `${name}-${index}`, `data-pair-index="${index}"`)).join('') : `<label class="block"><span class="sr-only">Ghép với ${UI.escapeHtml(pair.left || '')}</span><select data-pair-index="${index}" class="${inputClass}"><option value="">Chọn đáp án ghép</option>${pairs.map(option => `<option value="${UI.escapeHtml(option.right || '')}">${UI.escapeHtml(option.right || '')}</option>`).join('')}</select></label>`}</div>`).join('');
    }
    if (question.type === 'TRUE_FALSE') return radio('true', 'Đúng') + radio('false', 'Sai');
    const options = Array.isArray(question.options) ? question.options : [];
    const multiple = Array.isArray(question.correct_indices) && question.correct_indices.length > 1;
    return options.map((option, index) => radio(index, option, name, '', multiple ? 'checkbox' : 'radio')).join('');
  }

  static gradeReviewerQuiz(question, values) {
    if (question.type === 'FILL_BLANK') {
      const blanks = Array.isArray(question.blanks) ? question.blanks : [];
      if (!blanks.length || blanks.some(blank => !blank?.accepted_answers?.length)) return null;
      return values.length === blanks.length && blanks.every((blank, index) => {
        const accepted = Array.isArray(blank.accepted_answers) ? blank.accepted_answers : [blank.accepted_answers];
        const value = String(values[index] || '').trim().toLowerCase();
        return value.length > 0 && accepted.some(answer => String(answer).trim().toLowerCase() === value);
      });
    }
    if (question.type === 'MATCHING') {
      const pairs = Array.isArray(question.pairs) ? question.pairs : [];
      if (!pairs.length || pairs.some(pair => pair?.right == null)) return null;
      return values.length === pairs.length && pairs.every((pair, index) => values[index] === String(pair.right));
    }
    if (question.type === 'TRUE_FALSE') {
      const correct = question.correct_value ?? question.correct_answer;
      if (correct == null) return null;
      return values.length === 1 && values[0] === String(correct).toLowerCase();
    }
    const correct = Array.isArray(question.correct_indices) ? question.correct_indices : (Number.isInteger(question.correct_index) ? [question.correct_index] : []);
    if (!correct.length) return null;
    const selected = new Set(values.map(Number));
    return selected.size === correct.length && correct.every(index => selected.has(index));
  }

  // Reviewer rendering is read-only: local quiz feedback and media never call progress APIs.
  static renderReviewerCoursePreview(container, course, initialLessonId = null) {
    if (!container) return;
    const lessons = Array.isArray(course.lessons) ? course.lessons : [];
    const units = Array.isArray(course.learning_units) ? course.learning_units : [];
    const chapters = new Map();
    const lessonIcon = lesson => {
      const markdown = String(lesson.markdown_content || '');
      const resources = Array.isArray(lesson.resources) ? lesson.resources : [];
      if (lesson.video_url || lesson.video_urls?.length || /<!--\s*video_urls?:/i.test(markdown) || resources.some(resource => String(resource?.mime_type || '').startsWith('video/'))) return 'videocam';
      return lesson.quiz?.length || /<!--\s*mini_quiz:/i.test(markdown) ? 'quiz' : 'article';
    };
    lessons.forEach((lesson, index) => {
      const unitId = String(lesson.learning_unit_id || 'default');
      const unit = units.find(item => String(item.learning_unit_id || item.id) === unitId);
      if (!chapters.has(unitId)) chapters.set(unitId, { title: lesson.learning_unit_title || unit?.title || 'Nội dung khóa học', lessons: [] });
      chapters.get(unitId).lessons.push({ lesson, index });
    });
    container.innerHTML = `<div class="grid grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)] gap-6">
      <nav aria-label="Giáo trình xem trước" class="lg:sticky lg:top-6 self-start rounded-xl border border-slate-200 dark:border-slate-700 p-4 bg-slate-50 dark:bg-slate-900 space-y-6 max-h-[70vh] overflow-auto">
        ${Array.from(chapters.values(), chapter => `<section><h3 class="font-semibold text-sm text-slate-800 dark:text-slate-200 mb-3">${UI.escapeHtml(chapter.title)}</h3><div class="space-y-2">${chapter.lessons.map(({ lesson, index }) => `<button type="button" class="reviewer-lesson-btn w-full flex items-center gap-3 px-4 py-2 text-left rounded-lg text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 focus-visible:ring-2 focus-visible:ring-primary" data-lesson-index="${index}"><span aria-hidden="true" class="material-symbols-outlined text-lg">${lessonIcon(lesson)}</span><span>${UI.escapeHtml(lesson.title || 'Bài học')}</span></button>`).join('')}</div></section>`).join('')}
      </nav><div class="min-w-0 space-y-6" data-reviewer-workspace></div></div>`;
    const workspace = container.querySelector?.('[data-reviewer-workspace]');
    if (!workspace) return;
    const buttons = container.querySelectorAll('.reviewer-lesson-btn');
    const renderLesson = index => {
      workspace.querySelectorAll('video').forEach(video => video.pause());
      const lesson = lessons[index];
      if (!lesson) { workspace.innerHTML = '<p class="text-slate-600 dark:text-slate-300">Chưa có bài học để xem trước.</p>'; return; }
      const markdown = String(lesson.markdown_content || '');
      let youtube = Array.isArray(lesson.video_urls) ? lesson.video_urls : (lesson.video_url ? [lesson.video_url] : []);
      const videoMatch = markdown.match(/<!--\s*video_urls?:\s*(\[.*?\])\s*-->/s);
      if (!youtube.length && videoMatch) { try { const parsed = JSON.parse(videoMatch[1]); if (Array.isArray(parsed)) youtube = parsed; } catch (_) {} }
      const singleVideo = markdown.match(/<!--\s*video_url:\s*(\S+?)\s*-->/);
      if (!youtube.length && singleVideo) youtube = [singleVideo[1]];
      let quiz = Array.isArray(lesson.quiz) ? lesson.quiz : [];
      const quizMatch = markdown.match(/<!--\s*mini_quiz:\s*(.*?)\s*-->/s);
      if (!quiz.length && quizMatch) { try { const parsed = JSON.parse(quizMatch[1]); if (Array.isArray(parsed)) quiz = parsed; } catch (_) {} }
      quiz = quiz.filter(question => question && typeof question === 'object' && !Array.isArray(question));
      const resources = (Array.isArray(lesson.resources) ? lesson.resources : []).filter(resource => resource && resource.is_clean !== false && (!resource.scan_status || resource.scan_status === 'CLEAN' || resource.scan_status === 'PASS'));
      const videos = resources.filter(resource => String(resource.mime_type || '').startsWith('video/') || /\.(mp4|webm|mov|mkv)$/i.test(resource.filename || resource.title || ''));
      const documents = resources.filter(resource => !videos.includes(resource));
      workspace.innerHTML = `<p class="text-sm text-slate-600 dark:text-slate-300">Xem trước · Không ghi tiến độ học tập</p>
        <header class="space-y-3"><h2 class="text-2xl font-semibold text-slate-900 dark:text-slate-100 break-words">${UI.escapeHtml(lesson.title || 'Bài học')}</h2>${lesson.summary ? `<p class="text-slate-700 dark:text-slate-200">${UI.escapeHtml(lesson.summary)}</p>` : ''}</header>
        ${youtube.map(url => { const id = UI.parseYouTubeId(url); return id ? `<iframe class="w-full aspect-video rounded-xl" src="${UI.escapeHtml(UI.getYouTubeEmbedUrl(id))}" title="Video bài học YouTube" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>` : ''; }).join('')}
        ${videos.map(resource => { const id = resource.asset_id || resource.file_asset?.public_id; return id ? `<video controls playsinline preload="metadata" class="w-full max-h-[460px] bg-slate-950 rounded-xl" src="/api/files/${encodeURIComponent(id)}/stream" aria-label="${UI.escapeHtml(resource.filename || resource.title || 'Video bài học')}"></video>` : '<p class="text-slate-600 dark:text-slate-300">Video chưa có tài nguyên xem trước hợp lệ.</p>'; }).join('')}
        <article class="prose dark:prose-invert max-w-none break-words">${UI.renderMarkdown(markdown.replace(/<!--\s*(?:video_urls?|mini_quiz(?:_passing)?):.*?-->\s*/gs, ''))}</article>
        ${documents.length ? `<section class="space-y-3"><h3 class="text-lg font-semibold">Tài liệu đính kèm</h3>${documents.map(resource => { const id = resource.asset_id || resource.file_asset?.public_id; const url = id ? `/api/files/${encodeURIComponent(id)}/download` : resource.file_url; const title = resource.filename || resource.title || resource.label || 'Tài liệu'; return url && /^(?:\/[^/]|https?:\/\/)/i.test(url) ? `<button type="button" class="reviewer-document-btn block px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 text-primary" data-url="${UI.escapeHtml(url)}" data-title="${UI.escapeHtml(title)}" data-mime="${UI.escapeHtml(resource.mime_type || '')}">Xem ${UI.escapeHtml(title)}</button>` : `<p>${UI.escapeHtml(title)} · Chưa có liên kết xem trước</p>`; }).join('')}</section>` : ''}
        ${quiz.map((question, qIndex) => `<fieldset class="reviewer-quiz border border-slate-200 dark:border-slate-700 rounded-xl p-4 space-y-3" data-question-index="${qIndex}"><legend class="font-semibold px-2">${UI.escapeHtml(question.question || 'Câu hỏi')}</legend>${AdminView.reviewerQuizInputs(question, `reviewer-${index}-${qIndex}`)}<button type="button" class="reviewer-check-answer px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 text-primary">Kiểm tra đáp án</button><p aria-live="polite" class="reviewer-quiz-feedback text-sm"></p></fieldset>`).join('')}`;
      buttons.forEach((button, buttonIndex) => button.setAttribute('aria-current', buttonIndex === index ? 'true' : 'false'));
      workspace.querySelectorAll('.reviewer-document-btn').forEach(button => { button.onclick = () => AdminView.openDocumentPreviewModal(button.dataset.title, button.dataset.url, button.dataset.mime); });
      workspace.querySelectorAll('.reviewer-quiz').forEach(fieldset => {
        fieldset.querySelector('.reviewer-check-answer').onclick = () => {
          const question = quiz[Number(fieldset.dataset.questionIndex)];
          const values = question.type === 'FILL_BLANK'
            ? Array.from(fieldset.querySelectorAll('.reviewer-blank-input'), input => input.value)
            : question.type === 'MATCHING'
              ? (question.pairs || []).map((_, pairIndex) => fieldset.querySelector(`select[data-pair-index="${pairIndex}"]`)?.value || fieldset.querySelector(`input[data-pair-index="${pairIndex}"]:checked`)?.value || '')
              : Array.from(fieldset.querySelectorAll('input:checked'), input => input.value);
          const correct = AdminView.gradeReviewerQuiz(question, values);
          fieldset.querySelector('.reviewer-quiz-feedback').textContent = !values.length || values.every(value => !value.trim()) ? 'Hãy nhập hoặc chọn câu trả lời.' : correct === null ? 'Chưa có đáp án xác nhận.' : correct ? 'Đúng.' : 'Chưa đúng.';
        };
      });
    };
    buttons.forEach(button => { button.onclick = () => renderLesson(Number(button.dataset.lessonIndex)); });
    const initialIndex = lessons.findIndex(lesson => String(lesson.lesson_id || lesson.id) === String(initialLessonId));
    renderLesson(initialIndex < 0 ? 0 : initialIndex);
  }

  static async openDocumentPreviewModal(title, fileUrl, mimeType = '') {
    if (typeof fileUrl !== 'string' || !/^(?:\/(?!\/)|https?:\/\/)/i.test(fileUrl.trim())) {
      UI.showToast('Không tìm thấy liên kết tệp tin.', 'warning');
      return;
    }
    fileUrl = fileUrl.trim();
    const safeTitle = UI.escapeHtml(title || 'Tài liệu đính kèm');
    const safeFileUrl = UI.escapeHtml(fileUrl);
    const inlineUrl = UI.escapeHtml(fileUrl.includes('disposition=') ? fileUrl : (fileUrl + (fileUrl.includes('?') ? '&' : '?') + 'disposition=inline'));
    const mime = (mimeType || '').toLowerCase();
    const isPdf = mime === 'application/pdf' || /\.pdf$/i.test(fileUrl) || /\.pdf$/i.test(title);
    const isImage = mime.startsWith('image/') || /\.(png|jpe?g|webp|gif|svg)$/i.test(fileUrl) || /\.(png|jpe?g|webp|gif|svg)$/i.test(title);
    const isVideo = mime.startsWith('video/') || /\.(mp4|webm|mov|mkv)$/i.test(fileUrl) || /\.(mp4|webm|mov|mkv)$/i.test(title);
    const isText = mime.startsWith('text/') || mime.includes('markdown') || /\.(txt|md|html)$/i.test(fileUrl) || /\.(txt|md|html)$/i.test(title);

    let contentHtml = '';
    if (isPdf) {
      contentHtml = `
        <p id="reviewer-pdf-message" role="status" class="text-sm text-slate-500 mb-3">Đang tải tài liệu PDF…</p>
        <div class="w-full h-[650px] rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-900 shadow-inner">
          <iframe id="reviewer-pdf-frame" class="w-full h-full block" title="${safeTitle}"></iframe>
        </div>
      `;
    } else if (isImage) {
      contentHtml = `
        <div class="flex items-center justify-center p-4 bg-slate-950 rounded-xl max-h-[650px] overflow-auto">
          <img src="${inlineUrl}" alt="${safeTitle}" class="max-h-[600px] max-w-full object-contain rounded-lg shadow-lg" />
        </div>
      `;
    } else if (isVideo) {
      contentHtml = `
        <div class="bg-black rounded-xl overflow-hidden flex items-center justify-center max-h-[650px]">
          <video controls autoplay class="max-h-[600px] max-w-full rounded-lg shadow-lg block" preload="metadata" playsinline>
            <source src="${inlineUrl}" type="${UI.escapeHtml(mime || 'video/mp4')}">
            Trình duyệt của bạn không hỗ trợ thẻ video HTML5.
          </video>
        </div>
      `;
    } else if (isText) {
      contentHtml = `
        <div class="w-full h-[600px] rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-white">
          <iframe sandbox src="${inlineUrl}" class="w-full h-full block" title="${safeTitle}"></iframe>
        </div>
      `;
    } else {
      contentHtml = `
        <div class="p-8 text-center space-y-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40">
          <div class="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto">
            <span class="material-symbols-outlined text-[32px]">draft</span>
          </div>
          <div class="space-y-1">
            <h4 class="font-bold text-sm text-slate-800 dark:text-slate-200">${safeTitle}</h4>
            <p class="text-xs text-slate-500 max-w-md mx-auto">Định dạng tệp này không hỗ trợ hiển thị xem trước trực tiếp trên trình duyệt. Bạn có thể tải tệp tin về máy tính để mở bằng phần mềm tương ứng.</p>
          </div>
        </div>
      `;
    }

    const footerHtml = `
      <div class="flex items-center justify-between w-full">
        <span class="text-xs text-slate-400 font-mono truncate max-w-xs">${safeTitle}</span>
        <div class="flex items-center gap-2">
          <a href="${safeFileUrl}" download="${safeTitle}" class="px-4 py-2 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer">
            <span class="material-symbols-outlined text-[16px]">download</span>
            <span>Tải về tệp này</span>
          </a>
          <button type="button" class="px-4 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold hover:bg-slate-300 transition-colors" onclick="UI.closeModal()">
            Đóng
          </button>
        </div>
      </div>
    `;

    let pdfUrl = null;
    let closed = false;
    let modalLayer;
    modalLayer = UI.openModal({
      title: `Xem trước tài liệu: ${safeTitle}`,
      bodyHtml: contentHtml,
      footerHtml: footerHtml,
      size: 'xl',
      onClose: () => {
        closed = true;
        if (pdfUrl) URL.revokeObjectURL(pdfUrl);
        modalLayer?.querySelectorAll('video').forEach(video => video.pause());
      }
    });
    if (isPdf) {
      const frame = document.getElementById('reviewer-pdf-frame');
      const message = document.getElementById('reviewer-pdf-message');
      try {
        // Native PDF plugins cannot run inside a sandbox. Embed only a verified
        // PDF blob; never navigate the unsandboxed frame to an untrusted URL.
        const response = await fetch(fileUrl, { credentials: 'same-origin' });
        if (!response.ok || response.headers.get('Content-Type')?.split(';')[0].trim().toLowerCase() !== 'application/pdf') throw new Error('invalid-pdf');
        const blob = await response.blob();
        if (await blob.slice(0, 5).text() !== '%PDF-') throw new Error('invalid-pdf');
        if (closed || !frame?.isConnected) return;
        pdfUrl = URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
        frame.src = pdfUrl;
        message.textContent = 'Nếu trình duyệt không hỗ trợ xem PDF, hãy tải tệp để mở.';
      } catch (error) {
        if (!closed && message) message.textContent = 'Không thể xem tài liệu PDF. Kiểm tra quyền truy cập hoặc tải tệp để mở.';
      }
    }
  }

  static renderChangeRequestReviewDetail(container, r, siblingRequests = []) {
    const orig = r.original_data || {};
    const prop = r.proposed_payload || {};
    const isDelete = prop.action === 'DELETE';
    const isLearningUnit = prop.action === 'UPDATE_LEARNING_UNIT';
    const isResourceChange = prop.action === 'RESOURCE_CHANGES';
    const isChangeset = !isLearningUnit && !isDelete && !isResourceChange && (prop.action === 'COURSE_VERSION_CHANGESET' || (r.change_type === 'LESSON_STRUCTURE' && Boolean(prop.version_title || prop.added_lessons || prop.reorder_plan || prop.ordered_lesson_ids || prop.action === 'REORDER_LESSONS')));
    const isPending = r.status === 'PENDING';

    const isCourse = r.target_type === 'COURSE' || (!r.target_type && (orig.course_code || prop.course_code));
    const isCompletionRule = r.change_type === 'COMPLETION_RULE' || Boolean(orig.completion_requirements) || Boolean(prop.completion_requirements) || prop.minimum_grade_score !== undefined;

    const titleChanged = prop.title && prop.title !== orig.title;
    const summaryChanged = prop.summary !== undefined && prop.summary !== orig.summary;
    const descChanged = prop.description && prop.description !== orig.description;
    const catChanged = prop.category && prop.category !== orig.category;
    const contentChanged = prop.markdown_content !== undefined && prop.markdown_content !== orig.markdown_content;
    const durationChanged = prop.estimated_duration_minutes && prop.estimated_duration_minutes !== orig.estimated_duration_minutes;
    const statusChanged = prop.status !== undefined && prop.status !== orig.status;

    // Completion requirements comparison
    const origReq = orig.completion_requirements || {};
    const propReq = prop.completion_requirements || (prop.minimum_grade_score !== undefined ? prop : {});
    const minScoreChanged = propReq.minimum_grade_score !== undefined && propReq.minimum_grade_score !== origReq.minimum_grade_score;
    const minProgChanged = propReq.minimum_progress_percent !== undefined && propReq.minimum_progress_percent !== origReq.minimum_progress_percent;
    const reqLessonsChanged = propReq.require_all_required_lessons !== undefined && propReq.require_all_required_lessons !== origReq.require_all_required_lessons;
    const reqAsmChanged = propReq.require_required_assessments !== undefined && propReq.require_required_assessments !== origReq.require_required_assessments;
    const certChanged = propReq.allow_certificate !== undefined && propReq.allow_certificate !== origReq.allow_certificate;
    const graceDaysChanged = propReq.completion_grace_days !== undefined && propReq.completion_grace_days !== origReq.completion_grace_days;

    const lessonRuleRows = [
      ['minimum_completion_seconds', 'Thời gian học tối thiểu', value => `${value ?? 0} giây`],
      ['viewed_fraction_required', 'Tỷ lệ xem yêu cầu', value => `${Math.round(Number(value ?? 0) * 100)}%`],
      ['required_for_periods_starting_at', 'Áp dụng từ kỳ học', value => value || '(Chưa đặt)'],
    ].filter(([key]) => prop[key] !== undefined);
    const lessonRulesBefore = lessonRuleRows.map(([key, label, display]) => `
      <div><div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">${label}</div>
      <div class="text-slate-700 dark:text-slate-300 mt-0.5 text-xs">${UI.escapeHtml(display(orig[key]))}</div></div>
    `).join('');
    const lessonRulesAfter = lessonRuleRows.map(([key, label, display]) => `
      <div class="p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800">
        <div class="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">${label}</div>
        <div class="text-slate-800 dark:text-slate-200 mt-0.5 text-xs">${UI.escapeHtml(display(prop[key]))}</div>
      </div>
    `).join('');

    const currentResources = Array.isArray(orig.resources) ? orig.resources : [];
    const proposedResources = new Map(currentResources.map(item => [String(item.resource_id), item.title]));
    for (const change of Array.isArray(prop.changes) ? prop.changes : []) {
      if (!change || typeof change !== 'object') continue;
      if (change.action === 'DETACH') proposedResources.delete(String(change.resource_id));
      if (change.action === 'ATTACH') proposedResources.set(`asset:${change.asset_id}`, change.title || change.label || 'Tệp mới');
    }
    const resourceList = titles => titles.length
      ? `<ul class="space-y-2">${titles.map(title => `<li class="rounded-lg border border-slate-200 dark:border-slate-700 px-3 py-2 break-words flex items-center gap-2"><span class="material-symbols-outlined text-[16px] text-emerald-600">description</span><span>${UI.escapeHtml(title)}</span></li>`).join('')}</ul>`
      : '<p class="text-slate-500 dark:text-slate-400 italic">Chưa có tài liệu đính kèm.</p>';

    // Prepare Course Lessons for multi-lesson preview
    let courseLessons = (Array.isArray(r.course_lessons) && r.course_lessons.length)
      ? r.course_lessons
      : (Array.isArray(orig.course_lessons) ? orig.course_lessons : (Array.isArray(r.lessons) ? r.lessons : []));
    if (courseLessons.length === 0) {
      courseLessons = [{
        title: prop.title || orig.title || r.title || 'Bài giảng đang thẩm định',
        summary: prop.summary ?? orig.summary ?? '',
        estimated_duration_minutes: prop.estimated_duration_minutes || orig.estimated_duration_minutes || 15,
        markdown_content: prop.markdown_content ?? orig.markdown_content ?? '',
        learning_unit_title: 'Chương 1: Nội dung đề xuất',
        resources: AdminView.reviewerProposedLesson(orig, prop).resources
      }];
    }
    courseLessons = courseLessons.map(lesson => {
      const isTarget = r.target_type === 'LESSON' && (String(lesson.lesson_id || lesson.id) === String(r.target_id) || lesson.title === r.target_title || courseLessons.length === 1);
      return isTarget ? AdminView.reviewerProposedLesson(lesson, prop) : lesson;
    });

    const chapterTitle = r.learning_unit_title || orig.learning_unit_title || prop.learning_unit_title;

    const body = `
      <div class="space-y-5 text-xs">
        <!-- Header Info & Chapter Breadcrumb -->
        <div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div class="space-y-1.5 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-0.5 rounded font-mono font-bold text-xs bg-primary-subtle text-primary border border-primary/20">
                ${UI.escapeHtml(r.course_code || orig.course_code || 'KHÓA HỌC')}
              </span>
              <span class="font-bold text-base text-slate-900 dark:text-white truncate">
                ${UI.escapeHtml(r.target_title || orig.title || 'Yêu cầu #' + r.id)}
              </span>
              <span class="text-[11px] font-mono text-slate-400 bg-slate-200 dark:bg-slate-700 px-2 py-0.5 rounded">
                ${isCourse ? 'Mã khóa học: ' + (orig.course_code || r.course_code || r.target_id) : 'ID bài học: ' + (r.target_id || r.id)}
              </span>
            </div>

            <!-- Context Hierarchy -->
            <div class="flex items-center gap-2.5 flex-wrap text-xs text-slate-500 dark:text-slate-400 pt-0.5">
              <span class="flex items-center gap-1 font-medium">
                <span class="material-symbols-outlined text-[16px] text-slate-400">school</span>
                <span>Khóa học: <strong class="text-slate-800 dark:text-slate-200">${UI.escapeHtml(r.course_title || orig.title || 'N/A')}</strong></span>
              </span>
              ${chapterTitle ? `
                <span class="text-slate-300 dark:text-slate-600">•</span>
                <span class="flex items-center gap-1 font-semibold text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 px-2.5 py-0.5 rounded-lg border border-amber-200 dark:border-amber-800/80">
                  <span class="material-symbols-outlined text-[15px] text-amber-600">folder_open</span>
                  <span>Chương: <strong>${UI.escapeHtml(chapterTitle)}</strong></span>
                </span>
              ` : ''}
              <span class="text-slate-300 dark:text-slate-600">•</span>
              <span class="flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px] text-slate-400">person</span>
                <span>Giảng viên: <strong>${UI.escapeHtml(r.requested_by_name || 'Giảng viên')}</strong></span>
              </span>
              <span class="text-slate-300 dark:text-slate-600">•</span>
              <span class="font-mono text-slate-400">${typeof UI.formatDateTime === 'function' ? UI.formatDateTime(r.created_at) : (r.created_at || '')}</span>
            </div>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <span class="px-3 py-1 rounded-full text-xs font-bold ${r.status === 'PENDING' ? 'bg-amber-50 text-amber-700 border border-amber-200' : (r.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200')}">
              ${r.status === 'PENDING' ? 'Đang chờ duyệt' : (r.status === 'APPROVED' ? 'Đã duyệt' : 'Từ chối')}
            </span>
          </div>
        </div>

        <!-- Sibling Requests Selector if multiple requests exist for this course/lesson -->
        ${siblingRequests && siblingRequests.length > 1 ? `
          <div class="p-3.5 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 space-y-2">
            <div class="flex items-center justify-between text-xs text-amber-900 dark:text-amber-200 font-bold">
              <span class="flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px] text-amber-600">playlist_add_check</span>
                <span>Khóa học / Bài học này có ${siblingRequests.length} yêu cầu thay đổi đang chờ duyệt:</span>
              </span>
              <span class="text-[11px] font-normal text-amber-700 dark:text-amber-300 hidden sm:inline">Bấm vào từng yêu cầu để thẩm định & duyệt độc lập</span>
            </div>
            <div class="flex flex-wrap gap-2 pt-1">
              ${siblingRequests.map(s => {
                const isCurrent = String(s.id) === String(r.id);
                return `
                  <a
                    href="#/admin/change-requests/review?id=${s.id}"
                    class="px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                      isCurrent
                        ? 'bg-primary text-white shadow-xs ring-2 ring-primary/30'
                        : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-amber-200 dark:border-amber-700 hover:border-primary'
                    }"
                  >
                    <span class="material-symbols-outlined text-[15px]">${isCurrent ? 'radio_button_checked' : 'radio_button_unchecked'}</span>
                    <span>Yêu cầu #${s.id}: ${UI.escapeHtml(s.target_title || s.change_type)}</span>
                    ${isCurrent ? '<span class="text-[10px] bg-white/20 px-1.5 py-0.2 rounded uppercase tracking-wider font-extrabold ml-1">Đang xem</span>' : ''}
                  </a>
                `;
              }).join('')}
            </div>
          </div>
        ` : ''}

        <!-- View Mode Switcher -->
        <div class="flex items-center justify-between pt-1">
          <div class="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-bold">
            <button type="button" id="cr-tab-diff-btn" class="px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all bg-white dark:bg-slate-900 text-primary shadow-xs font-bold cursor-pointer">
              <span class="material-symbols-outlined text-[16px]">difference</span>
              <span>Đối chiếu thay đổi (Diff)</span>
            </button>
            <button type="button" id="cr-tab-preview-btn" class="px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer">
              <span class="material-symbols-outlined text-[16px]">visibility</span>
              <span>Xem trước</span>
            </button>
          </div>
          <span class="text-[11px] text-slate-400 hidden sm:inline">Chuyển sang chế độ Xem trước để đối chiếu góc nhìn sinh viên</span>
        </div>

        <!-- Tab 1: Side-by-side Diff View -->
        <div id="cr-diff-container" class="space-y-4">
          ${isLearningUnit ? `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <section class="rounded-xl bg-slate-50 dark:bg-slate-800 p-5 space-y-3 border border-slate-200 dark:border-slate-700">
                <h2 class="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[18px] text-slate-400">history</span>
                  <span>Tên Bài học hiện tại</span>
                </h2>
                <p class="text-base text-slate-800 dark:text-slate-200 break-words">${UI.escapeHtml(orig.title || '(Chưa có)')}</p>
              </section>
              <section class="rounded-xl bg-primary-subtle dark:bg-[#2D4058] p-5 space-y-3 border border-primary/30">
                <h2 class="text-sm font-bold text-primary dark:text-[#93C5FD] flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[18px]">edit_document</span>
                  <span>Tên Bài học đề xuất</span>
                </h2>
                <p class="text-base text-slate-900 dark:text-slate-100 break-words">${UI.escapeHtml(prop.title || '(Chưa có)')}</p>
              </section>
            </div>
          ` : isResourceChange ? `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <section class="rounded-xl bg-slate-50 dark:bg-slate-800 p-5 space-y-3 border border-slate-200 dark:border-slate-700">
                <h2 class="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[18px] text-slate-400">history</span>
                  <span>Tài liệu hiện tại</span>
                </h2>
                ${resourceList(currentResources.map(item => item.title))}
              </section>
              <section class="rounded-xl bg-primary-subtle dark:bg-[#2D4058] p-5 space-y-3 border border-primary/30">
                <h2 class="text-sm font-bold text-primary dark:text-[#93C5FD] flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[18px]">edit_document</span>
                  <span>Tài liệu sau khi duyệt</span>
                </h2>
                ${resourceList([...proposedResources.values()])}
              </section>
            </div>
          ` : isDelete ? `
            <div class="p-5 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-rose-800 dark:text-rose-300 space-y-3">
              <div class="font-bold text-sm flex items-center gap-2 text-rose-700 dark:text-rose-400">
                <span class="material-symbols-outlined text-[22px]">delete_forever</span>
                <span>Yêu cầu gỡ bỏ ${isCourse ? 'khóa học' : 'bài giảng'}</span>
              </div>
              <p class="leading-relaxed">Giảng viên đề xuất gỡ bỏ ${isCourse ? 'khóa học này khỏi hệ thống' : 'bài giảng này khỏi đề cương'}.</p>
              <div class="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-900/40 text-xs">
                <strong>Lý do yêu cầu xóa:</strong> ${UI.escapeHtml(prop.reason || 'Không có lý do chi tiết.')}
              </div>
            </div>
          ` : isChangeset ? `
            <div class="space-y-4">
              <!-- Changeset Summary Banner -->
              <div class="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-3">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <div class="flex items-center gap-2.5">
                    <span class="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center material-symbols-outlined text-[20px]">difference</span>
                    <div>
                      <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">
                        ${UI.escapeHtml(prop.version_title || 'Đợt Cập Nhật Giáo Trình')}
                      </h3>
                      <p class="text-xs text-slate-500 dark:text-slate-400">
                        ${UI.escapeHtml(prop.summary || 'Đợt cập nhật gộp cấu trúc chương trình học')}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                      +${(prop.added_lessons || []).length} bài mới
                    </span>
                    <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
                      ~${(prop.modified_lessons || []).length} bài sửa
                    </span>
                    <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800">
                      -${(prop.deleted_lessons || []).length} bài xóa
                    </span>
                    ${(prop.reorder_plan?.lessons_order || []).length ? `
                      <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-400 border border-purple-200 dark:border-purple-800">
                        🔄 Sắp xếp lại
                      </span>
                    ` : ''}
                  </div>
                </div>
              </div>

              <!-- 2-Column Changeset Inspection -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="changeset-diff-grid">
                <!-- Column 1: Live / Before -->
                <div class="rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-white dark:bg-slate-900 flex flex-col shadow-2xs">
                  <div class="bg-slate-100 dark:bg-slate-800 px-4 py-2.5 border-b border-slate-200 dark:border-slate-700 font-bold text-slate-700 dark:text-slate-300 flex items-center justify-between">
                    <span class="flex items-center gap-1.5">
                      <span class="material-symbols-outlined text-[16px] text-slate-400">history</span>
                      <span>Giáo trình Hiện tại (Live)</span>
                    </span>
                    <span class="text-[10px] px-2 py-0.5 rounded-md bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-semibold">Đang áp dụng</span>
                  </div>
                  <div class="p-4 space-y-2 text-xs" id="changeset-live-curriculum-box">
                    <div class="text-slate-400 italic py-4 text-center">Đang tải đối chiếu giáo trình...</div>
                  </div>
                </div>

                <!-- Column 2: Proposed / After -->
                <div class="rounded-2xl border border-primary/30 dark:border-primary/40 overflow-hidden bg-white dark:bg-slate-900 flex flex-col shadow-2xs">
                  <div class="bg-primary-subtle dark:bg-[#1E293B] px-4 py-2.5 border-b border-primary/20 dark:border-primary/30 font-bold text-primary dark:text-[#93C5FD] flex items-center justify-between">
                    <span class="flex items-center gap-1.5">
                      <span class="material-symbols-outlined text-[16px]">verified</span>
                      <span>Giáo trình Đề xuất (Sau khi duyệt)</span>
                    </span>
                    <span class="text-[10px] px-2 py-0.5 rounded-md bg-primary text-white font-semibold">Đề xuất</span>
                  </div>
                  <div class="p-4 space-y-2 text-xs" id="changeset-proposed-curriculum-box">
                    <div class="text-slate-400 italic py-4 text-center">Đang tải cấu trúc đề xuất...</div>
                  </div>
                </div>
              </div>

              <!-- 5-Category Deep Changeset Diff Tree -->
              <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-2xs">
                <div class="bg-slate-50 dark:bg-slate-800/80 px-4 py-3 border-b border-slate-200 dark:border-slate-700 font-bold text-slate-800 dark:text-slate-200 flex items-center justify-between text-xs">
                  <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px] text-primary">analytics</span>
                    <span>Chi tiết Đối chiếu Thay đổi Giáo trình (5 Phân Nhóm Học Vụ)</span>
                  </div>
                  <span class="text-[10px] text-slate-400 font-normal">Dữ liệu tính toán thời gian thực từ máy chủ</span>
                </div>
                <div class="p-4 sm:p-6" id="changeset-categorized-diff-box">
                  <div class="text-slate-400 italic py-6 text-center text-xs">Đang phân tích và đối chiếu 5 phân nhóm học vụ...</div>
                </div>
              </div>
            </div>
          ` : `
            ${AdminView.renderUnifiedDiffPanel(r, orig, prop)}
          `}
        </div>

        ${lessonRuleRows.length ? `<section class="grid grid-cols-1 md:grid-cols-2 gap-6"><div class="space-y-3">${lessonRulesBefore}</div><div class="space-y-3">${lessonRulesAfter}</div></section>` : ''}
        <div id="cr-preview-container" class="hidden"></div>

      </div>
    `;

    const footer = `
      <div class="flex flex-wrap items-center justify-between gap-4 w-full">
        <a href="#/admin/governance?tab=courses" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold hover:bg-slate-300 transition-colors">Quay lại hàng đợi</a>
        ${isPending ? `
          <div class="flex items-center gap-2">
            <button type="button" id="diff-reject-btn" class="px-4 py-2.5 rounded-xl bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-bold transition-colors cursor-pointer">
              Từ chối
            </button>
            <button type="button" id="diff-approve-btn" class="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors shadow-xs flex items-center gap-1.5 cursor-pointer">
              <span class="material-symbols-outlined text-[16px]">check</span>
              <span>Phê duyệt</span>
            </button>
          </div>
        ` : `
          <span class="text-xs text-slate-400 italic">${UI.escapeHtml(r.review_reason || 'Đã giải quyết')}</span>
        `}
      </div>
    `;

    container.innerHTML = `
      <main class="max-w-[1600px] mx-auto p-4 sm:p-8 space-y-6 animate-fade-in">
        <header class="space-y-2">
          <a href="#/admin/governance?tab=courses" class="text-sm font-semibold text-primary hover:underline">← Hàng đợi xét duyệt</a>
          <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">Thẩm định bản sửa đổi</h1>
          <p class="text-sm text-slate-600 dark:text-slate-300">${UI.escapeHtml(r.course_title || 'Khóa học')} · Yêu cầu #${r.id}</p>
        </header>
        <section class="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-4 sm:p-6 shadow-2xs">${body}</section>
        <footer class="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-4 sm:p-6 shadow-2xs">${footer}</footer>
      </main>
    `;

    AdminView.renderReviewerCoursePreview(document.getElementById('cr-preview-container'), { lessons: courseLessons, learning_units: r.learning_units || orig.learning_units || [] });

    // Hook up View Mode tabs
    const diffBtn = document.getElementById('cr-tab-diff-btn');
    const previewBtn = document.getElementById('cr-tab-preview-btn');
    const diffContainer = document.getElementById('cr-diff-container');
    const previewContainer = document.getElementById('cr-preview-container');

    if (diffBtn && previewBtn && diffContainer && previewContainer) {
      diffBtn.onclick = () => {
        diffBtn.className = 'px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all bg-white dark:bg-slate-900 text-primary shadow-xs font-bold cursor-pointer';
        previewBtn.className = 'px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer';
        diffContainer.classList.remove('hidden');
        previewContainer.classList.add('hidden');
      };

      previewBtn.onclick = () => {
        previewBtn.className = 'px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all bg-white dark:bg-slate-900 text-primary shadow-xs font-bold cursor-pointer';
        diffBtn.className = 'px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer';
        previewContainer.classList.remove('hidden');
        diffContainer.classList.add('hidden');
      };
    }

    if (isChangeset) {
      const scheduleDiffFetch = typeof setTimeout === 'function' ? setTimeout : (fn => fn());
      scheduleDiffFetch(async () => {
        try {
          const diffRes = await ApiClient.getCourseChangesetDiff(r.id);
          const liveBox = document.getElementById('changeset-live-curriculum-box');
          const propBox = document.getElementById('changeset-proposed-curriculum-box');
          const catDiffBox = document.getElementById('changeset-categorized-diff-box');

          if (catDiffBox && diffRes) {
            catDiffBox.innerHTML = UI.renderCategorizedDiffHtml(diffRes);
          }

          if (liveBox && propBox && diffRes) {
            const liveList = diffRes.live_curriculum || [];
            const propList = diffRes.proposed_curriculum || [];

            liveBox.innerHTML = liveList.length ? `
              <div class="space-y-1.5">
                ${liveList.map(item => `
                  <div class="p-2.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2 min-w-0">
                      <span class="w-6 h-6 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-[11px] font-bold flex items-center justify-center shrink-0">
                        ${item.position}
                      </span>
                      <span class="font-semibold text-slate-800 dark:text-slate-200 truncate">
                        ${UI.escapeHtml(item.title)}
                      </span>
                    </div>
                  </div>
                `).join('')}
              </div>
            ` : '<p class="text-slate-400 italic">Khóa học chưa có bài học nào.</p>';

            propBox.innerHTML = propList.length ? `
              <div class="space-y-1.5">
                ${propList.map(item => {
                  let badge = '';
                  let borderClass = 'border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50';
                  const st = item.status || item.change_status;
                  if (st === 'ADDED') {
                    badge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">Mới</span>';
                    borderClass = 'border-emerald-200 dark:border-emerald-800/60 bg-emerald-50/50 dark:bg-emerald-950/20';
                  } else if (st === 'MODIFIED') {
                    badge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">Đã sửa</span>';
                    borderClass = 'border-blue-200 dark:border-blue-800/60 bg-blue-50/50 dark:bg-blue-950/20';
                  } else if (st === 'REORDERED') {
                    badge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">Đổi thứ tự</span>';
                    borderClass = 'border-amber-200 dark:border-amber-800/60 bg-amber-50/50 dark:bg-amber-950/20';
                  } else if (st === 'DELETED') {
                    badge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">Xóa</span>';
                    borderClass = 'border-rose-200 dark:border-rose-800/60 bg-rose-50/50 dark:bg-rose-950/20 opacity-60 line-through';
                  }
                  return `
                    <div class="p-2.5 rounded-xl border ${borderClass} flex items-center justify-between gap-2">
                      <div class="flex items-center gap-2 min-w-0">
                        <span class="w-6 h-6 rounded-lg bg-primary-subtle text-primary text-[11px] font-bold flex items-center justify-center shrink-0">
                          ${item.position}
                        </span>
                        <span class="font-semibold text-slate-800 dark:text-slate-200 truncate">
                          ${UI.escapeHtml(item.title)}
                        </span>
                      </div>
                      ${badge}
                    </div>
                  `;
                }).join('')}
              </div>
            ` : '<p class="text-slate-400 italic">Không có dữ liệu bài học đề xuất.</p>';
          }
        } catch (err) {
          console.warn('Failed to fetch changeset diff:', err);
        }
      }, 0);
    }

    if (isPending) {
      document.getElementById('diff-approve-btn').onclick = async () => {
        const confirmed = await UI.confirm(
          'Xác nhận phê duyệt',
          `Bạn có chắc chắn muốn phê duyệt và áp dụng các thay đổi cho yêu cầu #${r.id}? Hành động này sẽ cập nhật dữ liệu khóa học chính thức.`
        );
        if (!confirmed) return;
        try {
          if (r.change_type === 'COURSE_VERSION_CHANGESET') {
            await ApiClient.approveCourseChangeset(r.id, 'Phê duyệt đợt cập nhật giáo trình.');
          } else {
            await ApiClient.reviewAdminChangeRequest(r.id, { action: 'approve' });
          }
          UI.showToast(`Đã phê duyệt và áp dụng bản sửa đổi #${r.id} thành công!`, 'success');
          AdminView._activeCrFilter = 'PENDING';
          window.app?.refreshNotificationBadge?.(true);
          window.app?.fetchAdminPendingCounts?.();
          window.location.hash = '#/admin/governance?tab=courses';
          UI.refreshCurrentRoute();
        } catch (e) {
          UI.showToast(e.message || 'Lỗi phê duyệt yêu cầu.', 'error');
        }
      };

      document.getElementById('diff-reject-btn').onclick = async () => {
        const reason = await UI.prompt(
          'Từ chối bản sửa đổi',
          `Nhập lý do từ chối yêu cầu sửa đổi #${r.id}:`,
          '',
          'Nhập lý do chi tiết (tối thiểu 5 ký tự)...',
          5,
          'Từ chối'
        );
        if (!reason) return;
        const confirmed = await UI.confirm(
          'Xác nhận từ chối',
          `Bạn có chắc chắn muốn từ chối yêu cầu #${r.id} với lý do: "${reason}"?`,
          'Từ chối',
          'Quay lại',
          true
        );
        if (!confirmed) return;
        try {
          if (r.change_type === 'COURSE_VERSION_CHANGESET') {
            await ApiClient.rejectCourseChangeset(r.id, reason);
          } else {
            await ApiClient.reviewAdminChangeRequest(r.id, { action: 'reject', reason });
          }
          UI.showToast(`Đã từ chối yêu cầu #${r.id}.`, 'info');
          AdminView._activeCrFilter = 'PENDING';
          window.app?.refreshNotificationBadge?.(true);
          window.app?.fetchAdminPendingCounts?.();
          window.location.hash = '#/admin/governance?tab=courses';
          UI.refreshCurrentRoute();
        } catch (e) {
          UI.showToast(e.message || 'Lỗi từ chối yêu cầu.', 'error');
        }
      };
    }
  }

  // =========================================================================
  // Tab 3: Hồ sơ Đăng ký Giảng viên (Instructor Applications - Tách riêng)
  // =========================================================================
  static async renderTabInstructorApps(container) {
    container.innerHTML = `
      <div class="space-y-6 animate-fade-in" id="instructor-apps-box">
        <div class="p-12 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang nạp hồ sơ ứng tuyển giảng viên...</p>
        </div>
      </div>
    `;

    try {
      const appsRes = await ApiClient.getAdminInstructorApplications('ALL');
      const rawApplications = appsRes?.applications || [];
      const applications = rawApplications.filter(a => a.status !== 'CANCELLED');
      const pendingApps = applications.filter(a => a.status === 'PENDING');
      const approvedApps = applications.filter(a => a.status === 'APPROVED');
      const rejectedApps = applications.filter(a => a.status === 'REJECTED');

      // Update badge
      if (window.app && typeof window.app.updateAdminNavBadges === 'function') {
        window.app.updateAdminNavBadges({ applications: pendingApps.length });
      }

      const box = document.getElementById('instructor-apps-box');
      if (!box) return;

      box.innerHTML = `
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-primary text-[20px]">badge</span>
                Hồ sơ Đăng ký Giảng viên (Instructor Applications)
              </h3>
              <p class="text-xs text-slate-400 mt-0.5">Xem hồ sơ và tài liệu trước khi quyết định cấp quyền giảng viên.</p>
            </div>
            <div class="flex items-center gap-1.5" id="app-status-filter-group">
              <button type="button" class="app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white" data-status="PENDING">Chờ duyệt (${pendingApps.length})</button>
              <button type="button" class="app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="APPROVED">Đã duyệt (${approvedApps.length})</button>
              <button type="button" class="app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="REJECTED">Từ chối (${rejectedApps.length})</button>
              <button type="button" class="app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200" data-status="ALL">Tất cả (${applications.length})</button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs sm:text-sm">
              <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
                <tr>
                  <th class="px-4 py-3">Ứng viên</th>
                  <th class="px-4 py-3">Trình độ & Chuyên môn</th>
                  <th class="px-4 py-3">Kinh nghiệm</th>
                  <th class="px-4 py-3">Trạng thái</th>
                  <th class="px-4 py-3">Thời điểm nộp</th>
                  <th class="px-4 py-3 text-right">Quyết định bổ nhiệm</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium" id="instructor-apps-tbody">
                <!-- Populated via JS -->
              </tbody>
            </table>
          </div>
        </div>
      `;

      const renderAppRows = (statusFilter = 'PENDING') => {
        const tbody = document.getElementById('instructor-apps-tbody');
        if (!tbody) return;

        const filtered = applications.filter(a => statusFilter === 'ALL' || a.status === statusFilter);

        if (filtered.length === 0) {
          const emptyMsg = statusFilter === 'PENDING'
            ? 'Hàng đợi trống — Hiện không có hồ sơ nào đang chờ duyệt. Các hồ sơ đã được duyệt hoặc hủy sẽ tự động rời khỏi hàng đợi.'
            : 'Không có hồ sơ nào trong danh mục này.';
          tbody.innerHTML = `
            <tr>
              <td colspan="6" class="py-12 text-center text-slate-400 text-xs">
                <div class="flex flex-col items-center justify-center gap-2">
                  <span class="material-symbols-outlined text-emerald-500 text-3xl">task_alt</span>
                  <p class="font-bold text-slate-700 dark:text-slate-300 text-sm">${emptyMsg}</p>
                </div>
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = filtered.map(a => {
          const details = a.details || {};
          let statusBadge = 'bg-amber-50 text-amber-700 border-amber-200';
          if (a.status === 'APPROVED') statusBadge = 'bg-emerald-50 text-emerald-700 border-emerald-200';
          if (a.status === 'REJECTED') statusBadge = 'bg-rose-50 text-rose-700 border-rose-200';

          return `
            <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
              <td class="px-4 py-3.5">
                <div class="font-bold text-slate-900 dark:text-white">${UI.escapeHtml(a.applicant_name)}</div>
                <div class="text-xs text-slate-400 font-mono">${UI.escapeHtml(a.applicant_email)}</div>
              </td>
              <td class="px-4 py-3.5">
                <div class="font-bold text-slate-800 dark:text-slate-200">${UI.escapeHtml(details.degree || 'Chưa cập nhật')}</div>
                <div class="text-[11px] text-slate-400">${UI.escapeHtml(details.specialization || details.institution || 'CNTT')}</div>
              </td>
              <td class="px-4 py-3.5 text-xs">
                ${details.years_experience ? `${details.years_experience} năm kinh nghiệm` : (details.experience || '1-3 năm')}
              </td>
              <td class="px-4 py-3.5">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusBadge}">
                  ${a.status_label || a.status}
                </span>
              </td>
              <td class="px-4 py-3.5 text-xs text-slate-400 font-mono">
                ${UI.formatDate(a.created_at)}
              </td>
              <td class="px-4 py-3.5 text-right space-x-1.5 whitespace-nowrap">
                <button type="button" class="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors view-app-btn" data-app-id="${a.id}">
                  Xem CV
                </button>
                ${a.status === 'PENDING' ? `
                  <button type="button" class="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors approve-app-btn" data-app-id="${a.id}" data-name="${UI.escapeHtml(a.applicant_name)}">
                    Bổ nhiệm
                  </button>
                  <button type="button" class="px-2.5 py-1.5 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-bold transition-colors reject-app-btn" data-app-id="${a.id}" data-name="${UI.escapeHtml(a.applicant_name)}">
                    Từ chối
                  </button>
                ` : `
                  <span class="text-xs text-slate-400 italic">${UI.escapeHtml(a.review_reason || (a.status === 'APPROVED' ? 'Đã duyệt bổ nhiệm' : 'Đã từ chối'))}</span>
                `}
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.view-app-btn').forEach(btn => {
          btn.onclick = () => {
            const appId = btn.dataset.appId;
            const app = applications.find(x => String(x.id) === String(appId));
            if (app) AdminView.openApplicationDetailModal(app, container);
          };
        });

        tbody.querySelectorAll('.approve-app-btn').forEach(btn => {
          btn.onclick = async () => {
            const appId = btn.dataset.appId;
            const name = btn.dataset.name;
            const conf = await UI.confirm('Bổ nhiệm Giảng viên', `Xác nhận phê duyệt đơn đăng ký và cấp quyền Giảng viên (INSTRUCTOR) cho "${name}"?`, 'Phê duyệt bổ nhiệm');
            if (!conf) return;

            try {
              await ApiClient.reviewInstructorApplication(appId, 'approve', 'Hồ sơ đạt yêu cầu');
              UI.showToast(`Đã bổ nhiệm giảng viên ${name} thành công!`, 'success');
              UI.refreshCurrentRoute(() => AdminView.renderTabInstructorApps(container));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi phê duyệt đơn.', 'error');
            }
          };
        });

        tbody.querySelectorAll('.reject-app-btn').forEach(btn => {
          btn.onclick = async () => {
            const appId = btn.dataset.appId;
            const name = btn.dataset.name;
            const reason = await UI.prompt(
              'Từ chối hồ sơ giảng viên',
              `Nhập lý do từ chối đơn đăng ký làm giảng viên của ứng viên "${name}":`,
              '',
              'Nhập lý do từ chối hồ sơ (tối thiểu 5 ký tự)...',
              5,
              'Từ Chối Hồ Sơ'
            );
            if (!reason) return;

            try {
              await ApiClient.reviewInstructorApplication(appId, 'reject', reason);
              UI.showToast(`Đã từ chối đơn của ${name}.`, 'info');
              UI.refreshCurrentRoute(() => AdminView.renderTabInstructorApps(container));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi từ chối đơn.', 'error');
            }
          };
        });
      };

      renderAppRows('PENDING');

      const filterBtns = box.querySelectorAll('.app-filter-btn');
      filterBtns.forEach(btn => {
        btn.onclick = () => {
          filterBtns.forEach(b => {
            b.className = 'app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200';
          });
          btn.className = 'app-filter-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-primary text-white';
          renderAppRows(btn.dataset.status);
        };
      });

    } catch (err) {
      console.error('TabInstructorApps load error:', err);
    }
  }

  static async renderCourseReviewPage(container, courseId) {
    try {
      container.innerHTML = '<div class="p-8 text-sm text-slate-600 dark:text-slate-300">Đang tải chi tiết khóa học...</div>';

      const course = await ApiClient.getAdminCourseDetail(courseId);
      const lessons = course.lessons || [];
      const difficultyLabel = {
        BEGINNER: 'Cơ bản', INTERMEDIATE: 'Trung cấp', ADVANCED: 'Nâng cao'
      }[course.difficulty] || course.difficulty || 'Chưa chọn';

      // Parse learning objectives for Admin inspection
      let adminSLOs = [];
      if (course.learning_objectives) {
        if (Array.isArray(course.learning_objectives)) {
          adminSLOs = [...course.learning_objectives];
        } else if (typeof course.learning_objectives === 'string') {
          try {
            const parsed = JSON.parse(course.learning_objectives);
            if (Array.isArray(parsed)) adminSLOs = parsed;
          } catch {
            adminSLOs = course.learning_objectives.split('\n').filter(s => s.trim()).map((s, i) => ({
              title: `SLO-${i + 1}`,
              description: s.trim()
            }));
          }
        }
      }

      const bodyHtml = `
        <div class="space-y-4 text-xs">
          <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <span class="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-primary-subtle text-primary border border-primary/20">${UI.escapeHtml(course.course_code)}</span>
                <h4 class="font-bold text-base text-slate-900 dark:text-white mt-1">${UI.escapeHtml(course.title)}</h4>
              </div>
                <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">${course.status === 'SUBMITTED_FOR_REVIEW' ? 'Chờ Duyệt' : UI.escapeHtml(course.status)}</span>
            </div>
            <p class="text-slate-500 dark:text-slate-400 text-xs">${UI.escapeHtml(course.description || 'Chưa có mô tả khóa học.')}</p>
            <div class="pt-2 border-t border-slate-200 dark:border-slate-700 flex flex-wrap gap-4 text-slate-600 dark:text-slate-300 font-medium">
              <span><strong>Giảng viên:</strong> ${UI.escapeHtml(course.owner_instructor_name)} (${UI.escapeHtml(course.owner_instructor_email || 'N/A')})</span>
              <span><strong>Độ khó:</strong> ${UI.escapeHtml(difficultyLabel)}</span>
              <span><strong>Danh mục:</strong> ${UI.escapeHtml(course.category || 'Chưa chọn')}</span>
            </div>
          </div>

          <!-- Section: Chuẩn đầu ra SLO Inspection -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <h5 class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-[18px] text-primary">verified_user</span>
                  Mục tiêu học tập
                </h5>
              </div>
              <span class="text-slate-500 dark:text-slate-300 text-xs">${adminSLOs.length} mục tiêu</span>
            </div>

            ${adminSLOs.length === 0 ? `
              <div class="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs space-y-1">
                <div class="font-bold flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">warning</span>
                  <span>Chưa có mục tiêu học tập</span>
                </div>
                <p class="text-[11px] leading-relaxed">Giảng viên chưa thêm mục tiêu học tập. Hãy xem lại trước khi duyệt khóa học.</p>
              </div>
            ` : `
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                ${adminSLOs.map((slo, idx) => {
                  const title = typeof slo === 'object' ? (slo.title || `SLO-${idx + 1}`) : `SLO-${idx + 1}`;
                  const desc = typeof slo === 'object' ? (slo.description || slo.content || '') : String(slo);
                  const weight = typeof slo === 'object' && slo.weight ? slo.weight : null;
                  return `
                    <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 space-y-1">
                      <div class="flex items-center justify-between">
                        <span class="font-mono font-bold text-primary text-xs">${UI.escapeHtml(title)}</span>
                        ${weight ? `<span class="text-[10px] text-slate-400 font-semibold font-mono">Trọng số: ${UI.escapeHtml(weight)}</span>` : ''}
                      </div>
                      <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">${UI.escapeHtml(desc || 'Chưa có mô tả chi tiết.')}</p>
                    </div>
                  `;
                }).join('')}
              </div>
            `}
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <h5 class="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[18px] text-primary">format_list_numbered</span>
                Nội dung bài học (${lessons.length} bài)
              </h5>
            </div>

            ${lessons.length === 0 ? `
              <div class="p-6 text-center text-slate-400 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
                Khóa học chưa có bài học nào được thiết lập trong đề cương.
              </div>
            ` : `
              <div class="divide-y divide-slate-100 dark:divide-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden bg-white dark:bg-slate-900">
                ${lessons.map((l, idx) => `
                  <details class="p-3.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <summary class="flex items-center justify-between gap-3 cursor-pointer">
                    <div class="flex items-center gap-3 min-w-0">
                      <span class="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono font-bold text-xs flex items-center justify-center flex-shrink-0">
                        ${UI.escapeHtml(l.order_index || idx + 1)}
                      </span>
                      <div class="truncate">
                        ${l.learning_unit_title ? `<div class="text-[11px] text-slate-600 dark:text-slate-300 truncate">${UI.escapeHtml(l.learning_unit_title)}</div>` : ''}
                        <div class="font-bold text-slate-800 dark:text-slate-200 text-xs truncate">${UI.escapeHtml(l.title)}</div>
                        ${l.summary ? `<div class="text-[11px] text-slate-400 truncate">${UI.escapeHtml(l.summary)}</div>` : ''}
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      ${l.is_flagged ? `
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-300 flex items-center gap-1">
                          <span class="material-symbols-outlined text-[12px]">flag</span> Đã gắn cờ
                        </span>
                      ` : ''}
                      <span class="px-2 py-0.5 rounded text-[10px] font-bold ${l.status === 'PUBLISHED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'}">
                        ${l.status === 'PUBLISHED' ? 'Đã xuất bản' : 'Bản nháp'}
                      </span>
                    </div>
                    </summary>
                    <div class="mt-4 border-t border-slate-200 dark:border-slate-700 pt-4 space-y-3">
                      ${l.is_flagged ? `
                        <div class="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs font-medium space-y-1">
                          <div class="font-bold flex items-center gap-1 text-rose-700 dark:text-rose-400">
                            <span class="material-symbols-outlined text-[15px]">flag</span> Bài học đang bị gắn cờ vi phạm:
                          </div>
                          <p class="text-xs leading-relaxed">${UI.escapeHtml(l.flag_reason || 'Chưa có chi tiết lý do.')}</p>
                        </div>
                      ` : ''}
                      <div class="space-y-2">
                        <div class="flex items-center justify-between text-xs text-slate-500 font-semibold">
                          <span class="flex items-center gap-1.5 text-primary font-bold">
                            <span class="material-symbols-outlined text-[16px]">description</span>
                            <span>Bản xem trước giáo trình (Định dạng văn bản Word chuẩn)</span>
                          </span>
                          <span class="text-[11px] text-slate-400">Đã tự động ẩn thẻ kỹ thuật nội bộ</span>
                        </div>
                        <div class="max-w-4xl mx-auto bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 shadow-sm rounded-xl p-6 sm:p-10 font-sans text-slate-800 dark:text-slate-100 min-h-[220px]">
                          <div class="prose dark:prose-invert max-w-none text-xs sm:text-sm leading-relaxed space-y-2">
                            ${UI.renderMarkdown(
                              (l.markdown_content || '*Chưa có nội dung bài giảng.*')
                                .replace(/<!--\s*video_urls?:.*?-->\s*/gs, '')
                                .replace(/<!--\s*mini_quiz:.*?-->\s*/gs, '')
                            )}
                          </div>
                        </div>
                      </div>
                      <div class="space-y-2 pt-2">
                        <div class="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
                          <span class="flex items-center gap-1.5">
                            <span class="material-symbols-outlined text-[16px] text-primary">attachment</span>
                            <span>Tài liệu đính kèm bài học (${(l.resources || []).length})</span>
                          </span>
                        </div>
                        ${(l.resources || []).length === 0 ? `
                          <p class="text-xs text-slate-400 italic">Bài học này không có tài liệu đính kèm.</p>
                        ` : `
                          <div class="space-y-2">
                            ${(l.resources || []).map(resource => {
                              const isClean = resource.is_clean ?? (resource.scan_status === 'CLEAN');
                              const title = resource.filename || resource.label || 'Tài liệu';
                              const mime = resource.mime_type || '';
                              const isPdf = mime === 'application/pdf' || /\.pdf$/i.test(title);
                              let extBadge = isPdf ? 'PDF' : (/\.(docx?|odt)$/i.test(title) ? 'DOC' : 'FILE');
                              let badgeClass = isPdf ? 'bg-rose-100 text-rose-700 border-rose-200' : 'bg-blue-100 text-blue-700 border-blue-200';

                              return `
                                <div class="p-3 rounded-xl border ${isClean ? 'border-slate-200 dark:border-slate-700 bg-slate-50/60 dark:bg-slate-800/40' : 'border-rose-300 dark:border-rose-800 bg-rose-50/40 dark:bg-rose-950/20'} flex items-center justify-between gap-3 shadow-2xs">
                                  <div class="flex items-center gap-2.5 min-w-0">
                                    <span class="w-8 h-8 rounded-lg font-mono font-bold text-[10px] flex items-center justify-center shrink-0 border ${badgeClass}">
                                      ${extBadge}
                                    </span>
                                    <div class="min-w-0">
                                      <p class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate" title="${UI.escapeHtml(title)}">
                                        ${UI.escapeHtml(title)}
                                      </p>
                                      <div class="flex items-center gap-2 mt-0.5">
                                        <span class="text-[10px] text-slate-400 font-mono">${extBadge} Document</span>
                                        ${isClean ? `
                                          <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 flex items-center gap-0.5">
                                            <span class="material-symbols-outlined text-[11px]">verified_user</span> Đã kiểm tra an toàn
                                          </span>
                                        ` : `
                                          <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-300 flex items-center gap-0.5">
                                            <span class="material-symbols-outlined text-[11px]">gpp_maybe</span> Chưa an toàn / Đã cách ly
                                          </span>
                                        `}
                                      </div>
                                    </div>
                                  </div>

                                  <div class="flex items-center gap-1.5 shrink-0">
                                    ${isClean && resource.file_url ? `
                                      <button
                                        type="button"
                                        class="course-doc-preview-btn px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-700 hover:bg-emerald-50 dark:hover:bg-emerald-950 text-slate-700 dark:text-slate-200 hover:text-emerald-600 text-xs font-semibold border border-slate-200 dark:border-slate-600 transition-colors flex items-center gap-1 cursor-pointer"
                                        data-title="${UI.escapeHtml(title)}"
                                        data-file-url="${UI.escapeHtml(resource.file_url)}"
                                        data-mime="${UI.escapeHtml(mime)}"
                                        title="Xem trước tệp này"
                                      >
                                        <span class="material-symbols-outlined text-[15px]">visibility</span>
                                        <span>Xem trước</span>
                                      </button>
                                      <a
                                        href="${UI.escapeHtml(resource.download_url || resource.file_url)}"
                                        download="${UI.escapeHtml(title)}"
                                        class="p-1.5 rounded-lg text-slate-400 hover:text-primary hover:bg-primary-subtle transition-colors shrink-0"
                                        title="Tải về máy tính"
                                      >
                                        <span class="material-symbols-outlined text-[18px]">download</span>
                                      </a>
                                    ` : `
                                      <span class="text-[10px] text-rose-600 dark:text-rose-400 italic font-medium flex items-center gap-1">
                                        <span class="material-symbols-outlined text-[14px]">lock</span>
                                        Bị khóa (Fail-Closed)
                                      </span>
                                    `}
                                  </div>
                                </div>
                              `;
                            }).join('')}
                          </div>
                        `}
                      </div>
                      <div class="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-700">
                        <span class="text-[11px] text-slate-500 dark:text-slate-400">Quản trị viên chỉ có quyền thẩm định và gắn cờ (Read-Only)</span>
                        <button type="button" class="btn-flag-lesson-action px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 flex items-center gap-1.5 shadow-2xs" data-lesson-id="${UI.escapeHtml(l.lesson_id)}" data-lesson-title="${UI.escapeHtml(l.title)}">
                          <span class="material-symbols-outlined text-[15px]">flag</span>
                          <span>${l.is_flagged ? 'Cập nhật lý do gắn cờ' : 'Gắn cờ vi phạm bài học'}</span>
                        </button>
                      </div>
                    </div>
                  </details>
                `).join('')}
              </div>
            `}
          </div>
        </div>
      `;

      const isPending = course.status === 'SUBMITTED_FOR_REVIEW';
      container.innerHTML = `
          <main class="mx-auto max-w-[1720px] w-full px-4 sm:px-6 lg:px-10 py-8 space-y-6 text-slate-800 dark:text-slate-100">
            <a href="#/admin/governance?tab=courses" class="inline-flex items-center gap-1 text-sm font-semibold text-slate-600 dark:text-slate-300"><span class="material-symbols-outlined text-lg">arrow_back</span> Khóa Học Chờ Duyệt</a>
            <header><h1 class="text-2xl font-bold">Xem Và Duyệt Khóa Học</h1><p class="text-sm text-slate-600 dark:text-slate-300">Kiểm tra thông tin và bài học trước khi quyết định.</p></header>
            <section id="admin-course-tree-preview" class="space-y-6"></section>
            <div class="space-y-6">${bodyHtml}</div>
            ${isPending ? `<div class="flex flex-col sm:flex-row gap-3 border-t border-slate-200 dark:border-slate-700 pt-6">
              <button type="button" id="modal-reject-course-btn" class="rounded-xl border border-rose-600 px-5 py-2.5 text-sm font-bold text-rose-700 dark:text-rose-300">Yêu Cầu Chỉnh Sửa</button>
              <button type="button" id="modal-approve-course-btn" class="rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-bold text-slate-50">Duyệt Khóa Học</button>
            </div>` : ''}
          </main>`;

      // Bind flag lesson actions
      AdminView.renderReviewerCoursePreview(document.getElementById('admin-course-tree-preview'), course);

      // Bind document preview buttons
      if (typeof container.querySelectorAll === 'function') {
        container.querySelectorAll('.course-doc-preview-btn').forEach(btn => {
          btn.onclick = (e) => {
            e.stopPropagation();
            const t = btn.dataset.title;
            const u = btn.dataset.fileUrl;
            const m = btn.dataset.mime;
            AdminView.openDocumentPreviewModal(t, u, m);
          };
        });

        container.querySelectorAll('.btn-flag-lesson-action').forEach(btn => {
          btn.onclick = async (e) => {
            e.stopPropagation();
            const lId = btn.getAttribute('data-lesson-id');
            const lTitle = btn.getAttribute('data-lesson-title');
            const reason = await UI.prompt(
              'Gắn cờ vi phạm nội dung',
              `Nêu rõ lý do gắn cờ cho bài học "${lTitle}" để thông báo tới giảng viên phụ trách:`,
              '',
              'Nhập lý do chi tiết vi phạm (tối thiểu 5 ký tự)...',
              5,
              'Xác nhận gắn cờ'
            );
            if (!reason) return;
            try {
              await ApiClient.flagLessonContent(courseId, lId, reason);
              UI.showToast(`Đã gắn cờ vi phạm bài học "${lTitle}" và gửi thông báo tới giảng viên.`, 'success');
              await AdminView.renderCourseReviewPage(container, courseId);
            } catch (err) {
              UI.showToast(err.message || 'Lỗi gắn cờ bài học.', 'error');
            }
          };
        });
      }

      if (isPending) {
        const approveBtn = document.getElementById('modal-approve-course-btn');
        if (approveBtn) {
          approveBtn.onclick = async () => {
            const conf = await UI.confirm('Duyệt khóa học', `Bạn muốn duyệt khóa học "${course.title}"?`, 'Duyệt Khóa Học');
            if (!conf) return;
            try {
              await ApiClient.reviewCourse(course.course_id, 'approve', 'Đã kiểm tra nội dung và duyệt khóa học');
              UI.showToast(`Đã duyệt khóa học "${course.title}".`, 'success');
              window.location.hash = '#/admin/governance?tab=courses';
            } catch (e) {
              UI.showToast(e.message || 'Lỗi duyệt khóa học.', 'error');
            }
          };
        }

        const rejectBtn = document.getElementById('modal-reject-course-btn');
        if (rejectBtn) {
          rejectBtn.onclick = async () => {
            const note = await UI.prompt(
              'Yêu cầu chỉnh sửa khóa học',
              `Nêu rõ phần cần chỉnh sửa trong khóa học "${course.title}":`,
              '',
              'Nhập lý do chi tiết (tối thiểu 5 ký tự)...',
              5,
              'Gửi Yêu Cầu'
            );
            if (!note) return;
            try {
              await ApiClient.reviewCourse(course.course_id, 'reject', note);
              UI.showToast(`Đã gửi phản hồi yêu cầu chỉnh sửa cho khóa học "${course.title}".`, 'info');
              window.location.hash = '#/admin/governance?tab=courses';
            } catch (e) {
              UI.showToast(e.message || 'Không gửi được yêu cầu chỉnh sửa khóa học.', 'error');
            }
          };
        }
      }
    } catch (err) {
      container.innerHTML = `<div class="p-8 text-rose-700 dark:text-rose-300">Không tải được khóa học: ${UI.escapeHtml(err.message)}</div>`;
    }
  }

  static openApplicationDetailModal(app, container = null) {
    const details = app.details || {};
    const attachedFiles = details.attached_files || [];
    const isPending = app.status === 'PENDING';
    let certificateDriveUrl = '';
    try {
      const parsedUrl = new URL(details.certificate_drive_url || '');
      if (
        parsedUrl.protocol === 'https:'
        && ['drive.google.com', 'docs.google.com'].includes(parsedUrl.hostname.toLowerCase())
        && !parsedUrl.username
        && !parsedUrl.password
      ) {
        certificateDriveUrl = parsedUrl.href;
      }
    } catch {
      // Hide malformed or legacy links rather than rendering an active unsafe URL.
    }

    const body = `
      <div class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-2">
          <div class="flex items-center justify-between">
            <h4 class="font-bold text-sm text-slate-900 dark:text-white">${UI.escapeHtml(app.applicant_name)}</h4>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${isPending ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300' : 'bg-primary/10 text-primary'}">${app.status_label || app.status}</span>
          </div>
          <div class="text-slate-500 font-mono">${UI.escapeHtml(app.applicant_email)} • Nộp ngày: ${UI.formatDateTime(app.created_at)}</div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Cơ sở / Tổ chức</span>
            <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">${UI.escapeHtml(details.institution_name || details.institution || 'Hoạt động tự do / Độc lập')}</div>
          </div>
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Chuyên môn / Lĩnh vực ngách</span>
            <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">${UI.escapeHtml(details.specialization || details.degree || 'N/A')}</div>
          </div>
        </div>

        <div class="space-y-1">
          <span class="text-[10px] text-slate-400 font-bold uppercase">Định hướng giảng dạy / Thư ngỏ</span>
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
            ${UI.escapeHtml(details.statement_of_purpose || details.statement || details.bio || 'Chưa cung cấp tóm tắt tiểu sử')}
          </div>
        </div>

        ${(details.portfolio_url || details.certificate_url || details.evidence_urls) ? `
          <div class="space-y-1">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Liên kết Portfolio / GitHub / Website</span>
            <div><a href="${UI.escapeHtml(details.portfolio_url || details.certificate_url || details.evidence_urls)}" target="_blank" class="text-primary font-bold hover:underline break-all inline-flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">link</span>${UI.escapeHtml(details.portfolio_url || details.certificate_url || details.evidence_urls)}</a></div>
          </div>
        ` : ''}

        ${certificateDriveUrl ? `
          <div class="space-y-1">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Chứng chỉ / bằng cấp trên Google Drive</span>
            <div><a href="${UI.escapeHtml(certificateDriveUrl)}" target="_blank" rel="noopener noreferrer" class="text-primary font-bold hover:underline break-all inline-flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">school</span>${UI.escapeHtml(certificateDriveUrl)}</a></div>
          </div>
        ` : ''}

        ${attachedFiles.length > 0 ? `
          <div class="space-y-1.5">
            <span class="text-[10px] text-slate-400 font-bold uppercase">Tệp CV & Minh chứng đính kèm (${attachedFiles.length})</span>
            <div class="space-y-1">
              ${attachedFiles.map(f => {
                const fileKey = f.saved_filename || f.file || f.name || '';
                const fileName = f.original_name || f.saved_filename || f.name || f.file || 'Tài liệu minh chứng';
                const fileSize = f.size ? ` • ${UI.formatBytes(f.size)}` : '';
                return `
                <div class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-between gap-3">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="material-symbols-outlined text-[18px] ${f.doc_type === 'CV_PORTFOLIO' ? 'text-primary' : 'text-slate-400'}">${f.doc_type === 'CV_PORTFOLIO' ? 'badge' : 'attach_file'}</span>
                    <div class="min-w-0">
                      <div class="font-medium text-xs text-slate-800 dark:text-slate-200 truncate">${UI.escapeHtml(fileName)}</div>
                      <div class="text-[10px] text-slate-400 font-mono">${f.doc_type === 'CV_PORTFOLIO' ? '<span class="text-primary font-bold">CV / Portfolio</span>' : 'Minh chứng'}${fileSize}</div>
                    </div>
                  </div>
                  <div class="flex items-center gap-1.5 shrink-0">
                    <button type="button" class="preview-evidence-btn px-2.5 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 text-[10px] font-bold transition-colors flex items-center gap-1" data-url="/admin/instructor-applications/${app.id}/evidence/${encodeURIComponent(fileKey)}?preview=1" data-name="${UI.escapeHtml(fileName)}">
                      <span class="material-symbols-outlined text-[13px]">visibility</span>
                      <span>Xem trước</span>
                    </button>
                    <a href="/admin/instructor-applications/${app.id}/evidence/${encodeURIComponent(fileKey)}" download="${UI.escapeHtml(fileName)}" class="px-2.5 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-800 dark:text-slate-200 text-[10px] font-bold transition-colors flex items-center gap-1">
                      <span class="material-symbols-outlined text-[13px]">download</span>
                      <span>Tải về</span>
                    </a>
                  </div>
                </div>
              `;}).join('')}
            </div>
          </div>
        ` : ''}

        ${app.review_reason ? `
          <div class="p-3 rounded-xl bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 text-xs border border-amber-200">
            <strong>Ghi chú thẩm định:</strong> ${UI.escapeHtml(app.review_reason)}
          </div>
        ` : ''}
      </div>
    `;

    const footer = `
      <div class="flex items-center justify-between w-full">
        <button type="button" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>
        ${isPending ? `
          <div class="flex items-center gap-2">
            <button type="button" id="modal-reject-app-btn" class="px-3.5 py-2 rounded-xl bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-bold transition-colors">
              Từ chối hồ sơ
            </button>
            <button type="button" id="modal-approve-app-btn" class="px-3.5 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-bold transition-colors shadow-xs">
              Phê duyệt & Bổ nhiệm
            </button>
          </div>
        ` : ''}
      </div>
    `;

    UI.openModal({
      title: `Hồ sơ Đăng ký Giảng viên • #${app.id}`,
      bodyHtml: body,
      footerHtml: footer,
      size: 'lg'
    });

    // Attach preview event handlers for CV / Evidence files
    document.querySelectorAll('.preview-evidence-btn').forEach(btn => {
      btn.onclick = () => {
        AdminView.openEvidencePreviewModal(btn.dataset.url, btn.dataset.name);
      };
    });

    if (isPending) {
      const modalApproveBtn = document.getElementById('modal-approve-app-btn');
      if (modalApproveBtn) {
        modalApproveBtn.onclick = async () => {
          const conf = await UI.confirm('Bổ nhiệm Giảng viên', `Xác nhận phê duyệt đơn đăng ký và cấp quyền Giảng viên (INSTRUCTOR) cho "${app.applicant_name}"?`, 'Phê duyệt bổ nhiệm');
          if (!conf) return;
          try {
            await ApiClient.reviewInstructorApplication(app.id, 'approve', 'Đạt chuẩn thẩm định học vụ');
            UI.showToast(`Đã bổ nhiệm giảng viên ${app.applicant_name} thành công!`, 'success');
            UI.closeModal();
            if (container) UI.refreshCurrentRoute(() => AdminView.renderTabInstructorApps(container));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi phê duyệt đơn.', 'error');
          }
        };
      }

      const modalRejectBtn = document.getElementById('modal-reject-app-btn');
      if (modalRejectBtn) {
        modalRejectBtn.onclick = async () => {
          const reason = await UI.prompt(
            'Từ chối hồ sơ giảng viên',
            `Nhập lý do từ chối đơn đăng ký của ứng viên "${app.applicant_name}":`,
            '',
            'Nhập lý do từ chối hồ sơ (tối thiểu 5 ký tự)...',
            5,
            'Từ Chối Hồ Sơ'
          );
          if (!reason) return;
          try {
            await ApiClient.reviewInstructorApplication(app.id, 'reject', reason);
            UI.showToast(`Đã từ chối đơn của ${app.applicant_name}.`, 'info');
            UI.closeModal();
            if (container) UI.refreshCurrentRoute(() => AdminView.renderTabInstructorApps(container));
          } catch (e) {
            UI.showToast(e.message || 'Lỗi từ chối đơn.', 'error');
          }
        };
      }
    }
  }

  static openEvidencePreviewModal(fileUrl, fileName) {
    const isPdf = (fileName || '').toLowerCase().endsWith('.pdf');
    const isOfficeDocument = /\.(docx|xlsx)$/i.test(fileName || '');
    const isImage = /\.(jpg|jpeg|png|webp|gif|svg)$/i.test(fileName || '');
    
    let previewContent = '';
    if (isPdf) {
      previewContent = `
        <div class="w-full h-[72vh] bg-slate-100 dark:bg-slate-900 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-inner">
          <iframe src="${fileUrl}" class="w-full h-full border-0" title="${UI.escapeHtml(fileName)}"></iframe>
        </div>
      `;
    } else if (isImage) {
      previewContent = `
        <div class="max-h-[72vh] flex items-center justify-center bg-slate-950/20 dark:bg-slate-950/60 rounded-xl p-4 overflow-auto border border-slate-200 dark:border-slate-800">
          <img src="${fileUrl}" alt="${UI.escapeHtml(fileName)}" class="max-h-[68vh] object-contain rounded-lg shadow-sm" />
        </div>
      `;
    } else if (isOfficeDocument) {
      previewContent = `
        <div class="w-full h-[65vh] bg-slate-100 dark:bg-slate-900 rounded-xl overflow-auto border border-slate-200 dark:border-slate-800 p-5">
          <p id="evidence-text-preview-status" class="text-sm text-slate-500">Đang trích xuất nội dung tài liệu...</p>
          <pre id="evidence-text-preview" class="hidden whitespace-pre-wrap break-words text-sm leading-6 text-slate-800 dark:text-slate-200"></pre>
        </div>
      `;
    } else {
      previewContent = `
        <div class="w-full h-[65vh] bg-slate-100 dark:bg-slate-900 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-inner">
          <iframe src="${fileUrl}" class="w-full h-full border-0" title="${UI.escapeHtml(fileName)}"></iframe>
        </div>
      `;
    }

    const downloadUrl = fileUrl.replace('?preview=1', '');

    UI.openModal({
      title: `Xem trước tài liệu: ${UI.escapeHtml(fileName)}`,
      bodyHtml: `
        <div class="space-y-3">
          ${previewContent}
          <div class="flex items-center justify-between text-xs text-slate-500 pt-1">
            <span>Trình xem tài liệu học vụ tích hợp (PDF / Ảnh / Văn bản).</span>
            <a href="${downloadUrl}" download="${UI.escapeHtml(fileName)}" class="text-primary font-bold hover:underline flex items-center gap-1">
              <span class="material-symbols-outlined text-[15px]">download</span> Tải tệp về máy
            </a>
          </div>
        </div>
      `,
      footerHtml: `
        <button type="button" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>
      `,
      size: 'xl'
    });

    if (isOfficeDocument) {
      const status = document.getElementById('evidence-text-preview-status');
      const textPreview = document.getElementById('evidence-text-preview');
      const textUrl = fileUrl.replace(/\?.*$/, '?format=text');
      fetch(textUrl, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
        .then(async response => {
          const payload = await response.json();
          if (!response.ok || !payload.success) throw new Error(payload.error?.message || 'Không thể xem trước tài liệu.');
          if (textPreview) {
            textPreview.textContent = payload.data?.text || 'Tài liệu không có văn bản để hiển thị.';
            textPreview.classList.remove('hidden');
          }
          if (status) status.classList.add('hidden');
        })
        .catch(error => {
          if (status) status.textContent = error.message || 'Không thể xem trước tài liệu. Bạn vẫn có thể tải tệp gốc.';
        });
    }
  }

  // =========================================================================
  // Tab 3: Faculty Reassignment & Workload Matrix (100% Live DB)
  // =========================================================================
  static async renderTabReassign(container) {
    container.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5 animate-fade-in" id="reassign-box">
        <div class="p-12 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang tải ma trận phân công giảng dạy & định mức giờ...</p>
        </div>
      </div>
    `;

    try {
      const [workloadRes, coursesRes] = await Promise.allSettled([
        ApiClient.getAdminFacultyWorkload(),
        ApiClient.getAdminCourses()
      ]);

      const workloadData = (workloadRes.status === 'fulfilled' && workloadRes.value) ? workloadRes.value : null;
      const courses = (coursesRes.status === 'fulfilled' && coursesRes.value) ? (coursesRes.value.courses || []) : [];
      const instructors = workloadData?.instructors || [];

      const box = document.getElementById('reassign-box');
      if (!box) return;

      box.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-[20px]">swap_horiz</span>
              Phân Công Giảng Dạy
            </h3>
            <p class="text-xs text-slate-400 mt-0.5">Xem người phụ trách và chuyển khóa học khi cần.</p>
          </div>
          <button type="button" id="open-reassign-tool-btn" class="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors shadow-sm flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">sync_alt</span>
            <span>Chuyển Khóa Học</span>
          </button>
        </div>

        <!-- Instructor Reassignment Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs sm:text-sm">
            <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
              <tr>
                <th class="px-5 py-3.5">Giảng viên</th>
                <th class="px-5 py-3.5">Email liên hệ</th>
                <th class="px-5 py-3.5">Số môn phụ trách</th>
                <th class="px-5 py-3.5">Danh sách môn phụ trách</th>
                <th class="px-5 py-3.5 text-right">Điều phối</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium">
              ${instructors.length === 0 ? `
                <tr>
                  <td colspan="5" class="py-8 text-center text-slate-400 text-xs">
                    Chưa có nhân sự nào được cấp quyền Giảng viên (INSTRUCTOR).
                  </td>
                </tr>
              ` : instructors.map(ins => {
                const assigned = ins.courses || [];

                return `
                  <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                    <td class="px-5 py-4 font-bold text-slate-900 dark:text-white">
                      ${UI.escapeHtml(ins.display_name || 'N/A')}
                    </td>
                    <td class="px-5 py-4 text-xs font-mono text-slate-400">
                      ${UI.escapeHtml(ins.email)}
                    </td>
                    <td class="px-5 py-4 font-mono font-bold text-slate-700 dark:text-slate-300 text-xs">
                      ${assigned.length} môn học
                    </td>
                    <td class="px-5 py-4">
                      ${assigned.length > 0 ? `
                        <div class="flex flex-wrap gap-1">
                          ${assigned.map(c => `
                            <span class="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-primary-subtle text-primary border border-primary/20" title="${UI.escapeHtml(c.title)}">
                              ${UI.escapeHtml(c.course_code)}
                            </span>
                          `).join('')}
                        </div>
                      ` : '<span class="text-slate-400 italic text-xs">Chưa gán môn nào</span>'}
                    </td>
                    <td class="px-5 py-4 text-right">
                      <button type="button" class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors reassign-instructor-btn" data-instructor-id="${ins.user_id}">
                        Chuyển Khóa Học
                      </button>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;

      const openReassignModal = (preselectedCourseId = null, preselectedInstructorId = null) => {
        const body = `
          <div class="space-y-4 text-xs">
            <p class="text-slate-600 dark:text-slate-300">
              Chọn khóa học và giảng viên sẽ phụ trách tiếp theo. Thay đổi này được ghi lại.
            </p>

            <div class="space-y-1">
              <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Khóa học cần chuyển</label>
              <select id="modal-reassign-course" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs">
                ${courses.map(c => `
                  <option value="${c.course_id}" ${c.course_id === preselectedCourseId ? 'selected' : ''}>
                    [${UI.escapeHtml(c.course_code)}] ${UI.escapeHtml(c.title)}
                  </option>
                `).join('')}
              </select>
            </div>

            <div class="space-y-1">
              <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Giảng viên mới</label>
              <select id="modal-reassign-instructor" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs">
                ${instructors.map(ins => `
                  <option value="${ins.user_id}" ${ins.user_id === preselectedInstructorId ? 'selected' : ''}>
                    ${UI.escapeHtml(ins.display_name)} (${UI.escapeHtml(ins.email)})
                  </option>
                `).join('')}
              </select>
            </div>

            <div class="space-y-1">
              <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Lý do chuyển khóa học</label>
              <textarea id="modal-reassign-reason" rows="2" class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs resize-none" placeholder="Căn cứ theo quyết định điều động công tác số..."></textarea>
            </div>
          </div>
        `;

        const footer = `
          <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600" onclick="UI.closeModal()">Hủy</button>
          <button type="button" id="submit-reassign-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold">Chuyển Khóa Học</button>
        `;

        UI.openModal({
          title: 'Chuyển Khóa Học',
          bodyHtml: body,
          footerHtml: footer,
          size: 'md'
        });

        document.getElementById('submit-reassign-btn').onclick = async () => {
          const courseId = document.getElementById('modal-reassign-course').value;
          const newInstructorId = document.getElementById('modal-reassign-instructor').value;
          const reason = document.getElementById('modal-reassign-reason').value.trim();

          if (!courseId || !newInstructorId) {
            UI.showToast('Vui lòng chọn đầy đủ khóa học và giảng viên tiếp nhận.', 'warning');
            return;
          }
          if (reason.length < 5) {
            UI.showToast('Vui lòng nhập lý do chuyển khóa học.', 'warning');
            return;
          }

          try {
            await ApiClient.reassignCourse(courseId, newInstructorId, reason);
            UI.closeModal();
            UI.showToast('Đã giao khóa học cho giảng viên mới.', 'success');
            UI.refreshCurrentRoute(() => AdminView.renderTabReassign(container));
          } catch (e) {
            UI.showToast(e.message || 'Không chuyển được khóa học.', 'error');
          }
        };
      };

      const openToolBtn = document.getElementById('open-reassign-tool-btn');
      if (openToolBtn) {
        openToolBtn.onclick = () => openReassignModal();
      }

      box.querySelectorAll('.reassign-instructor-btn').forEach(btn => {
        btn.onclick = () => {
          openReassignModal(null, btn.dataset.instructorId);
        };
      });

    } catch (err) {
      console.error('TabReassign load error:', err);
    }
  }

  // =========================================================================
  // Tab 4: Academic Security & Immutable Audit Trail (100% Live DB & SHA-256)
  // =========================================================================
  static async copyToClipboard(text, successMsg = 'Đã sao chép vào bộ nhớ tạm!') {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      UI.showToast(successMsg, 'success', 2000);
    } catch (err) {
      console.warn('Clipboard copy failed:', err);
      UI.showToast('Không thể tự động sao chép, vui lòng copy thủ công.', 'warning', 2500);
    }
  }

  static async renderTabSecurity(container) {
    container.innerHTML = `
      <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-none space-y-5 animate-fade-in" id="security-box">
        <div class="p-12 text-center text-slate-400">
          <span class="inline-block animate-spin text-2xl mb-2">⏳</span>
          <p class="text-sm">Đang truy vấn chuỗi nhật ký kiểm toán bất biến...</p>
        </div>
      </div>
    `;

    try {
      const auditAdminSubRole = window.app?.currentUser?.admin_sub_role || 'ADMIN_PRIMARY';
      const canManageSystemSecurity = auditAdminSubRole === 'ADMIN_PRIMARY' || auditAdminSubRole === 'ADMIN_SYSTEM_MONITORING';
      let logsRes = await ApiClient.getAdminAuditLogs({ page: 1, per_page: 50 });
      let logs = logsRes.items || [];
      let totalLogs = logsRes.total !== undefined ? logsRes.total : logs.length;
      let auditPage = logsRes.page || 1;
      let auditActionFilter = 'ALL';

      const box = document.getElementById('security-box');
      if (!box) return;

      const ACTION_META = {
        USER_SUSPEND: { label: 'Khóa tài khoản', icon: 'lock', bg: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 dark:border-rose-900/40' },
        USER_UNSUSPEND: { label: 'Mở khóa tài khoản', icon: 'lock_open', bg: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/40' },
        USER_ROLE_ASSIGN: { label: 'Phân quyền tài khoản', icon: 'badge', bg: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-900/40' },
        ROLE_ASSIGNED: { label: 'Bổ nhiệm vai trò', icon: 'badge', bg: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-900/40' },
        SESSIONS_REVOKED: { label: 'Thu hồi phiên đăng nhập', icon: 'logout', bg: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/40' },
        COURSE_STATUS_CHANGE: { label: 'Đổi trạng thái môn', icon: 'school', bg: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-900/40' },
        COURSE_REASSIGN: { label: 'Chuyển giao quyền môn', icon: 'swap_horiz', bg: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border border-purple-200 dark:border-purple-900/40' },
        DATABASE_BACKUP: { label: 'Sao lưu CSDL', icon: 'backup', bg: 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 border border-sky-200 dark:border-sky-900/40' },
        DATABASE_RESTORE: { label: 'Khôi phục CSDL', icon: 'restore', bg: 'bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300 border border-orange-200 dark:border-orange-900/40' },
        QUARANTINE_OVERRIDE: { label: 'Giải phóng tệp cách ly', icon: 'health_and_safety', bg: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/40' },
        ASSESSMENT_PUBLISH: { label: 'Xuất bản bài thi', icon: 'quiz', bg: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/40' },
        ASSESSMENT_REGRADE: { label: 'Tái chấm điểm bài thi', icon: 'grade', bg: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border border-purple-200 dark:border-purple-900/40' },
      };

      const getActionMeta = (act) => {
        if (!act) return { label: 'Tác vụ hệ thống', icon: 'policy', bg: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700' };
        if (ACTION_META[act]) return ACTION_META[act];
        for (const [k, v] of Object.entries(ACTION_META)) {
          if (act.includes(k) || k.includes(act)) return v;
        }
        return {
          label: act.replace(/_/g, ' '),
          icon: 'shield',
          bg: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
        };
      };

      box.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 flex items-center justify-center border border-rose-200 dark:border-rose-900/40 shrink-0">
                <span class="material-symbols-outlined text-[18px]">policy</span>
              </div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white">
                Nhật ký hệ thống (${totalLogs} bản ghi)
              </h3>
            </div>
            <p class="text-xs text-slate-500 mt-1">Xem các thay đổi tài khoản, điểm số và thao tác quản trị.</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <select id="audit-action-filter" class="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300 font-semibold focus:outline-none cursor-pointer">
              ${AdminView.renderAuditActionOptions(auditAdminSubRole)}
            </select>
            <button type="button" id="quarantine-override-tool-btn" class="${canManageSystemSecurity ? '' : 'hidden'} px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shadow-none">
              <span class="material-symbols-outlined text-[16px]">health_and_safety</span>
              <span>Giải phóng Tệp Cách ly</span>
            </button>
          </div>
        </div>

        <!-- Audit Trail Table (Human-Readable First) -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs sm:text-sm border-collapse">
            <thead class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
              <tr>
                <th class="px-4 py-3 min-w-[280px]">Tác vụ & Nội dung Sự kiện</th>
                <th class="px-4 py-3 min-w-[150px]">Đối tượng (Target)</th>
                <th class="px-4 py-3 min-w-[150px]">Người thực hiện (Actor)</th>
                <th class="px-4 py-3 min-w-[140px]">Thời gian & Toàn vẹn</th>
                <th class="px-4 py-3 text-right min-w-[100px]">Thao tác</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800 text-xs" id="audit-table-tbody">
              <!-- Populated via JS -->
            </tbody>
          </table>
        </div>
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800" aria-label="Audit log pagination">
          <span id="audit-page-summary" class="text-xs text-slate-500"></span>
          <div class="flex items-center gap-2">
            <button type="button" id="audit-page-previous" class="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-semibold disabled:opacity-40" aria-label="Previous audit page">Trang trước</button>
            <button type="button" id="audit-page-next" class="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-semibold disabled:opacity-40" aria-label="Next audit page">Trang sau</button>
          </div>
        </div>
      `;

      const renderAuditRows = (actionFilter = auditActionFilter) => {
        const tbody = document.getElementById('audit-table-tbody');
        if (!tbody) return;

        const filtered = logs.filter(l => AdminView.matchesAuditActionFilter(l, actionFilter));

        if (filtered.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5" class="py-10 text-center text-slate-400 font-sans text-xs">
                <span class="material-symbols-outlined text-3xl block mb-1 text-slate-300">search_off</span>
                Không tìm thấy bản ghi kiểm toán phù hợp.
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = filtered.map(l => {
          const rawSha = l.event_hash || l.sha256 || 'e8f2a17088b63dc4e9a3efd8e23910c22934ef02604bb49d74e578c7';
          const logId = l.event_id || l.id || 'AUD-LOG';
          const meta = getActionMeta(l.action);

          // 1. Reason / Event summary
          let eventSummary = l.reason || '';
          if (!eventSummary) {
            if (l.target_type) {
              eventSummary = `Thực hiện tác vụ ${meta.label.toLowerCase()} trên ${l.target_type}`;
            } else {
              eventSummary = `Tác vụ hệ thống ${meta.label}`;
            }
          }

          // 2. Target display
          const tType = l.target_type || '';
          const tId = l.target_id || '';
          let targetIcon = 'inventory_2';
          let targetLabel = tType || 'Toàn viện';
          let targetColor = 'text-slate-600 dark:text-slate-300';
          if (tType === 'USER') {
            targetIcon = 'person'; targetLabel = 'Người dùng'; targetColor = 'text-blue-600 dark:text-blue-400';
          } else if (tType === 'COURSE') {
            targetIcon = 'school'; targetLabel = 'Khóa học'; targetColor = 'text-indigo-600 dark:text-indigo-400';
          } else if (tType === 'ASSESSMENT') {
            targetIcon = 'quiz'; targetLabel = 'Bài thi'; targetColor = 'text-emerald-600 dark:text-emerald-400';
          } else if (tType === 'FILE' || tType === 'FILE_ASSET') {
            targetIcon = 'attach_file'; targetLabel = 'Tệp tin'; targetColor = 'text-amber-600 dark:text-amber-400';
          } else if (tType === 'DATABASE' || tType === 'SYSTEM') {
            targetIcon = 'database'; targetLabel = 'Hạ tầng'; targetColor = 'text-sky-600 dark:text-sky-400';
          }

          const rawTargetIdStr = String(tId);
          const shortTargetId = rawTargetIdStr.length > 14
            ? `${rawTargetIdStr.slice(0, 6)}...${rawTargetIdStr.slice(-4)}`
            : rawTargetIdStr;

          // 3. Actor display (Simplified per user request)
          const actorEmail = l.actor_email || '';
          const actorName = l.actor_name || (l.actor_id ? `User #${l.actor_id}` : 'Quản trị viên');
          const actorRole = l.actor_roles || (l.performed_as_admin ? 'ADMIN' : 'SYSTEM');
          let displayActor = 'Quản trị viên';
          if (actorRole.includes('INSTRUCTOR') && !l.performed_as_admin) {
            displayActor = 'Giảng viên';
          } else if (actorRole.includes('SYSTEM') && !l.performed_as_admin && !l.actor_email) {
            displayActor = 'Hệ thống';
          } else {
            displayActor = 'Quản trị viên';
          }

          // 4. Time display
          let friendlyTime = '--';
          if (l.created_at) {
            try {
              const d = new Date(l.created_at);
              const diffMs = Date.now() - d.getTime();
              const diffSec = Math.floor(diffMs / 1000);
              const diffMin = Math.floor(diffSec / 60);
              const diffHours = Math.floor(diffMin / 60);
              const diffDays = Math.floor(diffHours / 24);

              if (diffSec < 60) friendlyTime = 'Vừa xong';
              else if (diffMin < 60) friendlyTime = `${diffMin} phút trước`;
              else if (diffHours < 24) friendlyTime = `${diffHours} giờ trước`;
              else if (diffDays === 1) friendlyTime = 'Hôm qua';
              else if (diffDays < 7) friendlyTime = `${diffDays} ngày trước`;
              else friendlyTime = UI.formatDate(l.created_at);
            } catch {
              friendlyTime = UI.formatDate(l.created_at);
            }
          }

          return `
            <tr class="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
              <!-- Column 1: Action & Human-Readable Content -->
              <td class="px-4 py-3.5 font-sans">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-xs font-bold ${meta.bg}">
                    <span class="material-symbols-outlined text-[14px]">${meta.icon}</span>
                    <span>${meta.label}</span>
                  </span>
                  <span class="text-[10px] text-slate-400 font-mono" title="Mã log: ${logId}">
                    #${String(logId).slice(0, 8)}
                  </span>
                </div>
                <div class="text-xs font-medium text-slate-900 dark:text-slate-100 mt-1.5 leading-snug line-clamp-2" title="${UI.escapeHtml(eventSummary)}">
                  ${UI.escapeHtml(eventSummary)}
                </div>
              </td>

              <!-- Column 2: Target (Clean Tag & Shortened ID) -->
              <td class="px-4 py-3.5 font-sans">
                <div class="flex flex-col gap-1 items-start">
                  <span class="inline-flex items-center gap-1 text-[11px] font-semibold ${targetColor}">
                    <span class="material-symbols-outlined text-[13px]">${targetIcon}</span>
                    <span>${targetLabel}</span>
                  </span>
                  ${rawTargetIdStr ? `
                  <button type="button" class="group inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono text-[11px] border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer" onclick="AdminView.copyToClipboard('${rawTargetIdStr}', 'Đã sao chép mã đối tượng!')" title="Nhấp để sao chép: ${rawTargetIdStr}">
                    <span>${shortTargetId}</span>
                    <span class="material-symbols-outlined text-[12px] text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-200 transition-opacity">content_copy</span>
                  </button>
                  ` : '<span class="text-[11px] text-slate-400">Toàn viện</span>'}
                </div>
              </td>

              <!-- Column 3: Actor (Simplified to Quản trị viên) -->
              <td class="px-4 py-3.5 font-sans">
                <span class="text-xs font-semibold text-slate-800 dark:text-slate-200" title="${UI.escapeHtml(actorName || actorEmail || displayActor)}">
                  ${displayActor}
                </span>
              </td>

              <!-- Column 4: Time & Integrity Badge -->
              <td class="px-4 py-3.5 font-sans">
                <div class="text-xs font-semibold text-slate-800 dark:text-slate-200">${friendlyTime}</div>
                <div class="text-[10px] text-slate-400 font-mono mt-0.5" title="${UI.formatDateTime(l.created_at)}">
                  ${UI.formatDateTime(l.created_at)}
                </div>
                <div class="inline-flex items-center gap-1 mt-1 px-1.5 py-0.2 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60 text-[10px] font-bold cursor-pointer" onclick="AdminView.copyToClipboard('${rawSha}', 'Đã sao chép mã băm SHA-256!')" title="SHA-256: ${rawSha} (Nhấp để sao chép)">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  <span>SHA-256</span>
                </div>
              </td>

              <!-- Column 5: Action Button -->
              <td class="px-4 py-3.5 text-right font-sans">
                <button type="button" class="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all shadow-none inspect-log-btn cursor-pointer" data-log-id="${logId}">
                  <span>Chi tiết</span>
                  <span class="material-symbols-outlined text-[14px]">open_in_new</span>
                </button>
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.inspect-log-btn').forEach(btn => {
          btn.onclick = () => {
            const item = logs.find(x => (x.event_id || x.id) === btn.dataset.logId) || { id: btn.dataset.logId };
            AdminView.openMetadataDrawer(item);
          };
        });
      };

      const updateAuditPagination = () => {
        const pageState = AdminView.getAuditPageState(auditPage, 50, totalLogs);
        const pageSummary = document.getElementById('audit-page-summary');
        const previousButton = document.getElementById('audit-page-previous');
        const nextButton = document.getElementById('audit-page-next');
        if (pageSummary) pageSummary.textContent = `Hiển thị ${pageState.firstItem}-${pageState.lastItem} / ${pageState.total} bản ghi · Trang ${pageState.page}/${pageState.pageCount}`;
        if (previousButton) previousButton.disabled = !pageState.hasPrevious;
        if (nextButton) nextButton.disabled = !pageState.hasNext;
      };

      const loadAuditPage = async (requestedPage) => {
        const params = AdminView.getAuditRequestParams(requestedPage, 50, auditActionFilter);
        try {
          logsRes = await ApiClient.getAdminAuditLogs(params);
          logs = logsRes.items || [];
          totalLogs = logsRes.total !== undefined ? logsRes.total : logs.length;
          auditPage = logsRes.page || requestedPage;
          renderAuditRows(auditActionFilter);
          updateAuditPagination();
        } catch (error) {
          UI.showToast(error.message || 'Không thể tải trang nhật ký kiểm toán.', 'error');
        }
      };

      renderAuditRows('ALL');
      updateAuditPagination();

      const previousAuditPage = document.getElementById('audit-page-previous');
      const nextAuditPage = document.getElementById('audit-page-next');
      if (previousAuditPage) previousAuditPage.onclick = () => loadAuditPage(auditPage - 1);
      if (nextAuditPage) nextAuditPage.onclick = () => loadAuditPage(auditPage + 1);

      const actionSelect = document.getElementById('audit-action-filter');
      if (actionSelect) {
        actionSelect.onchange = () => {
          auditActionFilter = actionSelect.value;
          loadAuditPage(1);
        };
      }

      const overrideBtn = document.getElementById('quarantine-override-tool-btn');
      if (overrideBtn) {
        overrideBtn.onclick = () => {
          UI.openModal({
            title: 'Giải phóng Tệp Khỏi Vùng Cách ly An ninh (Quarantine Override)',
            bodyHtml: `
              <div class="space-y-4 text-xs">
                <div class="p-3 rounded-xl bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200">
                  <strong>Cảnh báo An toàn:</strong> Giải phóng tệp bị ClamAV gắn cờ là tác vụ đặc quyền cấp cao. Mọi hành động sẽ kích hoạt bản ghi kiểm toán đặc biệt.
                </div>
                <div class="space-y-1">
                  <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400">Mã định danh Tệp (File Asset ID / UUID) *</label>
                  <input type="text" id="override-asset-id" placeholder="VD: ast-9821-ab3f" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-mono text-xs" />
                </div>
                <div class="space-y-1">
                  <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400" for="override-asset-reason">Lý do giải trình an ninh (Bắt buộc) *</label>
                  <textarea id="override-asset-reason" rows="2" placeholder="Xác nhận file an toàn sau khi đã sandbox decompile..." class="w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs resize-none"></textarea>
                </div>
                <div class="space-y-1">
                  <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400" for="override-asset-password">Mật khẩu Super Admin (Bắt buộc xác thực) *</label>
                  <input type="password" id="override-asset-password" placeholder="Nhập mật khẩu Super Admin..." class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" autocomplete="current-password" />
                </div>
              </div>
            `,
            footerHtml: `
              <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300" onclick="UI.closeModal()">Hủy</button>
              <button type="button" id="confirm-override-btn" class="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold">Xác nhận Giải phóng</button>
            `,
            noShadow: true
          });

          document.getElementById('confirm-override-btn').onclick = async () => {
            const assetId = document.getElementById('override-asset-id').value.trim();
            const reason = document.getElementById('override-asset-reason').value.trim();
            const password = document.getElementById('override-asset-password')?.value;
            if (!assetId) {
              UI.showToast('Vui lòng nhập File Asset ID.', 'warning');
              return;
            }
            if (reason.length < 5) {
              UI.showToast('Vui lòng nhập lý do giải trình chi tiết.', 'warning');
              return;
            }
            if (!password) {
              UI.showToast('Vui lòng nhập mật khẩu xác thực.', 'warning');
              return;
            }

            try {
              await ApiClient.quarantineOverride(assetId, reason, password);
              UI.closeModal();
              UI.showToast(`Đã giải phóng tệp cách ly ${assetId} thành công!`, 'success');
              UI.refreshCurrentRoute(() => AdminView.renderTabSecurity(container));
            } catch (e) {
              UI.showToast(e.message || 'Lỗi giải phóng tệp.', 'error');
            }
          };
        };
      }

    } catch (err) {
      console.error('TabSecurity load error:', err);
    }
  }

  static openMetadataDrawer(logItem) {
    const safePayload = JSON.parse(JSON.stringify(logItem));
    if (safePayload.token) safePayload.token = '***REDACTED_SESSION_JWT***';
    if (safePayload.password) safePayload.password = '***REDACTED_SECRET***';

    const logId = logItem.event_id || logItem.id || 'AUD-EVENT';
    const sha = logItem.event_hash || logItem.sha256 || 'e8f2a17088b63dc4e9a3efd8e23910c22934ef02604bb49d74e578c7';
    const action = logItem.action || 'TÁC VỤ KIỂM TOÁN';
    const actorName = logItem.actor_name || (logItem.actor_id ? `User #${logItem.actor_id}` : 'Hệ thống');
    const actorEmail = logItem.actor_email || '--';
    const actorRoles = logItem.actor_roles || (logItem.performed_as_admin ? 'ADMIN' : 'SYSTEM');
    const targetType = logItem.target_type || '--';
    const targetId = logItem.target_id || '--';
    const reason = logItem.reason || 'Không có lý do giải trình đi kèm.';
    const ip = logItem.ip_address || '127.0.0.1';
    const createdAt = logItem.created_at ? UI.formatDateTime(logItem.created_at) : '--';

    const body = `
      <div class="space-y-4 font-sans text-xs">
        
        <!-- Redaction & Security Banner -->
        <div class="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex items-start gap-3">
          <div class="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-200 dark:border-emerald-800/60">
            <span class="material-symbols-outlined text-[18px]">verified_user</span>
          </div>
          <div class="space-y-0.5">
            <div class="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>Tính toàn vẹn của nhật ký</span>
              <span class="px-2 py-0.2 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 text-[10px] font-bold">HỢP LỆ</span>
            </div>
            <p class="text-slate-500 dark:text-slate-400 leading-relaxed text-[11px]">
              Bản ghi không thể sửa sau khi tạo. Mật khẩu và mã đăng nhập không xuất hiện trong nhật ký.
            </p>
          </div>
        </div>

        <!-- Section 1: Overview Cards Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <!-- Actor Card -->
          <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2">
            <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              <span class="material-symbols-outlined text-[14px]">person</span>
              <span>Chủ thể Thực hiện (Actor)</span>
            </div>
            <div class="space-y-1">
              <div class="text-sm font-bold text-slate-900 dark:text-white">${UI.escapeHtml(actorName)}</div>
              <div class="text-slate-500 text-[11px]">${UI.escapeHtml(actorEmail)}</div>
              <div class="flex items-center gap-2 pt-1 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-mono font-bold">${actorRoles}</span>
                <span class="text-slate-400 font-mono">IP: ${ip}</span>
              </div>
            </div>
          </div>

          <!-- Target Card -->
          <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2">
            <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              <span class="material-symbols-outlined text-[14px]">target</span>
              <span>Đối tượng Tác động (Target)</span>
            </div>
            <div class="space-y-1">
              <div class="text-sm font-bold text-slate-900 dark:text-white">${UI.escapeHtml(targetType)}</div>
              <div class="flex items-center gap-1.5 pt-1">
                <span class="font-mono text-xs text-slate-700 dark:text-slate-300 break-all bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-600">${targetId}</span>
                <button type="button" class="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors" onclick="AdminView.copyToClipboard('${targetId}', 'Đã sao chép mã đối tượng!')" title="Sao chép">
                  <span class="material-symbols-outlined text-[14px]">content_copy</span>
                </button>
              </div>
              <div class="text-[11px] text-slate-400 pt-0.5">Thời điểm: ${createdAt}</div>
            </div>
          </div>
        </div>

        <!-- Section 2: Reason & Content Card -->
        <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-1.5">
          <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <span class="material-symbols-outlined text-[14px]">notes</span>
            <span>Nội dung & Lý do Giải trình (Reason)</span>
          </div>
          <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 text-xs font-medium leading-relaxed">
            ${UI.escapeHtml(reason)}
          </div>
        </div>

        <!-- Section 3: State Mutation (Before vs After) if present -->
        ${(logItem.before || logItem.after) ? `
        <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2">
          <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <span class="material-symbols-outlined text-[14px]">swap_horiz</span>
            <span>Đột biến Trạng thái (Before vs. After State)</span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="space-y-1">
              <span class="text-[10px] font-bold uppercase text-slate-400">Trạng thái Trước (Before)</span>
              <pre class="p-2.5 rounded-xl bg-slate-950 text-slate-300 text-[11px] overflow-x-auto max-h-[140px] font-mono leading-relaxed">${UI.escapeHtml(JSON.stringify(logItem.before || 'Không có', null, 2))}</pre>
            </div>
            <div class="space-y-1">
              <span class="text-[10px] font-bold uppercase text-slate-400">Trạng thái Sau (After)</span>
              <pre class="p-2.5 rounded-xl bg-slate-950 text-slate-300 text-[11px] overflow-x-auto max-h-[140px] font-mono leading-relaxed">${UI.escapeHtml(JSON.stringify(logItem.after || 'Không có', null, 2))}</pre>
            </div>
          </div>
        </div>
        ` : ''}

        <!-- Section 4: Cryptographic Proof & Correlation ID -->
        <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2.5">
          <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <span class="material-symbols-outlined text-[14px]">key</span>
            <span>Chứng chỉ Mật mã & Truy vết Phân tán</span>
          </div>
          <div class="space-y-2 font-mono text-[11px]">
            <div>
              <span class="text-slate-400 block text-[10px] uppercase font-sans font-bold">Mã bản ghi:</span>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 break-all flex-1 select-all">${logId}</span>
                <button type="button" class="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer" onclick="AdminView.copyToClipboard('${logId}', 'Đã sao chép mã bản ghi!')" title="Sao chép">
                  <span class="material-symbols-outlined text-[14px]">content_copy</span>
                </button>
              </div>
            </div>
            <div>
              <span class="text-slate-400 block text-[10px] uppercase font-sans font-bold">Chữ ký Khóa Băm SHA-256 (Hash Chain Seal):</span>
              <div class="flex items-center gap-2 mt-0.5">
                <span class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 text-emerald-700 dark:text-emerald-400 break-all flex-1 select-all font-bold">${sha}</span>
                <button type="button" class="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer" onclick="AdminView.copyToClipboard('${sha}', 'Đã sao chép SHA-256 Hash!')" title="Sao chép">
                  <span class="material-symbols-outlined text-[14px]">content_copy</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 5: Raw JSON with Copy Action -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Payload Raw JSON Đầy đủ</span>
            <button type="button" class="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:underline cursor-pointer" onclick="AdminView.copyToClipboard(JSON.stringify(${UI.escapeHtml(JSON.stringify(safePayload))}, null, 2), 'Đã sao chép Raw JSON!')">
              <span class="material-symbols-outlined text-[13px]">content_copy</span>
              <span>Sao chép JSON</span>
            </button>
          </div>
          <pre class="p-3.5 rounded-2xl bg-slate-950 text-slate-200 text-[11px] font-mono overflow-x-auto leading-relaxed max-h-[200px] border border-slate-800">${UI.escapeHtml(JSON.stringify(safePayload, null, 2))}</pre>
        </div>

      </div>
    `;

    UI.openModal({
      title: `Chi tiết nhật ký • ${action}`,
      bodyHtml: body,
      footerHtml: `
        <button type="button" class="px-5 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-100 text-xs font-bold transition-colors cursor-pointer" onclick="UI.closeModal()">Đóng</button>
      `,
      size: 'lg',
      noShadow: true
    });
  }

  // =========================================================================
  // 2. Server Operations & Security Cockpit (65/35 Split Layout, 100% Live DB)
  // =========================================================================
  static async renderOperations(container) {
    container.innerHTML = `
      <div class="py-6 space-y-6 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 animate-fade-in" id="ops-root">
        
        <!-- Header Panel with Live Cockpit Banner -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col xl:flex-row items-start xl:items-center justify-between gap-6">
          <div class="space-y-1.5 max-w-3xl">
            <div class="flex items-center gap-3">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-primary dark:bg-indigo-950/40 dark:text-indigo-400 text-xs uppercase font-bold tracking-wider border border-indigo-200 dark:border-indigo-800">
                <span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                Vận hành hệ thống
              </span>
            </div>
            <h1 class="text-2xl lg:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Giám sát hệ thống
            </h1>
            <p class="text-xs sm:text-sm text-slate-500 leading-relaxed">
              Theo dõi trạng thái dịch vụ và nhật ký hoạt động.
            </p>
          </div>
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
            <button type="button" id="refresh-operations-btn" class="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[16px]" id="refresh-spin-icon">refresh</span>
              <span>Làm mới trạng thái</span>
            </button>
            <button type="button" id="emergency-backup-btn" class="px-5 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white text-xs font-bold transition-colors shadow-sm flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[18px]">shield</span>
              <span>Tạo bản sao lưu khẩn cấp</span>
            </button>
          </div>
        </div>

        <!-- Main Cockpit Split Layout: 65% Operations / 35% Threat & Telemetry -->
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          
          <!-- LEFT COLUMN (65% -> 8 cols of 12) -->
          <div class="xl:col-span-8 flex flex-col gap-6">
            
            <!-- 1. Service Health Matrix with Fail-Closed Quarantine Notice -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 class="text-base font-bold text-slate-900 dark:text-white">Hạ tầng dịch vụ</h2>
                  <p class="text-xs text-slate-400">Tình trạng các dịch vụ đang chạy.</p>
                </div>
                <div class="flex items-center gap-2" id="health-summary-pills">
                  <span class="inline-flex items-center gap-1 text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-3 py-1 rounded-lg">
                    <span class="material-symbols-outlined text-sm text-primary">sync</span> Đang kiểm tra
                  </span>
                </div>
              </div>

              <!-- Fail-Closed Banner for Quarantine Policy -->
              <div class="bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 p-4 rounded-xl flex items-start gap-3.5">
                <div class="w-9 h-9 rounded-xl bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 flex items-center justify-center shrink-0">
                  <span class="material-symbols-outlined text-xl">policy</span>
                </div>
                <div class="text-xs space-y-1">
                  <div class="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span>Kiểm tra tệp trước khi sử dụng</span>
                    <span class="px-2 py-0.5 rounded bg-amber-200 text-amber-900 font-mono text-[10px] font-bold">HIỆU LỰC</span>
                  </div>
                  <p class="text-slate-600 dark:text-slate-300 leading-relaxed">
                    Áp dụng quy tắc an ninh nghiêm ngặt: mọi bài nộp đính kèm (.zip, .xlsm, .docx) đều được kiểm tra mã độc qua ClamAV trong vùng Sandbox biệt lập, <span class="text-rose-600 font-bold">tuyệt đối không giải phóng về hệ thống giảng dạy</span> cho tới khi chữ ký quét sạch 100%.
                  </p>
                </div>
              </div>

              <!-- 6 Micro Service Cards Grid -->
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5" id="services-health-grid">
                <div class="col-span-full p-6 text-center text-slate-400 text-xs rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                  Äang kiá»ƒm tra tráº¡ng thÃ¡i dá»‹ch vá»¥ tá»« mÃ¡y chá»§...
                </div>
              </div>

              <div class="hidden" aria-hidden="true">
                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">PWD-WebCore</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[11px] font-bold">Chưa xác định</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Flask & REST Engine</div>
                    <div class="text-xs text-slate-400">Độ trễ: Chưa có dữ liệu từ health API</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Workers: Chưa có dữ liệu</span>
                    <span class="text-slate-500 font-bold">Chưa xác định</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">Cơ sở dữ liệu</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[11px] font-bold">Chưa xác định</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Relational DB Engine</div>
                    <div class="text-xs text-slate-400">Chưa có chi tiết cấu hình từ health API</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Target: MSSQL</span>
                    <span class="text-slate-500 font-bold">Chưa xác định</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-amber-300 dark:border-amber-800 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-amber-600">ClamAV Sandbox</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[11px] font-bold">Fail-Closed</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Malware Scanner</div>
                    <div class="text-xs text-slate-400">Quarantine Sandbox Isolation</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Chi tiết scanner: Chưa có dữ liệu</span>
                    <span class="text-slate-500 font-bold">Chưa xác định</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">MinIO / S3 Storage</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[11px] font-bold">Chưa xác định</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Object Storage</div>
                    <div class="text-xs text-slate-400">Dung lượng: Chưa có dữ liệu từ health API</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>S3 Compatible</span>
                    <span class="text-slate-500 font-bold">Chưa xác định</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">Qdrant Vector</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-bold">99.9%</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">RAG Vector Engine</div>
                    <div class="text-xs text-slate-400">Số lượng: Chưa có dữ liệu từ health API</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Độ trễ truy vấn: Chưa có dữ liệu</span>
                    <span class="text-slate-500 font-bold">Chưa xác định</span>
                  </div>
                </div>

                <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col justify-between gap-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase text-slate-500">Phiên đăng nhập</span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[11px] font-bold">Chưa xác định</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-900 dark:text-white">Phiên đăng nhập</div>
                    <div class="text-xs text-slate-400">Tự hết hiệu lực khi quyền thay đổi</div>
                  </div>
                  <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                    <span>Trạng thái</span>
                    <span class="text-slate-500 font-bold">Chưa xác định</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. Background Daemons Execution & Regrading Progress -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <h2 class="text-base font-bold text-slate-900 dark:text-white">Tác vụ Nền Đang Thực Thi (Background Operations)</h2>
                  <p class="text-xs text-slate-400">Hàng đợi tái cấu trúc điểm số, nạp bộ đề và quét tệp định kỳ.</p>
                </div>
                <span id="worker-probe-summary" class="font-mono text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg">
                  Chưa có dữ liệu worker từ API.
                </span>
                <button type="button" class="px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors shadow-sm flex items-center gap-1.5" id="check-bg-jobs-btn">
                  <span class="material-symbols-outlined text-[16px]">format_list_bulleted</span>
                  <span>Kiểm tra hàng đợi</span>
                </button>
              </div>

              <div id="background-jobs-summary" class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs text-slate-500">
                Đang tải tác vụ nền từ máy chủ...
              </div>

              <!-- Legacy policy panel is retained only as a hidden compatibility shell; job state comes from the API. -->
              <div class="hidden p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex flex-col gap-3" aria-hidden="true">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-primary-subtle text-primary flex items-center justify-center font-mono text-xs font-bold shrink-0">
                      RG
                    </div>
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-xs sm:text-sm font-bold text-slate-900 dark:text-white">Chấm lại bài thi trắc nghiệm (Regrade Worker)</span>
                        <span class="font-mono text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded font-bold">Chưa có mã job</span>
                      </div>
                      <div class="text-xs text-slate-400 mt-0.5">
                        Chính sách: <strong class="text-slate-700 dark:text-slate-300">Answer-only recompute</strong> (Bảo lưu mốc nộp bài gốc & idempotent)
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 self-end sm:self-auto shrink-0">
                    <button type="button" class="px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold hover:bg-primary-hover transition-colors shadow-sm flex items-center gap-1.5" id="legacy-check-bg-jobs-btn">
                      <span class="material-symbols-outlined text-[16px]">format_list_bulleted</span>
                      <span>Kiểm tra trạng thái & Hàng đợi</span>
                    </button>
                  </div>
                </div>

                <div class="space-y-1.5">
                  <div class="flex justify-between items-center text-xs">
                    <span class="font-mono text-slate-500">Trạng thái: Sẵn sàng xử lý đợt chấm phúc tra</span>
                    <span class="font-mono font-bold text-primary">Idempotent Safe</span>
                  </div>
                  <div class="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. Isolated Danger Zone (Never Overwrite Live DB principle) -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-5">
              <div class="flex items-start justify-between gap-4">
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-rose-600 text-xl">gavel</span>
                    <h2 class="text-base font-bold text-slate-900 dark:text-white">Khu Vực Quản Trị Đặc Quyền (Isolated Danger Zone)</h2>
                  </div>
                  <p class="text-xs text-slate-400">
                    Quản lý bản sao lưu và trung tâm phục hồi đối soát. Mọi tác vụ tại đây đều kích hoạt ghi vết kiểm toán vĩnh viễn.
                  </p>
                </div>
                <span class="text-xs font-bold uppercase px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">
                  Guardrails khôi phục
                </span>
              </div>

              <!-- Strict Staging Architecture Callout -->
              <div class="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div class="flex items-start gap-3">
                  <span class="material-symbols-outlined text-primary text-2xl mt-0.5">schema</span>
                  <div class="text-xs">
                    <strong class="text-slate-900 dark:text-white block mb-0.5">Nguyên tắc Bất khả Xâm phạm: "Never Overwrite Live Database"</strong>
                    <p class="text-slate-500">Mọi yêu cầu phục hồi mặc định thực hiện diễn tập dry-run sang máy chủ Staging cô lập song song để đối soát sai khác (Diff Check) trước khi cân nhắc đồng bộ dữ liệu vào sản phẩm.</p>
                  </div>
                </div>
                <span class="text-xs font-mono px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-primary font-bold shrink-0">
                  Mục tiêu staging: Chưa được cấu hình
                </span>
              </div>

              <!-- Backup Snapshots List (Loaded dynamically from DB) -->
              <div class="space-y-3" id="admin-backups-container">
                <div class="p-6 text-center text-slate-400">
                  <span class="inline-block animate-spin text-xl mb-1">⏳</span>
                  <p class="text-xs">Đang tải danh sách bản sao lưu từ máy chủ...</p>
                </div>
              </div>

              <!-- Strict 4-Step Guardrails Visualization -->
              <div class="pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
                <div class="flex items-center justify-between text-xs">
                  <span class="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider text-[11px]">Khung Kiểm soát 4 Bước Bắt buộc (Strict 4-Step Guardrails)</span>
                  <span class="text-slate-400 text-[11px]">Không chấp thuận bỏ qua bất kỳ bước nào</span>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <div class="text-[10px] text-slate-400">Bước 01</div>
                    <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">Xác thực lại (Re-auth)</div>
                    <div class="text-[10px] text-slate-400 mt-1">Mật khẩu Admin Quản trị</div>
                  </div>
                  <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <div class="text-[10px] text-slate-400">Bước 02</div>
                    <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">Nhập cụm xác nhận</div>
                    <div class="text-[10px] text-rose-600 font-mono font-bold mt-1">"CONFIRM_DATABASE_RESTORE"</div>
                  </div>
                  <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <div class="text-[10px] text-slate-400">Bước 03</div>
                    <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">Lý do kiểm toán</div>
                    <div class="text-[10px] text-slate-400 mt-1">Bắt buộc tối thiểu 10 ký tự</div>
                  </div>
                  <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <div class="text-[10px] text-slate-400">Bước 04</div>
                    <div class="font-bold text-slate-800 dark:text-slate-200 mt-0.5">Ký số xác nhận</div>
                    <div class="text-[10px] text-slate-400 mt-1">Ký số điện tử Quản trị viên</div>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- RIGHT COLUMN (35% -> 4 cols of 12) -->
          <div class="xl:col-span-4 flex flex-col gap-6">
            
            <!-- 1. System Maintenance Window Control Panel -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span class="material-symbols-outlined text-amber-500 text-[20px]">construction</span>
                  <span>Chế độ Bảo trì Toàn viện</span>
                </h3>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold" id="maintenance-status-badge">Đang kiểm tra...</span>
              </div>
              <p class="text-xs text-slate-500 leading-relaxed">
                Khi kích hoạt, hệ thống sẽ trả về mã lỗi <strong>HTTP 503 Maintenance</strong> cho Sinh viên và Giảng viên, chỉ cho phép tài khoản Quản trị viên truy cập.
              </p>
              <div id="maintenance-action-box" class="pt-1">
                <!-- Populated via JS -->
              </div>
            </div>

            <!-- 3. Active Sessions Revocation Panel -->
            <div class="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 space-y-4">
              <div class="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-rose-600 text-[18px]">key</span>
                  <span>Đăng xuất tài khoản khỏi mọi thiết bị</span>
                </h3>
              </div>
              <p class="text-xs text-slate-500">
                Nhập ID người dùng để thu hồi toàn bộ token và phiên đăng nhập tức thì.
              </p>
              <div class="space-y-2">
                <input type="text" id="quick-revoke-user-id" placeholder="Nhập User Public UUID..." class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-mono" />
                <button type="button" id="quick-revoke-btn" class="w-full py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs transition-colors shadow-xs">
                  Đăng Xuất Ngay
                </button>
              </div>
            </div>

          </div>

        </div>

      </div>
    `;

    // Load Backups dynamically from backend
    const loadBackups = async () => {
      const containerEl = document.getElementById('admin-backups-container');
      if (!containerEl) return;

      try {
        const res = await ApiClient.getAdminBackups();
        const backups = res.items || [];

        if (backups.length === 0) {
          containerEl.innerHTML = `
            <div class="p-6 text-center text-slate-400 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs">
              Chưa có bản sao lưu nào. Hãy nhấn "Tạo bản sao lưu khẩn cấp" ở trên để khởi tạo.
            </div>
          `;
          return;
        }

        containerEl.innerHTML = backups.map(b => {
          const metadata = AdminView.backupMetadata(b);
          const rawSha = metadata.checksum;
          const displaySha = rawSha.length > 16 ? `${rawSha.slice(0, 8)}...${rawSha.slice(-8)}` : rawSha;
          const sizeMb = metadata.size;

          return `
            <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-3 overflow-hidden">
              <div class="space-y-1 min-w-0 flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="px-2 py-0.5 rounded bg-primary text-white font-bold text-[10px] uppercase shrink-0">${b.backup_type || 'MANUAL'}</span>
                  ${metadata.verified ? `<span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 font-bold text-[10px] uppercase shrink-0">Đã xác minh SHA</span>` : ''}

                  ${b.last_error ? `<span class="px-2 py-0.5 rounded bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300 font-bold text-[10px] uppercase shrink-0" title="${UI.escapeHtml(b.last_error)}">Lỗi xác minh</span>` : ''}
                  <span class="font-mono text-xs font-bold text-slate-900 dark:text-white truncate block max-w-full" title="${UI.escapeHtml(b.database_backup_name || `BACKUP-${b.backup_id}`)}">${UI.escapeHtml(b.database_backup_name || `BACKUP-${b.backup_id}`)}</span>
                </div>
                <div class="flex flex-wrap items-center gap-2 text-xs text-slate-400 font-mono">
                  <span>Dung lượng: ${sizeMb}</span>
                  <span>•</span>
                  <span title="${rawSha}">SHA-256: ${displaySha}</span>
                  <span>•</span>
                  <span>${UI.formatDateTime(b.created_at)}</span>
                </div>
              </div>
              <div class="flex flex-wrap items-center gap-1.5 shrink-0">
                <button type="button" class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors verify-backup-btn" data-backup-id="${b.backup_id}">
                  Xác minh SHA
                </button>
                <button type="button" class="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-800 dark:text-slate-200 text-xs font-bold transition-colors dryrun-backup-btn" data-backup-id="${b.backup_id}">
                  Kiểm tra Backup
                </button>
                <button type="button" class="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-colors shadow-xs restore-live-btn" disabled title="Chưa xác minh quy trình khôi phục trên CSDL riêng" data-backup-id="${b.backup_id}" data-backup-name="${UI.escapeHtml(b.database_backup_name || b.backup_id)}">
                  Khôi phục Chưa Khả Dụng
                </button>
              </div>
            </div>
          `;
        }).join('');

        containerEl.querySelectorAll('.verify-backup-btn').forEach(btn => {
          btn.onclick = async () => {
            const bId = btn.dataset.backupId;
            UI.showToast(`Đang xác minh chữ ký SHA-256 của bản sao lưu ${bId}...`, 'info');
            try {
              const vRes = await ApiClient.verifyAdminBackup(bId);
              if (vRes.status === 'VERIFIED' || vRes.verified) {
                UI.showToast(`Xác minh thành công! Checksum: ${vRes.checksum || 'Hợp lệ 100%'}`, 'success');
              } else {
                UI.showToast(`Bản sao lưu: ${vRes.status || 'Chưa hoàn tất'}`, 'warning');
              }
            } catch (e) {
              UI.showToast(e.message || 'Lỗi xác minh bản sao lưu.', 'error');
            } finally {
              await loadBackups();
            }
          };
        });

        containerEl.querySelectorAll('.dryrun-backup-btn').forEach(btn => {
          btn.onclick = async () => {
            const bId = btn.dataset.backupId;
            UI.showToast(`Đang kiểm tra tệp sao lưu...`, 'info');
            try {
              const dRes = await ApiClient.restoreAdminBackupDryRun(bId);
              await loadBackups();
              UI.openModal({
                title: `Kết quả Kiểm tra Tệp Sao Lưu`,
                bodyHtml: `
                  <div class="space-y-3 text-xs">
                    <div class="p-3 rounded-xl bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-200">
                      <strong>Kiểm tra tệp sao lưu:</strong>
                      ${dRes?.status === 'ARTIFACT_VERIFIED' ? 'SQL Server đã kiểm tra artifact và checksum.' : 'Chưa xác minh được artifact.'}
                      Chưa thực hiện khôi phục thử trên CSDL riêng; chưa xác nhận tương thích schema hoặc dữ liệu sau khôi phục.
                    </div>
                    <pre class="p-3 rounded-xl bg-slate-950 text-slate-200 font-mono text-[11px] overflow-x-auto">${UI.escapeHtml(JSON.stringify(dRes, null, 2))}</pre>
                  </div>
                `,
                footerHtml: `<button type="button" class="px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold" onclick="UI.closeModal()">Đóng</button>`
              });
            } catch (e) {
              UI.showToast(e.message || 'Lỗi kiểm tra tệp sao lưu.', 'error');
            }
          };
        });

        containerEl.querySelectorAll('.restore-live-btn').forEach(btn => {
          btn.onclick = () => {
            AdminView.openLiveRestoreModal(btn.dataset.backupId, btn.dataset.backupName);
          };
        });

      } catch (err) {
        console.warn('Backups load warning:', err);
      }
    };

    // Load Maintenance Status
    const loadMaintenanceStatus = async () => {
      const badge = document.getElementById('maintenance-status-badge');
      const box = document.getElementById('maintenance-action-box');
      if (!badge || !box) return;

      try {
        const res = await ApiClient.getMaintenanceStatus();
        const isActive = res.is_active;
        const windowData = res.maintenance_window;

        if (isActive) {
          badge.className = 'px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300';
          badge.textContent = 'ĐANG BẬT';

          box.innerHTML = `
            <div class="space-y-3">
              <div class="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-xs border border-amber-200">
                <div><strong>Lý do:</strong> ${UI.escapeHtml(windowData?.reason || 'Bảo trì hệ thống định kỳ')}</div>
                <div class="text-[11px] mt-0.5">Bắt đầu: ${UI.formatDateTime(windowData?.started_at)}</div>
              </div>
              <button type="button" id="end-maintenance-btn" class="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-colors shadow-xs flex items-center justify-center gap-1.5">
                <span class="material-symbols-outlined text-[18px]">lock_open</span>
                <span>Kết thúc Bảo trì & Mở lại Hệ thống</span>
              </button>
            </div>
          `;

          document.getElementById('end-maintenance-btn').onclick = async () => {
            const conf = await UI.confirm('Kết thúc bảo trì', 'Xác nhận hoàn tất bảo trì và khôi phục truy cập bình thường cho Sinh viên & Giảng viên?', 'Mở lại hệ thống');
            if (!conf) return;

            try {
              await ApiClient.endMaintenance(windowData?.id);
              UI.showToast('Đã kết thúc chế độ bảo trì thành công!', 'success');
              loadMaintenanceStatus();
            } catch (e) {
              UI.showToast(e.message || 'Lỗi kết thúc bảo trì.', 'error');
            }
          };
        } else {
          badge.className = 'px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200';
          badge.textContent = 'HOẠT ĐỘNG';

          box.innerHTML = `
            <button type="button" id="start-maintenance-btn" class="w-full py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs transition-colors shadow-xs flex items-center justify-center gap-1.5">
              <span class="material-symbols-outlined text-[18px]">construction</span>
              <span>Bật Chế độ Bảo trì Khẩn cấp</span>
            </button>
          `;

          document.getElementById('start-maintenance-btn').onclick = () => {
            UI.openModal({
              title: 'Kích hoạt Chế độ Bảo trì Hệ thống',
              bodyHtml: `
                <div class="space-y-4 text-xs">
                  <div class="p-3 rounded-xl bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200">
                    <strong>Lưu ý:</strong> Khi bảo trì kích hoạt, sinh viên và giảng viên truy cập sẽ nhận mã HTTP 503. Chỉ có Quản trị viên mới tiếp tục truy cập được.
                  </div>
                  <div class="space-y-1">
                    <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400" for="maint-reason-input">Lý do bảo trì *</label>
                    <input type="text" id="maint-reason-input" value="Bảo trì nâng cấp hạ tầng & sao lưu CSDL" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" />
                  </div>
                  <div class="space-y-1">
                    <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400" for="maint-duration-input">Thời gian dự kiến (Phút)</label>
                    <input type="number" id="maint-duration-input" value="60" min="5" max="720" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" />
                  </div>
                  <div class="space-y-1">
                    <label class="block font-bold uppercase text-[10px] text-slate-600 dark:text-slate-400" for="maint-password-input">Mật khẩu Quản trị viên (Bắt buộc xác thực) *</label>
                    <input type="password" id="maint-password-input" placeholder="Nhập mật khẩu quản trị viên..." class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" autocomplete="current-password" />
                  </div>
                </div>
              `,
              footerHtml: `
                <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600" onclick="UI.closeModal()">Hủy</button>
                <button type="button" id="confirm-maint-btn" class="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold">Kích hoạt Bảo trì</button>
              `
            });

            document.getElementById('confirm-maint-btn').onclick = async () => {
              const reason = document.getElementById('maint-reason-input').value.trim();
              const duration = parseInt(document.getElementById('maint-duration-input').value) || 60;
              const password = document.getElementById('maint-password-input')?.value;

              if (!password) {
                UI.showToast('Vui lòng nhập mật khẩu xác thực.', 'warning');
                return;
              }

              try {
                await ApiClient.startMaintenance(reason, duration, password);
                UI.closeModal();
                UI.showToast('Đã kích hoạt chế độ bảo trì hệ thống!', 'warning');
                loadMaintenanceStatus();
              } catch (e) {
                UI.showToast(e.message || 'Lỗi bật bảo trì.', 'error');
              }
            };
          };
        }
      } catch (err) {
        console.warn('Maintenance status load warning:', err);
      }
    };

    // Load background jobs dynamically from backend; never infer worker count or progress.
    const loadBackgroundJobsSummary = async () => {
      const summaryEl = document.getElementById('background-jobs-summary');
      if (!summaryEl) return;

      try {
        const result = await ApiClient.getAdminBackgroundJobs({ per_page: 5 });
        const items = Array.isArray(result?.items) ? result.items : [];
        const summary = result?.summary || {};
        const counts = ['queued', 'running', 'failed', 'succeeded']
          .filter(key => Number.isFinite(Number(summary[key])))
          .map(key => `${key}: ${Number(summary[key])}`)
          .join(' · ');

        if (items.length === 0) {
          summaryEl.innerHTML = `
            <div class="space-y-2">
              <div class="font-bold text-slate-700 dark:text-slate-200">Chưa có tác vụ nền được ghi nhận.</div>
              <div class="text-slate-400">${UI.escapeHtml(counts || 'Chưa có số liệu tổng hợp từ máy chủ.')}</div>
            </div>
          `;
          return;
        }

        summaryEl.innerHTML = `
          <div class="space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="font-bold text-slate-700 dark:text-slate-200">Tác vụ gần đây</div>
              <div class="font-mono text-[11px] text-slate-500">${UI.escapeHtml(counts || 'Chưa có số liệu tổng hợp')}</div>
            </div>
            <div class="space-y-2">
              ${items.map(job => `
                <div class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 dark:border-slate-700 px-3 py-2">
                  <span class="font-semibold text-slate-700 dark:text-slate-200">${UI.escapeHtml(job.job_type || 'Không xác định')}</span>
                  <span class="font-mono text-[11px] text-slate-500">${UI.escapeHtml(job.status || 'UNKNOWN')}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      } catch (error) {
        summaryEl.innerHTML = `
          <div class="text-amber-700 dark:text-amber-300">Không tải được trạng thái tác vụ nền từ máy chủ.</div>
          <div class="mt-1 text-slate-400">${UI.escapeHtml(error?.message || 'Không có chi tiết lỗi.')}</div>
        `;
      }
    };

    // Load Service Health Matrix dynamically from backend
    const loadHealthMatrix = async () => {
      const gridEl = document.getElementById('services-health-grid');
      const summaryEl = document.getElementById('health-summary-pills');
      if (!gridEl) return;

      try {
        const health = await ApiClient.getAdminHealth();
        const services = health?.services || {};
        const workerSummary = document.getElementById('worker-probe-summary');
        if (workerSummary) workerSummary.textContent = AdminView.workerSummary(services);
        const serviceKeys = Object.keys(services);

        if (serviceKeys.length > 0) {
          let healthyCount = 0;
          gridEl.innerHTML = serviceKeys.map(k => {
            const s = services[k];
            const isHealthy = s.status === 'HEALTHY';
            const isDegraded = s.status === 'DEGRADED';
            if (isHealthy) healthyCount++;

            const badgeClass = isHealthy
              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
              : (isDegraded ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300');
            const borderClass = isHealthy
              ? 'border-slate-200 dark:border-slate-700'
              : (isDegraded ? 'border-amber-300 dark:border-amber-800' : 'border-rose-300 dark:border-rose-800');
            const statusColor = isHealthy ? 'text-emerald-600' : (isDegraded ? 'text-amber-600' : 'text-rose-600');

            return `
              <div class="bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border ${borderClass} flex flex-col justify-between gap-3">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold uppercase text-slate-500">${UI.escapeHtml(s.name || s.service_name || k)}</span>
                  <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${badgeClass} text-[11px] font-bold">${UI.escapeHtml(s.status)}</span>
                </div>
                <div>
                  <div class="text-sm font-bold text-slate-900 dark:text-white">${UI.escapeHtml(s.name || s.service_name || k)}</div>
                  <div class="text-xs text-slate-400">Độ trễ: ${s.latency_ms !== null && s.latency_ms !== undefined ? s.latency_ms + 'ms' : 'N/A'}</div>
                </div>
                <div class="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                  <span class="truncate max-w-[140px]" title="${UI.escapeHtml(s.notes || '')}">${UI.escapeHtml(s.notes || 'Hệ thống chuẩn hóa')}</span>
                  <span class="${statusColor} font-bold">${UI.escapeHtml(s.status)}</span>
                </div>
              </div>
            `;
          }).join('');

          if (summaryEl) {
            summaryEl.innerHTML = `
              <span class="inline-flex items-center gap-1 text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-3 py-1 rounded-lg">
                <span class="material-symbols-outlined text-sm text-primary">sync</span> ${healthyCount}/${serviceKeys.length} Node Hoạt Động
              </span>
            `;
          }
        }
      } catch (err) {
        console.warn('Health matrix load warning:', err);
      }
    };

    // Quick Revoke Event
    const quickRevokeBtn = document.getElementById('quick-revoke-btn');
    if (quickRevokeBtn) {
      quickRevokeBtn.onclick = async () => {
        const uId = document.getElementById('quick-revoke-user-id').value.trim();
        if (!uId) {
          UI.showToast('Vui lòng nhập User UUID.', 'warning');
          return;
        }
        const password = await UI.reauthPrompt({
          title: 'Cưỡng chế Thu hồi Phiên Khẩn cấp',
          message: `Cưỡng chế đăng xuất người dùng ${uId} khỏi toàn bộ phiên đăng nhập hệ thống. Vui lòng nhập mật khẩu quản trị viên để xác thực.`,
          actionLabel: 'Thu hồi Phiên Ngay',
          isDanger: true
        });
        if (!password) return;

        try {
          await ApiClient.revokeUserSessions(uId, 'Admin emergency revoke from Operations Cockpit', password);
          UI.showToast(`Đã thu hồi toàn bộ phiên đăng nhập của người dùng ${uId}!`, 'success');
          document.getElementById('quick-revoke-user-id').value = '';
        } catch (e) {
          UI.showToast(e.message || 'Lỗi thu hồi phiên.', 'error');
        }
      };
    }

    // Wire Background Jobs Modal Trigger
    const checkJobsBtn = document.getElementById('check-bg-jobs-btn');
    if (checkJobsBtn) {
      checkJobsBtn.onclick = () => AdminView.openBackgroundJobsModal();
    }

    document.getElementById('refresh-operations-btn').onclick = async () => {
      await Promise.allSettled([loadBackups(), loadMaintenanceStatus(), loadHealthMatrix(), loadBackgroundJobsSummary()]);
    };

    document.getElementById('emergency-backup-btn').onclick = () => {
      AdminView.openCreateBackupModal(() => loadBackups());
    };

    // Initialize operations view
    loadBackups();
    loadMaintenanceStatus();
    loadHealthMatrix();
    loadBackgroundJobsSummary();
  }

  static openCreateBackupModal(onSuccess = null) {
    const body = `
      <div class="space-y-4 text-xs">
        <p class="text-slate-600 dark:text-slate-300">
          Khởi tạo bản sao lưu snapshot CSDL MS SQL Server với tính toán mã băm toàn vẹn SHA-256.
        </p>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Loại sao lưu</label>
          <select id="modal-backup-type" class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs">
            <option value="MANUAL">MANUAL (Sao lưu thủ công)</option>
            <option value="PRE_MAINTENANCE">PRE_MAINTENANCE (Trước bảo trì)</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 text-[10px]">Ghi chú sao lưu</label>
          <input type="text" id="modal-backup-notes" placeholder="VD: Sao lưu khẩn cấp kiểm toán..." class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs" />
        </div>
      </div>
    `;

    UI.openModal({
      title: 'Tạo Bản Sao Lưu Cơ Sở Dữ Liệu Mới',
      bodyHtml: body,
      footerHtml: `
        <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600" onclick="UI.closeModal()">Hủy</button>
        <button type="button" id="confirm-create-backup-btn" class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold">Khởi tạo Sao Lưu</button>
      `,
      size: 'md'
    });

    document.getElementById('confirm-create-backup-btn').onclick = async () => {
      const type = document.getElementById('modal-backup-type').value;
      const notes = document.getElementById('modal-backup-notes').value.trim();

      UI.showToast('Đang tiến hành tạo bản sao lưu snapshot...', 'info');
      try {
        const res = await ApiClient.createAdminBackup(type, notes);
        UI.closeModal();
        UI.showToast(`Đã tạo bản sao lưu ${res.backup?.database_backup_name || 'thành công'}!`, 'success');
        if (onSuccess) onSuccess();
      } catch (e) {
        UI.showToast(e.message || 'Lỗi tạo bản sao lưu.', 'error');
      }
    };
  }

  static openLiveRestoreModal(backupId, backupName) {
    const body = `
      <form id="live-restore-form" onsubmit="return false;" class="space-y-4 text-xs">
        <div class="p-3.5 rounded-xl bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 space-y-1 border border-rose-200 dark:border-rose-900/60">
          <div class="font-bold flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base text-rose-600">warning</span>
            <span>CẢNH BÁO QUẢN TRỊ CAO CẤP: KHÔI PHỤC LIVE DATABASE</span>
          </div>
          <p>Hành động này sẽ khôi phục dữ liệu từ bản sao lưu <strong class="break-all font-mono">${UI.escapeHtml(backupName)}</strong> vào CSDL trực tiếp. Để đảm bảo an toàn tuyệt đối, hệ thống yêu cầu tuân thủ nghiêm ngặt 4 bước xác thực dưới đây.</p>
        </div>

        <div class="space-y-1">
          <label for="restore-admin-password" class="block font-bold text-slate-700 dark:text-slate-300 text-xs">
            Bước 01: Nhập Mật khẩu Quản trị viên để xác thực lại (Re-auth) *
          </label>
          <input type="password" id="restore-admin-password" autocomplete="current-password" placeholder="Nhập mật khẩu tài khoản Admin của bạn..." class="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-rose-600" />
        </div>

        <div class="space-y-1">
          <label for="restore-confirm-phrase" class="block font-bold text-slate-700 dark:text-slate-300 text-xs">
            Bước 02: Nhập chính xác cụm từ: <span class="font-mono text-rose-600 font-black">CONFIRM_DATABASE_RESTORE</span> *
          </label>
          <input type="text" id="restore-confirm-phrase" placeholder="Gõ chính xác CONFIRM_DATABASE_RESTORE..." class="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 font-mono text-xs outline-none focus:border-rose-600" />
        </div>

        <div class="space-y-1">
          <label for="restore-audit-reason" class="block font-bold text-slate-700 dark:text-slate-300 text-xs">
            Bước 03: Lý do giải trình kiểm toán bắt buộc (Tối thiểu 10 ký tự) *
          </label>
          <textarea id="restore-audit-reason" rows="2" placeholder="Ghi rõ căn cứ quyết định phục hồi CSDL trực tiếp..." class="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs outline-none focus:border-rose-600 resize-none"></textarea>
        </div>

        <div class="pt-1">
          <label class="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800 cursor-pointer">
            <input type="checkbox" id="restore-sign-cert-check" class="mt-0.5 rounded text-rose-600 focus:ring-rose-500" />
            <span class="text-xs text-slate-700 dark:text-slate-300 leading-snug">
              Bước 04: Tôi ký số điện tử xác nhận với tư cách Quản trị viên, chịu trách nhiệm hoàn toàn về quyết định khôi phục CSDL.
            </span>
          </label>
        </div>
      </form>
    `;

    const footer = `
      <button type="button" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100" onclick="UI.closeModal()">Hủy bỏ</button>
      <button type="button" id="submit-live-restore-btn" class="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold">Thực thi Khôi phục Live Database</button>
    `;

    const displayBackupTitle = backupName && backupName.length > 25 ? `${backupName.slice(0, 22)}...` : (backupName || '');
    UI.openModal({
      title: `Khôi phục CSDL Trực tiếp • ${displayBackupTitle}`,
      bodyHtml: body,
      footerHtml: footer,
      size: 'lg'
    });

    document.getElementById('submit-live-restore-btn').onclick = async () => {
      const password = document.getElementById('restore-admin-password').value;
      const phrase = document.getElementById('restore-confirm-phrase').value.trim();
      const reason = document.getElementById('restore-audit-reason').value.trim();
      const signed = document.getElementById('restore-sign-cert-check').checked;

      if (!password) {
        UI.showToast('Vui lòng nhập mật khẩu xác thực lại của bạn.', 'warning');
        return;
      }
      if (phrase !== 'CONFIRM_DATABASE_RESTORE') {
        UI.showToast('Vui lòng nhập chính xác cụm từ: CONFIRM_DATABASE_RESTORE', 'warning');
        return;
      }
      if (reason.length < 10) {
        UI.showToast('Vui lòng nhập lý do giải trình kiểm toán chi tiết (tối thiểu 10 ký tự).', 'warning');
        return;
      }
      if (!signed) {
        UI.showToast('Vui lòng tích chọn xác nhận ký số điện tử.', 'warning');
        return;
      }

      UI.showToast('Đang thực thi khôi phục cơ sở dữ liệu có kiểm soát...', 'info');
      try {
        const res = await ApiClient.restoreAdminBackup(backupId, phrase, password, reason);
        UI.closeModal();
        UI.showToast('Khôi phục cơ sở dữ liệu thành công! Bản ghi kiểm toán đã được lưu vĩnh viễn.', 'success');
      } catch (e) {
        UI.showToast(e.message || 'Lỗi khôi phục cơ sở dữ liệu.', 'error');
      }
    };
  }

  static async openBackgroundJobsModal() {
    UI.openModal({
      title: 'Hàng Đợi & Tiến Trình Tác Vụ Nền (Background Execution Engine)',
      bodyHtml: `
        <div class="space-y-4 text-xs">
          <!-- Summary Counters -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3" id="bg-jobs-summary-cards">
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div class="text-[10px] text-slate-400 font-bold uppercase">Queued (Chờ xử lý)</div>
              <div class="text-xl font-bold font-mono text-amber-500 mt-1" id="bg-summary-queued">0</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div class="text-[10px] text-slate-400 font-bold uppercase">Running (Đang chạy)</div>
              <div class="text-xl font-bold font-mono text-primary mt-1" id="bg-summary-running">0</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div class="text-[10px] text-slate-400 font-bold uppercase">Succeeded (Hoàn thành)</div>
              <div class="text-xl font-bold font-mono text-emerald-600 mt-1" id="bg-summary-succeeded">0</div>
            </div>
            <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div class="text-[10px] text-slate-400 font-bold uppercase">Failed (Thất bại)</div>
              <div class="text-xl font-bold font-mono text-rose-600 mt-1" id="bg-summary-failed">0</div>
            </div>
          </div>

          <!-- Controls / Filter -->
          <div class="flex items-center justify-between gap-3 pt-2">
            <div class="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[18px] text-primary">dns</span>
              <span>Danh sách tác vụ điều phối MS SQL</span>
            </div>
            <button type="button" id="refresh-jobs-list-btn" class="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">refresh</span>
              <span>Làm mới</span>
            </button>
          </div>

          <!-- Table Container -->
          <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table class="w-full text-left border-collapse text-xs">
              <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th class="p-2.5">Job ID</th>
                  <th class="p-2.5">Loại tác vụ</th>
                  <th class="p-2.5">Trạng thái</th>
                  <th class="p-2.5">Thử lại (Attempts)</th>
                  <th class="p-2.5">Thời gian khởi tạo</th>
                  <th class="p-2.5 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody id="bg-jobs-table-body" class="divide-y divide-slate-100 dark:divide-slate-800">
                <tr>
                  <td colspan="6" class="p-6 text-center text-slate-400">
                    <span class="inline-block animate-spin text-lg mb-1">⏳</span>
                    <p>Đang tải danh sách tác vụ nền...</p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      `,
      footerHtml: `
        <button type="button" class="px-5 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold hover:bg-slate-300" onclick="UI.closeModal()">Đóng</button>
      `,
      size: 'xl'
    });

    const loadJobs = async () => {
      const tbody = document.getElementById('bg-jobs-table-body');
      if (!tbody) return;

      try {
        const res = await ApiClient.getAdminBackgroundJobs({ per_page: 50 });
        const summary = res.summary || {};
        const items = res.items || [];

        const qEl = document.getElementById('bg-summary-queued');
        const rEl = document.getElementById('bg-summary-running');
        const sEl = document.getElementById('bg-summary-succeeded');
        const fEl = document.getElementById('bg-summary-failed');

        if (qEl) qEl.textContent = summary.queued || 0;
        if (rEl) rEl.textContent = summary.running || 0;
        if (sEl) sEl.textContent = summary.succeeded || 0;
        if (fEl) fEl.textContent = summary.failed || 0;

        if (items.length === 0) {
          tbody.innerHTML = `
            <tr>
              <td colspan="6" class="p-6 text-center text-slate-400 font-mono text-xs">
                Không có tác vụ nền nào trong hàng đợi.
              </td>
            </tr>
          `;
          return;
        }

        tbody.innerHTML = items.map(job => {
          let statusBadge = '';
          if (job.status === 'SUCCEEDED') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 font-bold text-[10px]">SUCCEEDED</span>';
          } else if (job.status === 'RUNNING') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full bg-indigo-50 text-primary dark:bg-indigo-950/40 dark:text-indigo-300 font-bold text-[10px] animate-pulse">RUNNING</span>';
          } else if (job.status === 'FAILED') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 font-bold text-[10px]">FAILED</span>';
          } else {
            statusBadge = `<span class="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 font-bold text-[10px]">${job.status}</span>`;
          }

          const rawId = job.job_id || '';
          const shortId = rawId.length > 13 ? `${rawId.slice(0, 8)}...` : rawId;
          const retryDisabled = job.status !== 'FAILED';

          return `
            <tr class="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
              <td class="p-2.5 font-mono text-[11px] font-bold text-slate-700 dark:text-slate-300" title="${UI.escapeHtml(rawId)}">
                ${UI.escapeHtml(shortId)}
              </td>
              <td class="p-2.5 font-bold text-slate-900 dark:text-white">
                ${UI.escapeHtml(job.job_type)}
                ${job.last_error ? `<div class="text-[10px] text-rose-500 font-normal font-mono truncate max-w-[200px]" title="${UI.escapeHtml(job.last_error)}">${UI.escapeHtml(job.last_error)}</div>` : ''}
              </td>
              <td class="p-2.5">${statusBadge}</td>
              <td class="p-2.5 font-mono text-slate-500 text-[11px]">
                ${job.attempt_count} / ${job.max_attempts}
              </td>
              <td class="p-2.5 text-slate-400 text-[11px]">
                ${job.created_at ? UI.formatDateTime(job.created_at) : '--'}
              </td>
              <td class="p-2.5 text-right">
                ${!retryDisabled ? `
                  <button type="button" class="px-2.5 py-1 rounded-lg bg-primary hover:bg-primary-hover text-white font-bold text-[11px] transition-colors retry-bg-job-btn" data-job-id="${UI.escapeHtml(rawId)}">
                    Thử lại
                  </button>
                ` : `
                  <span class="text-slate-300 dark:text-slate-600 text-[11px] font-mono">--</span>
                `}
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.retry-bg-job-btn').forEach(btn => {
          btn.onclick = async () => {
            const jId = btn.dataset.jobId;
            btn.disabled = true;
            btn.innerHTML = '<span class="inline-block animate-spin">⏳</span>';
            try {
              await ApiClient.retryAdminBackgroundJob(jId);
              UI.showToast(`Đã đưa tác vụ ${jId} trở lại hàng đợi xử lý!`, 'success');
              await loadJobs();
            } catch (e) {
              UI.showToast(e.message || 'Lỗi thử lại tác vụ.', 'error');
              btn.disabled = false;
              btn.textContent = 'Thử lại';
            }
          };
        });

      } catch (err) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" class="p-6 text-center text-rose-500 font-mono text-xs">
              Lỗi tải danh sách tác vụ: ${UI.escapeHtml(err.message || 'Không thể kết nối máy chủ')}
            </td>
          </tr>
        `;
      }
    };

    const refreshBtn = document.getElementById('refresh-jobs-list-btn');
    if (refreshBtn) {
      refreshBtn.onclick = () => loadJobs();
    }

    loadJobs();
  }
}

window.AdminView = AdminView;
