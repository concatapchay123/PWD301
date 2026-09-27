const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

test('all application dialog backdrops use a supported blur utility', () => {
  for (const relative of [
    '../../frontend/index.html',
    '../../frontend/assets/js/ui.js',
    '../../frontend/assets/js/views/instructor.js',
    '../../frontend/assets/js/views/instructor-exams.js',
  ]) {
    const source = fs.readFileSync(path.resolve(__dirname, relative), 'utf8');
    assert.doesNotMatch(source, /backdrop-blur-(?:none|xs)\b/, relative);
  }
});
