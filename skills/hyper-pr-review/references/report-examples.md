# From Review Notes to Useful Findings

These synthetic cases show how the same evidence should control the verdict, explanation, and presentation. File anchors and test results are fixture facts, not claims about a real repository. Preserve their scope when adapting the examples; do not copy invented receipts into a live review.

## A Blocker with Several Symptoms

The review notes establish:

- The contract permits retries but requires one charge per logical payment.
- The changed retry loop creates an idempotency key inside each attempt at `payments.ts:84`.
- The timeout fixture simulates provider acceptance followed by a lost response. It records two accepted charges with different keys.
- Separate review lenses flag duplicate charges, unstable retry identity, and missing retry coverage. All refer to this loop. The existing fixture already demonstrates the defect.
- The caller and timeout path were reviewed; settlement behavior was outside the requested scope.

A useful report:

> Needs changes. A retry can charge the same payment twice after the provider accepts the first request but its response is lost.
>
> **Required: preserve payment identity across retries.** The retry loop (`payments.ts:84`) creates a new idempotency key for each attempt. The timeout fixture records two accepted charges with different keys, so the provider cannot recognize the retry as the same payment. Keep the key stable for the logical payment and make that fixture assert a single accepted charge.
>
> I traced the caller and ran the timeout fixture. Settlement behavior was outside this review's scope.

The report keeps one cause and one remedy together. Three lenses do not justify three findings. The evidence supports the duplicate-charge claim; the remedy still needs verification after implementation. The opening names the consequence, while the finding explains how it happens.

## An Unfinished Review with Green Local Checks

The review notes establish:

- The requested scope includes a schema migration and its rollback behavior.
- The serializer tests passed, and the serializer code was read.
- The migration and rollback path have not been inspected. No database fixture was available.
- No defect was confirmed in the serializer.

A useful report:

> Inconclusive. The serializer checks passed, but the required migration and rollback review is unfinished.
>
> I found no material issue in the serializer code I inspected. That result does not cover the migration's data preservation or rollback behavior. Complete the migration trace and run its forward-and-rollback fixture before deciding whether to approve.

The report does not turn a missing environment into a claim that the migration is broken. Green checks remain useful evidence within their scope. If another inspected path contained a confirmed blocker, the opening would instead say needs changes and still disclose the unfinished migration review.

## A Valid Design with an Optional Improvement

The review notes establish:

- The two changed adapters deliberately evolve independently and satisfy their current contracts.
- The named scope was fully reviewed and both adapter suites passed.
- Each adapter duplicates the same formatting expression at `email_adapter.py:42` and `sms_adapter.py:31`.
- A shared helper would remove the duplication, but no divergence or required shared-format contract has been established.

A useful report when the author explicitly asked for design feedback:

> Approve. Both adapters preserve their contracts, and their test suites passed.
>
> **Optional: share the formatting expression if its behavior should stay coupled.** The email adapter (`email_adapter.py:42`) and SMS adapter (`sms_adapter.py:31`) currently use the same expression. A helper would give a future shared-format change one place to land, but independent evolution is also a valid reason to keep the expressions separate. No current defect makes that extraction necessary for this merge.

For a focused bug review, omit this low-value preference unless it affects the requested fix. A structural observation becomes useful through its consequence and tradeoff, not merely because two snippets match. Do not inflate a valid design choice into a blocker to make the review look thorough.
