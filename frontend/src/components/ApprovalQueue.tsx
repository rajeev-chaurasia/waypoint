import React, { useState, useMemo } from 'react';
import { useQuery } from '@apollo/client';
import { Search, ArrowUpRight } from 'lucide-react';
import { GET_SPEND_REQUESTS } from '../graphql/queries';
import { SpendRequest, User } from '../types';
import { AIComplianceBadge } from './AIComplianceBadge';

interface Props {
  currentUser: User;
  onSelectRequest: (request: SpendRequest) => void;
  selectedRequestId?: string | null;
}

export const ApprovalQueue: React.FC<Props> = ({
  currentUser,
  onSelectRequest,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatusTab, setSelectedStatusTab] = useState<'ALL' | 'ACTION_REQUIRED' | 'PENDING' | 'APPROVED' | 'REJECTED'>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  const { data, loading } = useQuery(GET_SPEND_REQUESTS, {
    pollInterval: 5000,
  });

  const requests: SpendRequest[] = data?.spendRequests || [];

  const filteredRequests = useMemo(() => {
    return requests.filter((req) => {
      // Search
      const matchesSearch =
        req.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.vendorName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.requester?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.id.toLowerCase().includes(searchTerm.toLowerCase());

      if (!matchesSearch) return false;

      // Category filter
      if (selectedCategory !== 'ALL' && req.category !== selectedCategory) {
        return false;
      }

      // Status tab filter
      if (selectedStatusTab === 'PENDING') return req.status === 'PENDING_APPROVAL';
      if (selectedStatusTab === 'APPROVED') return req.status === 'APPROVED';
      if (selectedStatusTab === 'REJECTED') return req.status === 'REJECTED';
      if (selectedStatusTab === 'ACTION_REQUIRED') {
        if (req.status !== 'PENDING_APPROVAL') return false;
        const currentStep = req.approvalChain?.steps.find(
          (s) => s.stepOrder === req.approvalChain?.currentStepOrder && s.status === 'PENDING'
        );
        return (
          currentStep &&
          (currentUser.role === currentStep.approverRole ||
            currentUser.role === 'ADMIN' ||
            currentUser.id === currentStep.approverId)
        );
      }

      return true;
    });
  }, [requests, searchTerm, selectedStatusTab, selectedCategory, currentUser]);

  const actionRequiredCount = useMemo(() => {
    return requests.filter((req) => {
      if (req.status !== 'PENDING_APPROVAL') return false;
      const currentStep = req.approvalChain?.steps.find(
        (s) => s.stepOrder === req.approvalChain?.currentStepOrder && s.status === 'PENDING'
      );
      return (
        currentStep &&
        (currentUser.role === currentStep.approverRole ||
          currentUser.role === 'ADMIN' ||
          currentUser.id === currentStep.approverId)
      );
    }).length;
  }, [requests, currentUser]);

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '28px' }}>
      {/* Top Header & Search Filters */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.375rem', fontWeight: 800 }}>Spend & Procurement Approval Queue</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
            Multi-tier spend requests routed with AI policy assessment and line citations.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ position: 'relative', minWidth: '260px' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search vendor, title, or requester..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field"
              style={{ paddingLeft: '36px', paddingRight: '12px' }}
            />
          </div>

          <select
            aria-label="Filter Category"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="select-field"
            style={{ width: 'auto', padding: '10px 14px' }}
          >
            <option value="ALL">All Categories</option>
            <option value="SOFTWARE_SAAS">Software (SaaS)</option>
            <option value="HARDWARE">IT Hardware</option>
            <option value="CONSULTING_CONTRACTOR">Consulting</option>
            <option value="TRAVEL_ENTERTAINMENT">Travel & Entertainment</option>
            <option value="OFFICE_SUPPLIES">Office Supplies</option>
            <option value="MARKETING_ADS">Marketing</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px', marginBottom: '20px' }}>
        <button
          onClick={() => setSelectedStatusTab('ALL')}
          className={`nav-tab ${selectedStatusTab === 'ALL' ? 'active' : ''}`}
        >
          All Requests ({requests.length})
        </button>
        <button
          onClick={() => setSelectedStatusTab('ACTION_REQUIRED')}
          className={`nav-tab ${selectedStatusTab === 'ACTION_REQUIRED' ? 'active' : ''}`}
          style={{ position: 'relative' }}
        >
          <span>Needs My Action</span>
          {actionRequiredCount > 0 && (
            <span
              style={{
                marginLeft: '6px',
                padding: '2px 6px',
                borderRadius: '10px',
                background: '#ef4444',
                color: '#fff',
                fontSize: '0.6875rem',
                fontWeight: 800,
              }}
            >
              {actionRequiredCount}
            </span>
          )}
        </button>
        <button
          onClick={() => setSelectedStatusTab('PENDING')}
          className={`nav-tab ${selectedStatusTab === 'PENDING' ? 'active' : ''}`}
        >
          Pending ({requests.filter((r) => r.status === 'PENDING_APPROVAL').length})
        </button>
        <button
          onClick={() => setSelectedStatusTab('APPROVED')}
          className={`nav-tab ${selectedStatusTab === 'APPROVED' ? 'active' : ''}`}
        >
          Approved ({requests.filter((r) => r.status === 'APPROVED').length})
        </button>
        <button
          onClick={() => setSelectedStatusTab('REJECTED')}
          className={`nav-tab ${selectedStatusTab === 'REJECTED' ? 'active' : ''}`}
        >
          Rejected ({requests.filter((r) => r.status === 'REJECTED').length})
        </button>
      </div>

      {/* Request Cards */}
      {loading && requests.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
          Loading spend requests from GraphQL API...
        </div>
      ) : filteredRequests.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
          No spend requests match the selected filters.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filteredRequests.map((req) => {
            const currentStep = req.approvalChain?.steps.find(
              (s) => s.stepOrder === req.approvalChain?.currentStepOrder && s.status === 'PENDING'
            );
            const isAssignedToMe =
              req.status === 'PENDING_APPROVAL' &&
              currentStep &&
              (currentUser.role === currentStep.approverRole ||
                currentUser.role === 'ADMIN' ||
                currentUser.id === currentStep.approverId);

            return (
              <div
                key={req.id}
                onClick={() => onSelectRequest(req)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 20px',
                  borderRadius: 'var(--radius-md)',
                  background: isAssignedToMe ? 'rgba(59, 130, 246, 0.08)' : 'var(--bg-input)',
                  border: isAssignedToMe ? '1px solid var(--border-active)' : '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = isAssignedToMe ? 'rgba(59, 130, 246, 0.08)' : 'var(--bg-input)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                {/* Left info */}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', flex: 1 }}>
                  <div style={{ marginTop: '4px' }}>
                    <span className={`badge badge-${req.status.toLowerCase().replace('_', '-')}`}>
                      {req.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {req.title}
                      </span>
                      <AIComplianceBadge status={req.policyEvaluation?.status} score={req.policyEvaluation?.score} />
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                      <span><strong>Vendor:</strong> {req.vendorName}</span>
                      <span>&middot;</span>
                      <span><strong>Requester:</strong> {req.requester?.name} ({req.department})</span>
                      <span>&middot;</span>
                      <span><strong>Category:</strong> {req.category.replace('_', ' ')}</span>
                      {currentStep && req.status === 'PENDING_APPROVAL' && (
                        <>
                          <span>&middot;</span>
                          <span style={{ color: '#93c5fd', fontWeight: 600 }}>
                            Waiting on: {currentStep.stepName} ({currentStep.approverRole})
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right info: Amount and CTA */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginLeft: '24px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.125rem', fontWeight: 800, color: '#34d399' }}>
                      ${req.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                      {req.currency}
                    </div>
                  </div>

                  <button
                    type="button"
                    className={`btn ${isAssignedToMe ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ padding: '6px 12px', fontSize: '0.8125rem' }}
                  >
                    <span>{isAssignedToMe ? 'Review & Action' : 'View'}</span>
                    <ArrowUpRight size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
