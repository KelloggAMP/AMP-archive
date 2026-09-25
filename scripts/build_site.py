#!/usr/bin/env python3
"""
AMP Stock Pitch Archive — site builder.

Builds docs/index.html: one self-contained, searchable catalog website of the
archive. ONE script, TWO sources — both produce the identical page, so moving
from local to Graph changes nothing students see.

  LOCAL  (now, no IT needed) — read a OneDrive-synced folder on this computer:
      python3 scripts/build_site.py --source local \
          --root "/path/to/PAST AMP STOCK PITCHES & UPDATES" \
          --base-url "https://nuwildcat.sharepoint.com/sites/KSM-AMP/Shared%20Documents/.../PAST%20AMP%20STOCK%20PITCHES%20%26%20UPDATES"

  GRAPH  (later, in the cloud) — read one SharePoint site via Microsoft Graph:
      python3 scripts/build_site.py --source graph
      # env: AZURE_CLIENT_ID, AZURE_TENANT_ID, SHAREPOINT_SITE_URL, ARCHIVE_FOLDER
      # (Graph also returns each file's canonical link automatically.)

It only ever READS names, folders, and links — never file contents, and never
modifies the archive.
"""
import argparse, base64, datetime, json, os, re, sys, urllib.parse
from pathlib import Path

# ---------------------------------------------------------------- parsing ----
PITCH_EXTS = {".pptx", ".ppt", ".pdf", ".xlsx", ".xls", ".xlsm", ".xlsb", ".docx", ".doc"}
SKIP_EXTS = {".lnk", ".tmp", ".ds_store"}
COMPANY_TICKER = re.compile(r"^(.*?)\s*\(([A-Za-z.&]{1,6})\)\s*$")
DOC_KEYWORDS = [
    ("Presentation", ["presentation", "pitch", "deck", "slides"]),
    ("Model", ["model", "dcf"]),
    ("Report", ["report", "write-up", "writeup", "memo"]),
    ("Update", ["update"]),
    ("Feedback", ["feedback"]),
]


def doc_type(stem):
    s = stem.lower()
    for label, kws in DOC_KEYWORDS:
        if any(k in s for k in kws):
            return label
    return "Document"


def extract(rel_parts, stem, ext):
    company = ticker = year = period = section = None
    for p in reversed(rel_parts[:-1]):
        m = COMPANY_TICKER.match(p)
        if m:
            company = m.group(1).strip() or None
            ticker = m.group(2).upper().replace(".", "")
            break
    for p in rel_parts[:-1]:                       # section from FOLDERS, not the filename
        pl = p.lower()
        if "pitch" in pl:
            section = "Pitches"
        elif "update" in pl:
            section = "Updates"
    for p in rel_parts:
        m = re.search(r"\b(0[1-9]|1[0-2])[-.](20\d\d)\b", p)
        if m:
            period, year = f"{m.group(2)}-{m.group(1)}", m.group(2)
            break
    m = re.search(r"\b(20\d\d)[-._]?(0[1-9]|1[0-2])[-._]?(0[1-9]|[12]\d|3[01])\b", stem)
    if m:
        period, year = f"{m.group(1)}-{m.group(2)}-{m.group(3)}", m.group(1)
    if not year:
        for p in reversed(rel_parts):
            m = re.search(r"\b(20\d\d)\b", p)
            if m:
                year = m.group(1)
                break
    return {"ticker": ticker, "company": company, "year": year, "period": period,
            "section": section, "doc_type": doc_type(stem), "ext": ext.lower().lstrip(".")}


def make_record(rel_parts, filename, url):
    ext = os.path.splitext(filename)[1]
    r = extract(rel_parts, os.path.splitext(filename)[0], ext)
    r.update({"filename": filename, "rel_path": "/".join(rel_parts), "url": url})
    return r


