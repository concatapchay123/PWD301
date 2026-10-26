"""Bounded offline TeX-to-vector rendering for ReportLab, including mixed inline text."""

from __future__ import annotations

import io
import json
import logging
import os
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from defusedxml import ElementTree
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable, Paragraph

try:
    from svglib.svglib import svg2rlg
except ImportError:
    svg2rlg = None

_MATH = re.compile(r"(?<!\\)(?:\$\$(.*?)\$\$|\$(.*?)\$|\\\((.*?)\\\)|\\\[(.*?)\\\])", re.DOTALL)
_FORBIDDEN = re.compile(
    r"\\(?:href|url|html\w*|require|includegraphics|input|include|write|openout|read|usepackage|class|style)\b",
    re.I,
)
_RENDERER = (
    Path(__file__).resolve().parents[3] / "tools" / "pdf-math" / "render.cjs"
    if (Path(__file__).resolve().parents[3] / "tools" / "pdf-math" / "render.cjs").is_file()
    else Path(__file__).resolve().parents[2] / "tools" / "pdf-math" / "render.cjs"
)


def _formula(match: re.Match[str]) -> str:
    return next(group for group in match.groups() if group is not None)


def _render_batch(formulas: tuple[str, ...]) -> list[bytes]:
    if not formulas:
        return []
    if len(formulas) > 256 or any(
        len(value) > 4096 or _FORBIDDEN.search(value) for value in formulas
    ):
        raise ValueError(
            "Math input exceeds the safe rendering limits or contains external content."
        )
    payload = json.dumps(formulas, ensure_ascii=False).encode("utf-8")
    if len(payload) > 524288:
        raise ValueError("Math input exceeds the safe rendering limits.")
    node = shutil.which("node")
    if not node:
        raise RuntimeError("The offline PDF math runtime is unavailable.")
    try:
        result = subprocess.run(
            [node, "--max-old-space-size=96", str(_RENDERER)],
            input=payload,
            capture_output=True,
            timeout=10,
            check=False,
            cwd=_RENDERER.parent,
            env={
                key: value
                for key, value in os.environ.items()
                if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG"}
            },
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise RuntimeError("The offline PDF math renderer could not complete.") from exc
    if result.returncode or len(result.stdout) > 8388608:
        raise ValueError("A math expression could not be rendered safely.")
    values = json.loads(result.stdout)
    if len(values) != len(formulas):
        raise RuntimeError("The offline PDF math renderer returned an incomplete batch.")
    output = []
    for value in values:
        encoded = value.encode("utf-8")
        if len(encoded) > 262144:
            raise ValueError("A rendered math expression exceeds the safe size limit.")
        root = ElementTree.fromstring(encoded)
        for element in root.iter():
            tag = element.tag.rsplit("}", 1)[-1]
            if tag not in {
                "svg",
                "g",
                "path",
                "rect",
                "line",
                "polygon",
                "polyline",
                "circle",
                "ellipse",
                "defs",
                "use",
                "title",
                "text",
                "tspan",
            }:
                raise ValueError("The rendered math contains unsupported SVG content.")
            if any(
                (name.rsplit("}", 1)[-1] == "href" and not target.startswith("#"))
                or name.lower().startswith("on")
                for name, target in element.attrib.items()
            ):
                raise ValueError("External SVG content is forbidden.")
        output.append(encoded)
    return output


@lru_cache(maxsize=64)
def render_math_svg(expression: str) -> bytes:
    """Render a single formula; only bounded generated paths enter the SVG converter."""
    return _render_batch((expression,))[0]


logger = logging.getLogger(__name__)


def prepare_math(values: list[str]) -> dict[str, bytes]:
    """Render a document's formulas in one process rather than one process per cell.

    Provides a resilient fallback: if the Node.js MathJax renderer is unavailable
    (e.g., node_modules not yet installed), returns an empty mapping so paragraphs
    fall back cleanly to text instead of failing the entire PDF document generation.
    """
    formulas = tuple(
        dict.fromkeys(_formula(match) for value in values for match in _MATH.finditer(value))
    )
    if not formulas:
        return {}
    try:
        return dict(zip(formulas, _render_batch(formulas), strict=True))
    except Exception as exc:
        logger.warning("Offline PDF math renderer unavailable; falling back to text: %s", exc)
        return {}


def _drawing(
    expression: str, font_size: float, font_name: str, rendered: dict[str, bytes] | None
) -> tuple[Any, float]:
    svg = (
        rendered[expression]
        if rendered is not None and expression in rendered
        else render_math_svg(expression)
    )
    root = ElementTree.fromstring(svg)
    width = float(root.attrib["width"].removesuffix("ex")) * font_size * 0.5
    height = float(root.attrib["height"].removesuffix("ex")) * font_size * 0.5
    baseline = re.search(r"vertical-align:\s*(-?[\d.]+)ex", root.attrib.get("style", ""))
    descent = max(0.0, -float(baseline.group(1)) * font_size * 0.5) if baseline else 0.0
    root.set("width", f"{width}pt")
    root.set("height", f"{height}pt")
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] in {"text", "tspan"}:
            element.set("font-family", font_name)
    # svglib documents file-like input, although its published annotation omits it.
    if svg2rlg is None:
        raise RuntimeError("svglib is not installed or available.")
    drawing = svg2rlg(cast(Any, io.BytesIO(ElementTree.tostring(root))), resolve_entities=False)
    if drawing is None or width <= 0 or height <= 0 or max(width, height) > 20000:
        raise ValueError("Invalid formula dimensions.")
    return drawing, descent


