# Deslop pattern catalog

The complete tell set, grouped by the pass that catches it. Ids are stable, so an audit can report "R4 at line 12" and a caller can name a specific tell.

Examples are drawn from software writing (docs, release notes, commit bodies, design docs, PR prose) because that is what most callers are producing. Every "after" keeps only information present in its "before". Where the fix needs a fact the draft does not have, the entry says so.

Run the passes in order: mechanical, structural, rhetorical, sentential, lexical, then the epistemic audit as the exit gate.

## 1. Mechanical (M)

Deterministic. Detect with the commands in `SKILL.md`, not by eye.

**M1. Em and en dashes.** A house rule and a density check rather than proof of authorship: published human essays out-dash frontier models (see `evidence.md`). On our surfaces the ban is absolute because the project contract bans it. On someone else's prose, treat density as a candidate and look for converging signals. Replace with a period first, a comma for a tight aside, a colon when introducing an explanation, or restructure. Catch spaced (` — `), unspaced, and double-hyphen (`a--b`) forms. One exception: a user-provided writing sample that uses them.
- Before: `The migration runs online—no downtime—but the backfill is slow.`
- After: `The migration runs online with no downtime. The backfill is slow.`

**M2. Curly quotes and apostrophes.** Straighten them. Weak on its own, since editors auto-curl, and worth fixing anyway in anything that lands near code.

**M3. Non-breaking spaces and ellipsis characters.** Copy-paste residue. Replace with a normal space and three periods.

**M4. Decorative emoji.** Remove from headings and bullets where they carry no meaning. Semantic palettes on artifacts that require them (PR bodies, review severity markers) are exempt and must survive the pass.

**M5. Mixed heading case.** Title case and sentence case are both legitimate conventions; the tell is one document mixing them, which is how an inserted section betrays a second author. Unify to the file's majority style. The scanner flags only the minority headings in a mixed file, and a proper noun can still land a heading on the wrong side, so the hit is a candidate, not a verdict.
- Before: `## Configuring The Build Cache`
- After: `## Configuring the build cache`

**M6. Trailing whitespace and double spaces after periods.** Not AI-specific. Quick to fix while you are in the file.

**M7. Uniform bullet punctuation.** Every bullet ending in a period when half are fragments, or none ending in one when all are sentences. Pick the rule the surface uses and apply it.

## 2. Structural (S)

The document's shape, judged with the text out of focus. Structural slop survives a perfect vocabulary pass, which is why it comes second.

**S1. Header inflation.** A heading over every two paragraphs. Headings are for sections a reader might jump to. Cut until each one earns its place, and let prose carry the transitions.

**S2. Bullets where the ideas connect.** Lists imply parallel, independent items. Reasoning that depends on the previous step is prose. The tell is a bulleted list whose items only make sense read in order.

**S3. Symmetry.** Every section the same length, every list the same item count, every paragraph three sentences. Real writing is lumpy, because the important part gets more room. Note the scale rule: uniformity inside a single sentence is desirable, and variation belongs across sentences and paragraphs, so these pull in opposite directions and a check that ignores scale gives the wrong answer.

**S4. Reasoning in table cells.** Tables hold enumerable facts (a flag list, a version matrix, a pass/fail grid). An argument crammed into a cell loses its connective tissue and gets skimmed.

**S5. Bold-lead bullets that restate the label.** The tell is the bold label plus colon whose sentence repeats it.
- Before: `- **Performance:** Performance improved through caching.`
- After: `- Response times dropped from 400ms to 90ms once the resolver cache landed.`
- Not a tell: a bold lead that ends in a period, names the thing, and is followed by new information (`**Schema in TypeScript.** Tables live in one file.`).
- Also not a tell, and this carve-out is mandatory rather than discretionary: a term-plus-definition list, which Microsoft's style guide explicitly prescribes ("for the term, use sentence case and bold... an exception to the general guideline"), and bold run-in heads, which the same guide recommends. Flagging either is a false positive against a published standard. The tell is restatement, not boldface.

**S6. The restating summary.** A closing section that recaps what the reader just read. Cut it. Summaries earn their place only at the top of something long, or when they carry a decision the body did not state.

