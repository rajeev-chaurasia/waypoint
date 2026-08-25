import enum
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.user import Department, User


class SpendCategory(str, enum.Enum):
    SOFTWARE_SAAS = "SOFTWARE_SAAS"
    HARDWARE = "HARDWARE"
    CONSULTING_CONTRACTOR = "CONSULTING_CONTRACTOR"
    TRAVEL_ENTERTAINMENT = "TRAVEL_ENTERTAINMENT"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    MARKETING_ADS = "MARKETING_ADS"
    OTHER = "OTHER"


class RequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class SpendRequest(Base):
    __tablename__ = "spend_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    category: Mapped[SpendCategory] = mapped_column(
        Enum(SpendCategory, native_enum=False), nullable=False
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[Department] = mapped_column(
        Enum(Department, native_enum=False), nullable=False
    )
    requester_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, native_enum=False),
        default=RequestStatus.PENDING_APPROVAL,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id])
    approval_chain: Mapped["ApprovalChain | None"] = relationship(
        "ApprovalChain", back_populates="request", uselist=False, cascade="all, delete-orphan"
    )
    policy_evaluation: Mapped["PolicyEvaluation | None"] = relationship(
        "PolicyEvaluation",
        back_populates="request",
        uselist=False,
        cascade="all, delete-orphan",
    )


from app.models.approval import ApprovalChain, PolicyEvaluation  # noqa: E402
