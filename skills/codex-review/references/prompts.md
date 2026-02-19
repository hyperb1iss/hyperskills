# Codex Review Prompt Templates

Copy-paste ready prompt templates for each review pass. All designed for `gpt-5.3-codex` at `reasoningEffort: "xhigh"`.

## General Review (for `review` tool)

Use as the `prompt` parameter with the Codex **review** tool:

```
Review this change with extreme thoroughness. Prioritize:
1. Correctness — logic errors, edge cases, null handling, race conditions
2. Security — injection, auth gaps, secrets exposure, OWASP Top 10
3. Performance — algorithmic complexity, N+1 queries, memory leaks
4. Maintainability — coupling, abstraction leaks, API consistency

For each finding:
- Cite exact file and line range
- Explain the bug/risk concretely (not "this could be improved")
- Suggest a specific fix
- Rate confidence 0.0-1.0

Skip: formatting, naming style, minor documentation gaps.
Overall verdict: "patch is correct" or "patch is incorrect" with justification.
```

## Security Deep-Dive (for `codex` tool)

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

## Architecture Review (for `codex` tool)

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

## Performance Review (for `codex` tool)

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

## Error Handling Review (for `codex` tool)

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

## Concurrency Review (for `codex` tool)

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

## Custom Template Skeleton

For domain-specific reviews, use this skeleton:

```
You are a [specific role] reviewing a code change for [specific domain].

Analyze the diff between current branch and main:
1. [Specific check 1]
2. [Specific check 2]
3. [Specific check 3]
...

For each finding:
- [Required output field 1]
- [Required output field 2]
- Affected file and line range
- Concrete fix with code example
- Confidence: 0.0-1.0

Skip: [explicitly list what to ignore].
```
