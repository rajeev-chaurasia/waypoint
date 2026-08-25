from typing import Any, Optional
import strawberry
from sqlalchemy import func, select
from strawberry.types import Info
from app.graphql.context import GraphQLContext
from app.graphql.types import (
    ApprovalStepType,
    Department,
    PolicyComplianceStatus,
    PolicyType,
    RequestStatus,
    SpendCategory,
    SpendRequestType,
    SystemMetricsType,
    UserRole,
    UserType,
)
from app.models.approval import (
    ApprovalChain,
    ApprovalStep,
    PolicyComplianceStatus as PolStatusEnum,
    PolicyEvaluation,
    StepStatus,
)
from app.models.policy import Policy
from app.models.spend_request import SpendRequest
from app.models.user import User


@strawberry.type
class Query:
    @strawberry.field
    async def spend_requests(
        self,
        info: Info[GraphQLContext, Any],
        category: Optional[SpendCategory] = None,
        status: Optional[RequestStatus] = None,
        department: Optional[Department] = None,
    ) -> list[SpendRequestType]:
        stmt = select(SpendRequest).order_by(SpendRequest.created_at.desc())
        if category:
            stmt = stmt.where(SpendRequest.category == category)
        if status:
            stmt = stmt.where(SpendRequest.status == status)
        if department:
            stmt = stmt.where(SpendRequest.department == department)

        result = await info.context.execute(stmt)
        requests = result.scalars().all()
        return [SpendRequestType.from_model(r) for r in requests]

    @strawberry.field
    async def spend_request(
        self, info: Info[GraphQLContext, Any], id: str
    ) -> Optional[SpendRequestType]:
        stmt = select(SpendRequest).where(SpendRequest.id == id)
        result = await info.context.execute(stmt)
        request = result.scalar_one_or_none()
        return SpendRequestType.from_model(request) if request else None

    @strawberry.field
    async def approval_queue(
        self,
        info: Info[GraphQLContext, Any],
        role: Optional[UserRole] = None,
        approver_id: Optional[str] = None,
        status: Optional[StepStatus] = None,
    ) -> list[ApprovalStepType]:
        stmt = select(ApprovalStep).order_by(ApprovalStep.created_at.desc())
        if role:
            stmt = stmt.where(ApprovalStep.approver_role == role)
        if approver_id:
            stmt = stmt.where(ApprovalStep.approver_id == approver_id)
        if status:
            stmt = stmt.where(ApprovalStep.status == status)

        result = await info.context.execute(stmt)
        steps = result.scalars().all()
        return [ApprovalStepType.from_model(s) for s in steps]

    @strawberry.field
    async def users(
        self, info: Info[GraphQLContext, Any], role: Optional[UserRole] = None
    ) -> list[UserType]:
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == role)
        result = await info.context.execute(stmt)
        users = result.scalars().all()
        return [UserType.from_model(u) for u in users]

    @strawberry.field
    async def current_user(
        self, info: Info[GraphQLContext, Any], user_id: Optional[str] = None
    ) -> Optional[UserType]:
        target_id = user_id or "user_sarah_emp"
        stmt = select(User).where(User.id == target_id)
        result = await info.context.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            # Fallback to any user
            fallback_res = await info.context.execute(select(User).limit(1))
            user = fallback_res.scalar_one_or_none()
        return UserType.from_model(user) if user else None

    @strawberry.field
    async def policies(
        self, info: Info[GraphQLContext, Any], active_only: bool = True
    ) -> list[PolicyType]:
        stmt = select(Policy)
        if active_only:
            stmt = stmt.where(Policy.is_active == True)  # noqa: E712
        result = await info.context.execute(stmt)
        policies = result.scalars().all()
        return [PolicyType.from_model(p) for p in policies]

    @strawberry.field
    async def system_metrics(
        self, info: Info[GraphQLContext, Any]
    ) -> SystemMetricsType:
        # Total counts
        total_req_res = await info.context.execute(select(func.count(SpendRequest.id)))
        total_requests = total_req_res.scalar() or 0

        spend_sum_res = await info.context.execute(select(func.sum(SpendRequest.amount)))
        total_spend = spend_sum_res.scalar() or 0.0

        pending_res = await info.context.execute(
            select(func.count(SpendRequest.id)).where(
                SpendRequest.status == RequestStatus.PENDING_APPROVAL
            )
        )
        pending_count = pending_res.scalar() or 0

        approved_res = await info.context.execute(
            select(func.count(SpendRequest.id)).where(
                SpendRequest.status == RequestStatus.APPROVED
            )
        )
        approved_count = approved_res.scalar() or 0

        rejected_res = await info.context.execute(
            select(func.count(SpendRequest.id)).where(
                SpendRequest.status == RequestStatus.REJECTED
            )
        )
        rejected_count = rejected_res.scalar() or 0

        compliant_res = await info.context.execute(
            select(func.count(PolicyEvaluation.id)).where(
                PolicyEvaluation.status == PolStatusEnum.LIKELY_COMPLIANT
            )
        )
        compliant_count = compliant_res.scalar() or 0

        flagged_res = await info.context.execute(
            select(func.count(PolicyEvaluation.id)).where(
                PolicyEvaluation.status.in_(
                    [
                        PolStatusEnum.NEEDS_REVIEW,
                        PolStatusEnum.LIKELY_VIOLATION,
                        PolStatusEnum.INSUFFICIENT_EVIDENCE,
                    ]
                )
            )
        )
        flagged_count = flagged_res.scalar() or 0

        # DataLoader efficiency calculation: (1 + 3*N queries) / 4 queries
        ratio = (
            ((1 + 3 * total_requests) / 4.0)
            if total_requests > 0
            else 1.0
        )

        return SystemMetricsType(
            total_requests=total_requests,
            total_spend_amount=round(total_spend, 2),
            pending_approvals=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            policy_compliant_count=compliant_count,
            policy_flagged_count=flagged_count,
            dataloader_efficiency_ratio=round(ratio, 2),
        )