# ------------------------------------------------------------ local source ----
def from_local(root, base_url, link_mode):
    root = Path(root)
    if not root.exists():
        sys.exit(f"--root not found: {root}")
    base = base_url.rstrip("/")
    recs = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() in SKIP_EXTS or f.name.lower().endswith("_error.txt"):
            continue
        if f.suffix.lower() not in PITCH_EXTS:
            continue
        parts = list(f.relative_to(root).parts)
        if not base:
            url = ""
        elif link_mode == "folder":
            url = base
        else:
            url = base + "/" + urllib.parse.quote("/".join(parts))
        recs.append(make_record(parts, f.name, url))
    return recs


# ------------------------------------------------------------ graph source ----
def from_graph():
    try:
        import msal, requests
    except ImportError:
        sys.exit("Graph mode needs: pip install msal requests")
    GRAPH = "https://graph.microsoft.com/v1.0"

    def token():
        cid, tid = os.environ["AZURE_CLIENT_ID"], os.environ["AZURE_TENANT_ID"]
        secret = os.environ.get("AZURE_CLIENT_SECRET")
        if secret:
            cred = secret
        else:                                       # GitHub OIDC federated credential (no secret)
            url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"] + "&audience=api://AzureADTokenExchange"
            t = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
            cred = {"client_assertion": requests.get(url, headers={"Authorization": "Bearer " + t}).json()["value"]}
        app = msal.ConfidentialClientApplication(
            cid, authority=f"https://login.microsoftonline.com/{tid}", client_credential=cred)
        res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in res:
            sys.exit("Graph auth failed: " + json.dumps(res.get("error_description", res)))
        return res["access_token"]

    s = requests.Session()
    s.headers["Authorization"] = "Bearer " + token()
    u = urllib.parse.urlparse(os.environ["SHAREPOINT_SITE_URL"].rstrip("/"))
    site = s.get(f"{GRAPH}/sites/{u.netloc}:{u.path}").json()
    if "id" not in site:
        sys.exit("Could not resolve SharePoint site: " + json.dumps(site))
    drive_id = s.get(f"{GRAPH}/sites/{site['id']}/drive?$select=id").json()["id"]
    folder = os.environ.get("ARCHIVE_FOLDER", "").strip("/")
    root = s.get(f"{GRAPH}/drives/{drive_id}/root:/{folder}" if folder
                 else f"{GRAPH}/drives/{drive_id}/root").json()
    if "id" not in root:
        sys.exit("Could not resolve archive folder: " + json.dumps(root))
    recs, stack = [], [(root["id"], [])]
    while stack:
        item_id, rel = stack.pop()
        url = f"{GRAPH}/drives/{drive_id}/items/{item_id}/children?$top=200&$select=id,name,file,folder,webUrl"
        while url:
            data = s.get(url).json()
            for c in data.get("value", []):
                nm = c["name"]
                if "folder" in c:
                    stack.append((c["id"], rel + [nm]))
                elif "file" in c and not nm.lower().endswith("_error.txt") \
                        and os.path.splitext(nm)[1].lower() in PITCH_EXTS:
                    recs.append(make_record(rel + [nm], nm, c.get("webUrl", "")))
            url = data.get("@odata.nextLink")
    return recs


