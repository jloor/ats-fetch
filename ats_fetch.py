#!/usr/bin/env python3
"""
ats_fetch.py — pull a job posting verbatim from its URL.

Detects the ATS behind a posting URL, calls that platform's public JSON API, and emits a
`job-description.md` block: a metadata table plus the FULL posting text, unedited.

    python3 ats_fetch.py <url>                          # print to stdout
    python3 ats_fetch.py <url> --append <dir>      # append verbatim block to job-description.md
    python3 ats_fetch.py <url> --new <dir>            # write a fresh job-description.md
    python3 ats_fetch.py <url> --json                      # dump the raw API payload

Supported: Greenhouse (incl. gh_jid embeds), Ashby, Lever, Workday. Anything else falls back
to fetching the page and stripping tags, which is lossier but usually still usable.

Why this exists: a posting is the record of what you applied to, and postings get pulled,
rewritten, and quietly re-priced. Comp ranges, remote status and work hours are the fields
that move. Archiving the text by hand is where it silently gets skipped.

Requires nothing but a Python interpreter. No third-party packages.
"""
import re, sys, json, html, argparse, datetime, urllib.request
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Honest identification. These are public JSON APIs and there is no reason to claim to be
# a browser.
UA = "ats-fetch/1.0 (+https://github.com/jloor/ats-fetch)"

# One source of truth for URL shapes, so detect() and the fetchers cannot disagree.
RE_GREENHOUSE = re.compile(r"(?:job-boards|boards)(?:\.eu)?\.greenhouse\.io/([^/]+)/jobs/(\d+)")
RE_ASHBY = re.compile(r"jobs\.ashbyhq\.com/([^/]+)/([0-9a-f-]{16,})")
RE_LEVER = re.compile(r"jobs\.lever\.co/([^/]+)/([0-9a-f-]{16,})")
RE_WORKDAY = re.compile(r"https://([^.]+)\.([^.]+)\.myworkdayjobs\.com/([^/]+)/job/(.+)$")


def detect(url):
    """Which ATS is behind this URL, from the URL alone. No network, so it is testable.

    A bare gh_jid query parameter counts as Greenhouse: that is the embedded-board case,
    where the company hosts the careers page and only the job id survives in the URL.
    """
    if RE_GREENHOUSE.search(url) or parse_qs(urlparse(url).query).get("gh_jid"):
        return "Greenhouse"
    if RE_ASHBY.search(url):
        return "Ashby"
    if RE_LEVER.search(url):
        return "Lever"
    if RE_WORKDAY.search(url):
        return "Workday"
    return None


def get(url, post=None):
    """Fetch a URL and return the body as text. Returns "" on any failure.

    urllib rather than a curl subprocess, so the only dependency is Python itself.
    Failure returns "" because every caller already reads an unparseable body as "this
    platform did not match", and raising here would abort a run over one dead endpoint.
    """
    data = post.encode("utf-8") if post is not None else None
    headers = {"User-Agent": UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, data=data, headers=headers), timeout=40) as r:
            return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")
    except Exception:
        return ""


