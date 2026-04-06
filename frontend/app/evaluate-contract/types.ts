import { z } from "zod";

export const FairnessRatingSchema = z.enum([
  "fair",
  "non-standard",
  "dealbreaker",
]);

export const ReviewClauseSchema = z.object({
  id: z.string().uuid(),
  section_number: z.string(),
  clause_type: z.string(),
  purpose: z.string().nullable(),
  fairness: FairnessRatingSchema.nullable(),
  market_standard: z.string().nullable(),
  explanation: z.string().nullable(),
  severity: z.number().min(1).max(10).optional().nullable(),
});

export const UploadResponseSchema = z.object({
  contract_id: z.string().uuid(),
  review_id: z.string().uuid(),
  status: z.literal("pending"),
});

export const ReviewPollingSchema = z.object({
  id: z.string().uuid(),
  contract_id: z.string().uuid(),
  status: z.enum(["pending", "reading", "evaluating"]),
});

export const ReviewCompletedSchema = z.object({
  id: z.string().uuid(),
  contract_id: z.string().uuid(),
  status: z.literal("completed"),
  overall_fairness: FairnessRatingSchema.nullable(),
  summary: z.string().nullable(),
  call_to_action: z.array(z.string()).nullable(),
  clauses: z.array(ReviewClauseSchema),
  completed_at: z.string(),
});

export const ReviewFailedSchema = z.object({
  id: z.string().uuid(),
  status: z.literal("failed"),
  failure_message: z.string().nullable(),
  failure_code: z.string().nullable(),
});

export const ReviewResponseSchema = z.discriminatedUnion("status", [
  ReviewPollingSchema,
  ReviewCompletedSchema,
  ReviewFailedSchema,
]);

export type FairnessRating = z.infer<typeof FairnessRatingSchema>;
export type ReviewClause = z.infer<typeof ReviewClauseSchema>;
export type UploadResponse = z.infer<typeof UploadResponseSchema>;
export type ReviewPolling = z.infer<typeof ReviewPollingSchema>;
export type ReviewCompleted = z.infer<typeof ReviewCompletedSchema>;
export type ReviewFailed = z.infer<typeof ReviewFailedSchema>;
export type ReviewResponse = z.infer<typeof ReviewResponseSchema>;
