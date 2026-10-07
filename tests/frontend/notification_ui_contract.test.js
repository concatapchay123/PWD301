const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const uiPath = path.resolve(__dirname, '../../frontend/assets/js/ui.js');

test('UI.alert keeps title and message in the caller contract', () => {
  const sandbox = {
    window: {},
    document: { getElementById: () => null },
    console,
  };
  vm.runInNewContext(fs.readFileSync(uiPath, 'utf8'), sandbox, { filename: uiPath });

  let modalOptions;
  sandbox.window.UI.openModal = (options) => {
    modalOptions = options;
  };

  sandbox.window.UI.alert('Tiêu đề cảnh báo', 'Nội dung cần hiển thị');

  assert.equal(modalOptions.title, 'Tiêu đề cảnh báo');
  assert.match(modalOptions.bodyHtml, /Nội dung cần hiển thị/);
});

test('ApiClient.formatApiErrorMessage correctly localizes error codes and messages', () => {
  const apiPath = path.resolve(__dirname, '../../frontend/assets/js/api.js');
  const sandbox = {
    window: {},
    document: { getElementById: () => null, querySelector: () => null },
    console,
  };
  vm.runInNewContext(fs.readFileSync(apiPath, 'utf8'), sandbox, { filename: apiPath });

  const ApiClient = sandbox.window.ApiClient;

  // 1. Standard Error Code translation
  const localizedCode = ApiClient.formatApiErrorMessage({
    error: { code: 'COURSE_NOT_FOUND', message: 'Course not found in database.' }
  }, 404);
  assert.equal(localizedCode, 'Không tìm thấy khóa học.');

  // 2. English phrase fallback translation
  const localizedPhrase = ApiClient.formatApiErrorMessage({
    error: { code: 'CUSTOM_ERR', message: 'Admin direct edits to an Instructor-owned course require a reason.' }
  }, 400);
  assert.equal(localizedPhrase, 'Quản trị viên chỉnh sửa khóa học của giảng viên cần cung cấp lý do thay đổi.');

  // 3. Existing Vietnamese message preserved untouched
  const viMsg = ApiClient.formatApiErrorMessage({
    error: { code: 'INVALID_CREDENTIALS', message: 'Email hoặc mật khẩu không chính xác.' }
  }, 401);
  assert.equal(viMsg, 'Email hoặc mật khẩu không chính xác.');

  // 4. Default fallback when no specific match
  const defaultFallback = ApiClient.formatApiErrorMessage({}, 500);
  assert.equal(defaultFallback, 'Lỗi yêu cầu (HTTP 500)');
});

test('Source files do not contain unmanaged raw alert or confirm calls', () => {
  const controllersPath = path.resolve(__dirname, '../../frontend/assets/js/controllers.js');
  const instructorPath = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');

  const controllersCode = fs.readFileSync(controllersPath, 'utf8');
  const instructorCode = fs.readFileSync(instructorPath, 'utf8');

  // Verify no raw alert(...) in controllers.js
  assert.equal(/(?<!UI\.)\balert\s*\(/.test(controllersCode), false, 'controllers.js should not call raw alert()');

  // Verify no raw confirm(...) in controllers.js
  assert.equal(/(?<!UI\.)\bconfirm\s*\(/.test(controllersCode), false, 'controllers.js should not call raw confirm()');

  // Verify no window.confirm in instructor.js
  assert.equal(/\bwindow\.confirm\s*\(/.test(instructorCode), false, 'instructor.js should not call window.confirm()');
});
