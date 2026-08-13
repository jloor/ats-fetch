# ATS survey

Which applicant tracking systems can be archived from a posting URL, which cannot, and why.

Everything here was probed against live endpoints on 2026-08-13. Where a platform is listed
as unusable, the reason is a specific thing that was tested, not an assumption.

`ats-fetch` needs two things from a platform. It has to identify the platform **from the URL
a person pastes**, and it has to reach **the full posting text**. A platform can have an
excellent public API and still be unusable here if its posting URLs do not identify it, or if
its API lists jobs without describing them.

## Supported

| Platform | Posting URL | Endpoint |
|---|---|---|
| Greenhouse | `job-boards.greenhouse.io/{token}/jobs/{id}`, `.eu` variants, and `gh_jid` embeds | `boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}?content=true` |
| Ashby | `jobs.ashbyhq.com/{token}/{uuid}` | `api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true` |
| Lever | `jobs.lever.co/{token}/{uuid}` | `api.lever.co/v0/postings/{token}/{id}?mode=json` |
| Workday | `{tenant}.{sub}.myworkdayjobs.com/{site}/job/{path}` | `/wday/cxs/{tenant}/{site}/job/{path}` |
| SmartRecruiters | `jobs.smartrecruiters.com/{company}/{id}` | `api.smartrecruiters.com/v1/companies/{company}/postings/{id}` |
| Workable | `apply.workable.com/{company}/j/{shortcode}` | `apply.workable.com/api/v1/widget/accounts/{company}?details=true` |

### Quirks worth knowing

**Ashby returns the entire board**, not the job you asked for. Filter by matching the UUID
against each entry's `jobUrl`. `includeCompensation=true` is off by default, so the pay range,
the single field most worth archiving, is the one you have to know to request.

**Greenhouse embedded boards carry no token.** When a company hosts its own careers page the
link is `company.com/careers/detail/?gh_jid=<id>` and the board token is nowhere in the URL.
`ats_fetch.py` recovers it from the hostname: strip `careers`, `jobs`, `apply`, then strip
suffixes like `hq`, `inc`, `labs`, `technologies`, and probe the API with each candidate until
one returns a real job.

**SmartRecruiters splits a posting into four named sections** (`companyDescription`,
`jobDescription`, `qualifications`, `additionalInformation`) rather than returning one blob.
The headings are preserved on purpose. Flattening them loses which requirements the employer
listed as qualifications and which as additional information.

**Workable omits every description** unless the request carries `details=true`. Without it you
get a listing. Its bare share link, `apply.workable.com/j/{shortcode}`, is **not supported**:
it carries no company, there is no shortcode-only endpoint, and the page is client rendered,
so nothing in that URL says which board to query.

**Workday is undocumented.** It is the internal API behind the careers front end, not a
published contract, and it can change without notice. It also has quirks: a `limit` above 20
returns zero results with no error.

## Not supported, and why

### Breezy HR: the description is not published

`{company}.breezy.hr/json` returns a **listing** feed. Names, locations, salaries, departments,
no bodies.

- `{company}.breezy.hr/json/{id}` and `/json/{friendly_id}` return **HTML**, not JSON.
- `/json?id={id}` ignores the parameter and returns the whole list again.
- The posting page is a client-rendered shell with no JSON-LD and no embedded state.
- The only description available anywhere is a truncated `og:description` meta tag.

Calling this a "public JSON feed" is accurate and misleading. It lists jobs. It does not
describe them. Nothing here can be fixed by a better adapter.

⚠️ Tested against Breezy's own demo tenant, the only live one found. The page architecture is
a platform-level template rather than a tenant setting, so a real customer is expected to
behave the same way, but that is an inference and has not been confirmed on a real tenant.

### Manatal: nothing maps a URL to a record

The API works: `api.careers-page.com/open/v1/career-pages/{slug}/job-posts` returns every
posting with the description under `translations[].description`, keyed by `language_code`.

The problem is the join. Posting URLs are `careers-page.com/{slug}/job/3W5R45VV`, and the API
returns UUIDs like `44040b2f-2482-48b0-8abb-eea4b31472c2`. **No item exposes a short code
field.** There is no per-job detail endpoint either; `/job-posts/{uuid}` returns 404.

One URL code was found inside a description, but only because one posting hyperlinked another.
That is a coincidence, not a mapping.

Given a Manatal posting URL, there is no public way to find the job it refers to.

### Recruitee: postings live on customer domains

`{company}.recruitee.com/api/offers` works and returns inline descriptions.

The canonical posting URL does not. It is the customer's own domain:

```
https://jobs.channable.com/o/account-executive-north-america-1
```

Nothing in that URL identifies Recruitee. A tool that detects the platform from the URL cannot
detect this one. Supporting it needs a design decision rather than an adapter, and the options
are tracked in the issues.

### HireHive: works, but unverified

`{company}.hirehive.com/api/v1/jobs` returns a list with descriptions inline, which is the
easiest shape on this page.

It is not shipped because it has never been exercised on real content. The only live tenant
found is HireHive's own, which has one job whose description is **2 characters**. An adapter
whose body extraction has never run against a real posting is not worth trusting.

One real tenant URL with a described job unblocks this.

## Method

Each platform was probed for a live tenant, then the payload was parsed rather than measured.
That distinction mattered: an early probe recorded one endpoint as returning 9,959 bytes of
JSON, and it was HTML. A response that is the right size is not a response of the right kind.

Live postings were used to verify the adapters by hand. **None of them appear in the test
suite.** Test fixtures are synthetic, because a fixture built from real postings encodes which
jobs the author was looking at.
