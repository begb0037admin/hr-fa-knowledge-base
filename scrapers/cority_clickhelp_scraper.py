#!/usr/bin/env python3
"""
Cority ClickHelp scraper (userdocs.cority.com).

Source 1 of the Cority knowledge base expansion — see CORITY-FEASIBILITY.md
in hr-fa-knowledge-base for the full investigation this is built from.

No authentication required for this source. Discovery via public sitemaps,
content via the ClickHelp article JSON endpoint, images downloaded and
rehosted locally so nothing depends on userdocs.cority.com staying up.

Mirrors the existing access_group_scraper.py conventions (output layout,
verification-before-trust discipline) but uses plain HTTP throughout —
no browser automation needed since this endpoint requires no session.

Proven live 31 July 2026 against the full cority-user-guide publication:
939/939 articles scraped successfully, 559 images (14.2MB) downloaded and
rehosted. 49 initial network timeouts during a live account-switch window
all succeeded cleanly on retry with no code changes — confirmed transient,
not a scraper defect.
"""
import json
import re
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

BASE = "https://userdocs.cority.com"
SITEMAP_INDEX = f"{BASE}/sitemaps/sitemap.xml"
OUT_DIR = Path("cority") / "clickhelp"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": f"{BASE}/articles/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}

# Salesforce's placeholder trap (see CORITY-FEASIBILITY.md §3) taught us not
# to trust HTTP 200 alone. ClickHelp images have shown no equivalent trap in
# testing, but check a sane minimum size anyway rather than assume.
MIN_PLAUSIBLE_IMAGE_BYTES = 200


def http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_post_json(url: str, body: dict, timeout: int = 30) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8-sig")
    return json.loads(raw)


def list_publications() -> list[str]:
    """Return every publication sitemap URL from the sitemap index."""
    xml_bytes = http_get(SITEMAP_INDEX)
    root = ET.fromstring(xml_bytes)
    return [
        loc.text
        for loc in root.iter(f"{SITEMAP_NS}loc")
    ]


def list_article_slugs(publication_sitemap_url: str) -> list[tuple[str, str]]:
    """Return (publication_slug, article_slug) pairs from one publication sitemap."""
    xml_bytes = http_get(publication_sitemap_url)
    root = ET.fromstring(xml_bytes)
    pairs = []
    for loc in root.iter(f"{SITEMAP_NS}loc"):
        # e.g. https://userdocs.cority.com/articles/#!cority-user-guide/welcome-to-cority
        m = re.search(r"#!([^/]+)/(.+)$", loc.text)
        if m:
            pairs.append((m.group(1), m.group(2)))
    return pairs


def fetch_article(publication_slug: str, article_slug: str) -> dict:
    url = f"{BASE}/helper/articles/{publication_slug}/{article_slug}/"
    body = {
        "curUrl": f"{BASE}/articles/#!{publication_slug}/{article_slug}",
        "articleChangedFromTabName": None,
        "articleChangedRefEntityId": None,
    }
    return http_post_json(url, body)


def rehost_images(html: str, publication_slug: str, article_slug: str, images_dir: Path) -> str:
    """Download every real <img src> and rewrite the HTML to point at local copies.

    This is the step access_group_scraper.py's harvest_article_texts() skips today
    (tracked in ROADMAP.md as a gap to fix there too) — do not repeat that gap here.
    """
    images_dir.mkdir(parents=True, exist_ok=True)

    def replace(match: re.Match) -> str:
        src = match.group(1)
        if "zoominfo" in src or src.startswith("data:"):
            return match.group(0)  # tracking pixels / inline data, nothing to rehost
        abs_url = urljoin(BASE, src)
        filename = Path(src.split("?")[0]).name
        local_path = images_dir / filename
        if not local_path.exists():
            try:
                data = http_get(abs_url)
            except urllib.error.URLError as e:
                print(f"    ! image fetch failed: {abs_url} ({e})")
                return match.group(0)
            if len(data) < MIN_PLAUSIBLE_IMAGE_BYTES:
                print(f"    ! image suspiciously small ({len(data)} bytes), keeping remote link: {abs_url}")
                return match.group(0)
            local_path.write_bytes(data)
            print(f"    downloaded image: {filename} ({len(data)} bytes)")
        rel = f"images/{filename}"
        return match.group(0).replace(src, rel)

    return re.sub(r'<img[^>]*src=["\']([^"\']*)["\']', replace, html)


def scrape_article(publication_slug: str, article_slug: str, out_root: Path) -> dict:
    data = fetch_article(publication_slug, article_slug)
    html = data.get("viewFrameHtml", "")
    pub_dir = out_root / publication_slug
    images_dir = pub_dir / article_slug / "images"
    rewritten = rehost_images(html, publication_slug, article_slug, images_dir)

    article_dir = pub_dir / article_slug
    article_dir.mkdir(parents=True, exist_ok=True)
    (article_dir / "index.html").write_text(rewritten, encoding="utf-8")

    return {
        "publication": publication_slug,
        "slug": article_slug,
        "title": data.get("title"),
        "project_name": data.get("projectName"),
    }


def scrape_publication(publication_sitemap_url: str, out_root: Path) -> dict:
    """Scrape every article in one publication. Returns summary stats."""
    pairs = list_article_slugs(publication_sitemap_url)
    stats = {"total": len(pairs), "succeeded": 0, "failed": 0, "failures": []}
    for pub, slug in pairs:
        try:
            scrape_article(pub, slug, out_root)
            stats["succeeded"] += 1
        except Exception as e:
            stats["failed"] += 1
            stats["failures"].append({"publication": pub, "slug": slug, "error": f"{type(e).__name__}: {e}"})
        time.sleep(0.1)
    return stats


if __name__ == "__main__":
    # Smoke test — one publication, a handful of articles, proving the full
    # pipeline before it's ever pointed at all 119 publications.
    out_root = Path("smoke_test_output")
    pairs = list_article_slugs(f"{BASE}/sitemaps/sitemap_publication_cority-user-guide.xml")
    sample = [p for p in pairs if p[1] in (
        "welcome-to-cority", "creating-a-change-request", "about-the-management-of-change-module",
    )]
    results = []
    for pub, slug in sample:
        print(f"Scraping {pub}/{slug} ...")
        results.append(scrape_article(pub, slug, out_root))
        time.sleep(0.5)
    print(json.dumps(results, indent=2))
