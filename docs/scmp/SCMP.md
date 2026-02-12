# Software Configuration Management Plan (SCMP)

Project: ReSkin AI  
Primary language: Python  
Version: 1.1  
Date: 2026-02-12  
Owner: Founder / Project Lead

ReSkin AI is operated as a safety-critical identity product.  
Engineering and operational controls must prioritize user dignity, privacy, emotional safety, and traceable decision making.

## 1. Purpose

This SCMP defines how ReSkin AI controls source code, documentation, model behavior, environments, and releases so the system remains reproducible, auditable, and safe as the team scales.

## 2. Scope

This plan applies to:
- Python application code and tests.
- Product and compliance documents.
- Prompt templates and model configuration files.
- Data schemas and non-production sample data.
- CI/CD workflows and deployment scripts.
- Release artifacts and change logs.
- Environment configuration and operations runbooks.

This plan does not cover:
- Medical diagnosis logic (project is non-medical).
- Raw personal user data retention policy details beyond repository governance.

## 3. SCM Objectives

- Ensure every production change is traceable to an approved request.
- Keep builds and environments reproducible across machines.
- Prevent unauthorized or unsafe changes to sensitive modules.
- Define measurable reliability and incident response targets.
- Support fast iteration while maintaining release quality.

## 4. Roles and Responsibilities

### 4.1 Core roles
- `SCM Owner` (initially founder): owns this SCMP and enforces process.
- `Maintainer`: reviews and merges pull requests.
- `Contributor`: implements changes with tests and docs.
- `Release Owner`: creates release candidate, tags release, publishes notes.
- `Incident Commander`: leads active incident response.
- `Comms Owner`: manages incident communications and updates.

In early stage, one person may hold multiple roles, but responsibilities remain separate in checklist form.

### 4.2 Change approval authority
- Low-risk changes (docs, non-critical UI text): 1 reviewer.
- Medium-risk changes (feature logic, API behavior): 1 reviewer + passing CI.
- High-risk changes (auth, privacy, deletion, billing, safety filters): 2 reviewers or external advisor sign-off.
- Incident hotfixes: Incident Commander + SCM Owner approval after containment.

## 5. Configuration Items (CIs)

Every CI must be version controlled or explicitly excluded with rationale.

### 5.1 CI categories
- `SRC`: Python source files under `src/` (or app root in current stage).
- `TEST`: unit/integration tests under `tests/`.
- `DOC`: proposal, design docs, policies, runbooks.
- `CFG`: config files (`pyproject.toml`, `.env.example`, lint/test config).
- `OPS`: CI workflows, scripts, deployment definitions.
- `ML`: prompt templates, model routing config, evaluation settings.
- `MODEL-REGISTRY`: versioned model behavior metadata.
- `DATA-SCHEMA`: schema definitions and anonymized fixtures only.

### 5.2 Naming and directory conventions
- Branch names:
  - `feature/<short-name>`
  - `fix/<short-name>`
  - `chore/<short-name>`
  - `release/<version>`
  - `hotfix/<short-name>`
- Python package layout target:
  - `src/reskin_ai/`
  - `tests/`
  - `docs/`
  - `scripts/`
- Files use lowercase with underscores when possible.

### 5.3 Items excluded from version control
- Virtual environments (`.venv/`).
- Secrets and private keys.
- Raw personally identifiable images or personal health-related data.
- Local IDE state files not needed for team workflows.

## 6. Environment Model and Isolation Strategy

ReSkin AI uses strict `dev`, `staging`, and `prod` separation.

### 6.1 DEV
- Purpose: rapid iteration, local debugging, feature development.
- Data policy: synthetic data or anonymized fixtures only.
- Access: developers and maintainers.
- Controls: relaxed scale/performance settings, strict secret handling still required.

### 6.2 STAGING
- Purpose: production-like validation before release.
- Data policy: no raw production personal data.
- Access: maintainers, release owner, designated testers.
- Required tests:
  - Permission testing.
  - Deletion workflow testing.
  - Safety filter regression checks.
  - Release candidate verification.

### 6.3 PROD
- Purpose: live user service.
- Data policy: production policy only; no test imports.
- Access: restricted; least privilege enforced.
- Change policy: audited changes only through approved release/hotfix workflow.

