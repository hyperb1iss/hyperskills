# Surface profiles

Use the artifact's purpose and authority to choose an edit. A correct rule applied to the wrong surface can remove necessary structure, uncertainty, or voice. The main skill contains the authority map; these examples show how that map changes a revision.

## README and project introduction

Lead with what the project does and who it serves. Preserve code, installation commands, badges, links, and supported capabilities. Do not add a benchmark to make an introduction sound concrete.

Before:

> Nexus is a powerful, seamless task runner built for modern development workflows. Leveraging a dependency graph, it delivers blazing-fast builds.

After:

> Nexus is a task runner that schedules work using a dependency graph.

The source does not establish parallel execution, caching, or any timing result. Add those only when the repository or supplied evidence supports them.

## Documentation body

Describe current behavior and mechanisms. Preserve API signatures, error strings, configuration, frontmatter, examples, and qualifications.

Before:

> Let's dive into how Nexus handles caching. Nexus uses content hashing to determine what needs to rebuild, ensuring an excellent development experience.

After:

> Nexus uses content hashes to determine what needs to rebuild.

A deeper explanation of cache keys needs code or documentation evidence. Do not invent which environment variables are hashed or claim a failure mode is the most common without support.

## Release notes and migration guides

Narrating a change is the purpose here. Keep versions, compatibility consequences, deprecations, and migration instructions. A factual change summary is appropriate even when the same phrasing would age badly in a code comment.

Before:

> Version 2.4 marks a pivotal moment for caching. The cache now includes the task definition in its key, so changing a task command invalidates the entry. The future looks bright!

After:

> Version 2.4 includes the task definition in the cache key. Changing a task command now invalidates the entry.

Do not insert a renamed flag or breaking change absent from the source. When creating release notes from a diff, that diff can supply the missing facts.

## Commit body

Follow the repository's commit contract. Under the house rules, use plain text, a Conventional Commit subject, a body explaining why, and 76-column wrapping. Required trailers and unavoidable URLs follow the contract's exceptions.

Example with supplied evidence:

```text
fix(cache): include the task command in cache keys

Editing a task command reused output from the previous command because
cache keys covered declared inputs only. Include the resolved command
in the key so a command change invalidates the cached result.
```

Use that explanation only if the diff establishes the described key change. Preserve uncertainty when a suspected failure has not been reproduced. A prose cleanup does not prove the implementation correct.

## Slack and email

Match the sender's voice. Preserve thread references, code, meaningful courtesy, and required signatures. Do not add a commitment the sender did not make.

Before:

> Great question! Happy to help clarify. So basically the deploy failed due to the fact that the migration timed out. Let me know if you'd like me to dig deeper!

After:

> The deploy failed because the migration timed out.

A timeout value, row count, root cause, batching recommendation, or promise to push a fix needs separate support. A warmer or more detailed reply can be appropriate when the context supplies it.

## PR body and reply

Use `super-good-pr` for structure and authorization. Preserve semantic emoji, reviewer guidance, validation receipts, and human-authored choices. Cut inflated significance without stripping useful evidence or calibrated uncertainty.

Before:

> ## 💡 What changes
>
> The limiter now uses one token bucket per tenant, a pivotal step toward a more robust API that showcases our commitment to reliability.

After:

> ## 💡 What changes
>
> The limiter now uses one token bucket per tenant.

A gateway enforcement point or signed tenant identity would be additional facts. Include them when the implementation establishes them. Do not convert a narrow proofreading request into a wholesale PR rewrite.

## Code comments and docstrings

Describe the current behavior or the non-obvious reason for an implementation choice. Preserve code examples, doctests, output, parameter names, and API contracts unless changing them is authorized.

Before:

```text
We now use a heap instead of sorting the whole list every time.
```

After:

```text
A heap avoids sorting the whole list for each operation.
```

An asymptotic complexity claim needs the actual operations and bounds. The word `heap` alone does not establish which elements are retained or how the algorithm uses them.

## Other registers

| Surface                                             | Preserve                                                                         |
| --------------------------------------------------- | -------------------------------------------------------------------------------- |
| Personal essay or blog                              | The author's stance, voice, and deliberate imagery                               |
| Encyclopedic or reference text                      | Neutrality, defined terms, and source attribution                                |
| Scientific, legal, medical, forecasting, postmortem | Qualification, evidence limits, approved language, and uncertainty               |
| Fiction                                             | The creative brief and the distinction between invention and factual attribution |
| Marketing                                           | Persuasive intent with support for factual claims                                |
| Agent brief, skill, or memory                       | Useful tables and precise terminology; clarity still matters                     |
| Quoted material                                     | Exact wording unless the request authorizes adaptation                           |

When the surface is unclear, infer it from the destination and surrounding artifact. Ask only when the answer would materially change the revision. A second model or an agent reader still needs a clear instruction; being able to ask follow-up questions does not make confusing prose acceptable.
