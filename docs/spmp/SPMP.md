# Software Project Management Plan (SPMP)

Project: ReSkin AI  
Primary language: Python  
Version: 1.0  
Date: 2026-02-12  
Owner: Founder / Project Lead

ReSkin AI is operated as a safety-critical identity product.  
Project management decisions must prioritize user dignity, privacy, emotional safety, and delivery predictability.

## 1. Purpose

This SPMP defines how ReSkin AI plans, executes, monitors, and controls software delivery from MVP validation to early production readiness.

## 2. Scope

This plan covers:
- Product planning, scheduling, and milestone management.
- Team structure, role ownership, and decision governance.
- Budget and resource planning for MVP stage.
- Risk, quality, and communication management.
- Integration with SCMP controls for code/config/release governance.

This plan does not cover:
- Clinical protocols (ReSkin AI is non-medical).
- Long-term scale operations beyond first production phase.

## 3. Project Goals and Success Criteria

### 3.1 Business and impact goals
- Deliver a scar-aware AI concepting MVP for user-artist co-creation.
- Validate user value and emotional safety in controlled pilots.
- Establish credible governance for privacy, safety, and reliability.

### 3.2 Success criteria (first 6 months)
- MVP launch in closed pilot by end of Month 3.
- Complete >= 15 user-artist closed-loop pilot cases by end of Month 5.
- Maintain deletion workflow success rate at 100% in pilot runs.
- Achieve initial service targets defined in SCMP SLO section.

## 4. Assumptions and Constraints

### 4.1 Assumptions
- Founder-led team can execute product + engineering + early partnerships.
- Managed AI APIs are available for initial model capability.
- Target users and artists can be recruited through community channels.

### 4.2 Constraints
- Small team and budget.
- High privacy and emotional safety bar.
- Strong dependency on partner willingness and user trust.

## 5. Lifecycle and Delivery Model

### 5.1 Delivery approach
- Iterative delivery in 2-week sprints.
- Monthly milestone review.
- Evidence-based go/no-go checks at major gates.

### 5.2 Stage model
1. Stage A (Weeks 1-4): discovery hardening and prototype design.
2. Stage B (Weeks 5-12): MVP build and internal validation.
3. Stage C (Weeks 13-20): closed pilot execution and measurement.
4. Stage D (Weeks 21-24): readiness review and next-stage decision.

## 6. Work Breakdown Structure (WBS)

1. Product and research
- User interviews and journey mapping.
- MVP requirements and acceptance criteria.
- Pilot protocol and feedback loops.

2. Engineering and AI
- Python service/API implementation.
- Prompt/model routing and safety controls.
- Artist collaboration workflow support.

3. Platform and operations
- Environment setup (`dev`, `staging`, `prod-ready`).
- CI quality gates and release pipeline setup.
- Observability and incident preparedness.

4. Governance and compliance
- Privacy by design and consent flow verification.
- Data deletion and permission workflow validation.
- SCMP/SPMP process adoption and audit prep.

5. GTM and partnerships
- Recruit seed artists and pilot users.
- Partner outreach and onboarding.
- Case-story documentation with explicit consent.

## 7. Schedule and Milestones

### 7.1 Baseline timeline
- Month 1:
  - Finalize scope baseline and acceptance criteria.
  - Complete low-fidelity prototype and risk map.
- Months 2-3:
  - Build MVP and complete staging validation.
  - Start closed pilot intake.
- Months 4-5:
  - Run pilot cohort and close >= 15 user-artist cases.
  - Evaluate value, safety, and operational readiness.
- Month 6:
  - Conduct stage-gate review and publish continuation plan.

### 7.2 Stage-gate decisions
- Gate 1 (end of Month 1): scope lock for MVP.
- Gate 2 (end of Month 3): pilot entry approval.
- Gate 3 (end of Month 5): readiness to expand or iterate.
- Gate 4 (end of Month 6): strategy decision for next phase.

## 8. Organization and Staffing

### 8.1 Current model
- Founder as Project Manager + Product Lead + Technical Owner.

### 8.2 Planned support
- Advisor: scar-experienced tattoo specialist.
- Advisor: trauma-informed mental health specialist.
- Advisor: privacy/compliance specialist (part-time).

### 8.3 RACI (initial)
- Scope and roadmap: Founder (A/R), Advisors (C).
- Engineering delivery: Founder (A/R), future contributors (R).
- Safety and privacy review: Founder (A), advisors (C), maintainers (R when assigned).
- Release sign-off: Founder/SCM Owner (A), Maintainer (R).

