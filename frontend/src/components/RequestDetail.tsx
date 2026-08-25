import React, { useState } from 'react';
import { useMutation } from '@apollo/client';
import {
  X,
  CheckCircle2,
  XCircle,
  ShieldCheck,
} from 'lucide-react';
import { APPROVE_STEP, REJECT_STEP } from '../graphql/mutations';
import { GET_SPEND_REQUESTS, GET_SYSTEM_METRICS } from '../graphql/queries';
import { SpendRequest, User } from '../types';
import { AIComplianceBadge } from './AIComplianceBadge';

interface Props {
  request: SpendRequest;
  currentUser: User;
  onClose: () => void;
  onViewPolicyCitation?: (section: string, lineNumber: number) => void;
}

export const RequestDetail: React.FC<Props> = ({
  request,
  currentUser,
  onClose,
  onViewPolicyCitation,
}) => {
  const [comment, setComment] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  const [approveStep, { loading: approving }] = useMutation(APPROVE_STEP, {
    refetchQueries: [{ query: GET_SPEND_REQUESTS }, { query: GET_SYSTEM_METRICS }],
  });

  const [rejectStep, { loading: rejecting }] = useMutation(REJECT_STEP, {
    refetchQueries: [{ query: GET_SPEND_REQUESTS }, { query: GET_SYSTEM_METRICS }],
  });

  const currentStep = request.approvalChain?.steps.find(
    (s) => s.stepOrder === request.approvalChain?.currentStepOrder && s.status === 'PENDING'
  );

  const canUserApprove =
    request.status === 'PENDING_APPROVAL' &&
    currentStep &&
    (currentUser.role === currentStep.approverRole ||
      currentUser.role === 'ADMIN' ||
      currentUser.id === currentStep.approverId);

  const handleApprove = async () => {
    if (!currentStep) return;
    try {
      setActionError(null);
      await approveStep({
        variables: {
          input: {
            stepId: currentStep.id,
            approverId: currentUser.id,
            comments: comment || `Approved by ${currentUser.name} (${currentUser.role})`,
          },
        },
      });
      setComment('');
      onClose();
    } catch (err: any) {
      setActionError(err.message || 'Failed to approve step');
    }
  };

  const handleReject = async () => {
    if (!currentStep) return;
    if (!comment.trim()) {
      setActionError('Please provide rejection comments explaining the rationale.');
      return;
    }
    try {
      setActionError(null);
      await rejectStep({
        variables: {
          input: {
            stepId: currentStep.id,
            approverId: currentUser.id,
            comments: comment,
          },
        },
      });
      setComment('');
      onClose();
    } catch (err: any) {
      setActionError(err.message || 'Failed to reject request');
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(5, 8, 16, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel animate-fade-in"
        style={{
          width: '100%',
          maxWidth: '960px',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '32px',
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-active)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span className={`badge badge-${request.status.toLowerCase().replace('_', '-')}`}>
                {request.status.replace('_', ' ')}
              </span>
              <AIComplianceBadge status={request.policyEvaluation?.status} score={request.policyEvaluation?.score} showScore />
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>{request.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '8px', borderRadius: '50%' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Spend Metadata Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '16px',
            padding: '16px 20px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-input)',
            border: '1px solid var(--border-subtle)',
            marginBottom: '24px',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Amount
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34d399' }}>
              ${request.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })} {request.currency}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Vendor
            </div>
            <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {request.vendorName}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Requester
            </div>
            <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {request.requester?.name || 'Unknown'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {request.department}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Category
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#93c5fd' }}>
              {request.category.replace('_', ' ')}
            </div>
          </div>
        </div>

        {/* Description */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
            Business Justification
          </h4>
          <p style={{ fontSize: '0.9375rem', color: 'var(--text-primary)', lineHeight: 1.6, background: 'rgba(0,0,0,0.2)', padding: '12px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            {request.description}
          </p>
        </div>

        {/* AI Policy Assessment & Grounded Citations */}
        {request.policyEvaluation && (
          <div
            style={{
              marginBottom: '28px',
              padding: '20px',
              borderRadius: 'var(--radius-md)',
              background:
                request.policyEvaluation.status === 'LIKELY_COMPLIANT'
                  ? 'rgba(16, 185, 129, 0.05)'
                  : request.policyEvaluation.status === 'NEEDS_REVIEW'
                  ? 'rgba(245, 158, 11, 0.05)'
                  : 'rgba(239, 68, 68, 0.05)',
              border:
                request.policyEvaluation.status === 'LIKELY_COMPLIANT'
                  ? '1px solid var(--success-border)'
                  : request.policyEvaluation.status === 'NEEDS_REVIEW'
                  ? '1px solid var(--warning-border)'
                  : '1px solid var(--danger-border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={18} color="#60a5fa" />
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 700 }}>AI Policy Grounding Assessment</h4>
              </div>
              <AIComplianceBadge status={request.policyEvaluation.status} score={request.policyEvaluation.score} showScore />
            </div>

            <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginBottom: '14px', lineHeight: 1.5 }}>
              {request.policyEvaluation.reason}
            </p>

            {request.policyEvaluation.citations && request.policyEvaluation.citations.length > 0 && (
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Policy Citations & Grounding Snippets:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {request.policyEvaluation.citations.map((cite, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '10px 14px',
                        background: 'rgba(0,0,0,0.3)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#93c5fd', fontFamily: 'var(--font-mono)' }}>
                          {cite.section} &middot; Line {cite.lineNumber}
                        </span>
                        {onViewPolicyCitation && (
                          <button
                            type="button"
                            onClick={() => onViewPolicyCitation(cite.section, cite.lineNumber)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: '#60a5fa',
                              fontSize: '0.6875rem',
                              cursor: 'pointer',
                              textDecoration: 'underline',
                            }}
                          >
                            View in Policy Doc &rarr;
                          </button>
                        )}
                      </div>
                      <div style={{ fontSize: '0.8125rem', color: '#e5e7eb', fontStyle: 'italic' }}>
                        "{cite.snippet}"
                      </div>
                      {cite.relevance && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                          Reason: {cite.relevance}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Approval Chain Timeline */}
        <div style={{ marginBottom: '28px' }}>
          <h4 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '12px' }}>
            Approval Chain Timeline
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {request.approvalChain?.steps.map((step) => {
              const isCurrent = step.stepOrder === request.approvalChain?.currentStepOrder && step.status === 'PENDING';
              return (
                <div
                  key={step.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    background: isCurrent ? 'rgba(59, 130, 246, 0.08)' : 'var(--bg-input)',
                    border: isCurrent ? '1px solid var(--border-active)' : '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.8125rem',
                        fontWeight: 700,
                        background:
                          step.status === 'APPROVED'
                            ? 'var(--success)'
                            : step.status === 'REJECTED'
                            ? 'var(--danger)'
                            : isCurrent
                            ? 'var(--primary)'
                            : 'rgba(255,255,255,0.1)',
                        color: '#ffffff',
                      }}
                    >
                      {step.status === 'APPROVED' ? '✓' : step.status === 'REJECTED' ? '✕' : step.stepOrder}
                    </div>
                    <div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 700 }}>{step.stepName}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Role: <strong>{step.approverRole}</strong>
                        {step.approver && ` &middot; Assigned to: ${step.approver.name}`}
                        {step.comments && ` &middot; "${step.comments}"`}
                      </div>
                    </div>
                  </div>

                  <span className={`badge badge-${step.status.toLowerCase()}`}>
                    {step.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Approver Action Panel */}
        {canUserApprove && (
          <div
            style={{
              padding: '20px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid var(--border-active)',
            }}
          >
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: '8px', color: '#93c5fd' }}>
              Action Required ({currentStep?.stepName})
            </h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              You are signed in as <strong>{currentUser.name}</strong> ({currentUser.role}). You have authority to approve or reject this step.
            </p>

            <div className="input-group">
              <input
                type="text"
                className="input-field"
                placeholder="Add optional approval note or required rejection rationale..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
            </div>

            {actionError && (
              <div style={{ color: 'var(--danger)', fontSize: '0.8125rem', marginBottom: '12px' }}>
                {actionError}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                type="button"
                onClick={handleApprove}
                disabled={approving || rejecting}
                className="btn btn-success"
                style={{ flex: 1, padding: '10px 16px' }}
              >
                <CheckCircle2 size={16} />
                <span>{approving ? 'Approving...' : 'Approve Step'}</span>
              </button>
              <button
                type="button"
                onClick={handleReject}
                disabled={approving || rejecting}
                className="btn btn-danger"
                style={{ padding: '10px 16px' }}
              >
                <XCircle size={16} />
                <span>{rejecting ? 'Rejecting...' : 'Reject Request'}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
