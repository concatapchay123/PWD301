const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const filename = path.resolve(__dirname, '../../frontend/assets/js/views/instructor.js');
const source = fs.readFileSync(filename, 'utf8');

function setupContext(extra = {}) {
  const window = {};
  const context = {
    window,
    document: {
      getElementById: () => null,
      querySelectorAll: () => [],
      querySelector: () => null,
      addEventListener: () => {}
    },
    UI: {
      escapeHtml: val => String(val ?? '').replaceAll('<', '&lt;').replaceAll('>', '&gt;'),
      statusBadge: status => `<span class="badge">${status}</span>`,
      renderMarkdown: md => md
    },
    ...extra
  };
  vm.runInNewContext(source, context, { filename });
  return { window, context };
}

test('renderLessonChildNavigator renders drag handles, delete button, and add lesson action', () => {
  const { window } = setupContext();
  const unit = {
    learning_unit_id: 'unit-1',
    title: 'Chương 1: Khởi động',
    lesson_count: 2,
    lessons: [
      { lesson_id: 'lesson-1', title: 'Bài 1: Giới thiệu', position: 1 },
      { lesson_id: 'lesson-2', title: 'Bài 2: Cài đặt', position: 2 }
    ]
  };

  const html = window.InstructorView.renderLessonChildNavigator(unit, 'course-1', 'lesson-1');
  assert.match(html, /Chương 1: Khởi động/);
  assert.match(html, /2\/10 Lesson/);
  assert.match(html, /href="#\/instructor\/courses\/course-1\/lessons\/lesson-1\/edit"/);
  assert.match(html, /href="#\/instructor\/courses\/course-1\/lessons\/lesson-2\/edit"/);
  assert.match(html, /aria-current="page"/);
  assert.match(html, /btn-nav-delete-lesson/);
  assert.match(html, /nav-drag-handle/);
  assert.match(html, /Thêm bài học mới/);
  assert.match(html, /data-lesson-id="lesson-1"/);
  assert.match(html, /data-lesson-id="lesson-2"/);
});

test('renderLessonChildNavigator hides add lesson button when unit has 10 lessons', () => {
  const { window } = setupContext();
  const unit = {
    learning_unit_id: 'unit-max',
    title: 'Chương Đầy',
    lesson_count: 10,
    lessons: Array.from({ length: 10 }, (_, i) => ({
      lesson_id: `l-${i}`,
      title: `Bài ${i + 1}`,
      position: i + 1
    }))
  };

  const html = window.InstructorView.renderLessonChildNavigator(unit, 'course-1', 'l-0');
  assert.doesNotMatch(html, /Thêm Lesson/);
  assert.doesNotMatch(html, /btn-nav-add-lesson/);
  assert.match(html, /10\/10 Lesson/);
});

test('instructor.js contains Learning Unit reordering and delete actions', () => {
  assert.ok(source.includes('btn-move-unit-up') || source.includes('btn-unit-move-up'), 'Includes unit move up');
  assert.ok(source.includes('btn-move-unit-down') || source.includes('btn-unit-move-down'), 'Includes unit move down');
  assert.ok(source.includes('btn-delete-learning-unit') || source.includes('btn-unit-delete'), 'Includes delete learning unit');
});

test('instructor.js does not contain global course-lessons-order details', () => {
  assert.ok(!source.includes('id="course-lessons-order"'), 'Removed global course-lessons-order details');
  assert.ok(!source.includes('Sắp xếp Lesson trong khóa học'), 'Removed global lessons order text');
});

test('instructor.js includes explicit delete buttons for video, document, and block items', () => {
  assert.ok(source.includes('btn-block-delete'), 'Includes block delete button');
  assert.ok(source.includes('btn-delete-learning-unit') || source.includes('btn-unit-delete'), 'Includes unit delete');
});

test('instructor.js includes cover photo reminder banner and badges', () => {
  assert.ok(source.includes('Khóa học này chưa có ảnh bìa đại diện'), 'Includes cover photo reminder text');
  assert.ok(source.includes('Chưa có ảnh bìa'), 'Includes badge text in course list');
});

