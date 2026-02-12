# Software Requirements Specification (SRS)

Project: ReSkin AI  
Primary language: Python  
Version: 1.0  
Date: 2026-02-12  
Owner: Founder / Product + Engineering Lead

ReSkin AI is operated as a safety-critical identity product.  
Requirements in this document must protect user dignity, privacy, emotional safety, and system reliability.

## 1. Introduction

### 1.1 Purpose
This SRS defines functional and non-functional requirements for ReSkin AI MVP and pilot phase. It is the baseline for engineering, testing, and acceptance decisions.

### 1.2 Scope
ReSkin AI provides scar-aware AI tattoo concept co-creation for users and tattoo artists with a privacy-first and safety-aware workflow.

### 1.3 Intended audience
- Product owner
- Python engineers
- QA and validation
- Safety/privacy reviewers
- Pilot partners (artists, community organizations)

### 1.4 References
- `docs/proposal/RESKINAI_PROPOSAL_V1.md`
- `docs/scmp/SCMP.md`
- `docs/spmp/SPMP.md`

### 1.5 Definitions
- User: person with visible scar using concept generation and collaboration workflow.
- Artist: tattoo professional invited by user to review concepts.
- Concept: AI-generated tattoo design draft.
- Safety filter: policy controls that block unsafe requests or outputs.
- Deletion workflow: user-initiated process to remove data and generated assets.

## 2. Overall Description

### 2.1 Product perspective
ReSkin AI is a web-based system with:
- Python backend services.
- Client UI for users and artists.
- AI model provider integration for image generation.
- Secure storage for consented uploads and generated outputs.

### 2.2 Product functions (high-level)
- Consent and onboarding
- Scar image upload and preference capture
- Scar-aware concept generation
- Concept comparison, feedback, and selection
- User-to-artist collaboration handoff
- Safety, privacy, and deletion controls
- Audit and operational observability

### 2.3 User classes
- `U1` End User (primary)
- `U2` Tattoo Artist
- `U3` System Admin / Operator (small internal team)

### 2.4 Operating environment
- `DEV`: synthetic/anonymized data only
- `STAGING`: production-like validation without raw production data
- `PROD`: restricted access and audited changes only

### 2.5 Constraints
- Product is non-medical; no diagnosis or treatment claims.
- Sensitive user imagery requires strict privacy controls.
- MVP runs with small team and managed model APIs.
- Python-first toolchain and services.

### 2.6 Assumptions and dependencies
- Managed model/image generation APIs available.
- Secure object storage available for uploads/results.
- Target users and artists can be recruited in pilot cohorts.

## 3. Functional Requirements

Requirement IDs use `FR-###`. Priority values: `MUST`, `SHOULD`, `COULD`.

### 3.1 Onboarding, identity, and consent

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-001 | System shall provide user onboarding with explicit non-medical disclaimer acceptance. | MUST | User cannot proceed to upload until disclaimer accepted. |
| FR-002 | System shall provide explicit consent capture before scar image upload. | MUST | Consent timestamp and policy version are stored per upload session. |
| FR-003 | System shall support anonymous mode for users who do not want profile identity exposure. | SHOULD | Anonymous users can complete generation and handoff with pseudonymous identifier. |
| FR-004 | System shall support role separation for user, artist, and admin views. | MUST | Each role sees only authorized screens and data. |
| FR-005 | System shall enforce age gate for legal tattoo eligibility based on configured jurisdiction policy. | SHOULD | Under-threshold users are blocked with clear message. |

### 3.2 User profile and preference capture

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-006 | System shall capture design preferences including style, motif, meaning keywords, and avoid-list. | MUST | Preference form values are persisted and retrievable for the session. |
| FR-007 | System shall allow users to edit preferences and regenerate concepts. | MUST | Changed preferences produce a new generation request version. |
| FR-008 | System shall support localization-ready content fields for multilingual UX. | SHOULD | Preference labels and prompts are configurable by locale. |

### 3.3 Scar image upload and preprocessing

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-009 | System shall accept image upload in allowed formats (JPEG, PNG, WEBP) with size limits. | MUST | Unsupported format or oversize upload is rejected with actionable error. |
| FR-010 | System shall run upload validation and malware scanning before processing. | MUST | Unsafe file is quarantined and not sent to generation pipeline. |
| FR-011 | System shall bind each uploaded image to consent record and owner identity (or anonymous token). | MUST | Upload records include consent ID and actor ID/token. |
| FR-012 | System shall support user preview and crop/region marking before generation. | SHOULD | User can confirm marked region before submission. |

