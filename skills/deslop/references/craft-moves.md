# Craft moves

Pattern matching finds tells. This file fixes them, using diagnostics from the editing tradition that predates AI by decades.

The reason it works is not sentiment. The three features with the largest measured gap between model and human prose (present participial clauses at 5.3 times the human rate, "that" clauses as subject at 2.6, nominalizations at 2.1, all in `evidence.md`) are precisely what Joseph Williams' character-and-action principle and Gopen and Swan's "articulate the action in the verb" were written to repair. The tradition aimed at clarity and happened to aim at the machine signature.

Two properties make these better than a wordlist. They are voice-neutral, so they fix the defect without imposing a register. And they cannot rot, because nobody is going to publicize participial-clause density until models stop producing it.

## The three tests to run on any paragraph

Each takes under a minute and each catches a different failure.

**The verb-list test** (Gopen and Swan). List every verb in the paragraph and read the list on its own. Do the real actions appear? A list reading *is, serves, has, represents, involves* means the actions are hidden in nouns, and that is the same defect as "plays a crucial role" and "serves as the entry point". Find the missing actions and make them the verbs.

**The topic-string test** (Williams). Underline the first seven or eight words of every sentence, stopping at the verb. Read the underlined strings together. Do they name a small set of related ideas, or does every sentence open on a new abstraction? A scattered topic string is why a paragraph feels like it is about nothing, and it is invisible sentence by sentence.

**The stress-position test** (Strunk, formalized by Gopen and Swan). Read aloud and tap hard on the last three or four words of each sentence. Do they deserve that emphasis? Sentences that end on metadiscourse or a hedge have buried the payload. Move peripheral ideas left and new information right.

## Character and action

Williams' central principle: make the main characters the subjects, and their actions the verbs. The diagnostic question is whether the subject names a character and the verb names that character's action.

- Before: `The automation of manufacturing by corporations means the loss of jobs for blue-collar workers.`
- After: `Corporations are automating, and blue-collar workers are losing jobs.`

Almost every AI structural tell is a violation of this one principle. Nominalization hides the action in a noun. The participial tail comments without a subject. Actor-hiding passive drops the character. False agency gives the action to an object. All four are repaired by the same edit, which makes this the highest-leverage move in the file.

Strunk's 1918 rule 10 carries a test that later editions dropped: "a common fault is to use as the subject of a passive construction a noun which expresses the entire action, leaving to the verb no function beyond that of completing the sentence." His fix for `A survey of this region was made in 1900` is `This region was surveyed in 1900`, which is still passive. That is the proof the test is about nominalization rather than voice, and it is exactly the distinction the popular "avoid the passive" rule destroys.

## Information flow

**Old before new.** Each sentence should open on something the reader already has and end on what is new. Passive voice is correct when it puts old information first, which is another reason a blanket passive purge damages prose.

**Throat-clearing.** Count the words before the subject. A stack of metadiscourse plus attitude plus time is the AI opening signature.

- Before: `And therefore, it is important to note that, in Eastern states since 1980, acid rain has become a problem.`
- After: `Since 1980, acid rain has become a serious problem in the Eastern states.`

**Subject-verb distance.** Count the intervening words. More than about twelve and the reader has lost the predicate. Move the interruption to the front or the back of the sentence.

**Faked coherence.** Does each connective mark a real logical relation? A chain of *Moreover, Furthermore, Additionally* is bluffing at cohesion. Deleting the connective is usually the whole fix, and when the relation is real, name it.

**Cohesion is not coherence.** Cohesion is adjacent sentences fitting together; coherence is the whole passage adding up to something. A passage can be perfectly cohesive and still incoherent, which is the exact experience of reading fluent AI prose that says nothing. Diagnose which one is broken before editing, because the fixes are different: cohesion is repaired sentence to sentence, coherence by cutting or restructuring whole units.

## Abstraction

**Concept nouns** (Zinsser). Ask whether you can picture someone doing something.

- Before: `The common reaction is incredulous laughter.`
- After: `Most people just laugh with disbelief.`

**Creeping nounism.** Count the nouns stacked before the verb. `Communication facilitation skills development intervention` becomes `a class to help students write better`.

**Metaconcepts** (Pinker). A sentence built on a container word instead of the thing itself: *approach, assumption, concept, condition, context, framework, issue, level, model, perspective, process, prospect, role, strategy, subject, tendency, variable*. Note that "plays a crucial role" is literally a metaconcept construction, which is why it feels like nothing is being said. Call the thing by its name.

**Significance tails** (Zinsser). Does the sentence tell the reader how to feel before giving them the fact? Cut the evaluation and keep the fact. Zinsser's line, written decades before "highlighting the importance of" existed: given the number, readers can do their own marveling.

## Hedging: the discriminator that actually works

