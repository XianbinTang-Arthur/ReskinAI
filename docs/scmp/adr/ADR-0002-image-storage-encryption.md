# ADR-0002: Image Storage Encryption Strategy

Status: Proposed  
Date: 2026-02-12  
Deciders: Founder / Project Lead  
Related issue: TBD

## Context

The system handles highly sensitive scar imagery. Storage design must minimize exposure risk and support deletion guarantees.

## Decision

Store user-uploaded images in encrypted object storage with environment-separated buckets and short default retention windows.

## Consequences

### Positive

- Reduced privacy breach risk.
- Clearer environment isolation and deletion operations.
- Better auditability for access controls.

### Negative

- Slightly higher storage and operations complexity.
- Additional key management responsibilities.

## Alternatives considered

- Option A: local file storage on application host.
- Option B: encrypted DB blob storage for all images.

## Rollback or revision trigger

Revisit if compliance requirements, performance needs, or cost profile materially change.
