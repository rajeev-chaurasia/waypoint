export type UserRole =
  | 'EMPLOYEE'
  | 'MANAGER'
  | 'FINANCE'
  | 'LEGAL'
  | 'SECURITY'
  | 'EXEC'
  | 'ADMIN';

export type Department =
  | 'ENGINEERING'
  | 'PRODUCT'
  | 'SALES'
  | 'MARKETING'
  | 'OPERATIONS'
  | 'LEGAL_FINANCE'
  | 'GENERAL_ADMIN';

export type SpendCategory =
  | 'SOFTWARE_SAAS'
  | 'HARDWARE'
  | 'CONSULTING_CONTRACTOR'
  | 'TRAVEL_ENTERTAINMENT'
  | 'OFFICE_SUPPLIES'
  | 'MARKETING_ADS'
  | 'OTHER';

export type RequestStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED';

export type ChainStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export type StepStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'SKIPPED';

export type PolicyComplianceStatus =
  | 'LIKELY_COMPLIANT'
  | 'NEEDS_REVIEW'
  | 'LIKELY_VIOLATION'
  | 'INSUFFICIENT_EVIDENCE';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  department: Department;
  managerId?: string | null;
  spendLimit: number;
}

export interface PolicyCitation {
  section: string;
  lineNumber: number;
  snippet: string;
  relevance: string;
}

export interface PolicyEvaluation {
  id: string;
  requestId: string;
  policyId?: string | null;
  status: PolicyComplianceStatus;
  score: number;
  reason: string;
  citations: PolicyCitation[];
  modelProvider?: string | null;
  evaluatedAt: string;
}

export interface ApprovalStep {
  id: string;
  chainId: string;
  stepOrder: number;
  stepName: string;
  approverRole: UserRole;
  approverId?: string | null;
  status: StepStatus;
  comments?: string | null;
  decisionAt?: string | null;
  approver?: User | null;
}

export interface ApprovalChain {
  id: string;
  requestId: string;
  status: ChainStatus;
  currentStepOrder: number;
  steps: ApprovalStep[];
}

export interface SpendRequest {
  id: string;
  title: string;
  description: string;
  amount: number;
  currency: string;
  category: SpendCategory;
  vendorName: string;
  department: Department;
  requesterId: string;
  status: RequestStatus;
  createdAt: string;
  updatedAt: string;
  requester?: User | null;
  approvalChain?: ApprovalChain | null;
  policyEvaluation?: PolicyEvaluation | null;
}

export interface Policy {
  id: string;
  title: string;
  version: string;
  isActive: boolean;
  content: string;
}

export interface SystemMetrics {
  totalRequests: number;
  totalSpendAmount: number;
  pendingApprovals: number;
  approvedCount: number;
  rejectedCount: number;
  policyCompliantCount: number;
  policyFlaggedCount: number;
  dataloaderEfficiencyRatio: number;
}
