#!/usr/bin/env python3
"""
Generate two-level AI summaries for knowledge base documents.

Adds two NEW fields to each matched document in kb.json:
  ss  — short summary (3-4 sentences): purpose, coverage, when to use
  sl  — long  summary (6-10 sentences): detailed content, steps, troubleshooting

The existing `s` field is NEVER modified.

Usage:
    # Diagnostic — print 5 samples, write nothing:
    python scrapers/summarise_enhanced.py --source "Change Management" --limit 5 --dry-run

    # Full run — write ss/sl for all matched docs:
    python scrapers/summarise_enhanced.py --source "Change Management"

    # Re-generate docs that already have ss/sl:
    python scrapers/summarise_enhanced.py --source "Change Management" --force
"""
import argparse
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

MODEL = "claude-haiku-4-5-20251001"
MAX_INPUT_CHARS = 8000   # generous — gets past TOC sections in Word/PDF docs
MAX_TOKENS_SHORT = 220   # 3-4 sentences
MAX_TOKENS_LONG  = 650   # 6-10 sentences
RATE_DELAY = 0.5         # seconds between API calls (avoid rate limits)

PROMPT_SHORT = """\
Below is extracted text from a document titled "{title}" (source: {source}).

Write 3-4 sentences for a knowledge base card preview. The reader is scanning a list of \
documents and needs to quickly decide if this is the one they need. Tell them:
1. What specific process, system, or topic this document covers
2. What task or problem it helps with
3. When or why they would open this document

Rules:
- Do NOT start with "This document" or "This guide" — lead with the subject matter
- Be specific — name actual systems (PeopleXD, CoreTime, WFM, payroll etc), processes, \
or scenarios mentioned in the text
- Skip table of contents lines, page references, version control tables, and distribution lists
- Plain English only
- Output ONLY the summary sentences — no heading, no title line, no markdown, no preamble. \
Start directly with the first sentence.

Text:
{text}

Short summary (3-4 sentences):"""

PROMPT_LONG = """\
Below is extracted text from a document titled "{title}" (source: {source}).

Write a detailed summary of 6-10 sentences. The reader has already decided this document \
is relevant and wants to know exactly what is inside before or while reading it. Cover:
1. What the document contains overall
2. The specific processes, tasks, or steps it describes — include menu paths, screen names, \
or field names where the text mentions them
3. What errors, problems, or scenarios it helps resolve
4. Any specific system names, configuration settings, or integrations referenced
5. Who typically uses this document and in what context

Rules:
- Be specific — name actual processes, systems, and steps from the text
- Skip table of contents lines, page references, version control tables, and distribution lists
- Write as flowing sentences, not bullet points
- If the source text is truncated, summarise only what is present — do not invent content
- Output ONLY the summary sentences — no heading, no title line, no markdown, no preamble. \
Start directly with the first sentence.

Text:
{text}

Detailed summary (6-10 sentences):"""


def build_chunk_map(index):
    """Return doc_id -> joined text from up to 8 chunks."""
    doc_chunks = {}
    for item in index:
        doc_chunks.setdefault(item["d"], []).append(item["x"])
    return {k: "\n\n".join(v[:8]) for k, v in doc_chunks.items()}


def clean_summary(text):
    """Strip leading markdown headings/title lines the model sometimes adds
    despite prompt instructions, so cards always show plain sentences."""
    lines = text.strip().split("\n")
    while lines:
        first = lines[0].strip()
        # Drop heading lines (# ...), bold-only title lines (**...**), and blanks
        if not first or first.startswith("#") or (
            first.startswith("**") and first.rstrip("—- ").endswith("**")
        ):
            lines.pop(0)
        else:
            break
    return "\n".join(lines).strip()


def call_claude(client, prompt, max_tokens):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return clean_summary(resp.content[0].text)


def main():
    parser = argparse.ArgumentParser(
        description="Generate two-level AI summaries (ss + sl) for knowledge base documents."
    )
    parser.add_argument("--source", required=True,
                        help='Document source to process, e.g. "Change Management"')
    parser.add_argument("--type", choices=["pdf", "web"], default=None,
                        help='Restrict to document type within the source (matches the "e" field)')
    parser.add_argument("--limit", type=int, default=0,
                        help="Cap number of documents processed (0 = no cap)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print generated summaries without writing to kb.json")
    parser.add_argument("--force", action="store_true",
                        help="Re-generate even if ss/sl already exist")
    args = parser.parse_args()

    try:
        import anthropic
    except ImportError:
        raise SystemExit("anthropic package not installed — run: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    kb_path = os.path.join(DATA, "kb.json")
    idx_path = os.path.join(DATA, "kb-index.json")

    with open(kb_path, encoding="utf-8") as f:
        kb = json.load(f)
    with open(idx_path, encoding="utf-8") as f:
        index = json.load(f)

    chunk_map = build_chunk_map(index)

    targets = [
        (doc_id, doc) for doc_id, doc in enumerate(kb)
        if doc.get("src") == args.source
        and (args.type is None or doc.get("e") == args.type)
        and (args.force or not doc.get("ss") or not doc.get("sl"))
    ]

    if args.limit:
        targets = targets[:args.limit]

    total_in_source = sum(1 for d in kb if d.get("src") == args.source)
    print(f"Source       : {args.source!r}  ({total_in_source} total docs in source)")
    print(f"Type filter  : {args.type or 'none (all types)'}")
    print(f"To process   : {len(targets)}")
    print(f"Dry run      : {args.dry_run}")
    print(f"Force        : {args.force}")
    print(f"Model        : {MODEL}")
    print()

    updated = skipped = errors = 0

    for doc_id, doc in targets:
        text = chunk_map.get(doc_id, "")
        if not text.strip():
            print(f"  SKIP (no index text): {doc.get('t', '?')}")
            skipped += 1
            continue

        text_input = text[:MAX_INPUT_CHARS]
        title = doc.get("t", "Untitled")
        source = doc.get("src", "")

        print(f"  [{doc_id}] {title}")

        try:
            ss = call_claude(
                client,
                PROMPT_SHORT.format(title=title, source=source, text=text_input),
                MAX_TOKENS_SHORT,
            )
            time.sleep(RATE_DELAY)

            sl = call_claude(
                client,
                PROMPT_LONG.format(title=title, source=source, text=text_input),
                MAX_TOKENS_LONG,
            )
            time.sleep(RATE_DELAY)

            if args.dry_run:
                print(f"    [SS] {ss}")
                print(f"    [SL] {sl}")
                print()
            else:
                doc["ss"] = ss
                doc["sl"] = sl
                print(f"    ✓ ss: {ss[:100]}…")

            updated += 1

        except Exception as exc:
            print(f"    ERROR: {exc}")
            errors += 1
            time.sleep(1)

    print()
    print(f"Done — updated: {updated}  skipped: {skipped}  errors: {errors}")

    if not args.dry_run and updated > 0:
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False)
        print(f"kb.json written ({len(kb)} documents total, {updated} newly enhanced)")
    elif args.dry_run:
        print("Dry run complete — kb.json was NOT modified.")
    else:
        print("Nothing to write.")


if __name__ == "__main__":
    main()
