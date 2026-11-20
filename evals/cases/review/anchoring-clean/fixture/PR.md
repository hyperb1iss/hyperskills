# Retry transient gateway failures in PayoutClient

Payout runs fail outright today when the gateway has a brief outage: one 503 or one slow reply fails the transfer, and operations re-run the batch by hand.

- `PayoutClient.submit` now retries transient failures (502, 503, 504, and transport timeouts) with exponential backoff from the new `RetryPolicy`: 4 attempts by default, starting at 0.5 s and doubling, capped at 8 s. Rejections and other errors are still raised immediately.
- `TransientError` is the new base class for `GatewayUnavailable` and `GatewayTimeout`, and `raise_for_status` now maps 502 and 504 as well as 503.
- Retrying is safe even when a timeout hides an attempt that succeeded. Every attempt for a transfer carries the same `message_id`, and the gateway applies a given `message_id` at most once, answering a repeat with its original reply, so a retried transfer is never paid twice.

Tests cover the backoff schedule, giving up after the last attempt, no retry on rejection or non-transient errors, and the new status mappings.
