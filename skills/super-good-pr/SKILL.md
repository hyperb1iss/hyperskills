---
name: super-good-pr
description: Use this skill when writing or polishing a pull request description — drafting a PR body, opening a PR, rewriting a weak one, or when asked to make a PR "good" or "a banger". Produces reviewer-first descriptions that lead with why, prove every claim with evidence, name the load-bearing files and invariants, and stay honest about blast radius. Activates on mentions of write a PR, PR description, draft a PR, open a pull request, polish this PR, make this PR good, banger PR, PR body, describe these changes, or PR writeup.
---

# Super Good PR Descriptions

A PR description is read by a human who has to rebuild your mental model from zero and decide whether to trust it. The job is to hand them that model fast, prove the parts they'd doubt, and be honest about what you didn't do.

**Core insight:** lead with _why_, prove with _evidence_, be honest about _blast radius_. A changelog tells the reviewer what moved. A super-good PR tells them what to believe, where to look, and what could still bite. The difference is entirely in altitude and receipts, not length.

**How to read this skill:** the spine below is a map, not a script. Real PRs drop sections that don't apply and add domain-specific ones that do. A one-file fix doesn't need a rollout-sequencing section; a migration does. Match the shape to the change. The non-negotiables are the part that's actually load-bearing — the section order is just a reliable way to deliver them.

## The non-negotiables

These are what make a description land. If a section doesn't serve one of these, cut it.

- **Open with the mental model, not the diff.** First paragraph says what this _is_ and, when there's a naive version a reader would assume, why that version is wrong. "IP/CIDR allowlists are the wrong primitive here — behind a shared cloud edge, allowing an IP means allowing every tenant on it." Now the reviewer knows why the code looks the way it does before they read a line of it.
- **Name the load-bearing invariant and tell reviewers to anchor on it.** Most PRs have one property that, if broken, breaks everything: an ordering, a fail-closed default, an idempotency key. Say it out loud. "Anchor on one property: no upstream socket is opened until every check passes." That sentence directs the entire review.
- **Name actual files, functions, and patterns.** `proxy.rs`, `resolvePolicy()`, `ON CONFLICT (id) DO UPDATE`, "the write → audit → revoke ordering." A reviewer should be able to navigate the diff cold from your prose. Vague nouns ("the handler", "some validation") make them hunt.
- **Prove every claim with a receipt.** Not "tests pass" — `cargo test -p proxy → 98 passed, 0 failed`. Not "it's safe" — show the test that pins it. Assertions are free; evidence is the whole point of the section.
- **Be honest about blast radius.** What's untouched ("default deployments get none of this"), what's deliberately _not_ built (the dangerous-but-obvious alternative you rejected, and why), and what's a known gap shipping as a follow-up. Hiding the gaps reads as not knowing them.

## The spine

Use the headers that carry weight for this change. Each is a `##` with a semantic emoji (palette below).

