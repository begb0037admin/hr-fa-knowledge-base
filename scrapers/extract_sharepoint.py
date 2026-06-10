#!/usr/bin/env python3
"""Extract full text from the SharePoint document library zips.

Expects the zips (downloaded from SharePoint, attached to the
'sharepoint-docs' GitHub release) to be unpacked under sp_docs/.
Walks every .docx and .pdf, extracts text, and writes
data/sharepoint-fulltext.json mapping filename -> text.

build_index.py picks that file up and gives the SharePoint documents
the same full-text treatment as the help-centre articles.
"""
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sp_docs")
OUT = os.path.join(ROOT, "data", "sharepoint-fulltext.json")

MAX_CHARS_PER_DOC = 60_000


def docx_text(path):
    """Pull paragraph text out of a .docx (it's a zip of XML)."""
    with zipfile.ZipFile(path) as zf:
        with zf.open("word/document.xml") as fh:
            xml = fh.read().decode("utf-8", errors="replace")
    # Paragraph and break tags become newlines, all other tags vanish.
    xml = re.sub(r"</w:p>|<w:br[^>]*/>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    text = (text.replace("&amp;", "&").replace("&lt;", "<")
                .replace("&gt;", ">").replace("&quot;", '"')
                .replace("&apos;", "'"))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def pdf_text(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    return "\n".join(pg.extract_text() or "" for pg in reader.pages).strip()


def main():
    if not os.path.isdir(SRC):
        print(f"No {SRC} directory - nothing to extract.", file=sys.stderr)
        return 1
    # Unzip any zips dropped directly in sp_docs/ first.
    for name in os.listdir(SRC):
        if name.lower().endswith(".zip"):
            print(f"Unpacking {name}...")
            with zipfile.ZipFile(os.path.join(SRC, name)) as zf:
                zf.extractall(SRC)

    out, failed = {}, 0
    for dirpath, _dirs, files in os.walk(SRC):
        for name in files:
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext not in ("docx", "pdf"):
                continue
            path = os.path.join(dirpath, name)
            try:
                text = docx_text(path) if ext == "docx" else pdf_text(path)
            except Exception as exc:  # noqa: BLE001 - log and continue
                print(f"  ! {name}: {exc}", file=sys.stderr)
                failed += 1
                continue
            if text:
                out[name] = text[:MAX_CHARS_PER_DOC]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print(f"Extracted text from {len(out)} documents "
          f"({failed} failed) -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
