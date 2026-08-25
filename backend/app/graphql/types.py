from datetime import datetime
from typing import Any, Optional
import strawberry
from strawberry.types import Info
from app.graphql.context import GraphQLContext
from app.models.approval import (
    ApprovalChain as ApprovalChainModel,
    ApprovalStep as ApprovalStepModel,
    ChainStatus,
    PolicyComplianceStatus,
    PolicyEvaluation as PolicyEvaluationModel,
    StepStatus,
)
from app.models.policy import Policy as PolicyModel
from app.models.spend_request import (
    RequestStatus,
    SpendCategory,
    SpendRequest as SpendRequestModel,
)
from app.models.user import Department, User as UserModel, UserRole

# Register Strawberry Enums
strawberry.enum(UserRole, name="UserRole")
strawberry.enum(Department, name="Department")
strawberry.enum(SpendCategory, name="SpendCategory")
strawberry.enum(RequestStatus, name="RequestStatus")
strawberry.enum(ChainStatus, name="ChainStatus")
strawberry.enum(StepStatus, name="StepStatus")
strawberry.enum(PolicyComplianceStatus, name="PolicyComplianceStatus")


@strawberry.type
class UserType:
    id: str
    email: str
    name: str
    role: UserRole
    department: Department
    manager_id: Optional[str]
    spend_limit: float
    created_at: datetime

    @classmethod
    def from_model(cls, model: UserModel) -> "UserType":
        return cls(
            id=model.id,
            email=model.email,
            name=model.name,
            role=model.role,
            department=model.department,
            manager_id=model.manager_id,
            spend_limit=model.spend_limit,
            created_at=model.created_at,
        )


@strawberry.type
class PolicyCitationType:
    section: str
    line_number: int
    snippet: str
    relevance: str


@strawberry.type
class PolicyEvaluationType:
    id: str
    request_id: str
    policy_id: Optional[str]
    status: PolicyComplianceStatus
    score: float
    reason: str
    citations: list[PolicyCitationType]
    model_provider: Optional[str]
    evaluated_at: datetime

    @classmethod
    def from_model(cls, model: PolicyEvaluationModel) -> "PolicyEvaluationType":
        raw_citations = model.citations or []
        citations = [
            PolicyCitationType(
                section=c.get("section", "SEC-1"),
                line_number=int(c.get("line_number", 1)),
                snippet=c.get("snippet", ""),
                relevance=c.get("relevance", ""),
            )
            for c in raw_citations
        ]
        return cls(
            id=model.id,
            request_id=model.request_id,
            policy_id=model.policy_id,
            status=model.status,
            score=model.score,
            reason=model.reason,
            citations=citations,
            model_provider=getattr(model, "model_provider", "deterministic-rule-engine") or "deterministic-rule-engine",
            evaluated_at=model.evaluated_at,
        )


@strawberry.type
class ApprovalStepType:
    id: str
    chain_id: str
    step_order: int
    step_name: str
    approver_role: UserRole
    approver_id: Optional[str]
    status: StepStatus
    comments: Optional[str]
    decision_at: Optional[datetime]
    created_at: datetime

    @classmethod
    def from_model(cls, model: ApprovalStepModel) -> "ApprovalStepType":
        return cls(
            id=model.id,
            chain_id=model.chain_id,
            step_order=model.step_order,
            step_name=model.step_name,
            approver_role=model.approver_role,
            approver_id=model.approver_id,
            status=model.status,
            comments=model.comments,
            decision_at=model.decision_at,
            created_at=model.created_at,
        )

    @strawberry.field
    async def approver(self, info: Info[GraphQLContext, Any]) -> Optional[UserType]:
        if not self.approver_id:
            return None
        user = await info.context.loaders.user_loader.load(self.approver_id)
        return UserType.from_model(user) if user else None


@strawberry.type
class ApprovalChainType:
    id: str
    request_id: str
    status: ChainStatus
    current_step_order: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: ApprovalChainModel) -> "ApprovalChainType":
        return cls(
            id=model.id,
            request_id=model.request_id,
            status=model.status,
            current_step_order=model.current_step_order,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @strawberry.field
    async def steps(self, info: Info[GraphQLContext, Any]) -> list[ApprovalStepType]:
        steps = await info.context.loaders.steps_by_chain_loader.load(self.id)
        return [ApprovalStepType.from_model(s) for s in steps]


@strawberry.type
class SpendRequestType:
    id: str
    title: str
    description: str
    amount: float
    currency: str
    category: SpendCategory
    vendor_name: str
    department: Department
    requester_id: str
    status: RequestStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: SpendRequestModel) -> "SpendRequestType":
        return cls(
            id=model.id,
            title=model.title,
            description=model.description,
            amount=model.amount,
            currency=model.currency,
            category=model.category,
            vendor_name=model.vendor_name,
            department=model.department,
            requester_id=model.requester_id,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @strawberry.field
    async def requester(self, info: Info[GraphQLContext, Any]) -> Optional[UserType]:
        user = await info.context.loaders.user_loader.load(self.requester_id)
        return UserType.from_model(user) if user else None

    @strawberry.field
    async def approval_chain(
        self, info: Info[GraphQLContext, Any]
    ) -> Optional[ApprovalChainType]:
        chain = await info.context.loaders.chain_by_request_loader.load(self.id)
        return ApprovalChainType.from_model(chain) if chain else None

    @strawberry.field
    async def policy_evaluation(
        self, info: Info[GraphQLContext, Any]
    ) -> Optional[PolicyEvaluationType]:
        evaluation = await info.context.loaders.policy_eval_by_request_loader.load(self.id)
        return PolicyEvaluationType.from_model(evaluation) if evaluation else None


@strawberry.type
class PolicyType:
    id: str
    title: str
    version: str
    is_active: bool
    content: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: PolicyModel) -> "PolicyType":
        return cls(
            id=model.id,
            title=model.title,
            version=model.version,
            is_active=model.is_active,
            content=model.content,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


@strawberry.type
class SystemMetricsType:
    total_requests: int
    total_spend_amount: float
    pending_approvals: int
    approved_count: int
    rejected_count: int
    policy_compliant_count: int
    policy_flagged_count: int
    dataloader_efficiency_ratio: float


@strawberry.input
class CreateSpendRequestInput:
    title: str
    description: str
    amount: float
    currency: str = "USD"
    category: SpendCategory
    vendor_name: str
    department: Department
    requester_id: str


@strawberry.input
class ApproveStepInput:
    step_id: str
    approver_id: str
    comments: Optional[str] = None


@strawberry.input
class RejectStepInput:
    step_id: str
    approver_id: str
    comments: str
