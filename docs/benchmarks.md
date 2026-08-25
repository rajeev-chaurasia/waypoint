# Benchmark Execution & Reproduction Guide

This document records the exact test outputs and reproduction steps for Waypoint benchmarks.

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

## 3. AI Policy Agent Evaluation Benchmark

**Command:**
```bash
uv run pytest backend/tests/test_policy_agent.py -v -s
```

**Measured Execution Output:**
```
================ POLICY AGENT EVALUATION REPORT ================
Total Hand-Labeled Test Cases: 30
Exact Matches: 30/30 (100.0%)
Compliant Precision: 100.0%
Compliant Recall: 100.0%
=================================================================
```

---

## 4. Full Suite Run

**Command:**
```bash
uv run pytest backend/tests/ -v
```

**Result:**
`30 passed in 0.48s`
