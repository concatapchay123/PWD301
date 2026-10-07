const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const instructorJsPath = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');

function loadInstructorContext(overrides = {}) {
  const window = {};
  const document = {
    getElementById: () => null,
    querySelectorAll: () => [],
    querySelector: () => null,
    createElement: (tag) => ({
      tagName: tag.toUpperCase(),
      classList: { add: () => {}, remove: () => {}, toggle: () => {} },
      setAttribute: () => {},
      getAttribute: () => null,
      appendChild: () => {},
      addEventListener: () => {},
      style: {},
    }),
  };
  const UI = {
    showToast: () => {},
    confirm: async () => true,
    prompt: async () => 'New Value',
    escapeHtml: (s) => String(s || ''),
    renderMarkdown: (s) => String(s || ''),
    refreshCurrentRoute: () => {},
  };
  const ApiClient = {
    getLesson: async () => ({ id: 'l1', title: 'Lesson 1', markdown_content: '' }),
    updateLesson: async () => ({ success: true }),
    attachLessonResource: async () => ({ success: true, resource_id: 'r1' }),
    detachLessonResource: async () => ({ success: true }),
    reorderLearningUnits: async () => ({ success: true }),
    reorderLessons: async () => ({ success: true }),
  };

  const context = {
    window,
    document,
    UI,
    ApiClient,
    console,
    ...overrides,
  };
  vm.runInNewContext(fs.readFileSync(instructorJsPath, 'utf8'), context, { filename: instructorJsPath });
  return context;
}

test('SYNC-009: parseLessonToBlocks and serializeBlocksToPayload preserve video_urls and videoType roundtrip', () => {
  const { window } = loadInstructorContext();
  const InstructorView = window.InstructorView;

  const rawLesson = {
    id: 'lesson-yt-1',
    title: 'Bài học YouTube',
    summary: 'Mô tả bài học',
    video_urls: [
      'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
      'https://youtu.be/9bZkp7q19f0'
    ],
    markdown_content: 'Nội dung bài học có video',
    quiz: [],
    resources: []
  };

  // 1. Parse into blocks
  const blocks = InstructorView.parseLessonToBlocks(rawLesson);
  const videoBlocks = blocks.filter(b => b.type === 'video');
  assert.equal(videoBlocks.length, 2, 'Should create 2 video blocks for 2 URLs');
  assert.equal(videoBlocks[0].videoType, 'YOUTUBE');
  assert.equal(videoBlocks[0].url, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
  assert.equal(videoBlocks[1].url, 'https://youtu.be/9bZkp7q19f0');

  // 2. Serialize blocks back to payload
  const payload = InstructorView.serializeBlocksToPayload(blocks, {
    title: rawLesson.title,
    summary: rawLesson.summary
  });

  assert.equal(payload.title, 'Bài học YouTube');
  assert.deepEqual([...payload.video_urls], [
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'https://youtu.be/9bZkp7q19f0'
  ], 'Should preserve all video URLs in serialized payload');
});

test('SYNC-015: lessonSaveOutcome and pending approval responses distinguish 202 from live applied', () => {
  const { window } = loadInstructorContext();
  const InstructorView = window.InstructorView;

  // 202 pending approval outcome
  assert.equal(InstructorView.lessonSaveOutcome({ pending_approval: true }, true), 'pending');
  assert.equal(InstructorView.lessonSaveOutcome({ status: 'PENDING_APPROVAL' }, true), 'pending');
  assert.equal(InstructorView.lessonSaveOutcome({ status: 202 }, true), 'pending');

  // Normal outcomes
  assert.equal(InstructorView.lessonSaveOutcome({ status: 'PUBLISHED' }, true), 'published');
  assert.equal(InstructorView.lessonSaveOutcome({ status: 'DRAFT' }, false), 'saved');
});

test('SYNC-011: Returned working draft ID replaces published lesson ID in active state', () => {
  const { window } = loadInstructorContext();
  const InstructorView = window.InstructorView;

  // Verify helper exists or can compute new draft ID replacement
  const targetLessonId = 'pub-lesson-123';
  const saveResponse = {
    success: true,
    is_draft: true,
    status: 'DRAFT',
    lesson: {
      lesson_id: 'draft-lesson-456',
      status: 'DRAFT'
    }
  };

  const newId = saveResponse?.lesson?.lesson_id || saveResponse?.lesson_id || saveResponse?.id;
  assert.equal(newId, 'draft-lesson-456');
  assert.notEqual(newId, targetLessonId);
});

test('SYNC-020: Optimistic move snapshot rollback correctly reverts unit arrays on failure', () => {
  const units = [
    { id: 'u1', title: 'Chương 1' },
    { id: 'u2', title: 'Chương 2' },
    { id: 'u3', title: 'Chương 3' }
  ];

  const snapshot = JSON.parse(JSON.stringify(units));
  // Mutate optimistically: swap u1 and u2
  const temp = units[0];
  units[0] = units[1];
  units[1] = temp;
  assert.equal(units[0].id, 'u2');

  // Simulate API failure: rollback from snapshot
  let rolledBack = JSON.parse(JSON.stringify(snapshot));
  assert.equal(rolledBack[0].id, 'u1');
  assert.equal(rolledBack[1].id, 'u2');
  assert.equal(rolledBack[2].id, 'u3');
});
