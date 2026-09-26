const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const instructorView = { InstructorView: {} };
const sourcePath = path.resolve(__dirname, '../../frontend/assets/js/views/instructor-exams.js');
vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), { window: instructorView }, { filename: sourcePath });

const isFillAnswerCorrect = instructorView.InstructorView.isInteractiveFillAnswerCorrect;

test('accepts any configured variant for one fill blank', () => {
  assert.equal(isFillAnswerCorrect(['JWT'], 'JWT, JSON Web Token'), true);
  assert.equal(isFillAnswerCorrect(['JSON Web Token'], 'JWT, JSON Web Token'), true);
});

test('matches each fill blank only against its own answer group', () => {
  assert.equal(isFillAnswerCorrect(['HTTP', 'Retrieval'], 'HTTP, Hypertext Transfer Protocol; GET, Retrieval'), true);
  assert.equal(isFillAnswerCorrect(['HTTP', 'HTTP'], 'HTTP, Hypertext Transfer Protocol; GET, Retrieval'), false);
  assert.equal(isFillAnswerCorrect(['HTTP'], 'HTTP; GET'), false);
});
