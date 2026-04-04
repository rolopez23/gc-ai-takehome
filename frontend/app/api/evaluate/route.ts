import Anthropic from '@anthropic-ai/sdk';
import { NextResponse } from 'next/server';
import { SYSTEM_PROMPT } from '../../../prompt';

export async function POST(request: Request) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'invalid JSON' }, { status: 400 });
  }

  const { text } = body;

  if (!text || typeof text !== 'string' || text.trim() === '') {
    return NextResponse.json({ error: 'text field is required' }, { status: 400 });
  }

  try {
    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
    const model = process.env.ANTHROPIC_MODEL ?? 'claude-haiku-4-5-20251001';

    const message = await client.messages.create({
      model,
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: text }],
    });

    const content = message.content[0];
    if (content.type !== 'text') {
      return NextResponse.json({ error: 'unexpected response type' }, { status: 500 });
    }

    const parsed = JSON.parse(content.text);
    return NextResponse.json(parsed);
  } catch {
    return NextResponse.json({ error: 'evaluation failed' }, { status: 500 });
  }
}
