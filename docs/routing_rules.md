# Approval Routing Rules & Policy Tiers

This document details the exact rule criteria implemented by the Waypoint `RoutingEngine`.

## Routing Matrix

| Spend Category | Amount Range | Approval Steps Required | Notes |
| :--- | :--- | :--- | :--- |
| **All Categories** | $0.01 to $499.99 | 1. Manager | Direct line manager authorization |
| **General / Supplies** | $500.00 to $9,999.99 | 1. Manager<br>2. Finance | Finance sign-off threshold starts at $500.00 |
| **Software SaaS** | $1,000.01 to $9,999.99 | 1. Manager<br>2. Security & IT<br>3. Finance | Security review for SOC2, data privacy, and architecture |
| **Hardware** | $500.01 to $9,999.99 | 1. Manager<br>2. Security/IT<br>3. Finance | IT hardware asset and specification check |
| **Consulting** | $5,000.01 to $9,999.99 | 1. Manager<br>2. Legal<br>3. Finance | Statement of Work (SOW) and MSA contract review |
| **All Categories** | $10,000.00 to $49,999.99 | 1. Manager<br>2. [Category Review]<br>3. Finance<br>4. Executive VP | Executive tier authorization |
| **All Categories** | >= $50,000.00 | 1. Manager<br>2. [Category Review]<br>3. Finance<br>4. Executive VP<br>5. Board & CEO | Material commitment sign-off |

## Policy Exception Injections

If the `PolicyEngine` audits a request and outputs a status of `NEEDS_REVIEW`, `LIKELY_VIOLATION`, or `INSUFFICIENT_EVIDENCE`, the `RoutingEngine` automatically inserts an additional mandatory compliance step:

* **Step Name**: `Compliance & Policy Exception Review`
* **Approver Role**: `LEGAL`
* **Position**: Injected prior to Finance disbursement
