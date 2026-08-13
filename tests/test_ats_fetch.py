#!/usr/bin/env python3
"""
Tests for ats_fetch.py. No network: everything here is a pure function.

The three things worth protecting are the three that have actually gone wrong or that
carry the knowledge:

  detect()                  which ATS is behind a URL, including the embedded-board case
                            where the board token is absent and only gh_jid survives
  looks_like_single_posting()  a board page returns plenty of text, so length cannot tell
                            it apart from a posting. Getting this wrong archives a
                            directory of open roles in a file that looks correct.
  detag()                   several ATS APIs return the description entity-escaped, some
                            of them twice. Strip before unescape and the markup survives
                            as literal words. Found 2026-08-11.

Run:  python3 tests/test_ats_fetch.py
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import ats_fetch as fj

failures = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<52} {got!r}")
    if not ok:
        failures.append(f"{label}: got {got!r}, want {want!r}")


print("ATS detection from the URL alone:")
for url, want in [
    ("https://job-boards.greenhouse.io/examplecorp/jobs/1234567890", "Greenhouse"),
    ("https://boards.greenhouse.io/acmeco/jobs/2345678901", "Greenhouse"),
    ("https://boards.eu.greenhouse.io/examplegmbh/jobs/3456789012", "Greenhouse"),
    ("https://job-boards.eu.greenhouse.io/examplemedical/jobs/4567890123", "Greenhouse"),
    # The embedded-board case: the company hosts the page, the board token is nowhere in
    # the URL, and only gh_jid identifies the job. This is the one worth publishing.
    ("https://www.examplecorp.com/careers/detail/?gh_jid=5678901234", "Greenhouse"),
    ("https://jobs.ashbyhq.com/examplecorp/00000000-1111-2222-3333-444444444444", "Ashby"),
    ("https://jobs.lever.co/examplecorp/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "Lever"),
    ("https://apply.workable.com/examplecorp/j/ABC1234567", "Workable"),
    ("https://examplecorp.workable.com/j/ABC1234567", "Workable"),
    ("https://examplecorp.wd501.myworkdayjobs.com/Careers/job/Remote/Support_JR100000",
     "Workday"),
    ("https://jobs.smartrecruiters.com/ExampleCorp/1234567890123456", "SmartRecruiters"),
    ("https://jobs.smartrecruiters.com/ExampleCorp/1234567890123456-senior-engineer",
     "SmartRecruiters"),
    ("https://example.com/careers/engineering", None),
]:
    check(url.split("//")[1][:48], fj.detect(url), want)

print("\nposting vs board page:")
for url, want in [
    ("https://jobs.ashbyhq.com/examplecorp/00000000-1111-2222-3333-444444444444", True),
    ("https://job-boards.greenhouse.io/examplecorp/jobs/1234567890", True),
    ("https://examplecorp.wd501.myworkdayjobs.com/Careers/job/Remote/Support_JR100000", True),
    ("https://www.examplecorp.com/careers/detail/?gh_jid=5678901234", True),
    ("https://jobs.smartrecruiters.com/ExampleCorp/1234567890123456-senior-engineer", True),
    ("https://apply.workable.com/examplecorp/j/ABC1234567", True),
    # Boards. Each of these returns a page full of text that is not a posting.
    ("https://jobs.ashbyhq.com/someboard", False),
    ("https://jobs.ashbyhq.com/examplecorp", False),
    ("https://example.com/careers", False),
    ("https://example.com/jobs/", False),
]:
    check(url.split("//")[1][:48], fj.looks_like_single_posting(url), want)

print("\ndetag, the unescape-before-strip order (the 2026-08-11 bug):")
# Singly escaped: one unescape pass exposes the tags, then they are stripped.
once = "&lt;div class=&quot;x&quot;&gt;Hello&lt;/div&gt;"
# Doubly escaped, which is what actually shipped from at least one ATS.
twice = "&amp;lt;div class=&amp;quot;x&amp;quot;&amp;gt;Hello&amp;lt;/div&amp;gt;"
for label, raw in [("singly escaped", once), ("doubly escaped", twice)]:
    out = fj.detag(raw)
    check(f"{label}: text survives", "Hello" in out, True)
    check(f"{label}: no literal 'div'", "div" in out, False)
    check(f"{label}: no literal 'class'", "class" in out, False)

print("\ndetag, ordinary markup:")
# Blank-line separated, because </li> emits a newline and the next <li> emits another.
# It still renders as a list in markdown, and tightening it would change the bytes of
# every archive this tool has already written. Asserted as-is deliberately.
check("list items become dashes", fj.detag("<ul><li>one</li><li>two</li></ul>"), "- one\n\n- two")
check("script contents dropped", "alert" in fj.detag("<script>alert(1)</script>hi"), False)
check("empty input", fj.detag(""), "")
check("none input", fj.detag(None), "")
check("nbsp becomes a space", fj.detag("a&nbsp;b"), "a b")
check("curly apostrophe normalised", fj.detag("don’t"), "don't")

print()
if failures:
    print(f"{len(failures)} FAILED")
    for f in failures:
        print("   ", f)
    sys.exit(1)
print("all passed")
