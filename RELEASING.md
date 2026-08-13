# Releasing

A release is a git tag, a set of notes, and an updated changelog. Nothing else.

## When to cut one

Release when a user-visible change has landed, not on a schedule and not per commit.

| Change | Version |
|---|---|
| A flag changes meaning, or the output format breaks an existing archive | major, `2.0.0` |
| A new ATS adapter, or a new flag | minor, `1.1.0` |
| A parser fix, a wrong pattern, a crash | patch, `1.0.1` |

⚠️ **The output format is the contract.** People archive postings and keep them. A change that
makes a new capture inconsistent with an old one is a **major** version, even when the code
change looks small.

## Steps

1. Move the `[Unreleased]` entries in `CHANGELOG.md` into a new version section, dated.
2. Add a fresh empty `[Unreleased]` section above it.
3. Update the two link definitions at the bottom of `CHANGELOG.md`.
4. Bump `UA` in `ats_fetch.py` if the minor or major number changed. It reports the version to
   every platform it calls, so a stale value is a small lie told at scale.
5. Commit, then tag and publish:

```
git commit -am "release: v1.1.0"
git push
git tag -a v1.1.0 -m "v1.1.0"
git push origin v1.1.0
gh release create v1.1.0 --notes-file /tmp/notes.md
```

`gh release create v1.1.0 --generate-notes` writes the notes from commits and merged pull
requests instead. Use that when the release is small and the commit messages already say it.

6. Check that CI is green on the tag before announcing it anywhere.

## Notes template

Write for someone deciding whether to upgrade. Lead with what they get, state what breaks,
and thank contributors by name.

```markdown
## What is new

- **<the change, in user terms>.** <One sentence on why it matters.>

## Fixed

- <The wrong behaviour, then the right one.>

## Breaking

- <What stops working, and the exact change a user has to make.>
  Omit this section entirely when nothing breaks. Do not write "none".

## Thanks

@<contributor> for <the specific thing>.
```

📌 Skip any section with nothing in it. A release note padded with "No breaking changes" and
"No fixes" trains people to stop reading them.

## What this project does not do

- **No PyPI package yet.** The tool is a single standard-library file and cloning it costs two
  commands. Publishing claims the name permanently and creates an expectation of maintenance,
  so it is a deliberate decision rather than a default. Revisit it when someone asks.
- **No release branches.** Single maintainer, single line of development. Tag `main`.
- **No pre-releases.** There is nothing here big enough to need one.