**S7. Boldface spray.** Bold on every proper noun, term, or acronym. Bold at most what a skimmer must not miss. Ten bolds per screen means none of them work.

**S8. Fragmented headers.** A heading followed by a one-line warm-up that restates it before the real content starts.
- Before: `## Caching` / `Caching matters.` / `The resolver caches by content hash, so...`
- After: `## Caching` / `The resolver caches by content hash, so...`

**S9. Parallel-structure lock-in.** Every list item opening with the same part of speech, every section opening with the same construction. A little parallelism is craft. Total parallelism reads generated.

**S10. Rule of three.** Ideas forced into groups of three to sound comprehensive, at every scale: three adjectives, three list items, three sections, three clauses in a closing sentence. Count the real items and use that number, even when the real number is one. Watch for the escalating variant where each of the three gets longer than the last, which reads as a rehearsed crescendo.
- Before: `The resolver is fast, reliable, and easy to extend.`
- After: `The resolver caches by content hash, so a warm build skips it entirely.`
- Before: `We built it for speed, for safety, and for the kind of clarity that lets a new engineer read the whole pipeline in an afternoon.`
- After: `We built it for speed and for safety. A new engineer can read the whole pipeline in an afternoon.`

**S11. Fractal summaries.** Every subsection gets a summary, every section gets a summary, and the document gets one too. Keep at most the outermost, and only when the document is long enough that a reader might not finish it.

**S12. Excessive enumeration.** A listicle wearing prose clothes, usually because someone banned bullets: "The first wall is... The second wall is... The third wall is..." Either use a real list or write the argument as connected reasoning.

**S13. Wh-word headers.** "What we do differently", "Where the market is stuck", "Why this matters", "How it works" repeated as a full heading scheme. One is fine. A document whose every heading opens on a wh-word is running a template.

**S14. Paragraph over-fragmentation.** A long run of one-sentence paragraphs, each landing like a beat. A single one-line paragraph is emphasis; eighteen of them is a texture, and it is the texture readers now recognize.

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

**R14. The generic-docs test.** A paragraph that could appear verbatim in an unrelated project's documentation probably says nothing about this project, so make it specific or cut it. One exception that matters: required boilerplate. License text, safety warnings, prerequisites, legal notices, and shared operational instructions are supposed to be transplantable, and the reader still needs them. Transplantability is a prompt to check whether the paragraph is doing work, not a verdict.
- Before: `Our goal is to provide a great developer experience with sensible defaults and clear errors.`
- After: `Every error names the config key that caused it and the file it was read from.`

**R15. Reasoning leak.** Chain-of-thought residue surfacing in the finished text: "I want to be precise about my own role here", "let me reconsider that". The model's deliberation is not the document.

**R16. Premise stacking.** The evidence paragraph placed before the point it supports, so the point arrives already argued twice. Lead with the claim, then support it.

**R17. Announced counts.** "Two constraints shape the design", "for three reasons", "there are four things to know". Naming the count before the items is a planning artifact. Either the list is visible and the count is redundant, or the count is wrong by the time you finish editing.

**R18. The tie-back close.** Ending by looping to the question: "So, to answer your question: yes." The reader knows what they asked.

**R19. Invented concept labels.** An abstract problem-noun bolted onto a domain word to coin a term the field does not use: "the supervision paradox", "the acceleration trap", "workload creep". One might be a real idea. Several in one document is a generator.

**R20. Forced figurative language.** A word lifted from the prompt or the subject and repurposed as a metaphor for something unrelated. Frontier models do this readily. If the metaphor does not survive being stated literally, cut it.

## 4. Sentential (N)

Sentence-level shape.

**N1. Negative parallelism, in excess or empty.** Narrower than the folklore, because the construction itself is endorsed craft: Williams lists "not only X but Y" among his six devices for emphasis, and Strunk's 1918 rule 11 says "the antithesis of negative and positive is strong: *not charity, but simple justice*". No corpus measurement of AI over-use exists. Two tests catch the real defect. Does the negated half name a position someone actually holds, or is it a strawman pivot? And does the antithesis recur more than once every few hundred words? A yes to the second or a no to the first means cut it.
- Before: `This isn't just a cache, it's a correctness guarantee.` (nobody claimed it was only a cache)
- After: `The cache also serializes writes, so two concurrent updates cannot interleave.`
- Mechanically safe subset, closed-class: `not careful` to `careless`, `not many` to `few`, `did not remember` to `forgot`.

