---
name: audit-security
description: Run a security audit on the codebase
---

# Security Audit Command

Perform a comprehensive security review of the current codebase.

## Process

1. **Dependency Scan**

   ```bash
   # Check for known vulnerabilities
   pnpm audit
   # or
   npm audit
   ```

2. **Secret Detection**
   - Scan for hardcoded secrets
   - Check .env files not in .gitignore
   - Review environment variable handling

3. **Code Review**
   - OWASP Top 10 checklist
   - Authentication/authorization flows
   - Input validation
   - SQL/NoSQL injection points
   - XSS vectors

4. **Infrastructure Review**
   - HTTPS enforcement
   - Security headers
   - CORS configuration
   - Rate limiting

5. **Container Security** (if applicable)
   ```bash
   trivy image <image-name>
   ```

## Output Format

```markdown
# Security Audit Report

## Summary

- Critical: X
- High: X
- Medium: X
- Low: X

## Critical Issues

[Details and remediation]

## High Priority Issues

[Details and remediation]

## Recommendations

[Proactive improvements]
```

## Remediation

For each issue found:

1. Explain the vulnerability
2. Show the vulnerable code
3. Provide the fix
4. Verify the fix
