## Claude Quick Load

Paste any URL below directly into Claude chat to load project context:

| File | Raw URL |
|---|---|
| `CLAUDE.md` | https://raw.githubusercontent.com/begb0037admin/hr-fa-knowledge-base/main/CLAUDE.md |

---

# HR Functional Analysis – Knowledge Base Dashboard

A searchable, filterable index of the HR Systems team's knowledge articles and how-to guides, hosted on GitHub Pages as a single self-contained HTML file.

**Live site:** `https://begb0037admin.github.io/hr-fa-knowledge-base/`

---

## What's in the repo

| File | Purpose |
|------|---------|
| `index.html` | The entire dashboard — all 260 documents, search, filters, and upload UI in one file |
| `README.md` | This file |

## Using the dashboard

- **Search** — full-text across title, summary, filename, and system tags
- **Filter** — by source (How To Guides / Change Management) and topic
- **Sort** — newest first, oldest first, A–Z, or source/topic
- **Show archived** — toggle to reveal archived topic entries
- **Open in SharePoint** / **Copy link** — direct access to each document

## Adding new documents

Two ways to add a document to the knowledge base:

### Quick add (browser only)
1. Click **+ Add Document** in the top-right corner
2. Upload the file (optional — reads filename/size) and paste the SharePoint URL
3. Click **✦ Analyse with AI** — Claude will auto-generate a summary and classify the topic and system
4. Review, edit if needed, then **Save to Knowledge Base**

The document is saved to your browser's `localStorage` and shows immediately with a 📎 Local badge. It persists across sessions on that browser.

### Permanent add (for GitHub Pages)
After adding documents locally:
1. Click **⬇ Export HTML** — downloads an updated `index.html` with all local additions baked into the JSON data
2. Replace the `index.html` in this repo with the downloaded file
3. Commit and push — GitHub Pages updates in ~1 minute

```bash
git add index.html
git commit -m "Add [document name] to knowledge base"
git push origin main
```

## Repo setup (first time)

```bash
# Create the repo on GitHub, then:
git clone https://github.com/begb0037admin/hr-fa-knowledge-base.git
cd hr-fa-knowledge-base
cp /path/to/index.html .
git add index.html README.md
git commit -m "Initial knowledge base — 260 documents"
git push origin main
```

Enable GitHub Pages in repo Settings → Pages → Source: `main` branch, `/ (root)`.

---

*Last refreshed: June 2026 · Maintained by HR Functional Analysis team*