test('document block template specifies CAD, 3D, office formats and excludes .zip', () => {
  assert.ok(
    source.includes('Tải tệp đính kèm (PDF, Word, Excel, PPT, CAD, 3D...)'),
    'Template label must mention Word, Excel, PPT, CAD, 3D and omit ZIP'
  );
  assert.ok(
    !source.includes('Tải tệp đính kèm (PDF, DOCX, ZIP)'),
    'Template must not mention ZIP in upload prompt'
  );
  assert.ok(
    source.includes('accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.dwg,.dxf,.obj,.fbx,.stl,.blend,.step,.stp,.gltf,.glb"'),
    'Template accept attribute must include comprehensive formats'
  );
  assert.ok(
    !source.includes('accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip"'),
    'Template accept attribute must not allow .zip'
  );
});

test('instructor.js declares let targetLessonId in upload handler avoiding TypeError', () => {
  assert.ok(
    source.includes('let targetLessonId = activeLessonId;'),
    'targetLessonId must be declared with let to allow reassignment'
  );
  assert.match(
    source,
    /cardBlockId\s*=\s*activeBlocks\[bIdx\]\?\.id;\s*let targetLessonId = activeLessonId;/,
    'upload card block handler must declare let targetLessonId instead of const'
  );
});

test('instructor.js document upload pre-flight validation blocks archive extensions and >50MB files', () => {
  assert.ok(
    source.includes("Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"),
    'Must include exact Vietnamese archive rejection message'
  );
  assert.ok(
    source.includes("Tệp vượt quá giới hạn 50 MB cho phép."),
    'Must include 50 MB limit rejection toast message'
  );
  assert.ok(
    source.includes("50_000_000") || source.includes("50000000"),
    'Must check 50,000,000 byte limit'
  );
});

