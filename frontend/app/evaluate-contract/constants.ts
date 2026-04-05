export const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
export const POLL_INTERVAL = 2000;
export const POLL_TIMEOUT = 10 * 60 * 1000;

export const STATUS_TEXT: Record<string, string> = {
  pending: 'Preparing evaluation...',
  reading: 'Reading document...',
  evaluating: 'Evaluating contract...',
};
