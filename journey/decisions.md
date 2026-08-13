# Decision log

Calls made, what was ambiguous, what was chosen, and what was traded away.

Separate from the overview on purpose. The overview is the narrative; this is the set of
places where more than one answer was defensible and one had to be picked.

---

## D1: Invert the dependency instead of extracting repeatedly
**2026-08-13**

**Ambiguity:** The tool lived inside a private repository next to a job search. The obvious
move was to copy the shareable parts out and delete the private ones on the way.

**Chose:** Make the public repository the upstream. The private one consumes it.

**Why:** The plan priced a single task, and the actual requirement is recurring. Publishing
once is a careful morning. Publishing whenever the code changes is a deletion that has to be
correct every time, forever, at the end of a workday, with no second reviewer. A process that
depends on someone remembering is not a boundary.

Measuring the coupling first is what made the decision cheap: four places in the whole engine
reached into private content. The problem was never the size of the coupling, it was that a
small repeated manual step had been chosen over a boundary the tooling can enforce.

**Traded:** The private repository now has to install a package instead of importing a local
file, and the two copies can drift until that inversion is actually done.

---

## D2: A fresh repository with no shared history
**2026-08-13**

**Ambiguity:** `git subtree split` preserves the commit history of an extracted directory,
which is normally the better outcome.

**Chose:** A new `git init` and a single root commit. No fork, no subtree.

**Why:** The private history contains the vault: salary floors, comp research, recruiter
names, negotiation decisions. Any history-preserving split carries all of it, and a clone
plus `git log -p` reads it back. The build log is not worth that.

**Traded:** Thirty commits of real development history are not visible on the public
repository. The story lives in this writeup instead, which tells it better than a diff would.

---

## D3: Ship one tool rather than a toolkit
**2026-08-13**

**Ambiguity:** A second tool in the same private repo does coverage analysis against a
posting, and it had roughly one line of coupling. It could have shipped at the same time.

**Chose:** `ats-fetch` alone.

**Why:** The second tool only makes sense to somebody who has already archived a posting. It
reinforces this one rather than standing beside it, and a repository that does one thing is
easier for a stranger to evaluate in ten seconds.

**Traded:** A slightly thinner first release, and a second extraction to do later.

---

## D4: Fix the four warts before publishing rather than after
**2026-08-13**

**Ambiguity:** The tool worked. Shipping it as-is would have taken minutes; the objections a
reviewer would raise were all cosmetic or structural rather than functional.

**Chose:** Fix all four first. Replace the `curl` subprocess with `urllib`, drop the
user-agent that claimed to be Chrome, strip the docstring references to the private
repository, and add tests.

**Why:** The repository's whole purpose is to be read. A reviewer who finds a shelled-out
`curl` in a file advertised as dependency-free stops reading, and they are right to.

**Traded:** A few hours, and one more chance to leak something while editing. Which is
exactly what happened. See D6.

---

## D5: Prove the curl-to-urllib change instead of testing it
**2026-08-13**

**Ambiguity:** Swapping an HTTP client is routine. Running the tool once afterwards and seeing
output would normally be enough.

**Chose:** Capture full output from five live postings across all four platforms before the
change, capture again after, and diff.

**Why:** This function produces the archive of record. "It still works" is not the standard;
"it produces the same bytes" is. A subtle difference in redirect handling or character
encoding would not have shown up in a spot check, and it would have been invisible until two
archives of the same posting disagreed months later.

Byte for byte identical on all five.

**Traded:** Twenty minutes, and a dependency on those five postings still being live at the
time. Both were worth it.

---

## D6: Synthetic test fixtures, after real ones leaked a live job pipeline
**2026-08-13**

**Ambiguity:** Test URLs have to look real for URL-shape detection to be meaningfully tested.
The fastest source of realistic URLs was a folder of archived job descriptions.

**Chose:** After publishing, and after finding the problem, replace every URL with an invented
one. `examplecorp`, `acmeco`, fabricated UUIDs and job ids.

**Why:** The real URLs were eight jobs I had applied to, including one application not yet
submitted and one requisition a recruiter had introduced me to that week. Anyone comparing the
repository to my public profile could read the pipeline off the test file.

Detection tests exercise URL *shapes*, so nothing lost coverage. Synthetic fixtures also do
not rot when a requisition closes, which real ones do.

**Traded:** Nothing, which is what makes this the most annoying entry in the log. There was
never a reason to use real URLs beyond convenience.

---

## D7: Force push to remove the identifiers rather than commit over them
**2026-08-13**

**Ambiguity:** Rewriting published history is bad practice. A normal follow-up commit would
have fixed what visitors see.

**Chose:** Amend and force push, three times across the hour.

**Why:** A follow-up commit fixes the visible file and leaves the identifiers one `git log -p`
away permanently. The repository was under half an hour old with no stars, forks or observable
clones, so the usual objection to rewriting history did not apply yet. That window closes fast
and it does not reopen.

**Traded:** Orphaned commits remain reachable by SHA on GitHub until it collects them. Nobody
has those SHAs, but that is obscurity rather than removal.

---

## D8: Accept pull requests
**2026-08-13**

**Ambiguity:** A single maintainer with no time is the standard argument for saying no
contributions up front, and an ignored pull request looks worse than a stated refusal.

**Chose:** Accept them, with the scope and the response time written into the README.

**Why:** The realistic contribution to this project is a new ATS adapter: one function
following an existing pattern plus a row in the detection test, reviewable in twenty minutes,
and the single best thing that could happen to the tool. Refusing contributions closes that
door to avoid a burden that is mostly hypothetical on a repository this small.

The failure mode is silence rather than volume, so the README states what will be merged, what
will not, and roughly how long a review takes.

**Traded:** An obligation that is small but real, and a security surface. Nothing that touches
the fetch layer or adds a dependency gets merged without reading every line.

---

## D9: Publish to PyPI as 1.1.0, not 1.0.0
**2026-08-13**

**Ambiguity:** `v1.0.0` was already tagged. Publishing the package as 1.0.0 would have kept
the numbers aligned.

**Chose:** 1.1.0.

**Why:** The tree at `v1.0.0` has no `pyproject.toml`, so publishing 1.0.0 to PyPI would ship
something different from what that tag contains. A console entry point is also a real
user-facing addition, which is a minor bump rather than a packaging detail.

**Traded:** The first PyPI release is not version 1.0.0, which looks slightly odd and is
correct.

---

## D10: No dependencies, as a constraint rather than a preference
**2026-08-13**

**Ambiguity:** `requests` would make the fetch layer shorter and handle a few edge cases for
free.

**Chose:** Standard library only, stated in the README and in the contribution rules as
something that will not be merged away.

**Why:** The tool's realistic user is somebody mid-job-search on whatever machine they have.
"Works with nothing but a Python interpreter" is a real property for that person, and it stops
being true the first time it is relaxed.

**Traded:** A slightly longer `get()`, and manual handling of a few HTTP details that a
library would cover.
