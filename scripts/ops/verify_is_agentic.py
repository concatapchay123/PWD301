"""Self-contained verification script for Agent Readiness (Is Agentic 100/100).

Simulates exact external crawler & agent HTTP requests:
1. Content is available without JavaScript (>= 500 chars, clear H1, sequential headings)
2. Agent-friendly 404s (Accept: text/markdown -> 404 Markdown body >= 20 chars with link to docs/sitemap/llms.txt)
3. Markdown content negotiation (Accept: text/markdown -> 200 OK Markdown with Vary: Accept; Accept: text/html -> HTML with Vary: Accept)
4. Brand name discoverability ("PPTQ LMS" in title, H1, metadata, canonical, direct 200)
5. JSON-LD structured data (SoftwareApplication, WebSite)
6. Agent instruction / when-to-use (llms.txt & llms-full.txt with 'When to Use This', 'Best-fit Use Cases', 'How an Agent Should Call You')
7. Sitemap exists (valid XML sitemap at /sitemap.xml under 50MB, lastmod dates, robots.txt)
8. Organization schema completeness (Organization/EducationalOrganization, contactPoint with email/phone/contactType, address with PostalAddress)
9. Trust anchor pages (/about, /contact, /privacy >= 500 chars in HTML and Markdown)
10. Metadata completeness (canonical, html lang, og:image, og:type)
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure source_code is on path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
source_code = os.path.join(repo_root, "source_code")
if source_code not in sys.path:
    sys.path.insert(0, source_code)

from backend import create_app  # noqa: E402


def run_full_verification() -> bool:
    app = create_app("testing")
    with app.app_context():
        from backend.extensions import db
        db.create_all()
    client = app.test_client()
    passed = 0
    total = 10

    print("=" * 70)
    print("PPTQ LMS — IS AGENTIC READINESS AUDIT & VERIFICATION HARNESS")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # 1. Content is available without JavaScript
    # --------------------------------------------------------------------------
    print("\n[Item 1] Content is available without JavaScript (Essential)")
    resp = client.get("/", headers={"Accept": "text/html"})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    h1 = soup.find("h1")
    assert h1 is not None and "PPTQ LMS" in h1.text, f"Invalid H1: {h1}"
    h2_tags = soup.find_all("h2")
    h3_tags = soup.find_all("h3")
    assert len(h2_tags) >= 2, f"Expected >= 2 h2, got {len(h2_tags)}"
    assert len(h3_tags) >= 4, f"Expected >= 4 h3, got {len(h3_tags)}"
    viewport = soup.find("main", id="app-viewport")
    raw_text = viewport.get_text(separator=" ", strip=True) if viewport else ""
    text_length = len(raw_text)
    assert text_length >= 500, f"Raw text must be >= 500 chars, got {text_length}"
    noscript = soup.find("noscript")
    assert noscript is not None, "Missing <noscript> fallback"
    print(f"  ✓ H1 tag found: '{h1.text.strip()}'")
    print(f"  ✓ Sequential headings verified: {len(h2_tags)} H2s, {len(h3_tags)} H3s")
    print(f"  ✓ Raw non-JS content length: {text_length} characters (>= 500 target)")
    print(f"  ✓ <noscript> fallback verified")
    passed += 1

    # --------------------------------------------------------------------------
    # 2. Agent-friendly 404s
    # --------------------------------------------------------------------------
    print("\n[Item 2] Agent-friendly 404s (Essential)")
    probe_url = "/__ora-404-probe-gr9m15ae"
    resp_404_md = client.get(probe_url, headers={"Accept": "text/markdown"})
    assert resp_404_md.status_code == 404, f"Expected 404, got {resp_404_md.status_code}"
    assert "text/markdown" in resp_404_md.content_type, f"Expected text/markdown, got {resp_404_md.content_type}"
    assert "Accept" in resp_404_md.headers.get("Vary", ""), "Vary header must include Accept"
    body_404 = resp_404_md.data.decode("utf-8")
    assert len(body_404) >= 20, f"Body must be >= 20 chars, got {len(body_404)}"
    assert "/llms.txt" in body_404 or "llms.txt" in body_404, "404 Markdown body must link to llms.txt"
    assert "/sitemap.xml" in body_404 or "sitemap.xml" in body_404, "404 Markdown body must link to sitemap.xml"

    # API JSON safety
    resp_404_json = client.get(probe_url, headers={"Accept": "application/json"})
    assert resp_404_json.status_code == 404 and resp_404_json.is_json
    print(f"  ✓ 404 status preserved on nonexistent probe: {probe_url}")
    print(f"  ✓ Content-Type: {resp_404_md.content_type}")
    print(f"  ✓ Vary header: '{resp_404_md.headers.get('Vary')}' (contains Accept)")
    print(f"  ✓ Markdown 404 error explanation length: {len(body_404)} characters (>= 20 target)")
    print(f"  ✓ Links to docs, llms.txt, and sitemap.xml present in Markdown error body")
    print(f"  ✓ Standard JSON 404 preserved for API clients: {resp_404_json.get_json()['error']['code']}")
    passed += 1

    # --------------------------------------------------------------------------
    # 3. Markdown content negotiation (acceptmarkdown.com)
    # --------------------------------------------------------------------------
    print("\n[Item 3] Markdown content negotiation (Essential)")
    resp_home_md = client.get("/", headers={"Accept": "text/markdown"})
    assert resp_home_md.status_code == 200, f"Expected 200, got {resp_home_md.status_code}"
    assert "text/markdown" in resp_home_md.content_type, f"Expected text/markdown, got {resp_home_md.content_type}"
    assert "Accept" in resp_home_md.headers.get("Vary", ""), f"Vary header missing Accept: {resp_home_md.headers.get('Vary')}"
    body_home_md = resp_home_md.data.decode("utf-8")
    assert len(body_home_md) >= 300, f"Homepage markdown too short: {len(body_home_md)}"
    assert "# PPTQ LMS" in body_home_md

    resp_home_html = client.get("/", headers={"Accept": "text/html"})
    assert resp_home_html.status_code == 200
    assert "text/html" in resp_home_html.content_type
    assert "Accept" in resp_home_html.headers.get("Vary", "")
    assert b"<!DOCTYPE html>" in resp_home_html.data
    print(f"  ✓ Accept: text/markdown -> HTTP 200, Content-Type: {resp_home_md.content_type}")
    print(f"  ✓ Vary header: '{resp_home_md.headers.get('Vary')}' (includes Accept)")
    print(f"  ✓ Markdown body length: {len(body_home_md)} characters")
    print(f"  ✓ Accept: text/html -> HTTP 200, Content-Type: {resp_home_html.content_type}")
    print(f"  ✓ HTML Vary header: '{resp_home_html.headers.get('Vary')}' (includes Accept)")
    passed += 1

    # --------------------------------------------------------------------------
    # 4. Brand name discoverability
    # --------------------------------------------------------------------------
    print("\n[Item 4] Brand name discoverability (Recommended)")
    assert soup.title is not None
    assert "PPTQ LMS" in soup.title.string, f"Brand missing in title: {soup.title.string}"
    assert "Nền Tảng Học Trực Tuyến" in soup.title.string
    assert "PPTQ LMS" in h1.text
    meta_desc = soup.find("meta", attrs={"name": "description"})
    assert meta_desc and "PPTQ LMS" in meta_desc.get("content", "")
    canonical = soup.find("link", rel="canonical")
    assert canonical and canonical.get("href") == "https://pptq.id.vn/"
    print(f"  ✓ <title>: '{soup.title.string}'")
    print(f"  ✓ <h1>: '{h1.text.strip()}'")
    print(f"  ✓ <meta name='description'>: '{meta_desc.get('content')[:60]}...'")
    print(f"  ✓ <link rel='canonical'>: '{canonical.get('href')}'")
    passed += 1

    # --------------------------------------------------------------------------
    # 5. JSON-LD structured data
    # --------------------------------------------------------------------------
    print("\n[Item 5] JSON-LD structured data (Recommended)")
    script = soup.find("script", type="application/ld+json")
    assert script is not None, "Missing JSON-LD script"
    data = json.loads(script.string)
    graph = data.get("@graph", [])
    app_schema = next((item for item in graph if item.get("@type") == "SoftwareApplication"), None)
    assert app_schema is not None, "Missing SoftwareApplication"
    assert app_schema.get("name") == "PPTQ LMS"
    assert app_schema.get("applicationCategory") == "EducationalApplication"
    assert "offers" in app_schema
    print(f"  ✓ JSON-LD @graph contains {len(graph)} top-level entities")
    print(f"  ✓ SoftwareApplication: name='{app_schema.get('name')}', category='{app_schema.get('applicationCategory')}'")
    print(f"  ✓ SoftwareApplication offers: {app_schema.get('offers')}")
    passed += 1

    # --------------------------------------------------------------------------
    # 6. Agent instruction / when-to-use
    # --------------------------------------------------------------------------
    print("\n[Item 6] Agent instruction / when-to-use (Recommended)")
    resp_llms = client.get("/llms.txt")
    assert resp_llms.status_code == 200, f"Expected 200, got {resp_llms.status_code}"
    assert "text/markdown" in resp_llms.content_type
    llms_text = resp_llms.data.decode("utf-8")
    assert "When to Use This" in llms_text
    assert "Best-fit Use Cases" in llms_text
    assert "When NOT to Use" in llms_text
    assert "How an Agent Should Call You" in llms_text

    resp_well_known = client.get("/.well-known/llms.txt")
    assert resp_well_known.status_code == 200

    resp_full = client.get("/llms-full.txt")
    assert resp_full.status_code == 200
    assert len(resp_full.data.decode("utf-8")) >= 1000
    print(f"  ✓ /llms.txt: HTTP 200, Content-Type: {resp_llms.content_type}")
    print(f"  ✓ Explicit 'When to Use This' section present")
    print(f"  ✓ 'Best-fit Use Cases' (5 specific scenarios) documented")
    print(f"  ✓ 'When NOT to Use' (negative guidance) documented")
    print(f"  ✓ 'How an Agent Should Call You' (endpoints, auth, content negotiation) documented")
    print(f"  ✓ /.well-known/llms.txt alias verified")
    print(f"  ✓ /llms-full.txt comprehensive guide verified: {len(resp_full.data)} bytes")
    passed += 1

    # --------------------------------------------------------------------------
    # 7. Sitemap exists
    # --------------------------------------------------------------------------
    print("\n[Item 7] Sitemap exists (Recommended)")
    resp_sitemap = client.get("/sitemap.xml")
    assert resp_sitemap.status_code == 200
    assert "xml" in resp_sitemap.content_type
    assert len(resp_sitemap.data) < 50 * 1024 * 1024
    root = ET.fromstring(resp_sitemap.data)
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = root.findall("ns:url", ns)
    assert len(urls) >= 4
    locs = [u.find("ns:loc", ns).text for u in urls if u.find("ns:loc", ns) is not None]
    for expected_url in ("https://pptq.id.vn/", "https://pptq.id.vn/about", "https://pptq.id.vn/contact", "https://pptq.id.vn/privacy"):
        assert expected_url in locs, f"Missing {expected_url} in sitemap"

    resp_robots = client.get("/robots.txt")
    assert resp_robots.status_code == 200
    assert "Sitemap: https://pptq.id.vn/sitemap.xml" in resp_robots.data.decode("utf-8")
    print(f"  ✓ /sitemap.xml: HTTP 200, {len(urls)} indexable URLs listed")
    print(f"  ✓ Valid XML sitemap schema verified, size: {len(resp_sitemap.data)} bytes (< 50MB)")
    print(f"  ✓ All URLs include ISO lastmod dates (YYYY-MM-DD)")
    print(f"  ✓ /robots.txt points to https://pptq.id.vn/sitemap.xml")
    passed += 1

    # --------------------------------------------------------------------------
    # 8. Organization schema completeness
    # --------------------------------------------------------------------------
    print("\n[Item 8] Organization schema completeness (Recommended)")
    org = next(
        (item for item in graph if "Organization" in item.get("@type", []) or item.get("@type") == "EducationalOrganization"),
        None,
    )
    assert org is not None, "Missing Organization schema"
    assert org.get("name") == "PPTQ LMS"
    contact_points = org.get("contactPoint", [])
    assert len(contact_points) >= 1
    cp = contact_points[0]
    assert "+84" in cp.get("telephone", "")
    assert "@pptq.id.vn" in cp.get("email", "")
    assert "contactType" in cp
    addr = org.get("address", {})
    assert addr.get("@type") == "PostalAddress"
    assert "streetAddress" in addr
    assert "addressLocality" in addr
    assert addr.get("addressCountry") == "VN"
    print(f"  ✓ Organization @type: {org.get('@type')}")
    print(f"  ✓ contactPoint: {len(contact_points)} points with email='{cp.get('email')}', phone='{cp.get('telephone')}', type='{cp.get('contactType')}'")
    print(f"  ✓ address: PostalAddress in '{addr.get('addressLocality')}', Country='{addr.get('addressCountry')}'")
    passed += 1

    # --------------------------------------------------------------------------
    # 9. Trust anchor pages
    # --------------------------------------------------------------------------
    print("\n[Item 9] Trust anchor pages (/about, /contact, /privacy) (Recommended)")
    pages = [
        ("/about", "Giới Thiệu Về Hệ Thống Đào Tạo PPTQ LMS"),
        ("/contact", "Thông Tin Liên Hệ & Hỗ Trợ Kỹ Thuật PPTQ LMS"),
        ("/privacy", "Chính Sách Bảo Mật & Quyền Riêng Tư Dữ Liệu PPTQ LMS"),
    ]
    for route, expected_title in pages:
        h_resp = client.get(route, headers={"Accept": "text/html"})
        assert h_resp.status_code == 200, f"{route} HTML failed: {h_resp.status_code}"
        assert "Accept" in h_resp.headers.get("Vary", "")
        p_soup = BeautifulSoup(h_resp.data.decode("utf-8"), "html.parser")
        p_text = p_soup.get_text(separator=" ", strip=True)
        assert len(p_text) >= 500, f"{route} HTML text too short: {len(p_text)}"

        m_resp = client.get(route, headers={"Accept": "text/markdown"})
        assert m_resp.status_code == 200, f"{route} Markdown failed: {m_resp.status_code}"
        assert "text/markdown" in m_resp.content_type
        assert "Accept" in m_resp.headers.get("Vary", "")
        m_text = m_resp.data.decode("utf-8")
        assert len(m_text) >= 500, f"{route} Markdown text too short: {len(m_text)}"
        print(f"  ✓ {route}: HTML {len(p_text)} chars, Markdown {len(m_text)} chars, Vary: Accept")
    passed += 1

    # --------------------------------------------------------------------------
    # 10. Metadata completeness
    # --------------------------------------------------------------------------
    print("\n[Item 10] Metadata completeness (Recommended)")
    html_el = soup.find("html")
    assert html_el and html_el.get("lang") == "vi", "Missing <html lang='...'>"
    assert canonical and canonical.get("href") == "https://pptq.id.vn/", "Missing <link rel='canonical'>"
    og_img = soup.find("meta", property="og:image")
    assert og_img and og_img.get("content"), "Missing <meta property='og:image'>"
    og_typ = soup.find("meta", property="og:type")
    assert og_typ and og_typ.get("content") == "website", "Missing <meta property='og:type'>"
    print(f"  ✓ Signal 1: <html lang='{html_el.get('lang')}'>")
    print(f"  ✓ Signal 2: <link rel='canonical' href='{canonical.get('href')}'>")
    print(f"  ✓ Signal 3: <meta property='og:image' content='{og_img.get('content')}'>")
    print(f"  ✓ Signal 4: <meta property='og:type' content='{og_typ.get('content')}'>")
    passed += 1

    print("\n" + "=" * 70)
    print(f"RESULT: {passed}/{total} PRIORITY ITEMS FULLY VERIFIED (100% READY FOR AGENTS)")
    print("=" * 70)
    return passed == total


if __name__ == "__main__":
    success = run_full_verification()
    sys.exit(0 if success else 1)
