---
name: security
description: Use this skill for security reviews, threat modeling, compliance work, or incident response. Activates on mentions of security audit, vulnerability, OWASP, threat model, zero trust, SOC 2, HIPAA, GDPR, compliance, incident response, SBOM, supply chain security, or secrets management.
---

# Security Operations

Frameworks and checklists for secure systems. This skill is a triage map: use it to find the right review lens, then pull the authoritative standard for implementation detail.

## Zero Trust Principles

NIST SP 800-207 frames Zero Trust as removing implicit trust based on network location, asset ownership, or perimeter membership. Access decisions are resource-centered and continuously evaluated.

| Tenet                     | Review Question                                              |
| ------------------------- | ------------------------------------------------------------ |
| Resource-centric access   | Is the protected thing a specific app, service, or data set? |
| Per-session authorization | Is access granted for this request/session, not forever?     |
| Continuous evaluation     | Do identity, device posture, and behavior affect decisions?  |
| Least privilege           | Are permissions scoped to the minimum operation needed?      |
| Assume breach             | Can one compromised account/device move laterally?           |

**Do not equate Zero Trust with micro-segmentation.** Segmentation can help, but the security boundary is identity, policy, and resource access.

## SLSA 1.2 (Supply Chain)

As of Apr 26, 2026, SLSA 1.2 uses separate tracks. The old single SLSA 1-4 framing is retired; Build L4, hermetic builds, and reproducible builds are future-direction topics, not current requirements.

| Track  | Level | Meaning                                | Primary Protection        |
| ------ | ----- | -------------------------------------- | ------------------------- |
| Build  | L0    | No guarantees                          | None                      |
| Build  | L1    | Provenance exists                      | Mistakes, traceability    |
| Build  | L2    | Signed provenance from hosted platform | Tampering after build     |
| Build  | L3    | Hardened build platform                | Tampering during build    |
| Source | L1-L3 | Increasing trust in source revisions   | Source integrity controls |

For agent work, minimum practical target is Build L2 for releases: hosted CI, signed provenance, and consumer verification. Aim for Build L3 when release artifacts are high-trust dependencies.

## Threat Modeling (STRIDE)

| Threat                     | Example             | Mitigation                  |
| -------------------------- | ------------------- | --------------------------- |
| **S**poofing               | Fake identity       | Strong auth, MFA            |
| **T**ampering              | Modified data       | Integrity checks, signing   |
| **R**epudiation            | Deny actions        | Audit logs, non-repudiation |
| **I**nformation Disclosure | Data leak           | Encryption, access control  |
| **D**enial of Service      | Overload            | Rate limiting, scaling      |
| **E**levation of Privilege | Unauthorized access | Least privilege, RBAC       |

## OWASP Top 10:2025 Checklist

As of Apr 26, 2026, OWASP lists the 2025 release as current.

- [ ] A01: Broken Access Control
- [ ] A02: Security Misconfiguration
- [ ] A03: Software Supply Chain Failures
- [ ] A04: Cryptographic Failures
- [ ] A05: Injection
- [ ] A06: Insecure Design
- [ ] A07: Authentication Failures
- [ ] A08: Software or Data Integrity Failures
- [ ] A09: Security Logging and Alerting Failures
- [ ] A10: Mishandling of Exceptional Conditions

## Secrets Management

**Never commit secrets.** Use environment-based injection (External Secrets Operator, Vault, cloud-native secret managers). Scan with `gitleaks` or `trufflehog` in CI.

## Supply Chain Security

- Generate SBOMs with Syft: `syft packages dir:. -o spdx-json`
- Scan with Grype: `grype sbom:sbom.spdx.json --fail-on high`
- Scan container images with Trivy: `trivy image <image> --severity HIGH,CRITICAL`
- Use distroless/Chainguard base images

## Incident Response

NIST SP 800-61 Rev. 3 maps incident response into the CSF 2.0 lifecycle instead of treating response as a linear cleanup checklist.

| Function | Agent Checklist                                      |
| -------- | ---------------------------------------------------- |
| Govern   | Owners, severity policy, legal/comms paths are known |
| Identify | Assets, dependencies, data classes, and blast radius |
| Protect  | Preventive controls, backups, secrets rotation path  |
| Detect   | Alerts, logs, indicators, timelines, correlation     |
| Respond  | Containment, evidence preservation, eradication      |
| Recover  | Restore service, monitor recurrence, capture lessons |

## Compliance Frameworks

| Framework     | Focus                           |
| ------------- | ------------------------------- |
| SOC 2 Type II | Service organization controls   |
| ISO 27001     | Information security management |
| HIPAA         | Protected health information    |
| GDPR          | EU data protection              |
| PCI DSS       | Payment card data               |

Use Vanta or Drata for continuous monitoring and automated evidence collection.

## Anti-Patterns

| Anti-Pattern                          | Fix                                                        |
| ------------------------------------- | ---------------------------------------------------------- |
| Treating OWASP Top 10 as a full audit | Use it as a baseline; add abuse cases and data-flow review |
| Claiming "Zero Trust compliant"       | Name concrete controls and the resource they protect       |
| Calling SBOMs supply-chain security   | Pair SBOM with provenance, signing, and verification       |
| Doing security review after merge     | Threat-model before design freezes; scan continuously      |
| Ignoring recovery paths               | Test restore, key rotation, and evidence capture           |

## What This Skill is NOT

- Not legal or compliance advice.
- Not a replacement for current OWASP, NIST, SLSA, or framework-specific docs.
- Not a penetration testing methodology.
- Not sufficient for regulated environments without organization-specific controls.
