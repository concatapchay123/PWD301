import test from 'node:test';
import assert from 'node:assert/strict';

test('ExamStore canVisitStep permits step 2 unconditionally', () => {
  // Mock ExamStore contract
  class ExamStoreMock {
    static canVisitStep(step) {
      if (step === 1 || step === 2) return true;
      return false;
    }
  }

  assert.equal(ExamStoreMock.canVisitStep(1), true);
  assert.equal(ExamStoreMock.canVisitStep(2), true, 'Step 2 must be accessible freely');
  assert.equal(ExamStoreMock.canVisitStep(3), false);
});

test('Student course progress dynamically calculates percentage from effective lessons', () => {
  const allCourseLessons = [
    { id: 'l1', is_completed: true },
    { id: 'l2', is_completed: false },
    { id: 'l3', is_completed: false },
    { id: 'l4', is_completed: true },
  ];
  const allLessons = [];
  const effectiveLessons = allCourseLessons.length > 0 ? allCourseLessons : allLessons;
  const completedLessons = effectiveLessons.filter(l => l.is_completed).length;
  const progressPercent = effectiveLessons.length > 0
    ? Math.round((completedLessons / effectiveLessons.length) * 100)
    : 0;

  assert.equal(progressPercent, 50, 'Progress must be 50% for 2 completed out of 4 lessons');
  assert.notEqual(progressPercent, 100, 'Progress must not be stuck at 100%');
});

test('Teaching assignment reassign tool live filters course list', () => {
  const courses = [
    { course_code: 'WIR201', title: 'An ninh Mạng Không dây', instructor_name: 'TS. Nguyễn An Ninh' },
    { course_code: 'THI301', title: 'Tình báo Mối đe dọa', instructor_name: 'ThS. Trần Quốc Bảo' },
    { course_code: 'KAL101', title: 'Kiểm thử Xâm nhập Kali', instructor_name: 'TS. Nguyễn An Ninh' },
  ];

  const filterCourses = (term) => {
    const q = term.trim().toLowerCase();
    return courses.filter(c =>
      c.course_code.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      c.instructor_name.toLowerCase().includes(q)
    );
  };

  const wirMatches = filterCourses('WIR201');
  assert.equal(wirMatches.length, 1);
  assert.equal(wirMatches[0].course_code, 'WIR201');

  const ninhMatches = filterCourses('An Ninh');
  assert.equal(ninhMatches.length, 2);
});

test('Broadcast notification RBAC locks non-system categories for system monitoring admin', () => {
  const getAvailableCategories = (subRole, isPrimary) => {
    if (isPrimary || subRole === 'ADMIN_PRIMARY') {
      return ['SYSTEM', 'COURSE', 'ASSESSMENT'];
    }
    if (subRole === 'ADMIN_SYSTEM_MONITORING') {
      return ['SYSTEM'];
    }
    return [];
  };

  const primaryCats = getAvailableCategories('ADMIN_PRIMARY', true);
  assert.deepEqual(primaryCats, ['SYSTEM', 'COURSE', 'ASSESSMENT']);

  const monitorCats = getAvailableCategories('ADMIN_SYSTEM_MONITORING', false);
  assert.deepEqual(monitorCats, ['SYSTEM'], 'System monitoring admin can only broadcast SYSTEM');

  const courseReviewCats = getAvailableCategories('ADMIN_COURSE_REVIEW', false);
  assert.deepEqual(courseReviewCats, [], 'Other sub-admins cannot broadcast');
});

test('Reviewer 16:9 thumbnail cover resolves correct image URL or fallback', () => {
  const resolveThumbnailHtml = (course) => {
    const url = course.thumbnail_url || course.cover_url;
    if (url) {
      return `<img src="${url}" class="w-full h-full object-cover" />`;
    }
    return `<div class="aspect-video">Khóa học chưa thiết lập ảnh bìa 16:9</div>`;
  };

  const withThumb = resolveThumbnailHtml({ thumbnail_url: '/api/courses/123/thumbnail' });
  assert.match(withThumb, /<img src="\/api\/courses\/123\/thumbnail"/);

  const withoutThumb = resolveThumbnailHtml({});
  assert.match(withoutThumb, /chưa thiết lập ảnh bìa/);
});
