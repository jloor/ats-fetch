I scanned all 32 commits of a private repository for secrets before publishing any part of
it. Clean. No keys, no tokens, nothing.

Twenty-eight minutes after the public repo went live, I found the requisition ID of a job I
had applied to and not heard back from sitting in a test fixture, on the internet, under my
own name.

## What this is

[ats-fetch](https://github.com/jloor/ats-fetch) takes the URL of a job posting, works out
which applicant tracking system is behind it, calls that platform's own JSON API, and writes
the full posting text unedited.

Greenhouse, Ashby, Lever, Workday. 282 lines, standard library only, no dependencies.

It exists because postings do not stay put. They get pulled, rewritten, and quietly
re-priced, and the fields that move are the compensation range, the remote status, and the
work hours. I wrote it after three postings I was working on disappeared before I finished
applying to them.

The tool is the small part. It had been running privately for a week and it worked. What
this writeup is actually about is the hour it took to get 282 lines out of a private
repository and onto the internet without publishing something I did not mean to.

I got that wrong twice.

## The audit that found the right thing

The private repository holds a job search: applications, salary floors, notes on what I would
accept, recruiter names. The tool lives next to all of it. So before anything moved I ran the
obvious check across every commit for anything shaped like a credential.

Nothing. Every match was a 1Password reference, a placeholder, or a literal `dev`.

Then I opened the test fixtures by hand and found my own email address in one, underneath a
valid DKIM signature over a real message somebody had sent me.

I had put it there deliberately. A webhook parser had broken on three wrong assumptions at
once, and saving one real payload was the only reliable way to test against the real shape.
That was the right call. It is also exactly how a personal address ended up in a tracked file
I was about to publish.

The lesson I wrote down at the time was this. A secret scanner answers one question: did a
credential get committed. Publication needs a second one: is this file safe for a stranger to
read. The second question is much bigger, and it covers fixtures, sample data, screenshots,
error logs, and anything captured from a real system because the real system was the point.

I regenerated the fixture with synthetic values, kept the structure, and moved on satisfied.

## The leak the audit was never designed to find

The public repo went live at 09:39.

Its test file contained a Greenhouse URL, an Ashby UUID, a Lever UUID, a Workday path, and a
`gh_jid` from an embedded board. Eight identifiers in total, and every one of them was a job I
had actually applied to. One was an application I had not submitted yet. One was a
requisition a recruiter had introduced me to that week.

They were there because building the fixtures had been easy. I had a folder full of archived
job descriptions, so I pulled real URLs out of it, which is the fastest way to get realistic
test data and the reason the test data was not fiction.

The pre-publication audit had been clean. It searched for my domain, for `vault/`, for
`applications/`, for the identity strings I knew to worry about. It never searched for company
names, because at no point had I written down that company names were the thing at risk.

That is the whole failure. The audit did not fail. The audit ran, passed, and was answering a
question I had chosen myself.

Fixed at 10:07. Twenty-eight minutes, on a repository with no stars, no forks, and no traffic,
which is luck rather than mitigation. Because the repo was minutes old I could amend and force
push instead of adding a commit, so the identifiers are gone from the history rather than
sitting one `git log -p` away.

Every URL in the tests is now synthetic. `examplecorp`, `acmeco`, invented UUIDs. The URL
*shapes* are what the detection tests exercise, so nothing lost coverage, and synthetic
fixtures do not rot when a requisition closes.

## The third one, which is smaller and more embarrassing

In between those two, I published the wrong README twice.

The first push carried a version I had already revised. I amended and force pushed. The
output said `6 files changed, 557 insertions` and I read it as done.

It was not done. `git commit --amend` rebuilds a commit from the index, and I had never
staged the README. The amend rewrote the same content with a new timestamp, twice, and both
times the terminal told me so: an amend that picks up 35 new lines does not report the same
insertion count as the commit before it. The number was right there and I did not read it.

I only caught it by querying the remote and comparing line counts, which is the check I
should have been running from the start instead of trusting a summary of what I had intended.

## The pattern, which is not new

Three failures in one hour, and they are the same failure:

**A check that passes tells you the thing you looked for is absent. It does not tell you the
thing is safe.**

The secret scan proved no credentials were committed. It said nothing about a personal email
in a fixture. The pre-publication grep proved my identity strings were gone. It said nothing
about eight company names. The amend reported success. It was reporting on an empty index.

My previous project had four instances of this, and the version there was *a passing test
proves the assertion held, it does not prove the code ran*. I wrote a page about it. It did
not stop me repeating the shape a week later in a different medium, which is worth being
honest about: knowing the failure mode by name does not make you immune to it, because each
instance arrives disguised as a different kind of task.

The one thing that did work, both times, was **looking at the actual artifact instead of the
report about it**. The fixture leak was found by opening the file. The company-name leak was
found by grepping the published tree against a list of every company in my pipeline, which is
a check I only wrote after being burned once.

That check is now in the release spec. Audit a public repository against the *contents* of
the private one, not against the paths and identity strings you happened to think of.

## What the tool actually does, and the part worth stealing

Four endpoints, all public, all unauthenticated, none documented anywhere convenient:

| Platform | Endpoint |
|---|---|
| Greenhouse | `boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}?content=true` |
| Ashby | `api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true` |
| Lever | `api.lever.co/v0/postings/{token}/{id}?mode=json` |
| Workday | `{tenant}.{sub}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/job/{path}` |

Two of them have a catch, and one of those is the only genuinely clever thing in the file.

**Ashby returns the entire board**, not the job you asked for, so you filter by matching the
UUID against each entry's `jobUrl`. `includeCompensation=true` is what gets you the pay range
and it is off by default.

**Greenhouse embedded boards carry no token.** When a company hosts its own careers page the
link is `company.com/careers/detail/?gh_jid=5678901234`, and the board token the API needs is
nowhere in the URL. So the tool derives it: take the hostname labels, strip `careers`, `jobs`
and `apply`, then strip company suffixes like `hq`, `inc`, `labs` and `technologies`, and
probe the API with each candidate until one returns a real job. That is how it works on boards
that do not look like Greenhouse at all.

The subtlest bug in the file is an ordering one. Several of these APIs return the description
**entity-escaped, and at least one returns it escaped twice**. Strip the tags before
unescaping and the markup survives as literal words: `span`, `div class`,
`data-ccp-parastyle`. Nothing crashes. The text just quietly fills with markup vocabulary that
then poisons anything you do with it downstream. So it unescapes to a fixed point first, then
strips.

## The one refactor, and how it was proved

The private version shelled out to `curl`. A tool whose selling point is "no dependencies"
should not require a binary that is missing on a default Windows install, so it moved to
`urllib`.

That is the kind of change that is obviously safe and quietly is not, because this function
produces an archive of record. So the change was proved rather than assumed: capture output
from five live postings across all four platforms first, make the change, capture again,
compare.

Byte for byte identical on all five.

The same pass dropped a user-agent string that claimed to be Chrome 126. These are public
APIs published to serve public job boards. There is no reason to lie to them, and all four
accept `ats-fetch/1.1` without complaint.

## Deliberately not claimed

- **Twenty-eight minutes of exposure is not proof nobody saw it.** No stars, no forks, no
  clones I can see, and the identifiers are out of the history. That is a good outcome, not
  evidence of no harm.
- **The endpoints are not a discovery.** At least one public article documents the same six
  ATS APIs. What is here is working code and the two catches, not the existence of the URLs.
- **Nobody else uses this.** It is on PyPI and it has no users. Everything above is about how
  it was built and shipped, not about adoption.
- **The tests do not hit the network.** 29 assertions covering ATS detection, the board-page
  refusal, and the unescape order. They cannot tell you an endpoint still works, only that a
  URL is still routed to the right adapter.
- **The generic HTML fallback is lossier and barely tested.** Four platforms are handled
  properly. Everything else gets tags stripped off a page and is best treated as a draft.
- **One person, one machine, one week of real use.**

## Read the actual work

The decision log records what was ambiguous and what got traded away, including the two
publication mistakes as decisions rather than as anecdotes.
