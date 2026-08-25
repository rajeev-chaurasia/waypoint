# waypoint

- **Repository:** https://github.com/rajeev-chaurasia/waypoint
- **One-liner:** A policy-aware spend and procurement approval router with Strawberry GraphQL, DataLoader batching that cuts query overhead by 93.8%, deterministic multi-tier routing verified by 26 boundary cases, and a grounded AI policy auditor scoring 1.00 precision and 1.00 recall with line-level citations against a written policy document.
- **Status:** complete, public, CI green
- **Timeline:** 42 commits, 2026-08-25
- **Category:** Enterprise Workflow Orchestration / Developer Platform / GraphQL Systems
- **Primary language:** Python 3.13 (FastAPI, Strawberry GraphQL, SQLAlchemy 2.0 Async, SQLite/PostgreSQL), TypeScript 5.6 on React 18 & Apollo Client 3.11

## Problem

Corporate spend management platforms either force rigid one-size-fits-all approval hierarchies or rely on opaque AI chatbots that hallucinate approvals without verifiable justification. In high-velocity procurement, reviewers are overwhelmed with requests, spend thresholds are inadvertently bypassed, and multi-year or high-risk software commitments slip through without required security or legal sign-offs.

Building an enterprise-grade procurement router requires solving three non-trivial engineering challenges:

1. **Relational Query Performance at Scale**: Nested procurement queries (fetching spend requests along with requesters, multi-step approval chains, approver profiles, and compliance audits) naturally degrade into catastrophic N+1 database queries unless batched at the resolver layer.
2. **Deterministic Threshold Governance**: Spend routing must be exact and auditable. Edge cases at dollar boundaries ($499.99 vs $500.00, $9,999.99 vs $10,000.00) and domain triggers (SaaS data privacy, contractor Statements of Work) cannot depend on probabilistic heuristics.
3. **Verifiable Policy Auditing with Strict Grounding**: Automated compliance checking is only trustworthy if every decision provides explicit line citations to the active policy document and strictly admits insufficient evidence on vague or unitemized submissions rather than guessing compliance.

This project delivers a complete workflow orchestration platform inspired by Zip's procurement architecture, where every performance claim, routing rule, and AI evaluation metric is backed by automated, reproducible benchmark test suites.

## Architecture

Three decoupled tiers separated by clean contract boundaries:

```
[ Frontend: React 18 + TypeScript + Apollo Client ]
                      |
                      | GraphQL Queries & Mutations over HTTP
                      v
[ Backend API: FastAPI + Strawberry GraphQL Router ]
        |                   |                   |
        v                   v                   v
 [Routing Engine]    [Policy Engine]     [AppDataLoaders]
  Deterministic       Grounded line-level Batched relational
  tier calculation    citation extractor  SQL statement runner
        |                   |                   |
        +-------------------+-------------------+
                            |
                            v
[ Storage: SQLAlchemy Async + aiosqlite / asyncpg (PostgreSQL) ]
```

### Clean Layering & Separation of Concerns

* `backend/app/core/`: Configuration via Pydantic Settings, async database session management, and SQL execution counter hooks for empirical query profiling.
* `backend/app/models/`: Normalized SQLAlchemy relational schema (`User`, `SpendRequest`, `ApprovalChain`, `ApprovalStep`, `Policy`, `PolicyEvaluation`).
* `backend/app/services/`: Pure business logic services (`RoutingEngine`, `PolicyEngine`, `RequestService`) operating independently of HTTP or GraphQL layers.
* `backend/app/graphql/`: Schema-first Strawberry types, DataLoader batch loaders with async concurrency locks, query resolvers, and mutation handlers.
* `backend/app/policies/`: Versioned written company procurement policy documents in indexed markdown format.
* `frontend/src/`: React + TypeScript frontend consuming the GraphQL API via Apollo Client, complete with live route simulation, role switching personas, request review queues, and metrics dashboards.

## DataLoader N+1 Elimination

Nested GraphQL queries across 20 spend requests with nested requesters, approval chains, approval steps, and policy evaluations trigger 81 separate SQL queries under naive resolver execution ($1 + 4N$ queries).

By implementing Strawberry `DataLoader` batch loaders for User lookups, Approval Chains by Request ID, Approval Steps by Chain ID, and Policy Evaluations by Request ID, database lookups are consolidated into 5 discrete SQL statements regardless of collection size:

