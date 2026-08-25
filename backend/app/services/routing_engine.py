from dataclasses import dataclass
from app.models.approval import PolicyComplianceStatus
from app.models.spend_request import SpendCategory
from app.models.user import Department, User, UserRole


@dataclass
class PlannedApprovalStep:
    step_order: int
    step_name: str
    approver_role: UserRole
    description: str
    approver_id: str | None = None


class RoutingEngine:
    """Calculates deterministic multi-tier approval chains based on spend thresholds and categories."""

    @staticmethod
    def generate_approval_route(
        amount: float,
        category: SpendCategory | str,
        department: Department | str | None = None,
        requester: User | None = None,
        policy_status: PolicyComplianceStatus | str | None = None,
    ) -> list[PlannedApprovalStep]:
        if amount <= 0:
            raise ValueError("Spend amount must be strictly greater than $0.00")

        cat = category.value if isinstance(category, SpendCategory) else str(category)
        pol_status = (
            policy_status.value
            if isinstance(policy_status, PolicyComplianceStatus)
            else (str(policy_status) if policy_status else None)
        )

        steps: list[PlannedApprovalStep] = []
        step_order = 1

        # Tier 1: Direct Manager Approval (Always required)
        manager_id = requester.manager_id if requester else None
        steps.append(
            PlannedApprovalStep(
                step_order=step_order,
                step_name="Direct Manager Approval",
                approver_role=UserRole.MANAGER,
                description="Initial verification of business purpose and budget allocation by line manager.",
                approver_id=manager_id,
            )
        )
        step_order += 1

        # Tier 2: Category & Domain Specific Governance
        if cat == SpendCategory.SOFTWARE_SAAS.value or cat == "SOFTWARE_SAAS":
            if amount > 1000.00:
                steps.append(
                    PlannedApprovalStep(
                        step_order=step_order,
                        step_name="Security & IT Architecture Review",
                        approver_role=UserRole.SECURITY,
                        description="SOC2, data privacy, and architecture review for SaaS vendor.",
                    )
                )
                step_order += 1

        elif cat == SpendCategory.HARDWARE.value or cat == "HARDWARE":
            if amount > 500.00:
                steps.append(
                    PlannedApprovalStep(
                        step_order=step_order,
                        step_name="IT Hardware Procurement Review",
                        approver_role=UserRole.SECURITY,
                        description="Verification of standard hardware asset specifications and vendor compatibility.",
                    )
                )
                step_order += 1

        elif cat == SpendCategory.CONSULTING_CONTRACTOR.value or cat == "CONSULTING_CONTRACTOR":
            if amount > 5000.00:
                steps.append(
                    PlannedApprovalStep(
                        step_order=step_order,
                        step_name="Legal & Contractor Governance Review",
                        approver_role=UserRole.LEGAL,
                        description="Review of Statement of Work (SOW), IP assignment, and contractor terms.",
                    )
                )
                step_order += 1

        # Policy Alert Step (If flagged as needs review or violation)
        if pol_status in [
            PolicyComplianceStatus.NEEDS_REVIEW.value,
            PolicyComplianceStatus.LIKELY_VIOLATION.value,
            PolicyComplianceStatus.INSUFFICIENT_EVIDENCE.value,
        ]:
            steps.append(
                PlannedApprovalStep(
                    step_order=step_order,
                    step_name="Compliance & Policy Exception Review",
                    approver_role=UserRole.LEGAL,
                    description=f"Automated policy auditor flagged: {pol_status}. Requires compliance review before disbursement.",
                )
            )
            step_order += 1

        # Tier 3: Finance Review (Threshold >= $500.00)
        if amount >= 500.00:
            steps.append(
                PlannedApprovalStep(
                    step_order=step_order,
                    step_name="Finance & Controller Review",
                    approver_role=UserRole.FINANCE,
                    description="General ledger coding, sales tax, and treasury cash flow authorization.",
                )
            )
            step_order += 1

        # Tier 4: VP & Executive Sign-off (Threshold >= $10,000.00)
        if amount >= 10000.00:
            steps.append(
                PlannedApprovalStep(
                    step_order=step_order,
                    step_name="Executive VP Sign-Off",
                    approver_role=UserRole.EXEC,
                    description="Executive authorization for high-value expenditure.",
                )
            )
            step_order += 1

        # Tier 5: Board / CEO Authorization (Threshold >= $50,000.00)
        if amount >= 50000.00:
            steps.append(
                PlannedApprovalStep(
                    step_order=step_order,
                    step_name="Board & CEO Authorization",
                    approver_role=UserRole.ADMIN,
                    description="Formal authorization by CEO and Board for material commitments.",
                )
            )
            step_order += 1

        return steps
