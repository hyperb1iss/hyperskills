# Codex Review Prompt Templates

Ready-to-use prompts for each review pass. These are model-agnostic — they work with any reviewer CLI.

## Usage

Pass prompts as the final argument to the reviewer CLI:

```bash
# From Claude (Codex reviews)
codex exec "PROMPT_TEXT_HERE"

# From Codex (Claude reviews)
claude -p "PROMPT_TEXT_HERE"

# Or pipe a diff into either
git diff main...HEAD | codex exec "PROMPT_TEXT_HERE"
git diff main...HEAD | claude -p "PROMPT_TEXT_HERE"
```

For Codex's structured `codex review` command, prompts aren't needed — it has its own review format.

## General Review

Best as the first pass. Broad coverage across all dimensions.

```
Review the changes between main and HEAD with extreme thoroughness. Prioritize:
1. Correctness — logic errors, edge cases, null handling, race conditions
2. Security — injection, auth gaps, secrets exposure, OWASP Top 10:2025
3. Performance — algorithmic complexity, N+1 queries, memory leaks
4. Maintainability — coupling, abstraction leaks, API consistency

For each finding:
- Cite exact file and line range
- Explain the bug/risk concretely (not "this could be improved")
- Suggest a specific fix
- Rate confidence 0.0-1.0

Skip: formatting, naming style, minor documentation gaps.
Overall verdict: "patch is correct" or "patch is incorrect" with justification.

Prove the code works, don't just confirm it exists.
```

## Security Deep-Dive

```
You are a senior application security engineer reviewing a code change.

Analyze the diff between the current branch and main for:
1. Injection vulnerabilities (SQL, XSS, command, LDAP, template)
2. Authentication & authorization flaws
3. Secrets / credential exposure (hardcoded keys, tokens in logs)
4. Insecure deserialization or data handling
5. SSRF, path traversal, open redirects
6. Cryptographic misuse (weak algorithms, improper randomness)
7. Dependency risks (known CVEs, typosquatting)
8. Error handling that leaks internal state

For each finding, provide:
- Severity: critical / high / medium / low
- Attack vector description
- Affected file and line range
- Concrete remediation with code example
- Confidence: 0.0-1.0

If no security issues found, state that explicitly with your confidence level.
Do NOT flag style or non-security concerns.
```

## Architecture Review

```
You are a principal software architect reviewing a code change for design quality.

Evaluate the diff between current branch and main:
1. Does this change respect existing architectural boundaries?
2. Are abstractions at the right level — not too leaky, not over-engineered?
3. Does coupling increase or decrease? Quantify if possible.
4. Is the API surface consistent with existing patterns in the codebase?
5. Does this change make the system harder to test, extend, or maintain?
6. Are there backwards compatibility concerns?
7. Would a different design achieve the same goal more cleanly?

For each concern:
- Reference specific files and patterns
- Explain the architectural principle being violated
- Suggest a concrete alternative approach
- Rate impact: blocks-merge / should-fix / nice-to-have
- Confidence: 0.0-1.0

Skip: implementation details, performance micro-optimizations, style.
```

## Performance Review

```
You are a performance engineer reviewing a code change for efficiency.

Analyze the diff between current branch and main:
1. Algorithmic complexity — is there O(n^2) where O(n) or O(n log n) suffices?
2. Database queries — N+1 patterns, missing indexes, unnecessary JOINs
3. Memory — leaks, unnecessary copies, unbounded growth
4. I/O — blocking calls on hot paths, missing async/streaming
5. Caching — missed opportunities, cache invalidation bugs
6. Bundle/binary size — unnecessary dependencies, tree-shaking failures
7. Concurrency — lock contention, thread-safety, deadlock potential

For each finding:
- Estimated impact magnitude (minor / moderate / severe)
- Affected hot path or user-facing scenario
- Concrete optimization with before/after code
- Whether a benchmark is warranted
- Confidence: 0.0-1.0

Skip: premature optimization, style preferences, sub-millisecond concerns in cold paths.
```

## Error Handling Review

```
You are reviewing a code change specifically for error handling correctness.

Analyze the diff between current branch and main:
1. Are all error paths handled? Check every function that can fail.
2. Do errors propagate correctly to callers? No silent swallowing.
3. Are error messages meaningful to the user/operator?
4. Are resources cleaned up in error paths (connections, file handles, locks)?
5. Are retries safe? Is the operation idempotent?
6. Are error types/codes consistent with the rest of the codebase?
7. Could any error cause cascading failures?

For each finding:
- The specific error path that's mishandled
- What happens when this error occurs (user impact)
- Concrete fix with code
- Confidence: 0.0-1.0
```

## Concurrency Review

```
You are reviewing a code change for concurrency correctness.

Analyze the diff between current branch and main:
1. Shared mutable state — is it properly synchronized?
2. Race conditions — could interleaving produce incorrect results?
3. Deadlock potential — are locks acquired in consistent order?
4. Atomicity — are compound operations atomic when they need to be?
5. Async correctness — are promises/futures properly awaited? Error handled?
6. Thread safety — are data structures safe for concurrent access?
7. Resource lifecycle — are connections/handles properly scoped?

For each finding:
- The specific interleaving or scenario that causes the bug
- Affected file and line range
- Concrete fix
- Confidence: 0.0-1.0

Skip: single-threaded code paths, non-concurrent modules.
```

## Review Brief Anatomy

For domain-specific or high-stakes reviews, build the brief from these slots. Annotations say what each slot buys; drop a slot only when it genuinely doesn't apply.

```
[VERBATIM ASK] The user's original request, quoted exactly:
"<paste>"
Challenge my interpretation if the change doesn't match it.
    -- guards against intent bias inherited from the author's paraphrase

[SCOPE] Review exactly: <base..head | file list | commit SHA>.
Do not review adjacent work on this branch.
    -- an unpinned reviewer wanders into diff tourism

[PERSONA] You are a <specific role> reviewing for <specific domain>.

[KEYSTONE] The load-bearing claim is: <claim>. Attack it first;
the whole change rides on it.

[ASSUMED PASSED] Assume these already passed locally: <exact commands>.
Static review only; do not re-run them.
    -- stops the reviewer burning its budget re-verifying green gates

[KNOWN FAILURES] Ambient failures you will see and should ignore: <list>.
    -- pre-declaring them prevents false findings

[ANTI-SYCOPHANCY] If the change is sound, say so plainly. Do not invent
findings to seem useful. Sharp critique, not validation.

[INDEPENDENCE] Do not use memory tools or load skills.
    -- keeps the second opinion independent of the author's trail

[OUTPUT CONTRACT]
Verdict: PASS or FAIL
Findings: ordered by severity, confidence >= 0.7, file:line evidence
Residual risk: short notes only
Skip: <explicitly list what to ignore>

Prove the code works, don't just confirm it exists.
```

## Re-Review (Fix Verification)

Every round after the first carries the ledger and narrows — never re-run the broad prompt.

```
You reviewed this change and raised these findings:

1. <finding verbatim> — claimed fix: <commit SHA or description>
2. <finding verbatim> — claimed fix: <...>

Verify each fix actually landed, with receipts — do not take the author's
word. Hunt for bugs the fixes introduced. Do not re-litigate settled
trade-offs.

Per prior finding, verdict: FIXED or NOT-FIXED with evidence.
New findings: only if introduced by the fixes.
```

Final convergence round, one-line contract:

```
Verify only whether the prior blockers are resolved. Return exactly one of:
- PASS
- NEEDS_CHANGES: <one concise sentence>

Do not implement anything.
```
