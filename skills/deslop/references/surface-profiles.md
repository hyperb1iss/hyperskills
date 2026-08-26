# Surface profiles

One profile per surface, each with a worked artifact-level example. Sentence-level fixes live in `pattern-catalog.md`; this file is about what a whole artifact should look like when it is clean, and which rules do not apply where.

Read the profile before editing. The most expensive deslop failure is not a missed tell, it is a correct rule applied to a surface that needed the opposite.

## Authority map

When a surface has its own skill, that skill owns the artifact's structure and this skill contributes prose patterns only.

| Surface                          | Structural authority | Deslop contributes                     |
| -------------------------------- | -------------------- | -------------------------------------- |
| PR body, PR comment reply        | `super-good-pr`      | Prose patterns, never shape            |
| PR review report                 | `hyper-pr-review`    | Prose patterns, never severity markers |
| Commit message                   | `implement`, `git`   | Prose patterns, plain-text enforcement |
| Spec, plan document              | `plan`               | Prose patterns, full pass              |
| Research report                  | `research`           | Prose patterns, full pass              |
| README, docs, blog, Slack, email | This skill           | Everything                             |
| Agent brief, skill file, memory  | None                 | Nothing. Exempt                        |

## README and project intro

Register: plain, concrete, second person. The reader is deciding whether to keep reading, so the first two sentences must say what the thing is and what it does, with no positioning.

Never touch: code blocks, install commands, badge markup, link targets.

Common failure: the intro is entirely unfalsifiable claims (E7) plus puffery (R2), and says nothing a competing project's README does not also say (R14).

**Before:**

> Nexus is a powerful, seamless task runner built for modern development workflows. Leveraging a robust dependency graph, it delivers blazing-fast builds while maintaining an elegant developer experience. Whether you're working on a small script or orchestrating a complex monorepo, Nexus provides the flexibility you need.

**After:**

> Nexus is a task runner for monorepos. It builds a dependency graph from your task definitions, runs independent tasks in parallel, and skips any task whose inputs have not changed since the last run.
>
> On a 40-package repo, a no-op build takes 300ms.

The rewrite drops every adjective and keeps only claims a reader can check. The number is only allowed here because the draft's author supplied it; if it were invented, that is E1 and a worse defect than the puffery it replaced.

## Documentation body

Register: mechanism first. Every paragraph should tell the reader something they could act on or verify.

Never touch: code blocks, CLI output, config samples, frontmatter, API signatures, error strings.

Common failure: feeling instead of mechanism (R13), signposting (R5), and header inflation (S1) chopping a two-paragraph explanation into four labeled stubs.

**Before:**

> ## Understanding Caching
>
> Caching is important.
>
> Let's dive into how Nexus handles caching. Nexus provides a powerful caching layer that ensures your builds stay fast, leveraging content hashing to intelligently determine what needs to rebuild.

**After:**

> ## Caching
>
> Nexus hashes every task's declared inputs (source files, environment variables, and the task definition itself) and stores the output under that hash. On the next run, a matching hash means the task is skipped and its cached output is restored.
>
> A task that does not declare an input will not invalidate when that input changes. This is the most common cause of a stale build.

Note what the fix adds: the actual mechanism, and the failure mode a reader needs. Deslopping is not only deletion.

## Release notes and changelogs

Register: version-scoped and factual.

Diff-anchored writing (E6) is **correct** here. These documents exist to narrate change, so "replaces the old resolver" is the point, not a tell.

Common failure: significance inflation (R1) and a generic upbeat close (R6) attached to an ordinary patch release.

**Before:**

> ## 2.4.0
>
> This release marks an exciting milestone in our journey, delivering a host of powerful improvements that enhance the developer experience. We've completely revamped the caching layer for blazing-fast performance. The future looks bright for Nexus!

**After:**

> ## 2.4.0
>
> The cache now keys on the task definition as well as its inputs, so editing a task's command invalidates it. Previously an edited command reused the old output.
>
> Breaking: `nexus run --force` is now `--no-cache`.

## Commit body

Register: plain text, factual, written for someone reading it years later during a bisect.

Hard rules: no markdown, no fences, no headers, no emoji in the subject, wrap at 76 columns. Attribution trailers and URLs are exempt from the wrap and from tell scanning.

