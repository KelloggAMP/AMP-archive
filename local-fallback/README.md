# Local fallback

Temporary. Once Graph access is granted, delete this whole folder and the
`.password` file at the repo root. Nothing else changes.

`Update Website.command` rebuilds the site from the OneDrive-synced SharePoint
folder and pushes it. Needs macOS, Python 3, the synced folder, a GitHub
sign-in, and a `.password` file at the repo root.

The real model is `.github/workflows/publish.yml`, which runs
`scripts/build_site.py --source graph`. That script stays at the repo root.
