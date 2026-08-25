import React from 'react';
import {
  Compass,
  FileSpreadsheet,
  PlusCircle,
  BookOpen,
  Activity,
} from 'lucide-react';
import { User } from '../types';

interface Props {
  activeTab: 'queue' | 'submit' | 'policy' | 'benchmarks';
  setActiveTab: (tab: 'queue' | 'submit' | 'policy' | 'benchmarks') => void;
  currentUser: User;
  allUsers: User[];
  onSelectUser: (user: User) => void;
}

export const Navbar: React.FC<Props> = ({
  activeTab,
  setActiveTab,
  currentUser,
  allUsers,
  onSelectUser,
}) => {
  return (
    <header className="header-nav glass-panel">
      {/* Brand */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        onClick={() => setActiveTab('queue')}
      >
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(59, 130, 246, 0.4)',
          }}
        >
          <Compass size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.03em', color: '#f9fafb' }}>
              Waypoint
            </span>
            <span
              style={{
                fontSize: '0.6875rem',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: '4px',
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
                border: '1px solid rgba(59, 130, 246, 0.3)',
              }}
            >
              GRAPHQL &middot; AI AGENT
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: '#9ca3af', margin: 0 }}>
            Policy-Aware Spend & Procurement Approval Router
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === 'queue' ? 'active' : ''}`}
          onClick={() => setActiveTab('queue')}
        >
          <FileSpreadsheet size={16} />
          <span>Approval Queue</span>
        </button>
        <button
          className={`nav-tab ${activeTab === 'submit' ? 'active' : ''}`}
          onClick={() => setActiveTab('submit')}
        >
          <PlusCircle size={16} />
          <span>New Spend Request</span>
        </button>
        <button
          className={`nav-tab ${activeTab === 'policy' ? 'active' : ''}`}
          onClick={() => setActiveTab('policy')}
        >
          <BookOpen size={16} />
          <span>Procurement Policy</span>
        </button>
        <button
          className={`nav-tab ${activeTab === 'benchmarks' ? 'active' : ''}`}
          onClick={() => setActiveTab('benchmarks')}
        >
          <Activity size={16} />
          <span>Benchmarks & Stats</span>
        </button>
      </nav>

      {/* Role Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#f3f4f6' }}>
            {currentUser.name}
          </div>
          <div style={{ fontSize: '0.6875rem', color: '#60a5fa', fontWeight: 600 }}>
            ROLE: {currentUser.role} &middot; {currentUser.department}
          </div>
        </div>

        <select
          aria-label="Switch active persona"
          value={currentUser.id}
          onChange={(e) => {
            const found = allUsers.find((u) => u.id === e.target.value);
            if (found) onSelectUser(found);
          }}
          className="select-field"
          style={{ width: 'auto', padding: '6px 12px', fontSize: '0.8125rem', cursor: 'pointer' }}
        >
          {allUsers.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name} ({u.role})
            </option>
          ))}
        </select>
      </div>
    </header>
  );
};
