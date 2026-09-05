# Deslop pattern catalog

Stable IDs let an audit name a concrete defect without repeating a long rule. These are diagnostic candidates, not proof of authorship. Use only the entries relevant to the artifact. A single clear defect can warrant an edit; several familiar constructions can all be appropriate.

Examples below preserve the stated facts. A replacement that needs a new mechanism, number, or actor must draw it from supplied evidence. When removing vague praise leaves no useful information, flag the missing content instead of inventing specificity.

## Mechanical (M)

| ID  | Candidate                                      | Decision                                                                                   |
| --- | ---------------------------------------------- | ------------------------------------------------------------------------------------------ |
| M1  | Em, en, or double-hyphen dash                  | Enforce the house ban where applicable; otherwise follow the author's requested typography |
| M2  | Curly quote or apostrophe variant              | Normalize under house rules; preserve meaningful language-specific typography elsewhere    |
| M3  | Non-breaking space or ellipsis glyph           | Check intended typography; these can be legitimate in published and localized text         |
| M4  | Decorative emoji                               | Remove empty decoration; preserve semantic palettes and the author's intended voice        |
| M5  | Mixed heading case                             | Follow the document's convention; proper nouns can fool the scanner                        |
| M6  | Trailing whitespace or doubled sentence spaces | Fix when formatting conventions require it; preserve intentional Markdown breaks           |
| M7  | Inconsistent bullet punctuation                | Apply punctuation appropriate to fragments versus full sentences                           |

The scanner masks protected regions and reports candidates; it does not authorize changing a quote, link, identifier, or code sample. See its documented heuristic limits in `../SKILL.md`.

## Structural (S)

| ID  | Candidate                                 | Decision                                                                                      |
| --- | ----------------------------------------- | --------------------------------------------------------------------------------------------- |
| S1  | Header inflation                          | Keep headings that support navigation; remove labels that merely fragment a short explanation |
| S2  | Bullets where ideas depend on one another | Use prose for an argument, numbered steps for a sequence, bullets for parallel items          |
| S3  | Forced symmetry                           | Let the important sections take more room; do not manufacture asymmetry                       |
| S4  | Reasoning buried in table cells           | Move a sustained explanation to prose; retain tables that clarify decisions or comparisons    |
| S5  | Bold lead restating its label             | Remove the repetition, not useful term-and-definition formatting                              |
| S6  | Restating summary                         | Keep a summary when it supports navigation, recall, or a decision; cut a redundant close      |
| S7  | Boldface spray                            | Emphasize only what a skimmer needs to find                                                   |
| S8  | Heading followed by a redundant warm-up   | Start the section's explanation immediately                                                   |
| S9  | Parallel-structure lock-in                | Retain helpful parallelism; edit only when the pattern distorts the content                   |
| S10 | Forced groups of three                    | Keep the actual items, however many; a three-item list is not itself a defect                 |
| S11 | Fractal summaries                         | Remove repeated recaps that add no navigation or decision value                               |
| S12 | Enumeration disguised as prose            | Use a list when items need counting; use connected prose for reasoning                        |
| S13 | Repeated wh-word heading scheme           | Check whether headings name useful reader questions; a coherent template can be appropriate   |
| S14 | Paragraph over-fragmentation              | Join fragments that need shared context; retain deliberate emphasis                           |

A safe repetition fix:

- Before: `- **Performance:** Performance improved through caching.`
- After: `- Caching improved performance.`

A latency delta would require measurements. An edit must not turn that sentence into an invented benchmark.

## Rhetorical (R)