### 6.4 Isolation guardrails (mandatory)
- Separate cloud project/account per environment when possible.
- Separate credentials and secret scopes per environment.
- Environment-specific database and storage buckets with explicit naming.
- Hard guard in app startup: reject destructive/test commands in `prod`.
- CI/CD promotion path only: `dev -> staging -> prod` (no direct `dev -> prod`).

These controls are required to prevent incidents such as running tests against production systems.

## 7. Baselines

A baseline is a reviewed, frozen snapshot used as a reference.

### 7.1 Baseline types
- `DEV Baseline`: end of each sprint/iteration.
- `RC Baseline` (Release Candidate): code freeze for release testing.
- `PROD Baseline`: tagged version deployed to production.
- `HOTFIX Baseline`: emergency patch based on a production tag.

### 7.2 Baseline records
Each baseline record must include:
- Baseline ID (for example `BL-2026-02-12-RC1`).
- Git tag/commit.
- Scope of included changes.
- Verification status.
- Approver and date.

## 8. Versioning and Branching Strategy

### 8.1 Versioning
- Use Semantic Versioning: `MAJOR.MINOR.PATCH`.
- Pre-release tags allowed: `-alpha.N`, `-beta.N`, `-rc.N`.
- Release tags format: `vX.Y.Z`.

### 8.2 Branch policy
- `main` is always releasable and protected.
- Work happens on short-lived feature branches.
- Merge strategy: squash merge by default for clean history.
- Direct push to `main` is disabled.

### 8.3 Commit message convention
- Use Conventional Commits:
  - `feat:`
  - `fix:`
  - `docs:`
  - `refactor:`
  - `test:`
  - `chore:`

## 9. Change Control Process

### 9.1 Change lifecycle
1. Create issue/change request with problem, scope, risk, rollback plan.
2. Implement on branch with tests/docs updates.
3. Open pull request linked to request.
4. Run CI checks and review.
5. Approve and merge.
6. Update changelog and baseline record if release-related.

### 9.2 Emergency changes (code hotfix)
- Allowed only for production incidents.
- Process:
  1. Branch from latest production tag.
  2. Apply minimal fix.
  3. Run focused verification.
  4. Release hotfix tag.
  5. Back-merge to `main`.
  6. Publish incident note within 24 hours.

### 9.3 Required PR checklist
- Linked issue/change request.
- Tests added/updated or justified.
- Backward compatibility impact stated.
- Security/privacy impact reviewed.
- Rollback method documented.

## 10. Build, Test, and Release Controls (Python-first)

### 10.1 Standard toolchain
- Python: 3.11+ (pin exact runtime in CI).
- Package/dependency management: `pip` with pinned lock strategy.
- Lint/format: `ruff`.
- Tests: `pytest`.
- Optional type checks: `mypy` for service modules.

### 10.2 CI minimum gates
- Install dependencies from lock file.
- Lint pass.
- Unit tests pass.
- Security scan of dependencies (`pip-audit` or equivalent) on release branches.
- Environment target check (release jobs cannot deploy from non-release branches).

### 10.3 Release process
1. Create `release/<version>` branch.
2. Freeze feature changes; bug fixes only.
3. Run full CI and release checklist.
4. Tag `vX.Y.Z` on approved commit.
5. Publish release notes and baseline record.

## 11. Reliability Targets (SLO)

Maintainable service means predictable behavior with explicit service targets.

### 11.1 Initial SLOs (v1 targets)
- Availability target: `99.5%` monthly.
- P95 generation latency: `< 12s`.
- Failed generation retry policy: `1` automatic retry.
- Safety filter availability: same as primary API availability.

### 11.2 Error budget policy
- If monthly error budget is exhausted:
  - Pause non-critical feature releases.
  - Prioritize reliability and safety fixes.
  - Resume feature velocity only after two stable weeks.

## 12. Incident Management (Operational)

Emergency code change is only one part of incident response. ReSkin AI also manages operational safety and privacy incidents.

### 12.1 Severity classification
- `SEV0`: confirmed privacy breach or unauthorized personal data exposure.
- `SEV1`: safety violation (for example unsafe generation escaping safeguards).
- `SEV2`: major degradation (for example frequent failed generations, critical workflow broken).
- `SEV3`: minor defect with workaround.

