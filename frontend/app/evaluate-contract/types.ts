export interface EvalClause {
  section_number: string;
  clause_type: string;
  purpose: string;
  fairness: 'fair' | 'unfair' | 'egregious';
  market_standard: string;
  explanation: string;
}

export interface EvalSuccess {
  error: null;
  overall_fairness: 'fair' | 'unfair' | 'egregious';
  summary: string;
  call_to_action: string[];
  clauses: EvalClause[];
}

export interface EvalError {
  error: true;
  reason: string;
}

export type EvalResponse = EvalSuccess | EvalError;

export function isEvalSuccess(res: unknown): res is EvalSuccess {
  return (
    typeof res === 'object' &&
    res !== null &&
    'error' in res &&
    (res as EvalSuccess).error === null &&
    'overall_fairness' in res &&
    'clauses' in res
  );
}

export function isEvalError(res: unknown): res is EvalError {
  return (
    typeof res === 'object' &&
    res !== null &&
    'error' in res &&
    (res as EvalError).error === true &&
    'reason' in res
  );
}
