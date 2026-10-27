# Waypoint

AI-assisted spend and procurement approval router inspired by modern workflow orchestration systems. Routes corporate purchase requests through deterministic, policy-aware approval chains while evaluating requests against written company policies with grounded line-level citations via Google Gemini and a resilient offline fail-safe auditor.

---

## Core System Capabilities

1. **Deterministic Multi-Tier Routing Engine**: Evaluates spend requests across amount thresholds and category criteria (Software SaaS, IT Hardware, Consulting, Travel, Marketing). Injects domain reviews (Security, Legal, Finance, Executive, Board) deterministically.
2. **Dual-Mode AI Policy Engine**: Combines live Google Gemini (`gemini-3.6-flash`) reasoning with a sub-millisecond local fail-safe auditor. Employs structured JSON schema outputs and extracts line-level citations from indexed company procurement policy markdown documents.
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

### 3. AI Policy Agent Dual-Mode Evaluation

Hand-labeled dataset evaluating classification accuracy and grounded citation generation against `corporate_procurement_policy_v1.md`:

| Metric | Offline Deterministic Auditor | Live Google Gemini Agent (`gemini-3.6-flash`) |
| :--- | :--- | :--- |
| **Total Test Cases** | 35 cases | 35 cases |
| **Compliant Precision** | **100.0%** (0 false positive approvals) | **100.0%** (0 false positive approvals) |
| **Compliant Recall** | **100.0%** | **80.0%** (found 2 subtle policy nuances) |
| **Citation Grounding** | **100.0%** (all decisions cited) | **100.0%** (all decisions cited) |
| **Average Latency** | **< 1 ms** | **~5.33 s** |
| **Rate-Limit Resilience** | Local execution | Handled via auto-fallback to local engine |

*Documented Nuances & Boundary Misses*:
* **GitHub Copilot ($120.00)**: Gemini flagged that despite being under the $500 software cap, Copilot is commercial generative AI handling proprietary code, triggering mandatory Security review under SEC-2 Line 7.
* **LinkedIn Recruiter ($170.00/mo)**: Gemini calculated that $170/month represents an annualized commitment of $2,040.00, exceeding the $1,000 threshold and requiring Security review under SEC-2 Line 6.
* **Case E-02 ($160 dinner with unstated headcount)**: Classified as `LIKELY_VIOLATION` rather than `NEEDS_REVIEW`, deliberately favoring false alarms over false compliance approvals.

*Test command*: `pytest backend/tests/test_policy_agent.py -v -s`

---

## System Architecture

```
waypoint/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration, Database engine, Query counter
│   │   ├── models/         # SQLAlchemy async models (User, SpendRequest, Approval, Policy)
│   │   ├── services/       # RoutingEngine, PolicyEngine, GeminiPolicyAgent, RequestService
│   │   ├── graphql/        # Strawberry Schema, Types, Queries, Mutations, DataLoaders
│   │   ├── policies/       # Indexed Procurement Policy markdown documents
│   │   └── main.py         # FastAPI application entrypoint and lifespan seeder
│   └── tests/              # Pytest suite (31 automated tests)
├── frontend/
│   ├── src/
│   │   ├── components/     # React components (Navbar, Queue, Form, Detail, Metrics, Policy)
│   │   ├── graphql/        # Typed Apollo Client queries and mutations
│   │   ├── styles/         # Custom vanilla CSS design system
│   │   └── App.tsx         # Main application view container
│   └── package.json
└── docs/                   # Architecture, benchmarks, and routing rule documentation
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
      modelProvider
      reason
      citations {
        section
        lineNumber
        snippet
        relevance
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
