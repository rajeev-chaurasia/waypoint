import React, { useState, useMemo } from 'react';
import { useMutation } from '@apollo/client';
import {
  Send,
  Sparkles,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';
import { CREATE_SPEND_REQUEST } from '../graphql/mutations';
import { GET_SPEND_REQUESTS, GET_SYSTEM_METRICS } from '../graphql/queries';
import { Department, SpendCategory, User } from '../types';

interface Props {
  currentUser: User;
  onSuccess: (requestId: string) => void;
}

export const SpendRequestForm: React.FC<Props> = ({ currentUser, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState<number | ''>(4200);
  const [currency] = useState('USD');
  const [category, setCategory] = useState<SpendCategory>('SOFTWARE_SAAS');
  const [vendorName, setVendorName] = useState('Datadog Inc.');
  const [department, setDepartment] = useState<Department>(currentUser.department || 'ENGINEERING');
  const [description, setDescription] = useState(
    'Annual cloud monitoring and distributed tracing licenses for engineering production infrastructure.'
  );

  const [createRequest, { loading, error }] = useMutation(CREATE_SPEND_REQUEST, {
    refetchQueries: [{ query: GET_SPEND_REQUESTS }, { query: GET_SYSTEM_METRICS }],
  });

  // Dynamic live approval route preview
  const estimatedRoute = useMemo(() => {
    const numAmount = typeof amount === 'number' ? amount : 0;
    if (numAmount <= 0) return [];

    const steps = [
      { order: 1, name: 'Direct Manager Approval', role: 'MANAGER', reason: 'Line manager verification' },
    ];

    if (category === 'SOFTWARE_SAAS' && numAmount > 1000) {
      steps.push({ order: 2, name: 'Security & IT Architecture Review', role: 'SECURITY', reason: 'SaaS data privacy & SOC2 check' });
    } else if (category === 'HARDWARE' && numAmount > 500) {
      steps.push({ order: 2, name: 'IT Hardware Procurement Review', role: 'SECURITY', reason: 'Device compatibility check' });
    } else if (category === 'CONSULTING_CONTRACTOR' && numAmount > 5000) {
      steps.push({ order: 2, name: 'Legal & Contractor Governance Review', role: 'LEGAL', reason: 'SOW / MSA contract audit' });
    }

    if (numAmount >= 500) {
      steps.push({ order: steps.length + 1, name: 'Finance & Controller Review', role: 'FINANCE', reason: 'General ledger & budget disbursement' });
    }

    if (numAmount >= 10000) {
      steps.push({ order: steps.length + 1, name: 'Executive VP Sign-Off', role: 'EXEC', reason: 'High-value executive sign-off' });
    }

    if (numAmount >= 50000) {
      steps.push({ order: steps.length + 1, name: 'Board & CEO Authorization', role: 'ADMIN', reason: 'Material company commitment' });
    }

    return steps;
  }, [amount, category]);

  const loadPreset = (type: string) => {
    switch (type) {
      case 'saas-compliant':
        setTitle('Figma Team Design Subscription');
        setAmount(360.0);
        setCategory('SOFTWARE_SAAS');
        setVendorName('Figma Inc.');
        setDescription('Annual design seats for UX and interface prototyping.');
        break;
      case 'saas-security':
        setTitle('Custom Generative AI Agent with Customer Data');
        setAmount(3200.0);
        setCategory('SOFTWARE_SAAS');
        setVendorName('OpenAI API Platform');
        setDescription('Integrating LLM API to process production customer data and proprietary source code.');
        break;
      case 'consulting-legal':
        setTitle('Brand Strategy Consulting Engagement');
        setAmount(18000.0);
        setCategory('CONSULTING_CONTRACTOR');
        setVendorName('Pentagram Design Advisory');
        setDescription('10-week corporate brand refresh. SOW executed and attached for legal sign-off.');
        break;
      case 'hardware-laptop':
        setTitle('MacBook Pro M3 Max for Senior Engineer');
        setAmount(3499.0);
        setCategory('HARDWARE');
        setVendorName('Apple Inc.');
        setDescription('Hardware workstation refresh for senior backend engineer.');
        break;
      case 'personal-violation':
        setTitle('Equinox Monthly Gym Membership');
        setAmount(280.0);
        setCategory('OTHER');
        setVendorName('Equinox Fitness');
        setDescription('Monthly personal fitness membership for home office wellness.');
        break;
      case 'vague-spend':
        setTitle('Miscellaneous Items for Project');
        setAmount(350.0);
        setCategory('OFFICE_SUPPLIES');
        setVendorName('Various');
        setDescription('Stuff needed for demo next week.');
        break;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || amount <= 0) return;

    try {
      const { data } = await createRequest({
        variables: {
          input: {
            title,
            description,
            amount: Number(amount),
            currency,
            category,
            vendorName,
            department,
            requesterId: currentUser.id,
          },
        },
      });

      if (data?.createSpendRequest?.id) {
        onSuccess(data.createSpendRequest.id);
      }
    } catch (err) {
      console.error('Error submitting spend request:', err);
    }
  };

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '6px' }}>Submit Spend & Procurement Request</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Requests are automatically audited against company procurement policy and routed through deterministic approval tiers.
          </p>
        </div>

        {/* Quick Test Preset Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Quick Test Scenarios
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={() => loadPreset('saas-compliant')} className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
              Standard SaaS ($360)
            </button>
            <button type="button" onClick={() => loadPreset('saas-security')} className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', borderColor: 'var(--warning-border)', color: '#fbbf24' }}>
              AI Tool ($3.2k)
            </button>
            <button type="button" onClick={() => loadPreset('consulting-legal')} className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
              Consulting ($18k)
            </button>
            <button type="button" onClick={() => loadPreset('personal-violation')} className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', borderColor: 'var(--danger-border)', color: '#f87171' }}>
              Gym Pass ($280)
            </button>
            <button type="button" onClick={() => loadPreset('vague-spend')} className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', borderColor: 'var(--purple-border)', color: '#c084fc' }}>
              Vague Spend ($350)
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '32px' }}>
        {/* Form Fields */}
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label className="input-label">Request Title</label>
            <input
              type="text"
              required
              className="input-field"
              placeholder="e.g. Datadog APM Enterprise Subscription"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="input-group">
              <label className="input-label">Spend Amount (USD)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                className="input-field"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value === '' ? '' : parseFloat(e.target.value))}
              />
            </div>

            <div className="input-group">
              <label className="input-label">Spend Category</label>
              <select
                aria-label="Spend Category"
                className="select-field"
                value={category}
                onChange={(e) => setCategory(e.target.value as SpendCategory)}
              >
                <option value="SOFTWARE_SAAS">Software & Cloud (SaaS)</option>
                <option value="HARDWARE">IT Hardware & Equipment</option>
                <option value="CONSULTING_CONTRACTOR">Consulting & Contractors</option>
                <option value="TRAVEL_ENTERTAINMENT">Travel & Entertainment</option>
                <option value="OFFICE_SUPPLIES">Office Supplies</option>
                <option value="MARKETING_ADS">Marketing & Advertising</option>
                <option value="OTHER">Other / General</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="input-group">
              <label className="input-label">Vendor Name</label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="e.g. Datadog Inc., Apple, Acme Corp"
                value={vendorName}
                onChange={(e) => setVendorName(e.target.value)}
              />
            </div>

            <div className="input-group">
              <label className="input-label">Department</label>
              <select
                aria-label="Department"
                className="select-field"
                value={department}
                onChange={(e) => setDepartment(e.target.value as Department)}
              >
                <option value="ENGINEERING">Engineering</option>
                <option value="PRODUCT">Product</option>
                <option value="SALES">Sales</option>
                <option value="MARKETING">Marketing</option>
                <option value="OPERATIONS">Operations</option>
                <option value="LEGAL_FINANCE">Legal & Finance</option>
                <option value="GENERAL_ADMIN">General Administration</option>
              </select>
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Business Justification & Details</label>
            <textarea
              required
              className="textarea-field"
              placeholder="Describe business purpose, items included, and usage..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--danger)', marginBottom: '16px', fontSize: '0.875rem' }}>
              <AlertCircle size={16} />
              <span>Error submitting request: {error.message}</span>
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
            <button
              type="submit"
              disabled={loading || !title || !amount}
              className="btn btn-primary"
              style={{ flex: 1, padding: '12px 20px', fontSize: '0.9375rem' }}
            >
              {loading ? (
                <span>Auditing & Submitting...</span>
              ) : (
                <>
                  <Send size={16} />
                  <span>Submit Spend Request</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Live Approval Route & Governance Preview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            style={{
              padding: '20px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(0, 0, 0, 0.25)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Sparkles size={18} color="#60a5fa" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Generated Approval Route</h3>
            </div>

            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Based on {category.replace('_', ' ')} (${Number(amount || 0).toLocaleString()} USD), this request requires {estimatedRoute.length} approval step{estimatedRoute.length === 1 ? '' : 's'}:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {estimatedRoute.map((step) => (
                <div
                  key={step.order}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      background: 'var(--primary)',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                    }}
                  >
                    {step.order}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {step.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {step.reason} &middot; <strong style={{ color: '#93c5fd' }}>{step.role}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div
            style={{
              padding: '16px 20px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(59, 130, 246, 0.05)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <ShieldCheck size={16} color="#60a5fa" />
              <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#93c5fd' }}>
                AI Policy Grounding Guarantee
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Upon submission, the agent parses the active Procurement Policy document and attaches line-level citations. If the submission lacks sufficient vendor details or itemized breakdown, it automatically flags <strong>INSUFFICIENT EVIDENCE</strong>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
