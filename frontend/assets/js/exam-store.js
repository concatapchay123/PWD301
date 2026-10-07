/**
 * ExamStore - Centralized Reactive Exam Draft Store for PWD301.
 * 
 * Manages shared exam draft state across all dedicated sub-pages:
 * - Hub / Method Selector (#/instructor/exams)
 * - Raw Syntax Editor (#/instructor/exams/editor)
 * - Interactive Visual Builder (#/instructor/exams/interactive)
 * - Excel Import (#/instructor/exams/excel)
 * - Moodle XML / JSON (#/instructor/exams/moodle)
 * - Academic Governance Matrix (#/instructor/exams/matrix)
 * - Proctoring & Settings (#/instructor/exams/settings)
 */

class ExamStore {
  static STORAGE_KEY = 'pwd301_azota_exam_draft';
  static _memoryDraft = null;
  static _memoryScopeUserId = null;
  static _memoryScopeRole = null;

  static getCurrentScope() {
    try {
      const router = window.app || window.appRouter;
      const user = router?.currentUser;
      if (!user) return { userId: null, role: null, canAuthor: false };
      const userId = user.id || user.public_id || null;
      const role = String(user.active_role || user.role || user.primary_role || '').toUpperCase();
      const canAuthor = role === 'INSTRUCTOR' || role === 'ADMIN';
      return { userId, role, canAuthor };
    } catch {
      return { userId: null, role: null, canAuthor: false };
    }
  }

  static checkScope() {
    const scope = this.getCurrentScope();
    if (this._memoryScopeUserId !== scope.userId || this._memoryScopeRole !== scope.role) {
      this._memoryDraft = null;
      this._memoryScopeUserId = scope.userId;
      this._memoryScopeRole = scope.role;
    }
    return scope;
  }

  static getStorageKey() {
    const scope = this.getCurrentScope();
    if (scope.userId && scope.canAuthor) {
      return `pwd301_azota_exam_draft_${scope.userId}`;
    }
    return null;
  }

  static clearMemoryDraft() {
    this._memoryDraft = null;
    this._memoryScopeUserId = null;
    this._memoryScopeRole = null;
  }

  static getDefaultDraft() {
    return {
      title: 'De_thi_moi.docx',
      rawText: '',
      courseId: '',
      courseCode: '',
      courseTitle: '',
      academicMode: 'independent',
      lessonId: '',
      questions: [],
      config: {
        duration: 45,
        maxAttempts: 1,
        shuffleQuestions: true,
        requirePassword: false,
        examPassword: '',
        examLayout: 'STANDARD',
        monitoringEnabled: false,
        requestFullscreen: false,
        scoreScale: 40.0
      },
      lastSaved: null,
      sourceMethod: 'manual',
      methodSelected: false,
      matrixConfirmed: false
    };
  }

  static getDraft() {
    const scope = this.checkScope();
    if (!scope.canAuthor && scope.userId) {
      return this.getDefaultDraft();
    }
    if (this._memoryDraft) {
      return this._memoryDraft;
    }
    const key = this.getStorageKey();
    if (key) {
      try {
        const stored = localStorage.getItem(key);
        if (stored) {
          const parsed = JSON.parse(stored);
          this._memoryDraft = {
            ...this.getDefaultDraft(),
            ...parsed,
            config: {
              ...this.getDefaultDraft().config,
              ...(parsed.config || {}),
              examPassword: '' // Password is strictly memory-only
            },
            methodSelected: parsed.methodSelected ?? Boolean(
              (parsed.rawText && parsed.rawText.trim()) ||
              (Array.isArray(parsed.questions) && parsed.questions.length)
            )
          };
          return this._memoryDraft;
        }
      } catch (e) {
        console.warn('[ExamStore] Error reading saved draft:', e);
      }
    }
    this._memoryDraft = this.getDefaultDraft();
    return this._memoryDraft;
  }

  static saveDraft(updates = {}) {
    const scope = this.checkScope();
    const current = this.getDraft();
    const invalidateMatrix = updates.questions !== undefined
      || (updates.courseId !== undefined && updates.courseId !== current.courseId)
      || (updates.sourceMethod !== undefined && updates.sourceMethod !== current.sourceMethod);

    this._memoryDraft = {
      ...current,
      ...updates,
      config: {
        ...current.config,
        ...(updates.config || {})
      },
      matrixConfirmed: updates.matrixConfirmed ?? (invalidateMatrix ? false : current.matrixConfirmed)
    };

    const key = this.getStorageKey();
    if (key && scope.canAuthor) {
      try {
        // Sanitize password before persisting to durable storage
        const durablePayload = {
          ...this._memoryDraft,
          config: {
            ...this._memoryDraft.config,
            examPassword: ''
          }
        };
        delete durablePayload.storageFailed;
        delete durablePayload.storageError;

        localStorage.setItem(key, JSON.stringify(durablePayload));
        this._memoryDraft.lastSaved = new Date().toISOString();
        this._memoryDraft.storageFailed = false;
        delete this._memoryDraft.storageError;
      } catch (e) {
        console.warn('[ExamStore] Error persisting draft to localStorage:', e);
        this._memoryDraft.lastSaved = null;
        this._memoryDraft.storageFailed = true;
        this._memoryDraft.storageError = e.message || String(e);
      }
    } else {
      // Memory-only (anonymous or non-persisted)
      this._memoryDraft.lastSaved = null;
      this._memoryDraft.storageFailed = false;
    }
    return this._memoryDraft;
  }

