# ADR-0001: Model Hosting Strategy

Status: Proposed  
Date: 2026-02-12  
Deciders: Founder / Project Lead  
Related issue: TBD

## Context

ReSkin AI needs a reliable and safe model serving approach for image generation and prompt safety enforcement. Team size is small and time-to-market for commercialization is short.

## Decision

Use managed model APIs in the initial phase instead of self-hosting model infrastructure.

## Consequences

### Positive

- Faster implementation and iteration speed.
- Lower operational burden for early stage team.
- Easier regional failover through provider options.

### Negative

- Less control over low-level model behavior.
- Vendor lock-in risk.
- Cost may increase with scale.

## Alternatives considered

- Option A: self-hosted diffusion stack from day 1.
- Option B: hybrid routing with managed primary and self-hosted backup.

## Rollback or revision trigger

Revisit if monthly inference cost, latency, safety control, or policy constraints exceed acceptable thresholds.
