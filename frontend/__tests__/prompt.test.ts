import { SYSTEM_PROMPT } from '../prompt';

describe('SYSTEM_PROMPT', () => {
  test('is a non-empty string', () => {
    expect(typeof SYSTEM_PROMPT).toBe('string');
    expect(SYSTEM_PROMPT.length).toBeGreaterThan(0);
  });

  test('contains success schema fields', () => {
    expect(SYSTEM_PROMPT).toContain('overall_fairness');
    expect(SYSTEM_PROMPT).toContain('call_to_action');
    expect(SYSTEM_PROMPT).toContain('clauses');
    expect(SYSTEM_PROMPT).toContain('section_number');
    expect(SYSTEM_PROMPT).toContain('clause_type');
    expect(SYSTEM_PROMPT).toContain('market_standard');
  });

  test('contains error schema fields', () => {
    expect(SYSTEM_PROMPT).toContain('"error": true');
    expect(SYSTEM_PROMPT).toContain('reason');
  });

  test('defines all three fairness tiers', () => {
    expect(SYSTEM_PROMPT).toMatch(/\bfair\b/);
    expect(SYSTEM_PROMPT).toMatch(/\bunfair\b/);
    expect(SYSTEM_PROMPT).toMatch(/\begregious\b/);
  });

  test('includes worst-clause-wins rule', () => {
    expect(SYSTEM_PROMPT).toMatch(/worst/i);
  });

  test('instructs to bias toward accepting borderline input', () => {
    expect(SYSTEM_PROMPT).toMatch(/when in doubt|if unsure|bias.+accept/i);
  });

  test('requires customer-perspective plain English for purpose', () => {
    expect(SYSTEM_PROMPT).toMatch(/customer/i);
    expect(SYSTEM_PROMPT).toMatch(/plain english|plain-english|customer.+perspective/i);
  });

  test('requires JSON-only output', () => {
    expect(SYSTEM_PROMPT).toMatch(/valid json|only.*json|no text outside/i);
  });
});
