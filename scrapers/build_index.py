#!/usr/bin/env python3
"""Build the knowledge-base data files consumed by the site.

Inputs:
  data/sharepoint-docs.json   260 SharePoint documents (title/summary/link metadata)
  data/kevin-guides.json      Internally authored guides (Kevin's Guides)
  downloads/manifest.csv      output of access_group_scraper.py (optional)
  downloads/<module>/*.pdf    scraped help-centre PDFs (optional)
  cority/clickhelp/*/*/index.html  output of cority_clickhelp_scraper.py (optional)
  data/hs-library-docs.json   14 curated IRIS/Odyssey/Healthy Working Plus docs (optional)
  data/hs-library-fulltext.json, data/hs-library-files.json  output of extract_hs_library.py (optional)
  data/oxford-signin-directory.json  53 curated Oxford IT sign-in service records (optional)
  data/pxd-services.json      14 curated HRIS Launcher (PeopleXD) service/team/data-protection records (optional)
  data/kb-overrides.json      durable annotations for scraped/mirrored docs, merged in last (optional)
  data/kb.json + kb-index.json  previous build, read (before being overwritten) so unchanged docs keep their "m" date

Outputs:
  data/kb.json        one record per document, drives the cards and filters
  data/kb-index.json  text chunks with doc references, drives AI retrieval
"""
import csv
import hashlib
import json
import os
import re
import sys
from html import unescape
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DOWNLOADS = os.path.join(ROOT, "downloads")
CORITY_CLICKHELP_DIR = os.path.join(ROOT, "cority", "clickhelp")

# Documents mirrored under library/ are served from GitHub Pages, so
# cards and citations never have to send Kevin through SharePoint SSO.
SITE_BASE = "https://begb0037admin.github.io/hr-fa-knowledge-base/"

CHUNK_CHARS = 1400
CHUNK_OVERLAP = 150
MAX_CHUNKS_PER_DOC = 40

def module_slug(label):
    """Manifest stores the display label ('People Management'); the folder
    on disk uses the slug ('people-management')."""
    return label.lower().replace(" ", "-")


def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text):
    """Split on paragraph boundaries into ~CHUNK_CHARS pieces with overlap."""
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) + 1 > CHUNK_CHARS:
            chunks.append(cur)
            cur = cur[-CHUNK_OVERLAP:] + " " + p if CHUNK_OVERLAP else p
        else:
            cur = (cur + "\n" + p) if cur else p
    if cur:
        chunks.append(cur)
    return chunks[:MAX_CHUNKS_PER_DOC]


