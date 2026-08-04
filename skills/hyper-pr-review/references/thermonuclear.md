# Thermonuclear Mode

The structural ambition pass. Correctness asks "does it work"; this asks "did the codebase get better." Run it on explicit request ("thermonuclear") or when the diff shapes architecture. It layers on top of the finding pipeline: structural findings still pass the falsifier gate, and their falsifiers are mechanical measurement or a sketched behavior-preserving alternative.

Above all, be ambitious about structure. Do not stop at local cleanup opportunities. Actively hunt "code judo" moves: restructurings that preserve behavior while making the implementation dramatically simpler, smaller, more direct, and more elegant. Assume one is often available; the job is to find it or to establish that it isn't there.

## The Baseline Charge

> Perform a deep code quality audit of the scoped changes. Rethink how the change could be structured to meaningfully improve quality without changing behavior. Improve abstractions and modularity, reduce spaghetti, improve succinctness and legibility. Be ambitious: if there is a clear path to a dramatically simpler implementation that involves restructuring, name it. Measure twice, cut once.

## Standards

1. **Be ambitious about structural simplification.** Look for reframings where whole branches, helpers, modes, conditionals, or layers disappear entirely. Prefer the solution that feels inevitable in hindsight. When complexity can be deleted rather than rearranged, push hard for deletion.
2. **Thresholds are smells, not compliance lines.** A PR pushing a file past ~1,000 lines is a strong decomposition smell, and a file parked at 996 lines does not pass the rule; the smell is the sprawl, not the number. Ask whether the code should be decomposed first. Waive only for a compelling structural reason that leaves the file clearly organized.
3. **No spaghetti growth.** New ad-hoc conditionals, scattered special cases, and one-off branches inserted into unrelated flows are design problems, not stylistic nits. Push the logic into a dedicated abstraction, helper, state machine, policy object, or module instead of tangling an existing path. Call out changes that make surrounding code harder to reason about even when they technically work.
4. **Clean the design, don't just accept working code.** If behavior can stay the same while the structure becomes meaningfully cleaner, push for the cleaner version. Strongly prefer simplifications that remove moving pieces over refactors that spread the same complexity around.
5. **Boring beats magical.** Brittle, ad-hoc, or "magic" behavior is a quality problem. Be skeptical of generic mechanisms that hide simple data-shape assumptions. Flag thin abstractions, identity wrappers, and pass-through helpers that add indirection without buying clarity.
6. **Type and boundary cleanliness.** Question unnecessary optionality, `unknown`, `any`, and cast-heavy code where a clearer boundary could exist. Prefer explicit typed models and shared contracts over loosely-shaped ad-hoc objects. A branch relying on silent fallback to paper over an unclear invariant should make the boundary explicit instead.
7. **Canonical layer, canonical helpers.** Call out feature logic leaking into shared paths and implementation details leaking through APIs. Prefer the existing canonical utility over a bespoke near-duplicate. Push code toward the package, service, or module that already owns the concept instead of normalizing architectural drift.
8. **Orchestration and atomicity.** Unnecessary serialization of independent work and related updates that can leave state half-applied are design smells when the cleaner structure is obvious. Don't chase micro-optimizations; do flag avoidable orchestration complexity that makes the implementation brittle.
9. **Scale, don't nerf.** At thermonuclear intensity the nerf-detector lens hardens: any restriction shipped as a fix (rate limit, cap, serialization, retry blanket) is presumptively blocking until the contended resource is named and the limit proven fundamental.

## Primary Review Questions

For every meaningful change, ask:

- Is there a code-judo move that would make this dramatically simpler?
- Does the platform or ecosystem now ship a primitive that deletes this machinery outright? Ground the answer in a dated primary source, not training-data memory (see Grounding at the Edge in SKILL.md).
- Can the change be reframed so fewer concepts, branches, or helper layers are needed?
- Does this improve or worsen the local architecture?
- Did the diff add branching complexity where a better abstraction should exist?
- Did a previously cohesive module become more coupled, more stateful, or harder to scan?
- Is this logic living in the right file and layer, or did it leak across a boundary?
- Did the change enlarge a file or component past a healthy size boundary?
- Are repeated conditionals signaling a missing model or missing helper?
- Is the implementation direct and legible, or does it lean on special cases and incidental control flow?
- Is each abstraction earning its keep, or is it a wrapper?
- Did the diff introduce casts, optionality, or ad-hoc shapes that obscure the real invariant?
- Is the orchestration more sequential or less atomic than it needs to be?

## Flag Aggressively

