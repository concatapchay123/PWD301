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

test('lesson studio reports review state and skips unchanged autosave', () => {
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });
  assert.equal(window.InstructorView.lessonSaveOutcome({ pending_approval: true }, true), 'pending');
  assert.equal(window.InstructorView.lessonSaveOutcome({ status: 'PUBLISHED' }, true), 'published');
  assert.equal(window.InstructorView.lessonSaveOutcome({ status: 'DRAFT' }, false), 'saved');
  assert.equal(window.InstructorView.shouldAutosaveLesson('same', 'same'), false);
  assert.equal(window.InstructorView.shouldAutosaveLesson('changed', 'same'), true);
});

test('learning unit lesson cards open their editor when selected', () => {
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), {
    window, document: {}, UI: { escapeHtml: value => String(value) },
  }, { filename });
  const html = window.InstructorView.renderLessonChildNavigator({
    learning_unit_id: 'unit-1',
    title: 'Bài học đầu',
    lessons: [{ lesson_id: 'lesson-1', title: 'Lesson đầu', position: 1 }],
  }, 'course-1', 'lesson-1');
  assert.match(html, /href="#\/instructor\/courses\/course-1\/lessons\/lesson-1\/edit"/);
  assert.match(html, /aria-current="page"/);
  assert.match(html, /Lesson đầu/);
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

test('files waiting for Admin approval stay out of attached Lesson resources', async () => {
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });
  const result = await window.InstructorView.uploadLessonFiles(
    [{ name: 'queued.pdf' }, { name: 'active.pdf' }],
    async file => file.name === 'queued.pdf'
      ? { pending_approval: true, change_request_id: 9 }
      : { resource_id: 'active', title: file.name },
  );
  assert.equal(result.pending.length, 1);
  assert.equal(result.uploaded.length, 1);
  assert.equal(result.uploaded[0].resource_id, 'active');
});

test('two video slots include YouTube links and uploaded videos together', () => {
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });
  const links = ['a'];
  const resources = [{ filename: 'one.mp4' }, { filename: 'notes.pdf' }];
  assert.equal(window.InstructorView.canAddLessonVideo(links, resources), false);
  assert.equal(window.InstructorView.canAddLessonVideo([], resources), true);
  assert.equal(window.InstructorView.getVideoCount(links, resources), 2);
  assert.equal(window.InstructorView.getRemainingVideoSlots(links, resources), 0);
  assert.equal(window.InstructorView.getRemainingVideoSlots([], resources), 1);
});

test('filterVideoUploadBatch respects remaining slots and categorizes invalid files', () => {
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });

  const files = [
    { name: 'clip1.mp4', size: 50000000 },
    { name: 'clip2.webm', size: 60000000 },
    { name: 'document.pdf', size: 1000000 },
    { name: 'giant_video.mov', size: 1000000001 },
    { name: 'clip3.mkv', size: 70000000 },
    { name: 'clip4.mp4', size: 80000000 }
  ];

  const res = window.InstructorView.filterVideoUploadBatch(files, 2);
  assert.equal(res.accepted.length, 2);
  assert.equal(res.accepted[0].name, 'clip1.mp4');
  assert.equal(res.accepted[1].name, 'clip2.webm');
  assert.equal(res.overflow.length, 2);
  assert.equal(res.overflow[0].name, 'clip3.mkv');
  assert.equal(res.overflow[1].name, 'clip4.mp4');
  assert.equal(res.invalidType.length, 1);
  assert.equal(res.invalidType[0].name, 'document.pdf');
  assert.equal(res.oversized.length, 1);
  assert.equal(res.oversized[0].name, 'giant_video.mov');
});

test('moveVideoItem reorders video list while preserving elements', () => {
  const window = {};
  const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
  vm.runInNewContext(fs.readFileSync(filename, 'utf8'), { window, document: {} }, { filename });

  const items = [{ id: '1' }, { id: '2' }, { id: '3' }];
  const movedDown = window.InstructorView.moveVideoItem(items, 0, 1);
  assert.equal(JSON.stringify(movedDown.map(i => i.id)), JSON.stringify(['2', '1', '3']));

  const movedUp = window.InstructorView.moveVideoItem(items, 2, 0);
  assert.equal(JSON.stringify(movedUp.map(i => i.id)), JSON.stringify(['3', '1', '2']));

  // Edge cases
  assert.equal(JSON.stringify(window.InstructorView.moveVideoItem(items, 0, 0).map(i => i.id)), JSON.stringify(['1', '2', '3']));
  assert.equal(JSON.stringify(window.InstructorView.moveVideoItem(items, -1, 2).map(i => i.id)), JSON.stringify(['1', '2', '3']));
  assert.equal(JSON.stringify(window.InstructorView.moveVideoItem(items, 0, 10).map(i => i.id)), JSON.stringify(['1', '2', '3']));
});

test('instructor video studio renders draggable cards and omits arrow buttons', () => {
  const code = fs.readFileSync(path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'), 'utf8');
  assert.ok(code.includes('video-draggable-card'));
  assert.ok(code.includes('drag_indicator'));
  assert.ok(!code.includes('btn-video-move-up'));
  assert.ok(!code.includes('btn-video-move-down'));
});
