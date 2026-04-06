import { z } from "zod";

export const StartedEventSchema = z.object({
  event: z.literal("started"),
  review_id: z.string(),
  summary: z.string(),
  call_to_action: z.array(z.string()),
});

export const TokenEventSchema = z.object({
  event: z.literal("token"),
  field: z.string(),
  text: z.string(),
});

export const VerifyingEventSchema = z.object({
  event: z.literal("verifying"),
  is_contract: z.boolean(),
});

export const SplittingEventSchema = z.object({
  event: z.literal("splitting"),
  agreement_type: z.string(),
  clause_count: z.number(),
});

export const StreamClauseSchema = z.object({
  section_number: z.string(),
  clause_type: z.string(),
  severity: z.number(),
  fairness: z.enum(["fair", "non-standard", "dealbreaker"]),
  purpose: z.string().optional(),
  market_standard: z.string().optional(),
  explanation: z.string().optional(),
  playbook_status: z.string().nullable().optional(),
  playbook_position: z.string().nullable().optional(),
  contract_language: z.string().nullable().optional(),
  finding: z.string().optional(),
  recommended_redline: z.string().nullable().optional(),
  status: z.string().optional(),
  is_synthetic: z.boolean().optional(),
});

export const ClauseEvaluatedEventSchema = z.object({
  event: z.literal("clause_evaluated"),
  clause: StreamClauseSchema,
});

export const ClauseErrorEventSchema = z.object({
  event: z.literal("clause_error"),
  section_number: z.string(),
  clause_type: z.string(),
  error: z.string(),
});

export const ReplaceEventSchema = z.object({
  event: z.literal("replace"),
  field: z.string(),
  text: z.string().optional(),
  value: z.array(z.string()).optional(),
});

export const CompletedEventSchema = z.object({
  event: z.literal("completed"),
  result: z.object({
    overall_fairness: z.enum(["fair", "non-standard", "dealbreaker"]),
    agreement_type: z.string(),
    summary: z.string(),
    call_to_action: z.array(z.string()),
    clauses: z.array(StreamClauseSchema),
  }),
});

export const RejectedEventSchema = z.object({
  event: z.literal("rejected"),
  reason: z.string(),
});

export const FailedEventSchema = z.object({
  event: z.literal("failed"),
  reason: z.string(),
});

export const StreamingEventSchema = z.discriminatedUnion("event", [
  StartedEventSchema,
  TokenEventSchema,
  VerifyingEventSchema,
  SplittingEventSchema,
  ClauseEvaluatedEventSchema,
  ClauseErrorEventSchema,
  ReplaceEventSchema,
  CompletedEventSchema,
  RejectedEventSchema,
  FailedEventSchema,
]);

export type StreamingEvent = z.infer<typeof StreamingEventSchema>;
export type StreamClause = z.infer<typeof StreamClauseSchema>;
