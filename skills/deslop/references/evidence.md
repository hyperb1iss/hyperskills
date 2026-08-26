# What the research actually supports

Deslop advice circulates as folklore, and several widely copied rules point the wrong way. This file separates what corpus work supports from what practitioners assert, so a rule can be weighed instead of obeyed.

Each claim carries a tier. **Verified** means the source was opened and the claim appears in its abstract. **Reported** means a research pass surfaced the figure from the paper body, and it was not independently confirmed here. **Unsourced** means a practitioner or community claim with no corpus behind it. Do not upgrade a tier by repeating it.

Dated Aug 2026. Lexical findings spoil fastest, structural findings least.

## Structure carries the signal, vocabulary does not

**Verified, in fiction.** [StoryScope: Investigating idiosyncrasies in AI fiction](https://arxiv.org/abs/2604.03136) (Russell, Rajendhran, Pham, Iyyer, Wieting) built a corpus of 61,608 stories from 10,272 prompts, each written by a human author and five LLMs. Its abstract reports that **narrative features alone achieve 93.2% macro-F1 for human versus AI detection**. Structure identifies machine text there without looking at a single word choice.

Read the scope honestly: the measurement is narrative features on fiction, and it does not establish the same result for a README or a spec. What carries across is the mechanism, since the four verified over-used features below are syntactic rather than narrative and appear in every register.

**Reported.** The same work finds surface-level rewriting barely moves detection, and separate self-similarity work finds machine text measurably over-coherent, with those features surviving paraphrase attack better than lexical baselines.

Consequence for this skill: the pass order runs structure before vocabulary. That ordering is a design bet supported by the fiction result and by marker rot, not a proven fact for technical prose.

## Features where the direction depends on the model

**Verified.** [Do LLMs write like humans? Variation in grammatical and rhetorical styles](https://arxiv.org/abs/2410.16107) (Reinhart, Markey, Laudenbach, Pantusen, Yurko, Weinberg, Brown; [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11874169/)) compares Llama 3 and GPT-4o variants against human corpora using Douglas Biber's feature set. Its abstract reports systematic differences that persist as models grow and are larger for instruction-tuned models than base models.

The finding that matters most for editing is that several features **diverge in direction between model families**, which makes any universal rule about them unsupported. Verified from the paper's text:

> Both GPT-4o models avoid clausal coordination, while all Llama 3 variants use it more frequently than humans.

> Both GPT-4o models use downtoners more frequently than humans, while all Llama 3 variants avoid them.

Downtoners are hedges. So "strip the hedges" is roughly right for GPT-4o prose and actively wrong for Llama 3 prose, and a skill that states either as a general rule is wrong half the time. **Reported** (from the paper's feature tables, not independently confirmed here): the same split appears in agentless passive, contractions, and first-person pronouns, where GPT-4o runs well below human rates (passive around 51 to 53%, contractions around 60 to 63%, first person around 62 to 81%) while Llama 3 Instruct sits near or above them.

Consequence, and it is the rule in `SKILL.md`: do not apply a blanket fix to passive voice, hedges, contractions, first person, or coordination style. Ask what the sentence needs. The only defensible version of the advice is narrow, so fix passive that hides an actor the reader needs and hedges that qualify nothing.

## Features verified over-used, which is where to aim

**Verified**, GPT-4o rates relative to humans, from the same paper:

| Feature                                                | Rate vs human |
| ------------------------------------------------------ | ------------- |
| Present participial clauses ("..., ensuring that...")   | 5.3x          |
| "That" clauses as subject ("That the build failed...")  | 2.6x          |
| Nominalizations ("the implementation of validation")    | 2.1x          |
| Phrasal coordination ("X, Y, and Z")                    | 1.9x          |

These four are the highest-confidence structural targets in this file. The participial figure is the strongest single signature measured anywhere in the sources here, which promotes the participial-tail tell (`pattern-catalog.md` N3) from a stylistic nitpick to the most reliable syntactic marker available. Nominalization and the phrasal-coordination imbalance are catalog entries N17 and N15.

Note the shape of the fix for each: all four are repaired by giving a real subject a real verb, which is the same move Joseph Williams built his style manual around. Turning "the implementation of validation ensures correctness" into "the middleware validates each request" fixes a nominalization, a participial clause, and an actor-hiding construction in one edit.

## Words that look like tells and are not

**Reported.** Log-odds analysis on the HC3 human-versus-ChatGPT corpus finds `robust` skewed **human** (roughly 0.47 times, z about -3.3), with `leverage` and `crucial` also at or below parity. Banning those three generates false positives on human prose.

**Reported.** The same analysis finds these over-represented in human writing, which makes them weak positive signals rather than things to cut: *my*, *really*, *we*, *now*, *just*, *but*, *actually*, *think*, *thing*, *since*.

**Reported.** Wikipedia's own corpus evidence lists isolated wordy constructions (*as a result of*, *in order to*, *the fact that*), plain copulas, honest superlatives, and hedging qualifiers as human signals. Mechanically stripping filler makes text read more generated, not less. Cut clusters, not instances.

## The em dash is a house rule, not a verdict

**Reported.** A twelve-model measurement of em dashes per 1,000 words against eight published human essays puts Twain's *Huckleberry Finn* at 10.13 and Melville at 8.12, above or near frontier models measured in the same pass, with a human baseline around 3.23 and a range from 0.33 to 17.12. A density gate cannot convict, and the em dash is better understood as a per-model fine-tuning artifact than as a universal tell.

**Reported.** Suppression resistance varies by model. Some drop by 98% when told to avoid markdown; others barely move, and some retain em dashes even under explicit prohibition. Format suppression and punctuation suppression are separate instructions, because an em dash is prose-legal and survives a "no markdown" instruction that zeroes headers and bullets.

**Reported.** The double-hyphen substitute is worth catching: writers and models prompted away from `—` are observed emitting `--` instead. Our fixtures verify only that the scanner detects a constructed `a--b`, not the behavioral claim. Either way, swapping one for the other trades a known signature for a newer one.

Consequence: on our surfaces the dash ban is enforced because the project contract bans it, not because it proves authorship. On someone else's prose, treat dash density as a candidate and look for converging signals.

## Marker rot is measured

**Verified.** [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016) (Kobak, González-Márquez, Horvát, Lause; also Science Advances 11(27):eadt3813) analyzed more than 15 million PubMed abstracts from 2010 to 2024 and found an abrupt post-LLM increase in certain **style words**, estimating that at least 13.5% of 2024 abstracts were LLM-processed, reaching about 40% in some subcategories. The paper's own title uses *delving*, which is the joke and also the point.

The published word list is machine-readable and MIT-licensed at [berenslab/llm-excess-vocab](https://github.com/berenslab/llm-excess-vocab) (`results/excess_words.csv`, 900 rows, typed `style` or `content` with part-of-speech annotations). Prefer it to any hand-written wordlist, because it was derived from frequency shift rather than intuition.

**Reported.** Two structural facts from that list are worth more than the words themselves. Close to 30% of excess style words are `-ing` forms, which turns the participial tell from a phrasing habit into a verb-inflection fingerprint. And fancy prepositions (*amidst*, *amid*, *alongside*, *midst*) appear as markers, which nobody lists.

**Reported.** Markers decay once they are publicly named. Words called out as AI tells later showed measurable uptake in spontaneous human speech, while *delve*'s frequency in one corpus fell after public callouts even as *significant* and *additionally* kept rising. Pre-LLM baseline usage for *realm*, *intricate*, and *pivotal* sits around 2 to 3%, which is the irreducible false-positive floor for any wordlist gate.

Consequence: date every wordlist, weight structure higher, and expect the lexical layer to keep thinning.

## Judges and scores

**Reported.** LLM evaluators recognize and prefer their own generations, so a model should not judge its own output. Agreement between LLM judges and human slop labels has been measured near chance (kappa around 0.01 to 0.03 across several frontier models), and judges have shown a preference for model-written text over human-written text. Asking a model for an absolute slop score out of 50 produces a number with no demonstrated validity, and the widely copied "below 35 out of 50, revise" threshold traces to a single repository with no validation behind it.

**Reported.** Self-gating, where one model both judges and repairs, raises acceptance while correctness falls. That is why `SKILL.md` separates the detector from the rewriter and forbids the detector to rewrite.

Consequence: use a different model when a judge is needed (`cross-model-review` provides that), demand analysis before scores, and never report a single composite number as the outcome.

## Detection is not the goal

**Reported.** OpenAI retired its own AI Text Classifier in July 2023 for low accuracy, having launched it at roughly 26% recall with a 9% false-positive rate. A study in *Patterns* found seven detectors misclassified a majority of TOEFL essays as AI-written, and later work found detectors disproportionately flagging English-language-learner essays where human annotators showed no such bias.

Consequence, and it is a hard rule in `SKILL.md`: never emit an authorship verdict, never report a detector score, and never treat a handed-over score as evidence. The damage from false positives falls on second-language and neurodivergent writers.

## Metrics worth computing, and their traps

**Verified by our own testing** (`scripts/slopscan.pl`, fixtures in `references/fixtures/`):

- Splitting sentences on every period breaks on version numbers, decimals, abbreviations, file paths, and URLs. One sentence containing `v1.2.3` and `e.g.` produced four fake sentences before the splitter required a terminator followed by whitespace and an opening character.
- A code-fence stripper anchored to column one leaks indented and tilde-delimited fences. Vocabulary counts from an unmasked file include the code.
- Markdown table delimiter rows read as double-hyphen dashes unless prose-free lines are skipped.
- `rg -c` counts matching lines rather than matches, so any budget check ("at most one per document") needs `rg -o | wc -l`.

**Reported.** Coefficient of variation on paragraph length is scale-free and trivial to compute, which makes it the better single rhythm metric. Type-token ratio is length-dependent and should be replaced by a moving-average variant over a 25 to 50 word window. Circulating thresholds for sentence-length standard deviation false-fire on short crisp technical prose, and a measurement of this repo's own contract prose landed above one published "human floor," which means that floor is wrong for terse instructional writing.

Consequence: the scanner reports rhythm and never gates on it, and the only deterministic rhythm rule is the over-correction trip, which fires on prose that has been cut too short rather than on prose that is too uniform.

**Reported.** `proselint` produced zero diagnostics against a fixture stuffed with AI tells, and its typography module wants curly quotes and ellipsis characters, which is the opposite of what this skill wants. Do not gate on it.

## Where this file is thin

The per-feature percentages in the folklore section are reported rather than verified, and they carry the most weight of anything here. Anyone extending this skill should open Reinhart et al. and read the feature tables directly. The community-sourced tell families in `pattern-catalog.md` (reasoning leak, premise stacking, calibration theatre, performed candor) are unsourced pattern observations, useful and unmeasured.
