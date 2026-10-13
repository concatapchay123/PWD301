const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

function setup(renew) {
  const user = { id: 'owner', active_role: 'STUDENT' };
  const window = { app: { currentUser: user } };
  const root = { isConnected: true };
  const calls = [], states = [];
  let tick, cleared = 0;
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/views/student.js', 'utf8'), {
    window, console,
    setInterval(fn, delay) { tick = fn; assert.equal(delay, 3000); return 7; },
    clearInterval(id) { assert.equal(id, 7); cleared++; },
    ApiClient: { renewAttemptLease: async (...args) => { calls.push(args); return renew(); } },
  });
  const heartbeat = window.StudentView.createAttemptLeaseHeartbeat(root, 'attempt', 'token', 3, (...args) => states.push(args));
  return { root, user, calls, states, heartbeat, tick: () => tick(), cleared: () => cleared };
}

test('heartbeat renewals serialize and retry a temporary failure', async () => {
  let resolve;
  const h = setup(() => new Promise(done => { resolve = done; }));
  const pending = h.tick();
  await h.tick();
  assert.equal(h.calls.length, 1);
  resolve({ remaining_seconds: 60 });
  await pending;
  assert.equal(h.states[0][0], true);
  h.heartbeat.stop();
  await h.tick();
  assert.equal(h.calls.length, 1);
  assert.equal(h.cleared(), 1);
});

test('temporary heartbeat failure reports unavailable and can recover', async () => {
  let failing = true;
  const h = setup(async () => { if (failing) throw new Error('Offline'); return {}; });
  await h.tick();
  assert.equal(h.states[0][0], false);
  assert.equal(h.cleared(), 0);
  failing = false;
  await h.heartbeat.retry();
  assert.equal(h.states[1][0], true);
});

test('lost lease stops polling and detached or changed owner ignores late renewal', async () => {
  const lost = setup(async () => { throw Object.assign(new Error('Lost lease'), { status: 409 }); });
  await lost.tick();
  await lost.tick();
  assert.equal(lost.calls.length, 1);
  assert.equal(lost.cleared(), 1);
  for (const mode of ['detached', 'owner', 'role']) {
    let resolve;
    const h = setup(() => new Promise(done => { resolve = done; }));
    const pending = h.tick();
    if (mode === 'detached') h.root.isConnected = false;
    else if (mode === 'owner') h.user.id = 'other';
    else h.user.active_role = 'INSTRUCTOR';
    resolve({});
    await pending;
    await h.tick();
    assert.equal(h.states.length, 0);
    assert.equal(h.cleared(), 1);
  }
});

test('API heartbeat uses existing renew endpoint and explicit lease header', async () => {
  const window = {};
  vm.runInNewContext(fs.readFileSync('frontend/assets/js/api.js', 'utf8'), { window, console });
  let request;
  window.ApiClient.request = async (url, options) => { request = { url, options }; return { status: 'IN_PROGRESS' }; };
  await window.ApiClient.renewAttemptLease('attempt', 'token');
  assert.equal(request.url, '/student/attempt/attempt/lease/renew');
  assert.equal(request.options.method, 'POST');
  assert.equal(request.options.headers['X-Attempt-Lease-Token'], 'token');
});
