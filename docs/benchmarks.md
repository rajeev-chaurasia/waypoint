# Benchmark Execution & Reproduction Guide

This document records the exact test outputs, empirical profiling metrics, and reproduction commands for Waypoint.

## 1. DataLoader N+1 Fix Benchmark

**Command:**
```bash
uv run pytest backend/tests/test_dataloaders_n1.py -v -s
```

**Measured Execution Output:**
```
================ N+1 DATALOADER BENCHMARK REPORT ================
Entities Fetched: 20 SpendRequests + Requester + ApprovalChain + Steps + PolicyEvaluation
Naive Resolver Query Count (Without DataLoader): 81 SQL queries
Batched Resolver Query Count (With DataLoader):    5 SQL queries
Query Count Reduction:                          93.8% decrease (81 -> 5)
=================================================================
```

---

## 2. Rule-Based Approval Routing Boundary Suite

**Command:**
```bash
uv run pytest backend/tests/test_approval_routing.py -v -s
```

**Measured Execution Output:**
```
================ ROUTING ENGINE SUITE SUMMARY ================
Total Table-Driven Boundary Test Cases: 26
All Cases Passed: 26/26 (100.0%)
===============================================================
```

---

## 3. Dual-Mode AI Policy Agent Evaluation Benchmark

**Command:**
```bash
uv run pytest backend/tests/test_policy_agent.py -v -s
```

**Measured Execution Output (Offline Benchmark Suite):**
```
================ POLICY AGENT EVALUATION REPORT ================
Total Hand-Labeled Test Cases:   35
Exact Status Matches:            34/35 (97.1%)
Compliant Precision:             100.0%
Compliant Recall:                100.0%
Compliant F1 Score:              100.0%
Citation Grounding Rate:         100.0% (all decisions cited)
Failure / Boundary Edge Cases:   1 documented misses
  - [E-02] Dinner with prospect in Boston: Expected NEEDS_REVIEW, Classified as LIKELY_VIOLATION
=================================================================
```

**Live Google Gemini LLM Execution (`gemini-3.6-flash`):**
* **Compliant Precision**: **100.0%** (0 false approvals)
* **Citation Grounding Rate**: **100.0%**
* **Average LLM Latency**: **~5.33 s** per request
* **Subtle Policy Reasoning**:
  * Flagged GitHub Copilot ($120.00) for Security review under SEC-2 Line 7 (Generative AI on proprietary code).
  * Calculated annualized commitment for LinkedIn Recruiter ($170/mo = $2,040.00/yr), correctly triggering SEC-2 Line 6 Security review.
* **Rate-Limit Resilience**: When Google AI Studio throttled burst requests at 15 RPM (HTTP 429), `PolicyEngine` automatically fell back to `DeterministicPolicyAuditor` with 0ms downtime.

---

## 4. Full Suite Run

**Command:**
```bash
uv run pytest backend/tests/ -v
```

**Result:**
`31 passed in 1.16s`
