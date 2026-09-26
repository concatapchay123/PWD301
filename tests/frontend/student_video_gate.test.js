const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const window = {};
const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/views/student.js');
vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), { window }, { filename: sourcePath });

test('video quiz gate requires full progress even when a stale completion flag exists', () => {
  assert.equal(window.StudentView.isLessonVideoWatched({
    video_url: '/lesson.mp4',
    minimum_completion_seconds: 30,
    progress: { seconds_spent: 60, max_view_fraction: 0.8, is_completed: true }
  }), false);
  assert.equal(window.StudentView.isLessonVideoWatched({
    video_url: '/lesson.mp4',
    minimum_completion_seconds: 30,
    progress: { seconds_spent: 30, max_view_fraction: 1.0, is_completed: false }
  }), true);
  assert.equal(window.StudentView.isLessonVideoWatched({
    video_url: null,
    progress: { seconds_spent: 0, max_view_fraction: 0 }
  }), true);
});