# --------------------------------------------------------------- rendering ----
TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive,nosnippet"><title>__TITLE__</title>
<style>
 :root{--bg:#201a2e;--panel:#282133;--panel2:#2e2640;--line:#3f3652;--text:#e3dded;--muted:#a096b5;--accent:#ffffff;--pill:#382f4d}
 *{box-sizing:border-box} body{margin:0;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--text)}
 header{padding:20px 24px;border-bottom:1px solid var(--line);background:var(--panel)} h1{margin:0;font-size:20px}
 .sub{color:var(--muted);font-size:13px;margin-left:8px} .stats{margin-top:8px;color:var(--muted);font-size:13px} .stats b{color:var(--accent)}
 .controls{display:flex;flex-wrap:wrap;gap:10px;padding:16px 24px;background:var(--panel2);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
 input[type=search],select{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:13px;outline:none}
 input[type=search]{flex:1;min-width:220px} input:focus,select:focus{border-color:var(--accent)}
 .wrap{padding:0 24px 60px} .count{padding:12px 0;color:var(--muted);font-size:13px}
 table{width:100%;border-collapse:collapse} th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
 th{position:sticky;top:64px;background:var(--bg);color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.4px;cursor:pointer;white-space:nowrap}
 th:hover{color:var(--text)} tr:hover td{background:var(--panel)} .tk{font-weight:700;color:var(--accent)} .muted{color:var(--muted)}
 .pill{display:inline-block;padding:2px 8px;border-radius:20px;background:var(--pill);font-size:11px;color:var(--muted)}
 a.file{color:var(--accent);text-decoration:underline;text-decoration-color:rgba(255,255,255,.3);text-underline-offset:3px} a.file:hover{text-decoration:underline} .empty{padding:50px;text-align:center;color:var(--muted)}
 .foot{padding:14px 24px;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}
 #gate{position:fixed;inset:0;z-index:100;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:20px}
 #gate .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:28px 30px;width:320px;max-width:100%;text-align:center}
 #gate h2{margin:0 0 6px;font-size:18px} #gate p{margin:0 0 16px;color:var(--muted);font-size:13px}
 #gate input{width:100%;margin-bottom:10px} #gate .err{color:#ff9aa2;font-size:12px;min-height:16px;margin-top:8px}
 #gate button{width:100%;background:var(--accent);color:#201a2e;border:0;border-radius:8px;padding:9px;font-size:14px;font-weight:600;cursor:pointer}
</style></head><body>
<div id="gate" hidden><div class="card">
 <h2>__TITLE__</h2><p>Enter the password to continue</p>
 <input type="password" id="pw" placeholder="Password" autocomplete="off">
 <button id="go">Enter</button><div class="err" id="err"></div>
</div></div>
<header><h1>__TITLE__</h1><div class="stats" id="stats"></div></header>
<div class="controls">
 <input type="search" id="q" placeholder="Search ticker, company, filename…" autofocus>
 <select id="fSection"><option value="">All sections</option></select>
 <select id="fYear"><option value="">All years</option></select>
 <select id="fType"><option value="">All types</option></select>
</div>
<div class="wrap"><div class="count" id="count"></div>
<table><thead><tr id="head"></tr></thead><tbody id="rows"></tbody></table>
<div class="empty" id="empty" style="display:none">No matches.</div></div>
<div class="foot" id="foot"></div>
<script id="data">window.DATA_B64="__DATA__";window.BUILT=__BUILT__;window.PWHASH=__PWHASH__;</script>
<script>
(function(){var H=window.PWHASH||0;if(!H)return;
 function hsh(t){var x=5381;for(var i=0;i<t.length;i++)x=((x*33)^t.charCodeAt(i))>>>0;return x}
 var ok=false;try{ok=localStorage.getItem("amp_unlocked")==="1"}catch(e){}
 var g=document.getElementById("gate");if(ok){g.remove();return}
 g.hidden=false;document.body.style.overflow="hidden";
 var pw=document.getElementById("pw"),er=document.getElementById("err");
 function go(){if(hsh(pw.value)===H){try{localStorage.setItem("amp_unlocked","1")}catch(e){}
   g.remove();document.body.style.overflow=""}else{er.textContent="Incorrect password";pw.select()}}
 document.getElementById("go").onclick=go;
 pw.addEventListener("keydown",function(e){if(e.key==="Enter")go()});
 setTimeout(function(){pw.focus()},30);})();
const D=(function(){try{var b=atob(window.DATA_B64||"");var u=Uint8Array.from(b,function(c){return c.charCodeAt(0)});return JSON.parse(new TextDecoder().decode(u))}catch(e){return[]}})();
const COLS=[["ticker","Ticker"],["company","Company"],["period","Period"],["section","Section"],["doc_type","Type"],["file","File",1]];
let sk="period",sd=-1;
const uniq=k=>[...new Set(D.map(r=>r[k]).filter(Boolean))];
function fill(id,arr,s){const e=document.getElementById(id);(s?arr.sort():arr).forEach(v=>{const o=document.createElement("option");o.value=o.textContent=v;e.appendChild(o)})}
fill("fSection",uniq("section"),true);fill("fYear",uniq("year").sort().reverse(),false);fill("fType",uniq("doc_type"),true);
document.getElementById("stats").innerHTML=`<b>${D.length}</b> files · <b>${new Set(D.map(r=>r.ticker).filter(Boolean)).size}</b> companies`;
document.getElementById("foot").textContent="Last updated: "+(window.BUILT||"");
const q_=document.getElementById("q"),fS=document.getElementById("fSection"),fY=document.getElementById("fYear"),fT=document.getElementById("fType");
function esc(s){return s?(""+s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])):s}
function head(){document.getElementById("head").innerHTML=COLS.map(c=>`<th data-k="${c[0]}">${c[1]}${!c[2]&&c[0]===sk?(sd<0?" ▼":" ▲"):""}</th>`).join("");
 document.querySelectorAll("#head th").forEach(t=>{const k=t.dataset.k;if(COLS.find(c=>c[0]===k)[2])return;t.onclick=()=>{sk===k?sd*=-1:(sk=k,sd=1);render()}})}
