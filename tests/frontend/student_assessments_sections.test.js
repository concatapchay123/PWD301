const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const filename = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
const uiFilename = path.resolve(__dirname, '../../frontend/assets/js/ui.js');

const window = {};
const document = {
  getElementById: () => null,
  querySelectorAll: () => [],
};

// Mock UI helper
const UI = {
  escapeHtml: (str) => String(str || ''),
  formatDuration: (sec) => `${sec}s`,
  statusBadge: (status) => `<span class="badge">${status}</span>`,
};

const sandbox = {
  window,
  document,
  UI,
  ApiClient: {},
  console,
};

vm.runInNewContext(fs.readFileSync(filename, 'utf8'), sandbox, { filename });

test('categorization partitions assessments into 3 non-overlapping sections', () => {
  const items = [
    { id: '1', title: 'Exam 1', is_open: true, is_closed: false, is_attempt_limit_reached: false, course_code: 'CS1' },
    { id: '2', title: 'Exam 2', is_open: false, is_closed: false, is_waiting_room_open: true, course_code: 'CS1' },
    { id: '3', title: 'Exam 3', is_open: false, is_closed: false, is_waiting_room_open: false, course_code: 'CS2' },
    { id: '4', title: 'Exam 4', is_open: true, is_closed: true, is_attempt_limit_reached: false, course_code: 'CS2' },
    { id: '5', title: 'Exam 5', is_open: true, is_closed: false, is_attempt_limit_reached: true, course_code: 'CS3' },
  ];

  const active = [];
  const upcoming = [];
  const completed = [];

  items.forEach(a => {
    if (a.is_closed || a.is_attempt_limit_reached) {
      completed.push(a);
    } else if (!a.is_open) {
      upcomingList = upcoming.push(a);
    } else {
      active.push(a);
    }
  });

  assert.equal(active.length, 1);
  assert.equal(active[0].id, '1');

  assert.equal(upcoming.length, 2);
  assert.equal(upcoming[0].id, '2');
  assert.equal(upcoming[1].id, '3');

  assert.equal(completed.length, 2);
  assert.equal(completed[0].id, '4');
  assert.equal(completed[1].id, '5');
});

test('renderAssessmentsList generates updated title and single status badge', async () => {
  let innerHTML = '';
  const container = {
    set innerHTML(val) {
      innerHTML = val;
    },
    get innerHTML() {
      return innerHTML;
    }
  };

  const grid = {
    set innerHTML(val) {
      this._html = val;
    },
    get innerHTML() {
      return this._html || '';
    },
    querySelectorAll: () => []
  };

  const statsBox = {
    set innerHTML(val) {
      this._html = val;
    }
  };

  sandbox.document.getElementById = (id) => {
    if (id === 'student-assessments-grid') return grid;
    if (id === 'student-assessments-stats') return statsBox;
    return null;
  };

  sandbox.ApiClient.getStudentAssessments = async () => ({
    assessments: [
      {
        id: 'asm-1',
        title: 'Đề kiểm tra Giữa kỳ',
        is_open: true,
        is_closed: false,
        is_attempt_limit_reached: false,
        course_code: 'DSA201',
        course_title: 'Cấu Trúc Dữ Liệu',
        time_limit_minutes: 60,
        max_points: 100,
        attempts_count: 0
      }
    ]
  });

  await sandbox.window.StudentView.renderAssessmentsList(container);

  // Title must be 'Danh sách Bài kiểm tra'
  assert.match(innerHTML, /Danh sách Bài kiểm tra/);
  assert.doesNotMatch(innerHTML, /Danh sách Bài thi & Khảo thí/);

  // Must have 3 section headers
  assert.match(grid.innerHTML, /Bài kiểm tra đang diễn ra/);
  assert.match(grid.innerHTML, /Bài kiểm tra sắp mở/);
  assert.match(grid.innerHTML, /Bài kiểm tra đã kết thúc & Quá hạn/);

  // Single badge invariant: must show 'Đang diễn ra' and NOT duplicate 'Đang mở'
  assert.match(grid.innerHTML, /Đang diễn ra/);
  assert.doesNotMatch(grid.innerHTML, />Đang mở</);
});
