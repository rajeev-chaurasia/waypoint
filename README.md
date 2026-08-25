# Waypoint

AI-assisted spend and procurement approval router inspired by modern workflow orchestration systems. Routes corporate purchase requests through deterministic, policy-aware approval chains while evaluating requests against written company policies with line-level citations.

---

## Resume Summary

**waypoint | AI-Assisted Procurement Approval Router | Python, FastAPI, GraphQL, React, TypeScript, PostgreSQL**

* Built a GraphQL API in FastAPI and Strawberry for a spend-approval router, fixing an N+1 query with DataLoader batching that cut per-request query count from **81** to **5** SQL queries (93.8% reduction).
* Implemented rule-based approval routing across amount and category tiers, verified by **26/26** table-driven boundary tests including exact-threshold edge cases ($499.99 vs $500.00, $9,999.99 vs $10,000.00, $49,999.99 vs $50,000.00).
* Built a policy-grounded AI agent that classifies each request against a written policy doc with line-level citations, measured at **97.1%** accuracy (**100.0%** precision and **100.0%** recall) over a **35**-case hand-labeled set with documented boundary failure modes.
* Shipped a React and TypeScript frontend over Apollo Client, submitting and reviewing requests live with role-based approver actions and policy grounding inspection.

---

## Core System Capabilities

1. **Deterministic Multi-Tier Routing Engine**: Evaluates spend requests across amount thresholds and category criteria (Software SaaS, IT Hardware, Consulting, Travel, Marketing). Injects domain reviews (Security, Legal, Finance, Executive, Board) deterministically.
2. **Policy-Grounded AI Agent**: Audits purchase justifications against indexed markdown policy documents. Strictly adheres to an "admit insufficient evidence" pattern when requests lack vendor details or itemized breakdowns rather than guessing compliance.
3. **Strawberry GraphQL & DataLoader Architecture**: Schema-first GraphQL layer with asynchronous batching via DataLoaders to eliminate nested relational N+1 queries.
4. **Interactive Approval Workspace**: Modern React + Apollo Client interface featuring live route simulation, role-switching personas, and citation inspection.

---

## Empirical Benchmark Results

### 1. DataLoader N+1 Query Elimination

Measured fetching 20 nested spend requests along with requester records, approval chains, approval steps, and policy evaluation objects:

| Execution Mode | Queries Executed | Relative Overhead | Query Reduction |
| :--- | :--- | :--- | :--- |
| Naive Resolver (Simulated N+1) | 81 queries | Baseline (1 + 4N) | 0.0% |
| Strawberry DataLoader (Batched) | 5 queries | Optimized batch | **93.8% decrease** |

*Test command*: `pytest backend/tests/test_dataloaders_n1.py -v -s`

### 2. Rule-Based Approval Routing Boundary Suite

Table-driven test suite validating exact dollar boundaries and category-specific governance:

* **Total Test Cases**: 26
* **Passed**: 26 / 26 (100.0%)
* **Edge Cases Verified**:
  * Micro spend under $500.00: Manager sign-off only
  * Exact $500.00 threshold: Manager + Finance
  * Software SaaS > $1,000.00: Security & IT architecture review
  * Hardware > $500.00: IT procurement check
  * Consulting > $5,000.00: Legal Counsel & Statement of Work check
  * Exact $10,000.00 threshold: Executive VP authorization
  * Exact $50,000.00 threshold: Board of Directors & CEO sign-off
  * Zero / negative values: Validation error raised

*Test command*: `pytest backend/tests/test_approval_routing.py -v -s`

### 3. AI Policy Agent Evaluation
Hand-labeled dataset evaluating classification accuracy and grounded citation generation against `corporate_procurement_policy_v1.md`:

* **Total Hand-Labeled Cases**: 35 (10 Compliant, 10 Violation, 10 Ambiguous/Review, 5 Boundary Cases)
* **Exact Status Matches**: 34 / 35 (**97.1% accuracy**)
* **Compliant Precision**: 100.0%
* **Compliant Recall**: 100.0%
* **Citation Grounding Rate**: 100.0% (every decision cites explicit policy section and line number)
* **Documented Failure Mode**: Case E-02 ($160 dinner with unstated headcount) was conservatively classified as `LIKELY_VIOLATION` rather than `NEEDS_REVIEW`, deliberately favoring false alarms over false compliance approvals.
* **Hallucination on Vague Data**: 0.0% (unitemized or missing vendor requests flagged as `INSUFFICIENT_EVIDENCE`)

*Test command*: `pytest backend/tests/test_policy_agent.py -v -s`

---

## System Architecture

```
waypoint/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration, Database engine, Query counter
│   │   ├── models/         # SQLAlchemy async models (User, SpendRequest, Approval, Policy)
│   │   ├── services/       # RoutingEngine, PolicyEngine, RequestService
│   │   ├── graphql/        # Strawberry Schema, Types, Queries, Mutations, DataLoaders
│   │   ├── policies/       # Indexed Procurement Policy markdown documents
│   │   └── main.py         # FastAPI application entrypoint and lifespan seeder
│   └── tests/              # Pytest suite (30 automated tests)
├── frontend/
│   ├── src/
│   │   ├── components/     # React components (Navbar, Queue, Form, Detail, Metrics, Policy)
│   │   ├── graphql/        # Typed Apollo Client queries and mutations
│   │   ├── styles/         # Custom vanilla CSS design system
│   │   └── App.tsx         # Main application view container
│   └── package.json
└── docs/                   # Architecture and routing rule documentation
```

---

## Quickstart Guide

### Prerequisites
* Python 3.11+
* Node.js 18+
* `uv` package manager (recommended) or `pip`

### 1. Start the Backend API

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

GraphQL Playground will be accessible at `http://127.0.0.1:8000/graphql`.

### 2. Start the Frontend Application

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### 3. Run Automated Tests

```bash
cd backend
uv run pytest tests/ -v
```

---

## GraphQL API Reference

### Sample Spend Request Submission Mutation

```graphql
mutation CreateSpendRequest($input: CreateSpendRequestInput!) {
  createSpendRequest(input: $input) {
    id
    title
    amount
    status
    requester {
      name
      role
    }
    policyEvaluation {
      status
      score
      reason
      citations {
        section
        lineNumber
        snippet
      }
    }
    approvalChain {
      status
      currentStepOrder
      steps {
        id
        stepOrder
        stepName
        approverRole
        status
      }
    }
  }
}
```

### Sample Approval Action Mutation

```graphql
mutation ApproveStep($input: ApproveStepInput!) {
  approveStep(input: $input) {
    id
    status
    comments
    decisionAt
  }
}
```

---

## License

MIT License.
