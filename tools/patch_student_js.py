"""Patch student.js to add both certificate download and HTML preview buttons."""

from __future__ import annotations

import os

FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "assets", "js", "views", "student.js")

with open(FILE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

target = "<span>Chứng chỉ khóa học</span>"
assert target in text, "Target string '<span>Chứng chỉ khóa học</span>' not found"

old_block = """                  <span class="material-symbols-outlined text-[18px]">workspace_premium</span>

                  <span>Chứng chỉ khóa học</span>

                </button>

              </div>

            `;

            const certBtn = document.getElementById('btn-download-course-certificate');

            if (certBtn) {

              certBtn.onclick = (e) => {

                e?.stopPropagation?.();

                e?.preventDefault?.();

                UI.showToast('Đang tạo và tải chứng chỉ khóa học PDF...', 'info');

                const link = document.createElement('a');

                link.href = `/student/courses/${courseId}/certificate`;

                link.download = `Chung_Chi_Khoa_Hoc_${courseId}.pdf`;

                link.target = '_blank';

                document.body.appendChild(link);

                link.click();

                link.remove();

              };

            }"""

new_block = """                  <span class="material-symbols-outlined text-[18px]">workspace_premium</span>

                  <span>Tải Chứng chỉ PDF</span>

                </button>

                <button type="button" id="btn-view-course-certificate" class="w-full py-2 px-3 rounded-xl border border-emerald-600/30 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 text-xs font-medium transition-all flex items-center justify-center gap-1.5 cursor-pointer">

                  <span class="material-symbols-outlined text-[16px]">visibility</span>

                  <span>Xem trước Chứng chỉ HTML</span>

                </button>

              </div>

            `;

            const certBtn = document.getElementById('btn-download-course-certificate');

            if (certBtn) {

              certBtn.onclick = (e) => {

                e?.stopPropagation?.();

                e?.preventDefault?.();

                UI.showToast('Đang tạo và tải chứng chỉ khóa học PDF...', 'info');

                const link = document.createElement('a');

                link.href = `/student/courses/${courseId}/certificate`;

                link.download = `Chung_Chi_Khoa_Hoc_${courseId}.pdf`;

                link.target = '_blank';

                document.body.appendChild(link);

                link.click();

                link.remove();

              };

            }

            const viewCertBtn = document.getElementById('btn-view-course-certificate');

            if (viewCertBtn) {

              viewCertBtn.onclick = (e) => {

                e?.stopPropagation?.();

                e?.preventDefault?.();

                window.open(`/student/courses/${courseId}/certificate?format=html`, '_blank');

              };

            }"""

assert old_block in text, "old_block not found in student.js"
updated = text.replace(old_block, new_block, 1)

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(updated)

print("[OK] Successfully patched student.js with both download and HTML view buttons!")
