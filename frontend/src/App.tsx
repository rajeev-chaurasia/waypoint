import React, { useState } from 'react';
import { useQuery } from '@apollo/client';
import { GET_SPEND_REQUEST, GET_USERS } from './graphql/queries';
import { Navbar } from './components/Navbar';
import { ApprovalQueue } from './components/ApprovalQueue';
import { SpendRequestForm } from './components/SpendRequestForm';
import { RequestDetail } from './components/RequestDetail';
import { PolicyViewer } from './components/PolicyViewer';
import { MetricsOverview } from './components/MetricsOverview';
import { SpendRequest, User } from './types';

const DEFAULT_USERS: User[] = [
  {
    id: 'user_sarah_emp',
    email: 'sarah.chen@acme.corp',
    name: 'Sarah Chen',
    role: 'EMPLOYEE',
    department: 'ENGINEERING',
    spendLimit: 1000,
  },
  {
    id: 'user_marcus_mgr',
    email: 'marcus.vance@acme.corp',
    name: 'Marcus Vance',
    role: 'MANAGER',
    department: 'ENGINEERING',
    spendLimit: 10000,
  },
  {
    id: 'user_elena_sec',
    email: 'elena.rostova@acme.corp',
    name: 'Elena Rostova',
    role: 'SECURITY',
    department: 'ENGINEERING',
    spendLimit: 25000,
  },
  {
    id: 'user_david_fin',
    email: 'david.miller@acme.corp',
    name: 'David Miller',
    role: 'FINANCE',
    department: 'LEGAL_FINANCE',
    spendLimit: 50000,
  },
  {
    id: 'user_victoria_leg',
    email: 'victoria.stone@acme.corp',
    name: 'Victoria Stone',
    role: 'LEGAL',
    department: 'LEGAL_FINANCE',
    spendLimit: 30000,
  },
  {
    id: 'user_rachel_exec',
    email: 'rachel.hayes@acme.corp',
    name: 'Rachel Hayes',
    role: 'EXEC',
    department: 'ENGINEERING',
    spendLimit: 100000,
  },
  {
    id: 'user_arthur_admin',
    email: 'arthur.pendleton@acme.corp',
    name: 'Arthur Pendleton',
    role: 'ADMIN',
    department: 'LEGAL_FINANCE',
    spendLimit: 500000,
  },
];

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'queue' | 'submit' | 'policy' | 'benchmarks'>('queue');
  const [currentUser, setCurrentUser] = useState<User>(DEFAULT_USERS[0]);
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [policyCitationFocus, setPolicyCitationFocus] = useState<{ section: string; line: number } | null>(null);

  const { data: usersData } = useQuery(GET_USERS);
  const allUsers: User[] = usersData?.users && usersData.users.length > 0 ? usersData.users : DEFAULT_USERS;

  const { data: requestDetailData } = useQuery(GET_SPEND_REQUEST, {
    variables: { id: selectedRequestId || '' },
    skip: !selectedRequestId,
  });

  const selectedRequest: SpendRequest | null = requestDetailData?.spendRequest || null;

  const handleViewPolicyCitation = (section: string, lineNumber: number) => {
    setSelectedRequestId(null);
    setPolicyCitationFocus({ section, line: lineNumber });
    setActiveTab('policy');
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        allUsers={allUsers}
        onSelectUser={(u) => setCurrentUser(u)}
      />

      <main>
        {activeTab === 'queue' && (
          <ApprovalQueue
            currentUser={currentUser}
            onSelectRequest={(req) => setSelectedRequestId(req.id)}
            selectedRequestId={selectedRequestId}
          />
        )}

        {activeTab === 'submit' && (
          <SpendRequestForm
            currentUser={currentUser}
            onSuccess={(newId) => {
              setSelectedRequestId(newId);
              setActiveTab('queue');
            }}
          />
        )}

        {activeTab === 'policy' && (
          <PolicyViewer
            highlightSection={policyCitationFocus?.section}
            highlightLine={policyCitationFocus?.line}
          />
        )}

        {activeTab === 'benchmarks' && <MetricsOverview />}
      </main>

      {/* Modal Detail View */}
      {selectedRequest && (
        <RequestDetail
          request={selectedRequest}
          currentUser={currentUser}
          onClose={() => setSelectedRequestId(null)}
          onViewPolicyCitation={handleViewPolicyCitation}
        />
      )}
    </div>
  );
};