class _MathParagraph(Flowable):
    def __init__(self, tokens: list[tuple[Any, ...]], style: Any, lines: Any = None):
        super().__init__()
        self.tokens, self.style, self.fixed_lines = tokens, style, lines
        self.lines: list[Any] = []

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = max(1.0, availWidth)
        if self.fixed_lines is not None:
            self.lines = self.fixed_lines
        else:
            self.lines = []
            current: list[Any] = []
            occupied = 0.0
            ascent, descent = self.style.fontSize * 0.8, self.style.fontSize * 0.2

            def finish() -> None:
                nonlocal current, occupied, ascent, descent
                line_height = max(float(self.style.leading), ascent + descent + 2)
                self.lines.append((current, line_height, ascent, descent))
                current, occupied = [], 0.0
                ascent, descent = self.style.fontSize * 0.8, self.style.fontSize * 0.2

            for kind, content, width, height, below in self.tokens:
                if kind == "newline":
                    finish()
                    continue
                scale = min(1.0, self.width / width) if width > 0 else 1.0
                token_width = width * scale
                if current and occupied + token_width > self.width + 0.01:
                    finish()
                if kind == "text" and not current and content.isspace():
                    continue
                current.append((kind, content, occupied, scale, below))
                occupied += token_width
                ascent = max(ascent, (height - below) * scale)
                descent = max(descent, below * scale)
            if current or not self.lines:
                finish()
        self.height = sum(line[1] for line in self.lines)
        return self.width, self.height

    def split(self, availWidth: float, availHeight: float) -> list[Flowable]:
        self.wrap(availWidth, availHeight)
        consumed, count = 0.0, 0
        for line in self.lines:
            if consumed + line[1] > availHeight:
                break
            consumed += line[1]
            count += 1
        if count == 0 or count == len(self.lines):
            return []
        return [
            _MathParagraph([], self.style, self.lines[:count]),
            _MathParagraph([], self.style, self.lines[count:]),
        ]

    def draw(self) -> None:
        canvas = self.canv
        canvas.setFont(self.style.fontName, self.style.fontSize)
        canvas.setFillColor(self.style.textColor)
        top = self.height
        for tokens, line_height, ascent, _descent in self.lines:
            baseline = top - ascent
            for kind, content, x, scale, below in tokens:
                if kind == "math":
                    canvas.saveState()
                    canvas.translate(x, baseline - below * scale)
                    canvas.scale(scale, scale)
                    content.drawOn(canvas, 0, 0)
                    canvas.restoreState()
                else:
                    canvas.saveState()
                    canvas.translate(x, baseline)
                    canvas.scale(scale, 1)
                    canvas.drawString(0, 0, content)
                    canvas.restoreState()
            top -= line_height


def math_paragraph(value: str, style: Any, rendered: dict[str, bytes] | None = None) -> Flowable:
    from html import escape

    matches = list(_MATH.finditer(value))
    if not matches or svg2rlg is None:
        return Paragraph(escape(value).replace("\n", "<br/>"), style)
    try:
        tokens = []

        def plain(text: str) -> None:
            for word in re.findall(r"\n|[^\S\n]+|[^\s]+", text):
                width = pdfmetrics.stringWidth(word, style.fontName, style.fontSize)
                tokens.append(
                    (
                        "newline" if word == "\n" else "text",
                        word,
                        width,
                        style.fontSize,
                        style.fontSize * 0.2,
                    )
                )

        position = 0
        for match in matches:
            plain(value[position : match.start()])
            drawing, descent = _drawing(_formula(match), style.fontSize, style.fontName, rendered)
            tokens.append(("math", drawing, drawing.width, drawing.height, descent))
            position = match.end()
        plain(value[position:])
        return _MathParagraph(tokens, style)
    except Exception:
        return Paragraph(escape(value).replace("\n", "<br/>"), style)
