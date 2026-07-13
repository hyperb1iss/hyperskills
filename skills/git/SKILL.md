---
name: git
description: Use this skill for complex git operations including rebases, merge conflict resolution, cherry-picking, branch management, PR branch upkeep, or repository archaeology. Activates on mentions of git rebase, merge conflict, cherry-pick, git history, branch cleanup, git bisect, worktree, force push, force-with-lease, PR branch, stacked PR, squash-merge, lease, shared repo, or complex git operations.
---

# Git Operations

Advanced git workflows: rebase surgery, conflict resolution, and coexistence in shared multi-agent repos.

## PR Branch Upkeep

The most-run workflow: keeping your own PR branch current against a moving main.

The loop: fetch → backup ref → rebase → re-run gates on the rebased SHA (pre-rebase receipts are void) → fetch again as the **last** pre-push step. Main moves mid-session; expect to loop — three rebases in one turn is normal, each with a fresh backup. The exit condition is machine-checkable, not vibes:

```bash
git merge-base --is-ancestor origin/main HEAD && echo "based on current main"
```

Review etiquette: while a reviewer (bot, human, or agent) is actively reading, hold pushes — batch fixes, then one rebase+push when the review lands. Freshness loops run at push boundaries.

### Pushing rewritten history

Pin the lease — an unpinned `--force-with-lease` is satisfied by your own stale fetch:

```bash
git ls-remote origin refs/heads/<branch>   # confirm the expected SHA immediately before pushing
git push --force-with-lease=refs/heads/<branch>:<expected-sha> origin HEAD:<branch>
```

On a "stale info" rejection, diagnose with `ls-remote` before any retry. Observed causes: auto-delete-on-merge removed the branch, a typo'd lease SHA, or the remote legitimately moved. Bare `--force` is not an escalation path.

### After the base squash-merges

When a parent PR squash-merges, its commits vanish from main's ancestry — a plain rebase replays them as ghosts. Detect the merge type first: squash, rebase-merge, and merge-commit each leave different ancestry.

| Situation                                  | Move                                                                                                                |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Parent PR squash-merged                    | `git rebase --onto <new-base> <old-base-sha>` — only your own commits replay                                          |
| Replay keeps conflicting / branch polluted | Rebuild as main + delta: one `git diff --binary` patch from the backup, applied onto fresh main; prove with range-diff |
| Pushing fixes to an old branch             | Verify PR open-state first — a squash-merged PR's branch is dead                                                      |
| Stacked chain                              | Cascade bottom-up with `--onto`, per-level backup, push bottom-first (validators diff against `origin/<base>`)        |

## Pre-Surgery Ref Reality

Local refs and the forge's view routinely disagree. Before any history surgery:

- Fetch with an explicit refspec — plain `git fetch origin main` can leave `origin/main` stale
- `git rev-parse --is-shallow-repository` — shallow history fabricates merge-bases and breaks three-dot diffs; deepen first
- Cross-check `gh pr view` base/head oids against local `rev-parse` / `ls-remote`
- Probe conflict shape for free: `git merge-tree --write-tree origin/main <branch>` — zero conflicts can also prove a restack is unnecessary
- Pin every operation to a captured SHA, never a moving ref

## Conflict Resolution

Conflicts are intent-merges, not side-picks. Read all three index stages (`git show :1:<file> :2:<file> :3:<file>`) plus the pre-rebase tip before resolving, and ask: did upstream obsolete this branch's mechanism? When main replaced it with a newer abstraction, plug your feature into main's shape instead of resurrecting the old one. Preserve invariant-explaining comments — they're load-bearing. Pace by risk class (slower on security-sensitive files). Close with a mechanical conflict-marker scan; survivors are real.

| Situation                                           | Strategy                                                                                     |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Encoded artifact (lockfile, SOPS, generated schema) | Never text-merge the encoding. Merge the meaning, re-encode with the canonical tool, roundtrip-verify. |
| Simple content conflict                             | Resolve as a union of both sides' intent; prefer the smallest diff.                           |
| Large structural conflict                           | Consider `--ours`/`--theirs` + manual reapply of the smaller side.                            |

### Lock files

Take one side, regenerate with the package tool, never hand-merge:

```bash
git checkout --theirs pnpm-lock.yaml && pnpm install && git add pnpm-lock.yaml
```

Same shape for any generated lockfile. Fold the regenerated lockfile back into the commit that carried it.

## Rebase vs Merge

Ownership and review state decide, not pushed-ness:

