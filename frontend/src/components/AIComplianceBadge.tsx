import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';
import { PolicyComplianceStatus } from '../types';

interface Props {
  status?: PolicyComplianceStatus;
  score?: number;
  showScore?: boolean;
}

export const AIComplianceBadge: React.FC<Props> = ({
  status = 'LIKELY_COMPLIANT',
  score,
  showScore = false,
}) => {
  switch (status) {
    case 'LIKELY_COMPLIANT':
      return (
        <span className="badge badge-compliant" title="Policy Agent: Compliant with written company policy">
          <CheckCircle2 size={13} />
          Likely Compliant
          {showScore && score !== undefined && <span style={{ opacity: 0.75 }}>({Math.round(score * 100)}%)</span>}
        </span>
      );
    case 'NEEDS_REVIEW':
      return (
        <span className="badge badge-review" title="Policy Agent: Requires compliance review or governance sign-off">
          <AlertTriangle size={13} />
          Needs Review
          {showScore && score !== undefined && <span style={{ opacity: 0.75 }}>({Math.round(score * 100)}%)</span>}
        </span>
      );
    case 'LIKELY_VIOLATION':
      return (
        <span className="badge badge-violation" title="Policy Agent: Potential policy violation detected">
          <XCircle size={13} />
          Likely Violation
          {showScore && score !== undefined && <span style={{ opacity: 0.75 }}>({Math.round(score * 100)}%)</span>}
        </span>
      );
    case 'INSUFFICIENT_EVIDENCE':
      return (
        <span className="badge badge-insufficient" title="Policy Agent: Lacks itemized details or verified vendor">
          <HelpCircle size={13} />
          Insufficient Evidence
        </span>
      );
    default:
      return null;
  }
};
