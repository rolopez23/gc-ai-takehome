import Anthropic from '@anthropic-ai/sdk';
import { NextResponse } from 'next/server';
import { SYSTEM_PROMPT } from '../../../prompt';
import { EvalResponseSchema } from '../../evaluate-contract/types';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const model = process.env.ANTHROPIC_MODEL ?? 'claude-haiku-4-5-20251001';

const MAX_TOKENS = 8192;

const HTTP_BAD_REQUEST = 400;
const HTTP_UNPROCESSABLE = 422;
const HTTP_INTERNAL = 500;

function errorResponse(message: string, status: number) {
  return NextResponse.json({ error: message }, { status });
}

function stripFences(text: string) {
  return text.replace(/^```(?:json)?\s*\n?/, '').replace(/\n?```\s*$/, '');
}

function parseRequestBody(body: unknown): string | null {
  if (typeof body !== 'object' || body === null || Array.isArray(body)) return null;
  const { text } = body as Record<string, unknown>;
  if (!text || typeof text !== 'string' || text.trim() === '') return null;
  return text.trim();
}

function buildMessages(text: string): Anthropic.MessageCreateParams {
  return {
    model,
    max_tokens: MAX_TOKENS,
    system: SYSTEM_PROMPT,
    messages: [{ role: 'user', content: text }],
  };
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return errorResponse('invalid JSON', HTTP_BAD_REQUEST);
  }

  const text = parseRequestBody(body);
  if (!text) return errorResponse('text field is required', HTTP_BAD_REQUEST);

  try {
    const message = await client.messages.create(buildMessages(text));

    if (message.stop_reason === 'max_tokens') {
      return errorResponse('contract too large to evaluate', HTTP_UNPROCESSABLE);
    }

    const content = message.content[0];
    if (!content || content.type !== 'text') {
      return errorResponse('unexpected response type', HTTP_INTERNAL);
    }

    const parsed = JSON.parse(stripFences(content.text.trim()));
    const result = EvalResponseSchema.safeParse(parsed);

    if (!result.success) {
      return errorResponse('model returned invalid response', HTTP_INTERNAL);
    }

    return NextResponse.json(result.data);
  } catch (e) {
    const status = e instanceof Anthropic.APIError ? e.status : HTTP_INTERNAL;
    return errorResponse('evaluation failed', status);
  }
}
