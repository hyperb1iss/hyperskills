# Deslop pattern catalog

The complete tell set, grouped by the pass that catches it. Ids are stable, so an audit can report "R4 at line 12" and a caller can name a specific tell.

Examples are drawn from software writing (docs, release notes, commit bodies, design docs, PR prose) because that is what most callers are producing. Every "after" keeps only information present in its "before". Where the fix needs a fact the draft does not have, the entry says so.

Run the passes in order: mechanical, structural, rhetorical, sentential, lexical, then the epistemic audit as the exit gate.

## 1. Mechanical (M)

Deterministic. Detect with the commands in `SKILL.md`, not by eye.

**M1. Em and en dashes.** The single most reliable tell. Replace with a period first, a comma for a tight aside, a colon when introducing an explanation, or restructure. Catch spaced (` — `) and double-hyphen (` -- `) forms too. One exception: a user-provided writing sample that uses them.
- Before: `The migration runs online—no downtime—but the backfill is slow.`
- After: `The migration runs online with no downtime. The backfill is slow.`

**M2. Curly quotes and apostrophes.** Straighten them. Weak on its own, since editors auto-curl, and worth fixing anyway in anything that lands near code.

**M3. Non-breaking spaces and ellipsis characters.** Copy-paste residue. Replace with a normal space and three periods.

**M4. Decorative emoji.** Remove from headings and bullets where they carry no meaning. Semantic palettes on artifacts that require them (PR bodies, review severity markers) are exempt and must survive the pass.

**M5. Title case headings.** Sentence case, always. Proper nouns keep their capitals, so the mechanical hit is a candidate, not a verdict.
- Before: `## Configuring The Build Cache`
- After: `## Configuring the build cache`

**M6. Trailing whitespace and double spaces after periods.** Not AI-specific. Cheap to fix while you are in the file.

**M7. Uniform bullet punctuation.** Every bullet ending in a period when half are fragments, or none ending in one when all are sentences. Pick the rule the surface uses and apply it.

## 2. Structural (S)

The document's shape, judged with the text out of focus. Structural slop survives a perfect vocabulary pass, which is why it comes second.

**S1. Header inflation.** A heading over every two paragraphs. Headings are for sections a reader might jump to. Cut until each one earns its place, and let prose carry the transitions.

**S2. Bullets where the ideas connect.** Lists imply parallel, independent items. Reasoning that depends on the previous step is prose. The tell is a bulleted list whose items only make sense read in order.

**S3. Symmetry.** Every section the same length, every list the same item count, every paragraph three sentences. Real writing is lumpy: the important part is longer. Uniform proportion is the machine's signature.

**S4. Reasoning in table cells.** Tables hold enumerable facts (a flag list, a version matrix, a pass/fail grid). An argument crammed into a cell loses its connective tissue and gets skimmed.

**S5. Bold-lead bullets that restate the label.** The tell is the bold label plus colon whose sentence repeats it.
- Before: `- **Performance:** Performance improved through caching.`
- After: `- Response times dropped from 400ms to 90ms once the resolver cache landed.`
- Not a tell: a bold lead that ends in a period, names the thing, and is followed by new information (`**Schema in TypeScript.** Tables live in one file.`).

**S6. The restating summary.** A closing section that recaps what the reader just read. Cut it. Summaries earn their place only at the top of something long, or when they carry a decision the body did not state.

**S7. Boldface spray.** Bold on every proper noun, term, or acronym. Bold at most what a skimmer must not miss. Ten bolds per screen means none of them work.

**S8. Fragmented headers.** A heading followed by a one-line warm-up that restates it before the real content starts.
- Before: `## Caching` / `Caching matters.` / `The resolver caches by content hash, so...`
- After: `## Caching` / `The resolver caches by content hash, so...`

**S9. Parallel-structure lock-in.** Every list item opening with the same part of speech, every section opening with the same construction. A little parallelism is craft. Total parallelism reads generated.

## 3. Rhetorical (R)

The argument's shape. These are the tells readers name when they say something "sounds like ChatGPT" but cannot point at a word.

