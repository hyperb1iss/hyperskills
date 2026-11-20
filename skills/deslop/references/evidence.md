# Evidence and limits

Sources checked 2026-09-04, with the sections from "Density and the reader without context" through "Reader approval" added on 2026-11-20. Distinguish a measured result in a named corpus from a useful editing heuristic. Neither is an authorship verdict, and neither establishes a rule for Astra or another model absent a relevant evaluation.

## Grammatical variation

[Reinhart et al., Do LLMs write like humans?](https://arxiv.org/html/2410.16107v2) compares GPT-4o and Llama 3 variants with human writing across several registers. The paper reports that instruction-tuned models use present participial clauses and nominalizations more often in these corpora; passive usage differs across models. The results concern those models, prompts, and corpora.

Editing implication: inspect noun-heavy sentences and empty participial tails, but retain constructions that carry useful meaning. A group frequency difference cannot determine whether a particular sentence needs editing. A passive can place the right topic first; a hedge can preserve the truth of a claim. The study does not validate blanket bans or an optimal sequence of editing passes.

## Narrative structure

[StoryScope, version 6](https://arxiv.org/abs/2604.03136v6) studies a parallel fiction corpus of 61,608 stories from 10,272 prompts. Its abstract reports 93.2% macro-F1 for human-versus-AI classification using narrative features alone.

Editing implication: repetitive plot or argument structure deserves attention beyond word choice. Applying that insight to technical prose is a design inference, not a result from this study. The score is not a writing-quality score, and the paper does not establish that technical documents with regular structure are defective.

## Vocabulary shifts

[Kobak et al., Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016v5) analyzes more than 15 million PubMed abstracts and finds post-LLM shifts in style-word frequency. Its aggregate estimate does not identify the author of an individual abstract or define a universal forbidden-word list.

Editing implication: date corpus-derived suggestions and check the domain before reuse. Do not treat a word common in biomedical abstracts as defective in every context. A frequency spike is not evidence that the word makes a particular sentence worse.

## Model-specific pattern suppression

[Paech et al., Antislop](https://arxiv.org/abs/2510.15061v2) profiles repetitive patterns and evaluates sampler and fine-tuning interventions. The abstract reports different quality effects for its interventions, including degradation from some suppression methods.

Editing implication: suppressing strings and improving a reader's experience are different objectives. Training and decoding results do not prove that a prose editing prompt will preserve meaning, that a banned-word list transfers across models, or that the scanner's thresholds are calibrated.

## False positives

[Liang et al., GPT detectors are biased against non-native English writers](https://arxiv.org/abs/2304.02819) reports disproportionate misclassification of non-native English writing by evaluated detectors.

Editing implication: do not emit an authorship verdict or treat detector scores as quality evidence. Describe a reader-facing defect directly. Avoid claims about other populations or current detectors that the study did not measure.

## Density and the reader without context

Anthropic's prompting guides for its Fable 5.1 and Fable 5.2 models (read 2026-11-20, undated pages: [5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1), [5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2)) describe a change of direction. The 5.1 guide says the model's writing "has few stock phrases and little unexplained jargon" while its prose is "denser" than its predecessor's: "sentences run longer and there are fewer paragraph breaks." It also says earlier models overused bullets and bold, that this one under-formats, and that anti-formatting rules written for older models should be removed. The 5.2 guide recommends telling the model to "write for an intelligent but low-context reader" who "has not seen your tool calls, your reasoning or the files you opened", with no "term or abbreviation that you made up during the work". Anthropic reports that this text "made final reports less dense and reduced the number of semicolons." The same guide warns that a hard style limit such as a 20-word sentence cap "can make its prose choppy." These are a vendor's internal observations about two models, with no effect sizes.

[Shaib et al., Measuring AI "Slop" in Text](https://arxiv.org/html/2509.19163v2) (version 2, 2026-01-24) had professional editors mark spans in news and question-answering text. In the combined data the strongest predictors of an editor's overall verdict were relevance, density, and tone. The editors agreed poorly with one another on that verdict (Cohen's kappa from -0.15 to 0.29), and the page's text and tables disagree on some figures. The generated text came from 2024-era models.

Local observation, 2026-11-20: the scanner as it then stood reported no findings on the ten most recently merged pull request descriptions in this repository (4,103 words). One of them had four sentences of 45 words or more, the longest at 64, and 11.6 semicolons per 1,000 words. The scanner had no measure that pointed at any of this.

Editing implication: check for packing as well as padding, and read as a person who lacks the writer's context. The strongest predictors of a poor verdict are properties no pattern match can see. The context family in the catalog and the density diagnostics in the scanner are responses to these observations. Neither has been validated against reader outcomes.

## Habits change between model generations

[Graphite's AI Tells update](https://graphite.io/five-percent/research/ai-tells-opus-5-5-update) (2026-10-01, an industry report without peer review) compares pre-2023 human articles with articles from ten models on 9,974 topics. Between two adjacent releases of one model family the em dash rate fell from 2.92 to 0.015 per 1,000 words, while the count of phrases used at twice the human rate or more fell by only 4% (2,666 to 2,548). The newer model's most over-used phrases flag importance ("this matters" at 116 times the human rate) or correct an unstated view ("rather than simply" at 32 times). The report's own summary is that such habits "change between models and versions, but do not go away."

[SlopBench](https://arxiv.org/html/2609.33905v1) (2026-09-27) sampled 18 models across email, essays, workplace chat, and social posts. Six classes of well-known markers, including "delve" and "as an AI", had a median of zero in every domain where they were scored. The authors work at a company that sells an AI email client.

Editing implication: date each observation and name the models it covered. A habit the newest models dropped is still produced by older and open-weight models, and by people whose writing they shaped, and a text under edit can come from any of them. No source here measured current open-weight models, so the catalog keeps the padding-era entries on the evidence of the earlier studies above and retires none of them on the strength of frontier-model results.

## Revision introduces its own defects

[Zamaraeva et al., The rise of antithesis in NLP papers](https://arxiv.org/html/2610.10092) (version 1, 2026-10-07) counts contrast constructions in papers and in model drafts and self-revisions. When one model revised its own draft, the share of "rather than" uses that an annotator found annoying rose from 3.2% to 41.7%. For two models from another family, pooled, it rose from 10.2% to 22.7% on one annotator's labels. A third model showed no rise. The two annotators are authors and agree poorly (kappa 0.18), and the corpus is academic prose.

[Oh et al., Science or Slop?](https://arxiv.org/html/2610.00531) (version 1, 2026-09-30) gave a reviser model definitions of six structural defects plus the flagged locations. The reviser pushed three scores past the human average, reached a zero redundancy score "by removing the repeated sentence together with four citations", and broke a content guard in 23% of rounds. A harness that edited only where evidence supported it, with a separate reviewer, broke none. The study covers generated scientific papers and validates against proxies, with no new human judgments.

[Abdulhai et al., How LLMs Distort Our Written Language](https://arxiv.org/html/2603.18161v2) (version 2, 2026-08-26) had three small models revise 86 student essays. Under an instruction to make only necessary corrections, adjective use still rose 40 to 87% and pronoun use fell 31 to 56%, where human revisions of the same drafts moved any category by under 5%. Heavy users in a separate trial rated the result as less in their own voice and were no less satisfied with it.

[Gooding et al., Writing as a testbed for open ended agents](https://arxiv.org/html/2503.19711v1) (2025-03-25) found that larger insertions went with lower human ratings of a revision and larger deletions with higher ones (both p < 0.001, no effect sizes reported). The three models' suggestions skewed toward adding, and human editors' suggestions toward removing and reshaping. The models are from 2024.

Editing implication: verify the revision against the source, mechanically where possible. An instruction to edit minimally or to preserve voice is not a check. Treat a scanner finding as a question, since a model given findings as targets can satisfy them by deleting content. The scanner's compare mode exists for this. Its inventories are lexical, so it cannot see a claim that changed meaning while keeping its numbers.

## Reader approval

[Cheng et al., Sycophantic AI Decreases Prosocial Intentions and Promotes Dependence](https://arxiv.org/abs/2510.01395) (2025-10-01) reports that 11 models affirmed users' actions 50% more than humans did, and that participants in two preregistered experiments (N = 1,604) rated sycophantic responses as higher quality and trusted them more. In the Shaib study above, a model given the editors' full annotation guide matched their verdicts at kappa 0.01. [SlopBench](https://arxiv.org/html/2609.33905v1) found no reliable relation between its composite marker score and crowd ratings of the same models (r = -0.115, 95% interval -0.55 to +0.37); its authors say the comparison "neither supports an association nor establishes the absence of one."

Editing implication: a reader liking a reply, a model judging its own draft clean, and a low marker count are all weak evidence of quality. Prefer a check with an answer: can a reader without context say what happened and what to do next. The sycophancy entry (E5) follows from the first study. Its scope is interpersonal advice, and applying it to technical replies is an inference.

## Editorial conventions

[Microsoft's list guidance](https://learn.microsoft.com/en-us/style-guide/scannable-content/lists) permits useful list structures, including term-and-definition formats. [Google's word list](https://developers.google.com/style/word-list) treats terminology as a contextual decision for an audience and product.

Editing implication: lists, bold terms, and repeated component names can improve documentation. Preserve a project's required structure and defined terms. Our dash ban is a house preference, not a scientific authorship test.

## Local observations and scanner evidence

The catalog's rhetorical families are editing observations. The scanner's three-family stacked-frame threshold is a candidate-generation heuristic, not an empirically established failure boundary. The same holds for the 45-word mark at which the density diagnostics list a sentence, which is a place to look and never a limit. Its regression suite tests detection, preservation, exit codes, and known masking limits; it does not validate authorship attribution or writing quality.

Earlier revisions included exact local model-comparison rates sourced to an unshipped, gitignored corpus, plus several unattributed "reported" benchmark numbers. Those numbers are not a reproducible basis for distributed instructions. Retain a quantitative local claim only with the collection method, consent and scope, model and prompt versions, matched comparison corpus, runnable analysis, and uncertainty. Raw transcripts need not be published to justify a useful editorial observation; describe the observation without unsupported precision.

No source here validates a three-rule cognitive ceiling, a fixed number of signals needed to report a defect, a healthy percentage of words to delete, or a universal sentence-length distribution. Keep mechanical diagnostics descriptive and evaluate revisions against meaning and the reader's task.

## Maintaining this reference

When adding research, open the primary source and record the version, domain, comparison, and limitation that affects the proposed rule. Record which models a result covered. A result about the newest frontier models is not grounds to remove guidance that older and open-weight models still need. Link the claim to the decision it changes. Remove a citation if it merely decorates advice. Do not promote a result from classification into an editing prescription without saying that the transfer is an inference.
