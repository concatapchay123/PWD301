const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const source = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');

function harness(standalone = false) {
  const requests = [];
  let frame;
  function node() {
    return {
      children: [], disabled: false, value: '', focusCount: 0, parent: null,
      get isConnected() { return this.scopeRoot?.isConnected ?? frame.root.isConnected; },
      set innerHTML(value) { this.html = value; for (const child of this.children) child.parent = null; this.children = []; },
      get innerHTML() { return this.html || ''; },
      appendChild(child) { child.parent = this; this.children.push(child); },
      remove() { if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this); },
      focus() { this.focusCount++; },
    };
  }
  function newFrame() {
    const elements = Object.fromEntries(['console-ai-messages', 'console-ai-input', 'console-ai-send-btn', 'console-ai-form', 'console-ai-new-chat-btn', 'console-ai-context-label', 'ai-chat-messages', 'ai-chat-input', 'ai-chat-send-btn', 'clear-ai-chat-btn', 'ai-context-course-select'].map(id => [id, node()]));
    elements['ai-context-course-select'].options = [];
    const root = { isConnected: true, querySelector(selector) { return elements[selector.slice(1)] || null; } };
    for (const element of Object.values(elements)) element.scopeRoot = root;
    return { elements, root };
  }
  frame = newFrame();
  const original = frame;
  const window = { location: { hash: '#/student/courses/course?lesson_id=first' }, app: { currentUser: { id: 'owner', active_role: 'STUDENT' } } };
  const context = {
    window, console, Date: { now: () => 1 },
    courseId: 'course', course: { title: 'Course' }, activeItem: { type: 'lesson', id: 'first', title: 'First' },
    container: { querySelector() { return original.root; } },
    document: {
      getElementById(id) { return frame.elements[id] || frame.elements['console-ai-messages'].children.find(child => child.id === id) || null; },
      querySelectorAll() { return []; }, createElement: node,
    },
    ApiClient: { getEnrolledCourses: async () => [], sendAIChat(...args) { return new Promise((resolve, reject) => requests.push({ args, resolve, reject })); } },
    UI: { escapeHtml: String, renderMarkdown: String, showToast() {} },
  };
  vm.createContext(context);
  vm.runInContext(source, context);
  const start = standalone ? source.indexOf("    const chatContainer = document.getElementById('ai-chat-messages');") : source.indexOf('      // AI Chat Controller inside NetAcad Course Console');
  const end = source.indexOf(standalone ? '    if (sendBtn) sendBtn.onclick' : '      // Search Box in Outline', start);
  vm.runInContext(source.slice(start, end) + `\nthis.send = ${standalone ? 'handleSend' : 'sendConsoleAIMessage'};`, context);
  return { context, window, original, requests,
    replaceRoot() { original.root.isConnected = false; frame = newFrame(); return frame; },
  };
}

test('new console conversation rejects old response and old finally cannot unlock a newer request', async () => {
  const h = harness();
  const old = h.context.send('Old question');
  h.original.elements['console-ai-new-chat-btn'].onclick();
  assert.equal(h.original.elements['console-ai-send-btn'].disabled, false);
  const current = h.context.send('New question');
  assert.equal(h.requests.length, 2);
  assert.equal(h.requests[1].args[1], null);
  h.requests[0].resolve({ conversation_id: 'old-conversation', reply: 'Old response' });
  await old;
  assert.equal(h.original.elements['console-ai-send-btn'].disabled, true);
  assert.equal(h.original.elements['console-ai-messages'].children.length, 2);
  h.requests[1].resolve({ conversation_id: 'current-conversation', reply: 'Current response' });
  await current;
  assert.equal(h.original.elements['console-ai-send-btn'].disabled, false);
  assert.equal(h.original.elements['console-ai-messages'].children.length, 2);
  assert.ok(h.original.elements['console-ai-messages'].children[1].innerHTML.includes('Current response'));
});

test('standalone context switch enables a new request but stale finally keeps its button locked', async () => {
  const h = harness(true);
  const old = h.context.send('Old question');
  h.original.elements['ai-context-course-select'].value = 'new-course';
  h.original.elements['ai-context-course-select'].onchange();
  assert.equal(h.original.elements['ai-chat-send-btn'].disabled, false);
  const current = h.context.send('New question');
  h.requests[0].resolve({ reply: 'Old response' });
  await old;
  assert.equal(h.original.elements['ai-chat-send-btn'].disabled, true);
  h.requests[1].resolve({ reply: 'Current response' });
  await current;
  assert.equal(h.original.elements['ai-chat-send-btn'].disabled, false);
});

test('standalone clear refreshes the active route after its staging container was detached', () => {
  const h = harness(true);
  let refreshes = 0;
  let capturedRenders = 0;
  h.context.UI.refreshCurrentRoute = () => { refreshes++; };
  h.context.capturedRender = () => { capturedRenders++; };
  vm.runInContext('StudentView.renderAIAssistant = capturedRender;', h.context);
  const start = source.indexOf('    if (clearBtn) {', source.indexOf('  static renderAIAssistant(container)'));
  const end = source.indexOf("    container.querySelectorAll('.chip-btn')", start);
  assert.ok(start >= 0 && end > start);
  vm.runInContext(source.slice(start, end), h.context);
  h.original.elements['clear-ai-chat-btn'].onclick();
  assert.equal(refreshes, 1);
  assert.equal(capturedRenders, 0);
});

test('standalone serializes sends and rejects responses after owner or route changes', async () => {
  for (const change of ['owner', 'route']) {
    const h = harness(true);
    const old = h.context.send('Old question');
    void h.context.send('Overlapping question');
    assert.equal(h.requests.length, 1);
    if (change === 'owner') h.window.app.currentUser.id = 'other';
    else h.window.location.hash = '#/student/dashboard';
    h.requests[0].resolve({ reply: 'Old response' });
    await old;
    assert.equal(h.original.elements['ai-chat-messages'].children.length, 1);
    assert.equal(h.original.elements['ai-chat-input'].focusCount, 0);
  }
});

test('standalone late failures and replaced roots cannot receive replies or focus', async () => {
  for (const change of ['owner', 'root']) {
    const h = harness(true);
    const old = h.context.send('Old question');
    if (change === 'owner') h.window.app.currentUser.active_role = 'INSTRUCTOR';
    else h.replaceRoot();
    h.requests[0].reject(new Error('Old failure'));
    await old;
    assert.equal(h.original.elements['ai-chat-messages'].children.length, 1);
    assert.equal(h.original.elements['ai-chat-input'].focusCount, 0);
  }
});

test('late console success or failure cannot append into a replaced root', async () => {
  for (const failing of [false, true]) {
    const h = harness();
    const pending = h.context.send('Old question');
    const next = h.replaceRoot();
    if (failing) h.requests[0].reject(new Error('Old failure'));
    else h.requests[0].resolve({ reply: 'Old response' });
    await pending;
    assert.equal(next.elements['console-ai-messages'].children.length, 0);
    assert.equal(next.elements['console-ai-input'].focusCount, 0);
  }
});

test('console response cannot apply after owner, route or lesson context changes', async () => {
  for (const change of ['owner', 'route', 'lesson']) {
    const h = harness();
    const pending = h.context.send('Old question');
    if (change === 'owner') h.window.app.currentUser.id = 'other-owner';
    else if (change === 'route') h.window.location.hash = '#/student/dashboard';
    else h.context.activeItem = { type: 'lesson', id: 'other', title: 'Other' };
    h.requests[0].resolve({ reply: 'Old response' });
    await pending;
    assert.equal(h.original.elements['console-ai-messages'].children.length, 1);
  }
});