**R1. Inflated significance.** Watch for: stands as, serves as, is a testament to, marks a pivotal moment, underscores the importance of, reflects a broader, setting the stage for, represents a shift, evolving landscape, indelible mark, deeply rooted. Say what happened and stop.
- Before: `The 2.0 release marks a pivotal moment in the project's evolution, underscoring its commitment to developer experience.`
- After: `Version 2.0 replaces the config loader and cuts cold start from 900ms to 120ms.`

**R2. Promotional puffery.** Watch for: boasts, vibrant, rich (figurative), seamless, powerful, robust, elegant, blazing fast, best-in-class, groundbreaking, world-class, effortless. Neutral description, or a number.
- Before: `A powerful, seamless CLI that makes deployment effortless.`
- After: `A CLI that deploys from a single config file. One command, no cluster access needed.`

**R3. Vague attribution.** Watch for: experts believe, industry reports suggest, it is widely regarded, many developers find, studies show, best practice dictates. Name the source, or cut the claim. Never decorate a guess into a citation.
- Before: `Best practice dictates that migrations run in a transaction.`
- After: `Postgres runs DDL transactionally, so a failed migration rolls back cleanly.` (Keep the mechanism you can verify, drop the appeal to authority.)

**R4. Notability name-dropping.** Listing logos, outlets, or adopters without saying what any of them did. Keep one with real context, drop the list.

**R5. Signposting and announcements.** Watch for: let's dive in, let's explore, let's break this down, here's what you need to know, in this section we will, without further ado, first, let's understand. Do the thing instead of announcing it.
- Before: `Let's dive into how the scheduler works. Here's what you need to know.`
- After: `The scheduler polls the queue every 200ms and leases each job for 30 seconds.`

**R6. Generic upbeat close.** Watch for: the future looks bright, exciting times ahead, a step in the right direction, the possibilities are endless, we can't wait to see what you build. Cut the paragraph and end on the last concrete fact.

**R7. Challenges-and-future-prospects.** The formulaic "Despite these challenges, X continues to thrive" section, or a "Limitations" block written to look thorough rather than to inform. Name specific limits with specific consequences, or drop the section.

**R8. Persuasive authority tropes.** Watch for: the real question is, at its core, fundamentally, what really matters, the deeper issue, the heart of the matter, make no mistake. These pretend to cut through noise before restating an ordinary point.
- Before: `At its core, what really matters is whether the cache invalidates correctly.`
- After: `The open question is whether the cache invalidates on a partial write.`

**R9. Aphorism formulas.** Watch for: X is the Y of Z, X becomes a trap, X is not a tool but a Y, the language of, the currency of, the architecture of. Replace the epigram with the concrete claim it is gesturing at.
- Before: `Observability is the currency of trust in distributed systems.`
- After: `Without per-request tracing, a p99 regression takes days to localize instead of minutes.`

**R10. Conversational rhetorical openers.** Watch for a standalone theatrical pause before an ordinary point: `Honestly?`, `Look.`, `Here's the thing.`, `The thing is.`, `Let's be real.` A person being candid usually just says the thing. Mid-sentence "honestly" or "look" in casual writing is not a tell.

**R11. Rhetorical question as transition.** Watch for: `The result?`, `Why does this matter?`, `So what changed?`, `The catch?` One is a style choice; a document with four is a template.
- Before: `The result? Builds got 3x faster.`
- After: `Builds got 3x faster.`

**R12. False balance.** Neutrally listing pros and cons on a question the writer has actually answered, so the reader cannot tell what the recommendation is. On any surface where a recommendation belongs, make it.

**R13. Feeling instead of mechanism.** Prose that describes how something feels rather than what it does. Ask what the sentence tells the reader to do or know, then write that.
- Before: `The API stays out of your way and keeps the database close at hand.`
- After: `Queries run in-process against a local file, so there is no connection string and no network hop.`

**R14. The generic-docs test.** Any paragraph that could appear verbatim in an unrelated project's documentation says nothing about this project. Cut it or make it specific.
- Before: `Our goal is to provide a great developer experience with sensible defaults and clear errors.`
- After: `Every error names the config key that caused it and the file it was read from.`

## 4. Sentential (N)

Sentence-level shape.

**N1. Negative parallelism.** Watch for: not just X but Y, it's not X, it's Y, not only, more than just. State the point directly.
- Before: `This isn't just a cache, it's a correctness guarantee.`
- After: `The cache also serializes writes, so two concurrent updates cannot interleave.`