  static hasDraft() {
    const scope = this.checkScope();
    if (!scope.canAuthor && scope.userId) return false;
    const key = this.getStorageKey();
    if (!key) {
      const d = this._memoryDraft;
      if (!d) return false;
      return Boolean(
        (d.rawText && d.rawText.trim().length > 0) ||
        (Array.isArray(d.questions) && d.questions.length > 0)
      );
    }
    try {
      const stored = localStorage.getItem(key);
      if (!stored) {
        const d = this._memoryDraft;
        return Boolean(
          d && (
            (d.rawText && d.rawText.trim().length > 0) ||
            (Array.isArray(d.questions) && d.questions.length > 0)
          )
        );
      }
      const parsed = JSON.parse(stored);
      return (
        (parsed.rawText && parsed.rawText.trim().length > 0) ||
        (Array.isArray(parsed.questions) && parsed.questions.length > 0)
      );
    } catch {
      return false;
    }
  }

  static canVisitStep(step) {
    if (step <= 1) return true;
    const draft = this.getDraft();
    const hasContent = Boolean(
      draft.methodSelected ||
      (Array.isArray(draft.questions) && draft.questions.length > 0) ||
      (draft.rawText && draft.rawText.trim().length > 0)
    );
    if (step === 2) return hasContent;
    const questionsReady = hasContent && Array.isArray(draft.questions) && draft.questions.length > 0;
    if (step === 3) return questionsReady;
    return questionsReady && Boolean(draft.matrixConfirmed);
  }

  static clearDraft() {
    this.checkScope();
    this._memoryDraft = this.getDefaultDraft();
    const key = this.getStorageKey();
    if (key) {
      try {
        localStorage.removeItem(key);
      } catch (e) {
        console.warn('[ExamStore] Error clearing draft:', e);
      }
    }
    return this._memoryDraft;
  }

  static appendQuestions(newQuestions = []) {
    if (!Array.isArray(newQuestions) || newQuestions.length === 0) return this.getDraft();
    const draft = this.getDraft();
    const existing = draft.questions || [];
    const startIndex = existing.length;

    const normalized = newQuestions.map((q, idx) => ({
      ...q,
      id: startIndex + idx + 1,
      number: startIndex + idx + 1
    }));

    draft.questions = [...existing, ...normalized];
    if (window.ExamParser) {
      draft.rawText = window.ExamParser.generateAzotaRawFromQuestions
        ? window.ExamParser.generateAzotaRawFromQuestions(draft.questions)
        : window.ExamParser.generateRawFromQuestions(draft.questions);
    }
    return this.saveDraft({ questions: draft.questions, rawText: draft.rawText });
  }

  static replaceQuestions(newQuestions = []) {
    const draft = this.getDraft();
    const normalized = (newQuestions || []).map((q, idx) => ({
      ...q,
      id: idx + 1,
      number: idx + 1
    }));

    draft.questions = normalized;
    if (window.ExamParser) {
      draft.rawText = window.ExamParser.generateAzotaRawFromQuestions
        ? window.ExamParser.generateAzotaRawFromQuestions(draft.questions)
        : window.ExamParser.generateRawFromQuestions(draft.questions);
    }
    return this.saveDraft({ questions: draft.questions, rawText: draft.rawText });
  }

  static updateQuestion(index, updatedFields = {}) {
    const draft = this.getDraft();
    if (draft.questions && draft.questions[index]) {
      draft.questions[index] = { ...draft.questions[index], ...updatedFields };
      if (window.ExamParser) {
        draft.rawText = window.ExamParser.generateAzotaRawFromQuestions
          ? window.ExamParser.generateAzotaRawFromQuestions(draft.questions)
          : window.ExamParser.generateRawFromQuestions(draft.questions);
      }
      this.saveDraft({ questions: draft.questions, rawText: draft.rawText });
    }
    return draft;
  }

  static deleteQuestion(index) {
    const draft = this.getDraft();
    if (draft.questions && index >= 0 && index < draft.questions.length) {
      draft.questions.splice(index, 1);
      // Re-index
      draft.questions = draft.questions.map((q, i) => ({
        ...q,
        id: i + 1,
        number: i + 1
      }));
      if (window.ExamParser) {
        draft.rawText = window.ExamParser.generateAzotaRawFromQuestions
          ? window.ExamParser.generateAzotaRawFromQuestions(draft.questions)
          : window.ExamParser.generateRawFromQuestions(draft.questions);
      }
      this.saveDraft({ questions: draft.questions, rawText: draft.rawText });
    }
    return draft;
  }
}

window.ExamStore = ExamStore;