- A complicated implementation where a cleaner reframing would delete whole categories of complexity.
- Refactors that move code around without reducing the number of concepts a reader must hold.
- A file crossing a size boundary because of the PR, when the new code could be split out.
- New conditionals bolted onto unrelated code paths; one-off booleans, nullable modes, or flags complicating existing control flow.
- Feature-specific logic leaking into general-purpose modules.
- Generic "magic" handling that hides simple structure.
- Thin wrappers and identity abstractions that add indirection without simplifying.
- Unnecessary casts, `any`, `unknown`, or optional params muddying the real contract.
- Copy-pasted logic where a helper should exist; bespoke helpers where a canonical utility already exists.
- Narrow edge-case handling implemented in the middle of an already busy function.
- "Temporary" branching likely to become permanent debt.
- Sequential async flow where obviously independent work would be simpler run in parallel.
- Partial-update logic that leaves state less atomic than necessary.

## Preferred Remedies

Ordered by ambition; reach as high as the change allows:

- Delete a whole layer of indirection rather than polishing it.
- Reframe the state model so conditionals disappear instead of getting centralized.
- Change the ownership boundary so the feature becomes a natural extension of an existing abstraction.
- Turn special-case logic into a simpler default flow with fewer exceptions.
- Replace condition chains with a typed model or explicit dispatcher.
- Split a large file into focused modules; extract helpers and pure functions.
- Move feature-specific logic behind its own abstraction; separate orchestration from business logic.
- Collapse duplicate branches into one clearer flow; delete wrappers that don't clarify the API.
- Reuse the canonical helper; move logic to the layer that owns the concept.
- Make type boundaries explicit so control flow gets simpler.
- Parallelize independent work when that also simplifies the orchestration; restructure related updates into an atomic flow.

Do not be satisfied with "maybe rename this" feedback when the real issue is structural. Do not be satisfied with a merely cleaner version of the same messy idea when a plausible path to a much simpler idea exists.

## The Finding Bar

Every structural finding carries four things:

1. **The mechanism**: why this hurts maintenance, in one or two sentences a reader can verify.
2. **Quantified impact**: line counts, branch counts, moving pieces, concept count, dollars where relevant. "This adds 3 new config surfaces and 2 shadow states for a feature that needs 1 function" beats "this feels overcomplicated."
3. **A sketched alternative**, concrete enough to evaluate: which files, which layers disappear, why behavior is preserved. A structural complaint without a sketched simpler alternative is not a finding; it's a mood.
4. **A mechanical falsifier**: `wc -l` the claimed-split files, count the branches before and after, list the layers the reframe deletes, show the duplication side by side. Structural claims get measured, never asserted.

No cosmetic nits in a thermonuclear report. A small number of high-conviction structural findings, severity-ordered, beats a long list of observations.

## Tone

Direct, serious, and demanding about quality. Never rude, and never softening a major maintainability issue into a mild suggestion. If the code makes the codebase messier, say so clearly. If the implementation missed a dramatic simplification, say that clearly too.

Phrasings that carry the right register:

- "this pushes the file past 1k lines. can we decompose first?"
- "this adds another special-case branch to an already busy flow. can it live behind its own abstraction?"
- "this works, but it makes the surrounding code more tangled. keep the behavior, restructure the implementation."
- "this looks like feature logic leaking into a shared path. can we isolate it?"
- "this abstraction isn't earning its keep. can we keep the direct flow?"
- "why the cast / optional here? can the boundary be explicit instead?"
- "this is a bespoke helper for something we already have. can we reuse the canonical one?"
- "i think there's a judo move here: reframe the state model and these branches disappear."
- "this refactor moves complexity around without deleting any. is there a simpler model?"

## Approval Bar

Do not approve merely because behavior is correct. Approval requires:

- No clear structural regression.
- No obvious missed opportunity for a dramatic simplification when such a path is visible.
- No unjustified file-size explosion.
- No spaghetti growth from special-case branching.
- No hacky or magical abstraction that makes the code harder to reason about.
- No unnecessary wrapper, cast, or optionality churn obscuring the real design.
- No architecture-boundary leak or avoidable duplication of a canonical helper.
- No unproven nerf shipped as a fix.

Presumptive blockers, waived only when the author justifies them clearly:

- The PR preserves substantial incidental complexity when a plausible judo move would delete it.
- The PR pushes a file across a size boundary that decomposition would avoid.
- The PR adds ad-hoc branching that tangles an existing flow.
- The PR solves a local problem by scattering feature checks across shared code.
- The PR adds an unnecessary abstraction, wrapper, or cast-heavy contract.
- The PR duplicates an existing helper or homes logic in the wrong layer.
- The PR restricts throughput, concurrency, or capability without naming the bottleneck.

When the bar is not met, leave explicit, actionable feedback with the sketched alternative, and push for the cleaner decomposition.
