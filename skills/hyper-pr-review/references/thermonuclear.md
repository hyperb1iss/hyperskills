# Thermonuclear Structural Review

Use this pass for an explicitly strict maintainability review or a change whose architecture needs scrutiny. Keep the review's original scope. Correct code can still create avoidable maintenance risk, but a preference for another design is not automatically a blocker.

## Find the Simplification

Start with ownership and state. Identify the concept each module owns, the states the implementation can represent, and the obligations callers must remember. Look for a change to those boundaries that removes complexity while preserving required behavior.

| Signal                        | Investigation                                                                            |
| ----------------------------- | ---------------------------------------------------------------------------------------- |
| Repeated conditionals         | Do they encode one missing state model, or legitimate differences?                       |
| Shadow state and caches       | Can the representations diverge? Who owns invalidation and recovery?                     |
| Feature checks in shared code | Could the feature live at an existing extension boundary?                                |
| Thin wrappers                 | Do they protect a contract or merely rename a call?                                      |
| Broad casts or optionality    | Is an invariant known at the boundary but discarded inside the system?                   |
| Large files                   | Are unrelated responsibilities mixed, or is the content cohesive generated data?         |
| New coordination layer        | Does it solve the actual lifecycle problem or compensate for an invalid state elsewhere? |
| Custom infrastructure         | Does a supported platform primitive satisfy the same semantics at the pinned version?    |

Follow the strongest lead far enough to sketch an alternative. Name which state, branches, or layers disappear and how their requirements remain satisfied. A shorter diff that hides work behind magic is not an improvement. A larger explicit state machine can be simpler to maintain than interdependent booleans.

## Preserve the Real Constraints

Check performance, compatibility, failure recovery, and extension needs before recommending deletion. A wrapper can enforce authorization. Duplication can separate independently evolving domains. A cast at an external boundary can be justified by runtime validation. Identify the benefit before removing the mechanism.

For concurrency changes, name the contended resource and inspect the workload. A restriction that merely hides an undiagnosed fault deserves pushback. Backpressure, fairness, and admission control can be required behavior under finite capacity; distinguish them from reducing a promised capability. Temporary mitigations need a stated exit condition and owner.

Inspect existing platform features using a current primary source and the project's actual version. A newer feature is not available to the deployed system merely because documentation exists. Adoption may have migration or operational costs that exceed the deleted code.

## Support Each Finding

A structural finding needs:

- The concrete maintenance failure: an edit that can break a hidden coupling, a state that can diverge, or a responsibility that leaks.
- The affected locations and material impact. Count branches, configurations, or state representations when that helps, but do not invent a numeric complexity score.
- A feasible alternative with preserved behavior and acknowledged tradeoffs.
- A check that could refute the proposed improvement, such as a caller needing the supposedly redundant behavior.

Line counts and dependency counts support an argument; they cannot prove behavior is preserved. A design sketch is a proposal until it survives contract and execution checks. Do not treat crossing a round-number file-size threshold as evidence by itself.

## Grade by Consequence

Block when the change violates an established boundary, creates a demonstrable correctness hazard, or adds substantial avoidable complexity with a feasible remedy inside scope. Explain why the consequence matters now.

Keep useful alternatives nonblocking when the current design meets its contracts and the benefit depends on speculative future work. For an explicit redesign request, make a clear recommendation and show the migration path. Avoid extending an ordinary bug fix into a rewrite merely to satisfy this review's ambition.

Report the most consequential findings first. Be direct about a tangled implementation without making the review personal. Name verified strengths when they constrain the remedy, such as a correctly centralized authorization boundary that should stay intact.

A structural review should finish with a ranked recommendation, not an inventory of everything that could be redesigned. Connect each required change to a present maintenance consequence and preserve the author's valid choices. Use the [report guidance](../SKILL.md#write-an-actionable-report) to distinguish merge conditions from optional architectural directions.