function filtered(){const q=q_.value.toLowerCase(),fs=fS.value,fy=fY.value,ft=fT.value;
 return D.filter(r=>{if(fs&&r.section!==fs)return 0;if(fy&&r.year!==fy)return 0;if(ft&&r.doc_type!==ft)return 0;
  if(q){if(![r.ticker,r.company,r.filename].join(" ").toLowerCase().includes(q))return 0}return 1})}
function render(){head();const rows=filtered().sort((a,b)=>{let x=(a[sk]||"")+"",y=(b[sk]||"")+"";return x<y?-sd:x>y?sd:0});
 document.getElementById("count").textContent=`${rows.length} result${rows.length===1?"":"s"}`;
 document.getElementById("empty").style.display=rows.length?"none":"block";
 document.getElementById("rows").innerHTML=rows.slice(0,4000).map(r=>`<tr>
  <td class="tk">${r.ticker||'<span class=muted>?</span>'}</td><td>${esc(r.company)||'<span class=muted>—</span>'}</td>
  <td class="muted">${r.period||"—"}</td><td><span class="pill">${r.section||"—"}</span></td><td>${r.doc_type||"—"}</td>
  <td>${r.url?`<a class="file" href="${r.url}" target="_blank" title="${esc(r.filename)}">${esc(r.filename)} ↗</a>`:esc(r.filename)}</td></tr>`).join("")}
[q_,fS,fY,fT].forEach(e=>e.addEventListener("input",render));render();
</script></body></html>"""


def js_hash(t):
    h = 5381
    for ch in t:
        h = ((h * 33) ^ ord(ch)) & 0xFFFFFFFF
    return h


def render(recs, title, out="docs", password=""):
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / ".nojekyll").touch()
    (Path(out) / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    page = (TEMPLATE
            .replace("__TITLE__", title)
            .replace("__DATA__", base64.b64encode(json.dumps(recs, separators=(",", ":")).encode("utf-8")).decode("ascii"))
            .replace("__BUILT__", json.dumps(datetime.date.today().isoformat()))
            .replace("__PWHASH__", str(js_hash(password)) if password else "0"))
    (Path(out) / "index.html").write_text(page)
    tick = len({r["ticker"] for r in recs if r["ticker"]})
    print(f"Wrote {out}/index.html — {len(recs)} files, {tick} companies.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["local", "graph"], required=True)
    ap.add_argument("--root", help="local mode: the archive folder on this computer")
    ap.add_argument("--base-url", default="", help="local mode: web address of that folder (for links)")
    ap.add_argument("--link-mode", choices=["path", "folder"], default="path")
    ap.add_argument("--title", default="AMP Archive")
    ap.add_argument("--out", default="docs")
    ap.add_argument("--password", default="", help="optional password gate (client-side speed bump only)")
    args = ap.parse_args()
    if args.source == "local":
        if not args.root:
            sys.exit("--root is required for --source local")
        recs = from_local(args.root, args.base_url, args.link_mode)
    else:
        recs = from_graph()
    render(recs, args.title, args.out, args.password)


if __name__ == "__main__":
    main()
