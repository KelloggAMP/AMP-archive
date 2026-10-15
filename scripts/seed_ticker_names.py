#!/usr/bin/env python3
"""
Fill gaps in ticker_company.json from the SEC's official ticker list.

Run LOCALLY and on demand (e.g. after consolidating a new quarter). The SEC
requires a contact in the User-Agent, so it is read from the environment and
never stored in this repo:

    SEC_CONTACT="AMP Archive you@northwestern.edu" python3 scripts/seed_ticker_names.py <folder>

<folder> is scanned for filenames; any ticker it finds that has no company name
is looked up and added. Existing entries are NEVER overwritten - human-curated
names and manual corrections always win.
"""
import json, os, re, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
LOOKUP = HERE / "ticker_company.json"
SEC_URL = "https://www.sec.gov/files/company_tickers.json"
sys.path.insert(0, str(HERE))
import build_site as P

SUFFIXES = re.compile(r"[,.]?\s+(inc|corp|corporation|co|ltd|plc|sa|nv|ag|lp|llc|holdings?|"
                      r"group|company|the|/\w+)\.?$", re.I)


def tidy(name):
    """'CRACKER BARREL OLD COUNTRY STORE, INC /DE/' -> 'Cracker Barrel Old Country Store'."""
    n = re.sub(r"\s+", " ", (name or "").strip(" .,"))
    n = re.sub(r"\s*/[A-Za-z]{2,}/?\s*$", "", n)      # SEC state markers: /DE/, /CN
    if (n.isupper() or n.islower()) and len(n.replace(" ", "")) > 4:
        n = n.title()                                  # leave short acronyms (NVR, BALL) alone
    prev = None
    while prev != n:                      # strip trailing legal suffixes
        prev = n
        n = SUFFIXES.sub("", n).strip(" .,")
    return n or None


def sec_table(contact):
    req = urllib.request.Request(SEC_URL, headers={"User-Agent": contact})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    return {v["ticker"].upper(): v["title"] for v in data.values()}


def tickers_in(folder):
    found = set()
    for f in Path(folder).rglob("*"):
        if f.is_file() and f.suffix.lower() in P.PITCH_EXTS:
            r = P.extract_modern([f.name], f.stem, f.suffix)
            tk = r["ticker"] or P._bare_ticker(f.stem)
            if tk:
                found.add(tk)
    return found


def main():
    contact = os.environ.get("SEC_CONTACT")
    if not contact or "@" not in contact:
        sys.exit('Set SEC_CONTACT first, e.g.\n  SEC_CONTACT="AMP Archive you@northwestern.edu" '
                 'python3 scripts/seed_ticker_names.py <folder>')
    if len(sys.argv) < 2:
        sys.exit("usage: seed_ticker_names.py <folder to scan>")

    current = json.loads(LOOKUP.read_text()) if LOOKUP.exists() else {}
    wanted = {t for t in tickers_in(sys.argv[1]) if t not in current}
    if not wanted:
        print("Nothing missing - every ticker already has a company name.")
        return

    print(f"Looking up {len(wanted)} unknown ticker(s) via SEC...")
    table = sec_table(contact)
    added, missed = {}, []
    for t in sorted(wanted):
        name = tidy(table.get(t))
        (added.__setitem__(t, name) if name else missed.append(t))

    current.update(added)
    LOOKUP.write_text(json.dumps(dict(sorted(current.items())), indent=1))
    print(f"Added {len(added)}; lookup now holds {len(current)}.")
    for t, n in sorted(added.items()):
        print(f"  {t:6} -> {n}")
    if missed:
        print(f"Not found in SEC (add by hand if you want them): {', '.join(missed)}")


if __name__ == "__main__":
    main()