## 9. Budget and Resource Plan

### 9.1 Cost categories
- AI inference and storage.
- Development tooling and infrastructure.
- User research and pilot operations.
- Compliance and advisory support.

### 9.2 Control policy
- Track planned vs actual spend monthly.
- Any unplanned spend >15% of monthly plan requires formal review.
- Freeze non-critical work if runway risk is identified.

## 10. Risk Management

### 10.1 Top project risks
- Privacy breach or sensitive data mishandling.
- Safety failure in generated outputs.
- Low pilot recruitment or weak partner participation.
- Delivery slippage due to founder bandwidth constraints.
- Cost volatility from AI inference usage.

### 10.2 Risk process
1. Identify and log risks weekly.
2. Score each risk on likelihood and impact.
3. Define owner, mitigation, and trigger.
4. Review risk register in weekly project review.

### 10.3 Escalation
- High/critical risks escalate to immediate action planning within 24 hours.
- Privacy and safety risks escalate through SCMP incident workflow.

## 11. Quality Management

### 11.1 Quality objectives
- Deliver features that meet acceptance criteria and safety constraints.
- Prevent regression in privacy and deletion workflows.
- Keep code quality aligned with Python-first CI gates.

### 11.2 Quality controls
- Definition of Done (DoD):
  - Acceptance criteria met.
  - Tests updated and passing.
  - Privacy/safety impacts reviewed.
  - Documentation updated.
- Periodic usability checks with target users.
- Release checklist must pass before any production promotion.

## 12. Communications Plan

### 12.1 Cadence
- Daily async status update.
- Weekly execution review (scope, schedule, risks, blockers).
- Biweekly milestone summary.
- Monthly stakeholder update.

### 12.2 Audience and artifacts
- Internal team: sprint board and weekly action list.
- Advisors: monthly checkpoint summary.
- External stakeholders: milestone and impact reports.

### 12.3 Incident communications
- Follow SCMP incident classification and response targets.
- Assign Comms Owner for all SEV0/SEV1 events.

## 13. Metrics and Reporting

### 13.1 Delivery metrics
- Planned vs completed sprint scope.
- Milestone on-time rate.
- Lead time from issue to deployed change.

### 13.2 Product and pilot metrics
- End-to-end flow completion rate.
- User-reported confidence/anxiety delta.
- User-to-artist handoff conversion rate.

### 13.3 Reliability and safety metrics
- SLO adherence (availability, P95 latency).
- Incident count by severity.
- Safety filter escape rate.

## 14. Change Management (Project Scope and Plan)

### 14.1 Baselines
- Scope baseline.
- Schedule baseline.
- Cost baseline.

### 14.2 Change request policy
- Any baseline-impacting change requires documented change request.
- Approval authority:
  - Minor: Project Manager.
  - Major (scope/time/cost impact): Project Manager + advisor review.
- All approved changes must update SPMP and related trackers.

## 15. Tools and Repositories

- Source and docs in project repository.
- Python toolchain aligned with SCMP (`pytest`, `ruff`, optional `mypy`).
- Templates in `docs/spmp/templates/`.
- SCM controls and release governance in `docs/scmp/`.

## 16. Dependency Management

### 16.1 External dependencies
- AI model providers.
- Cloud storage and compute services.
- Partner availability (artists and communities).

### 16.2 Dependency controls
- Identify single points of failure.
- Define fallback options for critical services.
- Review dependency risk in monthly governance review.

## 17. Procurement and Partner Management

- Use lightweight partner agreements for pilot collaboration.
- Define data handling and consent obligations in partner onboarding.
- Track partner onboarding status and performance feedback.

## 18. Security, Privacy, and Ethics Alignment

- Privacy-by-design is mandatory in all stories touching user images.
- Non-medical positioning must remain explicit in all product surfaces.
- Safety and dignity checks are required before pilot expansion.

## 19. Plan Maintenance and Reviews

- Review SPMP monthly or at every stage gate, whichever comes first.
- Update version and changelog on material process changes.
- Archive prior versions for auditability.

## 20. Immediate Adoption Plan (next 2 weeks)

1. Approve SPMP v1.0 as execution baseline.
2. Start weekly risk register and status report workflow.
3. Define Sprint 1 scope and acceptance criteria.
4. Run first gate-prep check using SPMP + SCMP controls.
5. Publish first monthly stakeholder summary.
