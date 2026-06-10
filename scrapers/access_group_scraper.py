#!/usr/bin/env python3
r"""
Access Group PeopleXD Help Centre scraper.

Logs into the Access Group support portal (if required), walks all eight
PeopleXD Help Centres, downloads every available PDF article using the
authenticated browser session, saves them into per-module subfolders, and
writes a manifest CSV plus an errors log.

This script is designed to run on the machine that actually owns the output
folder (e.g. the Windows workstation in the brief). It needs:
  - real outbound internet access
  - Python 3.9+
  - playwright (pip install playwright && playwright install chromium)

The password is NEVER written to disk or logged. Provide it via the
ACCESS_PASSWORD environment variable, or you will be prompted securely at
runtime (getpass — no echo).

Usage (PowerShell example):
    $env:ACCESS_PASSWORD = "..."        # optional; otherwise you'll be prompted
    python access_group_scraper.py `
        --username kevin.lelitte@admin.ox.ac.uk `
        --output "C:\Users\admin\Documents\Claude\Projects\hr-knowledge-base\downloads"

Add --headed to watch the browser, --print-fallback to render a PDF from the
page when no PDF link is found, and --limit N to test on the first N articles
per centre.
"""

from __future__ import annotations

import argparse
import csv
import getpass
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    from playwright.sync_api import (
        sync_playwright,
        TimeoutError as PWTimeoutError,
        Error as PWError,
    )
except ImportError:  # pragma: no cover - dependency guard
    sys.exit(
        "Playwright is not installed.\n"
        "  pip install playwright requests\n"
        "  playwright install chromium\n"
        "Then re-run this script."
    )


LOGIN_URL = "https://accessgroup.my.site.com/Support/s/login/?language=en_US"

# (module label, homepage URL, output subfolder)
HELP_CENTRES = [
    ("Payroll",              "https://help-peoplexdpayroll.theaccessgroup.com/en",              "payroll"),
    ("People Management",    "https://help-peoplexdpeoplemanagement.theaccessgroup.com/en",     "people-management"),
    ("Workforce Management", "https://help-peoplexdworkforcemanagement.theaccessgroup.com/en",  "workforce-management"),
    ("Talent",               "https://help-peoplexdtalent.theaccessgroup.com/en",              "talent"),
    ("Recruitment",          "https://help-peoplexdrecruitment.theaccessgroup.com/en",         "recruitment"),
    ("Expense",              "https://help-peoplexdexpense.theaccessgroup.com/en",             "expense"),
    ("Pension",              "https://help-peoplexdpension.theaccessgroup.com/en",             "pension"),
    ("Cross-module",         "https://help-peoplexd.theaccessgroup.com/en",                    "cross-module"),
]

DEFAULT_OUTPUT = r"C:\Users\admin\Documents\Claude\Projects\hr-knowledge-base\downloads"

NAV_TIMEOUT_MS = 45_000
RENDER_SETTLE_MS = 2_500


@dataclass
class ManifestRow:
    title: str
    module: str
    filename: str
    source_url: str
    downloaded: str  # "yes" / "no"
    notes: str = ""


@dataclass
class RunStats:
    found: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    harvested: int = 0
    rows: list = field(default_factory=list)


def log_error(errors_path: Path, message: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}\n"
    with errors_path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    print("  ! " + message, file=sys.stderr)


def sanitise_filename(title: str, max_len: int = 150) -> str:
    """Make a title safe for the Windows filesystem."""
    name = title.strip()
    # Strip characters illegal on Windows: \ / : * ? " < > |
    name = re.sub(r'[\\/:*?"<>|]', " ", name)
    # Collapse whitespace and trailing dots/spaces (Windows dislikes them)
    name = re.sub(r"\s+", " ", name).strip().rstrip(". ")
    if not name:
        name = "untitled"
    if len(name) > max_len:
        name = name[:max_len].rstrip(". ")
    return name


def unique_path(folder: Path, base: str, ext: str) -> Path:
    """Return a non-colliding path: 'Base.pdf', 'Base (2).pdf', ..."""
    candidate = folder / f"{base}{ext}"
    n = 2
    while candidate.exists():
        candidate = folder / f"{base} ({n}){ext}"
        n += 1
    return candidate


