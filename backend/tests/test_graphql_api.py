import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.core.database import Base, create_engine_and_session
from app.graphql.context import GraphQLContext
from app.graphql.dataloaders import AppDataLoaders
from app.graphql.schema import schema
from app.models.policy import Policy
from app.models.user import Department, User, UserRole


@pytest.fixture
async def api_test_db():
    engine, session_maker = create_engine_and_session("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        # Seed users
        users = [
            User(
                id="user_dev_sarah",
                email="sarah@company.com",
                name="Sarah Chen",
                role=UserRole.EMPLOYEE,
                department=Department.ENGINEERING,
                manager_id="user_mgr_marcus",
                spend_limit=500.0,
            ),
            User(
                id="user_mgr_marcus",
                email="marcus@company.com",
                name="Marcus Vance",
                role=UserRole.MANAGER,
                department=Department.ENGINEERING,
                spend_limit=10000.0,
            ),
            User(
                id="user_sec_elena",
                email="elena@company.com",
                name="Elena Rostova",
                role=UserRole.SECURITY,
                department=Department.ENGINEERING,
                spend_limit=25000.0,
            ),
            User(
                id="user_fin_david",
                email="david@company.com",
                name="David Miller",
                role=UserRole.FINANCE,
                department=Department.LEGAL_FINANCE,
                spend_limit=50000.0,
            ),
        ]
        session.add_all(users)

        policy = Policy(
            id="pol_v1",
            title="Global Spend Policy",
            version="1.0.0",
            is_active=True,
            content="Procurement Policy Guidelines",
        )
        session.add(policy)
        await session.commit()

    yield engine, session_maker
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_approve_spend_request_graphql_flow(api_test_db):
    engine, session_maker = api_test_db

    # 1. CREATE SPEND REQUEST MUTATION (SaaS > $1000 -> Manager + Security + Finance)
    create_mutation = """
    mutation CreateRequest($input: CreateSpendRequestInput!) {
        createSpendRequest(input: $input) {
            id
            title
            amount
            status
            category
            vendorName
            requester {
                name
                role
            }
            policyEvaluation {
                status
                citations {
                    section
                    lineNumber
                    snippet
                }
            }
            approvalChain {
                id
                status
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
    """
    mutation_vars = {
        "input": {
            "title": "Datadog APM Enterprise Subscription",
            "description": "Annual monitoring and APM infrastructure for production Kubernetes clusters.",
            "amount": 4200.00,
            "currency": "USD",
            "category": "SOFTWARE_SAAS",
            "vendorName": "Datadog Inc.",
            "department": "ENGINEERING",
            "requesterId": "user_dev_sarah",
        }
    }

    async with session_maker() as session:
        loaders = AppDataLoaders(session)
        ctx = GraphQLContext(session=session, loaders=loaders)
        res = await schema.execute(create_mutation, variable_values=mutation_vars, context_value=ctx)
        assert res.errors is None, f"Errors: {res.errors}"
        data = res.data["createSpendRequest"]
        assert data["title"] == "Datadog APM Enterprise Subscription"
        assert data["amount"] == 4200.00
        assert data["status"] == "PENDING_APPROVAL"
        assert data["requester"]["name"] == "Sarah Chen"
        assert data["policyEvaluation"]["status"] == "LIKELY_COMPLIANT"
        assert len(data["policyEvaluation"]["citations"]) > 0

        steps = data["approvalChain"]["steps"]
        assert len(steps) == 3
        assert steps[0]["approverRole"] == "MANAGER"
        assert steps[1]["approverRole"] == "SECURITY"
        assert steps[2]["approverRole"] == "FINANCE"

        step1_id = steps[0]["id"]
        step2_id = steps[1]["id"]
        step3_id = steps[2]["id"]
        req_id = data["id"]

    # 2. APPROVE STEP 1 (Manager Approval)
    approve_mutation = """
    mutation ApproveStep($input: ApproveStepInput!) {
        approveStep(input: $input) {
            id
            status
            comments
        }
    }
    """
    async with session_maker() as session:
        loaders = AppDataLoaders(session)
        ctx = GraphQLContext(session=session, loaders=loaders)
        res = await schema.execute(
            approve_mutation,
            variable_values={
                "input": {
                    "stepId": step1_id,
                    "approverId": "user_mgr_marcus",
                    "comments": "Approved for Q3 engineering budget.",
                }
            },
            context_value=ctx,
        )
        assert res.errors is None
        assert res.data["approveStep"]["status"] == "APPROVED"

    # 3. APPROVE STEP 2 (Security) & STEP 3 (Finance)
    async with session_maker() as session:
        loaders = AppDataLoaders(session)
        ctx = GraphQLContext(session=session, loaders=loaders)
        await schema.execute(
            approve_mutation,
            variable_values={
                "input": {
                    "stepId": step2_id,
                    "approverId": "user_sec_elena",
                    "comments": "SOC2 verified.",
                }
            },
            context_value=ctx,
        )
        res3 = await schema.execute(
            approve_mutation,
            variable_values={
                "input": {
                    "stepId": step3_id,
                    "approverId": "user_fin_david",
                    "comments": "PO issued.",
                }
            },
            context_value=ctx,
        )
        assert res3.errors is None

    # 4. QUERY REQUEST DETAIL AND VERIFY FINAL STATUS = APPROVED
    query_str = """
    query GetRequest($id: String!) {
        spendRequest(id: $id) {
            id
            status
            approvalChain {
                status
                steps {
                    stepOrder
                    status
                    comments
                }
            }
        }
    }
    """
    async with session_maker() as session:
        loaders = AppDataLoaders(session)
        ctx = GraphQLContext(session=session, loaders=loaders)
        res = await schema.execute(query_str, variable_values={"id": req_id}, context_value=ctx)
        assert res.errors is None
        req = res.data["spendRequest"]
        assert req["status"] == "APPROVED"
        assert req["approvalChain"]["status"] == "APPROVED"
        for s in req["approvalChain"]["steps"]:
            assert s["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_system_metrics_query(api_test_db):
    engine, session_maker = api_test_db
    query_str = """
    query GetMetrics {
        systemMetrics {
            totalRequests
            totalSpendAmount
            pendingApprovals
            dataloaderEfficiencyRatio
        }
    }
    """
    async with session_maker() as session:
        loaders = AppDataLoaders(session)
        ctx = GraphQLContext(session=session, loaders=loaders)
        res = await schema.execute(query_str, context_value=ctx)
        assert res.errors is None
        metrics = res.data["systemMetrics"]
        assert "totalRequests" in metrics
        assert "dataloaderEfficiencyRatio" in metrics
