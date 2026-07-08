#!/usr/bin/env python3
"""
Generate AI summaries for Access Group PDF step-by-step guides.

Reads kb.json + kb-index.json, calls Claude to produce a plain-English
summary for each PDF doc, and writes the updated s field back to kb.json.

Usage:
    python scrapers/summarise_docs.py
    python scrapers/summarise_docs.py --force   # re-summarise all, even if s exists
"""
import argparse
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

MODEL = "claude-haiku-4-5-20251001"
MAX_INPUT_CHARS = 5000   # send enough text to get past TOC pages
MAX_TOKENS = 400         # room for a proper summary without sentence caps
RATE_DELAY = 0.4         # seconds between API calls


PROMPT = """\
Below is extracted text from a PeopleXD HR system step-by-step guide titled "{title}".

Summarise what this guide covers in plain English — what the user will learn or be able to do after reading it. Focus on the actual content, not the document header, table of contents, distribution notices, or page numbers. Write as much as needed to give a clear and useful description.

Text:
{text}

Summary:"""


def build_chunk_map(index):
    """Return doc_id -> list of text chunks."""
    doc_chunks = {}
    for item in index:
        doc_chunks.setdefault(item["d"], []).append(item["x"])
    return doc_chunks


def summarise(client, title, text):
    prompt = PROMPT.format(title=title, text=text[:MAX_INPUT_CHARS])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Re-summarise all PDFs even if a summary already exists")
    args = parser.parse_args()

    try:
        import anthropic
    except ImportError:
        raise SystemExit("anthropic package not installed — run: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    with open(os.path.join(DATA, "kb.json"), encoding="utf-8") as f:
        kb = json.load(f)
    with open(os.path.join(DATA, "kb-index.json"), encoding="utf-8") as f:
        index = json.load(f)

    chunk_map = build_chunk_map(index)

    targets = [
        (doc_id, doc) for doc_id, doc in enumerate(kb)
        if doc.get("src") == "Access Group Help Centre" and doc.get("e") == "pdf"
        and (args.force or not doc.get("s") or len(doc.get("s", "")) < 50)
    ]

    print(f"Summarising {len(targets)} PDF guides (model: {MODEL})")

    updated = skipped = errors = 0
    for doc_id, doc in targets:
        chunks = chunk_map.get(doc_id, [])
        text = "\n\n".join(chunks[:5])
        if not text.strip():
            print(f"  SKIP (no text): {doc['t']}")
            skipped += 1
            continue

        print(f"  [{doc_id}] {doc['t']} ...", end=" ", flush=True)
        try:
            doc["s"] = summarise(client, doc["t"], text)
            updated += 1
            print("done")
        except Exception as exc:
            print(f"ERROR: {exc}")
            errors += 1

        time.sleep(RATE_DELAY)

    with open(os.path.join(DATA, "kb.json"), "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False)

    print(f"\nDone — updated: {updated}, skipped: {skipped}, errors: {errors}")
    print(f"kb.json written ({len(kb)} documents)")


if __name__ == "__main__":
    main()
