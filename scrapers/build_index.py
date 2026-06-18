#!/usr/bin/env python3
"""Build the knowledge-base data files consumed by the site.

Inputs:
  data/sharepoint-docs.json   260 SharePoint documents (title/summary/link metadata)
  data/kevin-guides.json      Internally authored guides (Kevin's Guides)
  downloads/manifest.csv      output of access_group_scraper.py (optional)
  downloads/<module>/*.pdf    scraped help-centre PDFs (optional)

Outputs:
  data/kb.json        one record per document, drives the cards and filters
  data/kb-index.json  text chunks with doc references, drives AI retrieval
"""
import csv
import json
import os
import re
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DOWNLOADS = os.path.join(ROOT, "downloads")

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


def main():
    sp_docs = load_sharepoint_docs()
    sp_fulltext = load_sharepoint_fulltext()
    sp_files = load_sharepoint_files()
    ag_docs = load_scraped_docs() + load_deep_articles() + load_kevin_guides()

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

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "kb.json"), "w", encoding="utf-8") as fh:
        json.dump(kb, fh, ensure_ascii=False)
    with open(os.path.join(DATA, "kb-index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False)

    print(f"kb.json:       {len(kb)} documents "
          f"({len(sp_docs)} SharePoint of which {sp_full} full-text, "
          f"{sp_local} linked to the local library, "
          f"{len(ag_docs)} help centre + Kevin's Guides)")
    print(f"kb-index.json: {len(index)} searchable chunks")


if __name__ == "__main__":
    main()
