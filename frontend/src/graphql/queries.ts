import { gql } from '@apollo/client';

export const GET_SPEND_REQUESTS = gql`
  query GetSpendRequests($category: SpendCategory, $status: RequestStatus, $department: Department) {
    spendRequests(category: $category, status: $status, department: $department) {
      id
      title
      description
      amount
      currency
      category
      vendorName
      department
      status
      createdAt
      requester {
        id
        name
        email
        role
        department
      }
      policyEvaluation {
        id
        status
        score
        reason
        citations {
          section
          lineNumber
          snippet
          relevance
        }
      }
      approvalChain {
        id
        status
        currentStepOrder
        steps {
          id
          stepOrder
          stepName
          approverRole
          status
          comments
          decisionAt
          approver {
            id
            name
          }
        }
      }
    }
  }
`;

export const GET_SPEND_REQUEST = gql`
  query GetSpendRequest($id: String!) {
    spendRequest(id: $id) {
      id
      title
      description
      amount
      currency
      category
      vendorName
      department
      status
      createdAt
      requester {
        id
        name
        email
        role
        department
      }
      policyEvaluation {
        id
        status
        score
        reason
        citations {
          section
          lineNumber
          snippet
          relevance
        }
      }
      approvalChain {
        id
        status
        currentStepOrder
        steps {
          id
          stepOrder
          stepName
          approverRole
          status
          comments
          decisionAt
          approver {
            id
            name
          }
        }
      }
    }
  }
`;

export const GET_POLICIES = gql`
  query GetPolicies {
    policies(activeOnly: true) {
      id
      title
      version
      isActive
      content
    }
  }
`;

export const GET_USERS = gql`
  query GetUsers {
    users {
      id
      name
      email
      role
      department
      spendLimit
    }
  }
`;

export const GET_SYSTEM_METRICS = gql`
  query GetSystemMetrics {
    systemMetrics {
      totalRequests
      totalSpendAmount
      pendingApprovals
      approvedCount
      rejectedCount
      policyCompliantCount
      policyFlaggedCount
      dataloaderEfficiencyRatio
    }
  }
`;