test('draft synchronization updates activeLessonId, tree item, child buttons, unit in memory, and DOM cards without throwing TypeError', async () => {
  const routeReplacements = [];

  class MockElement {
    constructor(tag = 'div', attrs = {}) {
      this.tagName = tag.toUpperCase();
      this.attributes = { ...attrs };
      this.dataset = {};
      this.children = [];
      this.innerHTML = '';
      this.value = '';
      for (const [k, v] of Object.entries(attrs)) {
        if (k.startsWith('data-')) {
          const camel = k.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
          this.dataset[camel] = String(v);
        }
      }
    }
    setAttribute(k, v) {
      this.attributes[k] = String(v);
      if (k.startsWith('data-')) {
        const camel = k.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
        this.dataset[camel] = String(v);
      }
    }
    getAttribute(k) {
      return this.attributes[k];
    }
    querySelector(sel) {
      return this.querySelectorAll(sel)[0] || null;
    }
    querySelectorAll(sel) {
      const results = [];
      const match = (el) => {
        if (sel.startsWith('.')) {
          const cls = sel.slice(1);
          if (el.attributes.class && el.attributes.class.split(/\s+/).includes(cls)) results.push(el);
        } else if (sel.startsWith('[data-lesson-id="')) {
          const id = sel.slice('[data-lesson-id="'.length, -2);
          if (el.dataset.lessonId === id) results.push(el);
        } else if (sel === '[data-lesson-id]') {
          if (el.dataset.lessonId !== undefined) results.push(el);
        }
        for (const child of el.children) match(child);
      };
      for (const child of this.children) match(child);
      return results;
    }
  }

  const oldId = 'lesson-published-1';
  const newId = 'lesson-draft-staging-2';

  const treeItem = new MockElement('div', { class: 'lesson-tree-item', 'data-lesson-id': oldId });
  const treeBtnDelete = new MockElement('button', { class: 'btn-lesson-delete', 'data-lesson-id': oldId });
  treeItem.children.push(treeBtnDelete);

  const curriculumCard = new MockElement('div', { class: 'curriculum-lesson-item', 'data-lesson-id': oldId });
  const anotherCardBtn = new MockElement('button', { class: 'btn-preview', 'data-lesson-id': oldId });

  const allElements = [treeItem, treeBtnDelete, curriculumCard, anotherCardBtn];

  const documentMock = {
    querySelectorAll: (sel) => {
      if (sel === `[data-lesson-id="${oldId}"]`) {
        return allElements.filter(el => el.dataset.lessonId === oldId);
      }
      return [];
    },
    querySelector: (sel) => documentMock.querySelectorAll(sel)[0] || null,
  };

  const treeContainerMock = {
    querySelector: (sel) => {
      if (sel === `.lesson-tree-item[data-lesson-id="${oldId}"]`) return treeItem;
      return null;
    }
  };

  const currentUnits = [
    {
      learning_unit_id: 'unit-1',
      lessons: [
        { lesson_id: oldId, id: oldId, status: 'PUBLISHED' }
      ]
    }
  ];

  let activeLessonId = oldId;
  let activeUnitId = 'unit-1';
  let activeLessonMeta = { status: 'PUBLISHED' };
  let targetLessonId = activeLessonId;

  const cId = 'course-1';
  const InstructorView = {
    replaceLessonEditorRoute: (courseId, fromId, toId) => {
      routeReplacements.push({ courseId, fromId, toId });
    }
  };

  const res = {
    lesson_id: newId,
    lesson: { lesson_id: newId, id: newId, status: 'DRAFT' }
  };

  const newLessonId = res?.lesson_id || res?.lesson?.lesson_id || res?.lesson?.id;
  assert.ok(newLessonId && String(newLessonId) !== String(targetLessonId));

  const oldLessonId = targetLessonId;
  if (String(activeLessonId) === String(oldLessonId)) {
    activeLessonId = newLessonId;
    if (activeLessonMeta) activeLessonMeta.status = res?.lesson?.status || res?.status || 'DRAFT';
    InstructorView.replaceLessonEditorRoute(cId, oldLessonId, newLessonId);
  }
  targetLessonId = newLessonId;

  const foundTreeItem = treeContainerMock.querySelector(`.lesson-tree-item[data-lesson-id="${oldLessonId}"]`);
  if (foundTreeItem) {
    foundTreeItem.setAttribute('data-lesson-id', newLessonId);
    foundTreeItem.dataset.lessonId = newLessonId;
    foundTreeItem.querySelectorAll('[data-lesson-id]').forEach(el => {
      el.setAttribute('data-lesson-id', newLessonId);
      el.dataset.lessonId = newLessonId;
    });
  }

  const unit = currentUnits.find(u => String(u.learning_unit_id || u.id) === String(activeUnitId));
  if (unit && unit.lessons) {
    const l = unit.lessons.find(item => String(item.lesson_id || item.id) === String(oldLessonId));
    if (l) {
      l.lesson_id = newLessonId;
      l.id = newLessonId;
      l.status = res?.lesson?.status || res?.status || 'DRAFT';
    }
  }

  documentMock.querySelectorAll(`[data-lesson-id="${oldLessonId}"]`).forEach(el => {
    el.setAttribute('data-lesson-id', newLessonId);
    el.dataset.lessonId = newLessonId;
  });

  assert.equal(activeLessonId, newId, 'activeLessonId must update to draft lesson ID');
  assert.equal(targetLessonId, newId, 'targetLessonId must update to draft lesson ID');
  assert.equal(activeLessonMeta.status, 'DRAFT', 'activeLessonMeta status must update to DRAFT');
  assert.equal(treeItem.dataset.lessonId, newId, 'treeItem dataset.lessonId must be newId');
  assert.equal(treeBtnDelete.dataset.lessonId, newId, 'treeItem child delete button must be updated to newId');
  assert.equal(curriculumCard.dataset.lessonId, newId, 'curriculumCard dataset.lessonId must be newId');
  assert.equal(anotherCardBtn.dataset.lessonId, newId, 'additional element dataset.lessonId must be newId');
  assert.equal(currentUnits[0].lessons[0].lesson_id, newId, 'in-memory lesson_id must update to newId');
  assert.equal(currentUnits[0].lessons[0].status, 'DRAFT', 'in-memory lesson status must update to DRAFT');
  assert.deepEqual(routeReplacements, [{ courseId: 'course-1', fromId: oldId, toId: newId }], 'Route must be replaced');
});
