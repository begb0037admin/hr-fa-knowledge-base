#!/usr/bin/env python3
"""Shared Voyage contextual-embedding and Cloudflare Vectorize helpers.

The knowledge-base index identifies a document by its existing stable source
field (normally ``p`` or ``f``).  Chunk positions are then the ordered
positions of that document's entries in kb-index.json.  Keeping that mapping
here gives the backfill, incremental rebuild, and browser the same identity.
"""
import hashlib
import json
import os

VOYAGE_URL = "https://api.voyageai.com/v1/contextualizedembeddings"
VECTORIZE_BASE_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{account_id}"
    "/vectorize/v2/indexes/{index_name}"
)
VOYAGE_MODEL = "voyage-context-3"
OUTPUT_DIMENSION = 1024
MAX_VOYAGE_DOCUMENTS = 1000
MAX_VOYAGE_TOKENS = 120_000
MAX_VOYAGE_CHUNKS = 16_000
MAX_DOCUMENT_TOKENS = 32_000
MAX_VECTORIZE_UPSERT = 5000
MAX_VECTORIZE_DELETE = 1000


def document_key(doc):
    """Return the stable identity already present in a kb.json document.

    ``p`` is the generated document URL for articles and local documents;
    ``f`` is the source filename for records that have no URL.  A few curated
    records carry an explicit ``id``.  The final fallback is deterministic
    source + title for older/hand-authored records without either field.
    """
    for field in ("id", "p", "f"):
        value = doc.get(field)
        if value is not None:
            value = str(value).strip()
            if value:
                return value
    return "\x1f".join((str(doc.get("src") or "").strip(),
                         str(doc.get("t") or "").strip()))


