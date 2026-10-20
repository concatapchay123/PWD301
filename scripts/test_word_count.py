import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.course_data.chapter1_tor import LESSONS
from scripts.course_data.common import count_vietnamese_words

for l in LESSONS:
    wc = count_vietnamese_words(l['markdown_content'])
    print(f"{l['title']}: {wc} words")