Pinker's formulation is the cleanest test anyone has written. **Does the qualifier name the conditions under which the claim fails, or is it an escape hatch?** A qualification is a choice; a hedge is a tic. Keep and even add qualifications; cut hedges.

A wordlist cannot make this call, and there is a paper proving it: the CoNLL-2010 shared task annotated legitimate scientific hedges and illegitimate encyclopedic weasels using overlapping word lists, where *probable, likely, possible, may, might, suggest, appear* appear in both taxonomies. The same task documents complex keywords, phrases that are speculative only as a whole, where neither word carries the speculation alone.

Six questions, and any single no means cut:

1. Can you name the span the hedge governs?
2. Is the uncertainty attributable to a named holder or body of evidence?
3. Is it falsifiable?
4. Does deleting it change the truth conditions of the sentence?
5. Is it a regulated or pre-approved string?
6. Does the hedge cover the recommendation, not only the finding?

That last one is where published writing fails most often. Roughly 44% of articles in one epidemiology survey hedged the finding and then overclaimed in the recommendation. And removing honest hedges demonstrably misleads expert readers: in a randomized trial of 300 clinicians, abstracts with spin were rated as showing more treatment benefit than the same abstracts de-spun.

The operational procedure from CoNLL-2010: mark the minimal cue, then extend the scope to the largest syntactic unit, such that disregarding the marked span leaves a sentence you can still extract facts from.

## The protocol: brackets, not deletions

Zinsser's method is the right shape for a detector. He bracketed every component that was not doing useful work rather than crossing it out, to avoid violating the writer's prose, so the message was "I think this can go, but you decide."

Two things follow. The detector proposes and the author disposes, which is the same separation `SKILL.md` enforces between roles. And the test is sharper than the usual paraphrase check: **is every word doing new work?**

## Guards, so a craft pass does not overshoot

Each of these contradicts advice that circulates widely.

| Guard                                        | Why                                                                                                                                              |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Do not vary sentence openings for variety     | Williams calls this bad advice outright. Changing subjects to make them different breaks the topic string, and most writers change topic too often |
| Keep four kinds of nominalization              | Back-reference subjects, replacements for `the fact that`, ones naming the verb's object, and familiar concepts acting as characters. See catalog N17 |
| Trailing participial clauses can be correct   | Williams treats them as free modifiers. The discriminator is whether the clause adds a fact or restates significance                              |
| Do not count adjectives or adverbs            | POS-tagging puts Zinsser's own book at 12.8% adjective-plus-adverb and a Bulwer-Lytton novel at 11.7%. The rate says nothing; semantic containment does |
| Do not optimize a readability grade            | Flesch-Kincaid and ARI both reward short sentences and short words, so chasing them manufactures the choppy uniform prose you are removing         |
| Repeat the term, vary the connective           | Consistency of terminology is required by Microsoft, Google, and ASD-STE100. Vary sentence shape and transitions, never the name of the thing       |
| Vary rhythm in clusters, not by alternation    | Human sentence-length series are persistent, with short following short and long following long in runs. Strict short-long alternation produces a pattern found in no corpus |
| Never frame the job as improving prose         | Editing measured as style change scored the only negative quality delta of any edit category in one study, while fluency-driven rewriting over-corrects and erases authorship. Delete tells; do not upgrade writing |

## The size of the edit

Lanham's lard factor is the one measurable over-correction guard worth computing:

```
lard_factor = (original_words - revised_words) / original_words
```

A third to a half is the normal range for a bloated draft, and Zinsser independently put most first drafts at 50% cuttable. Treat roughly 30 to 50% as healthy and about 70% as a ceiling. Williams' own demonstration ladder cuts 205 words to 149, then 99, then 51, and he says the shortest version lost the passage's charm. A pass that cut three quarters of the words did not clean the prose, it replaced it.

The factor measures your edit rather than the text, which is exactly what makes it useful here: it is the one number that catches an over-eager deslop pass in the act.

## Sources

Williams and Bizup, *Style: Lessons in Clarity and Grace*. [Gopen and Swan, "The Science of Scientific Writing," *American Scientist* 78 (1990)](https://www.americanscientist.org/blog/the-long-view/the-science-of-scientific-writing). Zinsser, *On Writing Well*. [Strunk, *The Elements of Style* (1918)](https://www.gutenberg.org/files/37134/37134-h/37134-h.htm), whose rule 10 differs from later editions. [Pinker, "Why Academics Stink at Writing"](https://stevenpinker.com/files/pinker/files/why_academics_stink_at_writing.pdf). [CoNLL-2010 shared task on hedge detection](https://aclanthology.org/W10-3001.pdf). Measured feature rates and effect sizes in `evidence.md`.

Book citations are to the works themselves; page and section numbers were not verified here, so quote by paraphrase rather than by page.