**N2. Tailing negation fragments.** Clipped negations bolted onto a sentence: `no guessing`, `no wasted motion`, `no config needed`, `no surprises`. Write the real clause.
- Before: `The flags come from the schema, no guessing.`
- After: `The flags are generated from the schema, so an unknown flag fails at parse time.`

**N3. Participle pseudo-analysis.** The strongest measured signature in this catalog: present participial clauses run at roughly 5.3 times the human rate (`evidence.md`), with the largest effect size of any feature tested. Watch for highlighting, underscoring, emphasizing, ensuring, reflecting, symbolizing, showcasing, fostering, contributing to, cementing, paving the way for. Delete the clause, or promote it into a real claim with a real subject.

The shape itself is legitimate. Williams treats the trailing participial clause as a free modifier that comments on the subject of the nearest verb (`Leonardo da Vinci was a man of powerful intellect, driven by an insatiable curiosity`). So the discriminator is content, not form: does the clause add a fact, or restate the significance of what was just said? A fact stays.
- Before: `The retry logic backs off exponentially, ensuring resilience and improving reliability.`
- After: `The retry logic backs off exponentially, so a downstream outage does not turn into a thundering herd.`

**N4. False ranges.** `From X to Y` where the endpoints share no scale.
- Before: `Everything from authentication to observability to schema migrations.`
- After: `It handles authentication, observability, and schema migrations.`

**N5. Copula avoidance.** Watch for: serves as, stands as, acts as, represents, boasts, features, offers, provides. Use `is` and `has`.
- Before: `The gateway serves as the entry point and features rate limiting.`
- After: `The gateway is the entry point. It rate-limits per tenant.`

**N6. Actor-hiding passive.** Narrow, and not the usual advice. GPT-4o uses agentless passive at roughly half the human rate while Llama 3 variants sit much closer to it (`evidence.md`), so the direction is model-specific and a blanket passive purge is unsupported. Fix only passive that hides an actor the reader needs in order to act.
- Before: `Requests are validated before the handler is invoked.`
- After: `The middleware validates each request before calling the handler.`
- Leave it alone when the actor is unknown, obvious, or genuinely irrelevant, which is most of the time.

**N7. Clause stacks.** If the reader has to backtrack to parse it, split it. One idea per sentence. Detail a reader can skip belongs in parentheses; detail they must parse to follow the argument belongs in its own sentence.

**N8. Manufactured punchlines.** Every sentence landing like a quotable closer. One short emphatic sentence is craft. A run of them is engineering.
- Before: `Then the scheduler changed. No more polling. No more drift. The old assumptions were gone.`
- After: `The scheduler switched from polling to a watch stream, which removed the up-to-200ms drift that the old assumptions were built on.`

**N9. Staccato fragment runs.** Three or more verbless fragments in a row inflating the tone. Rebuild at least one into a full sentence and vary the lengths around it.

**N10. Referential aliasing.** The same referent renamed every sentence: the resolver, the parser, the component, the module. Pick one name and repeat it. Countable test: per referent, count the distinct definite noun phrases in a paragraph, and three or more is the tell. (The popular explanation that a repetition penalty causes this is unmeasured, and the documented penalty signature is misspelling rather than aliasing, so treat the cause as unknown and the pattern as real.)

Repeating the term is not a failure, it is the requirement. Microsoft's style guide says "if you mean the same thing, use the same word"; Google's says to reuse the exact term including capitalization; ASD-STE100 allows "only one word for one meaning"; and Fowler named the anti-repetition instinct a fault a century ago. Two tiers: inside defined terms, API names, specs, safety text, legal text, or anything localized, repeating the exact term is mandatory. In general prose, vary connectives and sentence shapes, never the name of the thing.

