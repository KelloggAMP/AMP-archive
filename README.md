# AMP Stock Pitch Archive

A read-only, searchable catalog website of the Asset Management Practicum's
historical stock pitches and updates. It reads the files where they live in
SharePoint and publishes a browsable index to GitHub Pages. It never moves,
renames, or changes any files.

**Live site:** https://adamgodina.github.io/amp-archive-test/

## How it works
`scripts/build_site.py` reads the archive (names, folders, links — never file
contents) and writes `docs/index.html`, a self-contained page that GitHub Pages
serves. It has two interchangeable sources that produce the **same** site:

| Source | When | Runs | Needs |
|---|---|---|---|
| **local** | now | your Mac (double-click) | folder synced in OneDrive |
| **graph** | later | GitHub's cloud (a button) | IT grant on one SharePoint site |

## Using it now — LOCAL (no IT)
1. In OneDrive, sync the SharePoint library. For a **complete** build, right-click
   `PAST AMP STOCK PITCHES & UPDATES` → **"Always keep on this device"** and wait
   for OneDrive to say **"Up to date"** (online-only misses files that haven't
   downloaded yet).
2. Double-click **`Update Website.command`** — it rebuilds `docs/` and pushes.
   ~1 minute later the live site updates.

(Manual run: `python3 scripts/build_site.py --source local --root "<folder>" --base-url "<folder-url>"`)

## Switching to GRAPH later (nothing local)
Once IT grants the app read access to the site:
1. Add repo **Secrets** (Settings → Secrets and variables → Actions):
   - `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`
   - `SHAREPOINT_SITE_URL` = `https://nuwildcat.sharepoint.com/sites/KSM-AMP`
   - `ARCHIVE_FOLDER` = `Historical Pitches, Updates, Alumni, Jobs, etc/PAST AMP STOCK PITCHES & UPDATES`
2. **Actions → Publish AMP Archive → Run workflow.**
That's the whole switch — same site, now with canonical per-file links, and you
stop using the local launcher. (See `docs`-nothing else changes.)

## Publish / hosting
- Turn on Pages: **Settings → Pages → Deploy from a branch → `main` / `/docs`.**
- The repo holds only the website + scripts. The pitch files stay in SharePoint;
  the site links out to them (viewers need access to the SharePoint site).

## Layout
```
scripts/build_site.py     the builder (local + graph)
.github/workflows/        the GitHub Action (graph mode)
docs/index.html           the published website
Update Website.command    double-click: local build + publish
```
