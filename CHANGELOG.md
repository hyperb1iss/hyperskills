# Changelog

## 3.13.0

- Add demo-reel, a skill that films the real product end to end and treats the reel as its acceptance test. The shot list doubles as the test plan, and every failed take becomes a fix before the whole reel is reshot. Bundled scripts handle deterministic 4K browser capture, sandboxed agent takes, contact sheets, and MP4 verification.
- Add two hyper-pr-review lenses: Necessity and Ownership, which runs first on platform work, and Seams and Test Credibility, for layer boundaries tested only against fakes. Existing lenses gain checks for unknown outcomes, hand-maintained mirrors that drift, and "dark" claims that are false on default paths. A new section keeps review evidence, approvals, and reply threads inspectable.
- Generate skill counts, the inventory, and marketplace metadata from source, and fail CI on drift. Each version now ships from a verified release PR, and an interrupted release can be rerun safely.

Releases prepared by the release workflow are recorded here. Earlier changes are documented in the repository history and the [September 2026 audit](docs/library-review-2026-09.md).