| ID  | Candidate                             | Decision                                                                           |
| --- | ------------------------------------- | ---------------------------------------------------------------------------------- |
| R1  | Inflated significance                 | State the actual change and its supported consequence                              |
| R2  | Promotional puffery                   | Follow the brief; factual claims still need evidence                               |
| R3  | Vague attribution                     | Resolve "studies show" or "best practice" to support, qualify it, or remove it     |
| R4  | Notability name-dropping              | Explain relevant adoption or omit the logo list                                    |
| R5  | Announcing the explanation            | Begin the explanation unless the transition helps navigation                       |
| R6  | Generic upbeat close                  | End on a useful fact, decision, or next action                                     |
| R7  | Formulaic challenges/future section   | Name real limitations and consequences; omit decorative thoroughness               |
| R8  | Persuasive authority trope            | Replace "the real question" or "at its core" with the actual claim                 |
| R9  | Aphorism substituting for explanation | State the supported mechanism; retain an author's intentional metaphor when useful |
| R10 | Theatrical conversational opener      | Remove a staged pause that adds nothing; preserve natural conversational voice     |
| R11 | Rhetorical question as transition     | Keep a real reader question; remove a repeated manufactured reveal                 |
| R12 | False balance                         | State the supported recommendation when the task calls for one                     |
| R13 | Feeling in place of mechanism         | Explain what the system does, using available facts                                |
| R14 | Generic project copy                  | Add supported project-specific information or cut; required boilerplate is exempt  |
| R15 | Deliberation residue                  | Keep the conclusion and useful explanation; remove internal self-instructions      |
| R16 | Premise stacking                      | Lead with the claim when earlier evidence otherwise leaves the reader guessing     |
| R17 | Announced counts                      | Keep a count when it helps a sequence; remove one that only repeats a visible list |
| R18 | Tie-back close                        | Avoid re-answering a question already answered unless clarification is needed      |
| R19 | Invented concept labels               | Define a useful new concept or use the established term; avoid multiplying labels  |
| R20 | Forced metaphor                       | Keep imagery that serves the author's purpose; remove decorative domain-word reuse |

A vague draft such as `A powerful, seamless CLI that makes deployment effortless` supports the limited rewrite `A deployment CLI`. A single-command workflow or a claim that cluster access is unnecessary needs additional source evidence.

## Sentential (N)

| ID  | Candidate                                | Decision                                                                                           |
| --- | ---------------------------------------- | -------------------------------------------------------------------------------------------------- |
| N1  | Empty or repetitive negative parallelism | Keep real distinctions; remove imaginary opposing positions; honor a stricter house rule           |
| N2  | Tailing negation fragment                | Write the actual clause when the fragment leaves the meaning unclear                               |
| N3  | Participle pseudo-analysis               | Keep a tail that adds a fact; delete one that only restates significance                           |
| N4  | False range                              | Replace endpoints without a shared scale with a direct list                                        |
| N5  | Copula avoidance                         | Prefer `is` or `has` when `serves as` adds no meaning                                              |
| N6  | Actor-hiding passive                     | Name a known actor when the reader needs it; keep passive when appropriate                         |
| N7  | Clause stack                             | Separate claims that force backtracking without losing their relationship                          |
| N8  | Manufactured punchlines                  | Restore the explanation when every line performs a reveal                                          |
| N9  | Staccato fragment run                    | Connect ideas that need a shared sentence or paragraph                                             |
| N10 | Referential aliasing                     | Repeat the defined term; synonyms can accidentally invent a second component                       |
| N11 | Uniform sentence length                  | Inspect readability in context; do not enforce a histogram or add arbitrary variation              |
| N12 | Repetitive openings                      | Preserve topic continuity; change only a construction that obstructs the paragraph                 |
| N13 | False agency                             | Name the actual actor or mechanism when personification obscures responsibility                    |
| N14 | Distributive appositive                  | Remove a trailing metaphor that contributes nothing to the claim                                   |
| N15 | Phrasal coordination imbalance           | Convert a crowded list to clauses when the relations need explaining                               |
| N16 | Self-echo                                | Keep established terminology; remove an accidental repeated flourish                               |
| N17 | Nominalization                           | Put the action in the verb when it is buried; retain names of concepts and back-references         |
| N18 | `That` clause as subject                 | Reframe only if it improves readability without adding an actor or cause                           |
| N19 | Stacked rhetorical frames                | Separate competing claims when contrast, consequence, reframing, and negation overload a paragraph |

Useful repairs with no added facts:

- Before: `The gateway serves as the entry point and features rate limiting.`
- After: `The gateway is the entry point and rate-limits requests.`
- Before: `The committee conducted an investigation into the outage.`
- After: `The committee investigated the outage.`
- Before: `That the build failed was not surprising.`
- After: `The build's failure was unsurprising.`
- Before: `The retry logic backs off exponentially, ensuring resilience and improving reliability.`
- After: `The retry logic backs off exponentially.`

The retry edit cannot claim thundering-herd prevention without evidence about jitter and the actual workload. The build edit cannot invent earlier failures as a reason nobody was surprised.

The scanner's N19 trigger uses three frame families to locate candidates. The threshold is a convenience, not a model signature or a measured quality boundary. A paragraph can legitimately contain every listed frame. Check what the reader cannot follow before editing it.

