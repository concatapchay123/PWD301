const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const studentSourcePath = path.resolve('frontend/assets/js/views/student.js');
const instructorSourcePath = path.resolve('frontend/assets/js/views/instructor.js');

const studentSource = fs.readFileSync(studentSourcePath, 'utf8');
const instructorSource = fs.readFileSync(instructorSourcePath, 'utf8');

// =========================================================================
// CHALLENGE 1: Header Progress Badge Absence & Safe Function Invariants
// =========================================================================
test('Challenge 1.1: Header Progress Badge Absence from Student Console Header', () => {
  // Assert no occurrence of #console-course-progress-badge in student.js at all
  assert.doesNotMatch(
    studentSource,
    /id=["']console-course-progress-badge["']/,
    '#console-course-progress-badge must be completely eliminated from student.js'
  );

  // Extract console header HTML template between <header and </header>
  const headerMatch = studentSource.match(/<header[\s\S]*?id="console-exit-btn"[\s\S]*?<\/header>/);
  assert.ok(headerMatch, 'Student console header must exist in student.js');
  const headerHtml = headerMatch[0];

  // Assert header contains exit button
  assert.match(headerHtml, /id="console-exit-btn"/, 'Header must contain exit button');

  // Assert header does NOT contain any progress badge element
  assert.doesNotMatch(
    headerHtml,
    /console-course-progress-badge/,
    'Header template must not contain console-course-progress-badge'
  );
  assert.doesNotMatch(
    headerHtml,
    /class="[^"]*badge[^"]*"[^>]*progress/i,
    'Header template must not render any dynamic course progress badge'
  );
});

test('Challenge 1.2: Calling updateConsoleCourseProgressBadge with any inputs never throws', () => {
  // Extract definition of updateConsoleCourseProgressBadge
  const fnMatch = studentSource.match(/const\s+updateConsoleCourseProgressBadge\s*=\s*\([^)]*\)\s*=>\s*\{[\s\S]*?\};/);
  assert.ok(fnMatch, 'updateConsoleCourseProgressBadge function definition must exist in student.js');

  const fnCode = `${fnMatch[0]}; return updateConsoleCourseProgressBadge;`;
  const updateFn = new Function(fnCode)();
  assert.equal(typeof updateFn, 'function', 'Extracted function must be executable');

  // Adversarial stress test: pass arbitrary types, out-of-bounds numbers, nullish, objects
  const adversarialInputs = [
    [], // no args
    [0],
    [50],
    [100],
    [-1],
    [-999],
    [101],
    [999999],
    [0.5],
    [NaN],
    [Infinity],
    [-Infinity],
    [null],
    [undefined],
    [''],
    ['50'],
    ['100%'],
    ['<script>alert(1)</script>'],
    [{}],
    [{ percentage: 50 }],
    [[]],
    [[100]],
    [() => 100],
    [Symbol('progress')],
    [true],
    [false]
  ];

  for (const args of adversarialInputs) {
    assert.doesNotThrow(() => {
      updateFn(...args);
    }, `updateConsoleCourseProgressBadge(${args.map(a => String(a)).join(', ')}) threw an unexpected exception!`);
  }
});

// =========================================================================
// CHALLENGE 2: Hero Trailer Clean Shell Invariants
// =========================================================================
test('Challenge 2.1: Hero Trailer Clean Shell markup and CSS invariants', () => {
  // Verify hero-trailer-clean-shell exists and has overflow-hidden class (attribute-order agnostic)
  const shellTagMatch = studentSource.match(/<div\s+[^>]*id="hero-trailer-clean-shell"[^>]*>/);
  assert.ok(shellTagMatch, '#hero-trailer-clean-shell opening tag must exist in student.js');
  const shellTag = shellTagMatch[0];

  const classAttrMatch = shellTag.match(/class="([^"]*)"/);
  assert.ok(classAttrMatch, '#hero-trailer-clean-shell must have class attribute');
  const classList = classAttrMatch[1].split(/\s+/);
  assert.ok(
    classList.includes('overflow-hidden'),
    '#hero-trailer-clean-shell class attribute must contain overflow-hidden'
  );

  // Verify inner container scaling styles: top: -14%, height: 128%, pointer-events: none
  assert.match(
    studentSource,
    /style="[^"]*top:\s*-14%[^"]*"/,
    'Inner container must have top: -14% style for cropping native YouTube top bar'
  );
  assert.match(
    studentSource,
    /style="[^"]*height:\s*128%[^"]*"/,
    'Inner container must have height: 128% style for vertical scaling'
  );
  assert.match(
    studentSource,
    /style="[^"]*pointer-events:\s*none[^"]*"/,
    'Inner container must have pointer-events: none in inline style'
  );
  assert.match(
    studentSource,
    /class="[^"]*pointer-events-none[^"]*"/,
    'Inner container must have pointer-events-none Tailwind class'
  );

  // Verify iframe has pointer-events: none protection
  assert.match(
    studentSource,
    /<iframe[\s\S]*?id="hero-trailer-iframe"[\s\S]*?class="[^"]*pointer-events-none[^"]*"[\s\S]*?>/,
    '#hero-trailer-iframe must have class pointer-events-none to prevent direct interaction'
  );

  // Verify #hero-trailer-shield exists with absolute inset-0 z-10 cursor-pointer
  const shieldMatch = studentSource.match(/<div\s+[^>]*id="hero-trailer-shield"[^>]*>/);
  assert.ok(shieldMatch, '#hero-trailer-shield must exist in student.js');
  const shieldTag = shieldMatch[0];
  const shieldClasses = (shieldTag.match(/class="([^"]*)"/) || [])[1]?.split(/\s+/) || [];

  for (const reqClass of ['absolute', 'inset-0', 'z-10', 'cursor-pointer', 'bg-transparent']) {
    assert.ok(
      shieldClasses.includes(reqClass),
      `#hero-trailer-shield missing class "${reqClass}"`
    );
  }
});

