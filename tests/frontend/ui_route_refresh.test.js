const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadUI(app) {
  const window = { app };
  const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/ui.js');
  vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), { window }, { filename: sourcePath });
  return window.UI;
}

test('refreshes through the router when available and preserves the fallback outside the app', () => {
  const routed = [];
  const routedUI = loadUI({ handleRoute: () => { routed.push('route'); return 'staged-refresh'; } });
  let fallbackCalls = 0;

  assert.equal(routedUI.refreshCurrentRoute(() => { fallbackCalls += 1; }), 'staged-refresh');
  assert.deepEqual(routed, ['route']);
  assert.equal(fallbackCalls, 0);

  const standaloneUI = loadUI(null);
  assert.equal(standaloneUI.refreshCurrentRoute(() => { fallbackCalls += 1; return 'fallback'; }), 'fallback');
  assert.equal(fallbackCalls, 1);
});
