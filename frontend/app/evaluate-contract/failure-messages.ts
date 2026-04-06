export const FAILURE_MESSAGES: Record<string, string> = {
  too_large: 'This contract is too large to evaluate. Try a shorter document.',
  timeout: 'The evaluation timed out. Please try again.',
  anthropic_error: "We couldn't reach our AI service. Please try again later.",
  parse_error: 'The AI returned an unexpected response. Please try again.',
  unknown: 'Something went wrong. Please try again.',
};

export function getFailureMessage(code: string | null | undefined): string {
  if (!code) return FAILURE_MESSAGES.unknown;
  return FAILURE_MESSAGES[code] ?? FAILURE_MESSAGES.unknown;
}
