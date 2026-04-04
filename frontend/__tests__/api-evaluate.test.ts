import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { SYSTEM_PROMPT } from '../prompt';

const mockCreate = vi.fn();

vi.mock('@anthropic-ai/sdk', () => {
  return {
    default: class MockAnthropic {
      messages = { create: mockCreate };
    },
  };
});

function makeRequest(body: Record<string, unknown>): Request {
  return new Request('http://localhost:3000/api/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

const VALID_RESPONSE = {
  error: null,
  overall_fairness: 'fair',
  summary: 'All clauses are market standard.',
  call_to_action: [],
  clauses: [],
};

beforeEach(() => {
  mockCreate.mockReset();
  process.env.ANTHROPIC_API_KEY = 'test-key';
});

afterEach(() => {
  delete process.env.ANTHROPIC_MODEL;
});

describe('POST /api/evaluate', () => {
  describe('input validation', () => {
    test('returns 400 when text is missing', async () => {
      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({}));
      expect(res.status).toBe(400);
    });

    test('returns 400 when text is empty string', async () => {
      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: '' }));
      expect(res.status).toBe(400);
    });

    test('returns 400 when text is whitespace only', async () => {
      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: '   ' }));
      expect(res.status).toBe(400);
    });
  });

  describe('Anthropic call', () => {
    test('calls Anthropic and returns parsed response', async () => {
      mockCreate.mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify(VALID_RESPONSE) }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'sample contract text' }));
      const body = await res.json();

      expect(res.status).toBe(200);
      expect(body).toEqual(VALID_RESPONSE);
    });

    test('passes contract text as user message', async () => {
      mockCreate.mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify(VALID_RESPONSE) }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      await POST(makeRequest({ text: 'my contract text' }));

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          messages: [{ role: 'user', content: 'my contract text' }],
        }),
      );
    });

    test('uses SYSTEM_PROMPT from prompt module', async () => {
      mockCreate.mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify(VALID_RESPONSE) }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      await POST(makeRequest({ text: 'contract' }));

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          system: SYSTEM_PROMPT,
        }),
      );
    });
  });

  describe('error handling', () => {
    test('returns 500 when Anthropic SDK throws', async () => {
      mockCreate.mockRejectedValue(new Error('API error'));

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'contract' }));
      expect(res.status).toBe(500);

      const body = await res.json();
      expect(body).toHaveProperty('error');
    });

    test('returns 500 when response JSON is malformed', async () => {
      mockCreate.mockResolvedValue({
        content: [{ type: 'text', text: 'not json at all' }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'contract' }));
      expect(res.status).toBe(500);
    });
  });

  describe('model configuration', () => {
    test('uses ANTHROPIC_MODEL env var when set', async () => {
      process.env.ANTHROPIC_MODEL = 'claude-sonnet-4-5-20241022';
      mockCreate.mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify(VALID_RESPONSE) }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      await POST(makeRequest({ text: 'contract' }));

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ model: 'claude-sonnet-4-5-20241022' }),
      );
    });

    test('defaults to haiku when ANTHROPIC_MODEL is not set', async () => {
      delete process.env.ANTHROPIC_MODEL;
      mockCreate.mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify(VALID_RESPONSE) }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      await POST(makeRequest({ text: 'contract' }));

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ model: 'claude-haiku-4-5-20251001' }),
      );
    });
  });
});
