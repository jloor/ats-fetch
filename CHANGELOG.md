# Changelog

Notable changes to ats-fetch. Format follows [Keep a Changelog](https://keepachangelog.com/),
versioning follows [Semantic Versioning](https://semver.org/).

Entries describe what changed **for someone using the tool**. A refactor that changes no
behaviour does not belong here.

## [Unreleased]

### Added

- **SmartRecruiters** support, for postings at `jobs.smartrecruiters.com/{company}/{id}`.
  SmartRecruiters splits a posting into four named sections (company description, job
  description, qualifications, additional information) rather than returning one blob. The
  section headings are preserved, because flattening them would lose which requirements the
  employer listed as qualifications and which as additional information.
- **Workable** support, for postings at `apply.workable.com/{company}/j/{shortcode}` and the
  `{company}.workable.com/j/{shortcode}` form that redirects to it. Workable omits every
  description unless the request asks for them, so the board is fetched with `details=true`
  and the posting is picked out by shortcode.
  ⚠️ The bare share link `apply.workable.com/j/{shortcode}` is **not supported**. It carries
  no company, there is no shortcode-only endpoint, and the page is client rendered, so
  nothing in that URL identifies which board to query.

## [1.1.1] - 2026-08-13

### Fixed

- Replaced a real job requisition ID, used as an example URL in the README, with a synthetic
  one. The 1.1.0 page on PyPI still shows the original, because the metadata of a published
  release cannot be edited.

### Notes

- 1.1.0 was uploaded to PyPI but never tagged here. No commit ever matched its contents, so
  tagging one would misrepresent what was released. **1.1.1 is the first tagged package
  release.**
- The user-agent stays `ats-fetch/1.1`. A patch release does not change it.

## [1.1.0] - 2026-08-13

### Added

- Published to PyPI. `pip install ats-fetch` provides an `ats-fetch` console command, so
  the tool no longer has to be cloned to be used.

### Changed

- The user-agent now reports `ats-fetch/1.1`.

### Notes

- Still no dependencies. That is a constraint rather than an accident: adding one would mean
  the tool stops working on a machine that has only a Python interpreter.

## [1.0.0] - 2026-08-13

First public release.

### Added

- Archive a job posting verbatim from its URL, as a metadata table plus the full unedited
  posting text.
- Support for **Greenhouse**, including `gh_jid` embedded boards and the `.eu` domains.
  Where a company hosts its own careers page and the board token is absent from the URL, the
  token is recovered from the hostname and probed against the API.
- Support for **Ashby**, including published compensation tiers via `includeCompensation`.
- Support for **Lever**, stitching the description, lists, and additional sections.
- Support for **Workday**, via the `wday/cxs` endpoint.
- Generic HTML fallback for unrecognised platforms.
- `--new` and `--append` to write `job-description.md` into a directory, `--json` to dump the
  raw API payload.
- Capture of the fields employers most often edit after posting: compensation as stated,
  location as stated, the `isRemote` flag, and the posted date.
- Refusal to archive a board or listing page. A directory of open roles returns plenty of
  text, so length cannot distinguish it from a posting, and archiving one produces a file
  that looks correct and contains no job.
- Refusal to overwrite an existing verbatim block without `--new`.
- Tests covering ATS detection including the embedded-board case, the board-page refusal, and
  the unescape order. No network required.

### Notes

- Standard library only. Python 3.9 or newer.
- HTML entities are unescaped to a fixed point **before** tags are stripped. Several of these
  APIs return the description entity-escaped, and at least one returns it escaped twice.
  Stripping first leaves the markup behind as literal words such as `span` and `div class`,
  which then poison anything done downstream with the text.

[Unreleased]: https://github.com/jloor/ats-fetch/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/jloor/ats-fetch/releases/tag/v1.1.1
[1.0.0]: https://github.com/jloor/ats-fetch/releases/tag/v1.0.0
