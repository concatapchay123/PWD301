const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const filename = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
const window = {};
vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });

test('waiting room prioritizes resuming an active attempt over exhausted count', () => {
  const state = window.StudentView.getWaitingRoomState({
    active_attempt_id: 'attempt-a',
    is_attempt_limit_reached: true,
    is_closed: true,
  });
  assert.equal(state, 'RESUME');
});

test('waiting room prevents starting when closed or attempt limit reached', () => {
  assert.equal(window.StudentView.getWaitingRoomState({ is_open: true, is_closed: true }), 'CLOSED');
  assert.equal(window.StudentView.getWaitingRoomState({ is_open: true, is_attempt_limit_reached: true }), 'EXHAUSTED');
  assert.equal(window.StudentView.getWaitingRoomState({ is_open: false }), 'UPCOMING');
  assert.equal(window.StudentView.getWaitingRoomState({ is_open: true, can_start: true }), 'READY');
});
