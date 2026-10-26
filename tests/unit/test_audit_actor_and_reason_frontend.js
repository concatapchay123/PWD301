/**
 * Frontend Unit Test for Audit Log Actor Display and Vietnamese Event Summary
 */
const assert = require('assert');
const fs = require('fs');

const adminJs = fs.readFileSync('frontend/assets/js/views/admin.js', 'utf8');

console.log('--- TESTING ADMIN AUDIT LOG ACTOR & VIETNAMESE LOCALIZATION ---');

// 1. Verify formatAuditReasonVi exists and translates correctly
assert(adminJs.includes('formatAuditReasonVi('), 'AdminView must contain formatAuditReasonVi');
assert(adminJs.includes('getAuditActionMeta('), 'AdminView must contain getAuditActionMeta');

// 2. Extract and test formatAuditReasonVi via node eval
const sandbox = {
  UI: {
    escapeHtml: (s) => String(s || ''),
    formatRelativeTime: () => 'Vừa xong',
    formatDateTime: () => '25/10/2026 23:41:42'
  },
  ApiClient: {},
  document: {
    getElementById: () => null
  },
  window: { app: {} }
};

// Evaluate AdminView definition
const vm = require('vm');
vm.createContext(sandbox);

// Wrap AdminView in sandbox
const script = `
class UI {
  static escapeHtml(s) { return String(s || ''); }
  static formatRelativeTime() { return 'Vừa xong'; }
  static formatDateTime() { return '25/10/2026'; }
}
const ApiClient = {};
` + adminJs + `; this.AdminView = AdminView;`;

vm.runInContext(script, sandbox);
const AdminView = sandbox.AdminView;

// Test translation of forgery string
const forgeryEn = "Client attempted to forge 100% completion via zero-time reconcile bypass without required dwell time or video watch.";
const forgeryVi = AdminView.formatAuditReasonVi(forgeryEn, "SECURITY_ALERT_PROGRESS_FORGERY_ATTEMPT", "Lesson", { label: "CẢNH BÁO: Làm giả tiến độ học" });
assert.strictEqual(
  forgeryVi,
  "Phát hiện hành vi gian lận tiến độ học: Bỏ qua thời lượng học thực tế hoặc xem video bằng yêu cầu đồng bộ tức thì."
);
console.log('✓ Forgery reason translated to Vietnamese correctly');

// Test translation of attempt start & submit
const startVi = AdminView.formatAuditReasonVi("Student started attempt #1", "ATTEMPT_STARTED", "ASSESSMENT", {});
assert.strictEqual(startVi, "Học viên bắt đầu làm bài thi (lần thi #1)");
console.log('✓ Student started attempt translated correctly');

const subVi = AdminView.formatAuditReasonVi("Student submitted attempt #2", "ATTEMPT_SUBMITTED", "ASSESSMENT", {});
assert.strictEqual(subVi, "Học viên đã nộp bài thi (lần thi #2)");
console.log('✓ Student submitted attempt translated correctly');

// Test reordering questions
const reorderVi = AdminView.formatAuditReasonVi("Reordered 25 questions", "ASSESSMENT_QUESTIONS_REORDERED", "ASSESSMENT", {});
assert.strictEqual(reorderVi, "Đã sắp xếp lại thứ tự 25 câu hỏi");
console.log('✓ Reordered questions translated correctly');

// Test course completion
const compVi = AdminView.formatAuditReasonVi("Course completion criteria satisfied", "COURSE_COMPLETED", "COURSE", {});
assert.strictEqual(compVi, "Đã thỏa mãn đầy đủ điều kiện hoàn thành khóa học");
console.log('✓ Course completed translated correctly');

// Test action meta
const meta = AdminView.getAuditActionMeta("SECURITY_ALERT_PROGRESS_FORGERY_ATTEMPT");
assert.strictEqual(meta.label, "CẢNH BÁO: Làm giả tiến độ học");
console.log('✓ Action meta verified');

// 3. Verify Actor display logic in admin.js does NOT hardcode "Giảng viên" or role
assert(!adminJs.includes("displayActor = 'Giảng viên'"), 'Hardcoded displayActor Giảng viên must be removed');
assert(adminJs.includes("rawActorName || (actorEmail ? actorEmail"), 'displayActor must use actor name');

console.log('--- ALL FRONTEND AUDIT TESTS PASSED SUCCESSFULLY! ---');
