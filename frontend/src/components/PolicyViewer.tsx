import React, { useState } from 'react';
import { useQuery } from '@apollo/client';
import { BookOpen, Search } from 'lucide-react';
import { GET_POLICIES } from '../graphql/queries';
import { Policy } from '../types';

interface Props {
  highlightSection?: string | null;
  highlightLine?: number | null;
}

export const PolicyViewer: React.FC<Props> = ({ highlightSection, highlightLine }) => {
  const { data, loading } = useQuery(GET_POLICIES);
  const [searchTerm, setSearchTerm] = useState('');

  const policy: Policy | undefined = data?.policies?.[0];

  const sections = [
    { id: 'SEC-1', title: '1. Scope and Objective' },
    { id: 'SEC-2', title: '2. Software, Cloud, and AI Services' },
    { id: 'SEC-3', title: '3. IT Hardware and Physical Equipment' },
    { id: 'SEC-4', title: '4. Travel, Meals, and Entertainment' },
    { id: 'SEC-5', title: '5. Professional Services, Legal, and Contractors' },
    { id: 'SEC-6', title: '6. Restricted Vendors and Compliance Screening' },
    { id: 'SEC-7', title: '7. Gifts, Hospitality, and Prohibited Items' },
  ];

  if (loading || !policy) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading active procurement policy from GraphQL API...
      </div>
    );
  }

  const lines = policy.content.split('\n');

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <BookOpen size={20} color="#60a5fa" />
            <h2 style={{ fontSize: '1.375rem', fontWeight: 800 }}>{policy.title}</h2>
            <span className="badge badge-compliant">Version {policy.version}</span>
            <span className="badge badge-approved">Active Policy Document</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
            The canonical source document referenced by the AI Policy Agent for grounded citations and threshold compliance.
          </p>
        </div>

        <div style={{ position: 'relative', width: '280px' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search policy rules..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field"
            style={{ paddingLeft: '36px' }}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '28px' }}>
        {/* Quick Nav TOC */}
        <div style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', height: 'fit-content' }}>
          <h4 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>
            Table of Contents
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {sections.map((sec) => (
              <a
                key={sec.id}
                href={`#${sec.id}`}
                style={{
                  fontSize: '0.8125rem',
                  padding: '6px 10px',
                  borderRadius: 'var(--radius-sm)',
                  color: highlightSection === sec.id ? '#60a5fa' : 'var(--text-secondary)',
                  background: highlightSection === sec.id ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  textDecoration: 'none',
                  fontWeight: highlightSection === sec.id ? 700 : 500,
                  transition: 'all 0.15s ease',
                }}
              >
                {sec.title}
              </a>
            ))}
          </div>
        </div>

        {/* Policy Document Body with line numbers and citation anchors */}
        <div
          style={{
            background: 'var(--bg-input)',
            padding: '24px 28px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            fontFamily: 'var(--font-sans)',
            fontSize: '0.875rem',
            lineHeight: 1.7,
          }}
        >
          {lines.map((line, idx) => {
            const isHeading = line.startsWith('## ');
            const isLineRule = line.startsWith('Line ');
            const lineNumMatch = line.match(/^Line (\d+):/);
            const lineNum = lineNumMatch ? parseInt(lineNumMatch[1], 10) : null;
            const isHighlighted = highlightLine && lineNum === highlightLine;

            // Search filter highlight
            const matchesSearch = searchTerm && line.toLowerCase().includes(searchTerm.toLowerCase());

            if (isHeading) {
              const secCode = line.includes('(SEC-') ? line.substring(line.indexOf('(SEC-') + 1, line.indexOf(')')) : '';
              return (
                <div
                  key={idx}
                  id={secCode}
                  style={{
                    fontSize: '1.0625rem',
                    fontWeight: 700,
                    color: '#93c5fd',
                    marginTop: idx === 0 ? 0 : '24px',
                    marginBottom: '10px',
                    borderBottom: '1px solid var(--border-subtle)',
                    paddingBottom: '6px',
                  }}
                >
                  {line.replace('## ', '')}
                </div>
              );
            }

            if (isLineRule) {
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '4px 8px',
                    borderRadius: 'var(--radius-sm)',
                    background: isHighlighted
                      ? 'rgba(59, 130, 246, 0.25)'
                      : matchesSearch
                      ? 'rgba(245, 158, 11, 0.2)'
                      : 'transparent',
                    border: isHighlighted
                      ? '1px solid var(--border-focus)'
                      : matchesSearch
                      ? '1px solid var(--warning-border)'
                      : '1px solid transparent',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      color: isHighlighted ? '#60a5fa' : 'var(--text-muted)',
                      minWidth: '54px',
                      userSelect: 'none',
                      fontWeight: 600,
                    }}
                  >
                    Line {lineNum}:
                  </span>
                  <span style={{ color: isHighlighted ? '#ffffff' : 'var(--text-primary)', flex: 1 }}>
                    {line.replace(/^Line \d+:\s+/, '')}
                  </span>
                </div>
              );
            }

            return (
              <div key={idx} style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', margin: '4px 0' }}>
                {line}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
