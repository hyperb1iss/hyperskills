# Craft moves

Use these diagnostics when a sentence or paragraph has a concrete clarity problem. The goal is a useful revision that preserves meaning, not a more impressive rhythm statistic.

## Subject and action

Check whether the subject names the relevant actor and the verb carries the action. A nominalization can hide both:

- Before: `The committee conducted an investigation into the outage.`
- After: `The committee investigated the outage.`

Keep nominalizations that name a defined concept, refer back to an earlier sentence, or express the right object (`accept the request`). Keep passive voice when the actor is unknown, unimportant, or already clear. Never invent an actor to satisfy the active-voice preference.

## Paragraph continuity

Read the subjects of consecutive sentences. The paragraph should develop related ideas rather than rename its topic or introduce a new abstraction every sentence. Repeat defined terms; vary sentence shape only when the reader benefits.

Check each connective against the logical relationship. A `because` claims causation, a `therefore` claims an inference, and an `also` adds information. Removing an unsupported connective may be necessary, but weakening a supported causal claim is also a substantive edit.

A chain of individually clear sentences can still lack a point. State the paragraph's conclusion and keep only the material that supports or qualifies it. Preserve deliberate reminders in procedures and summaries that help readers navigate long documents.

## Sentence emphasis

Locate the main subject and verb. Move a long interruption if it forces the reader to hold an unfinished thought. Place the information the sentence develops where the reader can recognize it as the point, often near the end.

Avoid numerical gates for subject-verb distance, word count, or sentence length. A short legal sentence can be ambiguous; a long explanatory sentence can be clear. Read the revised paragraph in context instead of optimizing a single line.

## Uncertainty and qualifications

Keep a qualifier when deleting it changes the truth conditions, scope, confidence, or recommendation. Approved or regulated language stays intact unless editing that language is authorized.

| Question                                                    | Action                                                              |
| ----------------------------------------------------------- | ------------------------------------------------------------------- |
| Does the qualifier express a real uncertainty or condition? | Keep it and make its scope clear                                    |
| Does deleting it turn a possibility into a promise?         | Keep it                                                             |
| Do several qualifiers express the same uncertainty?         | Combine them without strengthening the claim                        |
| Does a recommendation overstate a qualified finding?        | Qualify the recommendation too                                      |
| Is the basis unknown?                                       | Flag the missing support; do not convert uncertainty into certainty |

Scientific hedging and vague attribution can use the same words. Context decides their function. The [CoNLL-2010 hedge detection task](https://aclanthology.org/W10-3001/) distinguishes uncertain language and its scope across scientific and Wikipedia text; its annotations are not a universal deletion rule.

## Diagnose before replacing

Mark the exact span and explain its defect. A proposed replacement should retain the same supported facts. When removing puffery leaves no factual content, say what evidence is missing or use the limited claim already present.

- Before: `The retry logic backs off exponentially, ensuring resilience and improving reliability.`
- After: `The retry logic backs off exponentially.`

A stronger statement about load or outage behavior needs evidence. An exponential delay alone does not establish jitter, a retry budget, or recovery under an outage.

## Check for drift

Compare the original and revision for changed actors, quantities, time, scope, modality, negation, and causal force. Verify that the rewrite did not rename a defined term or delete a necessary exception. Word-count changes can help find unexpectedly large edits, but no reduction percentage establishes quality.

When a sentence works, keep it. When a passage needs additional explanation, a longer revision may be the right edit. Do not inject staccato fragments or mechanically alternate short and long sentences to make prose appear human.

## Background

These diagnostics draw on the editing traditions of Joseph Williams and Joseph Bizup's _Style: Lessons in Clarity and Grace_, and [Gopen and Swan's The Science of Scientific Writing](https://www.americanscientist.org/blog/the-long-view/the-science-of-scientific-writing). Treat them as craft techniques, not experimental guarantees about current models. Checked corpus research and its limits live in `evidence.md`.
