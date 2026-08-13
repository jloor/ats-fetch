# ats-fetch

Archive a job posting verbatim, from its URL, using the applicant tracking system's own API.

```
git clone https://github.com/jloor/ats-fetch
cd ats-fetch
python3 ats_fetch.py https://jobs.ashbyhq.com/ramp/34413f8d-26bf-4bbc-8ade-eb309a0e2245
```

Python 3.9 or newer. No dependencies, standard library only.

## Why

A job posting is the record of what you applied to, and postings do not stay put. They get
pulled, rewritten, and quietly re-priced. The fields that move are the ones that decide
whether you want the job: the compensation range, the remote status, and the work hours.

Aggregators are not the record either. They publish estimated salaries the employer never
stated, and they drop the posting when the employer does.

This saves the real text, from the source, before it changes.

## The part worth stealing

If you only take one thing from this repository, take these. Each returns the full posting
as JSON, publicly, with no key.

| Platform | Endpoint |
|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}?content=true` |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true` |
| Lever | `https://api.lever.co/v0/postings/{token}/{id}?mode=json` |
| Workday | `https://{tenant}.{sub}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/job/{path}` |

Two of them have a catch.

**Ashby** returns the whole board, not one job. You filter for your posting by matching the
UUID against each entry's `jobUrl`. `includeCompensation=true` is what gets you the pay
range, and it is off by default.

**Greenhouse embedded boards have no token in the URL.** When a company hosts its own
careers page, the posting link looks like `company.com/careers/detail/?gh_jid=7961297`. The
board token you need for the API is nowhere in it. `ats_fetch.py` recovers it: it takes the
hostname labels, strips `careers`, `jobs`, and `apply`, then strips company suffixes like
`hq`, `inc`, `labs`, `technologies`, and probes the API with each candidate until one
returns a real job. That is how it works on boards that do not look like Greenhouse at all.

## Usage

```
python3 ats_fetch.py <url>                  print the archive block to stdout
python3 ats_fetch.py <url> --new <dir>      write a fresh job-description.md
python3 ats_fetch.py <url> --append <dir>   append the block to an existing one
python3 ats_fetch.py <url> --json           dump the raw API payload
```

The output is a metadata table followed by the full posting text. This is real output, not a
tidied-up version of it:

```
| Field | Value |
|---|---|
| **ATS** | Ashby |
| **Title** |  Security Engineer, Cloud |
| **Canonical URL** | https://jobs.ashbyhq.com/ramp/34413f8d-26bf-4bbc-8ade-eb309a0e2245 |
| **Apply URL** | https://jobs.ashbyhq.com/ramp/34413f8d-26bf-4bbc-8ade-eb309a0e2245/application |
| **Location as stated** | New York, NY (HQ) |
| **Comp as stated** | $211.4K – $290.6K • Offers Equity |
| **isRemote flag** | True |
| **Posted / updated** | 2026-04-07 |
| **Captured** | 2026-08-13 |
```

Note the leading space in the title and the bullet characters in the comp field. Those come
from the employer and they are left alone, which is the whole point.

Supported: **Greenhouse** (including `gh_jid` embedded boards and the `.eu` domains),
**Ashby**, **Lever**, **Workday**. Anything else falls back to fetching the page and
stripping tags, which is lossier but usually still usable.

## Three decisions worth knowing about

**It saves the text unedited.** No summary, no cleanup, and it does not fix the employer's
typos. An archive is only worth having if it is what was actually published.

**It refuses to archive a board page.** A directory of open roles returns plenty of text, so
length cannot tell it apart from a posting. `ats-fetch` checks the URL shape and exits with
an explanation rather than writing a file that looks like an archive and contains no job.

**It unescapes before it strips tags.** Several of these APIs return the description
entity-escaped, and at least one returns it escaped twice. Strip the tags first and the
markup survives as literal words: `span`, `div class`, `data-ccp-parastyle`. Those then
poison anything you do downstream with the text.

## What it does not do

- **Gated boards.** If a posting needs a login, a session, or an invitation, this cannot
  reach it. There is no authentication anywhere in the tool and none is planned.
- **Crawling or batch.** One posting per invocation, by design. See the note below.
- **Retries.** A failed fetch returns nothing and says so. Run it again.
- **Change detection.** It captures a posting at a moment. Comparing two captures to find
  what an employer edited is a genuinely useful thing to build, and it is not built here.

## Tests

```
python3 tests/test_ats_fetch.py
```

No network. They cover ATS detection including the embedded-board case, the board-page
refusal, and the unescape order.

## Contributions

New ATS adapters are very welcome. If a platform publishes a JSON posting API, add a fetcher
following the existing pattern and a row in the detection test. I review when I can, which
may take a couple of weeks.

I am unlikely to merge refactors, restyling, or anything that adds a dependency. Being
standard-library-only is a feature, not an oversight.

## A note on politeness

This calls public, unauthenticated endpoints that these platforms publish to serve their own
job boards, and it identifies itself honestly as `ats-fetch/1.0`. It fetches one posting per
invocation. Please keep it that way. If you want a corpus, ask the platform.

## On AI use

AI was used to write, organize, and maintain this project, including most of this README.

Scope, review, and the decision to ship are human gated by me. I read what goes out.

## Licence

MIT. See [LICENSE](LICENSE).
