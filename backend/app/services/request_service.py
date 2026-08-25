import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
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
from app.services.policy_engine import PolicyEngine
from app.services.routing_engine import RoutingEngine


class RequestService:
    @staticmethod
    async def create_request(
        session: AsyncSession,
        title: str,
        description: str,
        amount: float,
        currency: str,
        category: SpendCategory,
        vendor_name: str,
        department: Department,
        requester_id: str,
    ) -> SpendRequest:
        # 1. Fetch requester
        user_res = await session.execute(select(User).where(User.id == requester_id))
        requester = user_res.scalar_one_or_none()
        if not requester:
            raise ValueError(f"Requester with id '{requester_id}' not found.")

        # 2. Fetch active policy
        policy_res = await session.execute(
            select(Policy).where(Policy.is_active == True).limit(1)  # noqa: E712
        )
        active_policy = policy_res.scalar_one_or_none()

        # 3. Run Policy Check Agent
        policy_engine = PolicyEngine()
        eval_result = policy_engine.evaluate_request(
            title=title,
            description=description,
            amount=amount,
            category=category,
            vendor_name=vendor_name,
            department=department.value,
        )

        # 4. Generate Deterministic Approval Chain
        planned_steps = RoutingEngine.generate_approval_route(
            amount=amount,
            category=category,
            department=department,
            requester=requester,
            policy_status=eval_result.status,
        )

        request_id = str(uuid.uuid4())
        chain_id = str(uuid.uuid4())
        eval_id = str(uuid.uuid4())

        # 5. Build SpendRequest model
        new_request = SpendRequest(
            id=request_id,
            title=title,
            description=description,
            amount=amount,
            currency=currency,
            category=category,
            vendor_name=vendor_name,
            department=department,
            requester_id=requester_id,
            status=RequestStatus.PENDING_APPROVAL,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(new_request)

        # 6. Build PolicyEvaluation model
        new_eval = PolicyEvaluation(
            id=eval_id,
            request_id=request_id,
            policy_id=active_policy.id if active_policy else None,
            status=eval_result.status,
            score=eval_result.score,
            reason=eval_result.reason,
            citations=eval_result.citations,
            evaluated_at=datetime.now(timezone.utc),
        )
        session.add(new_eval)

        # 7. Build ApprovalChain and ApprovalSteps
        new_chain = ApprovalChain(
            id=chain_id,
            request_id=request_id,
            status=ChainStatus.PENDING,
            current_step_order=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(new_chain)

        # Match approvers based on role and department
        for p_step in planned_steps:
            approver_id = p_step.approver_id
            if not approver_id:
                # Find default user with matching role
                app_res = await session.execute(
                    select(User).where(User.role == p_step.approver_role).limit(1)
                )
                matching_user = app_res.scalar_one_or_none()
                if matching_user:
                    approver_id = matching_user.id

            step_model = ApprovalStep(
                id=str(uuid.uuid4()),
                chain_id=chain_id,
                step_order=p_step.step_order,
                step_name=p_step.step_name,
                approver_role=p_step.approver_role,
                approver_id=approver_id,
                status=StepStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
            session.add(step_model)

        await session.commit()
        await session.refresh(new_request)
        return new_request

    @staticmethod
    async def approve_step(
        session: AsyncSession,
        step_id: str,
        approver_id: str,
        comments: str | None = None,
    ) -> ApprovalStep:
        res = await session.execute(
            select(ApprovalStep).where(ApprovalStep.id == step_id)
        )
        step = res.scalar_one_or_none()
        if not step:
            raise ValueError(f"ApprovalStep with id '{step_id}' not found.")

        chain_res = await session.execute(
            select(ApprovalChain).where(ApprovalChain.id == step.chain_id)
        )
        chain = chain_res.scalar_one_or_none()
        if not chain:
            raise ValueError("ApprovalChain not found.")

        req_res = await session.execute(
            select(SpendRequest).where(SpendRequest.id == chain.request_id)
        )
        spend_req = req_res.scalar_one_or_none()
        if not spend_req:
            raise ValueError("SpendRequest not found.")

        step.status = StepStatus.APPROVED
        step.approver_id = approver_id
        step.comments = comments
        step.decision_at = datetime.now(timezone.utc)

        # Check remaining steps in chain
        all_steps_res = await session.execute(
            select(ApprovalStep)
            .where(ApprovalStep.chain_id == chain.id)
            .order_by(ApprovalStep.step_order)
        )
        all_steps = all_steps_res.scalars().all()

        next_steps = [
            s for s in all_steps if s.step_order > step.step_order and s.status == StepStatus.PENDING
        ]
        if next_steps:
            chain.current_step_order = next_steps[0].step_order
        else:
            # All steps completed
            chain.status = ChainStatus.APPROVED
            spend_req.status = RequestStatus.APPROVED
            spend_req.updated_at = datetime.now(timezone.utc)

        chain.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(step)
        return step

    @staticmethod
    async def reject_step(
        session: AsyncSession,
        step_id: str,
        approver_id: str,
        comments: str,
    ) -> ApprovalStep:
        res = await session.execute(
            select(ApprovalStep).where(ApprovalStep.id == step_id)
        )
        step = res.scalar_one_or_none()
        if not step:
            raise ValueError(f"ApprovalStep with id '{step_id}' not found.")

        chain_res = await session.execute(
            select(ApprovalChain).where(ApprovalChain.id == step.chain_id)
        )
        chain = chain_res.scalar_one_or_none()
        if not chain:
            raise ValueError("ApprovalChain not found.")

        req_res = await session.execute(
            select(SpendRequest).where(SpendRequest.id == chain.request_id)
        )
        spend_req = req_res.scalar_one_or_none()
        if not spend_req:
            raise ValueError("SpendRequest not found.")

        step.status = StepStatus.REJECTED
        step.approver_id = approver_id
        step.comments = comments
        step.decision_at = datetime.now(timezone.utc)

        chain.status = ChainStatus.REJECTED
        spend_req.status = RequestStatus.REJECTED
        spend_req.updated_at = datetime.utcnow()
        chain.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(step)
        return step
