import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.approval import (
    ApprovalChain,
    ApprovalStep,
    ChainStatus,
    PolicyComplianceStatus,
    PolicyEvaluation,
    StepStatus,
)
from app.models.policy import Policy
from app.models.spend_request import (
    RequestStatus,
    SpendCategory,
    SpendRequest,
)
from app.models.user import Department, User, UserRole


async def seed_database(session: AsyncSession):
    # Check if already seeded
    user_check = await session.execute(select(User).limit(1))
    if user_check.scalar_one_or_none():
        return

    # 1. Create Users
    users = [
        User(
            id="user_sarah_emp",
            email="sarah.chen@acme.corp",
            name="Sarah Chen",
            role=UserRole.EMPLOYEE,
            department=Department.ENGINEERING,
            manager_id="user_marcus_mgr",
            spend_limit=1000.0,
        ),
        User(
            id="user_marcus_mgr",
            email="marcus.vance@acme.corp",
            name="Marcus Vance",
            role=UserRole.MANAGER,
            department=Department.ENGINEERING,
            manager_id="user_rachel_exec",
            spend_limit=10000.0,
        ),
        User(
            id="user_david_fin",
            email="david.miller@acme.corp",
            name="David Miller",
            role=UserRole.FINANCE,
            department=Department.LEGAL_FINANCE,
            manager_id="user_rachel_exec",
            spend_limit=50000.0,
        ),
        User(
            id="user_elena_sec",
            email="elena.rostova@acme.corp",
            name="Elena Rostova",
            role=UserRole.SECURITY,
            department=Department.ENGINEERING,
            manager_id="user_rachel_exec",
            spend_limit=25000.0,
        ),
        User(
            id="user_victoria_leg",
            email="victoria.stone@acme.corp",
            name="Victoria Stone",
            role=UserRole.LEGAL,
            department=Department.LEGAL_FINANCE,
            manager_id="user_rachel_exec",
            spend_limit=30000.0,
        ),
        User(
            id="user_rachel_exec",
            email="rachel.hayes@acme.corp",
            name="Rachel Hayes (VP Eng)",
            role=UserRole.EXEC,
            department=Department.ENGINEERING,
            spend_limit=100000.0,
        ),
        User(
            id="user_arthur_admin",
            email="arthur.pendleton@acme.corp",
            name="Arthur Pendleton (CFO & Board)",
            role=UserRole.ADMIN,
            department=Department.LEGAL_FINANCE,
            spend_limit=500000.0,
        ),
    ]
    session.add_all(users)

    # 2. Create Active Policy
    policy_path = Path(settings.POLICY_FILE_PATH)
    raw_policy_content = (
        policy_path.read_text(encoding="utf-8")
        if policy_path.exists()
        else "Standard procurement policy"
    )
    policy = Policy(
        id="pol_v1_corporate",
        title="Global Corporate Spend and Procurement Policy",
        version="1.0.0",
        is_active=True,
        content=raw_policy_content,
    )
    session.add(policy)

    # 3. Create Sample Initial Requests with full chains & AI assessments
    # Sample 1: SaaS tool pending security + finance
    req1_id = "req_seed_001"
    req1 = SpendRequest(
        id=req1_id,
        title="Datadog APM & Distributed Tracing License",
        description="Annual monitoring tier for 35 microservices on production Kubernetes cluster.",
        amount=4200.00,
        currency="USD",
        category=SpendCategory.SOFTWARE_SAAS,
        vendor_name="Datadog Inc.",
        department=Department.ENGINEERING,
        requester_id="user_sarah_emp",
        status=RequestStatus.PENDING_APPROVAL,
    )
    chain1 = ApprovalChain(
        id="chain_seed_001",
        request_id=req1_id,
        status=ChainStatus.PENDING,
        current_step_order=1,
    )
    s1_1 = ApprovalStep(
        id="step_seed_001_1",
        chain_id="chain_seed_001",
        step_order=1,
        step_name="Direct Manager Approval",
        approver_role=UserRole.MANAGER,
        approver_id="user_marcus_mgr",
        status=StepStatus.PENDING,
    )
    s1_2 = ApprovalStep(
        id="step_seed_001_2",
        chain_id="chain_seed_001",
        step_order=2,
        step_name="Security & IT Architecture Review",
        approver_role=UserRole.SECURITY,
        approver_id="user_elena_sec",
        status=StepStatus.PENDING,
    )
    s1_3 = ApprovalStep(
        id="step_seed_001_3",
        chain_id="chain_seed_001",
        step_order=3,
        step_name="Finance & Controller Review",
        approver_role=UserRole.FINANCE,
        approver_id="user_david_fin",
        status=StepStatus.PENDING,
    )
    pe1 = PolicyEvaluation(
        id="eval_seed_001",
        request_id=req1_id,
        policy_id="pol_v1_corporate",
        status=PolicyComplianceStatus.LIKELY_COMPLIANT,
        score=0.92,
        reason="Valid business justification identified (SEC-1 Line 2). Compliant spend routed through standard SaaS tiers.",
        citations=[
            {
                "section": "SEC-1",
                "line_number": 2,
                "snippet": "All company expenditures must serve a direct business purpose, represent market value, and adhere to compliance routing.",
                "relevance": "Legitimate business expenditure for observability.",
            },
            {
                "section": "SEC-2",
                "line_number": 6,
                "snippet": "Software subscriptions exceeding $1,000.00 annually require mandatory Security and IT Operations review for data protection.",
                "relevance": "Triggers Security & IT review step.",
            },
        ],
    )

    # Sample 2: Generative AI Request (Flagged NEEDS_REVIEW)
    req2_id = "req_seed_002"
    req2 = SpendRequest(
        id=req2_id,
        title="Custom Generative AI Agent with Customer Data",
        description="Integrating LLM API to process production customer data and proprietary source code.",
        amount=3200.00,
        currency="USD",
        category=SpendCategory.SOFTWARE_SAAS,
        vendor_name="OpenAI API Platform",
        department=Department.ENGINEERING,
        requester_id="user_sarah_emp",
        status=RequestStatus.PENDING_APPROVAL,
    )
    chain2 = ApprovalChain(
        id="chain_seed_002",
        request_id=req2_id,
        status=ChainStatus.PENDING,
        current_step_order=1,
    )
    s2_1 = ApprovalStep(
        id="step_seed_002_1",
        chain_id="chain_seed_002",
        step_order=1,
        step_name="Direct Manager Approval",
        approver_role=UserRole.MANAGER,
        approver_id="user_marcus_mgr",
        status=StepStatus.PENDING,
    )
    s2_2 = ApprovalStep(
        id="step_seed_002_2",
        chain_id="chain_seed_002",
        step_order=2,
        step_name="Security & IT Architecture Review",
        approver_role=UserRole.SECURITY,
        approver_id="user_elena_sec",
        status=StepStatus.PENDING,
    )
    s2_3 = ApprovalStep(
        id="step_seed_002_3",
        chain_id="chain_seed_002",
        step_order=3,
        step_name="Compliance & Policy Exception Review",
        approver_role=UserRole.LEGAL,
        approver_id="user_victoria_leg",
        status=StepStatus.PENDING,
    )
    s2_4 = ApprovalStep(
        id="step_seed_002_4",
        chain_id="chain_seed_002",
        step_order=4,
        step_name="Finance & Controller Review",
        approver_role=UserRole.FINANCE,
        approver_id="user_david_fin",
        status=StepStatus.PENDING,
    )
    pe2 = PolicyEvaluation(
        id="eval_seed_002",
        request_id=req2_id,
        policy_id="pol_v1_corporate",
        status=PolicyComplianceStatus.NEEDS_REVIEW,
        score=0.50,
        reason="AI service handling sensitive company or customer data (SEC-2 Line 7). Mandatory Security review and SOC2 verification required.",
        citations=[
            {
                "section": "SEC-2",
                "line_number": 7,
                "snippet": "Use of commercial generative AI tools processing confidential company or customer data requires Security approval and SOC2 Type II verification.",
                "relevance": "Commercial AI tool processing confidential customer data requires Security sign-off.",
            }
        ],
    )

    # Sample 3: Small Pre-Approved Design Tool (Approved)
    req3_id = "req_seed_003"
    req3 = SpendRequest(
        id=req3_id,
        title="Figma Professional Annual License",
        description="Standard individual designer license for UX mockups and prototyping.",
        amount=180.00,
        currency="USD",
        category=SpendCategory.SOFTWARE_SAAS,
        vendor_name="Figma Inc.",
        department=Department.PRODUCT,
        requester_id="user_sarah_emp",
        status=RequestStatus.APPROVED,
    )
    chain3 = ApprovalChain(
        id="chain_seed_003",
        request_id=req3_id,
        status=ChainStatus.APPROVED,
        current_step_order=1,
    )
    s3_1 = ApprovalStep(
        id="step_seed_003_1",
        chain_id="chain_seed_003",
        step_order=1,
        step_name="Direct Manager Approval",
        approver_role=UserRole.MANAGER,
        approver_id="user_marcus_mgr",
        status=StepStatus.APPROVED,
        comments="Approved for design system maintenance.",
        decision_at=datetime.now(timezone.utc),
    )
    pe3 = PolicyEvaluation(
        id="eval_seed_003",
        request_id=req3_id,
        policy_id="pol_v1_corporate",
        status=PolicyComplianceStatus.LIKELY_COMPLIANT,
        score=0.95,
        reason="Standard SaaS spend under $500.00 limit (SEC-2 Line 8). Compliant with standard manager routing.",
        citations=[
            {
                "section": "SEC-2",
                "line_number": 8,
                "snippet": "Software purchases under $500.00 from pre-approved internal app catalogs may proceed with direct manager approval only.",
                "relevance": "Pre-approved software within allowable threshold.",
            }
        ],
    )

    session.add_all([req1, chain1, s1_1, s1_2, s1_3, pe1])
    session.add_all([req2, chain2, s2_1, s2_2, s2_3, s2_4, pe2])
    session.add_all([req3, chain3, s3_1, pe3])
    await session.commit()
