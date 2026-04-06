# Step: schema-migration

## Summary

Add agentic pipeline columns to existing tables via Alembic migration 003.

### ContractReview additions
- `agreement_type` (String, nullable)

### ReviewClause additions
- `status` (String, default "pending")
- `severity` (Integer, nullable)
- `playbook_status` (String, nullable)
- `playbook_position` (Text, nullable)
- `contract_language` (Text, nullable)
- `finding` (Text, nullable)
- `recommended_redline` (Text, nullable)
- `relevant_checks` (JSON, nullable)
- `cross_references` (JSON, nullable)
- `is_cycle` (Boolean, default false)
- `is_synthetic` (Boolean, default false)

### ReviewClause modifications
- Make `purpose`, `fairness`, `market_standard`, `explanation` nullable (clauses inserted at split time with null evaluation fields)

### Schema updates
- Add new fields to ClauseOut and ReviewOut Pydantic schemas

## Verification
- `cd backend && uv run python -m pytest -v` — all tests pass
- Migration file exists and is syntactically correct

## Files
- Create: `backend/migrations/versions/003_agentic_pipeline.py`
- Modify: `backend/models.py`
- Modify: `backend/schemas.py`
- Modify: `backend/tests/test_models.py` (new column tests)
- Modify: `backend/tests/test_schemas.py` (new field tests)