**N11. Uniform sentence length.** Not visible one sentence at a time. Check the histogram: a healthy piece has genuinely short and genuinely long sentences. A tight 12-to-25-word band is machine-flat even when every word is right.

**N12. Sentence openings, and why not to vary them.** Do not diversify openings for variety. Williams is explicit that the common advice is wrong: changing subjects to make them different breaks the topic string that makes a passage cohere, and most writers change topic too often already. The real test is the topic-string test in `craft-moves.md`, which asks whether the openings name a small set of related ideas rather than whether they differ. What is worth fixing is a run of identical *structures* (four sentences each opening on the same subordinate-clause pattern), which is a template rather than a topic.

**N17. Nominalization.** The action buried in an abstract noun instead of the verb, measured at 2.1 times the human rate (`evidence.md`). Williams' five patterns, each with its own fix: as the subject of an empty verb (`The intention of the committee is to audit` to `The committee intends to audit`); after an empty verb (`conducted an investigation into` to `investigated`); two bridged by an empty verb (`Our loss in sales was a result of their expansion` to `We lost sales because they expanded`); after `there is` (`There is no need for our further study` to `We need not study this further`); and chained by prepositions (`did a review of the evolution of the brain` to `reviewed how the brain evolved`).

Four nominalizations to keep, or a pass strips the cohesion devices: a short subject referring back to the previous sentence (`These arguments all depend on...`), one replacing an awkward `the fact that`, one naming what would be the verb's object (`I accepted her request`), and one naming a concept familiar enough to act as a character (`taxation`, `revolution`).

**N18. "That" clause as subject.** `That the build failed was not surprising` at 2.6 times the human rate. Rewrite with the real subject: `Nobody was surprised that the build failed`, or better, `The build had failed twice that week, so nobody was surprised`.

**N13. False agency.** An inanimate subject taking a human verb, which is how a sentence avoids naming who acted. "A complaint becomes a fix" (the complaint did nothing; someone fixed it). Also "the decision emerges", "the market rewards", "the data tells us". Name the actor, or state the mechanism.
- Before: `The migration surfaced a schema conflict that demanded attention.`
- After: `The migration failed on a duplicate index name, and we renamed the new index.`

**N14. Distributive appositive.** A trailing fragment that distributes a metaphor across a set: "each one a thread in the tapestry", "every request a small negotiation". Delete the fragment; the sentence rarely needs it.

**N15. Phrasal coordination imbalance.** Models over-use "X, Y, and Z" lists and under-use "and then X happened" clause sequences (`evidence.md`). When a paragraph is a chain of comma-lists, rebuild one of them as a sequence of clauses with real verbs. This fixes the tricolon feel more reliably than deleting the third item.

**N16. Self-echo.** Reusing a phrase from earlier in the same document as if it were an established term or a callback, when the first use was ordinary. Either make it a defined term or vary the wording.

## 5. Lexical (L)

Last pass, least valuable. Word swaps on unfixed structure produce clean-sounding slop.

**L1. AI vocabulary.** Frequent offenders: additionally, delve, seamless, enhance, foster, garner, interplay, intricate, pivotal, showcase, tapestry, testament, underscore, vibrant, holistic, nuanced, multifaceted, comprehensive, streamline, empower, unlock, elevate, myriad, plethora, realm, landscape (abstract). Replace with the plain word, or cut the adjective. These co-occur, so a cluster is stronger evidence than any single hit, and pre-LLM baseline usage of the famous ones sits around 2 to 3%, which is the false-positive floor.

