# Changelog

Notable changes to ats-fetch. Format follows [Keep a Changelog](https://keepachangelog.com/),
versioning follows [Semantic Versioning](https://semver.org/).

Entries describe what changed **for someone using the tool**. A refactor that changes no
behaviour does not belong here.

## [Unreleased]

Nothing yet.

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

[Unreleased]: https://github.com/jloor/ats-fetch/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/jloor/ats-fetch/releases/tag/v1.0.0
