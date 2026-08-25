import { gql } from '@apollo/client';

export const CREATE_SPEND_REQUEST = gql`
  mutation CreateSpendRequest($input: CreateSpendRequestInput!) {
    createSpendRequest(input: $input) {
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
        role
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
        }
      }
    }
  }
`;

export const APPROVE_STEP = gql`
  mutation ApproveStep($input: ApproveStepInput!) {
    approveStep(input: $input) {
      id
      status
      comments
      decisionAt
    }
  }
`;

export const REJECT_STEP = gql`
  mutation RejectStep($input: RejectStepInput!) {
    rejectStep(input: $input) {
      id
      status
      comments
      decisionAt
    }
  }
`;