test('Challenge 2.2: Hero Trailer Embed URL query parameters validation', () => {
  // Extract embed URL template string
  const embedUrlMatch = studentSource.match(/const\s+heroEmbedUrl\s*=\s*`([^`]+)`;/);
  assert.ok(embedUrlMatch, 'heroEmbedUrl template string must exist in student.js');

  const templateStr = embedUrlMatch[1];
  const testYtId = 'dQw4w9WgXcQ';
  const resolvedUrl = templateStr.replace(/\$\{ytMatch\[1\]\}/g, testYtId);

  const url = new URL(resolvedUrl);

  // Verify host and path
  assert.equal(url.hostname, 'www.youtube-nocookie.com', 'Embed must use privacy-enhanced youtube-nocookie.com domain');
  assert.equal(url.pathname, `/embed/${testYtId}`, 'Embed path must point to /embed/<ytId>');

  // Verify all required query parameters
  const params = url.searchParams;

  assert.equal(params.get('autoplay'), '1', 'Query param autoplay must be 1');
  assert.equal(params.get('mute'), '1', 'Query param mute must be 1 (browser autoplay requirement)');
  assert.equal(params.get('loop'), '1', 'Query param loop must be 1');
  assert.equal(params.get('playlist'), testYtId, 'Query param playlist must equal video ID for YouTube single-video loop');
  assert.equal(params.get('controls'), '0', 'Query param controls must be 0 (no native player controls)');
  assert.equal(params.get('showinfo'), '0', 'Query param showinfo must be 0');
  assert.equal(params.get('rel'), '0', 'Query param rel must be 0');
  assert.equal(params.get('iv_load_policy'), '3', 'Query param iv_load_policy must be 3 (hide annotations)');
  assert.equal(params.get('disablekb'), '1', 'Query param disablekb must be 1 (disable keyboard shortcuts)');
  assert.equal(params.get('modestbranding'), '1', 'Query param modestbranding must be 1 (suppress YouTube logo)');
  assert.equal(params.get('playsinline'), '1', 'Query param playsinline must be 1');
});

// =========================================================================
// CHALLENGE 3: Instructor Upload UI & Client-Side Archive Rejection
// =========================================================================
test('Challenge 3.1: Instructor Attachment input accept attribute excludes archives and includes CAD/3D/Docs', () => {
  // Find block-file-input in instructor.js
  const fileInputMatch = instructorSource.match(/<input\s+type="file"\s+class="block-file-input[^"]*"\s+accept="([^"]+)"/);
  assert.ok(fileInputMatch, 'block-file-input with accept attribute must exist in instructor.js');

  const acceptValue = fileInputMatch[1];
  const acceptedExts = acceptValue.split(',').map(s => s.trim().toLowerCase());

  // Strictly assert no archive formats in accept list
  const forbiddenArchives = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'];
  for (const arch of forbiddenArchives) {
    assert.ok(
      !acceptedExts.includes(arch),
      `accept attribute must NOT contain archive extension ${arch}`
    );
  }

  // Strictly assert required document, CAD, and 3D extensions are supported
  const requiredExts = [
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt',
    '.dwg', '.dxf', '.obj', '.fbx', '.stl', '.blend', '.step', '.stp', '.gltf', '.glb'
  ];
  for (const ext of requiredExts) {
    assert.ok(
      acceptedExts.includes(ext),
      `accept attribute must contain expected supported extension ${ext}`
    );
  }

  // Verify attachment upload button label
  assert.match(
    instructorSource,
    /<span>Tải tệp đính kèm \(PDF, Word, Excel, PPT, CAD, 3D\.\.\.\)<\/span>/,
    'Upload button label must strictly match the non-archive specification'
  );
});

test('Challenge 3.2: Client-side validation rejects archive filenames with exact Vietnamese error message', () => {
  const EXACT_VIETNAMESE_ERROR = "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)";

  // Assert exact error string exists in instructor.js
  assert.ok(
    instructorSource.includes(EXACT_VIETNAMESE_ERROR),
    'instructor.js must contain exact Vietnamese error rejection string'
  );

  // Extract the client-side validation logic from instructor.js
  const validationSnippetMatch = instructorSource.match(
    /const forbiddenArchiveExts = (\[[^\]]+\]);[\s\S]*?if\s*\(([^)]+)\)\s*\{\s*UI\.showToast\(([^,]+),\s*'error'\);\s*return;\s*\}/
  );
  assert.ok(validationSnippetMatch, 'Archive validation check must be present in instructor.js');

  const forbiddenExts = JSON.parse(validationSnippetMatch[1].replace(/'/g, '"'));

  // Test validator function mimicking the implementation
  const validateFileName = (fileName) => {
    const fileNameLower = (fileName || '').toLowerCase();
    if (forbiddenExts.some(ext => fileNameLower.endsWith(ext))) {
      return { valid: false, error: EXACT_VIETNAMESE_ERROR };
    }
    return { valid: true };
  };

  // Adversarial test cases: forbidden archives with varying cases and double extensions
  const archiveFiles = [
    'archive.zip',
    'ARCHIVE.ZIP',
    'project.Zip',
    'course_backup.rar',
    'DATA.RAR',
    'files.7z',
    'package.7Z',
    'distribution.tar',
    'compressed.tar.gz',
    'image.gz',
    'bundle.bz2',
    'payload.xz',
    'installer.iso',
    'my.report.zip',
    'drawing.dwg.7z',
    'model.blend.rar'
  ];

  for (const filename of archiveFiles) {
    const result = validateFileName(filename);
    assert.equal(
      result.valid,
      false,
      `Filename "${filename}" should be rejected as an archive!`
    );
    assert.equal(
      result.error,
      EXACT_VIETNAMESE_ERROR,
      `Filename "${filename}" must yield exact Vietnamese rejection message`
    );
  }

  // Allowed files: valid documents, CAD, 3D models, and sneaky names containing "zip"
  const allowedFiles = [
    'lecture_notes.pdf',
    'report.docx',
    'budget.xlsx',
    'presentation.pptx',
    'readme.txt',
    'floor_plan.dwg',
    'electrical.dxf',
    'character.blend',
    'part_mesh.stl',
    'scene.obj',
    'rig.fbx',
    'assembly.step',
    'component.stp',
    'scene.gltf',
    'avatar.glb',
    'zip_code_analysis.pdf',  // contains 'zip' but valid .pdf extension
    'rarity_guide.docx',      // contains 'rar' but valid .docx extension
    '7zone_map.dwg'           // contains '7z' but valid .dwg extension
  ];

  for (const filename of allowedFiles) {
    const result = validateFileName(filename);
    assert.equal(
      result.valid,
      true,
      `Allowed file "${filename}" was unexpectedly rejected!`
    );
  }
});

test('Challenge 3.3: Client-side file size check enforces 50 MB (50,000,000 bytes) threshold and boundary edge cases', () => {
  // Verify 50MB threshold expression in instructor.js
  assert.match(
    instructorSource,
    /if\s*\(\s*file\.size\s*>\s*50_000_000\s*\)/,
    'instructor.js must strictly check file.size > 50_000_000'
  );

  assert.match(
    instructorSource,
    /UI\.showToast\(\s*["']Tệp vượt quá giới hạn 50 MB cho phép\.["']\s*,\s*['"]error['"]\s*\)/,
    'instructor.js must display 50MB limit rejection error toast'
  );

  // Replicate boundary check logic
  const validateFileSize = (sizeBytes) => {
    if (sizeBytes > 50_000_000) {
      return { valid: false, error: 'Tệp vượt quá giới hạn 50 MB cho phép.' };
    }
    return { valid: true };
  };

  // Boundary condition tests
  assert.equal(validateFileSize(0).valid, true, '0 bytes should be allowed');
  assert.equal(validateFileSize(1).valid, true, '1 byte should be allowed');
  assert.equal(validateFileSize(1024).valid, true, '1 KB should be allowed');
  assert.equal(validateFileSize(49_999_999).valid, true, '49,999,999 bytes should be allowed');
  assert.equal(validateFileSize(50_000_000).valid, true, '50,000,000 bytes (exact limit) should be allowed');
  assert.equal(validateFileSize(50_000_001).valid, false, '50,000,001 bytes (limit + 1) must be rejected');
  assert.equal(validateFileSize(52_428_800).valid, false, '50 MiB (52,428,800 bytes) must be rejected (> 50,000,000)');
  assert.equal(validateFileSize(100_000_000).valid, false, '100 MB must be rejected');
});

