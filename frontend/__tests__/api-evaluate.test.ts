import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { SYSTEM_PROMPT } from '../prompt';

const mockCreate = vi.fn();

vi.mock('@anthropic-ai/sdk', () => {
  const APIError = class extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  };
  return {
    default: class MockAnthropic {
      static APIError = APIError;
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
    test('calls Anthropic and returns validated response', async () => {
      mockCreate.mockResolvedValue({
        stop_reason: 'end_turn',
        content: [{ type: 'text', text: JSON.stringify(VALID_RESPONSE) }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'sample contract text' }));
      const body = await res.json();

      expect(res.status).toBe(200);
      expect(body).toEqual(VALID_RESPONSE);
    });

    test('trims whitespace from input text', async () => {
      mockCreate.mockResolvedValue({
        stop_reason: 'end_turn',
        content: [{ type: 'text', text: JSON.stringify(VALID_RESPONSE) }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      await POST(makeRequest({ text: '  contract text  ' }));

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          messages: [{ role: 'user', content: 'contract text' }],
        }),
      );
    });

    test('uses SYSTEM_PROMPT from prompt module', async () => {
      mockCreate.mockResolvedValue({
        stop_reason: 'end_turn',
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

  describe('fence stripping', () => {
    test('strips markdown json fences from response', async () => {
      mockCreate.mockResolvedValue({
        stop_reason: 'end_turn',
        content: [{ type: 'text', text: '```json\n' + JSON.stringify(VALID_RESPONSE) + '\n```' }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'contract' }));
      const body = await res.json();

      expect(res.status).toBe(200);
      expect(body).toEqual(VALID_RESPONSE);
    });

    test('strips plain fences from response', async () => {
      mockCreate.mockResolvedValue({
        stop_reason: 'end_turn',
        content: [{ type: 'text', text: '```\n' + JSON.stringify(VALID_RESPONSE) + '\n```' }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'contract' }));

      expect(res.status).toBe(200);
    });
  });

  describe('truncation', () => {
    test('returns 422 when response is truncated', async () => {
      mockCreate.mockResolvedValue({
        stop_reason: 'max_tokens',
        content: [{ type: 'text', text: '{"error": null, "overall' }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'contract' }));
      const body = await res.json();

      expect(res.status).toBe(422);
      expect(body.error).toBe('contract too large to evaluate');
    });
  });

  describe('schema validation', () => {
    test('returns 500 when model returns invalid schema', async () => {
      mockCreate.mockResolvedValue({
        stop_reason: 'end_turn',
        content: [{ type: 'text', text: JSON.stringify({ error: 'some string', weird: true }) }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'contract' }));

      expect(res.status).toBe(500);
      const body = await res.json();
      expect(body.error).toBe('model returned invalid response');
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
        stop_reason: 'end_turn',
        content: [{ type: 'text', text: 'not json at all' }],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'contract' }));
      expect(res.status).toBe(500);
    });

    test('returns 500 when content array is empty', async () => {
      mockCreate.mockResolvedValue({
        stop_reason: 'end_turn',
        content: [],
      });

      const { POST } = await import('@/app/api/evaluate/route');
      const res = await POST(makeRequest({ text: 'contract' }));
      expect(res.status).toBe(500);
    });
  });
});
