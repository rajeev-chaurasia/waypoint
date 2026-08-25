import enum
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.user import User, UserRole


class ChainStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StepStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"


class PolicyComplianceStatus(str, enum.Enum):
    LIKELY_COMPLIANT = "LIKELY_COMPLIANT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    LIKELY_VIOLATION = "LIKELY_VIOLATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ApprovalChain(Base):
    __tablename__ = "approval_chains"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("spend_requests.id"), unique=True, index=True, nullable=False
    )
    status: Mapped[ChainStatus] = mapped_column(
        Enum(ChainStatus, native_enum=False), default=ChainStatus.PENDING, nullable=False
    )
    current_step_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    request: Mapped["SpendRequest"] = relationship("SpendRequest", back_populates="approval_chain")
    steps: Mapped[list["ApprovalStep"]] = relationship(
        "ApprovalStep",
        back_populates="chain",
        cascade="all, delete-orphan",
        order_by="ApprovalStep.step_order",
    )


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chain_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("approval_chains.id"), index=True, nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    approver_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), nullable=False
    )
    approver_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[StepStatus] = mapped_column(
        Enum(StepStatus, native_enum=False), default=StepStatus.PENDING, nullable=False
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    chain: Mapped["ApprovalChain"] = relationship("ApprovalChain", back_populates="steps")
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approver_id])


class PolicyEvaluation(Base):
    __tablename__ = "policy_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("spend_requests.id"), unique=True, index=True, nullable=False
    )
    policy_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("policies.id"), nullable=True
    )
    status: Mapped[PolicyComplianceStatus] = mapped_column(
        Enum(PolicyComplianceStatus, native_enum=False), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    request: Mapped["SpendRequest"] = relationship("SpendRequest", back_populates="policy_evaluation")


from app.models.spend_request import SpendRequest  # noqa: E402
