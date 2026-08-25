# Waypoint Architecture Document

This document describes the design decisions, data flow, dual-mode LLM policy engine, and GraphQL DataLoader batching in the Waypoint Spend & Procurement Approval Router.

## 1. High-Level Flow

```
[Employee Client / Frontend]
        |
        | 1. Submit Request (GraphQL Mutation)
        v
[FastAPI + Strawberry GraphQL Layer]
        |
        +---> [PolicyEngine (Dual-Mode)]
        |       Try: GeminiPolicyAgent (gemini-3.6-flash)
        |       Catch (429/Timeout): DeterministicPolicyAuditor
        |       Outputs: Status, Score, Citations, ModelProvider
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
* **PolicyEvaluation**: Grounded audit output capturing compliance status, confidence score, rationale, `model_provider`, and an array of line-level policy citations.
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

## 4. Dual-Mode Policy Grounding & Citation Extraction

The `PolicyEngine` orchestrates two specialized evaluation components:

1. **`GeminiPolicyAgent` (Live LLM Reasoning)**:
   * Formulates a structured system prompt embedding the active procurement policy markdown (`corporate_procurement_policy_v1.md`).
   * Enforces structured JSON output via `response_mime_type: "application/json"`.
   * Requires verbatim citations with section tags (`SEC-1`..`SEC-7`) and exact line numbers.
   * Employs an in-memory LRU evaluation cache.
2. **`DeterministicPolicyAuditor` (Offline Fail-Safe & CI Engine)**:
   * Fast, sub-millisecond local evaluator.
   * Catches HTTP 429 quota exhaustion, network timeouts, or unconfigured API keys with zero downtime.
   * Powers reproducible, zero-cost CI test suites.
