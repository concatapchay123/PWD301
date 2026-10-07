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

  static getStorageKey() {
    try {
      const router = window.app || window.appRouter;
      const userId = router?.currentUser?.id;
      if (userId) return `pwd301_azota_exam_draft_${userId}`;
    } catch {}
    return 'pwd301_azota_exam_draft';
  }

  static clearMemoryDraft() {
    this._memoryDraft = null;
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
    if (this._memoryDraft) {
      return this._memoryDraft;
    }
    try {
      const key = this.getStorageKey();
      const stored = localStorage.getItem(key) || (key !== 'pwd301_azota_exam_draft' ? localStorage.getItem('pwd301_azota_exam_draft') : null);
      if (stored) {
        const parsed = JSON.parse(stored);
        this._memoryDraft = {
          ...this.getDefaultDraft(),
          ...parsed,
          config: {
            ...this.getDefaultDraft().config,
            ...(parsed.config || {})
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
    this._memoryDraft = this.getDefaultDraft();
    return this._memoryDraft;
  }

  static saveDraft(updates = {}) {
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
      lastSaved: new Date().toISOString(),
      matrixConfirmed: updates.matrixConfirmed ?? (invalidateMatrix ? false : current.matrixConfirmed)
    };

    try {
      localStorage.setItem(this.getStorageKey(), JSON.stringify(this._memoryDraft));
    } catch (e) {
      console.warn('[ExamStore] Error persisting draft to localStorage:', e);
      this._memoryDraft.lastSaved = null;
      this._memoryDraft.storageFailed = true;
    }
    return this._memoryDraft;
  }

  static hasDraft() {
    try {
      const key = this.getStorageKey();
      const stored = localStorage.getItem(key) || (key !== 'pwd301_azota_exam_draft' ? localStorage.getItem('pwd301_azota_exam_draft') : null);
      if (!stored) return false;
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
    this._memoryDraft = this.getDefaultDraft();
    try {
      localStorage.removeItem(this.getStorageKey());
      localStorage.removeItem('pwd301_azota_exam_draft');
    } catch (e) {
      console.warn('[ExamStore] Error clearing draft:', e);
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