def detag(h):
    """HTML -> text.

    Order matters. Several ATS APIs return the description ENTITY-ESCAPED (&lt;div&gt;),
    sometimes doubly. Stripping tags before unescaping leaves the markup behind as literal
    words, which poison term extraction (span, div class, data-ccp-parastyle). So unescape
    to a fixed point FIRST, then strip. Found 2026-08-11, in downstream term-extraction
    output that was full of literal markup words.
    """
    h = h or ""
    for _ in range(3):
        u = html.unescape(h)
        if u == h:
            break
        h = u
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<(br|/p|/div|/li|/h[1-6]|/tr|/table)\s*/?>", "\n", h)
    h = re.sub(r"(?i)<li[^>]*>", "\n- ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h).replace("\xa0", " ").replace("\u2019", "'")
    h = re.sub(r"[ \t]+", " ", h)
    h = re.sub(r"\n\s*\n\s*\n+", "\n\n", h)
    h = "\n".join(l.rstrip() for l in h.split("\n")).strip()
    return re.sub(r"^(-\s*\n)+", "", h, flags=re.M)


# ---------------------------------------------------------------- platforms
def greenhouse(url):
    q = parse_qs(urlparse(url).query)
    jid = (q.get("gh_jid") or [None])[0]
    m = RE_GREENHOUSE.search(url)
    token, job = (m.group(1), m.group(2)) if m else (None, jid)
    if not token and job:               # embedded board: no token in the URL
        labels = [l for l in urlparse(url).netloc.split(".") if l not in ("www", "com", "io", "co")]
        cands = []
        for l in labels:
            base = re.sub(r"(careers?|jobs?|apply)", "", l).strip("-") or l
            cands += [base, re.sub(r"(hq|inc|labs|technologies|software)$", "", base)]
        seen, uniq = set(), []
        for cnd in cands:
            if cnd and len(cnd) > 1 and cnd not in seen:
                seen.add(cnd); uniq.append(cnd)
        for g in uniq:
            d = get(f"https://boards-api.greenhouse.io/v1/boards/{g}/jobs/{job}?content=true")
            if d.strip().startswith("{") and '"title"' in d:
                token = g
                break
    if not token or not job:
        return None
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job}?content=true")
    try:
        j = json.loads(d)
    except Exception:
        return None
    if "title" not in j:
        return None
    return {"ats": "Greenhouse", "title": j["title"], "raw": j,
            "location": (j.get("location") or {}).get("name", ""),
            "updated": (j.get("updated_at") or "")[:10],
            "url": j.get("absolute_url", url), "body": detag(j.get("content", ""))}


