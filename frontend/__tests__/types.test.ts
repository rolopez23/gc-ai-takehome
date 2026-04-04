import { isEvalSuccess, isEvalError } from '@/app/evaluate-contract/types';

describe('isEvalSuccess', () => {
  test('returns true for valid success response', () => {
    const res = {
      error: null,
      overall_fairness: 'fair',
      summary: 'All clauses are market standard.',
      call_to_action: [],
      clauses: [],
    };
    expect(isEvalSuccess(res)).toBe(true);
  });

  test('returns false for error response', () => {
    const res = { error: true, reason: 'not a contract' };
    expect(isEvalSuccess(res)).toBe(false);
  });

  test('returns false for null', () => {
    expect(isEvalSuccess(null)).toBe(false);
  });

  test('returns false for non-object', () => {
    expect(isEvalSuccess('string')).toBe(false);
  });
});

describe('isEvalError', () => {
  test('returns true for error response', () => {
    const res = { error: true, reason: 'This does not appear to be a contract.' };
    expect(isEvalError(res)).toBe(true);
  });

  test('returns false for success response', () => {
    const res = {
      error: null,
      overall_fairness: 'fair',
      summary: '',
      call_to_action: [],
      clauses: [],
    };
    expect(isEvalError(res)).toBe(false);
  });

  test('returns false for null', () => {
    expect(isEvalError(null)).toBe(false);
  });
});
