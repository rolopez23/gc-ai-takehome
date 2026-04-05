import {
  EvalSuccessSchema,
  EvalErrorSchema,
  EvalResponseSchema,
} from '@/app/evaluate-contract/types';

describe('EvalSuccessSchema', () => {
  test('parses valid success response', () => {
    const res = {
      error: null,
      overall_fairness: 'fair',
      summary: 'All clauses are market standard.',
      call_to_action: [],
      clauses: [],
    };
    expect(EvalSuccessSchema.safeParse(res).success).toBe(true);
  });

  test('rejects error response', () => {
    const res = { error: true, reason: 'not a contract' };
    expect(EvalSuccessSchema.safeParse(res).success).toBe(false);
  });

  test('rejects null', () => {
    expect(EvalSuccessSchema.safeParse(null).success).toBe(false);
  });

  test('rejects non-object', () => {
    expect(EvalSuccessSchema.safeParse('string').success).toBe(false);
  });

  test('rejects invalid fairness value', () => {
    const res = {
      error: null,
      overall_fairness: 'neutral',
      summary: '',
      call_to_action: [],
      clauses: [],
    };
    expect(EvalSuccessSchema.safeParse(res).success).toBe(false);
  });

  test('rejects non-array clauses', () => {
    const res = {
      error: null,
      overall_fairness: 'fair',
      summary: '',
      call_to_action: [],
      clauses: 'oops',
    };
    expect(EvalSuccessSchema.safeParse(res).success).toBe(false);
  });
});

describe('EvalErrorSchema', () => {
  test('parses valid error response', () => {
    const res = { error: true, reason: 'This does not appear to be a contract.' };
    expect(EvalErrorSchema.safeParse(res).success).toBe(true);
  });

  test('rejects success response', () => {
    const res = {
      error: null,
      overall_fairness: 'fair',
      summary: '',
      call_to_action: [],
      clauses: [],
    };
    expect(EvalErrorSchema.safeParse(res).success).toBe(false);
  });

  test('rejects null', () => {
    expect(EvalErrorSchema.safeParse(null).success).toBe(false);
  });
});

describe('EvalResponseSchema', () => {
  test('discriminates success by error: null', () => {
    const res = {
      error: null,
      overall_fairness: 'non-standard',
      summary: 'Issues found.',
      call_to_action: ['Review §3'],
      clauses: [],
    };
    const result = EvalResponseSchema.safeParse(res);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.error).toBeNull();
    }
  });

  test('discriminates error by error: true', () => {
    const res = { error: true, reason: 'Not a contract' };
    const result = EvalResponseSchema.safeParse(res);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.error).toBe(true);
    }
  });

  test('rejects unknown error value', () => {
    const res = { error: false, reason: 'weird' };
    expect(EvalResponseSchema.safeParse(res).success).toBe(false);
  });
});