1. **`# <emoji> <short evocative title>`** — a noun phrase that names the thing, not a verbatim copy of the commit subject. "Per-tenant rate limiting, end to end", not "feat(api): add limiter".
2. **Context blockquote (`>`)** — one to three lines orienting the reader. For a standalone PR, where it sits and what it assumes. For a stack, the nav line (see Stacked PRs below).
3. **`## 💡 What this is`** — the core, two to four sentences. Lead with the mental model; kill the naive primitive here if there is one.
4. **`## 🤔 Why we need it & what it replaces`** — the old world and why it falls short; what's deliberately _not_ built and why the obvious version was dangerous; the blast-radius framing ("dark by default", "non-X deployments untouched").
5. **`## 🎯 The invariant / anchor`** _(when there's one load-bearing property)_ — the single thing to anchor the review on. Optional but powerful; skip it if the change has no single crux.
6. **`## 🛠️ How it works`** — a numbered, sub-headed walkthrough a reviewer follows cold. Name files. Name patterns by name. This is where most of the body lives.
7. **Domain deep-dives** _(as needed)_ — `## 🗄️ The database`, `## 🔗 Identity, end to end`. Add one when a subsystem deserves its own focused pass.
8. **`## 🚦 Rollout sequencing (and why it's safe)`** _(for anything deployed)_ — the order of operations, what's safe to stop at, what the old path keeps doing.
9. **`## 🔁 What changed since the last review round`** _(on re-review)_ — the delta. Credit reviewers by handle. Mark security/critical fixes (🛡️ / 🚨). This is how a re-reviewer reloads without re-reading.
10. **`## 🧪 Validation`** — the receipts. Test suites with PASS counts, typecheck clean, render/lint green; one honest `⚠️` line for what's _not_ covered, with the backstop and the open follow-up.
11. **`## 🔍 What reviewers should focus on`** — the three-to-five trickiest surfaces, bulleted. End with what's intentionally out of scope.
12. **`## 📌 Follow-ups (deliberate non-fixes)`** _(when known gaps exist)_ — bounded gaps, why each is safe to defer.

## Evidence, not assertion

The Validation section is where trust is won or lost. Rules:

- Show the command and its result, not a summary of the result. `pnpm turbo typecheck` across the changed package and its dependents → 112 tasks clean.
- Count things. "25 passed", "98 passed, 0 failed", "12 passed (dark-by-default, label-gate dependencies, patch ordering…)". The parenthetical says _what_ the count proves.
- One honest `⚠️` beats ten green checks. "Local integration tests stay blocked by a local socket conflict; the CI job is the backstop, and a dedicated CI job for them is an open follow-up." That single line builds more trust than the whole rest of the section.
- If you didn't verify something, say so. Never imply a check ran that didn't.

## Emoji palette

Load-bearing, never decorative, never stacked. Section-semantic set that works:

`💡` what · `🤔` why · `🎯` anchor/invariant · `🛠️` how · `🗄️` database · `🔗` identity · `🎫` issuance · `📡` serve/API · `🧹` cleanup/retention · `🚦` rollout · `🔁` what-changed · `🧪` validation · `🔍` reviewer-focus · `📌` follow-ups · `🛡️` security fix · `🚨` critical fix · `🏷️` labels · `🔄` reconnect/refresh.

General palette also available when a header wants personality: 💜🔮⚡🌙🎭🦋🌸🌊🪄💎🌈🦄. The rule is one emoji per header, chosen because it means something.

**Banned — the AI-slop set, never use:** 🚀 ✨ 💯 🙏 👀 🎉 👍 🔥. Note 👀 specifically: it's a tempting choice for "reviewers should look here" and it shows up in the wild, but it's on the banned list — use `🔍` for the reviewer-focus header instead.

## Voice and anti-slop

- **"Banger" is the quality bar, not vocabulary.** Never write "this is a banger / gorgeous / sick / cinematic" into a PR body. Those are words for talking _about_ the work, not in it. The bar means: leads with why, proves claims, honest about blast radius. Real PR voice is plain, root-cause-first, full sentences.
- Full sentences that build linearly. No fragment-style compression, no em-dash overuse, no corporate slop ("in order to", "it should be noted"), no hedging ("just", "simply", "basically").
- Tables only for enumerable facts — a profile→mode mapping, a port list, a pass/fail grid. Never pack reasoning into table cells; reasoning goes in prose.
- A generated-by attribution footer is fine to leave in — many harnesses add one automatically.

## When the repo has a PR template

Make the template sing; don't abandon it. Map this spine onto the repo's sections — a `Changes / Reason / Validation / Reviewer notes` template absorbs the same content, just under its own headers. The non-negotiables don't change; only the section labels do. Keep any required checkboxes and metadata the template demands.

## Stacked PRs

A stack needs a nav blockquote at the top of every PR so a reviewer always knows where they are and what's landed:

```
> **Stack PR 2 of 4 · PROJ-481** — the policy engine.
> `#101` (data plane, ✅ merged) → **`#102` you are here** → `#103` (admin surface) → `#104` (client adoption).
> Rebased onto current `main`.
```

Each PR's "What this is" then says what the _previous_ PR established and what this one adds, so the stack reads as one argument across several documents. End each with what's deferred to the next PR in the stack.
