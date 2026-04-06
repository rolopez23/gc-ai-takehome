# Step: feedback-schema

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Two new SQLAlchemy models (`ReviewFeedback`, `ClauseFeedback`) and their corresponding Pydantic
schemas. After this step, the database tables exist and can be created/queried, and the API
layer has typed input/output schemas ready to use.

## Done When

- `ReviewFeedback` and `ClauseFeedback` models import cleanly from `models.py`
- Tables are created via `Base.metadata.create_all` with correct columns and constraints
- `FeedbackIn`, `ReviewFeedbackOut`, `ClauseFeedbackOut` schemas validate correctly
- Tests confirm unique constraints, FK relationships, and schema serialization

## Cycles

### review-feedback-model

**Test** — write these tests in `backend/tests/test_feedback.py` and confirm they fail:
- **test_create_review_feedback**: Insert a `ReviewFeedback` row with `review_id`, `vote="up"`,
  `comment="good"`. Assert row persists with correct fields. · setup: create Contract +
  ContractReview in db fixture (same pattern as `test_reviews.py`)
- **test_review_feedback_unique_constraint**: Insert two `ReviewFeedback` rows with the same
  `review_id`. Assert `IntegrityError` on flush. · setup: same

**Code** — Add to `backend/models.py`:
```python
class ReviewFeedback(Base):
    __tablename__ = "review_feedback"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contract_reviews.id"), unique=True
    )
    vote: Mapped[str] = mapped_column()
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    review: Mapped["ContractReview"] = relationship()
```

**Refactor** — none

**Commit**: `add ReviewFeedback model with unique review_id constraint`

---

### clause-feedback-model

**Test** — write these tests in `backend/tests/test_feedback.py` and confirm they fail:
- **test_create_clause_feedback**: Insert a `ClauseFeedback` row with `clause_id`, `vote="down"`,
  `comment=None`. Assert row persists. · setup: create Contract + ContractReview + ReviewClause
- **test_clause_feedback_unique_constraint**: Insert two `ClauseFeedback` rows with the same
  `clause_id`. Assert `IntegrityError`. · setup: same

**Code** — Add to `backend/models.py`:
```python
class ClauseFeedback(Base):
    __tablename__ = "clause_feedback"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    clause_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("review_clauses.id"), unique=True
    )
    vote: Mapped[str] = mapped_column()
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    clause: Mapped["ReviewClause"] = relationship()
```

**Refactor** — none

**Commit**: `add ClauseFeedback model with unique clause_id constraint`

---

### pydantic-schemas

**Test** — write these tests in `backend/tests/test_feedback.py` and confirm they fail:
- **test_feedback_in_valid**: `FeedbackIn(vote="up")` succeeds; `FeedbackIn(vote="up", comment="text")` succeeds
- **test_feedback_in_invalid_vote**: `FeedbackIn(vote="maybe")` raises `ValidationError`
- **test_review_feedback_out_from_model**: Create a `ReviewFeedback` ORM instance, construct
  `ReviewFeedbackOut.model_validate(instance)`, assert all fields round-trip correctly
- **test_clause_feedback_out_from_model**: Same for `ClauseFeedback` → `ClauseFeedbackOut`

**Code** — Add to `backend/schemas.py`:
```python
from enum import Enum

class Vote(str, Enum):
    up = "up"
    down = "down"

class FeedbackIn(BaseModel):
    vote: Vote
    comment: str | None = None

class ReviewFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    review_id: uuid.UUID
    vote: str
    comment: str | None
    created_at: datetime
    updated_at: datetime

class ClauseFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clause_id: uuid.UUID
    vote: str
    comment: str | None
    created_at: datetime
    updated_at: datetime
```

**Refactor** — none

**Commit**: `add FeedbackIn, ReviewFeedbackOut, ClauseFeedbackOut schemas`

---

## Verification

```bash
cd backend
python -m pytest tests/test_feedback.py -v
```

Expected: all tests pass. Additionally, verify table structure:

```bash
cd backend
python -c "
from database import Base
from models import ReviewFeedback, ClauseFeedback
for table_name in ['review_feedback', 'clause_feedback']:
    table = Base.metadata.tables[table_name]
    print(f'\n{table_name}:')
    for col in table.columns:
        print(f'  {col.name}: {col.type} nullable={col.nullable} unique={col.unique}')
"
```

Expected output shows both tables with correct column types, `review_id`/`clause_id` marked
unique, `comment` nullable, `vote` not nullable.
