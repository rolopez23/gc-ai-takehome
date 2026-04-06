# Step: playbook-parser

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

A module that parses the playbook markdown file (`docs/gc-ai-takehome/gc_ai_playbook.md`) into
structured Python data. Provides a `get_playbook()` function for exact-match check lookups and
a `get_check_names_with_descriptions()` function that returns the enum list for the splitter
prompt. Validates all 132 checks parsed across 4 agreement types at startup.

## Done When

- `parse_playbook()` returns 132 checks across 4 agreement types
- `get_playbook("SaaS MSA", ["Payment Terms"])` returns the matching check
- `get_playbook("SaaS MSA", ["Nonexistent Check"])` raises an error
- `get_check_names_with_descriptions("SaaS MSA")` returns 21 entries
- Startup validation passes (called from `main.py` lifespan)

## Cycles

### parse-markdown-tables

**Test** — write these tests and confirm they fail:
- **test_parse_playbook_returns_all_checks**: `parse_playbook()` returns a dict with 4 keys
  ("SaaS MSA", "NDA", "Commercial MSA", "DPA"), total check count is 132 ·
  setup: path to playbook file
- **test_parse_playbook_check_shape**: each check has `check_number: int`, `check_name: str`,
  `importance: str`, `key_position: str` · setup: parse one agreement type
- **test_parse_saas_msa_count**: "SaaS MSA" has exactly 21 checks
- **test_parse_nda_count**: "NDA" has exactly 15 checks
- **test_parse_commercial_msa_count**: "Commercial MSA" has exactly 80 checks
- **test_parse_dpa_count**: "DPA" has exactly 16 checks

**Code** — create `backend/services/playbook.py` with `parse_playbook(path: str) -> dict[str, list[PlaybookCheck]]`.
Parse the markdown tables using string splitting (no external markdown parser needed — the
format is stable pipe-delimited tables). Each table starts after a `## N. <Agreement Type>`
header. Extract check_number from column 1, check_name from column 2, importance from column 3,
key_position from column 4.

```python
@dataclass
class PlaybookCheck:
    check_number: int
    check_name: str
    importance: str  # "High" | "Medium" | "Low"
    key_position: str
```

**Refactor** — none

**Commit**: `add playbook markdown parser with per-type check counts`

---

### get-playbook-lookup

**Test** — write these tests and confirm they fail:
- **test_get_playbook_exact_match**: `get_playbook("SaaS MSA", ["Payment Terms"])` returns
  a list with one check where check_name == "Payment Terms"
- **test_get_playbook_multiple_checks**: `get_playbook("SaaS MSA", ["Payment Terms", "Auto-Renewal"])`
  returns 2 checks
- **test_get_playbook_zero_match_raises**: `get_playbook("SaaS MSA", ["Nonexistent"])`
  raises `PlaybookLookupError`
- **test_get_playbook_invalid_agreement_type**: `get_playbook("Invalid", ["Payment Terms"])`
  raises `PlaybookLookupError`

**Code** — add `get_playbook(agreement_type: str, check_names: list[str]) -> list[PlaybookCheck]`.
Perform exact-match lookups against the parsed data. Raise `PlaybookLookupError` on zero matches
or invalid agreement type.

**Refactor** — extract the parsed playbook into a module-level singleton (parse once, reuse)

**Commit**: `add get_playbook exact-match lookup with error on zero matches`

---

### check-names-for-splitter

**Test** — write these tests and confirm they fail:
- **test_get_check_names_saas_msa**: `get_check_names_with_descriptions("SaaS MSA")` returns
  21 tuples of (name, description)
- **test_check_name_description_format**: each tuple has a non-empty name and a non-empty
  description string
- **test_get_check_names_general_returns_empty**: `get_check_names_with_descriptions("General")`
  returns an empty list

**Code** — add `get_check_names_with_descriptions(agreement_type: str) -> list[tuple[str, str]]`.
Returns `(check_name, key_position)` tuples for the given agreement type. The key_position
serves as the one-sentence description for the splitter prompt.

**Refactor** — none

**Commit**: `add check name enum list for splitter prompt constraint`

---

### get-all-check-names

**Test** — write these tests and confirm they fail:
- **test_get_all_check_names_for_type**: `get_all_check_names("SaaS MSA")` returns a set
  of 21 strings
- **test_get_all_check_names_for_absent_detection**: calling with "Commercial MSA" returns
  80 check names — used by orchestrator for absent check detection

**Code** — add `get_all_check_names(agreement_type: str) -> set[str]`. Simple extraction
from parsed data.

**Refactor** — none

**Commit**: `add get_all_check_names for absent clause detection`

---

### startup-validation

**Test** — write these tests and confirm they fail:
- **test_validate_playbook_succeeds**: `validate_playbook()` does not raise when the real
  playbook file is present
- **test_validate_playbook_fails_on_bad_file**: `validate_playbook("/nonexistent")` raises
  `PlaybookValidationError`

**Code** — add `validate_playbook(path: str = None)` that calls `parse_playbook()` and asserts
132 total checks across 4 types. Add call to `validate_playbook()` in `main.py` lifespan.

**Refactor** — none

**Commit**: `add playbook startup validation in main.py lifespan`

---

## Verification

```bash
cd backend && uv run pytest tests/test_playbook.py -v
```

Expected: all tests pass. Then verify the startup validation works:

```bash
cd backend && uv run python -c "from services.playbook import validate_playbook; validate_playbook(); print('OK: 132 checks parsed')"
```

Expected output: `OK: 132 checks parsed`
