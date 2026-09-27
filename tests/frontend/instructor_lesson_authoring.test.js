const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const window = {};
const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), { window }, { filename: sourcePath });

test('lesson saves for one editor run in order, even when an earlier save is slow', async () => {
  const enqueueSave = window.InstructorView.createLessonSaveQueue();
  const events = [];
  const firstSave = enqueueSave(async () => {
    events.push('first-start');
    await new Promise(resolve => setTimeout(resolve, 20));
    events.push('first-finish');
  });
  const secondSave = enqueueSave(async () => {
    events.push('second-start');
    events.push('second-finish');
  });

  await Promise.all([firstSave, secondSave]);
  assert.deepEqual(events, ['first-start', 'first-finish', 'second-start', 'second-finish']);
});

test('lesson editor upload controls accept multiple files and expose a drop target', () => {
  const source = fs.readFileSync(sourcePath, 'utf8');
  assert.ok(source.includes('id="studio-hidden-file-input" class="hidden" multiple'));
  assert.ok(source.includes('id="studio-attachments-list"'));
  assert.ok(source.includes('resourceDropzone.ondrop'));
  assert.ok(source.includes('id="studio-video-file-input"'));
  assert.ok(source.includes('multiple'));
});
