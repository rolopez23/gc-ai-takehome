"""Playbook parser: reads the GC AI playbook markdown and provides lookup functions."""

import logging
import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger("uvicorn.error")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PLAYBOOK_PATH = REPO_ROOT / "docs" / "gc-ai-takehome" / "gc_ai_playbook.md"


class PlaybookCheck(BaseModel, frozen=True):
    """A single check from the playbook."""

    number: int
    name: str
    importance: str
    description: str


def parse_playbook(path: Path = DEFAULT_PLAYBOOK_PATH) -> dict[str, list[PlaybookCheck]]:
    """Parse the playbook markdown into a dict of agreement_type -> list[PlaybookCheck].

    Raises FileNotFoundError if the path doesn't exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Playbook not found at {path}")

    text = path.read_text(encoding="utf-8")
    result: dict[str, list[PlaybookCheck]] = {}

    # Split on ## headers to find agreement type sections
    # Pattern: ## N. Agreement Type Name (N Checks)
    section_pattern = re.compile(
        r"^## \d+\.\s+(.+?)\s+\(\d+ Checks\)\s*$", re.MULTILINE
    )

    matches = list(section_pattern.finditer(text))

    for i, match in enumerate(matches):
        agreement_type = match.group(1)
        # Get the section content between this header and the next (or end)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end]

        checks = _parse_table_rows(section_text)
        result[agreement_type] = checks

    return result


def _parse_table_rows(section_text: str) -> list[PlaybookCheck]:
    """Parse markdown table rows into PlaybookCheck objects."""
    checks: list[PlaybookCheck] = []

    # Match table rows: | number | name | importance | description |
    row_pattern = re.compile(
        r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\w+)\s*\|\s*(.+?)\s*\|$",
        re.MULTILINE,
    )

    for row_match in row_pattern.finditer(section_text):
        number = int(row_match.group(1))
        name = row_match.group(2).strip()
        importance = row_match.group(3).strip()
        description = row_match.group(4).strip()

        checks.append(
            PlaybookCheck(
                number=number,
                name=name,
                importance=importance,
                description=description,
            )
        )

    return checks


@lru_cache(maxsize=1)
def _cached_playbook() -> dict[str, list[PlaybookCheck]]:
    """Cache the parsed playbook so it's only read once."""
    return parse_playbook()


def get_playbook(
    agreement_type: str, check_names: list[str]
) -> list[PlaybookCheck]:
    """Look up checks by exact name match within an agreement type.

    Raises KeyError if agreement_type is unknown.
    Raises ValueError if zero checks match.
    """
    playbook = _cached_playbook()

    if agreement_type not in playbook:
        raise KeyError(f"Unknown agreement type: {agreement_type}")

    checks_by_name = {c.name: c for c in playbook[agreement_type]}
    matched = [checks_by_name[n] for n in check_names if n in checks_by_name]

    if not matched:
        raise ValueError(
            f"No matching checks found for names {check_names} "
            f"in agreement type '{agreement_type}'"
        )

    return matched


def get_check_names_with_descriptions(agreement_type: str) -> list[str]:
    """Return a list of 'CheckName: description' strings for an agreement type.

    Used to build the enum list for the splitter prompt.
    Raises KeyError if agreement_type is unknown.
    """
    playbook = _cached_playbook()

    if agreement_type not in playbook:
        raise KeyError(f"Unknown agreement type: {agreement_type}")

    return [f"{c.name}: {c.description}" for c in playbook[agreement_type]]


def get_all_check_names(agreement_type: str) -> set[str]:
    """Return the set of all check names for an agreement type.

    Used for absent-check detection.
    Raises KeyError if agreement_type is unknown.
    """
    playbook = _cached_playbook()

    if agreement_type not in playbook:
        raise KeyError(f"Unknown agreement type: {agreement_type}")

    return {c.name for c in playbook[agreement_type]}


def validate_playbook() -> None:
    """Startup validation: parse the playbook and log counts.

    Called from main.py lifespan. Raises if playbook can't be parsed.
    """
    playbook = parse_playbook()
    if not playbook:
        raise RuntimeError("Playbook parsed but contains no agreement types")
    total = sum(len(checks) for checks in playbook.values())
    if total == 0:
        raise RuntimeError("Playbook parsed but contains no checks")
    logger.info(
        "Playbook loaded: %d agreement types, %d total checks",
        len(playbook),
        total,
    )
    for agreement_type, checks in playbook.items():
        logger.info("  %s: %d checks", agreement_type, len(checks))
