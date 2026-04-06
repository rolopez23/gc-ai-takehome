import { describe, test, expect } from "vitest";
import { readNDJSONStream } from "@/app/evaluate-contract/stream";
import type { StreamingEvent } from "@/app/evaluate-contract/stream-types";

function makeReadableStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let index = 0;
  return new ReadableStream({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]));
        index++;
      } else {
        controller.close();
      }
    },
  });
}

function mockResponse(chunks: string[]): Response {
  return new Response(makeReadableStream(chunks));
}

async function collectEvents(response: Response): Promise<StreamingEvent[]> {
  const events: StreamingEvent[] = [];
  for await (const event of readNDJSONStream(response)) {
    events.push(event);
  }
  return events;
}

describe("readNDJSONStream", () => {
  test("parses complete NDJSON lines", async () => {
    const response = mockResponse([
      '{"event":"started","review_id":"abc","summary":"hi","call_to_action":[]}\n',
      '{"event":"token","field":"summary","text":"hello"}\n',
    ]);

    const events = await collectEvents(response);
    expect(events).toHaveLength(2);
    expect(events[0].event).toBe("started");
    expect(events[1].event).toBe("token");
  });

  test("handles multiple events in a single chunk", async () => {
    const response = mockResponse([
      '{"event":"token","field":"summary","text":"a"}\n{"event":"token","field":"summary","text":"b"}\n',
    ]);

    const events = await collectEvents(response);
    expect(events).toHaveLength(2);
    if (events[0].event === "token" && events[1].event === "token") {
      expect(events[0].text).toBe("a");
      expect(events[1].text).toBe("b");
    }
  });

  test("handles partial line buffering across chunks", async () => {
    const response = mockResponse([
      '{"event":"token","fiel',
      'd":"summary","text":"buffered"}\n',
    ]);

    const events = await collectEvents(response);
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe("token");
    if (events[0].event === "token") {
      expect(events[0].text).toBe("buffered");
    }
  });

  test("handles trailing data without newline", async () => {
    const response = mockResponse(['{"event":"failed","reason":"error"}']);

    const events = await collectEvents(response);
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe("failed");
  });

  test("skips empty lines", async () => {
    const response = mockResponse([
      '{"event":"token","field":"summary","text":"a"}\n\n\n{"event":"token","field":"summary","text":"b"}\n',
    ]);

    const events = await collectEvents(response);
    expect(events).toHaveLength(2);
  });

  test("validates events via Zod and throws on invalid data", async () => {
    const response = mockResponse(['{"event":"unknown_type","foo":"bar"}\n']);

    await expect(collectEvents(response)).rejects.toThrow();
  });

  test("parses clause_evaluated events with clause data", async () => {
    const clause = {
      section_number: "1.1",
      clause_type: "Termination",
      severity: 3,
      fairness: "fair",
    };
    const response = mockResponse([
      JSON.stringify({ event: "clause_evaluated", clause }) + "\n",
    ]);

    const events = await collectEvents(response);
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe("clause_evaluated");
    if (events[0].event === "clause_evaluated") {
      expect(events[0].clause.section_number).toBe("1.1");
    }
  });
});