### 3.4 AI concept generation

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-013 | System shall generate multiple scar-aware concept variants from user inputs and uploaded image. | MUST | At least one valid concept is returned or structured failure response provided. |
| FR-014 | System shall attach generation metadata (model version, prompt version, safety policy version) to each concept set. | MUST | Metadata is stored and retrievable for audit. |
| FR-015 | System shall enforce safety filters on prompts and outputs prior to user display. | MUST | Blocked content is not shown; user receives safe fallback message. |
| FR-016 | System shall support a bounded retry policy on generation failures. | MUST | One automatic retry occurs before fail response. |
| FR-017 | System shall provide user-visible progress state for generation requests. | SHOULD | UI shows queued/running/completed/failed states. |

### 3.5 Concept management and decision support

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-018 | System shall allow users to save and organize generated concepts by session. | MUST | Saved concepts remain accessible for authorized session/user. |
| FR-019 | System shall allow side-by-side comparison of selected concepts. | SHOULD | User can compare at least two concepts in one view. |
| FR-020 | System shall collect structured feedback (like/dislike/reason tags) per concept. | MUST | Feedback events are stored and tied to concept ID. |
| FR-021 | System shall allow users to mark one or more concepts as handoff candidates to artists. | MUST | Marked concepts are visible in artist handoff package. |

### 3.6 Artist collaboration workflow

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-022 | System shall allow user-authorized artist invitation via secure link or account mapping. | MUST | Artist cannot view data without explicit user authorization. |
| FR-023 | System shall provide artists a collaboration workspace with approved concepts and user notes. | MUST | Artist sees only user-approved artifacts. |
| FR-024 | System shall support artist feedback notes on feasibility and adaptation suggestions. | MUST | Feedback is versioned and visible to user. |
| FR-025 | System shall maintain version history for user and artist collaboration updates. | SHOULD | Each update stores author and timestamp. |
| FR-026 | System shall allow users to revoke artist access at any time. | MUST | Revoked artist immediately loses access to user assets. |

### 3.7 Safety and emotional protection

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-027 | System shall display emotional safety notice before first generation and provide skip/exit controls. | MUST | User can exit flow in one action from generation step. |
| FR-028 | System shall block disallowed content classes (self-harm encouragement, hate, explicit violence). | MUST | Violating prompts/outputs are blocked and logged. |
| FR-029 | System shall provide safety event logging for blocked content and policy actions. | MUST | Safety events include severity and policy rule ID. |

### 3.8 Privacy, security, and data rights

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-030 | System shall allow users to request deletion of uploaded images and generated concepts. | MUST | Deletion request completes and returns confirmation status. |
| FR-031 | System shall enforce environment-aware data isolation (`dev`, `staging`, `prod`). | MUST | Data from one environment is inaccessible from another without approved migration path. |
| FR-032 | System shall log access to sensitive assets for auditability. | MUST | Access logs include actor, resource, action, and timestamp. |
| FR-033 | System shall support configurable retention windows for uploaded images and outputs. | MUST | Records expire per policy with verifiable deletion job results. |

### 3.9 Administration and operations

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-034 | System shall provide admin capability to disable generation pipeline or specific model routes during incidents. | MUST | Admin action takes effect without redeploy. |
| FR-035 | System shall expose operational metrics required for SLO monitoring. | MUST | Availability, latency, and failure metrics are queryable. |
| FR-036 | System shall support incident severity tagging for operational events (`SEV0` to `SEV3`). | MUST | Incident records store severity and lifecycle state. |

## 4. External Interface Requirements

### 4.1 User interface
- Web UI shall be responsive on desktop and mobile breakpoints.
- UI shall clearly distinguish user and artist workspaces.
- UI shall provide clear consent, safety, and deletion controls.

### 4.2 API interface
- Backend shall expose versioned HTTPS APIs (`/api/v1/...`).
- API responses shall use structured error codes and human-readable messages.
- Authentication and authorization checks shall be enforced for protected routes.

### 4.3 AI provider interface
- System shall invoke approved model endpoints with configured policy constraints.
- Provider timeout, retry, and failover behavior shall be configurable.
- Generation requests/responses shall be recorded with model registry metadata.

### 4.4 Storage and messaging interface
- Sensitive media shall be stored in encrypted object storage.
- Deletion workflows shall propagate to storage and metadata stores.
- Optional async queue may be used for generation jobs and deletion tasks.

## 5. Non-Functional Requirements

Requirement IDs use `NFR-###`.

### 5.1 Performance and scalability

