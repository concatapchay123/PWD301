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

test('focus monitoring tracks away duration and invokes fullscreen callbacks', () => {
  const document = Object.assign(target(), { hidden: false, fullscreenElement: null });
  const window = Object.assign(target(), { crypto: { randomUUID: () => 'event-2' } });
  const filename = path.resolve(__dirname, '../../frontend/assets/js/ui.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document }, { filename });

  const events = [];
  const observations = [];
  let fullscreenExitCalled = false;
  let fullscreenEnterCalled = false;

  const monitor = new window.ExamAntiCheatManager({
    watchFullscreen: true,
    onEvent: event => events.push(event),
    onObservation: (count, type, dur, totalAway) => observations.push({ count, type, dur, totalAway }),
    onFullscreenExit: () => { fullscreenExitCalled = true; },
    onFullscreenEnter: () => { fullscreenEnterCalled = true; }
  });

  monitor.start();
  // Simulate fullscreen exit
  document.fullscreenElement = null;
  document.emit('fullscreenchange');
  assert.equal(fullscreenExitCalled, true);
  assert.equal(events.length, 1);
  assert.equal(events[0].event_type, 'FULLSCREEN_EXIT');
  assert.equal(events[0].phase, 'START');

  // Re-enter fullscreen
  document.fullscreenElement = {};
  document.emit('fullscreenchange');
  assert.equal(fullscreenEnterCalled, true);
  assert.equal(events.length, 2);
  assert.equal(events[1].phase, 'END');
  assert.equal(typeof events[1].duration_seconds, 'number');
  assert.equal(typeof events[1].total_away_seconds, 'number');
  assert.equal(observations.length, 2);

  // Anti-cheat event prevention
  let defaultPrevented = false;
  const mockEvt = { preventDefault: () => { defaultPrevented = true; }, key: 'F12', keyCode: 123 };
  document.listeners.get('keydown')?.(mockEvt);
  assert.equal(defaultPrevented, true);

  let contextmenuPrevented = false;
  document.listeners.get('contextmenu')?.({ preventDefault: () => { contextmenuPrevented = true; } });
  assert.equal(contextmenuPrevented, true);

  let copyPrevented = false;
  document.listeners.get('copy')?.({ preventDefault: () => { copyPrevented = true; } });
  assert.equal(copyPrevented, true);

  monitor.stop();
  assert.equal(document.listeners.size, 0);
});
