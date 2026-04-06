import { StreamingEventSchema, type StreamingEvent } from "./stream-types";

export async function* readNDJSONStream(
  response: Response,
): AsyncGenerator<StreamingEvent> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop()!;

    for (const line of lines) {
      if (line.trim()) {
        const parsed = JSON.parse(line);
        yield StreamingEventSchema.parse(parsed);
      }
    }
  }

  // Handle remaining buffer
  if (buffer.trim()) {
    const parsed = JSON.parse(buffer);
    yield StreamingEventSchema.parse(parsed);
  }
}
