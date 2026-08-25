import asyncio
from collections import defaultdict
from strawberry.dataloader import DataLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.approval import ApprovalChain, ApprovalStep, PolicyEvaluation
from app.models.user import User


async def load_users_by_id(
    keys: list[str], session: AsyncSession, lock: asyncio.Lock
) -> list[User | None]:
    if not keys:
        return []
    async with lock:
        result = await session.execute(select(User).where(User.id.in_(keys)))
        users_by_id = {user.id: user for user in result.scalars().all()}
    return [users_by_id.get(key) for key in keys]


async def load_chains_by_request_id(
    keys: list[str], session: AsyncSession, lock: asyncio.Lock
) -> list[ApprovalChain | None]:
    if not keys:
        return []
    async with lock:
        result = await session.execute(
            select(ApprovalChain).where(ApprovalChain.request_id.in_(keys))
        )
        chains_by_req = {chain.request_id: chain for chain in result.scalars().all()}
    return [chains_by_req.get(key) for key in keys]


async def load_steps_by_chain_id(
    keys: list[str], session: AsyncSession, lock: asyncio.Lock
) -> list[list[ApprovalStep]]:
    if not keys:
        return []
    async with lock:
        result = await session.execute(
            select(ApprovalStep)
            .where(ApprovalStep.chain_id.in_(keys))
            .order_by(ApprovalStep.step_order)
        )
        steps_by_chain: dict[str, list[ApprovalStep]] = defaultdict(list)
        for step in result.scalars().all():
            steps_by_chain[step.chain_id].append(step)
    return [steps_by_chain.get(key, []) for key in keys]


async def load_policy_eval_by_request_id(
    keys: list[str], session: AsyncSession, lock: asyncio.Lock
) -> list[PolicyEvaluation | None]:
    if not keys:
        return []
    async with lock:
        result = await session.execute(
            select(PolicyEvaluation).where(PolicyEvaluation.request_id.in_(keys))
        )
        evals_by_req = {pe.request_id: pe for pe in result.scalars().all()}
    return [evals_by_req.get(key) for key in keys]


class AppDataLoaders:
    def __init__(self, session: AsyncSession, lock: asyncio.Lock | None = None):
        self.session = session
        self.lock = lock or asyncio.Lock()
        self.user_loader = DataLoader(
            load_fn=lambda keys: load_users_by_id(keys, self.session, self.lock)
        )
        self.chain_by_request_loader = DataLoader(
            load_fn=lambda keys: load_chains_by_request_id(keys, self.session, self.lock)
        )
        self.steps_by_chain_loader = DataLoader(
            load_fn=lambda keys: load_steps_by_chain_id(keys, self.session, self.lock)
        )
        self.policy_eval_by_request_loader = DataLoader(
            load_fn=lambda keys: load_policy_eval_by_request_id(
                keys, self.session, self.lock
            )
        )
