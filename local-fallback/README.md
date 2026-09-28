# Local fallback (temporary)

This folder exists **only until Microsoft Graph access is granted**. Once the
GitHub Action can read SharePoint directly, **this entire folder can be deleted**
(along with the `.password` file at the repo root) and nothing else changes.

- `Update Website.command` — double-click on Adam's Mac to rebuild the site from
  the OneDrive-synced SharePoint folder and push it. Requires: macOS, Python 3,
  the synced archive folder, a GitHub sign-in, and a `.password` file at the repo root.

The real model is the cloud one: `.github/workflows/publish.yml` runs nightly and
on demand, using `scripts/build_site.py --source graph`. That script is shared and
must stay at the repo root.