| Situation                                       | Use                                                                          |
| ----------------------------------------------- | ----------------------------------------------------------------------------- |
| Your own PR branch behind main (pushed or not)  | Rebase + pinned-lease push. Hold pushes while a review is actively reading.    |
| Branch checked out in another worktree          | Work there; don't steal the checkout.                                          |
| Genuinely shared branch (others based work on it) | **Never rebase.** Merge, or `git revert` for published mistakes.              |
| Cleaning up messy commits before PR             | `git rebase -i` with squash/fixup                                              |

Ceremony scales with collaborator count — a solo repo can live on main — but the push-boundary rules hold regardless.

## Undo Operations

| What happened                     | Fix                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Uncommit / squash (keep changes staged) | `git reset --soft <captured-sha>` — never a moving ref. `reset --soft origin/main` mid-squash silently staged reverts of newly-landed main when the ref moved. Re-check base movement before amending. |
| Need to recover something lost    | Inspect `reflog`, `status`, and `log` first, then `git checkout HEAD@{N}` — never fire recovery commands speculatively     |

## Verify Before You Trust

Regenerating or rebasing is not the same as verifying the result. In a concurrent monorepo, prove it.

**Lockfile check** — after a rebase touches a lockfile, verify with the gate's exact command in a throwaway worktree. `pnpm install --lockfile-only` is vacuous: it never materializes snapshots, so it reports "up to date" while a full install fails.

```bash
git worktree add /tmp/lockcheck HEAD
(cd /tmp/lockcheck && pnpm install --frozen-lockfile)   # the command CI actually runs
git worktree remove /tmp/lockcheck
```

A passing check that disagrees with an observed failure is itself a finding — diagnose why the check is vacuous, upgrade the standard.

**Bracket every rewrite** — backup ref before, range-diff proof after. Persist the proof inputs so the receipt can be reconstructed exactly:

```bash
backup=backup/pre-rebase-$(date +%Y%m%d-%H%M%S)
git branch "$backup" && old_base=$(git merge-base HEAD origin/main)   # persist both to a scratch file
git rebase origin/main
git range-diff "$old_base".."$backup" origin/main..HEAD   # explicit ranges — the three-dot shorthand can include main's new commits
```

**Clean ≠ correct.** Zero conflicts prove nothing about semantics. After any rewrite, run the semantic drift audit: full gates on the rebased SHA, range-diff read as a bug detector (it catches resolutions rolling back newer main), symbol greps across HEAD vs `origin/main` vs the backup ref, syntax checks on every resolved file. Files new on your branch merge "cleanly" while still importing what upstream deleted — typecheck catches it, the merge doesn't.

## Proofs

Match the proof to the claim:

| Claim to prove                              | Proof                                                                            |
| ------------------------------------------- | --------------------------------------------------------------------------------- |
| Replay preserved per-commit intent          | `git range-diff <old-base>..<old-tip> <new-base>..<new-tip>` (explicit ranges)     |
| Squash/reshuffle left the tree identical    | `git rev-parse HEAD^{tree}` equality vs the backup ref — sharper than range-diff for N→1 squashes |
| Cherry-pick / second PR carries same change | `git patch-id --stable` on both                                                    |
| Nothing stranded before deletion            | `git branch --contains` + dry-run prune                                            |
| Merge captured everything                   | Content-parity diff after the merge event                                          |

## History Serves Its Readers

Atomic while working; collapse only when the history itself stops serving the reviewer.

| Concern                                                | Move                                                                                                        |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Squashing a reviewed branch                            | The PR body inherits the narrative — enumerate the logical commits the squash removed. Human-authored PR titles, bodies, and drafts are read-only absent explicit instruction. |
| Post-review fixes                                      | `git commit --fixup=<logical-parent>` + autosquash, not a "review fix" blob. Fix at the introducing commit when CI reads history (diffs `HEAD~1`) rather than the tree. |
| PR ancestry poisoned (wrong-base merge, CODEOWNERS dragnet) | The forge computes review surface from ancestry — merge gymnastics to dodge a force-push is worse than the force-push. Recover: push the clean replacement first, close the old PR with a pointer comment naming the replacement and why, then reopen. |
| Stale failed check inherited from a closed PR          | `git commit --amend --no-edit` mints a fresh SHA with the same tree.                                           |

### Commit bodies

Compose multi-line bodies via `git commit -F -` with a single-quoted heredoc (`<<'EOF'`) or a message file — stacked `-m` flags keep each paragraph as one unwrapped line and burn amend cycles. The quoting is load-bearing: an unquoted heredoc executes backticks and `$()` inside the message before Git sees it. Wrap at 76 characters; length checks are backstops, not the mechanism. Verify the recorded message after any shell-composed body (`git log -1 --format=%B`).

