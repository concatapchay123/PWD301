const fs = require('fs');

// 1. index.html
const indexHtml = fs.readFileSync('frontend/index.html', 'utf8');
if (!indexHtml.includes('absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2')) {
  throw new Error('index.html missing absolute centering classes on topbar');
}
if (!indexHtml.includes('id="topbar-wallet-wrapper"') || !indexHtml.includes('relative hidden" id="topbar-wallet-wrapper"')) {
  throw new Error('index.html missing hidden on topbar-wallet-wrapper');
}
console.log('PASS: index.html topbar centering and wallet hidden');

// 2. router.js
const routerJs = fs.readFileSync('frontend/assets/js/router.js', 'utf8');
if (!routerJs.includes("this.currentRole === 'ADMIN'") || !routerJs.includes("walletWrapper.classList.add('hidden')")) {
  throw new Error('router.js missing admin wallet hiding logic');
}
if (!routerJs.includes("this.currentRole !== 'ADMIN' ?")) {
  throw new Error('router.js missing role dropdown wallet filtering');
}
console.log('PASS: router.js wallet RBAC and responsive link classes');

// 3. instructor.js
const instructorJs = fs.readFileSync('frontend/assets/js/views/instructor.js', 'utf8');
if (!instructorJs.includes('data-qtype-select="TRUE_FALSE"')) {
  throw new Error('instructor.js missing data-qtype-select TRUE_FALSE');
}
if (!instructorJs.includes('quiz_tf_correct_')) {
  throw new Error('instructor.js missing quiz_tf_correct_ radio');
}
console.log('PASS: instructor.js TRUE_FALSE lesson quiz editor');

// 4. instructor-exams.js
const examsJs = fs.readFileSync('frontend/assets/js/views/instructor-exams.js', 'utf8');
if (!examsJs.includes('id="tab-btn-tf"')) {
  throw new Error('instructor-exams.js missing tab-btn-tf');
}
if (!examsJs.includes('id="form-container-tf"')) {
  throw new Error('instructor-exams.js missing form-container-tf');
}
if (!examsJs.includes("interactive_type: 'TRUE_FALSE'")) {
  throw new Error('instructor-exams.js missing interactive_type TRUE_FALSE generation');
}
console.log('PASS: instructor-exams.js TRUE_FALSE interactive builder');

// 5. student.js
const studentJs = fs.readFileSync('frontend/assets/js/views/student.js', 'utf8');
if (!studentJs.includes("q.question_type === 'TRUE_FALSE' ?")) {
  throw new Error('student.js missing TRUE_FALSE take page 2-column rendering');
}
console.log('PASS: student.js TRUE_FALSE take exam rendering');
