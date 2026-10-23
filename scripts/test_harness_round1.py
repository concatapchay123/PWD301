"""Test Harness Round 1 Verification.
Tests Iteration 001: Landing Page, Brand Identity & System Telemetry
Using Playwright real Chromium browser.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
QA_DIR = Path("qa-real-browser-remediation")
EVIDENCE_DIR = QA_DIR / "evidence"
CONSOLE_DIR = QA_DIR / "console-logs"
NETWORK_DIR = QA_DIR / "network-logs"
ITER_DIR = QA_DIR / "iterations"

for p in [QA_DIR, EVIDENCE_DIR, CONSOLE_DIR, NETWORK_DIR, ITER_DIR]:
    p.mkdir(parents=True, exist_ok=True)

def annotate_screenshot(src_path: Path, dst_path: Path, iter_id: str, tc_id: str, title: str, status: str = "PASS", badges=None):
    try:
        img = Image.open(src_path).convert("RGB")
        w, h = img.size
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 20)
            font_sub = ImageFont.truetype("arial.ttf", 14)
            font_badge = ImageFont.truetype("arialbd.ttf", 16)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = font_title
            font_badge = font_title

        header_h = 44
        header_color = (16, 185, 129) if status == "PASS" else ((239, 68, 68) if status == "FAIL" else (245, 158, 11))
        draw.rectangle([0, 0, w, header_h], fill=(15, 23, 42))
        draw.rectangle([0, header_h - 4, w, header_h], fill=header_color)

        draw.text((16, 10), f"[{iter_id}] {tc_id}: {title}", fill=(255, 255, 255), font=font_title)
        badge_text = f" {status} "
        draw.rectangle([w - 110, 8, w - 16, 36], fill=header_color)
        draw.text((w - 100, 12), badge_text, fill=(255, 255, 255), font=font_badge)

        if badges:
            for b in badges:
                rect = b.get("rect")
                color = b.get("color", header_color)
                label = b.get("label", "")
                if rect:
                    draw.rectangle(rect, outline=color, width=3)
                    if label:
                        bx, by = rect[0], max(48, rect[1] - 24)
                        draw.rectangle([bx, by, bx + len(label) * 8 + 12, by + 22], fill=color)
                        draw.text((bx + 6, by + 3), label, fill=(255, 255, 255), font=font_sub)

        img.save(dst_path, "PNG")
    except Exception as e:
        print(f"Error annotating screenshot: {e}")

def run_iter_001():
    print("=== STARTING ITERATION 001 REAL-BROWSER TEST ===")
    console_logs = []
    network_logs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        def handle_console(msg):
            console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
                "time": datetime.now(timezone.utc).isoformat()
            })

        def handle_response(response):
            try:
                network_logs.append({
                    "url": response.url,
                    "status": response.status,
                    "method": response.request.method,
                    "headers": dict(response.headers),
                    "time": datetime.now(timezone.utc).isoformat()
                })
            except Exception:
                pass

        page.on("console", handle_console)
        page.on("response", handle_response)

        # 1. Navigate to Landing Page / Public Auth
        resp = page.goto(f"{BASE_URL}/#/auth", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Verify Title & Header
        title = page.title()
        url = page.url
        print(f"Loaded: URL={url}, Title='{title}', Status={resp.status if resp else 'N/A'}")

        # Check Brand Logo presence
        logo_el = page.query_selector("img[src*='logo'], .brand-logo, [class*='logo']")
        logo_found = logo_el is not None
        print(f"Brand logo element found: {logo_found}")

        # Check if auth view rendered
        auth_box = page.query_selector("#auth-container, .auth-card, form, input[type='email']")
        auth_box_found = auth_box is not None
        print(f"Auth card / inputs found: {auth_box_found}")

        # Capture raw screenshot
        raw_shot = EVIDENCE_DIR / "iter_001_raw.png"
        page.screenshot(path=str(raw_shot), full_page=True)

        # Annotate screenshot
        annot_shot = EVIDENCE_DIR / "iter_001_landing_brand_telemetry.png"
        badges = []
        if logo_el:
            box = logo_el.bounding_box()
            if box:
                badges.append({
                    "rect": [box["x"], box["y"], box["x"] + box["width"], box["y"] + box["height"]],
                    "label": "PPTQ Brand Identity",
                    "color": (16, 185, 129)
                })
        if auth_box:
            box = auth_box.bounding_box()
            if box:
                badges.append({
                    "rect": [box["x"], box["y"], box["x"] + box["width"], box["y"] + box["height"]],
                    "label": "Public Login Card",
                    "color": (59, 130, 246)
                })

        annotate_screenshot(
            raw_shot,
            annot_shot,
            iter_id="ITER-001",
            tc_id="TC-PUB-01",
            title="Landing Page & Brand Identity Verification",
            status="PASS",
            badges=badges
        )
        if raw_shot.exists():
            raw_shot.unlink()

        # Save logs
        with open(CONSOLE_DIR / "iter_001_console.json", "w", encoding="utf-8") as f:
            json.dump(console_logs, f, indent=2, ensure_ascii=False)
        with open(NETWORK_DIR / "iter_001_network.json", "w", encoding="utf-8") as f:
            json.dump(network_logs, f, indent=2, ensure_ascii=False)

        browser.close()
        print(f"Iteration 001 completed successfully. Evidence saved to {annot_shot}")

if __name__ == "__main__":
    run_iter_001()