## Shared-Repo Coexistence

Multiple agents (and humans) work the same repo concurrently. Causation decides ownership.

| Signal                                | Move                                                                                                          |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Ambiguous churn in shared files       | Restore churn your own commands generated; leave others' work untouched — even in the same file                 |
| Co-edited file, mixed hunks           | Stage only your hunks; `git commit --only <file>` sidesteps concurrent staging noise                            |
| `index.lock`                          | Triage before removing: size + owning process (`lsof`/`ps`). Zero bytes and no holder = stale; live owner = wait |
| Another agent's rebase in progress    | Hold your verified commit — but a blocker must reproduce before you report it, and after repeated blocked turns escalate with pid + age as a question, not a fact |
| Branch checked out in another worktree | Work there; don't steal the checkout                                                                            |
| Multi-worktree edits                  | Edit tools root at the original cwd — identity-check (`git branch --show-current` + `pwd`) before editing; status-check every involved worktree after |

## Hooks

Hooks are receipts, not friction — wait them out and cite their output. A new hook failure gets fixed, never bypassed (pre-warm the build cache, fix the type error). The bypass window is narrow: the failure is known, named, pre-existing, and unrelated to your diff — or the hook physically can't run here — plus equivalent gates ran green, and the bypass is disclosed in the wrap-up. Some hosts mechanically block `--no-verify`; respect it. Auto-fixing hooks can rewrite unrelated files: diff after every commit, and before restoring a hook-touched file confirm it carried no one else's edits pre-hook — `git restore` discards the whole worktree copy, not just the hook's hunks.

## Non-Interactive Surgery

Agent hosts have no tty:

- `GIT_SEQUENCE_EDITOR=true GIT_EDITOR=true` pre-armors rebases; a stuck editor gets its pid killed, never the rebase
- No parallel git commands during surgery — `index.lock` collisions are self-inflicted
- When the sequencer wedges ("patch staged, commit not recorded"), read `.git/rebase-merge` state files and resume with `git commit -C <sha>` instead of firing recovery commands speculatively

## Safety Rules

1. **Never rebase genuinely shared branches** — your own PR branch is yours to rebase
2. **Pin the lease** — `--force-with-lease=refs/heads/<branch>:<sha>`, confirmed via `ls-remote` immediately before the push; never bare `--force`
3. **Regenerate encoded artifacts** — never text-merge them
4. **Backup ref before destructive ops** — `git branch backup/pre-op-$(date +%Y%m%d-%H%M%S)`; recovery infrastructure, not ceremony, so persist the name and old base to a scratch file
5. **Prove history rewrites** — backup the pre-rewrite head, then explicit-range `range-diff` to confirm every changed commit is intentional
6. **Identity-check before edits in multi-worktree repos** — `git branch --show-current` + `pwd`

## Anti-Patterns

| Anti-Pattern                                       | Fix                                                                                                              |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Manually merging generated lockfiles               | Take one side, regenerate with the package tool                                                                  |
| Trusting a lockfile check that never installs      | Verify with the gate's exact command (`pnpm install --frozen-lockfile`) in a throwaway worktree                  |
| Plain rebase over a squash-merged base             | `git rebase --onto <new-base> <old-base-sha>` — only your commits replay                                          |
| Merge gymnastics to dodge a force-push on a PR branch | Proper rebase + pinned-lease push — ancestry poisoning triggers review dragnets                                 |
| Rebasing a genuinely shared branch                 | Merge, or create a new branch                                                                                     |
| Using `--force`                                    | Pinned `--force-with-lease` only when approved                                                                    |
| Stacked `-m` flags for multi-line commit bodies    | `git commit -F -` heredoc or a message file                                                                       |
| Running recovery commands by habit                 | Inspect `status`, `log`, and `reflog` first                                                                       |
| Staging unrelated work                             | `git add <specific-files>`; `git commit --only <file>` under concurrency                                          |
| `git checkout <commit> -- <paths>` then committing | It **stages silently**; check `git diff --cached --name-only` before each commit or it swallows unintended files |
| Assuming a rebase kept your commits                | Prove it — explicit-range `range-diff`, tree-hash, or patch-id per the proofs table                               |

## What This Skill is NOT

- Not for routine `git status` or simple commits.
- Not permission to rewrite genuinely shared history.
- Not a replacement for understanding the diff before committing.