def content_hash(chunks):
    """Hash the ordered chunk texts, including boundaries and Unicode."""
    payload = json.dumps(list(chunks), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def vector_id(doc_key, chunk_index):
    """Return a Vectorize-safe, deterministic ID for one document chunk."""
    raw = f"{doc_key}\x00{chunk_index}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def group_index_chunks(kb, index):
    """Group kb-index.json's ``{d, x}`` rows by document in index order."""
    chunks_by_doc = [[] for _ in kb]
    for item in index:
        doc_index = item["d"]
        if not isinstance(doc_index, int) or doc_index < 0 or doc_index >= len(kb):
            raise ValueError(f"kb-index entry has invalid document index: {doc_index!r}")
        chunks_by_doc[doc_index].append(str(item.get("x", "")))

    groups = []
    seen = set()
    for doc, chunks in zip(kb, chunks_by_doc):
        key = document_key(doc)
        if key in seen:
            raise ValueError(f"duplicate document key in kb.json: {key!r}")
        seen.add(key)
        groups.append({"doc_key": key, "chunks": chunks})
    return groups


def _estimate_tokens(text):
    """Conservative character estimate used to stay below Voyage limits."""
    return max(1, (len(text) + 2) // 3)


def _voyage_batches(groups):
    batch = []
    batch_tokens = 0
    batch_chunks = 0
    for group in groups:
        chunks = group["chunks"]
        group_tokens = sum(_estimate_tokens(chunk) for chunk in chunks)
        group_chunks = len(chunks)
        if group_tokens > MAX_DOCUMENT_TOKENS:
            raise ValueError(
                f"document {group['doc_key']!r} exceeds Voyage's 32K-token inner-list limit"
            )
        if group_chunks > MAX_VOYAGE_CHUNKS:
            raise ValueError(
                f"document {group['doc_key']!r} exceeds Voyage's 16K-chunk request limit"
            )
        would_overflow = (
            batch and (
                len(batch) >= MAX_VOYAGE_DOCUMENTS
                or batch_tokens + group_tokens > MAX_VOYAGE_TOKENS
                or batch_chunks + group_chunks > MAX_VOYAGE_CHUNKS
            )
        )
        if would_overflow:
            yield batch
            batch = []
            batch_tokens = 0
            batch_chunks = 0
        batch.append(group)
        batch_tokens += group_tokens
        batch_chunks += group_chunks
    if batch:
        yield batch


def _requests_module():
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("The requests library is required for embedding sync") from exc
    return requests


def embed_documents(groups, api_key=None, verbose=True):
    """Embed grouped document chunks and return ``doc_key -> embeddings``.

    Empty documents are retained in the input groups but do not need a Voyage
    call.  Non-empty groups are sent as nested ``inputs`` lists so each
    document's chunks receive contextualised embeddings together.
    """
    groups = [group for group in groups if group["chunks"]]
    if not groups:
        return {}
    api_key = api_key or os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise RuntimeError("VOYAGE_API_KEY is not set")
    requests = _requests_module()
    output = {}
    batches = list(_voyage_batches(groups))
    for batch_number, batch in enumerate(batches, 1):
        if verbose:
            print(
                f"Voyage batch {batch_number}/{len(batches)}: "
                f"{len(batch)} documents, {sum(len(g['chunks']) for g in batch)} chunks",
                flush=True,
            )
        response = requests.post(
            VOYAGE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": [group["chunks"] for group in batch],
                "model": VOYAGE_MODEL,
                "input_type": "document",
                "output_dimension": OUTPUT_DIMENSION,
                "output_dtype": "float",
            },
            timeout=180,
        )
        if not response.ok:
            raise RuntimeError(
                f"Voyage HTTP {response.status_code}: {response.text[:200]}"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("Voyage returned invalid JSON") from exc
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise RuntimeError("Voyage returned an unrecognised response shape")

        received = set()
        for document_result in data:
            outer_index = document_result.get("index")
            if not isinstance(outer_index, int) or not 0 <= outer_index < len(batch):
                raise RuntimeError("Voyage returned an invalid document index")
            group = batch[outer_index]
            chunk_results = document_result.get("data")
            if not isinstance(chunk_results, list):
                raise RuntimeError("Voyage returned an invalid chunk list")
            embeddings = [None] * len(group["chunks"])
            for chunk_result in chunk_results:
                chunk_index = chunk_result.get("index")
                embedding = chunk_result.get("embedding")
                if (not isinstance(chunk_index, int) or
                        not 0 <= chunk_index < len(embeddings) or
                        not isinstance(embedding, list)):
                    raise RuntimeError("Voyage returned an invalid chunk embedding")
                embeddings[chunk_index] = embedding
            if any(embedding is None for embedding in embeddings):
                raise RuntimeError(
                    f"Voyage omitted an embedding for document {group['doc_key']!r}"
                )
            output[group["doc_key"]] = embeddings
            received.add(outer_index)
        if len(received) != len(batch):
            raise RuntimeError("Voyage omitted one or more document embeddings")
    return output


def vector_records(groups, embeddings):
    """Turn grouped embeddings into Vectorize upsert records."""
    records = []
    for group in groups:
        values = embeddings.get(group["doc_key"])
        if values is None:
            if group["chunks"]:
                raise ValueError(f"missing embeddings for {group['doc_key']!r}")
            continue
        if len(values) != len(group["chunks"]):
            raise ValueError(f"embedding count mismatch for {group['doc_key']!r}")
        for chunk_index, vector in enumerate(values):
            records.append({
                "id": vector_id(group["doc_key"], chunk_index),
                "values": vector,
                "metadata": {
                    "doc_key": group["doc_key"],
                    "chunk_index": chunk_index,
                },
            })
    return records


def stale_vector_ids(old_documents, new_documents):
    """Return vector IDs present in the old state but absent from the new one."""
    old_ids = {
        vector_id
        for document in old_documents.values()
        if isinstance(document, dict)
        for vector_id in (document.get("vector_ids") or [])
    }
    new_ids = {
        vector_id
        for document in new_documents.values()
        if isinstance(document, dict)
        for vector_id in (document.get("vector_ids") or [])
    }
    return sorted(old_ids - new_ids)


def _vectorize_url(account_id=None, index_name=None, action="upsert"):
    account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    index_name = index_name or os.environ.get("CLOUDFLARE_VECTORIZE_INDEX", "hr-fa-kb")
    if not account_id:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID is not set")
    return f"{VECTORIZE_BASE_URL.format(account_id=account_id, index_name=index_name)}/{action}"


def _mutation_id(response, operation):
    """Extract Cloudflare's acknowledgement ID for an async mutation."""
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Vectorize {operation} returned invalid JSON"
        ) from exc
    result = payload.get("result") if isinstance(payload, dict) else None
    mutation_id = result.get("mutationId") if isinstance(result, dict) else None
    if not isinstance(mutation_id, str) or not mutation_id:
        raise RuntimeError(
            f"Vectorize {operation} response omitted result.mutationId"
        )
    return mutation_id


def upsert_vectors(records, api_token=None, account_id=None, index_name=None,
                   verbose=True):
    """Upsert Vectorize records as NDJSON, at most 5,000 vectors per call."""
    if not records:
        return 0
    api_token = api_token or os.environ.get("CLOUDFLARE_API_TOKEN")
    if not api_token:
        raise RuntimeError("CLOUDFLARE_API_TOKEN is not set")
    requests = _requests_module()
    batches = [records[i:i + MAX_VECTORIZE_UPSERT]
               for i in range(0, len(records), MAX_VECTORIZE_UPSERT)]
    url = _vectorize_url(account_id, index_name, "upsert")
    for batch_number, batch in enumerate(batches, 1):
        if verbose:
            print(
                f"Vectorize upsert {batch_number}/{len(batches)}: "
                f"{len(batch)} vectors",
                flush=True,
            )
        body = "\n".join(json.dumps(record, ensure_ascii=False) for record in batch) + "\n"
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/x-ndjson",
            },
            data=body,
            timeout=180,
        )
        if not response.ok:
            raise RuntimeError(
                f"Vectorize upsert HTTP {response.status_code}: {response.text[:200]}"
            )
        mutation_id = _mutation_id(response, "upsert")
        if verbose:
            print(
                f"Vectorize upsert batch {batch_number} mutationId: {mutation_id}",
                flush=True,
            )
    return len(records)


def delete_vectors(ids, api_token=None, account_id=None, index_name=None,
                   verbose=True):
    """Delete Vectorize IDs in safe-sized batches."""
    ids = list(dict.fromkeys(ids))
    if not ids:
        return 0
    api_token = api_token or os.environ.get("CLOUDFLARE_API_TOKEN")
    if not api_token:
        raise RuntimeError("CLOUDFLARE_API_TOKEN is not set")
    requests = _requests_module()
    batches = [ids[i:i + MAX_VECTORIZE_DELETE]
               for i in range(0, len(ids), MAX_VECTORIZE_DELETE)]
    url = _vectorize_url(account_id, index_name, "delete_by_ids")
    for batch_number, batch in enumerate(batches, 1):
        if verbose:
            print(
                f"Vectorize delete {batch_number}/{len(batches)}: "
                f"{len(batch)} vectors",
                flush=True,
            )
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            json={"ids": batch},
            timeout=180,
        )
        if not response.ok:
            raise RuntimeError(
                f"Vectorize delete HTTP {response.status_code}: {response.text[:200]}"
            )
        mutation_id = _mutation_id(response, "delete")
        if verbose:
            print(
                f"Vectorize delete batch {batch_number} mutationId: {mutation_id}",
                flush=True,
            )
    return len(ids)
