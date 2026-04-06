import { z } from 'zod';
import { FairnessRatingSchema } from '@/app/evaluate-contract/types';

export const ContractListItemSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  upload_type: z.string(),
  created_at: z.string(),
  review_status: z.string().nullable(),
  overall_fairness: FairnessRatingSchema.nullable(),
  failure_code: z.string().nullable(),
});

export type ContractListItem = z.infer<typeof ContractListItemSchema>;
