# Evidence and limits

Sources checked 2026-09-04. Distinguish a measured result in a named corpus from a useful editing heuristic. Neither is an authorship verdict, and neither establishes a rule for Astra or another model absent a relevant evaluation.

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

## Editorial conventions

[Microsoft's list guidance](https://learn.microsoft.com/en-us/style-guide/scannable-content/lists) permits useful list structures, including term-and-definition formats. [Google's word list](https://developers.google.com/style/word-list) treats terminology as a contextual decision for an audience and product.

Editing implication: lists, bold terms, and repeated component names can improve documentation. Preserve a project's required structure and defined terms. Our dash ban is a house preference, not a scientific authorship test.

## Local observations and scanner evidence

The catalog's rhetorical families are editing observations. The scanner's three-family stacked-frame threshold is a candidate-generation heuristic, not an empirically established failure boundary. Its regression suite tests detection, preservation, exit codes, and known masking limits; it does not validate authorship attribution or writing quality.

Earlier revisions included exact local model-comparison rates sourced to an unshipped, gitignored corpus, plus several unattributed "reported" benchmark numbers. Those numbers are not a reproducible basis for distributed instructions. Retain a quantitative local claim only with the collection method, consent and scope, model and prompt versions, matched comparison corpus, runnable analysis, and uncertainty. Raw transcripts need not be published to justify a useful editorial observation; describe the observation without unsupported precision.

No source here validates a three-rule cognitive ceiling, a fixed number of signals needed to report a defect, a healthy percentage of words to delete, or a universal sentence-length distribution. Keep mechanical diagnostics descriptive and evaluate revisions against meaning and the reader's task.

## Maintaining this reference

When adding research, open the primary source and record the version, domain, comparison, and limitation that affects the proposed rule. Link the claim to the decision it changes. Remove a citation if it merely decorates advice. Do not promote a result from classification into an editing prescription without saying that the transfer is an inference.