### 12.2 Response targets
- `SEV0`: acknowledge in 15 minutes, containment start in 30 minutes.
- `SEV1`: acknowledge in 30 minutes, mitigation start in 60 minutes.
- `SEV2`: acknowledge in 2 hours, mitigation same business day.
- `SEV3`: triage within 2 business days.

### 12.3 Incident roles and authority
- Incident Commander: owns technical response and containment execution.
- Comms Owner: owns internal/external status updates.
- Rollback authority: Incident Commander + SCM Owner.
- Privacy/legal escalation: required for all `SEV0`.

### 12.4 Incident workflow
1. Detect and classify incident severity.
2. Contain impact (disable affected feature/model route if needed).
3. Communicate status and ETA.
4. Recover service.
5. Produce post-incident report within 48 hours for `SEV0/SEV1` and within 5 business days for `SEV2`.

## 13. AI Model, Prompt, and Safety Configuration Governance

Prompt changes are product changes and may be legal/safety changes.

### 13.1 Model registry requirement
Any model behavior change must create a registry entry including:
- Model provider and model version.
- Runtime parameters (for example temperature, top_p).
- System prompt hash and prompt template version.
- Safety filter version and policy set.
- Evaluation dataset version.
- Evaluation results (quality, safety, latency).
- Approval, date, and rollout scope.

### 13.2 Change policy
- Prompt/model config changes require PR review like code.
- Behavior-impacting changes require staging evaluation evidence.
- Never deploy model and prompt changes to prod without registry entry.
- Never store raw user scar photos in repository.

## 14. Architecture Decision Records (ADR)

Maintainability requires decision memory, not only clean code.

### 14.1 ADR policy
- Significant architecture decisions must be recorded as ADRs.
- ADRs live under `docs/scmp/adr/`.
- File naming: `ADR-XXXX-short-title.md`.

### 14.2 Required ADR topics
- Model hosting choice (managed API vs self-hosted).
- Data storage and encryption design.
- Service boundaries (for example separate artist portal service).
- Safety enforcement architecture.

## 15. Configuration Status Accounting

The team tracks:
- Open vs closed change requests.
- PR cycle time and review time.
- Defect escape count per release.
- Release frequency and rollback incidents.
- SLO burn rate and incident counts by severity.
- Model registry updates per release.

Records are stored in:
- `docs/scmp/` for formal records.
- Issue tracker for operational history.

## 16. Verification and Audits

### 16.1 Functional verification
- New behavior must be covered by tests or documented manual test evidence.

### 16.2 Configuration audit
Before each production release, verify:
- Tag points to approved commit.
- Changelog matches merged PRs.
- Dependency list is pinned and scanned.
- Privacy-sensitive changes reviewed.
- SLO-impacting changes include capacity/performance check.
- Model registry entry exists for behavior-impacting AI changes.

### 16.3 Quarterly process audit
- Review whether SCMP still matches actual workflow.
- Record deviations and update SCMP version if needed.

## 17. Security and Access Control

- Enforce least privilege for repository and deployment credentials.
- Require MFA on code hosting accounts.
- Secrets only in secret manager or CI secret store.
- Rotate keys/tokens on schedule or after contributor offboarding.

## 18. Backup and Recovery

- Repository mirrored daily to a second remote (if available).
- Release artifacts retained per release policy.
- Recovery drill every 6 months: restore from a tagged release to clean environment.

## 19. Training and Onboarding

Every new contributor must complete:
- Repository setup and coding standards.
- Branch/PR workflow.
- Privacy and safety expectations for AI + scar-related content.
- Incident severity model and response workflow.
- Release checklist walk-through.

## 20. SCMP Maintenance

- SCMP is versioned in Git under `docs/scmp/SCMP.md`.
- Any process change requires a PR labeled `process-change`.
- Owner reviews SCMP at least once per quarter.

## 21. Immediate Adoption Plan (next 2 weeks)

1. Confirm this SCMP as working baseline (v1.1).
2. Add issue templates and PR template aligned to Section 9.
3. Add CI workflow for lint + tests + deployment target checks.
4. Introduce model registry and incident report templates.
5. Create first ADR entries for model hosting and data storage.
6. Run first mini-audit after initial MVP sprint.