```sql
-- 1. Fetch collection of spend requests
SELECT * FROM spend_requests ORDER BY created_at DESC;

-- 2. Batched fetch of all unique requesters
SELECT * FROM users WHERE id IN ('user_001', 'user_002', ...);

-- 3. Batched fetch of all approval chains
SELECT * FROM approval_chains WHERE request_id IN ('req_001', 'req_002', ...);

-- 4. Batched fetch of all approval steps across chains
SELECT * FROM approval_steps WHERE chain_id IN ('chain_001', 'chain_002', ...) ORDER BY step_order;

-- 5. Batched fetch of all policy evaluations
SELECT * FROM policy_evaluations WHERE request_id IN ('req_001', 'req_002', ...);
```

### Empirical Query Measurement

| Resolver Strategy | SQL Statements (20 Requests) | Scaling Behavior | Query Reduction |
| :--- | :--- | :--- | :--- |
| Naive Resolver (N+1) | 81 queries | $O(N)$ linear database roundtrips | Baseline |
| Strawberry DataLoader | 5 queries | $O(1)$ constant query count | **93.8% reduction** |

*Verified by automated benchmark suite:* `pytest backend/tests/test_dataloaders_n1.py -v -s`

## Deterministic Approval Routing

The `RoutingEngine` processes request metadata (amount, currency, category, department, requester, and AI compliance status) through a deterministic multi-tier decision matrix:

1. **Tier 1 (Direct Line Manager)**: Mandatory initial verification for all requests ($> $0.00).
2. **Tier 2 (Category & Domain Governance)**:
   * `SOFTWARE_SAAS`: Mandatory Security & IT Architecture review for contracts $> $1,000.00.
   * `HARDWARE`: Mandatory IT Procurement verification for equipment $> $500.00.
   * `CONSULTING_CONTRACTOR`: Mandatory Legal Counsel & Statement of Work review for contracts $> $5,000.00.
3. **Policy Exception Injection**: When the AI policy auditor flags `NEEDS_REVIEW`, `LIKELY_VIOLATION`, or `INSUFFICIENT_EVIDENCE`, a mandatory `Compliance & Policy Exception Review` step is automatically injected before financial disbursement.
4. **Tier 3 (Finance & Controller Review)**: Budget allocation and GL coding review for all expenditures $\ge $500.00.
5. **Tier 4 (Executive VP Sign-Off)**: Executive authorization for major spend $\ge $10,000.00.
6. **Tier 5 (Board & CEO Authorization)**: Material commitment authorization for spend $\ge $50,000.00.

### Boundary Test Suite Results

Table-driven test suite validating exact dollar boundaries, category triggers, and exception handling:

* **Total Test Cases**: 26
* **Pass Rate**: 26 / 26 (100.0%)
* **Exact Dollar Boundaries Verified**:
  * `$499.99` (Manager only) vs `$500.00` (Manager + Finance)
  * `$500.00` (Standard hardware) vs `$500.01` (Hardware IT review trigger)
  * `$1,000.00` (Standard software) vs `$1,000.01` (SaaS Security review trigger)
  * `$5,000.00` (Standard services) vs `$5,000.01` (Consulting Legal review trigger)
  * `$9,999.99` (Departmental tier) vs `$10,000.00` (Executive VP sign-off trigger)
  * `$49,999.99` (Executive tier) vs `$50,000.00` (Board & CEO authorization trigger)

*Verified by table-driven test suite:* `pytest backend/tests/test_approval_routing.py -v -s`

## Policy Grounding & Citation Engine

The `PolicyEngine` indexes written corporate policy markdown into discrete section codes (`SEC-1` through `SEC-7`) and sequential line numbers. It extracts verifiable text citations for every classification.

### Strict Honesty on Insufficient Evidence

Unlike generative classifiers that invent reasons to approve ambiguous requests, the policy engine enforces a strict "admit insufficient evidence" contract:

* Vague titles (`"miscellaneous"`, `"urgent spend"`, `"project items"`) or missing vendor identities automatically return `INSUFFICIENT_EVIDENCE` citing Section 1 Line 4 and Section 7 Line 27.
* Prohibited items (gym passes, domestic utility bills, personal gift cards, crypto rewards, unitemized alcohol) return `LIKELY_VIOLATION` citing Section 7 Line 24/26 and Section 4 Line 17.
* High-risk AI tools handling proprietary code or customer data return `NEEDS_REVIEW` citing Section 2 Line 7.
* Multi-year SaaS subscriptions return `NEEDS_REVIEW` citing Section 2 Line 9.

### Hand-Labeled Benchmark Evaluation

Evaluated across a 30-case hand-labeled dataset spanning compliant requests, explicit violations, and ambiguous submissions:

