# Releasing Hyperskills

Release preparation updates the plugin version, changelog, and captured release intent together. Merging the resulting PR publishes that exact merged commit after validation. Ordinary skill PRs keep the current version; release preparation owns version increments.

## Keep derived metadata current

Run `make sync-metadata` after adding, removing, or renaming files or skills. The generator updates explicitly marked regions in the README and contributor guide: the skill badge, linked inventory, reference counts, and repository tree. The marketplace description follows the canonical plugin description. Descriptive skill prose and discovery keywords remain authored.

Run `make all` before committing. The same command runs in CI and fails on generated drift, malformed skills, inconsistent release state, or failing tests. Check mode never repairs files behind the reviewer's back. A second generation pass over the same source produces no changes.

## Prepare a release PR

Choose the increment from the public change:

| Change                                               | Increment |
| ---------------------------------------------------- | --------- |
| Existing skill content, fixes, or supporting tooling | `patch`   |
| Skill addition, removal, or rename                   | `minor`   |
| Plugin architecture or manifest layout               | `major`   |

Supply release notes explaining the changes a user should care about. The workflow does not infer release importance from commit prefixes or ask a model to write notes during publication.

```bash
gh workflow run prepare-release.yml --ref main \
  -f bump=patch \
  -f notes='Improve release recovery and metadata validation.'
```

The workflow captures the selected main revision, validates it, prepares the files, and opens a release PR. The branch name includes the target version and source commit. Repeating the same workflow inputs on the same source reuses a matching branch and open PR. A different existing branch is preserved and reported as a conflict.

The repository must permit GitHub Actions to create pull requests. The workflow requests only the job permissions it needs: repository contents and PR writes, plus Actions writes to dispatch CI. Default workflow permissions can remain read-only. A repository or organization policy that prevents bot PR creation must be resolved before using preparation.

For a local preview from a clean checkout, save notes outside the repository and run:

```bash
uv run scripts/release.py prepare --bump patch --notes-file /tmp/release-notes.md
git diff -- .claude-plugin/plugin.json CHANGELOG.md release.json
```

The local command changes files only. Repeating identical preparation before committing leaves the same version and bytes. Unrelated dirty files or conflicting pending notes stop preparation without discarding work.

## Merge and publish

Review the prepared notes and version, then merge the release PR when CI passes. The release commit must directly follow its captured source on main. A normal merge commit is supported when its first parent is that source; a squash merge is also supported. If main advances, prepare a new release PR from the new revision and close the obsolete one. The check rejects a stale release instead of silently including unreviewed changes.

Require the `Validate and test` status check with strict up-to-date branch checking in the main branch ruleset. A green run against an older base alone cannot prevent a stale PR from merging. Repository rules provide the merge-time enforcement; publication independently checks the source again.

Publication validates the exact event commit, verifies or creates its lightweight version tag, and verifies or creates its GitHub release with the captured notes. Existing tags and releases must match. The workflow never moves a tag or overwrites a different release body.

The checked-in `release.json` starts as `null`, representing an uninitialized release history. Installing the automation does not publish a release or reconstruct historical tags. The first explicitly prepared release starts from the current plugin version.

## Recover an interrupted run

| Interruption                                | Recovery                                                                          |
| ------------------------------------------- | --------------------------------------------------------------------------------- |
| Branch pushed, PR creation failed           | Rerun the original preparation workflow. Matching branch content is reused.       |
| PR created, CI dispatch failed              | Rerun preparation. The open PR is reused and CI is dispatched again.              |
| Tag created, release creation failed        | Rerun the original publication job. The verified tag is reused.                   |
| Tag or release differs from captured intent | Inspect the conflict. Automation stops without overwriting the existing artifact. |

Rerun the original job when recovering publication so it retains the original event commit, even if main has advanced. A fresh preparation dispatch captures the newly selected revision and therefore has different release input.

GitHub documents that token-generated push events do not start ordinary workflows. Preparation explicitly dispatches CI for the release branch, and publication creates the release in the same job as the tag. Neither depends on a bot-pushed tag starting another workflow. Bot-created PR events can also require approval before their runs start. See GitHub's [workflow triggering documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), checked September 2026.

## What the checks establish

Disposable Git repositories exercise preparation, repeat runs, dirty-index handling, stale sources, and merge commits. Fake GitHub responses exercise partial publication, conflicting tags, and API failures. Those tests do not establish repository permissions or a live GitHub release; a successful real workflow run supplies that separate evidence.

Determinism covers generated source and release intent. Commit timestamps, GitHub IDs, and runner timing are external execution details and are not claimed to reproduce byte for byte.
