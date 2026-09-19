/**
 * PWD301 LMS - API Client Layer
 * Unified REST API and Session-Authenticated Client across all roles.
 * Provides CSRF protection, error normalization, retry handlers, and role-based methods.
 */

class ApiClient {
  static _cachedCsrf = null;

  static getCsrfToken() {
    // 1. In-memory cached token
    if (ApiClient._cachedCsrf) return ApiClient._cachedCsrf;

    // 2. Meta tag
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;

    // 3. Cookie
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
      c = c.trim();
      if (c.startsWith('csrf_token=') || c.startsWith('pwd301_csrf=')) {
        return decodeURIComponent(c.substring(c.indexOf('=') + 1));
      }
    }
    return '';
  }

  static async ensureCsrfToken(forceRefresh = false) {
    let token = forceRefresh ? '' : ApiClient.getCsrfToken();
    if (!token || forceRefresh) {
      try {
        const res = await fetch('/auth/login', {
          credentials: 'same-origin',
          headers: { 'Accept': 'application/json' }
        });
        const data = await res.json();
        if (data && data.csrf_token) {
          token = data.csrf_token;
          ApiClient._cachedCsrf = token;
          const metaTag = document.querySelector('meta[name="csrf-token"]');
          if (metaTag) metaTag.setAttribute('content', token);
        }
      } catch (e) {
        console.warn('Could not fetch csrf token:', e);
      }
    }
    return token || ApiClient._cachedCsrf || '';
  }

  static async request(url, options = {}) {
    const defaultHeaders = {
      'Accept': 'application/json',
    };

    let processedBody = options.body;
    if (processedBody && !(processedBody instanceof FormData)) {
      if (typeof processedBody === 'object') {
        processedBody = JSON.stringify(processedBody);
      }
      defaultHeaders['Content-Type'] = 'application/json';
    }

    const method = (options.method || 'GET').toUpperCase();
    const isStateChanging = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);
    if (isStateChanging) {
      const csrfToken = await ApiClient.ensureCsrfToken();
      if (csrfToken) {
        defaultHeaders['X-CSRFToken'] = csrfToken;
      }
    }

    const finalOptions = {
      credentials: 'same-origin',
      ...options,
      body: processedBody,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    };

    try {
      const res = await fetch(url, finalOptions);
      const contentType = res.headers.get('content-type') || '';
      const isJson = contentType.includes('application/json');
      const data = isJson ? await res.json() : await res.text();

      if (!res.ok) {
        // Automatic single-retry on CSRF error / expiration
        if (res.status === 400 && data && data.error && data.error.code === 'CSRF_ERROR' && !options._isCsrfRetry) {
          console.info('[ApiClient] CSRF session token expired. Refreshing and retrying request once...');
          ApiClient._cachedCsrf = null;
          await ApiClient.ensureCsrfToken(true);
          return await ApiClient.request(url, { ...options, _isCsrfRetry: true });
        }

        const errorMsg = (data && data.error && data.error.message) || data.message || `Lỗi HTTP ${res.status}`;
        const err = new Error(errorMsg);
        err.status = res.status;
        err.data = data;
        throw err;
      }

      return data;
    } catch (err) {
      console.warn(`[ApiClient] Request to ${url} failed:`, err);
      throw err;
    }
  }

  // =========================================================================
  // 1. Authentication & Session Endpoints
  // =========================================================================
  static async getCurrentUser() {
    try {
      const res = await ApiClient.request('/auth/login', { method: 'GET' });
      if (res && res.csrf_token) {
        ApiClient._cachedCsrf = res.csrf_token;
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) metaTag.setAttribute('content', res.csrf_token);
      }
      if (res && res.status === 'authenticated') {
        return res.user;
      }
      return null;
    } catch {
      return null;
    }
  }

  static async login(email, password, remember = false) {
    const res = await ApiClient.request('/auth/login', {
      method: 'POST',
      body: { email, password, remember },
    });
    if (res && res.csrf_token) {
      ApiClient._cachedCsrf = res.csrf_token;
    }
    return res;
  }

  static async register(name, email, password) {
    return await ApiClient.request('/auth/register', {
      method: 'POST',
      body: { name, email, password },
    });
  }

  static async logout() {
    try {
      await ApiClient.request('/auth/logout', { method: 'POST' });
    } catch (e) {
      console.warn('Logout warning:', e);
    }
    ApiClient._cachedCsrf = null;
    document.cookie = 'csrf_token=; Max-Age=0; path=/;';
    document.cookie = 'pwd301_csrf=; Max-Age=0; path=/;';
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) metaTag.removeAttribute('content');
    const router = window.app || window.appRouter;
    if (router) {
      router.currentUser = null;
      router.currentRole = null;
      router.toggleShell(false);
    }
    window.location.hash = '#/auth';
  }

  static async switchRole(targetRole) {
    return await ApiClient.request('/auth/switch-role', {
      method: 'POST',
      body: { role: targetRole },
    });
  }

  // =========================================================================
  // 2. Student Role Endpoints
  // =========================================================================
  static async getStudentDashboard() {
    return await ApiClient.request('/student/dashboard');
  }

  static async getCatalogCourses(params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/api/courses?${query}` : '/api/courses';
    return await ApiClient.request(url);
  }

  static async getCourseDetail(courseId) {
    const isInstructorRoute = window.location.hash.startsWith('#/instructor');
    if (isInstructorRoute) {
      try {
        return await ApiClient.request(`/instructor/courses/${courseId}`);
      } catch {
        // Fall back to general endpoint
      }
    }
    try {
      return await ApiClient.request(`/api/courses/${courseId}`);
    } catch (err) {
      try {
        return await ApiClient.request(`/instructor/courses/${courseId}`);
      } catch {
        throw err;
      }
    }
  }

  static async getInstructorCourseDetail(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}`);
  }

  static async getStudentCourseDetail(courseId) {
    return await ApiClient.request(`/student/courses/${courseId}`);
  }

  static async enrollCourse(courseId) {
    return await ApiClient.request(`/student/courses/${courseId}/enroll`, {
      method: 'POST',
    });
  }

  static async getStudentEnrollments() {
    return await ApiClient.request('/student/my-learning');
  }

  static async getStudentCourseProgress(courseId) {
    return await ApiClient.request(`/student/courses/${courseId}/progress`);
  }

  static async getStudentLesson(courseId, lessonId) {
    return await ApiClient.request(`/student/courses/${courseId}/lessons/${lessonId}`);
  }

  static async recordLessonProgress(lessonId, secondsIncrement = 15, viewFraction = 1.0, completed = false) {
    return await ApiClient.request(`/student/lessons/${lessonId}/progress`, {
      method: 'POST',
      body: {
        seconds_increment: secondsIncrement,
        view_fraction: viewFraction,
        completed: completed
      }
    });
  }

  static async getStudentAssessments() {
    return await ApiClient.request('/student/assessments');
  }

  static async getStudentAssessmentDetail(assessmentId) {
    return await ApiClient.request(`/student/assessments/${assessmentId}`);
  }

  static async startAssessmentAttempt(assessmentId) {
    return await ApiClient.request(`/student/assessments/${assessmentId}/start`, {
      method: 'POST'
    });
  }

  static async getAttemptDelivery(attemptId) {
    return await ApiClient.request(`/student/attempt/${attemptId}`);
  }

  static async saveAttemptAnswer(attemptId, questionId, payload, leaseToken = '') {
    return await ApiClient.request(`/student/attempt/${attemptId}/answers/${questionId}`, {
      method: 'POST',
      headers: leaseToken ? { 'X-Attempt-Lease-Token': leaseToken } : {},
      body: payload
    });
  }

  static async submitAttempt(attemptId, leaseToken = '', idempotencyKey = '') {
    const headers = {};
    if (leaseToken) headers['X-Attempt-Lease-Token'] = leaseToken;
    if (idempotencyKey) headers['X-Submission-Idempotency-Key'] = idempotencyKey;

    return await ApiClient.request(`/student/attempt/${attemptId}/submit`, {
      method: 'POST',
      headers
    });
  }

  static async getAttemptResult(attemptId) {
    return await ApiClient.request(`/student/attempt/${attemptId}/result`);
  }

  static async submitAttemptAppeal(attemptId, payload) {
    return await ApiClient.request(`/student/attempts/${attemptId}/appeal`, {
      method: 'POST',
      body: payload
    });
  }

  static async getAttemptAppeal(attemptId) {
    return await ApiClient.request(`/student/attempts/${attemptId}/appeal`);
  }

  static async reviewAttemptAppeal(attemptId, payload) {
    return await ApiClient.request(`/instructor/attempts/${attemptId}/appeal/review`, {
      method: 'POST',
      body: payload
    });
  }

  static async sendAIChat(message, conversationId = null, courseId = null) {
    const body = { message };
    if (conversationId) body.conversation_id = conversationId;
    if (courseId) body.course_id = courseId;
    return await ApiClient.request('/student/ai/chat', {
      method: 'POST',
      body
    });
  }

  static async getInstructorApplication() {
    return await ApiClient.request('/student/become-instructor');
  }

  static async submitInstructorApplication(payload) {
    return await ApiClient.request('/student/become-instructor', {
      method: 'POST',
      body: payload
    });
  }

  static async cancelInstructorApplication() {
    return await ApiClient.request('/student/become-instructor/cancel', {
      method: 'POST'
    });
  }

  static async getStudentNotifications() {
    return await ApiClient.getNotifications();
  }

  static async markNotificationRead(notificationId) {
    try {
      return await ApiClient.request(`/auth/notifications/${notificationId}/read`, {
        method: 'POST'
      });
    } catch {
      return await ApiClient.request(`/student/notifications/${notificationId}/read`, {
        method: 'POST'
      });
    }
  }

  static async markAllNotificationsRead(category = null) {
    try {
      return await ApiClient.request('/auth/notifications/mark-all-read', {
        method: 'POST',
        body: category ? { category } : {}
      });
    } catch {
      return await ApiClient.request('/student/notifications/mark-all-read', {
        method: 'POST',
        body: category ? { category } : {}
      });
    }
  }

  static async getLessonNotes(lessonId) {
    return await ApiClient.request(`/student/lessons/${lessonId}/notes`);
  }

  static async saveLessonNotes(lessonId, notes) {
    return await ApiClient.request(`/student/lessons/${lessonId}/notes`, {
      method: 'POST',
      body: { notes }
    });
  }

  static async leaveCourse(courseId) {
    return await ApiClient.request(`/student/courses/${courseId}/leave`, {
      method: 'POST'
    });
  }

  static async withdrawCourse(courseId) {
    return await ApiClient.leaveCourse(courseId);
  }

  static async getEnrolledCourses() {
    return await ApiClient.getStudentEnrollments();
  }

  static async getCourses(params = {}) {
    return await ApiClient.getCatalogCourses(params);
  }

  // =========================================================================
  // 3. Instructor Role Endpoints
  // =========================================================================
  static async getInstructorDashboard() {
    return await ApiClient.request('/instructor/dashboard');
  }

  static async getInstructorCourses() {
    return await ApiClient.request('/instructor/courses');
  }

  static async createCourse(data) {
    return await ApiClient.request('/instructor/courses', {
      method: 'POST',
      body: data
    });
  }

  static async getCourseManage(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/manage`);
  }

  static async updateCourse(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}`, {
      method: 'POST',
      body: data
    });
  }

  static async submitCourseForReview(courseId, reason = '') {
    return await ApiClient.request(`/instructor/courses/${courseId}/submit`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async publishCourse(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/publish`, {
      method: 'POST'
    });
  }

  static async trashCourse(courseId, reason = '') {
    return await ApiClient.request(`/instructor/courses/${courseId}/trash`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async createLesson(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}/lessons`, {
      method: 'POST',
      body: data
    });
  }

  static async getLesson(lessonId) {
    return await ApiClient.request(`/instructor/lessons/${lessonId}`);
  }

  static async updateLesson(lessonId, data) {
    return await ApiClient.request(`/instructor/lessons/${lessonId}`, {
      method: 'PATCH',
      body: data
    });
  }

  static async deleteLesson(courseId, lessonId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/lessons/${lessonId}/delete`, {
      method: 'POST'
    });
  }

  static async reorderLessons(courseId, orderedLessonIds) {
    return await ApiClient.request(`/instructor/courses/${courseId}/lessons/reorder`, {
      method: 'POST',
      body: { ordered_lesson_ids: orderedLessonIds }
    });
  }

  static async changeLessonStatus(lessonId, status) {
    return await ApiClient.request(`/instructor/lessons/${lessonId}/status`, {
      method: 'POST',
      body: { status }
    });
  }

  static async attachLessonResource(courseId, lessonId, formData) {
    return await ApiClient.request(`/instructor/courses/${courseId}/lessons/${lessonId}/resources`, {
      method: 'POST',
      body: formData
    });
  }

  static async detachLessonResource(courseId, lessonId, resourceId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/lessons/${lessonId}/resources/${resourceId}`, {
      method: 'DELETE'
    });
  }

  static async deleteLessonResource(courseId, lessonId, resourceId) {
    return await ApiClient.detachLessonResource(courseId, lessonId, resourceId);
  }

  static async listCourseStudents(courseId, page = 1, perPage = 20) {
    return await ApiClient.request(`/instructor/courses/${courseId}/students?page=${page}&per_page=${perPage}`);
  }

  // Prerequisites Management
  static async getCoursePrerequisites(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/prerequisites`);
  }

  static async addCoursePrerequisite(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}/prerequisites`, {
      method: 'POST',
      body: data
    });
  }

  static async deleteCoursePrerequisite(courseId, prereqId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/prerequisites/${prereqId}`, {
      method: 'DELETE'
    });
  }

  static async getInstructorPrerequisiteRequests() {
    return await ApiClient.request('/instructor/prerequisite-requests');
  }

  static async reviewInstructorPrerequisiteRequest(requestId, data) {
    return await ApiClient.request(`/instructor/prerequisite-requests/${requestId}/review`, {
      method: 'POST',
      body: data
    });
  }

  // Completion Rules Management
  static async getCourseCompletionRules(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/completion-rules`);
  }

  static async updateCourseCompletionRules(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}/completion-rules`, {
      method: 'POST',
      body: data
    });
  }

  static async getQuestions(courseId, params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/instructor/courses/${courseId}/questions?${query}` : `/instructor/courses/${courseId}/questions`;
    return await ApiClient.request(url);
  }

  static async getCourseQuestionSummary(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/questions/summary`);
  }

  static async createQuestion(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}/questions`, {
      method: 'POST',
      body: data
    });
  }

  static async getQuestionDetail(questionId) {
    return await ApiClient.request(`/instructor/questions/${questionId}`);
  }

  static async updateQuestion(questionId, data) {
    return await ApiClient.request(`/instructor/questions/${questionId}`, {
      method: 'PATCH',
      body: data
    });
  }

  static async trashQuestion(questionId, reason = '') {
    return await ApiClient.request(`/instructor/questions/${questionId}/trash`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async restoreQuestion(questionId) {
    return await ApiClient.request(`/instructor/questions/${questionId}/restore`, {
      method: 'POST'
    });
  }

  static async getQuestionRevisions(questionId) {
    return await ApiClient.request(`/instructor/questions/${questionId}/revisions`);
  }

  static async createQuestionRevision(questionId, data) {
    return await ApiClient.request(`/instructor/questions/${questionId}/revisions`, {
      method: 'POST',
      body: data
    });
  }

  static async draftQuestionAI(data) {
    return await ApiClient.request('/instructor/ai/questions/draft', {
      method: 'POST',
      body: data
    });
  }

  static async approveQuestionDraft(draftId) {
    return await ApiClient.request(`/instructor/ai/questions/drafts/${draftId}/approve`, {
      method: 'POST'
    });
  }

  static async getCourseAssessments(courseId, params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/instructor/courses/${courseId}/assessments?${query}` : `/instructor/courses/${courseId}/assessments`;
    return await ApiClient.request(url);
  }

  static async createAssessment(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}/assessments`, {
      method: 'POST',
      body: data
    });
  }

  static async getAssessmentDetail(assessmentId) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}`);
  }

  static async updateAssessment(assessmentId, data) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}`, {
      method: 'PATCH',
      body: data
    });
  }

  static async publishAssessment(assessmentId) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/publish`, {
      method: 'POST'
    });
  }


  static async createAssessmentQuestion(assessmentId, data) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/create`, {
      method: 'POST',
      body: data
    });
  }

  static async createAssessmentQuestionsBatch(assessmentId, questions) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/batch`, {
      method: 'POST',
      body: { questions }
    });
  }

  static async batchCreateAssessmentQuestions(assessmentId, questions) {
    return await ApiClient.createAssessmentQuestionsBatch(assessmentId, questions);
  }

  static async getAssessmentAttempts(assessmentId) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/attempts`);
  }

  static async getInstructorAttemptResult(attemptId) {
    return await ApiClient.request(`/instructor/attempts/${attemptId}/results`);
  }

  // =========================================================================
  // 4. Admin Role Endpoints
  // =========================================================================
  static async getAdminGovernance() {
    return await ApiClient.request('/admin/dashboard');
  }

  static async getAdminUsers(params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/admin/users?${query}` : '/admin/users';
    return await ApiClient.request(url);
  }

  static async manageUserRole(userId, action, role, reason = '') {
    return await ApiClient.request(`/admin/users/${userId}/roles`, {
      method: 'POST',
      body: { action, role, reason }
    });
  }

  static async assignRole(userId, role, reason = '') {
    return await ApiClient.manageUserRole(userId, 'assign', role, reason);
  }

  static async removeRole(userId, role, reason = '') {
    return await ApiClient.manageUserRole(userId, 'remove', role, reason);
  }

  static async suspendUser(userId, reason = '') {
    return await ApiClient.request(`/admin/users/${userId}/suspend`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async unsuspendUser(userId, reason = '') {
    return await ApiClient.request(`/admin/users/${userId}/unsuspend`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async revokeUserSessions(userId, reason = '') {
    return await ApiClient.request(`/admin/users/${userId}/revoke-sessions`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async getAdminUserDetail(userId) {
    return await ApiClient.request(`/admin/users/${userId}`);
  }

  static async getAdminCourses() {
    return await ApiClient.request('/admin/courses');
  }

  static async getAdminCourseDetail(courseId) {
    return await ApiClient.request(`/admin/courses/${courseId}`);
  }

  static async getAdminFacultyWorkload() {
    return await ApiClient.request('/admin/faculty/workload');
  }

  static async getPendingCourses() {
    return await ApiClient.request('/admin/courses/pending');
  }

  static async reviewCourse(courseId, action, reason = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/review`, {
      method: 'POST',
      body: { action, reason }
    });
  }

  static async getAdminChangeRequests(status = 'ALL') {
    return await ApiClient.request(`/admin/change-requests?status=${encodeURIComponent(status)}`);
  }

  static async reviewAdminChangeRequest(requestId, data) {
    return await ApiClient.request(`/admin/change-requests/${requestId}/review`, {
      method: 'POST',
      body: data
    });
  }

  static async reassignCourse(courseId, newInstructorId, reason = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/reassign`, {
      method: 'POST',
      body: { new_instructor_id: newInstructorId, reason }
    });
  }

  static async publishCourseAdmin(courseId, reason = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/publish`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async trashCourseAdmin(courseId, reason = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/trash`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async restoreCourseAdmin(courseId, reason = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/restore`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async quarantineOverride(assetId, reason = '') {
    return await ApiClient.request(`/admin/files/${assetId}/quarantine-override`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async broadcastNotification(title, body, targetRole = null, category = 'SYSTEM') {
    return await ApiClient.request('/admin/notifications/broadcast', {
      method: 'POST',
      body: { title, body, target_role: targetRole, category }
    });
  }

  static async retryFailedEmails(maxEmails = 50) {
    return await ApiClient.request('/admin/emails/retry-failed', {
      method: 'POST',
      body: { max_emails: maxEmails }
    });
  }

  static async getAdminAuditLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/admin/audit-logs?${query}` : '/admin/audit-logs';
    return await ApiClient.request(url);
  }

  static async getAdminAuditLogDetail(auditId) {
    return await ApiClient.request(`/admin/audit-logs/${auditId}`);
  }

  static async getAdminBackups() {
    return await ApiClient.request('/admin/backups');
  }

  static async createAdminBackup(backupType = 'MANUAL', notes = '') {
    return await ApiClient.request('/admin/backups', {
      method: 'POST',
      body: { backup_type: backupType, notes }
    });
  }

  static async getAdminBackupDetail(backupId) {
    return await ApiClient.request(`/admin/backups/${backupId}`);
  }

  static async verifyAdminBackup(backupId) {
    return await ApiClient.request(`/admin/backups/${backupId}/verify`, {
      method: 'POST'
    });
  }

  static async restoreAdminBackupDryRun(backupId) {
    return await ApiClient.request(`/admin/backups/${backupId}/restore/dry-run`, {
      method: 'POST'
    });
  }

  static async restoreAdminBackup(backupId, confirmationPhrase, password) {
    return await ApiClient.request(`/admin/backups/${backupId}/restore`, {
      method: 'POST',
      body: {
        confirmation_phrase: confirmationPhrase,
        password: password
      }
    });
  }

  static async getMaintenanceStatus() {
    return await ApiClient.request('/admin/maintenance/status');
  }

  static async startMaintenance(reason = 'Scheduled platform maintenance', durationMinutes = 60) {
    return await ApiClient.request('/admin/maintenance/start', {
      method: 'POST',
      body: {
        reason,
        estimated_duration_minutes: durationMinutes
      }
    });
  }

  static async endMaintenance(windowId = null) {
    return await ApiClient.request('/admin/maintenance/end', {
      method: 'POST',
      body: windowId ? { window_id: windowId } : {}
    });
  }

  static async getAdminBackgroundJobs(params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/admin/operations/jobs?${query}` : '/admin/operations/jobs';
    return await ApiClient.request(url);
  }

  static async retryAdminBackgroundJob(jobId) {
    return await ApiClient.request(`/admin/operations/jobs/${jobId}/retry`, {
      method: 'POST'
    });
  }


  static async getAdminInstructorApplications(status = 'ALL') {
    return await ApiClient.request(`/admin/instructor-applications?status=${status}`);
  }

  static async getAdminInstructorApplicationDetail(appId) {
    return await ApiClient.request(`/admin/instructor-applications/${appId}`);
  }

  static async reviewInstructorApplication(appId, action, reviewReason = '') {
    return await ApiClient.request(`/admin/instructor-applications/${appId}/review`, {
      method: 'POST',
      body: { action, reason: reviewReason, review_reason: reviewReason }
    });
  }

  static async getAdminChangeRequests(status = 'ALL') {
    const query = status && status !== 'ALL' ? `?status=${status}` : '';
    return await ApiClient.request(`/admin/change-requests${query}`);
  }

  static async reviewAdminChangeRequest(requestId, data) {
    return await ApiClient.request(`/admin/change-requests/${requestId}/review`, {
      method: 'POST',
      body: data
    });
  }

  static async getAdminTelemetry() {
    try {
      return await ApiClient.request('/admin/telemetry');
    } catch {
      return await ApiClient.request('/api/admin/telemetry');
    }
  }

  static async getAdminHealth() {
    return await ApiClient.request('/admin/health');
  }

  // =========================================================================
  // 5. Notifications
  // =========================================================================
  static async getNotifications(options = {}) {
    const params = new URLSearchParams();
    if (options.category && options.category !== 'ALL') params.append('category', options.category);
    if (options.unread_only) params.append('unread_only', 'true');
    if (options.page) params.append('page', options.page);
    if (options.per_page) params.append('per_page', options.per_page);
    const qs = params.toString() ? `?${params.toString()}` : '';

    try {
      return await ApiClient.request(`/auth/notifications${qs}`);
    } catch {
      try {
        return await ApiClient.request(`/student/notifications${qs}`);
      } catch {
        try {
          return await ApiClient.request(`/api/notifications${qs}`);
        } catch {
          return { items: [], total: 0, unread_count: 0 };
        }
      }
    }
  }

  static async getUnreadNotificationCount() {
    try {
      const res = await ApiClient.request('/auth/notifications/unread-count');
      if (res && typeof res.unread_count !== 'undefined') return res.unread_count;
    } catch {
      // Fallback
    }
    const list = await ApiClient.getNotifications();
    return list.unread_count ?? (list.items || []).filter(i => !i.is_read && !i.read).length;
  }

  static async parseExamFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    return await ApiClient.request('/instructor/exams/parse-file', {
      method: 'POST',
      body: formData
    });
  }
}

window.ApiClient = ApiClient;
