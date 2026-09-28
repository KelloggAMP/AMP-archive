# AMP Stock Pitch Archive

A read-only, searchable catalog of the Asset Management Practicum's stock pitches
and updates. It reads the archive where it lives in SharePoint and publishes a
browsable index to GitHub Pages. **It never moves, renames, or changes any file.**

**Live site:** https://kelloggamp.github.io/AMP-archive/

## How it runs (the real model)
`.github/workflows/publish.yml` runs `scripts/build_site.py --source graph`, which
reads one SharePoint site through Microsoft Graph and rewrites `docs/index.html`.

- **Nightly** — automatic, ~09:00 UTC. Faculty just drop files in SharePoint.
- **On demand** — Actions tab → *Publish AMP Archive* → **Run workflow**.

If nothing in the archive changed, the run makes no commit and the site is left alone.

## Required repository secrets
**Settings → Secrets and variables → Actions → _Repository_ secrets** (not environment secrets):

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | app registration Application (client) ID |
| `AZURE_TENANT_ID` | Directory (tenant) ID |
| `SHAREPOINT_SITE_URL` | `https://nuwildcat.sharepoint.com/sites/KSM-AMP` |
| `ARCHIVE_FOLDER` | `Historical Pitches, Updates, Alumni, Jobs, etc/Website Archive` |
| `PAGE_PASSWORD` | the site password (omit and the site publishes with **no** gate) |

Auth uses a GitHub OIDC federated credential — there is **no client secret** to expire.

## Naming

**New files** — drop into a quarter folder (`Winter 2027`), named:

```
Company(TICKER)_YYYY-MM-DD_Type_Name.pptx
Nvidia(NVDA)_2026-10-01_Pitch_Smith.pptx
```

- `Type` is one of: Pitch · Presentation · Model · Report · Update · Feedback
- **Order doesn't matter** and `_` / `-` / spaces are interchangeable — the parser finds
  `(TICKER)`, the date, and the type wherever they sit. Just keep the company next to the
  ticker, since company and presenter are both free text.
- A bare ticker works too (`NVDA_2026-10-01_Pitch_Smith`); the company name is filled in
  from `scripts/ticker_company.json` — edit that file to add any ticker it doesn't know.
- The quarter comes from the folder, so it never needs to be in the filename.
- Anything unreadable still appears on the site with `?`. Rename it in SharePoint and it
  corrects itself on the next nightly run. Nothing is ever moved or renamed for you.

**Legacy** — `PAST AMP STOCK PITCHES & UPDATES` is frozen and never renamed. It's parsed
from its folders (`Company (TICKER)/Updates/file`) by `extract_legacy()`, which is fully
independent of the rules above, so changes to one can't affect the other.

## Access on the site
The page is gated by a password and the catalog is only decoded after it's entered;
`robots.txt` + `noindex` keep crawlers away. This stops bots, **not** determined people —
the files themselves stay protected by SharePoint login.

## Publishing
Pages serves from **`main` / `/docs`**.

## Layout
```
scripts/build_site.py      the builder (graph + local sources)
.github/workflows/         nightly + manual publish
docs/                      the published website
local-fallback/            TEMPORARY - delete once Graph access is live
```
