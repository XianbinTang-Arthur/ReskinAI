# Requirements Traceability Matrix (RTM)

Project: ReSkin AI  
Version: 1.0  
Date: 2026-02-12

## 1. Objective to Requirement Mapping

| Source Objective | Description | Mapped Requirements |
|---|---|---|
| Proposal H1 | Users will upload scar images with explicit privacy controls | FR-002, FR-009, FR-011, FR-030, FR-033, NFR-005, NFR-006 |
| Proposal H2 | AI concepting reduces first-consultation anxiety | FR-013, FR-017, FR-018, FR-019, FR-020, FR-027 |
| Proposal H3 | Artists adopt workflow if collaboration is efficient | FR-022, FR-023, FR-024, FR-025, FR-026 |
| Proposal H4 | Expression and user agency are core value | FR-006, FR-007, FR-018, FR-021, FR-027 |
| Proposal H5 | Workflow supports sustainable value delivery | FR-013, FR-021, FR-035, NFR-001, NFR-002 |
| SCMP Environment Isolation | Strict `dev/staging/prod` separation | FR-031, NFR-006, NFR-012 |
| SCMP Incident Model | Operational response for safety/privacy failures | FR-034, FR-036, NFR-010 |
| SCMP Model Governance | Model/prompt changes are controlled and traceable | FR-014, NFR-016, NFR-017 |
| SCMP SLO Targets | Predictable reliability baseline | NFR-001, NFR-002, NFR-003, NFR-012 |
| SPMP Milestone Goal | Pilot readiness and measurable outcomes | FR-035, NFR-018, Section 8 release criteria |

## 2. Requirement to Validation Mapping

| Requirement ID | Validation Type | Validation Artifact |
|---|---|---|
| FR-001 to FR-005 | Integration + E2E | Onboarding test suite, consent audit logs |
| FR-006 to FR-012 | Unit + Integration | Preference/upload tests, storage validation |
| FR-013 to FR-017 | Integration + Reliability | Generation pipeline tests, latency report |
| FR-018 to FR-021 | E2E | User concept workflow scenarios |
| FR-022 to FR-026 | E2E + Security | Artist authorization and revocation tests |
| FR-027 to FR-029 | Security + Safety | Prompt/output safety test pack, safety event logs |
| FR-030 to FR-033 | Integration + Audit | Deletion workflow tests, data retention logs |
| FR-034 to FR-036 | Operational + Incident Drill | Admin control tests, incident simulation report |
| NFR-001 to NFR-004 | Performance/Reliability | Staging load and SLO report |
| NFR-005 to NFR-008 | Security | Security checklist, secret scan, access audit |
| NFR-009 to NFR-011 | Safety/Compliance | Safety filter regression report, disclaimer checks |
| NFR-012 to NFR-014 | Reliability/Recovery | Error budget review, recovery drill report |
| NFR-015 to NFR-018 | Process/Observability | CI logs, model registry entries, ADR records, telemetry dashboards |

## 3. Change Impact Rule

If a requirement changes:
1. Update SRS requirement text.
2. Update this RTM mapping.
3. Update related test artifacts and acceptance evidence.
4. Record change in changelog and applicable baseline record.

