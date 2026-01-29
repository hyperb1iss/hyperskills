---
name: security
description: Use this skill for security reviews, threat modeling, compliance work, or incident response. Activates on mentions of security audit, vulnerability, OWASP, threat model, zero trust, SOC 2, HIPAA, GDPR, compliance, incident response, SBOM, supply chain security, or secrets management.
---

# Security Operations

Frameworks and checklists for secure systems.

## Zero Trust Principles

1. Never trust, always verify
2. Assume breach
3. Verify explicitly
4. Least privilege access
5. Micro-segmentation

## SLSA Framework (Supply Chain)

| Level | Requirements                             |
| ----- | ---------------------------------------- |
| 1     | Documentation of build process           |
| 2     | Hosted build platform, signed provenance |
| 3     | Hardened builds, 2-person review         |
| 4     | Hermetic, reproducible builds            |

## Threat Modeling (STRIDE)

| Threat                     | Example             | Mitigation                  |
| -------------------------- | ------------------- | --------------------------- |
| **S**poofing               | Fake identity       | Strong auth, MFA            |
| **T**ampering              | Modified data       | Integrity checks, signing   |
| **R**epudiation            | Deny actions        | Audit logs, non-repudiation |
| **I**nformation Disclosure | Data leak           | Encryption, access control  |
| **D**enial of Service      | Overload            | Rate limiting, scaling      |
| **E**levation of Privilege | Unauthorized access | Least privilege, RBAC       |

## OWASP Top 10 Checklist

- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection (SQL, NoSQL, OS, LDAP)
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Auth Failures
- [ ] A08: Software/Data Integrity Failures
- [ ] A09: Logging/Monitoring Failures
- [ ] A10: SSRF

## Secrets Management

**Never commit secrets.** Use environment-based injection (External Secrets Operator, Vault, cloud-native secret managers). Scan with `gitleaks` or `trufflehog` in CI.

## Supply Chain Security

- Generate SBOMs with Syft: `syft packages dir:. -o spdx-json`
- Scan with Grype: `grype sbom:sbom.spdx.json --fail-on high`
- Scan container images with Trivy: `trivy image <image> --severity HIGH,CRITICAL`
- Use distroless/Chainguard base images

## Incident Response Phases

1. **Detection & Analysis** -- Acknowledge alert, gather IOCs, determine scope, escalate if P1/P2
2. **Containment** -- Isolate systems, block malicious IPs, disable compromised accounts, preserve evidence
3. **Eradication** -- Remove malware/backdoors, patch vulnerabilities, reset credentials
4. **Recovery** -- Restore from clean backups, monitor for re-infection, gradual restoration
5. **Lessons Learned** -- Timeline reconstruction, root cause analysis, update playbooks

## Compliance Frameworks

| Framework     | Focus                           |
| ------------- | ------------------------------- |
| SOC 2 Type II | Service organization controls   |
| ISO 27001     | Information security management |
| HIPAA         | Protected health information    |
| GDPR          | EU data protection              |
| PCI DSS       | Payment card data               |

Use Vanta or Drata for continuous monitoring and automated evidence collection.
