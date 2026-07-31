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
import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

BASE = "https://userdocs.cority.com"
SITEMAP_INDEX = f"{BASE}/sitemaps/sitemap.xml"
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
    return [loc.text for loc in root.iter(f"{SITEMAP_NS}loc")]


def publication_slug_from_sitemap_url(sitemap_url: str) -> str:
    # e.g. https://.../sitemap_publication_cority-user-guide.xml -> cority-user-guide
    name = Path(sitemap_url).stem
    return name.removeprefix("sitemap_publication_")


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


def rehost_images(html: str, images_dir: Path) -> str:
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
    article_dir = out_root / publication_slug / article_slug
    images_dir = article_dir / "images"
    rewritten = rehost_images(html, images_dir)

    article_dir.mkdir(parents=True, exist_ok=True)
    (article_dir / "index.html").write_text(rewritten, encoding="utf-8")

    return {
        "publication": publication_slug,
        "slug": article_slug,
        "title": data.get("title"),
        "project_name": data.get("projectName"),
    }


def scrape_publication(publication_sitemap_url: str, out_root: Path, limit: int = 0) -> dict:
    """Scrape every article in one publication (or up to `limit` if >0). Returns summary stats."""
    pairs = list_article_slugs(publication_sitemap_url)
    if limit > 0:
        pairs = pairs[:limit]
    stats = {"publication": publication_slug_from_sitemap_url(publication_sitemap_url),
             "total": len(pairs), "succeeded": 0, "failed": 0, "images": 0, "failures": []}
    for pub, slug in pairs:
        try:
            before = set((out_root / pub / slug / "images").glob("*")) if (out_root / pub / slug / "images").exists() else set()
            scrape_article(pub, slug, out_root)
            after = set((out_root / pub / slug / "images").glob("*")) if (out_root / pub / slug / "images").exists() else set()
            stats["images"] += len(after - before)
            stats["succeeded"] += 1
        except Exception as e:
            stats["failed"] += 1
            stats["failures"].append({"publication": pub, "slug": slug, "error": f"{type(e).__name__}: {e}"})
        time.sleep(0.1)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape Cority ClickHelp documentation (userdocs.cority.com)")
    parser.add_argument("--output", default="cority/clickhelp", help="Output directory (default: cority/clickhelp)")
    parser.add_argument("--publications", default="all",
                         help="Comma-separated publication slugs to scrape, or 'all' (default: all)")
    parser.add_argument("--limit-per-publication", type=int, default=0,
                         help="Cap articles per publication, 0 = no limit (useful for a diagnostic run)")
    parser.add_argument("--stats-out", default=None, help="Optional path to write a JSON stats summary")
    args = parser.parse_args()

    out_root = Path(args.output)
    all_sitemaps = list_publications()

    if args.publications == "all":
        sitemaps = all_sitemaps
    else:
        wanted = {s.strip() for s in args.publications.split(",")}
        sitemaps = [s for s in all_sitemaps if publication_slug_from_sitemap_url(s) in wanted]
        missing = wanted - {publication_slug_from_sitemap_url(s) for s in sitemaps}
        if missing:
            print(f"WARNING: publications not found in sitemap index: {missing}", file=sys.stderr)

    print(f"Scraping {len(sitemaps)} publication(s) -> {out_root}")

    overall = {"publications": [], "total_articles": 0, "total_succeeded": 0,
               "total_failed": 0, "total_images": 0, "failures": []}

    for i, sitemap_url in enumerate(sitemaps, 1):
        pub_slug = publication_slug_from_sitemap_url(sitemap_url)
        print(f"[{i}/{len(sitemaps)}] {pub_slug} ...")
        stats = scrape_publication(sitemap_url, out_root, limit=args.limit_per_publication)
        overall["publications"].append(stats)
        overall["total_articles"] += stats["total"]
        overall["total_succeeded"] += stats["succeeded"]
        overall["total_failed"] += stats["failed"]
        overall["total_images"] += stats["images"]
        overall["failures"].extend(stats["failures"])
        print(f"    {pub_slug}: {stats['succeeded']}/{stats['total']} succeeded, "
              f"{stats['images']} images, {stats['failed']} failed")

    print("\n=== DONE ===")
    print(f"Publications: {len(sitemaps)}")
    print(f"Articles: {overall['total_succeeded']}/{overall['total_articles']} succeeded")
    print(f"Images downloaded: {overall['total_images']}")
    print(f"Failures: {overall['total_failed']}")

    if args.stats_out:
        Path(args.stats_out).write_text(json.dumps(overall, indent=2), encoding="utf-8")

    return 1 if overall["total_failed"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