def ashby(url):
    m = RE_ASHBY.search(url)
    if not m:
        return None
    token, jid = m.groups()
    try:
        board = json.loads(get(
            f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"))
    except Exception:
        return None
    j = next((x for x in board.get("jobs", []) if jid in x.get("jobUrl", "")), None)
    if not j:
        return None
    comp = (j.get("compensation") or {}).get("compensationTierSummary", "")
    return {"ats": "Ashby", "title": j["title"], "raw": j,
            "location": j.get("location", ""), "comp": comp,
            "updated": (j.get("publishedAt") or "")[:10],
            "remote": j.get("isRemote"), "url": j.get("jobUrl", url),
            "apply": j.get("applyUrl", ""), "body": detag(j.get("descriptionHtml", ""))}


def lever(url):
    m = RE_LEVER.search(url)
    if not m:
        return None
    token, jid = m.groups()
    try:
        j = json.loads(get(f"https://api.lever.co/v0/postings/{token}/{jid}?mode=json"))
    except Exception:
        return None
    if "text" not in j:
        return None
    body = detag(j.get("description", ""))
    for lst in j.get("lists", []):
        body += "\n\n" + (lst.get("text") or "") + "\n" + detag(lst.get("content", ""))
    if j.get("additional"):
        body += "\n\n" + detag(j["additional"])
    cat = j.get("categories") or {}
    return {"ats": "Lever", "title": j["text"], "raw": j,
            "location": cat.get("location", ""), "team": cat.get("team", ""),
            "url": j.get("hostedUrl", url), "apply": j.get("applyUrl", ""), "body": body}


def workday(url):
    m = RE_WORKDAY.search(url)
    if not m:
        return None
    tenant, sub, site, path = m.groups()
    api = f"https://{tenant}.{sub}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/job/{path}"
    try:
        j = json.loads(get(api))["jobPostingInfo"]
    except Exception:
        return None
    return {"ats": "Workday", "title": j.get("title", ""), "raw": j,
            "location": j.get("location", ""), "updated": (j.get("startDate") or "")[:10],
            "req": j.get("jobReqId", ""), "url": j.get("externalUrl", url),
            "body": detag(j.get("jobDescription", ""))}


def looks_like_single_posting(url):
    """Does this URL point at one requisition, rather than a board of many? No network.

    A board page still returns plenty of text, so length alone cannot tell them apart.
    The signal is in the path: a long numeric id, a UUID prefix, or a /job/<x>/<y> shape.
    """
    path = urlparse(url).path.rstrip("/")
    return bool(re.search(r"/\d{4,}|[0-9a-f]{8}-[0-9a-f]{4}|/job[s]?/[^/]+/[^/]+", path)
                or parse_qs(urlparse(url).query))


def generic(url):
    """Fallback scrape. Refuses board and listing pages: a directory of open roles is not a
    posting, and archiving one produces a file that looks right and is worthless."""
    if not looks_like_single_posting(url):
        sys.exit(
            f"\n  ERROR: {url}\n  looks like a job BOARD or listing page, not a single posting.\n"
            "  Archiving a directory of open roles would give you a file that looks like an\n"
            "  archive and contains no posting.\n\n"
            "  Pass the URL of the specific requisition. If the req is already gone, record\n"
            "  that as a loss rather than archiving the board in its place.\n")
    body = detag(get(url))
    if len(body) < 400:
        return None
    return {"ats": "generic HTML scrape", "title": "", "location": "", "url": url,
            "body": body, "raw": {}}


def fetch(url):
    for fn in (greenhouse, ashby, lever, workday):
        r = fn(url)
        if r and r.get("body", "").strip():
            return r
    return generic(url)


# ---------------------------------------------------------------- output
def block(d, url):
    today = datetime.date.today().isoformat()
    rows = [("ATS", d["ats"]), ("Title", d.get("title", "")),
            ("Canonical URL", d.get("url", url)), ("Apply URL", d.get("apply", "")),
            ("Location as stated", d.get("location", "")), ("Team", d.get("team", "")),
            ("Req ID", d.get("req", "")), ("Comp as stated", d.get("comp", "")),
            ("isRemote flag", "" if d.get("remote") is None else str(d.get("remote"))),
            ("Posted / updated", d.get("updated", "")), ("Captured", today)]
    tbl = "\n".join(f"| **{k}** | {v} |" for k, v in rows if str(v).strip())
    return (f"\n---\n\n## Full posting text (verbatim, captured {today})\n\n"
            f"| Field | Value |\n|---|---|\n{tbl}\n\n"
            f"_Fetched with `ats-fetch`. Do not edit below this line: it is the record "
            f"of what was actually posted._\n\n{d['body']}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--append", type=Path, help="directory: append the verbatim block to job-description.md")
    ap.add_argument("--new", type=Path, help="directory: write a fresh job-description.md")
    ap.add_argument("--json", action="store_true", help="dump the raw API payload")
    a = ap.parse_args()

    d = fetch(a.url)
    if not d:
        sys.exit("could not fetch a posting body from that URL")
    if a.json:
        print(json.dumps(d.get("raw", {}), indent=1)[:20000])
        return

    out = block(d, a.url)
    tgt = a.append or a.new
    if not tgt:
        print(out)
        return

    tgt.mkdir(parents=True, exist_ok=True)
    f = tgt / "job-description.md"
    if a.new or not f.exists():
        head = f"# {d.get('title') or 'Job'}\n"
        f.write_text(head + out, encoding="utf-8")
        print(f"wrote {f}  ({len(d['body'])} chars of posting text)")
    else:
        cur = f.read_text(encoding="utf-8")
        if "Full posting text" in cur:
            sys.exit(f"{f} already has a verbatim block. Delete it first, or use --new.")
        f.write_text(cur.rstrip() + "\n" + out, encoding="utf-8")
        print(f"appended to {f}  ({len(d['body'])} chars of posting text)")


if __name__ == "__main__":
    main()
