const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function target() {
  const listeners = new Map();
  return {
    listeners,
    addEventListener(name, callback) { listeners.set(name, callback); },
    removeEventListener(name) { listeners.delete(name); },
    emit(name) { listeners.get(name)?.(); },
  };
}

test('focus monitoring reports a start and end without submitting the attempt', () => {
  const document = Object.assign(target(), { hidden: false, fullscreenElement: {} });
  const window = Object.assign(target(), { crypto: { randomUUID: () => 'event-1' } });
  const filename = path.resolve(__dirname, '../../frontend/assets/js/ui.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document }, { filename });
  const events = [];
  const monitor = new window.ExamAntiCheatManager({ onEvent: event => events.push(event) });
  monitor.start();
  document.hidden = true;
  document.emit('visibilitychange');
  document.hidden = false;
  document.emit('visibilitychange');
  assert.equal(events.length, 2);
  assert.equal(events[0].event_type, 'TAB_HIDDEN');
  assert.equal(events[0].phase, 'START');
  assert.equal(events[1].phase, 'END');
  assert.equal(events[1].event_id, events[0].event_id);
  monitor.stop();
  assert.equal(document.listeners.size, 0);
});
