#!/usr/bin/env python3
"""Build the knowledge-base data files consumed by the site.

Inputs:
  data/sharepoint-docs.json   260 SharePoint documents (title/summary/link metadata)
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DOWNLOADS = os.path.join(ROOT, "downloads")

CHUNK_CHARS = 1400
CHUNK_OVERLAP = 150
MAX_CHUNKS_PER_DOC = 40

MODULE_LABELS = {
    "payroll": "Payroll",
    "people-management": "People Management",
    "workforce-management": "Workforce Management",
    "talent": "Talent",
    "recruitment": "Recruitment",
    "expense": "Expense",
    "pension": "Pension",
    "cross-module": "Cross-module",
}


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
            pdf_path = os.path.join(DOWNLOADS, module, row["filename"])
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
                "pdf": f"downloads/{module}/{row['filename']}",
                "s": (text[:300] + "...") if len(text) > 300 else text,
                "src": "Access Group Help Centre",
                "tp": MODULE_LABELS.get(module, module),
                "sy": "PeopleXD",
                "e": "pdf",
                "m": row.get("scraped", ""),
                "pg": pages,
                "_text": text,
            })
    return docs


def main():
    sp_docs = load_sharepoint_docs()
    ag_docs = load_scraped_docs()

    kb, index = [], []
    for doc in sp_docs:
        doc_id = len(kb)
        kb.append(doc)
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
          f"({len(sp_docs)} SharePoint, {len(ag_docs)} help centre)")
    print(f"kb-index.json: {len(index)} searchable chunks")


if __name__ == "__main__":
    main()
