# AMP Stock Pitch Archive

A read-only, searchable catalog of the Asset Management Practicum's stock pitches and
updates. It reads the archive where it lives in SharePoint and publishes a browsable
index to GitHub Pages. It never moves, renames, or changes any file.

Live site: https://kelloggamp.github.io/AMP-archive/

## How it runs

`.github/workflows/publish.yml` runs `scripts/build_site.py --source graph`, which reads
one SharePoint site through Microsoft Graph and rewrites `docs/index.html`.

- Nightly, around 09:00 UTC. Faculty just drop files in SharePoint.
- On demand: Actions tab, *Publish AMP Archive*, **Run workflow**.

If nothing in the archive changed, the run makes no commit.

The nightly schedule is currently commented out. Re-enable it once the Graph secrets below
are set, or every run fails and emails you.

## Required repository secrets

Settings, Secrets and variables, Actions, **Repository** secrets (not environment secrets):

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | app registration Application (client) ID |
| `AZURE_TENANT_ID` | Directory (tenant) ID |
| `SHAREPOINT_SITE_URL` | `https://nuwildcat.sharepoint.com/sites/KSM-AMP` |
| `ARCHIVE_FOLDER` | `Historical Pitches, Updates, Alumni, Jobs, etc/Website Archive` |
| `PAGE_PASSWORD` | site password. Omit it and the site publishes with no gate. |

Auth uses a GitHub OIDC federated credential, so there is no client secret to expire.

## Naming

New files go in a quarter folder (`Winter 2027`), named:

```
Company(TICKER)_YYYY-MM-DD_Type_Name.pptx
Nvidia(NVDA)_2026-10-01_Pitch_Smith.pptx
```

- `Type` is one of: Pitch, Presentation, Model, Report, Update, Feedback.
- Order does not matter, and `_` `-` and spaces are interchangeable. The parser finds
  `(TICKER)`, the date, and the type wherever they sit. Keep the company next to the
  ticker, since company and presenter are both free text.
- A bare ticker works too (`NVDA_2026-10-01_Pitch_Smith`). The company name comes from
  `scripts/ticker_company.json`.
- The quarter comes from the folder, so it never needs to be in the filename.
- Anything unreadable still appears on the site with `?`. Rename it in SharePoint and it
  corrects itself on the next run. Nothing is ever moved or renamed for you.

### Company names

`scripts/ticker_company.json` maps ticker to company. An unknown ticker is looked up once
via Yahoo during the build and written back, so it is never looked up twice. A failed
lookup leaves the company blank and never breaks a run.

To bulk-fill after a large import, run locally:

```
SEC_CONTACT="AMP Archive you@northwestern.edu" python3 scripts/seed_ticker_names.py <folder>
```

SEC requires a contact in the request header. It is read from the environment and never
stored in this repo.

### Legacy archive

`PAST AMP STOCK PITCHES & UPDATES` is frozen and never renamed. `extract_legacy()` parses
it from its folders (`Company (TICKER)/Updates/file`) and is independent of the rules
above, so changes to one cannot affect the other.

It has no quarter folders, so the quarter is estimated from the file date: Winter is
January to mid-March, Spring is late March to June, Fall is September to December.

The Quarter column therefore mixes stated values (new files, read from the folder) with
estimated ones (legacy, derived from the date), and does not distinguish them. Estimates
follow real AMP session boundaries but are inferred. A legacy file with no readable date
has no quarter.

## Access

The page is gated by a password, and the catalog is only decoded after it is entered.
`robots.txt` and `noindex` keep crawlers away. This stops bots, not determined people.
The files themselves stay protected by SharePoint login.

## Publishing

Pages serves from `main` / `/docs`.

## Layout

```
scripts/build_site.py        builder, graph and local sources
scripts/seed_ticker_names.py bulk-fill company names from SEC
.github/workflows/           nightly and manual publish
docs/                        the published site
local-fallback/              temporary, delete once Graph access is live
```