Common failure: house jargon (L7), hedging (L4), and narrating the session instead of the change.

**Before:**

```
fix: various improvements to the cache

Refactored the caching layer to be more robust. This should
significantly improve performance and probably fixes the stale
build issue that was load-bearing for the CI flake.
```

**After:**

```
fix(cache): key cache entries on the task definition

Editing a task's command reused the previous output, because the
cache key covered declared inputs but not the command itself. CI
saw this as an intermittent stale build whenever a task definition
changed in the same commit as its sources.

The key now includes a hash of the resolved task definition.
```

The rewrite names the mechanism, states the observed symptom as fact rather than guess, and drops the jargon a stranger would not decode.

## Slack and email

Register: warm, complete sentences, peer energy. Explain at whatever length understanding requires.

Never touch: a required signature footer, thread links, code snippets.

Common failure: chatbot artifacts (E4), sycophancy (E5), and compression into fragments that read as curt.

**Before:**

> Great question! Happy to help clarify. So basically the deploy failed due to the fact that the migration timed out. Let me know if you'd like me to dig deeper!

**After:**

> The deploy failed because the migration hit the 30-second statement timeout while backfilling `orders.tenant_id`. The table is 40M rows, so it needs to run in batches instead of one statement. I can push that change today if you want it in this release.

## PR body: what not to strip

The instructive case. A PR body has required structure that a general cleanup pass destroys.

Preserve: semantic emoji headers, bold section leads, tables of enumerable facts, severity markers, the receipts and their counts, any body a human wrote.

Fix: em dashes, inflated significance, hedging, chatbot closers, house jargon, participle pseudo-analysis.

**Before:**

> ## 💡 What this is
>
> This PR fundamentally reimagines the rate limiter — a pivotal step toward a more robust API — leveraging a token bucket to ensure fairness across tenants, showcasing our commitment to reliability.

**After:**

> ## 💡 What this is
>
> Per-tenant rate limiting, enforced at the gateway. A shared global limit let one noisy tenant consume the whole budget, so each tenant now gets its own token bucket keyed on the tenant id from the request's signed context.

The emoji header survives because it is load-bearing. Everything after it was decoration.

## Code comments and docstrings

Register: describe the thing as it is.

Diff-anchored comments are a tell here, unlike changelogs. A comment saying "replaces the old loop" rots the moment the old loop is forgotten.

Never touch: doctest bodies, type annotations, parameter names, example output.

**Before:**

```python
# We now use a heap here instead of sorting the whole list every time,
# which was the previous approach and was really slow.
```

**After:**

```python
# A heap keeps the k smallest without sorting the full list: O(n log k)
# rather than O(n log n), which matters because n is the full event
# backlog and k is the page size.
```

## Profiles without worked examples

These need a rule, not a demonstration.

| Surface                                             | The rule that matters most                                                                                                                   |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Blog, essay, opinion, personal writing              | Voice belongs here. Sterile neutrality is its own tell, so stance, mixed feelings, and uneven rhythm are the fix, not a violation             |
| Encyclopedic, reference, neutral docs               | Neutral **is** the human register. Never inject first person or opinion. This is where an over-eager "add soul" pass does real damage          |
| Scientific, legal, medical, forecasting, postmortem | Hedges are honest. Strip only hedges that qualify nothing, and never convert a calibrated claim into a flat one                               |
| Fiction and creative writing                        | The no-fabrication rule does not apply. Invented detail is the work                                                                          |
| Marketing copy the user actually wants              | Puffery is the genre. Flag it once, then respect the brief. Do not silently rewrite persuasion into a spec sheet                              |
| Agent briefs, skill files, prompts, memories        | Exempt. Dense jargon and tables are correct for a machine reader, and prose polish here spends tokens for no reader                            |
| Text quoting or discussing slop                     | Exempt. A watched phrase inside a quotation, a title, or an example is being discussed, not used                                              |

## When the surface is unclear

Ask one question: who reads this, and can they ask a follow-up? A reader who can ask (the user in chat, an agent in a brief) tolerates jargon and density. A reader who cannot (anyone downstream of a published artifact) needs the full pass.

If the answer is genuinely both, treat it as published and run the pass.
