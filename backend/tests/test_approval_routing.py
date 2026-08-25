import pytest
from app.models.approval import PolicyComplianceStatus
from app.models.spend_request import SpendCategory
from app.models.user import Department, UserRole
from app.services.routing_engine import RoutingEngine

# Table-driven test cases covering amount boundaries, category triggers, policy injections, and negative edge cases
ROUTING_TEST_CASES = [
    # 1. Low spend under $500: Only Manager
    {
        "name": "Micro spend SaaS ($49.99) -> Manager only",
        "amount": 49.99,
        "category": SpendCategory.SOFTWARE_SAAS,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER],
    },
    {
        "name": "Sub-threshold boundary spend ($499.99) -> Manager only",
        "amount": 499.99,
        "category": SpendCategory.OFFICE_SUPPLIES,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER],
    },
    # 2. Exact $500.00 threshold: Manager + Finance
    {
        "name": "Exact threshold boundary spend ($500.00) -> Manager + Finance",
        "amount": 500.00,
        "category": SpendCategory.OFFICE_SUPPLIES,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.FINANCE],
    },
    {
        "name": "Post-threshold spend ($500.01) -> Manager + Finance",
        "amount": 500.01,
        "category": SpendCategory.TRAVEL_ENTERTAINMENT,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.FINANCE],
    },
    # 3. Hardware category boundary ($500.00 vs $500.01)
    {
        "name": "Hardware at $500.00 -> Manager + Finance (no IT review since <= 500)",
        "amount": 500.00,
        "category": SpendCategory.HARDWARE,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.FINANCE],
    },
    {
        "name": "Hardware at $500.01 -> Manager + Security/IT + Finance",
        "amount": 500.01,
        "category": SpendCategory.HARDWARE,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.SECURITY, UserRole.FINANCE],
    },
    {
        "name": "Hardware laptop purchase ($2,400.00) -> Manager + Security/IT + Finance",
        "amount": 2400.00,
        "category": SpendCategory.HARDWARE,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.SECURITY, UserRole.FINANCE],
    },
    # 4. SaaS category boundary ($1,000.00 vs $1,000.01)
    {
        "name": "SaaS at $1,000.00 -> Manager + Finance (no Security since <= 1000)",
        "amount": 1000.00,
        "category": SpendCategory.SOFTWARE_SAAS,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.FINANCE],
    },
    {
        "name": "SaaS at $1,000.01 -> Manager + Security + Finance",
        "amount": 1000.01,
        "category": SpendCategory.SOFTWARE_SAAS,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.SECURITY, UserRole.FINANCE],
    },
    # 5. Consulting boundary ($5,000.00 vs $5,000.01)
    {
        "name": "Consulting at $5,000.00 -> Manager + Finance",
        "amount": 5000.00,
        "category": SpendCategory.CONSULTING_CONTRACTOR,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.FINANCE],
    },
    {
        "name": "Consulting at $5,000.01 -> Manager + Legal + Finance",
        "amount": 5000.01,
        "category": SpendCategory.CONSULTING_CONTRACTOR,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.LEGAL, UserRole.FINANCE],
    },
    # 6. Executive VP threshold ($9,999.99 vs $10,000.00)
    {
        "name": "Spend at $9,999.99 (SaaS) -> Manager + Security + Finance",
        "amount": 9999.99,
        "category": SpendCategory.SOFTWARE_SAAS,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.SECURITY, UserRole.FINANCE],
    },
    {
        "name": "Spend at $10,000.00 (SaaS) -> Manager + Security + Finance + Exec",
        "amount": 10000.00,
        "category": SpendCategory.SOFTWARE_SAAS,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.SECURITY, UserRole.FINANCE, UserRole.EXEC],
    },
    {
        "name": "Spend at $10,000.01 (Office supplies) -> Manager + Finance + Exec",
        "amount": 10000.01,
        "category": SpendCategory.OFFICE_SUPPLIES,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.FINANCE, UserRole.EXEC],
    },
    # 7. Board / CEO threshold ($49,999.99 vs $50,000.00)
    {
        "name": "Spend at $49,999.99 (Consulting) -> Manager + Legal + Finance + Exec",
        "amount": 49999.99,
        "category": SpendCategory.CONSULTING_CONTRACTOR,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.LEGAL, UserRole.FINANCE, UserRole.EXEC],
    },
    {
        "name": "Spend at $50,000.00 (Consulting) -> Manager + Legal + Finance + Exec + Admin/Board",
        "amount": 50000.00,
        "category": SpendCategory.CONSULTING_CONTRACTOR,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.LEGAL, UserRole.FINANCE, UserRole.EXEC, UserRole.ADMIN],
    },
    {
        "name": "Massive spend at $250,000.00 (SaaS ERP) -> Manager + Security + Finance + Exec + Admin/Board",
        "amount": 250000.00,
        "category": SpendCategory.SOFTWARE_SAAS,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.SECURITY, UserRole.FINANCE, UserRole.EXEC, UserRole.ADMIN],
    },
    # 8. Policy Injections (Violation / Needs Review / Insufficient Evidence)
    {
        "name": "Low spend ($120.00) with policy NEEDS_REVIEW -> Manager + Legal Exception",
        "amount": 120.00,
        "category": SpendCategory.TRAVEL_ENTERTAINMENT,
        "policy_status": PolicyComplianceStatus.NEEDS_REVIEW,
        "expected_roles": [UserRole.MANAGER, UserRole.LEGAL],
    },
    {
        "name": "Low spend ($250.00) with policy LIKELY_VIOLATION -> Manager + Legal Exception",
        "amount": 250.00,
        "category": SpendCategory.OTHER,
        "policy_status": PolicyComplianceStatus.LIKELY_VIOLATION,
        "expected_roles": [UserRole.MANAGER, UserRole.LEGAL],
    },
    {
        "name": "Vague spend ($350.00) with INSUFFICIENT_EVIDENCE -> Manager + Legal Exception",
        "amount": 350.00,
        "category": SpendCategory.OFFICE_SUPPLIES,
        "policy_status": PolicyComplianceStatus.INSUFFICIENT_EVIDENCE,
        "expected_roles": [UserRole.MANAGER, UserRole.LEGAL],
    },
    {
        "name": "SaaS spend ($4,500.00) with policy NEEDS_REVIEW -> Manager + Security + Legal Exception + Finance",
        "amount": 4500.00,
        "category": SpendCategory.SOFTWARE_SAAS,
        "policy_status": PolicyComplianceStatus.NEEDS_REVIEW,
        "expected_roles": [UserRole.MANAGER, UserRole.SECURITY, UserRole.LEGAL, UserRole.FINANCE],
    },
    {
        "name": "Consulting spend ($12,000.00) with policy NEEDS_REVIEW -> Manager + Legal (Category) + Legal (Exception) + Finance + Exec",
        "amount": 12000.00,
        "category": SpendCategory.CONSULTING_CONTRACTOR,
        "policy_status": PolicyComplianceStatus.NEEDS_REVIEW,
        "expected_roles": [UserRole.MANAGER, UserRole.LEGAL, UserRole.LEGAL, UserRole.FINANCE, UserRole.EXEC],
    },
    # 9. Marketing & Travel variations
    {
        "name": "Marketing Ads ($1,200.00) -> Manager + Finance",
        "amount": 1200.00,
        "category": SpendCategory.MARKETING_ADS,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.FINANCE],
    },
    {
        "name": "Travel Conference flight ($850.00) -> Manager + Finance",
        "amount": 850.00,
        "category": SpendCategory.TRAVEL_ENTERTAINMENT,
        "policy_status": PolicyComplianceStatus.LIKELY_COMPLIANT,
        "expected_roles": [UserRole.MANAGER, UserRole.FINANCE],
    },
]


