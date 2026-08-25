# Waypoint Architecture Document

This document describes the design decisions, data flow, and components of the Waypoint Spend & Procurement Approval Router.

## 1. High-Level Flow

```
[Employee Client / Frontend]
        |
        | 1. Submit Request (GraphQL Mutation)
        v
[FastAPI + Strawberry GraphQL Layer]
        |
        +---> [PolicyEngine]
        |       Audits text against written policy (SEC-1..7)
        |       Outputs: Status, Score, Citations
        |
        +---> [RoutingEngine]
        |       Evaluates Amount + Category + Policy Status
        |       Outputs: Ordered Approval Chain & Steps
        |
        +---> [PostgreSQL / SQLite Database]
                Persists SpendRequest, PolicyEvaluation, ApprovalChain, ApprovalSteps
```

## 2. Relational Schema Design

* **User**: Identity and role context (`EMPLOYEE`, `MANAGER`, `FINANCE`, `LEGAL`, `SECURITY`, `EXEC`, `ADMIN`).
* **SpendRequest**: Primary spend item with currency, amount, department, category, and lifecycle status.
* **ApprovalChain**: 1-to-1 relationship with `SpendRequest`, maintaining `current_step_order` and overall chain status.
* **ApprovalStep**: Individual step within a chain, with assigned `approver_role`, optional assigned `approver_id`, and status (`PENDING`, `APPROVED`, `REJECTED`, `SKIPPED`).
* **PolicyEvaluation**: Grounded audit output capturing compliance status, confidence score, rationale, and an array of line-level policy citations.
* **Policy**: Versioned written procurement policy markdown document.

## 3. Strawberry DataLoader Batching Pattern

When querying a collection of spend requests, naive resolver execution triggers sequential database queries for each relation (N+1 problem):

1. Query all spend requests: `1 query`
2. For each request, resolve requester: `N queries`
3. For each request, resolve approval chain: `N queries`
4. For each request, resolve approval steps: `N queries`
5. For each request, resolve policy evaluation: `N queries`

Total: `1 + 4N queries` (81 queries for 20 requests).

By wrapping foreign key lookups in Strawberry's `DataLoader`, queries are consolidated into batch statements:

1. `SELECT * FROM spend_requests`
2. `SELECT * FROM users WHERE id IN (...)`
3. `SELECT * FROM approval_chains WHERE request_id IN (...)`
4. `SELECT * FROM approval_steps WHERE chain_id IN (...)`
5. `SELECT * FROM policy_evaluations WHERE request_id IN (...)`

Total: `5 queries` regardless of N (measured at 93.8% query reduction).

## 4. Policy Grounding & Citation Extraction

The `PolicyEngine` reads the active company policy file, indexing it by section codes (`SEC-1` through `SEC-7`) and individual line numbers.

When evaluating a spend request:
* If required information is missing (such as unverified vendor or vague justification like 'miscellaneous'), it flags `INSUFFICIENT_EVIDENCE` citing Section 1 Line 4 and Section 7 Line 27.
* If a prohibited category is detected (personal items, gym passes, unitemized alcohol), it flags `LIKELY_VIOLATION` with the exact line citation.
* If high-risk tools or commitments are detected (AI services with customer data, multi-year SaaS, contractors over $5,000 without SOW), it flags `NEEDS_REVIEW` and routes an additional compliance approval step.
