#!/usr/bin/env python3
"""Extract full text from the Health & Safety reference library — IRIS,
Odyssey, and Healthy Working Plus (Cardinus) — committed under
'library/Health and Safety/<System>/'.

Unlike extract_sharepoint.py there's no zip/release-asset step here: this
is a small, hand-curated set of documents Kevin approved individually
(see CORITY-FEASIBILITY.md's sibling investigation note in HANDOVER.md,
1 August 2026 session 3), already committed directly under
'library/Health and Safety/'. This script just walks that folder,
extracts text from every .docx/.pdf/.xlsx using the same technique as
extract_sharepoint.py (docx: strip word/document.xml tags; pdf: pypdf),
plus a new xlsx path (openpyxl, flattened row-by-row), and writes:

  data/hs-library-fulltext.json   filename -> extracted text
  data/hs-library-files.json      filename -> repo path (library/...)

mirroring extract_sharepoint.py's two output files exactly, so
build_index.py's load_hs_library_docs() can merge them the same way.

Per-document title/system/topic-group/summary metadata lives in
data/hs-library-docs.json, maintained by hand (14 documents, not a
scraped harvest) — this script does not touch that file.
"""
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library", "Health and Safety")
OUT = os.path.join(ROOT, "data", "hs-library-fulltext.json")
FILES_OUT = os.path.join(ROOT, "data", "hs-library-files.json")

MAX_CHARS_PER_DOC = 60_000


def docx_text(path):
    """Pull paragraph text out of a .docx (it's a zip of XML) — identical
    approach to extract_sharepoint.py's docx_text()."""
    with zipfile.ZipFile(path) as zf:
        with zf.open("word/document.xml") as fh:
            xml = fh.read().decode("utf-8", errors="replace")
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


def xlsx_text(path):
    """Flatten every populated row of every sheet into readable
    '|'-separated lines, one sheet heading per block. Good enough for
    chunking/search — this is reference/schema data (permissions
    matrices, data flows), not meant to render as a formatted table."""
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    lines = []
    for ws in wb.worksheets:
        lines.append(f"## {ws.title}")
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() for c in row if c is not None and str(c).strip() != ""]
            if cells:
                lines.append(" | ".join(cells))
        lines.append("")
    return "\n".join(lines).strip()


def main():
    if not os.path.isdir(LIB):
        print(f"No {LIB} directory - nothing to extract.", file=sys.stderr)
        return 1

    out, files_map, failed = {}, {}, 0
    for dirpath, _dirs, files in os.walk(LIB):
        for name in files:
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            files_map[name] = rel
            if ext not in ("docx", "pdf", "xlsx"):
                continue
            try:
                if ext == "docx":
                    text = docx_text(path)
                elif ext == "pdf":
                    text = pdf_text(path)
                else:
                    text = xlsx_text(path)
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
