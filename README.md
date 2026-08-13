# ats-fetch

[![tests](https://github.com/jloor/ats-fetch/actions/workflows/ci.yml/badge.svg)](https://github.com/jloor/ats-fetch/actions/workflows/ci.yml)

Archive a job posting verbatim, from its URL, using the applicant tracking system's own API.

```
pip install ats-fetch
ats-fetch https://jobs.ashbyhq.com/ramp/34413f8d-26bf-4bbc-8ade-eb309a0e2245
```

Or run the single file with no install at all:

```
git clone https://github.com/jloor/ats-fetch
cd ats-fetch
python3 ats_fetch.py <posting-url>
```

Python 3.9 or newer. No dependencies, standard library only.

## Why

A job posting is the record of what you applied to, and postings do not stay put. They get
pulled, rewritten, and quietly re-priced. The fields that move are the ones that decide
whether you want the job: the compensation range, the remote status, and the work hours.

Aggregators are not the record either. They publish estimated salaries the employer never
stated, and they drop the posting when the employer does.

This saves the real text, from the source, before it changes.

**It is not a job scraper.** Scrapers exist to discover jobs: you point one at a company, or
at many companies, and it returns everything currently open. This does a different job. You
give it one posting you already care about, and it keeps that posting exactly as published.

The difference is not cosmetic, because the two have different standards of correctness. A
scraper that misses two percent of listings is working fine. An archive that alters one word
is not an archive.

## When this matters

**The range moves between the posting and the offer.** You applied against a published band.
Weeks later the number on the table is lower, and the live posting no longer says what it said
when you read it. The archived copy is what was published on the day you applied.

**The requisition is pulled while you are still in process.** Your interview is Monday and the
posting is gone. You cannot prepare against a page that returns a 404, and asking the recruiter
to resend the description is not a strong opening move.

**Remote turns out to mean something else.** "Remote - US" on the day you applied, "hybrid,
three days on site" by the time it comes up on a call. One of you is misremembering and only
one of you can prove it.

**You cannot remember which one wanted what.** Eleven applications in six weeks, and the
company asking you about Terraform is not the company you think it is.

**You are working out what a level actually pays.** Published employer ranges, gathered across
many companies, instead of an aggregator's estimate. Several jurisdictions now require a range
in the posting, which makes the posting the primary source and worth keeping.

**You want to see what an employer changed.** Two captures of the same requisition, weeks
apart, show you exactly which words moved. Nothing here does that comparison for you yet, and
it is the most obvious thing to build next.

I wrote this after three postings I was working on disappeared before I finished applying to
them.

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
careers page, the posting link looks like `company.com/careers/detail/?gh_jid=5678901234`. The
board token you need for the API is nowhere in it. `ats_fetch.py` recovers it: it takes the
hostname labels, strips `careers`, `jobs`, and `apply`, then strips company suffixes like
`hq`, `inc`, `labs`, `technologies`, and probes the API with each candidate until one
returns a real job. That is how it works on boards that do not look like Greenhouse at all.

## Usage

```
ats-fetch <url>                  print the archive block to stdout
ats-fetch <url> --new <dir>      write a fresh job-description.md
ats-fetch <url> --append <dir>   append the block to an existing one
ats-fetch <url> --json           dump the raw API payload
```

Substitute `python3 ats_fetch.py` for `ats-fetch` if you cloned rather than installed. The
arguments are identical.

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

## Which platforms are possible, and which are not

[`docs/ats-survey.md`](docs/ats-survey.md) records what was probed on each platform: the
endpoints, the quirks, and the four that cannot be supported with the reason for each. Read it
before proposing a new adapter. Three of those four fail for reasons no adapter can fix.

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
