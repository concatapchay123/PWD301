const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

test('only the active lesson studio may save its form fields', () => {
  const first = { isConnected: false };
  const second = { isConnected: true };
  const active = { current: second };
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window,
    document: { getElementById: id => id === 'lesson-studio-root' ? active.current : null },
  }, { filename });

  assert.equal(window.InstructorView.isActiveLessonStudio(first), false);
  assert.equal(window.InstructorView.isActiveLessonStudio(second), true);
  active.current = null;
  assert.equal(window.InstructorView.isActiveLessonStudio(second), false);
});

test('lesson resource batch processes every selected file independently', async () => {
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });
  const seen = [];
  const files = [{ name: 'a.pdf' }, { name: 'b.pdf' }, { name: 'c.pdf' }];
  const result = await window.InstructorView.uploadLessonFiles(files, async file => {
    seen.push(file.name);
    if (file.name === 'b.pdf') throw new Error('scan failed');
    return { title: file.name };
  });
  assert.deepEqual(seen, ['a.pdf', 'b.pdf', 'c.pdf']);
  assert.equal(result.uploaded.length, 2);
  assert.equal(result.failed.length, 1);
});

test('five video slots include YouTube links and uploaded videos together', () => {
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });
  const links = ['a', 'b', 'c'];
  const resources = [{ filename: 'one.mp4' }, { filename: 'two.webm' }, { filename: 'notes.pdf' }];
  assert.equal(window.InstructorView.canAddLessonVideo(links, resources), false);
  assert.equal(window.InstructorView.canAddLessonVideo(links.slice(1), resources), true);
});
