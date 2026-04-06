## Verify: fix-status-bug
## Date: 2026-04-05

### Verified ✅
- **Status transitions from pending → evaluating → completed** — Uploaded `test-contract.txt` via `curl -s -X POST localhost:8000/api/contracts/upload -F file=@tests/fixtures/test-contract.txt`, then polled `/api/reviews/{id}` every 0.5s. Observed `status=evaluating` on polls 1-10, then `status=completed` on poll 11. Previously this would have shown `pending` until `completed` because `flush()` didn't commit.

---
Overall: Verified