**N2. Tailing negation fragments.** Clipped negations bolted onto a sentence: `no guessing`, `no wasted motion`, `no config needed`, `no surprises`. Write the real clause.
- Before: `The flags come from the schema, no guessing.`
- After: `The flags are generated from the schema, so an unknown flag fails at parse time.`

**N3. Participle pseudo-analysis.** A present participle clause bolted on to fake depth: highlighting, underscoring, emphasizing, ensuring, reflecting, symbolizing, showcasing, fostering, contributing to, cementing, paving the way for. Delete it, or promote it into a real claim with a real subject.
- Before: `The retry logic backs off exponentially, ensuring resilience and improving reliability.`
- After: `The retry logic backs off exponentially, so a downstream outage does not turn into a thundering herd.`

**N4. False ranges.** `From X to Y` where the endpoints share no scale.
- Before: `Everything from authentication to observability to schema migrations.`
- After: `It handles authentication, observability, and schema migrations.`

**N5. Copula avoidance.** Watch for: serves as, stands as, acts as, represents, boasts, features, offers, provides. Use `is` and `has`.
- Before: `The gateway serves as the entry point and features rate limiting.`
- After: `The gateway is the entry point. It rate-limits per tenant.`

**N6. Actor-hiding passive.** Catch `is/are/was/were + past participle` and name the actor when the actor matters.
- Before: `Requests are validated before the handler is invoked.`
- After: `The middleware validates each request before calling the handler.`
- Keep the passive when the actor is unknown, obvious, or genuinely irrelevant.

**N7. Clause stacks.** If the reader has to backtrack to parse it, split it. One idea per sentence. Detail a reader can skip belongs in parentheses; detail they must parse to follow the argument belongs in its own sentence.

**N8. Manufactured punchlines.** Every sentence landing like a quotable closer. One short emphatic sentence is craft. A run of them is engineering.
- Before: `Then the scheduler changed. No more polling. No more drift. The old assumptions were gone.`
- After: `The scheduler switched from polling to a watch stream, which removed the up-to-200ms drift that the old assumptions were built on.`

**N9. Staccato fragment runs.** Three or more verbless fragments in a row inflating the tone. Rebuild at least one into a full sentence and vary the lengths around it.

**N10. Synonym cycling.** Repetition penalty artifact: the same referent renamed every sentence (the resolver, the parser, the component, the module). Pick one name and repeat it. Consistent terminology is a feature in technical writing.

**N11. Uniform sentence length.** Not visible one sentence at a time. Check the histogram: a healthy piece has genuinely short and genuinely long sentences. A tight 12-to-25-word band is machine-flat even when every word is right.

**N12. Sentence-opening monotony.** Six sentences in a row opening with the subject, or four opening with a subordinate clause. Vary the entry point.

## 5. Lexical (L)

Last pass, least valuable. Word swaps on unfixed structure produce clean-sounding slop.

**L1. AI vocabulary.** Highest-frequency offenders: additionally, crucial, delve, robust, seamless, leverage, utilize, enhance, foster, garner, interplay, intricate, pivotal, showcase, tapestry, testament, underscore, vibrant, holistic, nuanced, multifaceted, comprehensive, streamline, empower, unlock, elevate, myriad, plethora, realm, landscape (abstract). Replace with the plain word, or cut the adjective. These co-occur, so a cluster is stronger evidence than any single hit.

**L2. Plain-word swaps.** utilize to use, leverage to use, facilitate to help, in the event that to if, prior to to before, subsequent to to after, numerous to many, commence to start, terminate to stop, ascertain to find out, endeavor to try. The fancier synonym is rarely clearer.

**L3. Filler phrases.** in order to (to), due to the fact that (because), at this point in time (now), it is important to note that (delete), has the ability to (can), for the purpose of (to), in terms of (usually delete), it should be noted (delete).

**L4. Stacked hedges.** `could potentially possibly` becomes `may`. One hedge carries the uncertainty; three signal a writer with no basis. Single honest hedges in scientific, legal, medical, and forecasting prose stay.