| ID | Requirement | Target |
|---|---|---|
| NFR-001 | API availability | >= 99.5% monthly |
| NFR-002 | Generation latency | P95 < 12 seconds |
| NFR-003 | Retry behavior | 1 automatic retry for failed generation request |
| NFR-004 | Pilot load support | Support at least 100 daily generation requests in MVP pilot without critical degradation |

### 5.2 Security and privacy

| ID | Requirement | Target |
|---|---|---|
| NFR-005 | Data encryption | Encrypt sensitive data in transit and at rest |
| NFR-006 | Access control | Least privilege, role-based access for all sensitive resources |
| NFR-007 | Auditability | Sensitive access events are logged and queryable |
| NFR-008 | Secret management | No secrets in source repo; managed secret store required |

### 5.3 Safety and ethical behavior

| ID | Requirement | Target |
|---|---|---|
| NFR-009 | Unsafe content prevention | Safety filters applied to prompts and outputs before user display |
| NFR-010 | Incident readiness | Operational incidents classified and handled by `SEV0-SEV3` process |
| NFR-011 | Non-medical compliance | Non-medical disclaimer shown at onboarding and relevant flows |

### 5.4 Reliability and recoverability

| ID | Requirement | Target |
|---|---|---|
| NFR-012 | Error budget policy | Enforced as defined in SCMP when budget is exhausted |
| NFR-013 | Backup/recovery readiness | Ability to restore from tagged baseline in clean environment |
| NFR-014 | Graceful failure | User receives actionable failure messages without data corruption |

### 5.5 Maintainability and observability

| ID | Requirement | Target |
|---|---|---|
| NFR-015 | Code quality gates | Lint and tests must pass in CI before merge |
| NFR-016 | Traceability | Behavior-impacting model/prompt changes require model registry record |
| NFR-017 | Decision memory | Architecture-impacting decisions documented as ADRs |
| NFR-018 | Telemetry | Metrics for latency, error rates, safety blocks, and deletion success are available |

## 6. Data Requirements

### 6.1 Core entities
- UserAccount / AnonymousSession
- ArtistProfile
- ConsentRecord
- UploadedImage
- PreferenceProfile
- GenerationRequest
- ConceptAsset
- CollaborationNote
- SafetyEvent
- AuditEvent
- DeletionRequest

### 6.2 Data classification
- High sensitivity: scar images, user identity attributes, consent and audit records.
- Medium sensitivity: preferences, concept feedback, collaboration notes.
- Low sensitivity: aggregated metrics and anonymized analytics.

### 6.3 Retention and deletion
- Retention windows must be configurable by policy and environment.
- User deletion request must remove or anonymize associated artifacts per policy.
- Deletion jobs must produce verifiable execution logs.

## 7. System Constraints and Compliance

### 7.1 Technical constraints
- Python 3.11+ runtime for backend services.
- Use environment isolation as defined in SCMP.
- Use approved model provider interfaces for MVP.

### 7.2 Regulatory and policy constraints
- Product claims must remain non-medical.
- Privacy controls must meet applicable data protection obligations in launch region.
- Incident reporting requirements follow SCMP severity model.

## 8. Verification and Validation

### 8.1 Test levels
- Unit testing for domain logic and validation rules.
- Integration testing for API, generation pipeline, storage, deletion flow.
- End-to-end testing for user and artist workflows.
- Security/safety testing for blocked prompts, permission boundaries, and data deletion.

### 8.2 Entry/exit criteria for MVP release
- All MUST requirements implemented or formally deferred with approval.
- All critical/high defects resolved or accepted with mitigation.
- NFR baseline targets measured in staging with documented evidence.
- Privacy and safety checks pass release checklist.

### 8.3 Requirement traceability
See `docs/srs/REQUIREMENTS_TRACEABILITY_MATRIX.md` for objective-to-requirement and requirement-to-validation mapping.

## 9. Out of Scope (MVP)

- Social feed or public sharing platform.
- In-app clinical counseling functionality.
- Fully automated tattoo execution recommendation without artist collaboration.
- Advanced marketplace billing and payout automation.

## 10. Open Decisions

- Initial core segment final lock (for example post-mastectomy users first).
- Default retention window value for production launch.
- Region-first launch (CN-first or EN/global-first).
- Initial monetization sequence (B2C-first vs studio-first).

## 11. Versioning and Change Control

- SRS updates must follow change control in SCMP and SPMP.
- Requirement ID stability must be preserved across versions.
- Any deleted requirement must be marked as deprecated with rationale.

