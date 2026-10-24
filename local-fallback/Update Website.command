#!/bin/bash
# ============================================================
#  AMP Archive local build and publish. Use until Graph is set up.
#  Double-click to rebuild the website from the synced SharePoint
#  folder and push it to GitHub Pages.
# ============================================================
cd "$(dirname "$0")/.." || exit 1

# ---- The synced SharePoint folder on THIS Mac ----
ARCHIVE_PATH="$HOME/Library/CloudStorage/OneDrive-SharedLibraries-NorthwesternUniversity/Asset Management Practicum Class - Documents/Historical Pitches, Updates, Alumni, Jobs, etc/Website Archive"

# ---- The web address of that SAME folder (for file links) ----
SP_BASE_URL="https://nuwildcat.sharepoint.com/sites/KSM-AMP/Shared%20Documents/Historical%20Pitches%2C%20Updates%2C%20Alumni%2C%20Jobs%2C%20etc/Website%20Archive"

pause () { echo; read -n 1 -s -r -p "Press any key to close..."; exit "$1"; }

echo "==============================================="
echo "   AMP Archive: Rebuild and Publish"
echo "==============================================="
echo
if [ ! -d "$ARCHIVE_PATH" ]; then
  echo "✖ Archive folder not found on this Mac:"; echo "    $ARCHIVE_PATH"
  echo "  Sync it in OneDrive, or edit ARCHIVE_PATH at the top of this file."; pause 1
fi
echo "▶ Reading: $ARCHIVE_PATH"
echo "  Reads names only. For a complete build, right-click the folder,"
echo "   'Always keep on this device' and wait for OneDrive to say 'Up to date'.)"
PW="$(cat .password 2>/dev/null | tr -d "\r\n")"
[ -z "$PW" ] && echo "  No .password file. Site will build with no password gate."
python3 scripts/build_site.py --source local --root "$ARCHIVE_PATH" \
    --base-url "$SP_BASE_URL" --link-mode path --title "AMP Archive" --password "$PW" \
    || { echo "✖ build failed"; pause 1; }
echo

echo "▶ Publishing to GitHub..."
git add docs
git commit -m "Update archive $(date +%Y-%m-%d)" 2>/dev/null || echo "  (no changes to publish)"
git push || { echo "Push failed. Is your GitHub sign-in set up on this Mac?"; pause 1; }

echo
echo "==============================================="
echo "   Done. Site updates in about a minute at:"
echo "   https://kelloggamp.github.io/AMP-archive/"
echo "==============================================="
pause 0