| Metric | Measured Result | Benchmark Target |
| :--- | :--- | :--- |
| **Total Test Cases** | 30 / 30 exact matches | 100.0% |
| **Compliant Precision** | **100.0%** | $\ge$ 95.0% |
| **Compliant Recall** | **100.0%** | $\ge$ 95.0% |
| **Citation Grounding Rate** | **100.0%** | 100.0% |
| **Hallucinations on Vague Data** | **0.0%** | 0.0% |

*Verified by benchmark test suite:* `pytest backend/tests/test_policy_agent.py -v -s`

## Interactive User Workspace

The React + TypeScript frontend is engineered for fast review cycles and visibility into governance decisions:

1. **Live Approval Route Preview**: As an employee types spend amount and selects categories, the UI dynamically previews the generated approval steps in real time before submission.
2. **Approval Queue & Action Filtering**: Filter requests by status (`Needs My Action`, `Pending`, `Approved`, `Rejected`) or category, with quick persona switching to simulate Manager, Security, Finance, Legal, and Exec approvals.
3. **Policy Grounding Detail Modal**: Displays full request metadata, visual step-by-step approval chain timeline, and policy evaluation card with clickable line citations.
4. **Interactive Policy Document Explorer**: View active corporate procurement policy with search highlighting and instant anchor jumps from citation links.
5. **Architecture & Benchmark Dashboard**: Live visual KPI metrics showcasing spend throughput, DataLoader query reduction ratios (93.8%), and policy precision rates.

## Tech Stack (Verified)

* **Backend**: Python 3.13, FastAPI 0.115, Strawberry GraphQL 0.324, Uvicorn 0.52
* **Database & ORM**: SQLAlchemy 2.0 Async, aiosqlite 0.22, asyncpg 0.31
* **Frontend**: React 18.3, TypeScript 5.6, Apollo Client 3.11, Vite 5.4, Lucide React 0.453
* **Styling**: Vanilla CSS Design System with curated HSL dark mode palette, glassmorphism, and responsive layouts
* **Testing & Profiling**: Pytest 9.1, Pytest-Asyncio 1.4, Custom `QueryCounter` SQL event listener

## Testing Suite

30 automated tests across 4 specialized test modules:

1. `test_dataloaders_n1.py`: Measures SQL cursor execution count comparing naive resolver execution (81 queries) against batched DataLoader execution (5 queries).
2. `test_approval_routing.py`: 26-case table-driven parameterized suite covering exact threshold boundaries ($499.99 vs $500.00, $9,999.99 vs $10,000.00, $49,999.99 vs $50,000.00) and category routing.
3. `test_policy_agent.py`: 30-case hand-labeled dataset measuring precision, recall, and citation validity for the AI policy agent.
4. `test_graphql_api.py`: End-to-end integration tests for GraphQL queries, mutations, approval transitions, and metrics.

## Resume Points

* Built a GraphQL API in FastAPI and Strawberry for a spend-approval router, fixing an N+1 query with DataLoader batching that cut per-request query count from 81 to 5 (93.8% reduction).
* Implemented rule-based approval routing across amount and category tiers, verified by 26/26 table-driven boundary tests including exact-threshold edge cases ($499.99 vs $500.00, $9,999.99 vs $10,000.00).
* Built a policy-grounded AI agent that classifies each request against a written policy doc with line-level citations, measured at 100.0% precision and 100.0% recall over a 30-case hand-labeled set.
* Shipped a React and TypeScript frontend over Apollo Client, submitting and reviewing requests live with interactive approval actions and policy grounding inspection.
* Designed an asynchronous database query counter event listener in SQLAlchemy to empirically benchmark SQL execution reduction in continuous integration.
* Engineered a strict "admit insufficient evidence" classification engine that rejects ambiguous procurement requests without hallucinating compliance.

### One-Line Resume Summary

Policy-aware spend approval router built in FastAPI, Strawberry GraphQL, PostgreSQL, and React, eliminating N+1 queries by 93.8% with DataLoaders and auditing requests with 100% precision using grounded policy citations.

## Interview Talking Points

* Why GraphQL with DataLoaders is the optimal architectural fit for complex workflow orchestration where requests have deeply nested, multi-relational approval hierarchies.
* How asynchronous greenlet execution in SQLAlchemy asyncio requires explicit concurrency serialization to prevent session contention during parallel field resolution.
* Why table-driven boundary testing is mandatory for financial routing engines to prevent off-by-one threshold circumvention ($499.99 vs $500.00).
* How the grounded citation pattern avoids LLM hallucination by indexing policy line numbers and forcing an explicit `INSUFFICIENT_EVIDENCE` fallback when vendor details are missing.
* The trade-offs between schema-first vs code-first GraphQL and why Strawberry's type-annotated resolvers provide superior maintainability in Python.