**False-positive trap:** `robust`, `leverage`, and `crucial` are widely banned and skew **human** in corpus log-odds (`evidence.md`). They are not on the list above. Neither are *just*, *really*, *actually*, *my*, or *thing*, which are human-overused and should survive the pass. Prefer the empirically derived list at [berenslab/llm-excess-vocab](https://github.com/berenslab/llm-excess-vocab) to any hand-written one, and note that close to 30% of its style markers are `-ing` forms, which makes N3 a verb-inflection fingerprint rather than a phrasing habit.

**L2. Plain-word swaps.** utilize to use, leverage to use, facilitate to help, in the event that to if, prior to to before, subsequent to to after, numerous to many, commence to start, terminate to stop, ascertain to find out, endeavor to try. The fancier synonym is rarely clearer.

**L3. Filler phrases.** in order to (to), due to the fact that (because), at this point in time (now), it is important to note that (delete), has the ability to (can), for the purpose of (to), in terms of (usually delete), it should be noted (delete). Cut clusters, not instances: isolated wordy constructions are a human signal in the Wikipedia corpus, and a document scrubbed of every one of these reads more generated, not less.

**L4. Stacked hedges.** Only the stacks. `could potentially possibly` becomes `may`, because one hedge carries the uncertainty and three signal a writer with no basis. Single hedges stay everywhere, and in scientific, legal, medical, and forecasting prose they are the honest register. Hedge direction is model-specific: GPT-4o over-uses downtoners while every Llama 3 variant avoids them (`evidence.md`), so "strip the hedges" is unsupported as a general rule. Use the six-question test in `craft-moves.md` instead of a word count.

**L5. Adverb props.** `runs quickly` becomes `is fast` or the measured number. `significantly improves` becomes the delta. An adverb holding up a weak verb means the verb is wrong. Worst offenders: significantly, effectively, essentially, basically, simply, just, actually, really, quite, very, incredibly, seamlessly, robustly.

**L6. Abstract metaphor nouns.** substrate (base), wedge (add), vector (method), locus, vantage, nexus, primitive (as a noun), harness (as a metaphor), surface (as in API surface), bedrock, scaffolding (as a metaphor), modality, paradigm, gold-plating (more than the job needs), ratchet (the mechanism's real name, or a limit that only tightens), evacuate (move out), flywheel, north star, endgame (the last phase). These read technical and usually have a plainer concrete word.

**L7. House jargon leaking outward.** Terms that are efficient between agents and opaque to a human reader: load-bearing, blast radius, nerf, falsifier gate, consumption boundary, receipts. Fine in skill files and briefs. Sweep them from anything a human reads, unless the reader shares the vocabulary.

**L8. Hyphenated-pair uniformity.** AI hyphenates compounds in every position. Keep the hyphen when the compound modifies a following noun (`a high-quality report`), drop it when it follows the noun (`the report is high quality`). Watch: third-party, data-driven, decision-making, well-known, high-quality, real-time, long-term, end-to-end, cross-functional.

**L9. Colon as a mid-sentence connector.** Colons introduce lists and explanations. Used as a dramatic hinge it does the same job as the em dash it replaced, which is why a dash purge often shows up as a colon spike.
- Before: `The tradeoff is simple: you trade memory for latency.`
- After: `The tradeoff is memory for latency.`

**L10. Superlative inflation.** `the most`, `the best`, `the only`, `never`, `always`, `every single` where the writer has not checked. Either verify the claim or scale it down to what is known.

**L11. Era-overuse, current generation.** As of Aug 2026 the Claude-generation set is: load-bearing, in service of, earns its keep, priors, backstop, pivot point, sharp insight, key insight. These are house-fluent between agents and instantly recognizable to a human reader. The `→` arrow and an unrequested collaborative "we" belong here too. Expect this list to rot within months, which is the point of dating it.

**L12. Borrowed rigor.** Economics and optimization vocabulary used as decoration: first-order concerns, the binding constraint, asymmetric upside, forcing function, the delta between, necessary but not sufficient, the operative word. Each has a precise technical meaning. Used loosely, they signal rigor without adding any. The same register prices effort like a market: a cheap check, an expensive migration, what a refactor buys you, a search that isn't paying rent. Write quick, easy, or small instead, or name the actual cost. Literal money and resource costs are not the tell.

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

**E9. Process theatre.** Claims about the work rather than the result: "double-checked", "after extensive analysis", "thoroughly reviewed", "I carefully considered". A receipt is a command and its output. Everything else is a claim about diligence, and it reads as padding at best.

**E10. Agent-loop vocabulary.** Text addressed to the orchestrator rather than the reader: "this turn", "as requested", "in this session", "point me at", "let me know if you want me to". Common when an agent's status report gets pasted into a document.

**E11. Provider and harness residue.** Mechanical, always wrong, never legitimate: `turn12search4` style citation stubs, `[cite: 7]`, `[span_4]`, lenticular brackets around a source name, dagger-digit footnote markers, and `utm_source=chatgpt` on a pasted link. The scanner treats these as hard failures.

**E12. Orphan statistics.** A suspiciously precise figure with no source: "cut deploy time by 47%", "improves accuracy by 12.4%". Precision manufactures authority. Either the number has a receipt or it does not belong.

**E13. Calibration theatre.** Confidence bands that nothing depends on: "epistemic status: moderate", "I'm about 80% confident", "I hold this loosely". Real calibration changes what the reader should do. Decorative calibration just performs rigor.

**E14. Performed candor.** Announcing honesty rather than being honest: "let me be blunt", "the strongest version of their argument is", "worth naming that", "the uncomfortable truth". Also the withheld payoff, where a sentence promises a revelation and delivers an ordinary point: "where the real work happens", "the part nobody tells you".

**E15. Clean slop, the second-order tell.** Prose that passes every check above and is still recognizable, because the aphoristic one-liner closing each paragraph and the clipped fragment pairs have themselves become a uniform. Any individual instance is fine. As a texture across a document, it is the current signature of text that has been through a deslop pass. The only fix is variation the writer actually chose.

## Swap traps

Each row is a fix that looks clean and reads worse, because removing a tell relocates it.

| You removed           | The trap                                                    | Do this instead                                                       |
| --------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------- |
| An em dash            | Parenthesis spray, colon as connector, or a `--` substitute  | End the sentence. Use a comma for a tight aside                        |
| Rule of three         | Rule of four, or three items with new rhythm                | Count the real items, then rebuild the list as clauses                 |
| Uniform rhythm        | Mechanical short-long-short alternation                     | Vary in clusters, since human sentence runs are persistent (N11)       |
| Bold-lead bullets     | A heading per former bullet                                 | Prose, or a bold lead ending in a period followed by new information   |
| An AI vocabulary word | A same-register synonym ("crucial" to "vital")              | The plain word, or cut the adjective                                   |
| Passive voice         | A fake actor ("the system", "the framework")                | The real actor, or leave the passive alone                             |
| Hedging               | A flat overclaim                                            | The calibrated claim plus its basis                                    |
| Synonym cycling fix   | Renaming the thing to avoid repetition                      | Repeat the term. Vary the connective instead (N10)                     |
| A generic conclusion  | A different generic conclusion ("In short", "Ultimately")    | Stop at the last concrete fact                                         |
| Sycophancy            | Clipped coldness                                            | A neutral, direct answer                                               |
| Staccato drama        | One long clause-stacked sentence                            | Mixed rhythm across the paragraph                                      |
| Decorative emoji      | Caps or bold as replacement decoration                      | Nothing. The sentence carries itself                                   |
| "Delve into"          | "Dive into", "explore"                                      | The verb for what happened: read, measured, tested, benchmarked        |

## Signal families

Convergence counts by family, not by id, because several ids describe one underlying habit. Two hits inside a family count as one signal.

| Family                  | Ids                          |
| ----------------------- | ---------------------------- |
| Texture                 | S14, N8, N9, E15             |
| Coordination and cadence | S3, S10, N11, N15            |
| Inflation               | R1, R2, R9, E7               |
| Evasion                 | R3, N6, N13, E3              |
| Ceremony                | R5, R17, R18, E9, E13, E14   |
| Jargon                  | L6, L7, L11, L12             |
| Abstraction             | N17, N18, R13, L1            |

## What not to flag

Detailed in `SKILL.md` under the preservation contract. The short version: single instances prove nothing, technical precision is not slop, honest hedges stay, and quoted or code text is never edited. Look for clusters.

## Sources

The pattern set synthesizes [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (WikiProject AI Cleanup), the [blader/humanizer](https://github.com/blader/humanizer) skill, Cursor's [pstack `unslop`](https://github.com/cursor/plugins/blob/main/pstack/skills/unslop/SKILL.md) skill, and house conventions already encoded in `super-good-pr` and `hyper-pr-review`. Examples here are original.
