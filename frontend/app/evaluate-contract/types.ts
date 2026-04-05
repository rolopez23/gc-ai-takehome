import { z } from 'zod';

export const FairnessRatingSchema = z.enum(['fair', 'non-standard', 'dealbreaker']);

export const EvalClauseSchema = z.object({
  section_number: z.string(),
  clause_type: z.string(),
  purpose: z.string(),
  fairness: FairnessRatingSchema,
  market_standard: z.string(),
  explanation: z.string(),
});

export const EvalSuccessSchema = z.object({
  error: z.null(),
  overall_fairness: FairnessRatingSchema,
  summary: z.string(),
  call_to_action: z.array(z.string()),
  clauses: z.array(EvalClauseSchema),
});

export const EvalErrorSchema = z.object({
  error: z.literal(true),
  reason: z.string(),
});

export const EvalResponseSchema = z.discriminatedUnion('error', [
  EvalSuccessSchema,
  EvalErrorSchema,
]);

export type FairnessRating = z.infer<typeof FairnessRatingSchema>;
export type EvalClause = z.infer<typeof EvalClauseSchema>;
export type EvalSuccess = z.infer<typeof EvalSuccessSchema>;
export type EvalError = z.infer<typeof EvalErrorSchema>;
export type EvalResponse = z.infer<typeof EvalResponseSchema>;
