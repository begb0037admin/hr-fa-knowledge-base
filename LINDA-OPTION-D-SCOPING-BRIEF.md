# Linda — Self-Learning / Compounding Layer (Option D) — Scoping Brief

**Status:** NOT designed, NOT approved for build. This is a list of questions a scoping
session must answer before Option D can be designed or sized — nothing here is a decision.
**Authored:** 27 August 2026, ~10:26 UTC, by Markey.
**Relationship to Option C:** Option C (cross-session *conversation* memory — see
`LINDA-OPTION-C-BUILD-PLAN.md`) is approved and separate. Option D is the larger,
still-undesigned "Linda gets better over time from usage" capability. D is *not* required
for "resume my thread from yesterday" — that's C.

---

## Why this is a scoping brief and not a plan

`ROADMAP.md` has flagged since 31 July 2026 that "self-learning / compounding from usage"
is genuinely different work from conversation memory and "needs its own design before it
can be scoped — what 'compounding' concretely means (a running FAQ digest? weighting search
results by past query success? something else?) hasn't been decided anywhere findable."
That is still true. A design can't start until the questions below have answers.

---

## Questions the scoping session must answer

### 1. What qualifies as "worth learning"?
- An explicit correction Kevin gives Linda in chat ("no, the CR template lives in
  `hris-change-requests`, not here")?
- An explicit instruction ("remember that we call Healthy Working Plus 'DSE'")?
- A frequently-asked question the KB answers poorly or not at all (detected from
  zero-result or low-confidence retrievals)?
- A recurring phrasing that *should* map to a specific document but doesn't rank for it?
- Nothing implicit at all — only things a human explicitly marks?

### 2. Who curates / reviews a candidate learning before it can influence answers?
- Auto-apply immediately (fastest, riskiest)?
- A review queue Kevin approves before anything takes effect (a moderation UI — big scope
  difference)?
- A periodic digest Kevin reads and accepts/rejects in bulk?
- Where does that review happen — in the Linda panel, a separate admin page, a PR against
  a file in this repo?

### 3. How is a wrong learning corrected or removed?
- An edit/delete UI for individual learned items?
- A "forget that" command in chat?
- Versioned, append-only log so any state is reconstructible and a bad batch can be rolled
  back?
- What's the recovery story if a learning silently degrades answers for a week before
  anyone notices?

### 4. How is the learned layer kept from polluting the curated KB?
Linda's current `RETRIEVAL_GOVERNANCE` text makes retrieved KB chunks (`data/kb.json` /
`data/kb-index.json`) the **sole factual authority** and tells the model never to treat a
prior answer as verified evidence. A self-learning layer has to slot in *without breaking
that guarantee*. Which of these is it?
- Learned items become additional **retrievable context** (then: are they visibly labelled
  as "learned, not sourced"? can they ever outrank a real KB doc?)?
- A **system-prompt addendum** (a short "things to keep in mind" block)?
- A **search-ranking signal only** (boost/penalise existing KB chunks by past query
  success — never introduces new claims)?
- Purely a **UX hint** (e.g. "people often also ask…") with no effect on answer content?
- Never written back into `data/kb.json` itself — confirm that's a hard line.

### 5. Versioning and shape
- Is the learned layer an append-only event log, a periodically-rebuilt digest/summary, or
  live editable state?
- Where does it live — Cloudflare KV/D1 bound to the Worker (like Option C), a committed
  file in this repo (reviewable via PR), or both?
- How is a "known-good" version pinned and rolled back to?

### 6. Relationship to Option C
- Does D build **on top of** C's per-identity store, or is it a **single global** "Linda's
  learning" shared across everyone regardless of identity?
- If global, it can ship independently of C. If per-user, it depends on C's identity model
  (currently: keyed on `KB_ACCESS_TOKEN`, i.e. one shared identity) being firmed up first.
- Does answering C's open question #1 (shared vs per-person identity) block D?

### 7. Scope of "self"
- Conversation-derived only, or also **usage analytics** — query frequency, zero-result
  queries, which citations get clicked, dwell time?
- If analytics: that's new client instrumentation + an events store + a privacy position,
  each its own sub-decision.

### 8. Success criteria and drift detection
- How do we know the self-learning is *helping* and not slowly degrading answer quality?
- Is there a held-out set of reference questions to re-run after each learning batch?
- What's the kill switch?

### 9. Privacy, retention, PII
- Learned content will quote real user questions verbatim. Retention limit? Redaction?
- The existing **`data/kb.json` / `data/kb-index.json` data-protection gap** (open on
  `ROADMAP.md` under "Needs Kevin's Action" since 10 July 2026) applies here too and may
  need resolving first.
- Does any learned content ever leave Kevin's Cloudflare account (e.g. into a prompt sent
  to Anthropic)? It already would, if learnings become prompt/context — make that explicit.

---

## What a decision from Kevin would unblock

| Kevin decides… | …which unblocks |
|---|---|
| A concrete definition of "compounding" (Q1) | The design can actually start; the work can be sized |
| Auto-apply vs review-queue (Q2) | Whether a moderation UI is needed — the single biggest scope driver |
| Global vs per-identity (Q6) | Whether D depends on Option C shipping first, or can run in parallel |
| Retrievable-context vs ranking-signal vs prompt-note vs UX-hint (Q4) | The integration surface in `index.html` / `worker.js`, and whether `RETRIEVAL_GOVERNANCE` needs changing |
| Conversation-only vs usage-analytics (Q7) | Whether new client instrumentation + an events store + a privacy stance are in scope |
| Storage shape and location (Q5) | Whether this reuses Option C's KV/D1, adds a committed reviewable file, or both |

Once Q1, Q2, Q4 and Q6 have answers, Option D can be turned into a real build plan the
same shape as `LINDA-OPTION-C-BUILD-PLAN.md`.
