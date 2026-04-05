import { describe, test, expect } from 'vitest';
import {
  UploadResponseSchema,
  ReviewPollingSchema,
  ReviewCompletedSchema,
  ReviewFailedSchema,
  ReviewResponseSchema,
} from '@/app/evaluate-contract/types';

const uuid = '550e8400-e29b-41d4-a716-446655440000';
const uuid2 = '660e8400-e29b-41d4-a716-446655440001';
const clauseId = '770e8400-e29b-41d4-a716-446655440002';

describe('UploadResponseSchema', () => {
  test('test_upload_response_parses', () => {
    const data = { contract_id: uuid, review_id: uuid2, status: 'pending' };
    expect(UploadResponseSchema.safeParse(data).success).toBe(true);
  });
});

describe('ReviewPollingSchema', () => {
  test('test_review_polling_parses', () => {
    const data = { id: uuid, contract_id: uuid2, status: 'evaluating' };
    expect(ReviewPollingSchema.safeParse(data).success).toBe(true);
  });
});

describe('ReviewCompletedSchema', () => {
  test('test_review_completed_with_fairness', () => {
    const data = {
      id: uuid,
      contract_id: uuid2,
      status: 'completed',
      overall_fairness: 'fair',
      summary: 'All clauses are market standard.',
      call_to_action: ['Review section 3'],
      clauses: [
        {
          id: clauseId,
          section_number: '1.1',
          clause_type: 'Termination',
          purpose: 'Defines termination conditions',
          fairness: 'fair',
          market_standard: 'Standard termination clause',
          explanation: 'This clause is standard.',
        },
      ],
      completed_at: '2026-04-05T12:00:00Z',
    };
    expect(ReviewCompletedSchema.safeParse(data).success).toBe(true);
  });

  test('test_review_completed_null_fairness', () => {
    const data = {
      id: uuid,
      contract_id: uuid2,
      status: 'completed',
      overall_fairness: null,
      summary: null,
      call_to_action: null,
      clauses: [],
      completed_at: '2026-04-05T12:00:00Z',
    };
    expect(ReviewCompletedSchema.safeParse(data).success).toBe(true);
  });
});

describe('ReviewFailedSchema', () => {
  test('test_review_failed_parses', () => {
    const data = { id: uuid, status: 'failed', failure_message: 'Unable to process document' };
    expect(ReviewFailedSchema.safeParse(data).success).toBe(true);
  });
});

describe('ReviewResponseSchema', () => {
  test('test_discriminated_union_completed', () => {
    const data = {
      id: uuid,
      contract_id: uuid2,
      status: 'completed',
      overall_fairness: 'non-standard',
      summary: 'Issues found.',
      call_to_action: ['Review section 3'],
      clauses: [],
      completed_at: '2026-04-05T12:00:00Z',
    };
    const result = ReviewResponseSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.status).toBe('completed');
    }
  });

  test('test_discriminated_union_failed', () => {
    const data = { id: uuid, status: 'failed', failure_message: 'Error occurred' };
    const result = ReviewResponseSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.status).toBe('failed');
    }
  });
});
