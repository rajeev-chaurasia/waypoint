import enum
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    FINANCE = "FINANCE"
    LEGAL = "LEGAL"
    SECURITY = "SECURITY"
    EXEC = "EXEC"
    ADMIN = "ADMIN"


class Department(str, enum.Enum):
    ENGINEERING = "ENGINEERING"
    PRODUCT = "PRODUCT"
    SALES = "SALES"
    MARKETING = "MARKETING"
    OPERATIONS = "OPERATIONS"
    LEGAL_FINANCE = "LEGAL_FINANCE"
    GENERAL_ADMIN = "GENERAL_ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), default=UserRole.EMPLOYEE, nullable=False
    )
    department: Mapped[Department] = mapped_column(
        Enum(Department, native_enum=False), default=Department.ENGINEERING, nullable=False
    )
    manager_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    spend_limit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    manager: Mapped["User | None"] = relationship("User", remote_side=[id], lazy="selectin")
