const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/views/instructor-exams.js');
const uploadedFiles = [];
const window = { InstructorView: {} };
class TestFile {
  constructor(parts, name, options) {
    this.parts = parts;
    this.name = name;
    this.type = options.type;
    this.size = parts.reduce((size, part) => size + part.length, 0);
  }
}

vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), {
  window,
  File: TestFile,
  atob: value => Buffer.from(value, 'base64').toString('binary'),
  Buffer,
  ApiClient: {
    async uploadCourseFile(courseId, file) {
      uploadedFiles.push({ courseId, file });
      return { asset_id: `${uploadedFiles.length}`.padStart(8, '0') + '-0000-4000-8000-000000000000' };
    }
  },
  console
}, { filename: sourcePath });

test('Moodle import refuses broken images without uploading or dropping review metadata', async () => {
  uploadedFiles.length = 0;
  const questions = [{
    images: [{ filename: 'valid.png', mime_type: 'image/png', data_base64: 'aW1hZ2U=', broken: false }]
  }, {
    images: [{ filename: 'missing.png', mime_type: '', data_base64: '', broken: true }]
  }];

  await assert.rejects(
    window.InstructorView.uploadMoodleQuestionImages(questions, 'course-1'),
    /missing or unsafe/i
  );

  assert.equal(uploadedFiles.length, 0);
  assert.equal(questions[1].images[0].broken, true);
});

test('Moodle import uploads all embedded images and preserves their order as question resources', async () => {
  uploadedFiles.length = 0;
  const question = {
    image_asset_ids: ['existing-asset'],
    images: [
      { filename: 'first.png', mime_type: 'image/png', data_base64: 'aW1hZ2UtMQ==', broken: false },
      { filename: 'second.jpg', mime_type: 'image/jpeg', data_base64: 'aW1hZ2UtMg==', broken: false }
    ]
  };

  await window.InstructorView.uploadMoodleQuestionImages([question], 'course-1');

  assert.deepEqual(uploadedFiles.map(item => item.file.name), ['first.png', 'second.jpg']);
  assert.equal(question.image_asset_ids.length, 3);
  assert.equal(question.image_asset_id, 'existing-asset');
  assert.equal(Object.hasOwn(question, 'images'), false);
});

test('clipboard image extraction accepts inline image data but ignores remote image URLs', () => {
  const images = window.InstructorView.extractPastedImages({
    items: [],
    getData(type) {
      if (type === 'text/html') {
        return '<p>Question</p><img src="data:image/png;base64,aW1hZ2U="><img src="https://example.invalid/remote.png">';
      }
      return '';
    }
  });

  assert.equal(images.length, 1);
  assert.equal(images[0].type, 'image/png');
  assert.equal(images[0].name, 'pasted-question-image-1.png');
});