def is_logged_in(page) -> bool:
    """Heuristic: a Salesforce community login form is no longer present."""
    try:
        # The login page exposes username/password inputs; absence => logged in.
        return page.query_selector("input[name='username'], input#username") is None
    except PWError:
        return False


def do_login(page, username: str, password: str, errors_path: Path) -> bool:
    """Attempt to authenticate. Returns True if a session looks active."""
    print("Logging in to Access Group support portal...")
    try:
        page.goto(LOGIN_URL, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        page.wait_for_timeout(RENDER_SETTLE_MS)
    except PWTimeoutError:
        log_error(errors_path, f"Login page navigation timed out: {LOGIN_URL}")
        return False

    user_sel = "input[name='username'], input#username"
    pass_sel = "input[name='password'], input#password"
    try:
        page.wait_for_selector(user_sel, timeout=NAV_TIMEOUT_MS)
        page.fill(user_sel, username)
        page.fill(pass_sel, password)
        # Submit: button labelled Log In, or the form's submit input.
        submit = page.query_selector(
            "button:has-text('Log In'), button[type='submit'], input[type='submit']"
        )
        if submit:
            submit.click()
        else:
            page.press(pass_sel, "Enter")
        page.wait_for_load_state("networkidle", timeout=NAV_TIMEOUT_MS)
        page.wait_for_timeout(RENDER_SETTLE_MS)
    except PWTimeoutError:
        log_error(errors_path, "Login form interaction timed out.")
        return False
    except PWError as exc:
        log_error(errors_path, f"Login form error: {exc}")
        return False

    if is_logged_in(page):
        print("  Login appears successful.")
        return True

    log_error(errors_path, "Login did not succeed (login form still present).")
    return False


def collect_article_links(page, homepage: str, errors_path: Path) -> list[tuple[str, str]]:
    """
    Load a Help Centre homepage and return [(title, url), ...] for article-like
    links. Heuristic-based: the exact DOM varies per portal, so this gathers
    in-domain content links and de-duplicates them.
    """
    try:
        page.goto(homepage, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        page.wait_for_timeout(RENDER_SETTLE_MS)
        # Best effort: let lazy content settle.
        try:
            page.wait_for_load_state("networkidle", timeout=NAV_TIMEOUT_MS)
        except PWTimeoutError:
            pass
    except PWTimeoutError:
        log_error(errors_path, f"Homepage navigation timed out: {homepage}")
        return []

    host = urlparse(homepage).netloc
    anchors = page.query_selector_all("a[href]")
    seen: dict[str, str] = {}
    results: list[tuple[str, str]] = []
    for a in anchors:
        href = a.get_attribute("href") or ""
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue
        url = urljoin(homepage, href)
        parsed = urlparse(url)
        if parsed.netloc != host:
            continue
        # Skip the homepage/section roots and obvious non-article paths.
        path = parsed.path.rstrip("/")
        if not path or path.endswith("/en") or path == "/en":
            continue
        if any(seg in path for seg in ("/search", "/login", "/logout")):
            continue
        title = (a.inner_text() or "").strip()
        if not title:
            title = a.get_attribute("title") or path.rsplit("/", 1)[-1]
        title = title.strip()
        if not title or len(title) < 3:
            continue
        key = url.split("#")[0]
        if key in seen:
            continue
        seen[key] = title
        results.append((title, key))
    return results


def harvest_article_texts(page, links: list[tuple[str, str]],
                          errors_path: Path, limit: int = 0) -> list[dict]:
    """Deep crawl: follow collection pages to every individual article and
    extract its title, URL and full body text (no PDF rendering)."""
    article_urls: dict[str, str] = {}
    collection_urls: list[str] = []
    for title, url in links:
        path = urlparse(url).path
        if "/articles/" in path:
            article_urls.setdefault(url.split("?")[0], title)
        elif "/collections/" in path:
            collection_urls.append(url)

    for curl in collection_urls:
        try:
            page.goto(curl, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
            page.wait_for_timeout(1200)
            for a in page.query_selector_all('a[href*="/articles/"]'):
                href = a.get_attribute("href") or ""
                url = urljoin(curl, href).split("#")[0].split("?")[0]
                title = (a.inner_text() or "").strip().split("\n")[0].strip()
                if title and url not in article_urls:
                    article_urls[url] = title
        except Exception as exc:  # noqa: BLE001 - log and continue
            log_error(errors_path, f"Collection crawl failed {curl}: {exc}")

    items = list(article_urls.items())
    if limit:
        items = items[:limit]

    harvested: list[dict] = []
    for url, title in items:
        try:
            page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
            page.wait_for_timeout(900)
            h1 = page.query_selector("h1")
            if h1:
                h1_text = (h1.inner_text() or "").strip()
                if h1_text:
                    title = h1_text
            text = page.evaluate(
                "() => (document.querySelector('article') || document.body).innerText")
            harvested.append({"title": title, "url": url,
                              "text": (text or "").strip()})
        except Exception as exc:  # noqa: BLE001 - log and continue
            log_error(errors_path, f"Article harvest failed {url}: {exc}")
    return harvested


def find_pdf_url(page, article_url: str, errors_path: Path) -> str | None:
    """Open an article and return the best PDF download URL, or None."""
    try:
        page.goto(article_url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        page.wait_for_timeout(RENDER_SETTLE_MS)
    except PWTimeoutError:
        log_error(errors_path, f"Article navigation timed out: {article_url}")
        return None

    # 1) Direct links to a .pdf resource.
    for a in page.query_selector_all("a[href]"):
        href = a.get_attribute("href") or ""
        if ".pdf" in href.lower():
            return urljoin(article_url, href)

    # 2) Buttons/links whose text mentions PDF or download.
    candidate = page.query_selector(
        "a:has-text('PDF'), a:has-text('Download'), "
        "button:has-text('PDF'), button:has-text('Download')"
    )
    if candidate:
        href = candidate.get_attribute("href")
        if href and ".pdf" in href.lower():
            return urljoin(article_url, href)
    return None


def download_via_session(context, url: str, dest: Path, errors_path: Path) -> bool:
    """Download a URL reusing the browser's authenticated cookies."""
    try:
        resp = context.request.get(url, timeout=NAV_TIMEOUT_MS)
        if not resp.ok:
            log_error(errors_path, f"HTTP {resp.status} downloading {url}")
            return False
        body = resp.body()
        dest.write_bytes(body)
        return True
    except PWError as exc:
        log_error(errors_path, f"Download error for {url}: {exc}")
        return False


def render_pdf(page, article_url: str, dest: Path, errors_path: Path) -> bool:
    """Fallback: render the current article page to a PDF (headless only)."""
    try:
        page.goto(article_url, timeout=NAV_TIMEOUT_MS, wait_until="networkidle")
        page.wait_for_timeout(RENDER_SETTLE_MS)
        page.emulate_media(media="print")
        page.pdf(path=str(dest), format="A4", print_background=True)
        return True
    except PWError as exc:
        log_error(errors_path, f"Print-to-PDF failed for {article_url}: {exc}")
        return False


def write_manifest(manifest_path: Path, rows: list[ManifestRow]) -> None:
    with manifest_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["title", "module", "filename", "source_url", "downloaded", "notes"]
        )
        for r in rows:
            writer.writerow(
                [r.title, r.module, r.filename, r.source_url, r.downloaded, r.notes]
            )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape Access Group PeopleXD Help Centres.")
    p.add_argument("--username",
                   default=os.environ.get("ACCESS_USERNAME",
                                          "kevin.lelitte@admin.ox.ac.uk"))
    p.add_argument("--output", default=DEFAULT_OUTPUT, help="Output root folder.")
    p.add_argument("--headed", action="store_true", help="Show the browser window.")
    p.add_argument("--no-login", action="store_true",
                   help="Skip portal login (use if help centres are public).")
    p.add_argument("--print-fallback", action="store_true",
                   help="Render a PDF from the page when no PDF link is found.")
    p.add_argument("--deep", action="store_true",
                   help="Follow collection pages and harvest the full text of "
                        "every individual article into articles.json.")
    p.add_argument("--limit", type=int, default=0,
                   help="Process at most N articles per centre (0 = no limit).")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    password = os.environ.get("ACCESS_PASSWORD")
    if not password and not args.no_login:
        if sys.stdin.isatty():
            password = getpass.getpass("Access Group password (input hidden): ")
        if not password:
            print("No password provided (set ACCESS_PASSWORD) and --no-login "
                  "not set. Aborting.", file=sys.stderr)
            return 2

    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_path = out_root / "manifest.csv"
    errors_path = out_root / "errors.log"
    # Fresh error log per run.
    errors_path.write_text("", encoding="utf-8")

    stats = RunStats()
    all_articles: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        context = browser.new_context(accept_downloads=True)
        context.set_default_timeout(NAV_TIMEOUT_MS)
        page = context.new_page()

        logged_in = False
        if not args.no_login:
            logged_in = do_login(page, args.username, password, errors_path)
            if not logged_in:
                log_error(errors_path,
                          "Login failed. Continuing unauthenticated; gated content "
                          "may be unavailable. Re-run with --no-login to silence this.")

        for module, homepage, subfolder in HELP_CENTRES:
            print(f"\n=== {module} ===")
            folder = out_root / subfolder
            folder.mkdir(parents=True, exist_ok=True)

            links = collect_article_links(page, homepage, errors_path)
            if args.limit:
                links = links[: args.limit]
            print(f"  {len(links)} candidate article link(s) found.")
            stats.found += len(links)

            if args.deep:
                arts = harvest_article_texts(page, links, errors_path, args.limit)
                for art in arts:
                    art["module"] = module
                all_articles.extend(arts)
                stats.harvested += len(arts)
                print(f"  {len(arts)} individual article(s) harvested.")

            for title, url in links:
                base = sanitise_filename(title)
                pdf_url = find_pdf_url(page, url, errors_path)

                if not pdf_url:
                    if args.print_fallback:
                        dest = unique_path(folder, base, ".pdf")
                        ok = render_pdf(page, url, dest, errors_path)
                        if ok:
                            stats.downloaded += 1
                            stats.rows.append(ManifestRow(
                                title, module, dest.name, url, "yes",
                                "rendered from page (no PDF link)"))
                        else:
                            stats.failed += 1
                            stats.rows.append(ManifestRow(
                                title, module, "", url, "no", "print-fallback failed"))
                    else:
                        stats.skipped += 1
                        stats.rows.append(ManifestRow(
                            title, module, "", url, "no", "no PDF link found"))
                        print(f"  - skip (no PDF): {title}")
                    continue

                dest = unique_path(folder, base, ".pdf")
                ok = download_via_session(context, pdf_url, dest, errors_path)
                if not ok:
                    time.sleep(2)  # retry once after a short pause
                    ok = download_via_session(context, pdf_url, dest, errors_path)

                if ok:
                    stats.downloaded += 1
                    stats.rows.append(ManifestRow(
                        title, module, dest.name, url, "yes", ""))
                    print(f"  + {dest.name}")
                else:
                    stats.failed += 1
                    stats.rows.append(ManifestRow(
                        title, module, "", url, "no",
                        f"download failed after retry ({pdf_url})"))

        context.close()
        browser.close()

    write_manifest(manifest_path, stats.rows)
    if args.deep:
        (out_root / "articles.json").write_text(
            json.dumps(all_articles, ensure_ascii=False), encoding="utf-8")

    print("\n================ SUMMARY ================")
    print(f"Articles found:      {stats.found}")
    print(f"Deep articles:       {stats.harvested}")
    print(f"PDFs downloaded:     {stats.downloaded}")
    print(f"Skipped (no PDF):    {stats.skipped}")
    print(f"Failed:              {stats.failed}")
    print(f"Manifest:            {manifest_path}")
    print(f"Errors log:          {errors_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
