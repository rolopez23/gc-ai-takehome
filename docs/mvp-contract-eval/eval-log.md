# Eval Log: MVP Contract Evaluation

Informal tracking of prompt performance across models and contracts. Directional until a full eval pipeline is built.

See [AGENTS.md eval rules](../../AGENTS.md#eval-rules) for benchmarks.

---

## 2026-04-04 — Initial verification run

**Model**: `claude-3-haiku-20240307`
**Prompt version**: Zod-derived schemas, scoring terms `fair/non-standard/dealbreaker`
**Fence stripping**: Required — model wraps output in ```json fences despite instruction

| Contract | Expected | Actual | Schema Valid | TTFT | Notes |
|---|---|---|---|---|---|
| non-contract (cookie recipe) | `error: true` | `error: true` | yes | ~1s | Correctly detected non-contract |
| simple 4-clause | `fair` | `fair` (4 clauses, all fair) | yes | ~2s | Clean pass |

### Truncation failures (Haiku 3 — max_tokens: 4096)

| Contract | Status | Notes |
|---|---|---|
| contract_1_clean | TRUNCATED | JSON cut off before closing brace |
| contract_2_egregious | TRUNCATED | Same — too many clauses for 4096 output |
| contract_3_nonstandard | TRUNCATED | Same |
| contract_4_minor_issues | TRUNCATED | Same |
| contract_5_mixed | TRUNCATED | Same |

**Conclusion**: `claude-3-haiku-20240307` (4096 max output) cannot handle full contract evaluation. Need a model with higher output limits for the training contracts.

---

## 2026-04-04 — Haiku 4.5 partial run (pre-fence-strip)

**Model**: `claude-haiku-4-5-20251001`
**Fence stripping**: Not applied in first run — all results showed valid JSON wrapped in fences

| Contract | Expected | Actual (from raw output) | Schema Valid | Notes |
|---|---|---|---|---|
| non-contract | `error: true` | `error: true` | yes (after strip) | Reason text customized per input |
| contract_1_clean | `fair` | `fair` | — | Truncated at 4096, needs higher max_tokens |
| contract_2_egregious | `dealbreaker` | `dealbreaker` | — | Truncated |
| contract_3_nonstandard | `fair` | `fair` | — | Truncated; expected non-standard — needs investigation |
| contract_4_minor_issues | `non-standard` | `dealbreaker` | — | Truncated; scored harsher than expected |
| contract_5_mixed | `dealbreaker` | `dealbreaker` | — | Truncated |

**Observations**:
- Both models wrap JSON in markdown fences — need fence stripping in the API route
- Haiku 4.5 supports up to 8192 output tokens — may still truncate on large contracts
- contract_3_nonstandard scored `fair` when we expected `non-standard` — prompt may need tuning or benchmark may need adjustment
- contract_4_minor_issues scored `dealbreaker` when we expected `non-standard` — the expanded dealbreaker definition and death-by-paper-cuts rule may be aggressive

---

## Model Constraints Reference

| Model | Max Output Tokens | Context Window | Cost (input/output per MTok) |
|---|---|---|---|
| `claude-3-haiku-20240307` | 4,096 | 200K | $0.25 / $1.25 |
| `claude-haiku-4-5-20251001` | 8,192 | 200K | $0.80 / $4.00 |
| `claude-sonnet-4-6` | 16,384 | 200K | $3.00 / $15.00 |

**Recommendation**: Use Haiku 4.5 for dev/testing with `max_tokens: 8192`. If truncation persists on large contracts, bump to Sonnet. API route should detect `stop_reason: 'max_tokens'` and return a structured error.

---

## Action Items

- [ ] Add fence stripping to API route (`route.ts`) before `JSON.parse`
- [ ] Check `stop_reason` for truncation and return structured error
- [ ] Re-run full contract suite on Haiku 4.5 with `max_tokens: 8192` after fence stripping
- [ ] Investigate contract_3_nonstandard scoring `fair` — may need prompt tuning or benchmark adjustment
- [ ] Add TTFT measurement to API route or verification script