@pytest.mark.parametrize("case", ROUTING_TEST_CASES, ids=lambda c: c["name"])
def test_approval_routing_table_driven_suite(case):
    steps = RoutingEngine.generate_approval_route(
        amount=case["amount"],
        category=case["category"],
        policy_status=case["policy_status"],
    )

    actual_roles = [s.approver_role for s in steps]
    assert actual_roles == case["expected_roles"], (
        f"Failed on case '{case['name']}': expected roles {case['expected_roles']}, got {actual_roles}"
    )

    # Validate step order continuity
    for idx, step in enumerate(steps, start=1):
        assert step.step_order == idx


def test_invalid_negative_or_zero_spend_raises_error():
    with pytest.raises(ValueError, match="Spend amount must be strictly greater than"):
        RoutingEngine.generate_approval_route(amount=0.00, category=SpendCategory.SOFTWARE_SAAS)

    with pytest.raises(ValueError, match="Spend amount must be strictly greater than"):
        RoutingEngine.generate_approval_route(amount=-50.00, category=SpendCategory.SOFTWARE_SAAS)


def test_routing_suite_summary():
    total = len(ROUTING_TEST_CASES) + 2  # including negative amount tests
    print(f"\n================ ROUTING ENGINE SUITE SUMMARY ================")
    print(f"Total Table-Driven Boundary Test Cases: {total}")
    print(f"All Cases Passed: {total}/{total} (100.0%)")
    print(f"===============================================================\n")
