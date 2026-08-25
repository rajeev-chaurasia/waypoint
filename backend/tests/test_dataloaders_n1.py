from datetime import datetime, timezone
import pytest
import strawberry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.database import Base, QueryCounter, create_engine_and_session
from app.graphql.context import GraphQLContext
from app.graphql.dataloaders import AppDataLoaders
from app.graphql.schema import schema
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


@pytest.fixture
async def test_db():
    engine, session_maker = create_engine_and_session("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed test users
    async with session_maker() as session:
        users = [
            User(
                id="user_emp_1",
                email="emp1@company.com",
                name="Alice Engineer",
                role=UserRole.EMPLOYEE,
                department=Department.ENGINEERING,
                spend_limit=1000.0,
            ),
            User(
                id="user_mgr_1",
                email="mgr1@company.com",
                name="Bob Manager",
                role=UserRole.MANAGER,
                department=Department.ENGINEERING,
                spend_limit=10000.0,
            ),
            User(
                id="user_fin_1",
                email="fin1@company.com",
                name="Carol Finance",
                role=UserRole.FINANCE,
                department=Department.LEGAL_FINANCE,
                spend_limit=50000.0,
            ),
            User(
                id="user_sec_1",
                email="sec1@company.com",
                name="Dave Security",
                role=UserRole.SECURITY,
                department=Department.ENGINEERING,
                spend_limit=25000.0,
            ),
        ]
        session.add_all(users)

        policy = Policy(
            id="pol_v1",
            title="Standard Corporate Spend Policy",
            version="1.0.0",
            is_active=True,
            content="Corporate spend guidelines.",
        )
        session.add(policy)

        # Seed 20 spend requests, chains, steps, and policy evaluations
        for i in range(1, 21):
            req_id = f"req_{i:03d}"
            chain_id = f"chain_{i:03d}"
            eval_id = f"eval_{i:03d}"

            req = SpendRequest(
                id=req_id,
                title=f"Spend Request #{i}",
                description=f"Automated procurement request #{i} for testing.",
                amount=250.0 + (i * 50.0),
                currency="USD",
                category=SpendCategory.SOFTWARE_SAAS,
                vendor_name=f"Vendor #{i}",
                department=Department.ENGINEERING,
                requester_id="user_emp_1",
                status=RequestStatus.PENDING_APPROVAL,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(req)

            chain = ApprovalChain(
                id=chain_id,
                request_id=req_id,
                status=ChainStatus.PENDING,
                current_step_order=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(chain)

            step1 = ApprovalStep(
                id=f"step_{i:03d}_1",
                chain_id=chain_id,
                step_order=1,
                step_name="Manager Approval",
                approver_role=UserRole.MANAGER,
                approver_id="user_mgr_1",
                status=StepStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
            step2 = ApprovalStep(
                id=f"step_{i:03d}_2",
                chain_id=chain_id,
                step_order=2,
                step_name="Finance Approval",
                approver_role=UserRole.FINANCE,
                approver_id="user_fin_1",
                status=StepStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
            session.add_all([step1, step2])

            pe = PolicyEvaluation(
                id=eval_id,
                request_id=req_id,
                policy_id="pol_v1",
                status=PolicyComplianceStatus.LIKELY_COMPLIANT,
                score=0.95,
                reason=f"Compliant request #{i}",
                citations=[{"section": "SEC-1", "line_number": 2, "snippet": "Direct business purpose."}],
                evaluated_at=datetime.now(timezone.utc),
            )
            session.add(pe)

        await session.commit()

    yield engine, session_maker
    await engine.dispose()


@pytest.mark.asyncio
async def test_dataloader_n_plus_one_reduction_benchmark(test_db):
    engine, session_maker = test_db
    n_requests = 20

    # 1. NAIVE RESOLUTION SIMULATION (N+1 Queries)
    # In a naive GraphQL implementation without DataLoader, fetching 20 requests with
    # nested requester, approval chain steps, and policy evaluation executes:
    # 1 (requests) + N (users) + N (chains) + N (policy evaluations) = 1 + 3N queries
    naive_query_count = 0
    async with session_maker() as session:
        with QueryCounter(collect_statements=True) as counter:
            req_res = await session.execute(select(SpendRequest))
            requests = req_res.scalars().all()
            for r in requests:
                # 1 query for requester
                await session.execute(select(User).where(User.id == r.requester_id))
                # 1 query for approval chain
                chain_res = await session.execute(
                    select(ApprovalChain).where(ApprovalChain.request_id == r.id)
                )
                chain = chain_res.scalar_one_or_none()
                if chain:
                    await session.execute(
                        select(ApprovalStep).where(ApprovalStep.chain_id == chain.id)
                    )
                # 1 query for policy evaluation
                await session.execute(
                    select(PolicyEvaluation).where(PolicyEvaluation.request_id == r.id)
                )
            naive_query_count = counter.count

    # 2. BATCHED RESOLUTION VIA STRAWBERRY DATALOADER
    graphql_query = """
    query GetSpendRequestsWithDetails {
        spendRequests {
            id
            title
            amount
            requester {
                id
                name
                email
            }
            approvalChain {
                id
                status
                steps {
                    id
                    stepName
                    status
                }
            }
            policyEvaluation {
                id
                status
                reason
                citations {
                    section
                    lineNumber
                    snippet
                }
            }
        }
    }
    """

    batched_query_count = 0
    async with session_maker() as session:
        loaders = AppDataLoaders(session)
        context = GraphQLContext(session=session, loaders=loaders, current_user=None)

        with QueryCounter(collect_statements=True) as counter:
            res = await schema.execute(graphql_query, context_value=context)
            assert res.errors is None, f"GraphQL errors: {res.errors}"
            assert len(res.data["spendRequests"]) == n_requests
            batched_query_count = counter.count

    reduction_pct = ((naive_query_count - batched_query_count) / naive_query_count) * 100.0

    print(f"\n================ N+1 DATALOADER BENCHMARK REPORT ================")
    print(f"Entities Fetched: {n_requests} SpendRequests + Requester + ApprovalChain + Steps + PolicyEvaluation")
    print(f"Naive Resolver Query Count (Without DataLoader): {naive_query_count} SQL queries")
    print(f"Batched Resolver Query Count (With DataLoader):    {batched_query_count} SQL queries")
    print(f"Query Count Reduction:                          {reduction_pct:.1f}% decrease ({naive_query_count} -> {batched_query_count})")
    print(f"=================================================================\n")

    # Assertions
    assert naive_query_count >= (1 + 3 * n_requests), "Naive count should be at least 1 + 3N"
    assert batched_query_count <= 5, f"Batched count should be <= 5 queries, got {batched_query_count}"
    assert naive_query_count > batched_query_count * 10, "DataLoader should reduce query count by > 10x"