def load_sharepoint_docs():
    path = os.path.join(DATA, "sharepoint-docs.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_scraped_docs():
    """Read manifest.csv and extract text from each downloaded PDF."""
    manifest = os.path.join(DOWNLOADS, "manifest.csv")
    if not os.path.exists(manifest):
        print("No downloads/manifest.csv - skipping help-centre docs.")
        return []
    try:
        from pypdf import PdfReader
    except ImportError:
        print("pypdf not installed - skipping help-centre text extraction.",
              file=sys.stderr)
        return []
    docs = []
    with open(manifest, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("downloaded") != "yes":
                continue
            module = row["module"]
            slug = module_slug(module)
            pdf_path = os.path.join(DOWNLOADS, slug, row["filename"])
            text = ""
            pages = 0
            if os.path.exists(pdf_path):
                try:
                    reader = PdfReader(pdf_path)
                    pages = len(reader.pages)
                    text = clean_text(
                        "\n".join(pg.extract_text() or "" for pg in reader.pages))
                except Exception as exc:  # noqa: BLE001 - log and continue
                    print(f"  ! text extraction failed for {pdf_path}: {exc}",
                          file=sys.stderr)
            docs.append({
                "t": row["title"],
                "f": row["filename"],
                "p": row["source_url"],
                "pdf": f"downloads/{slug}/{row['filename']}",
                "s": (text[:300] + "...") if len(text) > 300 else text,
                "src": "Access Group Help Centre",
                "tp": module,
                "sy": "PeopleXD",
                "e": "pdf",
                "m": row.get("scraped", ""),
                "pg": pages,
                "_text": text,
            })
    return docs


def load_deep_articles():
    """Read downloads/articles.json (full text of individual help-centre
    articles harvested by the scraper's --deep mode)."""
    path = os.path.join(DOWNLOADS, "articles.json")
    if not os.path.exists(path):
        print("No downloads/articles.json - skipping deep articles.")
        return []
    import time
    today = time.strftime("%Y-%m-%d")
    with open(path, encoding="utf-8") as fh:
        arts = json.load(fh)
    docs = []
    for a in arts:
        text = clean_text(a.get("text", ""))
        docs.append({
            "t": a["title"],
            "p": a["url"],
            "s": (text[:300] + "...") if len(text) > 300 else text,
            "src": "Access Group Help Centre",
            "tp": a.get("module", ""),
            "sy": "PeopleXD",
            "e": "web",
            "m": today,
            "_text": text,
        })
    return docs


def load_kevin_guides():
    """Read data/kevin-guides.json — internally authored guides."""
    path = os.path.join(DATA, "kevin-guides.json")
    if not os.path.exists(path):
        print("No data/kevin-guides.json - skipping Kevin's Guides.")
        return []
    with open(path, encoding="utf-8") as fh:
        guides = json.load(fh)
    docs = []
    for g in guides:
        text = clean_text(g.pop("_text", ""))
        docs.append({**g, "_text": text})
    return docs


def load_oxford_signin_docs():
    """Curated Oxford IT sign-in service directory — 53 hand-authored records
    (service name, sign-in link, guide link, account type), no source
    document to extract from, same self-authored shape as load_kevin_guides().
    Purely additive. As of 19 Aug 2026 this is wired into its own SERVICES
    sidebar section in index.html (Kevin's explicit request), in addition
    to the standalone signin-directory.html reference page added 18 Aug 2026
    (that page and its footer link remain, unchanged)."""
    path = os.path.join(DATA, "oxford-signin-directory.json")
    if not os.path.exists(path):
        print("No data/oxford-signin-directory.json - skipping Oxford IT sign-in directory.")
        return []
    with open(path, encoding="utf-8") as fh:
        entries = json.load(fh)
    docs = []
    for e in entries:
        text = clean_text(e.pop("_text", ""))
        docs.append({**e, "_text": text})
    return docs


def load_pxd_services_docs():
    """Curated HRIS Launcher (pxd.lelitte.co.uk / begb0037admin/hris-launcher)
    reference records — 14 hand-authored entries mirroring that site's own
    sidebar groupings (Service Catalogue, Other Teams, Data Protection),
    added 19 Aug 2026 per Kevin's request to surface the same reference
    data inside this knowledge base. Same self-authored shape as
    load_oxford_signin_docs() / load_kevin_guides(); no source document to
    extract from. Purely additive."""
    path = os.path.join(DATA, "pxd-services.json")
    if not os.path.exists(path):
        print("No data/pxd-services.json - skipping HRIS Launcher (PeopleXD) services.")
        return []
    with open(path, encoding="utf-8") as fh:
        entries = json.load(fh)
    docs = []
    for e in entries:
        text = clean_text(e.pop("_text", ""))
        docs.append({**e, "_text": text})
    return docs


def cority_topic_group(pub_slug):
    """Bucket one of Cority's ~119 ClickHelp publications into a manageable
    sidebar grouping, by product family rather than alphabetically. Verified
    1 August 2026 to cover all 119 known publication slugs with no fallback
    hits — see HANDOVER.md for the full per-bucket breakdown."""
    core = {"cority-user-guide", "cority-system-guide",
            "cority-beta-documentation-publication", "management-system"}
    if pub_slug in core:
        return "Core Product Guides"
    if (pub_slug.startswith("gx2-and-mycority-") or
            pub_slug.startswith("cority-and-mycority-") or
            pub_slug in ("core-and-mycority-ui-ux-enhancements-release-notes",
                          "edx-2024-3-0-new-features-release-notes")):
        return "GX2 & myCority Combined Release Notes"
    if pub_slug.startswith("gx2-") or re.match(r"^cority-20\d\d-", pub_slug):
        return "GX2 / CoreEHS+ Release Notes"
    if pub_slug.startswith("enterprise-"):
        return "Enterprise Release Notes"
    if pub_slug == "mycority" or pub_slug.startswith("mycority-"):
        return "myCority"
    if pub_slug in ("meddbase-help-center", "medical-considerations-march-2023-updates",
                     "drug-database-and-eprescription-guide",
                     "erx-epcs-implementation-and-support-guide",
                     "ergonomics", "rsiguard6"):
        return "Occupational Health & Medical"
    if (pub_slug in ("chemical-management", "emission-factor-library-update-publication",
                      "trireporter", "wesustain") or
            pub_slug.startswith("methodology-") or pub_slug.startswith("spm-") or
            pub_slug.startswith("sustainability-")):
        return "Sustainability & Environmental (SPM)"
    if pub_slug.startswith("scs-") or pub_slug == "supply-chain-sustainability-user-guides-publication":
        return "Supply Chain Sustainability"
    if pub_slug.startswith("readyset"):
        return "ReadySet"
    if pub_slug in ("appsolutions", "cortex-ai", "data-integration-utility-guide",
                     "device-import-utilities-guide", "email-notification-utility-guide",
                     "employee-merge-utility-guide", "fordevelopers",
                     "hr-integration-utility-guide", "report-writer-utility-guide"):
        return "Utilities, Integration & Developer Guides"
    return "Other Cority Publications"  # safety net; should never trigger


def strip_html(html_text):
    """Small tag-stripper for the scraper's saved article HTML — good enough
    for chunking/search text, not meant to preserve structure."""
    html_text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html_text)
    return unescape(text)


def load_cority_clickhelp_docs():
    """Cority (Health & Safety) ClickHelp corpus — see CORITY-FEASIBILITY.md
    and scrapers/cority_clickhelp_scraper.py. No login required for this
    source; content is committed directly under cority/clickhelp/."""
    if not os.path.isdir(CORITY_CLICKHELP_DIR):
        print("No cority/clickhelp/ directory - skipping Cority Health & Safety docs.")
        return []
    import time
    today = time.strftime("%Y-%m-%d")
    docs = []
    for pub_slug in sorted(os.listdir(CORITY_CLICKHELP_DIR)):
        pub_dir = os.path.join(CORITY_CLICKHELP_DIR, pub_slug)
        if not os.path.isdir(pub_dir):
            continue
        for article_slug in sorted(os.listdir(pub_dir)):
            article_path = os.path.join(pub_dir, article_slug, "index.html")
            if not os.path.exists(article_path):
                continue
            with open(article_path, encoding="utf-8") as fh:
                html_content = fh.read()
            title_match = re.search(r"<title>(.*?)</title>", html_content, re.S | re.I)
            title = (unescape(title_match.group(1).strip()) if title_match
                      else article_slug.replace("-", " ").title())
            text = clean_text(strip_html(html_content))
            docs.append({
                "t": title,
                "p": SITE_BASE + quote(f"cority/clickhelp/{pub_slug}/{article_slug}/index.html"),
                "s": (text[:300] + "...") if len(text) > 300 else text,
                "src": "Cority (Health & Safety)",
                "tp": cority_topic_group(pub_slug),
                "sy": "Cority",
                "e": "web",
                "m": today,
                "_text": text,
            })
    return docs


def load_sharepoint_fulltext():
    """Full document text extracted by extract_sharepoint.py, if present."""
    path = os.path.join(DATA, "sharepoint-fulltext.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_sharepoint_files():
    """Filename -> library/ path map written by extract_sharepoint.py."""
    path = os.path.join(DATA, "sharepoint-files.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_hs_library_docs():
    """Curated Health & Safety reference library — IRIS, Odyssey, and
    Healthy Working Plus (Cardinus) — a small, hand-picked set of 14
    documents Kevin approved individually (1 August 2026), distinct from
    the Cority ClickHelp corpus. Source files are committed under
    'library/Health and Safety/<System>/'; metadata (title/topic/system/
    summary) lives in data/hs-library-docs.json, hand-maintained since
    this is a curated set, not a scraped harvest; full text comes from
    scrapers/extract_hs_library.py's two output files. Purely additive —
    same shape/discipline as load_cority_clickhelp_docs()."""
    meta_path = os.path.join(DATA, "hs-library-docs.json")
    if not os.path.exists(meta_path):
        print("No data/hs-library-docs.json - skipping H&S reference library.")
        return []
    with open(meta_path, encoding="utf-8") as fh:
        meta = json.load(fh)
    fulltext_path = os.path.join(DATA, "hs-library-fulltext.json")
    fulltext = {}
    if os.path.exists(fulltext_path):
        with open(fulltext_path, encoding="utf-8") as fh:
            fulltext = json.load(fh)
    files_path = os.path.join(DATA, "hs-library-files.json")
    files_map = {}
    if os.path.exists(files_path):
        with open(files_path, encoding="utf-8") as fh:
            files_map = json.load(fh)
    docs = []
    for m in meta:
        d = dict(m)
        local = files_map.get(d.get("f", ""))
        if local:
            d["p"] = SITE_BASE + quote(local)
        d["_text"] = clean_text(fulltext.get(d.get("f", ""), ""))
        docs.append(d)
    return docs


def apply_overrides(kb, index):
    """Merge data/kb-overrides.json into the finished kb/index lists.

    Scraped and mirrored documents are regenerated from their source PDFs on
    every run, so a hand edit made directly in kb.json / kb-index.json is
    silently lost on the next rebuild. This is the durable place for such
    edits. Each override names exactly ONE document via "match" (all listed
    fields must equal the doc's; use src + f) and may add:
      s_append      text appended to the card summary "s"
      extra_chunks  extra text chunks added to the search index for that doc
    A match that hits zero or several docs is skipped with a warning, never
    guessed at. Re-applying is a no-op (nothing is added twice)."""
    path = os.path.join(DATA, "kb-overrides.json")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        overrides = json.load(fh).get("overrides", [])
    applied = 0
    for ov in overrides:
        match = ov.get("match") or {}
        hits = [i for i, d in enumerate(kb)
                if match and all(d.get(k) == v for k, v in match.items())]
        if len(hits) != 1:
            print(f"  ! kb-overrides: {match} matched {len(hits)} docs "
                  f"(expected exactly 1) - skipped", file=sys.stderr)
            continue
        i = hits[0]
        add = ov.get("s_append")
        if add and add not in kb[i].get("s", ""):
            kb[i]["s"] = (kb[i].get("s", "") + " " + add).strip()
        for ch in ov.get("extra_chunks", []):
            if not any(c["d"] == i and c["x"] == ch for c in index):
                index.append({"d": i, "x": ch})
        applied += 1
    print(f"kb-overrides:  {applied}/{len(overrides)} applied")


def _doc_signature(doc, chunks):
    """Hash of everything about a document EXCEPT its "m" date: every other
    card field plus its ordered search-index chunks."""
    body = {k: v for k, v in doc.items() if k != "m"}
    blob = json.dumps([body, chunks], ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def _chunks_by_doc(kb, index):
    by_doc = [[] for _ in kb]
    for ch in index:
        by_doc[ch["d"]].append(ch["x"])
    return by_doc


def preserve_modified_dates(kb, index):
    """Keep "m" (Modified) stable across rebuilds.

    Several loaders stamp "m" with the build date (deep articles, Cority),
    so a plain rebuild used to rewrite "m" on ~6,000 documents even though
    nothing about them had changed. Here every rebuilt document is compared
    with the previous data/kb.json + data/kb-index.json (read before they are
    overwritten): if its card fields (everything except "m") and its search
    chunks are identical to a previous document, that document keeps its
    previous "m". A document whose text, title, link or any other field
    changed, or that is new, keeps the freshly stamped "m". Matching is by
    content signature, not position, so re-ordering or inserting documents
    cannot misattribute a date. Limit: only the first MAX_CHUNKS_PER_DOC
    chunks of a document are indexed, so a change beyond that cap is not
    seen (same blind spot the search index itself has)."""
    kb_path = os.path.join(DATA, "kb.json")
    idx_path = os.path.join(DATA, "kb-index.json")
    if not (os.path.exists(kb_path) and os.path.exists(idx_path)):
        print("m dates:       no previous kb.json/kb-index.json - all stamped fresh")
        return
    try:
        with open(kb_path, encoding="utf-8") as fh:
            old_kb = json.load(fh)
        with open(idx_path, encoding="utf-8") as fh:
            old_index = json.load(fh)
        old_chunks = _chunks_by_doc(old_kb, old_index)
    except (ValueError, KeyError, IndexError) as exc:
        print(f"  ! m dates: previous data unreadable ({exc}) - all stamped fresh",
              file=sys.stderr)
        return
    previous = {}
    for doc, chunks in zip(old_kb, old_chunks):
        if "m" in doc:
            previous.setdefault(_doc_signature(doc, chunks), []).append(doc["m"])
    new_chunks = _chunks_by_doc(kb, index)
    kept = changed = 0
    for doc, chunks in zip(kb, new_chunks):
        if "m" not in doc:
            continue
        dates = previous.get(_doc_signature(doc, chunks))
        if dates:
            doc["m"] = dates.pop(0)
            kept += 1
        else:
            changed += 1
    print(f"m dates:       {kept} unchanged documents kept their previous date, "
          f"{changed} new/changed documents stamped fresh")


def main():
    sp_docs = load_sharepoint_docs()
    sp_fulltext = load_sharepoint_fulltext()
    sp_files = load_sharepoint_files()
    cority_docs = load_cority_clickhelp_docs()
    hs_library_docs = load_hs_library_docs()
    signin_docs = load_oxford_signin_docs()
    pxd_docs = load_pxd_services_docs()
    ag_docs = (load_scraped_docs() + load_deep_articles() + load_kevin_guides()
               + cority_docs + hs_library_docs + signin_docs + pxd_docs)

    kb, index = [], []
    sp_full = sp_local = 0
    for doc in sp_docs:
        local = sp_files.get(doc.get("f", ""))
        if local:
            doc["p"] = SITE_BASE + quote(local)
            sp_local += 1
        doc_id = len(kb)
        kb.append(doc)
        text = sp_fulltext.get(doc.get("f", ""))
        if text:
            sp_full += 1
            for ch in chunk_text(clean_text(text)):
                index.append({"d": doc_id, "x": ch})
            continue
        body = " ".join(filter(None, [doc.get("t"), doc.get("s"), doc.get("sy")]))
        if body.strip():
            index.append({"d": doc_id, "x": body.strip()})

    for doc in ag_docs:
        text = doc.pop("_text", "")
        doc_id = len(kb)
        kb.append(doc)
        chunks = chunk_text(text) if text else []
        if not chunks:
            chunks = [doc["t"]]
        for ch in chunks:
            index.append({"d": doc_id, "x": ch})

    apply_overrides(kb, index)
    preserve_modified_dates(kb, index)

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "kb.json"), "w", encoding="utf-8") as fh:
        json.dump(kb, fh, ensure_ascii=False)
    with open(os.path.join(DATA, "kb-index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False)

    print(f"kb.json:       {len(kb)} documents "
          f"({len(sp_docs)} SharePoint of which {sp_full} full-text, "
          f"{sp_local} linked to the local library, "
          f"{len(ag_docs)} help centre + Kevin's Guides + Cority + H&S library, "
          f"of which {len(cority_docs)} Cority Health & Safety, "
          f"{len(hs_library_docs)} IRIS/Odyssey/Healthy Working Plus, "
          f"{len(signin_docs)} Oxford IT sign-in directory, "
          f"{len(pxd_docs)} HRIS Launcher / PeopleXD services)")
    print(f"kb-index.json: {len(index)} searchable chunks")


if __name__ == "__main__":
    main()
