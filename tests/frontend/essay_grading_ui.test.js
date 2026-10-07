const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const apiSource = fs.readFileSync(
  path.resolve(__dirname, '../../frontend/assets/js/api.js'),
  'utf8',
);
const instructorSource = fs.readFileSync(
  path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js'),
  'utf8',
);
const studentSource = fs.readFileSync(
  path.resolve(__dirname, '../../frontend/assets/js/views/student.js'),
  'utf8',
);

test('instructor API client exposes the server-authoritative essay grading action', () => {
  assert.match(apiSource, /gradeInstructorAttemptQuestion\s*\(\s*attemptId[\s\S]*attemptQuestionId/);
});

test('instructor attempt detail renders a pending essay grading control', () => {
  assert.match(instructorSource, /grading_status\s*===\s*['"]PENDING['"]/);
  assert.match(instructorSource, /awarded_points/);
  assert.match(instructorSource, /gradeInstructorAttemptQuestion\(/);
  assert.match(instructorSource, /Lưu điểm tự luận/);
});

test('student result preserves manually graded essay answers and awarded points', () => {
  assert.match(studentSource, /questionType\s*===\s*['"]ESSAY['"]/);
  assert.match(studentSource, /student_answer_text/);
  assert.match(studentSource, /grading_status\s*===\s*['"]MANUAL_GRADED['"]/);
  assert.match(studentSource, /points_assigned/);
});

test('student result distinguishes a hidden essay answer from an unanswered submission', () => {
  assert.match(studentSource, /answer_visibility_policy/);
  assert.match(studentSource, /Câu trả lời đang được ẩn theo chính sách khảo thí/);
});
