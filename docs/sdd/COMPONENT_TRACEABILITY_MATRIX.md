# Component Traceability Matrix

Project: ReSkin AI  
Version: 1.0  
Date: 2026-02-12

## 1. Requirement to Component Mapping

| Requirement IDs | Primary Components | Secondary Components |
|---|---|---|
| FR-001, FR-002 | CMP-02 Consent Service | CMP-01 API Gateway |
| FR-003, FR-004, FR-005 | CMP-01 API Gateway/Auth | CMP-10 Audit Service |
| FR-006, FR-007, FR-008 | CMP-03 Preference Service | CMP-01 API Gateway |
| FR-009, FR-010, FR-011, FR-012 | CMP-04 Asset Ingestion | CMP-02 Consent Service, CMP-10 Audit Service |
| FR-013, FR-014, FR-016, FR-017 | CMP-05 Generation Orchestrator | CMP-06 Safety Engine, CMP-10 Audit Service |
| FR-015, FR-028, FR-029 | CMP-06 Safety Filter Engine | CMP-05 Generation Orchestrator |
| FR-018, FR-019, FR-020, FR-021 | CMP-07 Concept Management | CMP-05 Generation Orchestrator |
| FR-022, FR-023, FR-024, FR-025, FR-026 | CMP-08 Collaboration Service | CMP-01 API Gateway, CMP-10 Audit Service |
| FR-030, FR-033 | CMP-09 Privacy and Deletion Service | CMP-10 Audit Service |
| FR-031 | CMP-01 API Gateway/Auth | Deployment isolation controls |
| FR-032 | CMP-10 Audit and Access Log Service | All components |
| FR-034, FR-035, FR-036 | CMP-11 Operations Control Service | CMP-10 Audit Service |

## 2. NFR to Design Control Mapping

| NFR | Design Controls |
|---|---|
| NFR-001, NFR-002, NFR-003 | Orchestrator timeout/retry, metrics instrumentation, worker queue |
| NFR-004 | Capacity envelope in staging load tests, queue backpressure |
| NFR-005, NFR-006, NFR-007, NFR-008 | Encryption, RBAC, audit logs, secret manager |
| NFR-009, NFR-010, NFR-011 | Safety engine, incident workflow hooks, disclaimer gating |
| NFR-012, NFR-013, NFR-014 | Error budget policy, recovery drill support, graceful failure responses |
| NFR-015, NFR-016, NFR-017, NFR-018 | CI quality gates, model registry metadata, ADRs, telemetry stack |

## 3. Change Impact Rule

If a component design changes:
1. Update impacted SRS requirement mappings in this file.
2. Update `docs/sdd/SDD.md` component section.
3. Update related tests and operational checks.
4. Record in changelog and relevant baseline record.