## Lexical (L)

| ID  | Candidate                             | Decision                                                                                             |
| --- | ------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| L1  | Familiar AI-associated vocabulary     | Judge function and precision; no word establishes authorship                                         |
| L2  | Needlessly elaborate synonym          | Use the familiar word when its meaning is equivalent                                                 |
| L3  | Filler phrase                         | Remove words that add no meaning; preserve emphasis and author voice where useful                    |
| L4  | Stacked hedges                        | Combine redundant qualifiers without changing certainty; retain calibrated uncertainty               |
| L5  | Adverb propping up an imprecise claim | State a supported property or measurement; do not invent a stronger verb                             |
| L6  | Abstract metaphor noun                | Use the domain term when precise; avoid replacing real technical meanings blindly                    |
| L7  | House jargon leaking outward          | Write for the audience; terms useful between agents may confuse a public reader                      |
| L8  | Hyphenated-pair uniformity            | Follow grammar, defined terms, and house style; do not remove a hyphen that disambiguates a modifier |
| L9  | Colon as a dramatic connector         | Use a colon for its grammatical purpose, not as an automatic replacement for every dash              |
| L10 | Superlative inflation                 | Verify `only`, `always`, and `best`, or limit the claim to the evidence                              |
| L11 | Generation-associated mannerism       | Treat as a dated observation, not an enduring model fingerprint                                      |
| L12 | Borrowed rigor                        | Use economics or optimization terms only when their precise meaning applies                          |

Words such as `robust`, `leverage`, `just`, and `actually` can be appropriate or empty in context. Corpus rates cannot settle an individual edit. Names such as `API surface`, `vector`, and `primitive` often have exact technical meanings. Do not flatten them into misleading synonyms.

## Epistemic (E)

| ID  | Candidate                           | Decision                                                                                                                |
| --- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| E1  | Fabricated specificity              | Add no factual detail without source support; invention belongs only to an authorized creative brief                    |
| E2  | Knowledge-cutoff disclaimer         | State the relevant information gap and verification status                                                              |
| E3  | Speculative gap-filling             | Distinguish a useful labeled hypothesis from unsupported factual filler                                                 |
| E4  | Chatbot artifact                    | Remove interactive offers or greetings pasted into a standalone artifact                                                |
| E5  | Sycophancy                          | Credit a real catch when justified; do not reflexively agree or praise                                                  |
| E6  | Diff-anchored documentation         | Describe current behavior in references/comments; change narratives belong in release notes, PRs, or migration guidance |
| E7  | Unfalsifiable claim                 | Name a testable property and evidence, or remove the claim                                                              |
| E8  | Confident restatement of the prompt | Add the supported answer or remove the repetition                                                                       |
| E9  | Process theatre                     | Give relevant evidence instead of an assertion of diligence                                                             |
| E10 | Agent-loop vocabulary               | Write for the reader of the artifact, not the supervising agent                                                         |
| E11 | Provider or harness residue         | Repair unresolved citation tokens; inspect footnotes, tracking parameters, and language-specific punctuation in context |
| E12 | Orphan statistic                    | Cite the actual result or remove unsupported precision                                                                  |
| E13 | Calibration theatre                 | Keep uncertainty that affects interpretation; omit ornamental confidence scores                                         |
| E14 | Performed candor                    | State the fact without announcing honesty                                                                               |
| E15 | Formulaic cleanup                   | Check for meaning lost to clipped fragments or canned closes; do not chase an authorship impression                     |

## Swap traps

| Removed           | Risk                                      | Safer check                          |
| ----------------- | ----------------------------------------- | ------------------------------------ |
| Dash              | Parenthesis or colon replacing every dash | Choose punctuation per sentence      |
| Passive           | Invented actor                            | Keep passive if the actor is unknown |
| Hedge             | Overclaim                                 | Compare truth conditions             |
| Vague praise      | Fabricated metric                         | Require source evidence              |
| Repeated term     | Ambiguous synonym                         | Preserve defined terms               |
| Long sentence     | Fragmented explanation                    | Read the whole paragraph             |
| Redundant summary | Loss of procedure reminder                | Check the reader's point of use      |

## Evidence and sources

Checked research and its limits live in `evidence.md`; practical repairs live in `craft-moves.md`. The catalog includes house conventions and editorial observations. Stable IDs support communication, not scoring. Do not count weak markers into a claim about authorship, and do not hide a clear factual or clarity defect because it has only one ID.
