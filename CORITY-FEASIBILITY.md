# Cority Knowledge Base — Feasibility Findings

**Status:** Feasibility confirmed via direct testing, 31 July 2026. Not yet built — this document records what was proven, how it was proven, and the recommended build approach, so the next session can pick this up without re-deriving it.

**Owner:** Kevin Lelitte · **Source:** Live technical investigation against `uc.cority.com` and `userdocs.cority.com`, credentials supplied by Kevin for this session only, never stored.

---

## 1. Summary

Cority — the University's Occupational Health / H&S management system — turns out to have **two independent public-facing content sources**, both technically viable to bring into this knowledge base, one of them considerably easier than anything the Access Group build required.

| Source | Platform | Login required? | Build difficulty |
|---|---|---|---|
| `userdocs.cority.com` | ClickHelp (commercial docs platform) | No | Low — plain HTTP, no browser needed |
| `uc.cority.com` | Salesforce Experience Cloud (Aura) | Yes | Medium — same shape of work as the existing Access Group scraper |

**Recommendation:** build the ClickHelp side first (no open unknowns, largest known content volume), then the Salesforce Community side second, reusing the existing `access_group_scraper.py` login pattern.

---

## 2. Source 1 — `userdocs.cority.com` (ClickHelp)

Confirmed via response headers (`ASP.NET_SessionId`/`ch_uid` cookies, CSP referencing `*.clickhelp.com`) to be running **ClickHelp**, a commercial documentation platform — not Salesforce, not related to the Community side.

**Discovery:** a public sitemap index exists at `https://userdocs.cority.com/sitemaps/sitemap.xml`, listing **119 separate "publication" sitemaps** (one per manual/guide). Each publication sitemap lists every article's clean URL slug — full inventory available with no crawling.

Publications most relevant to CoreEHS+(GX2) & myCority:

| Publication | Articles |
|---|---|
| `cority-user-guide` | 939 |
| `cority-system-guide` | 73 |
| `mycority` | 94 |
| `mycority-it-setup` | not yet counted |
| ~30 dated GX2/myCority release-notes publications | not yet counted |

**Content endpoint:** the article reader is a client-side app (hash-fragment routed, `#!publication/slug`), but it calls:

```
POST https://userdocs.cority.com/helper/articles/{publication-slug}/{article-slug}/
```

This returns clean JSON — `title`, `projectName`, and a `viewFrameHtml` field containing the full article body as real structured HTML (`<h2>`/`<h4>` headings, `<ul>/<li>` lists, `<img>` tags). **No login required** — verified with a completely fresh, cookie-free request.

**Verified across 4 different publications** (`cority-user-guide`, `cority-system-guide`, `mycority`, `mycority-it-setup`, plus one release-notes publication), not just one — the pattern generalises. One timing quirk found: the first article load after switching into a new publication needs noticeably longer than a simple page-load wait before the content call fires (a client-side app-init delay, not a failure) — worth building a proper wait condition around this rather than a fixed short timeout.

**Images:** referenced as relative paths, e.g. `/resources/Storage/cority-user-guide/WebHelp/CorityUserGuide/ManagementOfChange/MOC_change_requests_select_type.gif`. Confirmed fetchable with **zero authentication, zero cookies** — and confirmed *visually*, not just by HTTP status, to be genuine screenshot content (a real step-by-step graphic), not a placeholder. No known auth trap on this side.

---

## 3. Source 2 — `uc.cority.com` (Salesforce Community)

Confirmed Salesforce Experience Cloud running the Aura framework (`Server: sfdcedge` headers, `aura_prod.js`, `siteforce:loginApp2` login app) — the same platform family as Access Group's `accessgroup.my.site.com`, but a separate org.

**Login flow (plain email/password, not SSO):**
1. `https://uc.cority.com/s/` → unauthenticated visitors are redirected to `/UCLogin` (an older Visualforce login-chooser page, not the Aura app)
2. Click the **"All Other Cority Users"** tile exactly — a loose text-match selector wrongly clicked a different tile ("Contact community@cority.com") during testing; must use an exact-text locator
3. This lands on `https://uc.cority.com/s/login/?language=en_US&param=Cority&startURL=%2Fs%2F` — the real Aura login form
4. Email/password fields use Aura-generated dynamic IDs containing colons (e.g. `178:0`) — a plain CSS `#id` selector breaks on these; must use an attribute selector (`[id='178:0']`)
5. Submit → lands authenticated at `https://uc.cority.com/s/`

This is the same shape of login flow `access_group_scraper.py`'s `do_login()` already handles (Playwright browser context, fill + submit, verify by absence of the login form) — expected to be directly reusable/adaptable, not a new pattern.

**Content is genuine Salesforce Knowledge Articles**, not arbitrary web pages. Article pages render standard Knowledge Article fields (Title, URL Name, Body, Article Type) and the network capture during page load shows Aura RPC calls to `RecordServiceComponent.getArticleVersionId` and `RichText.getParsedRichTextValue` — the real Knowledge Article body fetch. Article URLs are clean slugs: `/s/article/{Title-Slug}`.

**Bulk enumeration — solved via Coveo.** The Community search is backed by a dedicated external Coveo search API:

