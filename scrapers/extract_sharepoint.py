#!/usr/bin/env python3
"""Extract full text from the SharePoint document library zips.

Expects the zips (downloaded from SharePoint, attached to the
'sharepoint-docs' GitHub release) to sit under sp_docs/. Unpacks them
into library/ — which is committed to the repo and served by GitHub
Pages, so every document is downloadable without SharePoint — then
walks every .docx and .pdf, extracts text, and writes
data/sharepoint-fulltext.json mapping filename -> text plus
data/sharepoint-files.json mapping filename -> repo path.

build_index.py picks those up: full text feeds the AI index, and the
file map rewrites each card's link from SharePoint to the Pages copy.
"""
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sp_docs")
LIB = os.path.join(ROOT, "library")
OUT = os.path.join(ROOT, "data", "sharepoint-fulltext.json")
FILES_OUT = os.path.join(ROOT, "data", "sharepoint-files.json")

MAX_CHARS_PER_DOC = 60_000
# GitHub blocks pushes of files over 100 MB; leave headroom.
MAX_FILE_BYTES = 95 * 1024 * 1024
# Windows shortcuts and other junk that has no place in the library.
SKIP_EXTS = {"lnk", "zip", "url", "tmp", "db"}


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
    # Unpack the release zips into the committed library/ folder.
    os.makedirs(LIB, exist_ok=True)
    for name in os.listdir(SRC):
        if name.lower().endswith(".zip"):
            print(f"Unpacking {name} into library/ ...")
            with zipfile.ZipFile(os.path.join(SRC, name)) as zf:
                zf.extractall(LIB)

    out, files_map, failed = {}, {}, 0
    for dirpath, _dirs, files in os.walk(LIB):
        for name in files:
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            path = os.path.join(dirpath, name)
            if ext in SKIP_EXTS:
                os.remove(path)
                continue
            if os.path.getsize(path) > MAX_FILE_BYTES:
                print(f"  ! {name}: over 95 MB, not committable - skipped",
                      file=sys.stderr)
                os.remove(path)
                continue
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            files_map[name] = rel
            if ext not in ("docx", "pdf"):
                continue
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
    with open(FILES_OUT, "w", encoding="utf-8") as fh:
        json.dump(files_map, fh, ensure_ascii=False)
    print(f"Extracted text from {len(out)} documents "
          f"({failed} failed) -> {OUT}")
    print(f"Library holds {len(files_map)} files -> {FILES_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
