#!/usr/bin/env python3
"""One-time full Voyage contextual-embedding backfill for the KB."""
import json
import os
import sys

import embedding_sync


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_state(path, state):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(temporary, path)


def main():
    data_dir = os.path.join(os.getcwd(), "data")
    kb_path = os.path.join(data_dir, "kb.json")
    index_path = os.path.join(data_dir, "kb-index.json")
    state_path = os.path.join(data_dir, "kb-embedding-state.json")
    processed = vectors_upserted = 0
    failures = []

    try:
        print(f"Loading {kb_path} and {index_path} ...", flush=True)
        kb = _load(kb_path)
        index = _load(index_path)
        groups = embedding_sync.group_index_chunks(kb, index)
        processed = len(groups)
        chunk_count = sum(len(group["chunks"]) for group in groups)
        print(
            f"Loaded {processed} documents and {chunk_count} ordered chunks.",
            flush=True,
        )
        embeddings = embedding_sync.embed_documents(groups, verbose=True)
        records = embedding_sync.vector_records(groups, embeddings)
        vectors_upserted = embedding_sync.upsert_vectors(records, verbose=True)

        documents = {}
        for group in groups:
            documents[group["doc_key"]] = {
                "content_hash": embedding_sync.content_hash(group["chunks"]),
                "vector_ids": [
                    embedding_sync.vector_id(group["doc_key"], chunk_index)
                    for chunk_index in range(len(group["chunks"]))
                ],
            }
        old_documents = {}
        if os.path.exists(state_path):
            try:
                previous = _load(state_path)
                if isinstance(previous, dict) and isinstance(previous.get("documents"), dict):
                    old_documents = previous["documents"]
                else:
                    print(
                        "Embeddings: existing state has no documents map; "
                        "skipping stale-vector deletion.",
                        file=sys.stderr,
                        flush=True,
                    )
            except (OSError, ValueError) as exc:
                print(
                    f"Embeddings: existing state unreadable ({exc}); "
                    "skipping stale-vector deletion.",
                    file=sys.stderr,
                    flush=True,
                )
        stale_ids = embedding_sync.stale_vector_ids(old_documents, documents)
        print(
            f"Embedding reconciliation: {len(stale_ids)} stale vectors to delete.",
            flush=True,
        )
        embedding_sync.delete_vectors(stale_ids, verbose=True)
        state = {
            "version": 1,
            "model": embedding_sync.VOYAGE_MODEL,
            "output_dimension": embedding_sync.OUTPUT_DIMENSION,
            "documents": documents,
        }
        # Vectorize mutations are asynchronous: mutation IDs confirm acceptance,
        # not that the vectors are already queryable. We intentionally write the
        # state after accepted calls without polling; a later server-side failure
        # requires rerunning this backfill rather than being silently retried by
        # the unchanged content hash.
        _write_state(state_path, state)
        print(f"Wrote embedding state to {state_path}.", flush=True)
    except Exception as exc:  # noqa: BLE001 - final summary must include the failure
        failures.append(str(exc))
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)

    print("\nEmbedding backfill summary:", flush=True)
    print(f"  documents processed: {processed}", flush=True)
    print(f"  vectors upserted:    {vectors_upserted}", flush=True)
    print(f"  failures:            {len(failures)}", flush=True)
    for failure in failures:
        print(f"    - {failure}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