**L5. Adverb props.** `runs quickly` becomes `is fast` or the measured number. `significantly improves` becomes the delta. An adverb holding up a weak verb means the verb is wrong. Worst offenders: significantly, effectively, essentially, basically, simply, just, actually, really, quite, very, incredibly, seamlessly, robustly.

**L6. Abstract metaphor nouns.** substrate (base), wedge (add), vector (method), locus, vantage, nexus, primitive (as a noun), harness (as a metaphor), surface (as in API surface), bedrock, scaffolding (as a metaphor), modality, paradigm, gold-plating (more than the job needs), ratchet, flywheel, north star, endgame. These read technical and usually have a plainer concrete word.

**L7. House jargon leaking outward.** Terms that are efficient between agents and opaque to a human reader: load-bearing, blast radius, nerf, falsifier gate, consumption boundary, receipts. Fine in skill files and briefs. Sweep them from anything a human reads, unless the reader shares the vocabulary.

**L8. Hyphenated-pair uniformity.** AI hyphenates compounds in every position. Keep the hyphen when the compound modifies a following noun (`a high-quality report`), drop it when it follows the noun (`the report is high quality`). Watch: third-party, data-driven, decision-making, well-known, high-quality, real-time, long-term, end-to-end, cross-functional.

**L9. Colon as a mid-sentence connector.** Colons introduce lists and explanations. As a dramatic hinge, a colon is an em dash wearing a hat.
- Before: `The tradeoff is simple: you trade memory for latency.`
- After: `The tradeoff is memory for latency.`

**L10. Superlative inflation.** `the most`, `the best`, `the only`, `never`, `always`, `every single` where the writer has not checked. Either verify the claim or scale it down to what is known.

## 6. Epistemic (E)

Truth-level tells. These are the ones that make text untrustworthy rather than merely unpleasant, and they are checked at the exit gate.

**E1. Fabricated specificity.** The deslopper's own worst failure: replacing a vague claim with an invented concrete one. `Experts believe it improves performance` becoming `Benchmarks show a 40% improvement` is a defect even though it reads better. No name, number, date, version, quote, or citation may enter the rewrite unless the source or the user supplied it. Ask for the fact, or write the plain version without it. (Fiction is exempt. Invented detail is the job there.)

**E2. Knowledge-cutoff disclaimers.** `As of my last training update`, `While specific details are limited`, `based on available information`. Say what is not known, or cut the sentence.

**E3. Speculative gap-filling.** When a model cannot find a fact, it writes a paragraph about not finding one and then invents plausible filler. Watch for: `likely`, `it is believed`, `presumably`, `maintains a low profile`, `may have been`. State the gap or omit it.

**E4. Chatbot artifacts.** `I hope this helps`, `Let me know if`, `Of course!`, `Certainly!`, `Great question`, `Would you like me to`, `Here is a`, `Found the smoking gun`. Conversation residue pasted into a document.

**E5. Sycophancy.** `You're absolutely right`, `That's an excellent point`, `Great catch`. Answer directly. The fix is neutral, not cold.

**E6. Diff-anchored writing.** Documentation or comments narrating a change instead of describing the thing as it is. Correct in changelogs, release notes, and migration guides. A tell everywhere else.
- Before: `This function replaces the old loop, which was O(n²).`
- After: `This function looks up by hash, so it runs in O(1) per item.`

**E7. Unfalsifiable claims.** `Designed for scale`, `built with security in mind`, `production-ready`, `enterprise-grade`, `battle-tested`. Nothing in these can be checked. Replace with the property and its evidence, or cut them.

**E8. Confident restatement of the prompt.** Text that answers by paraphrasing the question with more words. Common in generated docs sections that mirror their own heading. If a paragraph adds no information the heading did not, cut the paragraph.

## What not to flag

Detailed in `SKILL.md` under the preservation contract. The short version: single instances prove nothing, technical precision is not slop, honest hedges stay, and quoted or code text is never edited. Look for clusters.

## Sources

The pattern set synthesizes [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (WikiProject AI Cleanup), the [blader/humanizer](https://github.com/blader/humanizer) skill, Cursor's [pstack `unslop`](https://github.com/cursor/plugins/blob/main/pstack/skills/unslop/SKILL.md) skill, and house conventions already encoded in `super-good-pr` and `hyper-pr-review`. Examples here are original.
