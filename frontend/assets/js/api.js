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

  static getToken() {
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

  static formatApiErrorMessage(data, status) {
    let rawMsg = '';
    if (typeof data?.error === 'string') {
      rawMsg = data.error;
    } else if (data && data.error && typeof data.error.message === 'string') {
      rawMsg = data.error.message;
    } else if (typeof data?.message === 'string') {
      rawMsg = data.message;
    }
    const code = (data && data.error && typeof data.error === 'object' && data.error.code) || data?.code || '';

    // If message already contains Vietnamese characters, respect it directly
    const hasVietnamese = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(rawMsg);
    if (hasVietnamese && rawMsg.trim()) {
      return rawMsg;
    }

    // Standard Vietnamese dictionary for API error codes
    const CODE_TRANSLATIONS = {
      'UNAUTHORIZED': 'Phiên làm việc đã hết hạn hoặc chưa đăng nhập.',
      'INVALID_CREDENTIALS': 'Email hoặc mật khẩu không chính xác.',
      'FORBIDDEN': 'Bạn không có quyền thực hiện thao tác này.',
      'CSRF_ERROR': 'Phiên bảo mật đã hết hạn. Vui lòng thử lại.',
      'NOT_FOUND': 'Không tìm thấy dữ liệu yêu cầu.',
      'RESOURCE_NOT_FOUND': 'Không tìm thấy tài nguyên yêu cầu.',
      'COURSE_NOT_FOUND': 'Không tìm thấy khóa học.',
      'ASSESSMENT_NOT_FOUND': 'Không tìm thấy bài thi khảo thí.',
      'USER_NOT_FOUND': 'Không tìm thấy thông tin người dùng.',
      'VALIDATION_ERROR': 'Dữ liệu đầu vào không hợp lệ. Vui lòng kiểm tra lại.',
      'BAD_REQUEST': 'Yêu cầu không hợp lệ.',
      'CONFLICT': 'Dữ liệu bị trùng lặp hoặc xung đột trạng thái.',
      'ALREADY_EXISTS': 'Dữ liệu đã tồn tại trong hệ thống.',
      'RATE_LIMIT_EXCEEDED': 'Bạn đã thao tác quá nhanh. Vui lòng thử lại sau giây lát.',
      'INTERNAL_ERROR': 'Lỗi máy chủ nội bộ. Vui lòng thử lại sau.',
      'INTERNAL_SERVER_ERROR': 'Lỗi máy chủ nội bộ. Vui lòng thử lại sau.',
      'FILE_TOO_LARGE': 'Kích thước tệp vượt quá giới hạn cho phép.',
      'INVALID_FILE_TYPE': 'Định dạng tệp không được hỗ trợ.',
      'SCAN_FAILED': 'Quét tệp an toàn thất bại.',
      'ATTEMPT_LOCKED': 'Bài thi đã bị khóa hoặc hết thời gian làm bài.',
      'ACTIVE_LEASE_EXISTS': 'Bài thi đang được mở ở một phiên làm việc khác.'
    };

    // Common backend English phrases to Vietnamese translations (checked before generic code fallback)
    if (rawMsg) {
      const lower = rawMsg.toLowerCase();
      if (lower.includes('admin direct edits to an instructor-owned course require a reason')) {
        return 'Quản trị viên chỉnh sửa khóa học của giảng viên cần cung cấp lý do thay đổi.';
      }
      if (lower.includes('choose a clean image uploaded for this course')) {
        return 'Vui lòng chọn tệp ảnh hợp lệ (PNG, JPEG, WebP) đã được quét an toàn cho khóa học này.';
      }
      if (lower.includes('a valid cover image asset id is required')) {
        return 'Mã tài sản ảnh bìa không hợp lệ. Vui lòng tải lại ảnh.';
      }
      if (lower.includes('course not found') || (lower.includes('course \'') && lower.includes('not found'))) {
        return 'Không tìm thấy khóa học.';
      }
      if (lower.includes('assessment not found')) {
        return 'Không tìm thấy bài thi khảo thí.';
      }
      if (lower.includes('user not found')) {
        return 'Không tìm thấy người dùng.';
      }
      if (lower.includes('invalid credentials') || lower.includes('invalid email or password')) {
        return 'Email hoặc mật khẩu không chính xác.';
      }
      if (lower.includes('unauthorized') || lower.includes('authentication required')) {
        return 'Vui lòng đăng nhập để tiếp tục.';
      }
      if (lower.includes('permission denied') || lower.includes('forbidden')) {
        return 'Bạn không có quyền thực hiện thao tác này.';
      }
    }

    if (code && CODE_TRANSLATIONS[code]) {
      // If code is generic VALIDATION_ERROR but we have a non-empty rawMsg, show rawMsg
      if (code === 'VALIDATION_ERROR' && rawMsg && rawMsg.trim()) {
        return rawMsg.trim();
      }
      return CODE_TRANSLATIONS[code];
    }

    return rawMsg || `Lỗi yêu cầu (HTTP ${status})`;
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

      if (!isJson && typeof data === 'string' && /^\s*<(!doctype|html)/i.test(data)) {
        throw new Error('Máy chủ trả về trang HTML ngoài dự kiến thay vì phản hồi JSON API.');
      }

      if (!res.ok) {
        // Rate Limiting (HTTP 429) friendly handling
        if (res.status === 429) {
          const retryAfter = res.headers.get('retry-after') || (data && data.retry_after) || 60;
          const limitMsg = (data && data.error) ? (typeof data.error === 'string' ? data.error : (data.error.message || 'Thao tác quá nhanh.')) : `Hệ thống ghi nhận quá nhiều yêu cầu. Vui lòng thử lại sau ${retryAfter} giây.`;
          if (typeof UI !== 'undefined' && typeof UI.showToast === 'function') {
            UI.showToast(limitMsg, 'warning');
          }
        }

        // Automatic single-retry on CSRF error / expiration
        if (res.status === 400 && data && data.error && data.error.code === 'CSRF_ERROR' && !options._isCsrfRetry) {
          console.info('[ApiClient] CSRF session token expired. Refreshing and retrying request once...');
          ApiClient._cachedCsrf = null;
          await ApiClient.ensureCsrfToken(true);
          return await ApiClient.request(url, { ...options, _isCsrfRetry: true });
        }

        const errorMsg = ApiClient.formatApiErrorMessage(data, res.status);
        const err = new Error(errorMsg);
        err.rawMessage = (data && data.error && (data.error.message || data.error)) || data?.message || '';
        err.code = (data && data.error && data.error.code) || null;
        err.status = res.status;
        err.data = data;
        throw err;
      }

      if (data && typeof data === 'object' && data.success === false && !options._allowFailure) {
        const errorMsg = ApiClient.formatApiErrorMessage(data, res.status);
        const err = new Error(errorMsg);
        err.rawMessage = (data && data.error && (data.error.message || data.error)) || data?.message || '';
        err.code = (data && data.error && data.error.code) || 'BUSINESS_ERROR';
        err.status = res.status;
        err.data = data;
        throw err;
      }

      if (isStateChanging && typeof SWRCache !== 'undefined') {
        if (url.includes('/courses')) {
          SWRCache.invalidate(/(\/admin\/courses|\/admin\/governance|\/instructor\/courses)/);
        } else if (url.includes('/users') || url.includes('/roles')) {
          SWRCache.invalidate(/(\/admin\/users|\/admin\/governance)/);
        } else if (url.includes('/change-requests')) {
          SWRCache.invalidate(/(\/admin\/change-requests|\/admin\/governance)/);
        } else if (url.includes('/instructor-applications')) {
          SWRCache.invalidate(/(\/admin\/instructor-applications|\/admin\/governance)/);
        } else {
          SWRCache.invalidate();
        }
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
      // DEFECT-AUTH-02: Use dedicated /auth/session endpoint with fallback
      let res = await ApiClient.request('/auth/session', { method: 'GET' }).catch(() => null);
      if (!res || !res.status) {
        res = await ApiClient.request('/auth/login', { method: 'GET' });
      }
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
    let body = { email, password, remember };

    // Hybrid WebCrypto in-transit encryption
    const cryptoHelper = (typeof window !== 'undefined' && window.CryptoHelper)
      ? window.CryptoHelper
      : (typeof CryptoHelper !== 'undefined' ? CryptoHelper : null);

    if (cryptoHelper && typeof cryptoHelper.encryptLoginPayload === 'function') {
      try {
        const envelope = await cryptoHelper.encryptLoginPayload(email, password);
        if (envelope && envelope.prefix === 'PPTQ LMS') {
          console.info('🛡️ [PPTQ LMS In-Transit Encryption] Gói tin đăng nhập đã được mã hóa lai (RSA-OAEP 2048 + AES-GCM 256):', envelope);
          body = {
            encrypted_envelope: envelope,
            remember: Boolean(remember),
          };
        }
      } catch (cryptoErr) {
        console.warn('[ApiClient] Hybrid login encryption unavailable or failed, falling back:', cryptoErr.message || cryptoErr);
        body = { email, password, remember };
      }
    }

    const res = await ApiClient.request('/auth/login', {
      method: 'POST',
      body,
    });
    if (res && res.csrf_token) {
      ApiClient._cachedCsrf = res.csrf_token;
    }
    return res;
  }

  static async register(name, email, password) {
    let body = { name, email, password };

    // Hybrid WebCrypto in-transit encryption
    const cryptoHelper = (typeof window !== 'undefined' && window.CryptoHelper)
      ? window.CryptoHelper
      : (typeof CryptoHelper !== 'undefined' ? CryptoHelper : null);

    if (cryptoHelper && typeof cryptoHelper.encryptRegisterPayload === 'function') {
      try {
        const envelope = await cryptoHelper.encryptRegisterPayload(name, email, password);
        if (envelope && envelope.prefix === 'PPTQ LMS') {
          console.info('🛡️ [PPTQ LMS In-Transit Encryption] Gói tin đăng ký đã được mã hóa lai (RSA-OAEP 2048 + AES-GCM 256):', envelope);
          body = {
            encrypted_envelope: envelope,
          };
        }
      } catch (cryptoErr) {
        console.warn('[ApiClient] Hybrid registration encryption unavailable or failed, falling back:', cryptoErr.message || cryptoErr);
        body = { name, email, password };
      }
    }

    return await ApiClient.request('/auth/register', {
      method: 'POST',
      body,
    });
  }

  static async verifyEmail(token) {
    return await ApiClient.request(`/auth/verify-email/${encodeURIComponent(token)}`, {
      method: 'GET',
    });
  }

  static async resendVerification(email) {
    return await ApiClient.request('/auth/resend-verification', {
      method: 'POST',
      body: { email },
    });
  }

  static async forgotPassword(email, displayName = '') {
    return await ApiClient.request('/auth/forgot-password', {
      method: 'POST',
      body: { email, display_name: displayName },
    });
  }


  static async verifyResetPasswordToken(token) {
    return await ApiClient.request(`/auth/reset-password/${encodeURIComponent(token)}`, {
      method: 'GET',
    });
  }

  static async resetPassword(token, password, confirmPassword) {
    return await ApiClient.request(`/auth/reset-password/${encodeURIComponent(token)}`, {
      method: 'POST',
      body: {
        password,
        confirm_password: confirmPassword,
      },
    });
  }

  static async logout() {
    let serverRevoked = false;
    let serverError = null;
    try {
      await ApiClient.request('/auth/logout', { method: 'POST' });
      serverRevoked = true;
    } catch (e) {
      serverError = e;
      console.warn('Logout server revocation failed:', e);
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
    if (window.UI && typeof window.UI.closeAllModals === 'function') {
      window.UI.closeAllModals();
    }
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
      modalContainer.innerHTML = '';
      modalContainer.classList.add('hidden');
    }
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, '', '#/auth');
    } else {
      window.location.hash = '#/auth';
    }
    if (!serverRevoked && serverError) {
      return { revoked: false, error: serverError };
    }
    return { revoked: true };
  }

  static async switchRole(targetRole) {
    return await ApiClient.request('/auth/switch-role', {
      method: 'POST',
      body: { role: targetRole },
    });
  }

  static async getProfile() {
    return await ApiClient.request('/auth/profile', { method: 'GET' });
  }

  static async updateProfile(data) {
    return await ApiClient.request('/auth/profile', {
      method: 'PUT',
      body: data,
    });
  }

  static async changePassword(currentPassword, newPassword, confirmPassword) {
    return await ApiClient.request('/auth/change-password', {
      method: 'POST',
      body: {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      },
    });
  }

  static async getPreferences() {
    return await ApiClient.request('/auth/preferences', { method: 'GET' });
  }

  static async updatePreferences(data) {
    return await ApiClient.request('/auth/preferences', {
      method: 'PUT',
      body: data,
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

  static async getCourse(courseId) {
    return await ApiClient.getCourseDetail(courseId);
  }

  static async getCourseDetail(courseId) {
    if (!courseId || courseId === 'undefined' || courseId === 'null' || !String(courseId).trim()) {
      throw new Error('Course ID is required');
    }
    const isInstructorRoute = window.location.hash.startsWith('#/instructor');
    if (isInstructorRoute) {
      return await ApiClient.request(`/instructor/courses/${courseId}`);
    }
    const isStudentRoute = window.location.hash.startsWith('#/student');
    if (isStudentRoute) {
      try {
        return await ApiClient.request(`/student/courses/${courseId}`);
      } catch {
        // Fall back to general endpoint
      }
    }
    try {
      return await ApiClient.request(`/api/courses/${courseId}`);
    } catch (err) {
      try {
        return await ApiClient.request(`/student/courses/${courseId}`);
      } catch {
        try {
          return await ApiClient.request(`/instructor/courses/${courseId}`);
        } catch {
          throw err;
        }
      }
    }
  }

  static async getInstructorCourseDetail(courseId) {
    if (!courseId || courseId === 'undefined' || courseId === 'null' || !String(courseId).trim()) {
      throw new Error('Course ID is required');
    }
    return await ApiClient.request(`/instructor/courses/${courseId}`);
  }

  static async getInstructorCourse(courseId) {
    return await ApiClient.getInstructorCourseDetail(courseId);
  }

  static async getStudentCourseDetail(courseId) {
    if (!courseId || courseId === 'undefined' || courseId === 'null' || !String(courseId).trim()) {
      throw new Error('Course ID is required');
    }
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

  static async getStudentCourseCompletion(courseId) {
    return await ApiClient.request(`/student/courses/${encodeURIComponent(courseId)}/completion`);
  }

  static async downloadCertificate(courseId, courseCode = 'PPTQ') {
    if (!courseId) {
      if (typeof UI !== 'undefined') UI.showToast('Mã khóa học không hợp lệ.', 'warning');
      return;
    }

    try {
      // Lightweight preflight completion verification
      try {
        const comp = await ApiClient.request(`/student/courses/${encodeURIComponent(courseId)}/completion`).catch(() => null);
        if (comp && comp.data) {
          const cData = comp.data;
          if (cData.is_completed === false && cData.ever_completed === false) {
            if (typeof UI !== 'undefined') UI.showToast('Học viên chưa hoàn thành đủ bài học và bài thi để được cấp chứng chỉ.', 'warning');
            return;
          }
        }
      } catch (_) {}

      // Native Download Stream: Trigger direct browser download stream via virtual anchor click
      // Eliminates JS heap allocation, memory spikes, and silent iframe HTML trapping
      const cleanCode = String(courseCode || 'PPTQ').replace(/[^a-zA-Z0-9_-]/g, '_');
      const streamUrl = `/student/courses/${encodeURIComponent(courseId)}/certificate`;

      const link = document.createElement('a');
      link.href = streamUrl;
      link.setAttribute('download', `Chung_chi_${cleanCode}.pdf`);
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        if (link.parentNode) {
          link.parentNode.removeChild(link);
        }
      }, 1000);
    } catch (err) {
      console.error('[ApiClient] downloadCertificate error:', err);
      // Fallback: direct window trigger
      window.location.assign(`/student/courses/${encodeURIComponent(courseId)}/certificate`);
    }
  }

  static async getStudentCourseProgress(courseId) {
    return await ApiClient.request(`/student/courses/${courseId}/progress`);
  }

  static async getStudentLesson(courseId, lessonId) {
    return await ApiClient.request(`/student/courses/${courseId}/lessons/${lessonId}`);
  }

  static async startLessonPlayback(lessonId, mediaId) {
    return ApiClient.request(`/student/lessons/${encodeURIComponent(lessonId)}/playback-sessions`, { method: 'POST', body: { media_id: mediaId } });
  }

  static async recordPlaybackHeartbeat(lessonId, heartbeat) {
    return ApiClient.request(`/student/lessons/${encodeURIComponent(lessonId)}/progress`, { method: 'POST', body: heartbeat });
  }

  static async getFileDownloadTicket(assetId, version = null, disposition = 'attachment') {
    return ApiClient.request(`/api/files/${encodeURIComponent(assetId)}/download-ticket`, { method: 'POST', body: { ...(version ? { version } : {}), disposition } });
  }

  static async recordLessonProgress(lessonId, secondsIncrement = 15, viewFraction = 1.0, completed = false, clientEventId = null) {
    const eventId = clientEventId || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : ('ev_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9)));
    return await ApiClient.request(`/student/lessons/${lessonId}/progress`, {
      method: 'POST',
      body: {
        seconds_increment: secondsIncrement,
        view_fraction: viewFraction,
        completed: completed,
        client_event_id: eventId
      }
    });
  }

  static async recordTelemetry(eventType, payload = {}) {
    try {
      return await ApiClient.request('/api/telemetry', {
        method: 'POST',
        body: {
          event_type: eventType,
          payload: payload,
          client_timestamp: new Date().toISOString()
        }
      });
    } catch (err) {
      console.warn('Telemetry delivery failed or unsupported:', err);
      return null;
    }
  }

  static async completeLessonMiniQuiz(lessonId, answers) {
    return await ApiClient.request(`/student/lessons/${lessonId}/quiz-completion`, {
      method: 'POST',
      body: { answers }
    });
  }

  static async optInLessonRevision(lessonId) {
    return await ApiClient.request(`/student/lessons/${lessonId}/opt-in`, {
      method: 'POST'
    });
  }

  static async getStudentAssessments() {
    return await ApiClient.request('/student/assessments');
  }

  static async getStudentAssessmentDetail(assessmentId) {
    return await ApiClient.request(`/student/assessments/${assessmentId}`);
  }

  static async getStudentAssessment(assessmentId) {
    return await ApiClient.getStudentAssessmentDetail(assessmentId);
  }

  static async startAssessmentAttempt(assessmentId) {
    return await ApiClient.request(`/student/assessments/${assessmentId}/start`, {
      method: 'POST'
    });
  }

  static async getAttemptDelivery(attemptId) {
    return await ApiClient.request(`/student/attempt/${attemptId}`);
  }

  static async renewAttemptLease(attemptId, leaseToken) {
    return await ApiClient.request(`/student/attempt/${attemptId}/lease/renew`, {
      method: 'POST', headers: { 'X-Attempt-Lease-Token': leaseToken }
    });
  }

  static async recordAttemptFocusEvent(attemptId, event) {
    return await ApiClient.request(`/student/attempt/${attemptId}/focus-events`, {
      method: 'POST',
      keepalive: true,
      body: event
    });
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

  static async getInstructorAttemptAppeal(attemptId) {
    return await ApiClient.request(`/instructor/attempts/${attemptId}/appeal`);
  }

  static async getAttemptGradeHistory(attemptId) {
    return await ApiClient.request(`/student/attempts/${attemptId}/grade-history`);
  }

  static async reviewAttemptAppeal(attemptId, payload) {
    return await ApiClient.request(`/instructor/attempts/${attemptId}/appeal/review`, {
      method: 'POST',
      body: payload
    });
  }

  static async sendAIChat(message, conversationId = null, courseId = null, lessonId = null) {
    const body = { message };
    if (conversationId !== undefined) body.conversation_id = conversationId;
    if (courseId) body.course_id = courseId;
    if (lessonId) body.lesson_id = lessonId;
    return await ApiClient.request('/student/ai/chat', {
      method: 'POST',
      body
    });
  }

  static async getRecommendations(limit = 4) {
    try {
      const res = await ApiClient.request(`/student/recommendations?limit=${limit}`);
      return res?.recommendations || res?.data?.recommendations || res || [];
    } catch {
      try {
        const res = await ApiClient.request(`/api/ai/recommendations?limit=${limit}`);
        return res?.recommendations || res?.data?.recommendations || res || [];
      } catch {
        return [];
      }
    }
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

  static async markAllNotificationsRead(category = null, role = null) {
    const payload = {};
    if (category) payload.category = category;
    if (role) payload.role = role;
    try {
      return await ApiClient.request('/auth/notifications/mark-all-read', {
        method: 'POST',
        body: payload
      });
    } catch {
      return await ApiClient.request('/student/notifications/mark-all-read', {
        method: 'POST',
        body: payload
      });
    }
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
  static async getInstructorDashboard(params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/instructor/dashboard?${query}` : '/instructor/dashboard';
    return await ApiClient.request(url);
  }

  static async getInstructorCourses(params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/instructor/courses?${query}` : '/instructor/courses';
    return await ApiClient.request(url);
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

  static async getCoursePublishChecklist(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/publish-checklist`);
  }

  static async cancelSubmitCourse(courseId, reviewVersion = '') {
    return await ApiClient.request(`/instructor/courses/${courseId}/cancel-submit`, {
      method: 'POST',
      body: { review_version: reviewVersion }
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

  static async getLearningUnits(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/learning-units`);
  }

  static async createLearningUnit(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}/learning-units`, {
      method: 'POST', body: data
    });
  }

  static async updateLearningUnit(unitId, data) {
    return await ApiClient.request(`/instructor/learning-units/${unitId}`, {
      method: 'PATCH', body: data
    });
  }

  static async deleteLearningUnit(unitId) {
    return await ApiClient.request(`/instructor/learning-units/${unitId}`, {
      method: 'DELETE'
    });
  }

  static async reorderLearningUnits(courseId, unitIds) {
    return await ApiClient.request(`/instructor/courses/${courseId}/learning-units/reorder`, {
      method: 'PUT',
      body: { unit_ids: unitIds }
    });
  }

  static async submitLearningUnit(unitId, courseId = null) {
    const url = courseId
      ? `/instructor/courses/${courseId}/learning-units/${unitId}/submit`
      : `/instructor/learning-units/${unitId}/submit`;
    return await ApiClient.request(url, { method: 'POST' });
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

  static async discardLessonDraft(lessonId) {
    return await ApiClient.request(`/instructor/lessons/${lessonId}/draft/discard`, {
      method: 'POST'
    });
  }

  static async deleteLesson(courseId, lessonId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/lessons/${lessonId}/delete`, {
      method: 'POST'
    });
  }

  static async reorderLessons(courseId, orderedLessonIds, move = null) {
    return await ApiClient.request(`/instructor/courses/${courseId}/lessons/reorder`, {
      method: 'POST',
      body: { ordered_lesson_ids: orderedLessonIds, ...(move ? { move } : {}) }
    });
  }

  static async getCourseChangesetStatus(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/changeset/status`);
  }

  static async submitCourseChangeset(courseId, changesetData) {
    return await ApiClient.request(`/instructor/courses/${courseId}/changeset/submit`, {
      method: 'POST',
      body: changesetData
    });
  }

  static async retractCourseChangeset(courseId, identity = {}) {
    return await ApiClient.request(`/instructor/courses/${courseId}/changeset/retract`, {
      method: 'POST',
      body: { request_id: identity.request_id, review_version: identity.review_version }
    });
  }

  static async discardCourseChangeset(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/changeset/discard`, {
      method: 'POST'
    });
  }

  static async getInstructorCourseChangesetDiff(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/changeset/diff`);
  }

  static async getAdminCourseChangesetDiff(changeRequestId) {
    return await ApiClient.request(`/admin/course-changes/${changeRequestId}/diff`);
  }

  static async getCourseChangesetDiff(idOrCourseId, forAdmin = null) {
    if (forAdmin === true || (forAdmin === null && typeof window !== 'undefined' && window.location.hash.startsWith('#/admin'))) {
      return await ApiClient.getAdminCourseChangesetDiff(idOrCourseId);
    }
    return await ApiClient.getInstructorCourseChangesetDiff(idOrCourseId);
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

  static async checkYouTubeLink(url) {
    return await ApiClient.request('/instructor/check-youtube-link', {
      method: 'POST',
      body: { url }
    });
  }

  static async scanCourseVideos(courseId) {
    return await ApiClient.request(`/instructor/courses/${courseId}/scan-videos`, {
      method: 'POST'
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
    return await ApiClient.request('/instructor/prerequisites/incoming-requests');
  }

  static async getInstructorPrerequisitePendingCount() {
    return await ApiClient.request('/instructor/prerequisites/incoming-requests/count');
  }

  // Instructor Grade Appeals Management (TASK-108)
  static async getInstructorAppeals(params = {}) {
    const q = new URLSearchParams(params).toString();
    const url = q ? `/instructor/appeals?${q}` : '/instructor/appeals';
    return await ApiClient.request(url);
  }

  static async getInstructorAppealDetail(appealId) {
    return await ApiClient.request(`/instructor/appeals/${appealId}`);
  }

  static async resolveInstructorAppeal(appealId, data) {
    return await ApiClient.request(`/instructor/appeals/${appealId}/resolve`, {
      method: 'POST',
      body: data
    });
  }

  // Instructor Draft Course Deletion (TASK-108/TASK-109)
  static async deleteInstructorDraftCourse(courseId, data = {}) {
    return await ApiClient.request(`/instructor/courses/${courseId}`, {
      method: 'DELETE',
      body: data
    });
  }

  // Admin Course Deletion (TASK-108/TASK-109)
  static async deleteAdminCourse(courseId, data = {}) {
    return await ApiClient.request(`/admin/courses/${courseId}`, {
      method: 'DELETE',
      body: data
    });
  }

  static async getInstructorIncomingPrerequisiteRequests() {
    return await ApiClient.request('/instructor/prerequisites/incoming-requests');
  }

  static async reviewInstructorIncomingPrerequisiteRequest(courseId, prereqId, data) {
    return await ApiClient.request(`/instructor/prerequisites/incoming-requests/${courseId}/${prereqId}/review`, {
      method: 'POST',
      body: data
    });
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

  static async saveCourseAcademicSettings(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}/academic-settings`, {
      method: 'PUT',
      body: data
    });
  }

  static async updateCourseCompletionRules(courseId, data) {
    return await ApiClient.request(`/instructor/courses/${courseId}/completion-rules`, {
      method: 'POST',
      body: data
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

  static async publishAssessment(assessmentId, expectedAuthoringToken = null) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/publish`, {
      method: 'POST',
      ...(expectedAuthoringToken ? { body: { expected_authoring_token: expectedAuthoringToken } } : {})
    });
  }

  static async trashAssessment(assessmentId, reason = '') {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/trash`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async reorderAssessmentQuestions(assessmentId, orderedQuestionIds) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/reorder`, {
      method: 'POST',
      body: { ordered_question_ids: orderedQuestionIds }
    });
  }

  static async createAssessmentQuestion(assessmentId, data) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/create`, {
      method: 'POST',
      body: data
    });
  }

  static async saveAssessmentAuthoring(assessmentId, payload) {
    const response = await ApiClient.request(`/instructor/assessments/${assessmentId}/authoring`, { method: 'POST', body: payload });
    return response?.data || response;
  }

  static async createAssessmentQuestionsBatch(assessmentId, questions) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/batch`, {
      method: 'POST',
      body: { questions }
    });
  }

  static async editAssessmentQuestion(assessmentId, questionId, data) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/${questionId}/edit`, {
      method: 'POST',
      body: data
    });
  }

  static async removeAssessmentQuestion(assessmentId, questionId) {
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/questions/${questionId}`, {
      method: 'DELETE'
    });
  }

  static async uploadCourseFile(courseId, file, title = file.name, assetType = 'RESOURCE') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title || (file && file.name) || 'course_file');
    formData.append('asset_type', assetType);
    const csrf = ApiClient.getCsrfToken();
    if (csrf) {
      formData.append('csrf_token', csrf);
    }
    const res = await ApiClient.request(`/instructor/courses/${courseId}/files`, {
      method: 'POST',
      body: formData
    });
    return res;
  }

  static async batchCreateAssessmentQuestions(assessmentId, questions) {
    return await ApiClient.createAssessmentQuestionsBatch(assessmentId, questions);
  }

  static async getAssessmentAttempts(assessmentId, page = 1, perPage = 50) {
    const query = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    return await ApiClient.request(`/instructor/assessments/${assessmentId}/attempts?${query.toString()}`);
  }

  static async getInstructorAttemptResult(attemptId, reason = '') {
    const query = reason ? `?reason=${encodeURIComponent(reason)}` : '';
    return await ApiClient.request(`/instructor/attempts/${attemptId}/results${query}`);
  }

  static async gradeInstructorAttemptQuestion(
    attemptId,
    attemptQuestionId,
    awardedPoints,
    reason = '',
    rowVersion = null,
  ) {
    return await ApiClient.request(`/instructor/attempts/${attemptId}/grades/${attemptQuestionId}`, {
      method: 'POST',
      body: {
        awarded_points: awardedPoints,
        reason,
        ...(rowVersion ? { row_version: rowVersion } : {}),
      },
    });
  }

  static async getInstructorAttemptFocusEvents(attemptId) {
    return await ApiClient.request(`/instructor/attempts/${attemptId}/focus-events`);
  }

  // =========================================================================
  // 4. Admin Role Endpoints
  // =========================================================================
  static async getAdminGovernance() {
    return await ApiClient.request('/admin/dashboard');
  }

  static async getAdminGovernanceSummary(force = false) {
    if (typeof SWRCache !== 'undefined') {
      return await SWRCache.wrap('/admin/governance/summary', () => ApiClient.request('/admin/governance/summary'), { force, ttl: 2 * 60 * 1000 });
    }
    return await ApiClient.request('/admin/governance/summary');
  }

  static async updateCoursePrice(courseId, price, reason = '') {
    const isAdmin = (window.app?.currentRole === 'ADMIN') || 
                    (window.Router?.currentRole === 'ADMIN') || 
                    (window.location.hash.startsWith('#/admin'));
    const endpoint = isAdmin
      ? `/admin/courses/${courseId}/price`
      : `/instructor/courses/${courseId}/price`;
    const payload = { price: Math.max(0, parseInt(price, 10) || 0) };
    if (reason && typeof reason === 'string' && reason.trim()) {
      payload.reason = reason.trim();
    }
    return await ApiClient.request(endpoint, {
      method: 'PUT',
      body: payload
    });
  }

  static async getAdminUsers(params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `/admin/users?${query}` : '/admin/users';
    return await ApiClient.request(url);
  }

  static async manageUserRole(userId, action, role, reason = '', adminSubRole = null) {
    const body = { action, role, reason };
    if (adminSubRole) body.admin_sub_role = adminSubRole;
    return await ApiClient.request(`/admin/users/${userId}/roles`, {
      method: 'POST',
      body,
    });
  }

  static async assignRole(userId, role, reason = '', adminSubRole = null) {
    return await ApiClient.manageUserRole(userId, 'assign', role, reason, adminSubRole);
  }

  static async assignRoles(userId, roles, reason = '', adminSubRole = null) {
    const body = { action: 'assign', roles, reason };
    if (adminSubRole) body.admin_sub_role = adminSubRole;
    return await ApiClient.request(`/admin/users/${userId}/roles`, {
      method: 'POST',
      body,
    });
  }

  static async removeRole(userId, role, reason = '') {
    return await ApiClient.manageUserRole(userId, 'remove', role, reason);
  }

  static async removeRoles(userId, roles, reason = '') {
    return await ApiClient.request(`/admin/users/${userId}/roles`, {
      method: 'POST',
      body: { action: 'remove', roles, reason },
    });
  }

  static async suspendUser(userId, reason = '', password = '', confirmationPhrase = '') {
    const body = { reason, confirmation_phrase: confirmationPhrase };
    if (password) body.password = password;
    return await ApiClient.request(`/admin/users/${userId}/suspend`, {
      method: 'POST',
      body
    });
  }

  static async unsuspendUser(userId, reason = '') {
    return await ApiClient.request(`/admin/users/${userId}/unsuspend`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async revokeUserSessions(userId, reason = '', password = '') {
    const body = { reason };
    if (password) body.password = password;
    return await ApiClient.request(`/admin/users/${userId}/revoke-sessions`, {
      method: 'POST',
      body
    });
  }

  static async forceRevokeSessions(userId, reason = '', password = '') {
    return await ApiClient.revokeUserSessions(userId, reason, password);
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

  static async getPendingCourses(force = false) {
    if (typeof SWRCache !== 'undefined') {
      return await SWRCache.wrap('/admin/courses/pending', () => ApiClient.request('/admin/courses/pending'), { force, ttl: 2 * 60 * 1000 });
    }
    return await ApiClient.request('/admin/courses/pending');
  }

  static async reviewCourse(courseId, action, reason = '', reviewVersion = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/review`, {
      method: 'POST',
      body: { action, reason, review_version: reviewVersion }
    });
  }

  static async flagLessonContent(courseId, lessonId, reason, contentType = 'bài học') {
    return await ApiClient.request(`/admin/courses/${courseId}/lessons/${lessonId}/flag`, {
      method: 'POST',
      body: { reason, content_type: contentType }
    });
  }

  static async getAdminChangeRequests(status = 'ALL') {
    const query = status && status !== 'ALL' ? `?status=${encodeURIComponent(status)}` : '';
    return await ApiClient.request(`/admin/change-requests${query}`);
  }

  static async getAdminChangeRequest(requestId) {
    return await ApiClient.request(`/admin/change-requests?request_id=${encodeURIComponent(requestId)}`);
  }

  static async reviewAdminChangeRequest(requestId, data) {
    return await ApiClient.request(`/admin/change-requests/${requestId}/review`, {
      method: 'POST',
      body: data
    });
  }

  static async getAdminCourseChangesetDiff(changeRequestId) {
    return await ApiClient.request(`/admin/course-changes/${changeRequestId}/diff`);
  }

  static async approveCourseChangeset(changeRequestId, reason = '', reviewVersion = '') {
    return await ApiClient.request(`/admin/course-changes/${changeRequestId}/approve`, {
      method: 'POST',
      body: { reason, request_id: changeRequestId, review_version: reviewVersion }
    });
  }

  static async rejectCourseChangeset(changeRequestId, reason = '', reviewVersion = '') {
    return await ApiClient.request(`/admin/course-changes/${changeRequestId}/reject`, {
      method: 'POST',
      body: { reason, request_id: changeRequestId, review_version: reviewVersion }
    });
  }

  static async reassignCourse(courseId, newInstructorId, reason = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/reassign`, {
      method: 'POST',
      body: { new_instructor_id: newInstructorId, reason }
    });
  }

  static async swapCourses(courseAId, courseBId, reason = '') {
    return await ApiClient.request('/admin/courses/swap', {
      method: 'POST',
      body: { course_a_id: courseAId, course_b_id: courseBId, reason }
    });
  }


  static async publishCourseAdmin(courseId, reason = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/publish`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async trashCourseAdmin(courseId, reason = '', password = '') {
    const body = { reason };
    if (password) body.password = password;
    return await ApiClient.request(`/admin/courses/${courseId}/trash`, {
      method: 'POST',
      body
    });
  }

  static async restoreCourseAdmin(courseId, reason = '') {
    return await ApiClient.request(`/admin/courses/${courseId}/restore`, {
      method: 'POST',
      body: { reason }
    });
  }

  static async quarantineOverride(assetId, reason = '', password = '') {
    const body = { reason };
    if (password) body.password = password;
    return await ApiClient.request(`/admin/files/${assetId}/quarantine-override`, {
      method: 'POST',
      body
    });
  }

  static async broadcastNotification(title, body, targetRole = null, category = 'SYSTEM', idempotencyKey = null) {
    const headers = idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {};
    return await ApiClient.request('/admin/notifications/broadcast', {
      method: 'POST',
      body: { title, body, target_role: targetRole, category },
      headers
    });
  }

  static async getAdminBroadcasts() {
    try {
      const res = await ApiClient.request('/admin/notifications/broadcasts');
      return res?.data || res?.broadcasts || (Array.isArray(res) ? res : []);
    } catch (err) {
      return [];
    }
  }

  static async deleteAdminBroadcast(eventId) {
    if (!eventId) throw new Error('eventId is required to delete broadcast');
    try {
      return await ApiClient.request(`/admin/notifications/broadcasts/${eventId}`, {
        method: 'DELETE'
      });
    } catch (err) {
      return await ApiClient.request(`/admin/notifications/broadcasts/${eventId}/delete`, {
        method: 'POST'
      });
    }
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

  static async restoreAdminBackup(backupId, confirmationPhrase, password, reason = '') {
    return await ApiClient.request(`/admin/backups/${backupId}/restore`, {
      method: 'POST',
      body: {
        confirmation_phrase: confirmationPhrase,
        password: password,
        reason: reason
      }
    });
  }

  static async getMaintenanceStatus() {
    return await ApiClient.request('/admin/maintenance/status');
  }

  static async startMaintenance(reason = 'Scheduled platform maintenance', durationMinutes = 60, password = '') {
    const body = {
      reason,
      estimated_duration_minutes: durationMinutes
    };
    if (password) body.password = password;
    return await ApiClient.request('/admin/maintenance/start', {
      method: 'POST',
      body
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
    if (options.role) params.append('role', options.role);
    if (options.target_role) params.append('target_role', options.target_role);
    if (options.category && options.category !== 'ALL') params.append('category', options.category);
    if (options.unread_only) params.append('unread_only', 'true');
    if (options.page) params.append('page', options.page);
    if (options.per_page) params.append('per_page', options.per_page);
    const qs = params.toString() ? `?${params.toString()}` : '';

    let lastError = null;
    for (const endpoint of ['/auth/notifications', '/student/notifications', '/api/notifications']) {
      try {
        return await ApiClient.request(`${endpoint}${qs}`);
      } catch (error) {
        lastError = error;
      }
    }

    const unavailable = new Error('Không thể tải thông báo. Dữ liệu hiện chưa xác định.');
    unavailable.code = 'NOTIFICATIONS_UNAVAILABLE';
    unavailable.cause = lastError;
    throw unavailable;
  }

  static async getUnreadNotificationCount(options = {}) {
    const params = new URLSearchParams();
    if (options.role) params.append('role', options.role);
    if (options.target_role) params.append('target_role', options.target_role);
    const qs = params.toString() ? `?${params.toString()}` : '';
    try {
      const res = await ApiClient.request(`/auth/notifications/unread-count${qs}`);
      if (res && typeof res.unread_count !== 'undefined') return res.unread_count;
    } catch {
      // Fallback
    }
    const list = await ApiClient.getNotifications(options);
    return list.unread_count ?? (list.items || []).filter(i => !i.is_read && !i.read).length;
  }

  static async markNotificationRead(notificationId) {
    if (!notificationId) return { success: false };
    return await ApiClient.request(`/auth/notifications/${notificationId}/read`, {
      method: 'POST',
    });
  }

  static async markAllNotificationsRead(category = null, role = null) {
    const body = {};
    if (category && category !== 'ALL') body.category = category;
    if (role) body.role = role;
    return await ApiClient.request('/auth/notifications/mark-all-read', {
      method: 'POST',
      body: body,
    });
  }

  static async deleteNotification(notificationId) {
    if (!notificationId) return { success: false };
    return await ApiClient.request(`/auth/notifications/${notificationId}`, {
      method: 'DELETE',
    });
  }

  static async clearNotifications(role = null) {
    return await ApiClient.request('/auth/notifications/clear', {
      method: 'POST',
      body: role ? { role } : {},
    });
  }

  static async parseExamFile(file, courseId = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (courseId) {
      formData.append('course_id', courseId);
    }
    return await ApiClient.request('/instructor/exams/parse-file', {
      method: 'POST',
      body: formData
    });
  }

  static async downloadExcelExamTemplate() {
    window.location.href = '/instructor/exams/excel-template';
  }

  static async parseExcelExam(file, courseId = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (courseId) {
      formData.append('course_id', courseId);
    }
    return await ApiClient.request('/instructor/exams/parse-excel', {
      method: 'POST',
      body: formData
    });
  }

  static async parseMoodleXml(fileOrText, courseId = null) {
    if (fileOrText instanceof File || fileOrText instanceof Blob) {
      const formData = new FormData();
      formData.append('file', fileOrText);
      if (courseId) {
        formData.append('course_id', courseId);
      }
      return await ApiClient.request('/instructor/exams/parse-moodle-xml', {
        method: 'POST',
        body: formData
      });
    }
    return await ApiClient.request('/instructor/exams/parse-moodle-xml', {
      method: 'POST',
      body: { xml: String(fileOrText), course_id: courseId }
    });
  }

  static async parseMoodleJson(fileOrText, courseId = null) {
    if (fileOrText instanceof File || fileOrText instanceof Blob) {
      const formData = new FormData();
      formData.append('file', fileOrText);
      if (courseId) {
        formData.append('course_id', courseId);
      }
      return await ApiClient.request('/instructor/exams/parse-json', {
        method: 'POST',
        body: formData
      });
    }
    const body = typeof fileOrText === 'object' ? { ...fileOrText } : { json_content: String(fileOrText) };
    if (courseId) {
      body.course_id = courseId;
    }
    return await ApiClient.request('/instructor/exams/parse-json', {
      method: 'POST',
      body: body
    });
  }

  static async downloadMoodleXmlSample() {
    window.location.href = '/instructor/exams/samples/moodle-xml';
  }

  static async downloadMoodleJsonSample() {
    window.location.href = '/instructor/exams/samples/json';
  }

  // =========================================================================
  // 6. Digital Wallet & PayOS Payments (TASK-120)
  // =========================================================================
  static async getMyWallet(page = 1, pageSize = 5) {
    return await ApiClient.request(`/api/payments/wallet/me?page=${page}&page_size=${pageSize}`);
  }

  static async createDepositRequest(amount, returnUrl = '', cancelUrl = '') {
    return await ApiClient.request('/api/payments/deposit/create', {
      method: 'POST',
      body: { amount, return_url: returnUrl, cancel_url: cancelUrl }
    });
  }

  static async purchaseCourseWithWallet(courseId) {
    return await ApiClient.request('/api/payments/course/purchase', {
      method: 'POST',
      body: { course_id: courseId }
    });
  }

  static async createDirectCourseQr(courseId, returnUrl = '', cancelUrl = '') {
    return await ApiClient.request('/api/payments/course/create-direct-qr', {
      method: 'POST',
      body: { course_id: courseId, return_url: returnUrl, cancel_url: cancelUrl }
    });
  }

  static async checkTransactionStatus(txId) {
    return await ApiClient.request('/api/payments/check-status/' + txId);
  }

  static async getAdminCashflowDashboard() {
    return await ApiClient.request('/admin/cashflow/dashboard');
  }

  static async getAdminCashflowTransactions(options = {}) {
    const params = new URLSearchParams();
    if (options.limit) params.append('limit', options.limit);
    if (options.offset) params.append('offset', options.offset);
    if (options.tx_type) params.append('tx_type', options.tx_type);
    if (options.user_id) params.append('user_id', options.user_id);
    const qs = params.toString() ? '?' + params.toString() : '';
    return await ApiClient.request('/admin/cashflow/transactions' + qs);
  }

  static async verifyAdminCashflowTransaction(txId, formDataOrBody) {
    return await ApiClient.request('/admin/cashflow/verify/' + txId, {
      method: 'POST',
      body: formDataOrBody
    });
  }

  static async revokeAdminCashflowTransaction(txId, reason = '') {
    return await ApiClient.request('/admin/cashflow/revoke/' + txId, {
      method: 'POST',
      body: { reason }
    });
  }



  static async getCashflowDashboard() {
    return await ApiClient.getAdminCashflowDashboard();
  }

  static async getCashflowTransactions(options = {}) {
    return await ApiClient.getAdminCashflowTransactions(options);
  }

  static async verifyCashflowTransaction(txId, formDataOrBody) {
    return await ApiClient.verifyAdminCashflowTransaction(txId, formDataOrBody);
  }

  static async revokeCashflowTransaction(txId, reason = '') {
    return await ApiClient.revokeAdminCashflowTransaction(txId, reason);
  }
}


window.ApiClient = ApiClient;
