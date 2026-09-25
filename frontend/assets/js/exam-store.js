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
        proctoring: false,
        lockTab: true,
        scoreScale: 40.0
      },
      lastSaved: null,
      sourceMethod: 'manual'
    };
  }

  static getDraft() {
    if (this._memoryDraft) {
      return this._memoryDraft;
    }
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        this._memoryDraft = {
          ...this.getDefaultDraft(),
          ...parsed,
          config: {
            ...this.getDefaultDraft().config,
            ...(parsed.config || {})
          }
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
    this._memoryDraft = {
      ...current,
      ...updates,
      config: {
        ...current.config,
        ...(updates.config || {})
      },
      lastSaved: new Date().toISOString()
    };

    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this._memoryDraft));
    } catch (e) {
      console.warn('[ExamStore] Error persisting draft to localStorage:', e);
    }
    return this._memoryDraft;
  }

  static hasDraft() {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
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

  static clearDraft() {
    this._memoryDraft = this.getDefaultDraft();
    try {
      localStorage.removeItem(this.STORAGE_KEY);
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
