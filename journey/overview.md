Three job postings I was working on disappeared before I finished applying to them. One was
pulled six days after I submitted. Another died quietly, with no announcement at all. The
third came off the board before I ever hit send.

What I lost each time was not the job. It was the text: what they had actually asked for,
what the range actually said, what the hours actually were. You cannot prepare for an
interview against a page that returns a 404, and when a number moves later you have nothing
to compare it against.

So I built the thing that stops it, and then pulled that piece out so anyone else can use it.

## The larger thing this came from

I have been running my job search as an engineering problem rather than a spreadsheet.
Applications, the postings themselves, the answers I have already written for application
forms, what I can honestly claim and at what level, and a record of every conversation. That
system is private and stays private, because it holds salary floors, comp research, and
recruiter names.

Most of it is specific to me and would be useless to anyone else. One component is not.

Archiving the posting turned out to be the load-bearing part of the whole system. Everything
downstream depends on having the real text: tailoring a résumé against what the employer
actually wrote, preparing for an interview weeks later, checking whether a number moved
between the posting and the offer. It was also the step most likely to get skipped, because
doing it by hand means copying a wall of text into a file at the exact moment you would
rather be writing the application, usually at the end of a long day.

That is a bad place to leave a manual process.

## What it does

[ats-fetch](https://github.com/jloor/ats-fetch) takes a posting URL, works out which
applicant tracking system is behind it, calls that platform's own JSON API, and writes the
full posting text unedited.

Greenhouse, Ashby, Lever, Workday. 282 lines, standard library only, no dependencies.

```
pip install ats-fetch
ats-fetch https://jobs.ashbyhq.com/ramp/34413f8d-26bf-4bbc-8ade-eb309a0e2245
```

It captures the fields employers most often edit after posting: the compensation range as
stated, the location and remote status as stated, the posted date, and the date you captured
it.

**It is not a job scraper.** Scrapers exist to discover jobs: point one at a company and it
returns everything open. This does a different job. You give it one posting you already care
about and it keeps that posting exactly as published. The two have different standards of
correctness. A scraper that misses two
percent of listings is working fine. An archive that alters one word is not an archive.

## The part worth stealing

Four endpoints, all public, all unauthenticated, none documented anywhere convenient:

| Platform | Endpoint |
|---|---|
| Greenhouse | `boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}?content=true` |
| Ashby | `api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true` |
| Lever | `api.lever.co/v0/postings/{token}/{id}?mode=json` |
| Workday | `{tenant}.{sub}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/job/{path}` |

Going through the API rather than scraping the page is what makes the result trustworthy. A
scrape gives you the posting plus the navigation, the cookie banner, and whatever the design
team shipped that week. The API gives you the fields the employer filled in.

Two of them have a catch.

**Ashby returns the entire board**, not the job you asked for, so you filter by matching the
UUID against each entry's `jobUrl`. `includeCompensation=true` is what gets you the pay range,
and it is off by default, which means the single most important field is the one you have to
know to ask for.

**Greenhouse embedded boards carry no token.** When a company hosts its own careers page the
link looks like `company.com/careers/detail/?gh_jid=<id>`, and the board token the API needs is
nowhere in the URL. So the tool derives it: take the hostname labels, strip `careers`, `jobs`
and `apply`, then strip company suffixes like `hq`, `inc`, `labs` and `technologies`, and probe
the API with each candidate until one returns a real job. That is what makes it work on boards
that do not look like Greenhouse at all, which is most of the interesting ones.

## Three decisions that are the point of the tool

**It saves the text unedited.** No summary, no cleanup, and it does not fix the employer's
typos. I wanted a summary at first, and that is the wrong instinct. The archive is only worth
having if it is admissible, and the moment it becomes a paraphrase it stops settling any
argument about what was published.

**It refuses to archive a board page.** A directory of open roles returns plenty of text, so
length cannot tell it apart from a real posting. Archive one by accident and you get a file
that looks exactly like an archive and contains no job, which you find out six weeks later
when you need it. It checks the URL shape and exits with an explanation instead.

**It unescapes before it strips tags.** Several of these APIs return the description
entity-escaped, and at least one returns it escaped twice. Strip the tags first and the markup
survives as literal words: `span`, `div class`, `data-ccp-parastyle`. Nothing crashes. The text
just quietly fills with markup vocabulary, which then poisons anything you do with it
afterwards. This one cost me an afternoon, and it is why the ordering carries a comment.

## Taking one piece out of a private repository

The tool grew up next to the private half of the system, so extracting it was its own small
project.

The decision that mattered was to stop treating it as an export. My first plan was to copy the
shareable parts out and delete the rest on the way, which is fine once and untenable forever,
because I want to keep publishing as the code changes. A deletion step that has to be correct
every single time is not a boundary, it is a habit. So the public repository is the upstream
now, and the private one will consume it as a dependency.

Measuring first is what made that cheap. The whole engine reached into private content in
exactly four places. The problem was never the size of the coupling; it was that I had been
about to solve it with care rather than with structure.

The rest was ordinary discipline, and the decision log has it in full: a fresh repository with
no shared history, because the private history holds things a fork would carry with it.
Synthetic test fixtures, after the real ones turned out to encode more about my own pipeline
than I had noticed. An HTTP client swap proved by capturing five live postings before and
after and diffing them byte for byte rather than assuming.

The useful lesson from that hour, and the decision log names the specific mistakes: every
check I wrote found what I had thought to look for and nothing else. That is worth knowing
before anyone extracts anything from a repository that holds private data.

## Deliberately not claimed

- **Nobody else uses this yet.** It is on PyPI and it has no users. Everything here is about
  how it was built, not about adoption.
- **The endpoints are not a discovery.** At least one public article documents the same ATS
  APIs. What is here is working code, plus the two catches that cost me time.
- **Four platforms are handled properly. Everything else is a fallback.** Unrecognised sites
  get their page fetched and tags stripped, which is lossier and barely tested. Treat that
  output as a draft.
- **The tests do not touch the network.** 29 assertions covering ATS detection, the board-page
  refusal, and the unescape order. They cannot tell you an endpoint still works, only that a
  URL is routed to the right adapter. If a platform changes its API, the suite stays green.
- **No change detection.** Comparing two captures of the same requisition to see which words an
  employer edited is the obvious next feature and the one I actually want. It is not built.
- **One person, one machine, a few weeks of real use.**

## Read the actual work

The decision log records what was ambiguous, what got chosen, and what was traded away,
including the mistakes made while getting this out of a private repository.
