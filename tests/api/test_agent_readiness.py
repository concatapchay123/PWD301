"""Comprehensive test suite for Agent Readiness & Crawlability (Is Agentic audit).

Verifies all 10 priority criteria:
1. Content is available without JavaScript (>= 500 chars, H1, sequential headings)
2. Agent-friendly 404s (Accept: text/markdown -> 404 with Markdown body, Vary: Accept)
3. Markdown content negotiation (acceptmarkdown.com standard on homepage)
4. Brand name discoverability ("PPTQ LMS" in title, H1, metadata, canonical)
5. JSON-LD structured data (SoftwareApplication, WebSite)
6. Agent instruction / when-to-use (llms.txt with When to Use This section)
7. Sitemap exists (valid XML sitemap at /sitemap.xml with lastmod dates, robots.txt)
8. Organization schema completeness (contactPoint with phone/email, PostalAddress)
9. Trust anchor pages (/about, /contact, /privacy >= 500 chars in HTML and Markdown)
10. Metadata completeness (canonical, html lang, og:image, og:type)
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from flask.testing import FlaskClient


# ==============================================================================
# 1. Content is available without JavaScript & 4. Brand Discoverability & 10. Metadata
# ==============================================================================

def test_homepage_content_without_javascript(client: FlaskClient) -> None:
    """Requirement 1: Serve at least 500 characters of meaningful homepage content in raw HTML with sequential headings."""
    resp = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert resp.status_code == 200
    assert "text/html" in resp.content_type

    soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    # 1. Clear H1 tag
    h1 = soup.find("h1")
    assert h1 is not None, "Homepage must have an <h1> tag in raw HTML"
    assert "PPTQ LMS" in h1.text, f"H1 must feature brand name, got: {h1.text.strip()}"

    # 2. Sequential headings check
    h2_tags = soup.find_all("h2")
    assert len(h2_tags) >= 2, f"Expected at least 2 <h2> tags, found {len(h2_tags)}"
    h3_tags = soup.find_all("h3")
    assert len(h3_tags) >= 4, f"Expected at least 4 <h3> tags, found {len(h3_tags)}"

    # 3. Meaningful content length in main container
    viewport = soup.find("main", id="app-viewport")
    assert viewport is not None, "<main id='app-viewport'> must exist"
    text = viewport.get_text(separator=" ", strip=True)
    assert len(text) >= 500, f"Expected >= 500 chars of raw content, got {len(text)}"

    # 4. Noscript fallback presence
    noscript = soup.find("noscript")
    assert noscript is not None, "Homepage must have <noscript> tag for non-JS clients"


def test_homepage_metadata_completeness_and_brand_signals(client: FlaskClient) -> None:
    """Requirement 4 & 10: Verify all 4 required metadata signals and brand discoverability."""
    resp = client.get("/", headers={"Accept": "text/html"})
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    # Signal 1: <html lang="...">
    html_tag = soup.find("html")
    assert html_tag is not None and html_tag.get("lang") == "vi"

    # Signal 2: <link rel="canonical">
    canonical = soup.find("link", rel="canonical")
    assert canonical is not None, "Missing <link rel='canonical'>"
    assert canonical.get("href") == "https://pptq.id.vn/"

    # Signal 3: <meta property="og:image">
    og_image = soup.find("meta", property="og:image")
    assert og_image is not None, "Missing <meta property='og:image'>"
    assert "pptq_icon.png" in og_image.get("content", "")

    # Signal 4: <meta property="og:type">
    og_type = soup.find("meta", property="og:type")
    assert og_type is not None, "Missing <meta property='og:type'>"
    assert og_type.get("content") == "website"

    # Brand Title
    assert soup.title is not None
    assert "PPTQ LMS" in soup.title.string

    # Additional Open Graph & Twitter Signals
    assert soup.find("meta", property="og:title") is not None
    assert soup.find("meta", property="og:url") is not None
    assert soup.find("meta", attrs={"name": "twitter:card"}) is not None


# ==============================================================================
# 2. Agent-friendly 404s
# ==============================================================================

def test_agent_friendly_404_markdown_negotiation(client: FlaskClient) -> None:
    """Requirement 2: Nonexistent path returns 404 with Markdown error body when Accept: text/markdown."""
    probe_url = "/__ora-404-probe-gr9m15ae"
    resp = client.get(probe_url, headers={"Accept": "text/markdown"})

    assert resp.status_code == 404
    assert "text/markdown" in resp.content_type
    assert "Accept" in resp.headers.get("Vary", "")

    body = resp.data.decode("utf-8")
    assert len(body) >= 20, f"Markdown 404 body must be >= 20 chars, got {len(body)}"
    assert "404" in body
    assert "https://pptq.id.vn/llms.txt" in body or "/llms.txt" in body
    assert "https://pptq.id.vn/sitemap.xml" in body or "/sitemap.xml" in body


def test_standard_404_preserves_json_for_api_clients(client: FlaskClient) -> None:
    """Requirement 2 (Safety): API clients requesting application/json still receive JSON 404 envelope."""
    resp = client.get("/__ora-404-probe-standard", headers={"Accept": "application/json"})
    assert resp.status_code == 404
    assert resp.is_json
    data = resp.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


# ==============================================================================
# 3. Markdown content negotiation (acceptmarkdown.com)
# ==============================================================================

def test_homepage_markdown_content_negotiation(client: FlaskClient) -> None:
    """Requirement 3: Accept: text/markdown returns 200 OK Markdown with Vary: Accept."""
    resp = client.get("/", headers={"Accept": "text/markdown"})
    assert resp.status_code == 200
    assert "text/markdown" in resp.content_type
    assert "Accept" in resp.headers.get("Vary", "")

    body = resp.data.decode("utf-8")
    assert len(body) >= 200, "Markdown body must be nonempty and substantial"
    assert "# PPTQ LMS" in body
    assert "https://pptq.id.vn" in body
    assert "/llms.txt" in body
    assert "/sitemap.xml" in body


def test_homepage_html_negotiation_includes_vary_accept(client: FlaskClient) -> None:
    """Requirement 3: Accept: text/html returns HTML with Vary: Accept."""
    resp = client.get("/", headers={"Accept": "text/html"})
    assert resp.status_code == 200
    assert "text/html" in resp.content_type
    assert "Accept" in resp.headers.get("Vary", "")
    assert b"<!DOCTYPE html>" in resp.data


# ==============================================================================
# 5. JSON-LD structured data & 8. Organization schema completeness
# ==============================================================================

def test_homepage_json_ld_schema_completeness(client: FlaskClient) -> None:
    """Requirement 5 & 8: Verify JSON-LD with EducationalOrganization, contactPoint, address, SoftwareApplication."""
    resp = client.get("/", headers={"Accept": "text/html"})
    soup = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    script = soup.find("script", type="application/ld+json")
    assert script is not None, "Missing <script type='application/ld+json'>"

    data = json.loads(script.string)
    assert data.get("@context") == "https://schema.org"
    graph = data.get("@graph", [])
    assert len(graph) >= 2, "Expected @graph with multiple schema entities"

    def _type_matches(item: dict, target_types: tuple[str, ...]) -> bool:
        t = item.get("@type")
        if isinstance(t, list):
            return any(x in target_types for x in t)
        return t in target_types

    # 1. Organization / EducationalOrganization schema (Requirement 8)
    org = next(
        (item for item in graph if _type_matches(item, ("EducationalOrganization", "Organization"))),
        None
    )
    assert org is not None, "Missing EducationalOrganization/Organization schema"
    assert org.get("name") == "PPTQ LMS"
    assert org.get("url") == "https://pptq.id.vn/"

    # contactPoint verification
    contact_points = org.get("contactPoint")
    assert isinstance(contact_points, list) and len(contact_points) > 0, "contactPoint must be provided"
    first_cp = contact_points[0]
    assert "telephone" in first_cp and "+84" in first_cp["telephone"]
    assert "email" in first_cp and "@pptq.id.vn" in first_cp["email"]
    assert "contactType" in first_cp

    # address verification
    addr = org.get("address")
    assert isinstance(addr, dict), "address must be a PostalAddress object"
    assert addr.get("@type") == "PostalAddress"
    assert "streetAddress" in addr
    assert "addressLocality" in addr
    assert addr.get("addressCountry") == "VN"

    # 2. SoftwareApplication schema (Requirement 5)
    app = next(
        (item for item in graph if item.get("@type") == "SoftwareApplication"),
        None
    )
    assert app is not None, "Missing SoftwareApplication schema"
    assert app.get("name") == "PPTQ LMS"
    assert app.get("applicationCategory") == "EducationalApplication"
    assert "offers" in app


# ==============================================================================
# 6. Agent instruction / when-to-use
# ==============================================================================

def test_llms_txt_and_when_to_use_guidance(client: FlaskClient) -> None:
    """Requirement 6: Verify /llms.txt and /llms-full.txt with explicit 'When to Use This' guidance."""
    resp = client.get("/llms.txt")
    assert resp.status_code == 200
    assert "text/markdown" in resp.content_type or "text/plain" in resp.content_type

    content = resp.data.decode("utf-8")
    assert "# PPTQ LMS" in content
    assert "When to Use This" in content or "when to use this" in content.lower()
    assert "Best-fit Use Cases" in content
    assert "When NOT to Use" in content
    assert "How an Agent Should Call You" in content

    # Check .well-known alias
    well_known_resp = client.get("/.well-known/llms.txt")
    assert well_known_resp.status_code == 200
    assert "When to Use This" in well_known_resp.data.decode("utf-8")

    # Check full version
    full_resp = client.get("/llms-full.txt")
    assert full_resp.status_code == 200
    assert len(full_resp.data.decode("utf-8")) >= 1000


# ==============================================================================
# 7. Sitemap exists
# ==============================================================================

def test_sitemap_xml_and_robots_txt(client: FlaskClient) -> None:
    """Requirement 7: Verify valid XML sitemap at /sitemap.xml under 50MB with lastmod dates."""
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "application/xml" in resp.content_type or "text/xml" in resp.content_type
    assert len(resp.data) < 50 * 1024 * 1024  # under 50MB

    root = ET.fromstring(resp.data)
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = root.findall("ns:url", namespace)
    assert len(urls) >= 4, f"Expected at least 4 URLs in sitemap, found {len(urls)}"

    locs = [u.find("ns:loc", namespace).text for u in urls if u.find("ns:loc", namespace) is not None]
    assert "https://pptq.id.vn/" in locs
    assert "https://pptq.id.vn/about" in locs
    assert "https://pptq.id.vn/contact" in locs
    assert "https://pptq.id.vn/privacy" in locs

    # Verify lastmod dates exist
    for u in urls:
        lastmod = u.find("ns:lastmod", namespace)
        assert lastmod is not None and len(lastmod.text) == 10  # YYYY-MM-DD

    # Verify robots.txt references the sitemap
    robots_resp = client.get("/robots.txt")
    assert robots_resp.status_code == 200
    robots_content = robots_resp.data.decode("utf-8")
    assert "Sitemap: https://pptq.id.vn/sitemap.xml" in robots_content


# ==============================================================================
# 9. Trust anchor pages (/about, /contact, /privacy)
# ==============================================================================

def test_trust_anchor_pages_content_and_negotiation(client: FlaskClient) -> None:
    """Requirement 9: /about, /contact, /privacy each serve >= 500 characters in HTML & Markdown."""
    pages = [
        ("/about", "Giới Thiệu Về Hệ Thống Đào Tạo PPTQ LMS"),
        ("/contact", "Thông Tin Liên Hệ & Hỗ Trợ Kỹ Thuật PPTQ LMS"),
        ("/privacy", "Chính Sách Bảo Mật & Quyền Riêng Tư Dữ Liệu PPTQ LMS"),
    ]

    for route, expected_title_part in pages:
        # 1. HTML request
        html_resp = client.get(route, headers={"Accept": "text/html"})
        assert html_resp.status_code == 200
        assert "text/html" in html_resp.content_type
        assert "Accept" in html_resp.headers.get("Vary", "")

        soup = BeautifulSoup(html_resp.data.decode("utf-8"), "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        assert len(text) >= 500, f"{route} HTML content must be >= 500 chars, got {len(text)}"

        h1 = soup.find("h1")
        assert h1 is not None, f"{route} must have an <h1> tag"
        assert expected_title_part in h1.text

        # 2. Markdown request (Content Negotiation)
        md_resp = client.get(route, headers={"Accept": "text/markdown"})
        assert md_resp.status_code == 200
        assert "text/markdown" in md_resp.content_type
        assert "Accept" in md_resp.headers.get("Vary", "")

        md_text = md_resp.data.decode("utf-8")
        assert len(md_text) >= 500, f"{route} Markdown content must be >= 500 chars, got {len(md_text)}"
        assert expected_title_part in md_text