```
POST https://corityproductionhx5oknmn.org.coveo.com/rest/search/v2
```

Confirmed working and authenticated-session-aware: returns `totalCount`, pagination, and structured per-result metadata (`title`, `uri`, `clickUri`, `excerpt`) for genuine Knowledge Articles — confirmed via `article:kA8OF...`-format IDs in result URIs (the standard Salesforce Knowledge Article Version ID prefix). This gives full-catalogue discovery equivalent to what the ClickHelp sitemap provides for free. Searching the single common word "the" returned `totalCount: 11,673` across the whole index — not a clean Knowledge-only figure (the index likely also holds Cases, Ideas, etc.), but confirms a large real corpus. **Getting an exact Knowledge-only count via a content-type facet filter is an open item before build.**

**Images — the one real trap found in this whole investigation.** Screenshots embedded in Knowledge Article rich text are served via:

```
https://uc.cority.com/servlet/rtaImage?eid={articleId}&feoid={fieldId}&refid={attachmentId}
```

This endpoint returns **`HTTP 200 OK` regardless of authentication.** Without a valid session, it silently returns a generic Salesforce placeholder PNG reading *"Image Not Available — You don't have the privileges to see it, OR it has been removed from the system"* (confirmed exact size in testing: 2,846 bytes) — not a 403, not an error, a normal-looking successful image response. With a valid authenticated session (same cookies as the login above), the same URL returns the real screenshot (confirmed visually — a genuine instructional image, 124,197 bytes in the tested case).

**Any Salesforce-side image download step must:**
- Reuse the authenticated browser/session context for every image fetch, never an anonymous request
- Verify downloaded images aren't the placeholder before trusting them (by size/hash — do not assume HTTP 200 means success)

This same failure mode should be assumed possible anywhere else Salesforce-hosted images are pulled without an authenticated session — this is exactly the reason §5 below flags the Access Group/PeopleXD side as needing revisiting, not just a Cority-specific caveat.

---

## 4. Recommended architecture

- **Storage format: local HTML, not PDF**, for both sources. The source content is already structured rich HTML — converting to PDF would lose animated GIFs and add print-pagination artifacts for no benefit. This is consistent with the existing scraper's own `render_pdf()` fallback already being labelled a last resort, not a preferred path.
- **Hosting: committed into this repo (`hr-fa-knowledge-base`), served via GitHub Pages** (`https://begb0037admin.github.io/hr-fa-knowledge-base/`) — the same pattern already used for the 567 existing PDFs (`downloads/`) and 260 SharePoint docs (`library/`). Never left only on a local machine, per the project's GitHub-only working rule.
- **Images must be explicitly downloaded and rehosted alongside the HTML**, not left as external links — this is not automatic. Every `<img src>` needs its bytes fetched (with the authentication caveats above for the Salesforce side) and the HTML rewritten to point at the local copy.
- **Execution: GitHub Actions**, modelled directly on the existing `.github/workflows/scrape-help-centres.yml` — Playwright + Chromium on a cloud Linux runner, credentials from GitHub Actions secrets (new secrets needed, e.g. `CORITY_USERNAME` / `CORITY_PASSWORD`), commits results back to `main`. Note: the existing Access Group workflow is **manually triggered** (`workflow_dispatch`) only, not scheduled — stating this accurately since an earlier draft of this plan incorrectly assumed it was automatic. Add a `schedule:` trigger if automatic refresh is wanted; not present today.
- **Build order:** ClickHelp first (no open unknowns, plain HTTP, no login, largest known volume) → Salesforce Community second (needs the authenticated Playwright flow, the Coveo enumeration call, and the image placeholder safety check).

---

## 5. Open items before build begins

- Get an exact Knowledge-Article-only count via a Coveo content-type facet filter, rather than the mixed 11,673 figure
- Decide whether to add a `schedule:` trigger to the new workflow for automatic refresh, or keep it manual-trigger-only like the existing one
- **Separate follow-up, not part of this build — revisit the Access Group/PeopleXD scraper to add image preservation.** Its current deep-crawl path (`harvest_article_texts()` in `access_group_scraper.py`) extracts `innerText` only and drops all images from the ~1,948 web articles today — the same placeholder-trap risk described in §3 applies there too, since Access Group's Salesforce org hosts images the same way. Explicitly deferred by Kevin (31 July 2026) to a later session. **Tracked as its own scoped entry in `ROADMAP.md` → "Parked — Technical Debt"** — see that file for the concrete step-by-step fix, so it isn't lost and doesn't need to be re-derived from this document.

---

## 6. How this was verified (not just asserted)

Every claim above was tested directly, not inferred from documentation, including catching and correcting two mistakes along the way:
- A loose text-selector click during login testing hit the wrong UI tile — fixed by switching to an exact-text locator
- An early pass on the ClickHelp screenshot checked only HTTP status and byte count, not the actual image content — given the Salesforce-side placeholder trap found immediately after, that check was redone visually and confirmed genuine

See also `knowledge-base-playbook` → Section 13, "Recommendations for Expansion" → "Cority (Health & Safety) — in progress" for a pointer back to this document from the general methodology reference, and `ROADMAP.md` in this repo for the separate Access Group image-preservation follow-up task referenced in §5.
