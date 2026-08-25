from typing import Any
import strawberry
from strawberry.types import Info
from app.graphql.context import GraphQLContext
from app.graphql.types import (
    ApprovalStepType,
    ApproveStepInput,
    CreateSpendRequestInput,
    RejectStepInput,
    SpendRequestType,
)
from app.services.request_service import RequestService


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_spend_request(
        self, info: Info[GraphQLContext, Any], input: CreateSpendRequestInput
    ) -> SpendRequestType:
        spend_req = await RequestService.create_request(
            session=info.context.session,
            title=input.title,
            description=input.description,
            amount=input.amount,
            currency=input.currency,
            category=input.category,
            vendor_name=input.vendor_name,
            department=input.department,
            requester_id=input.requester_id,
        )
        return SpendRequestType.from_model(spend_req)

    @strawberry.mutation
    async def approve_step(
        self, info: Info[GraphQLContext, Any], input: ApproveStepInput
    ) -> ApprovalStepType:
        step = await RequestService.approve_step(
            session=info.context.session,
            step_id=input.step_id,
            approver_id=input.approver_id,
            comments=input.comments,
        )
        return ApprovalStepType.from_model(step)

    @strawberry.mutation
    async def reject_step(
        self, info: Info[GraphQLContext, Any], input: RejectStepInput
    ) -> ApprovalStepType:
        step = await RequestService.reject_step(
            session=info.context.session,
            step_id=input.step_id,
            approver_id=input.approver_id,
            comments=input.comments,
        )
        return ApprovalStepType.from_model(step)
