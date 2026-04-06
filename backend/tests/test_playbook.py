"""Tests for the playbook parser service."""

import os
from pathlib import Path

import pytest

from services.playbook import (
    PlaybookCheck,
    get_all_check_names,
    get_check_names_with_descriptions,
    get_playbook,
    parse_playbook,
    validate_playbook,
)

# Path to the real playbook in the repo
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLAYBOOK_PATH = REPO_ROOT / "docs" / "gc-ai-takehome" / "gc_ai_playbook.md"


class TestParsePlaybook:
    """Tests for parse_playbook()."""

    def test_returns_dict_of_agreement_types(self):
        result = parse_playbook(PLAYBOOK_PATH)
        assert isinstance(result, dict)
        assert len(result) == 4

    def test_agreement_type_keys(self):
        result = parse_playbook(PLAYBOOK_PATH)
        expected_keys = {
            "SaaS Master Service Agreement",
            "Mutual Non-Disclosure Agreement",
            "Commercial Master Services Agreement \u2014 Non-SaaS",
            "Data Processing Agreement",
        }
        assert set(result.keys()) == expected_keys

    def test_saas_has_21_checks(self):
        result = parse_playbook(PLAYBOOK_PATH)
        assert len(result["SaaS Master Service Agreement"]) == 21

    def test_nda_has_15_checks(self):
        result = parse_playbook(PLAYBOOK_PATH)
        assert len(result["Mutual Non-Disclosure Agreement"]) == 15

    def test_commercial_msa_has_80_checks(self):
        result = parse_playbook(PLAYBOOK_PATH)
        checks = result["Commercial Master Services Agreement \u2014 Non-SaaS"]
        assert len(checks) == 80

    def test_dpa_has_16_checks(self):
        result = parse_playbook(PLAYBOOK_PATH)
        assert len(result["Data Processing Agreement"]) == 16

    def test_total_132_checks(self):
        result = parse_playbook(PLAYBOOK_PATH)
        total = sum(len(checks) for checks in result.values())
        assert total == 132

    def test_check_is_playbook_check_type(self):
        result = parse_playbook(PLAYBOOK_PATH)
        first_check = result["SaaS Master Service Agreement"][0]
        assert isinstance(first_check, PlaybookCheck)

    def test_check_fields_populated(self):
        result = parse_playbook(PLAYBOOK_PATH)
        first_check = result["SaaS Master Service Agreement"][0]
        assert first_check.name == "Payment Terms"
        assert first_check.importance == "Medium"
        assert "Net 45" in first_check.description

    def test_check_number_field(self):
        result = parse_playbook(PLAYBOOK_PATH)
        checks = result["SaaS Master Service Agreement"]
        assert checks[0].number == 1
        assert checks[20].number == 21

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            parse_playbook(Path("/nonexistent/path.md"))


class TestGetPlaybook:
    """Tests for get_playbook() exact-match lookup."""

    def test_returns_matching_checks(self):
        checks = get_playbook(
            "SaaS Master Service Agreement",
            ["Payment Terms", "Auto-Renewal"],
        )
        assert len(checks) == 2
        names = {c.name for c in checks}
        assert names == {"Payment Terms", "Auto-Renewal"}

    def test_single_check_lookup(self):
        checks = get_playbook("Data Processing Agreement", ["Audit Rights"])
        assert len(checks) == 1
        assert checks[0].name == "Audit Rights"

    def test_zero_matches_raises_value_error(self):
        with pytest.raises(ValueError, match="No matching checks"):
            get_playbook("SaaS Master Service Agreement", ["Nonexistent Check"])

    def test_unknown_agreement_type_raises_key_error(self):
        with pytest.raises(KeyError):
            get_playbook("Unknown Agreement Type", ["Payment Terms"])

    def test_preserves_order(self):
        checks = get_playbook(
            "SaaS Master Service Agreement",
            ["Uptime SLA", "Payment Terms", "Auto-Renewal"],
        )
        names = [c.name for c in checks]
        assert names == ["Uptime SLA", "Payment Terms", "Auto-Renewal"]


class TestGetCheckNamesWithDescriptions:
    """Tests for get_check_names_with_descriptions()."""

    def test_returns_list_of_strings(self):
        result = get_check_names_with_descriptions("SaaS Master Service Agreement")
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)

    def test_count_matches_agreement(self):
        result = get_check_names_with_descriptions("SaaS Master Service Agreement")
        assert len(result) == 21

    def test_format_includes_name_and_description(self):
        result = get_check_names_with_descriptions("SaaS Master Service Agreement")
        # Each entry should contain the check name and some description text
        first = result[0]
        assert "Payment Terms" in first
        assert "Net 45" in first

    def test_unknown_agreement_type_raises(self):
        with pytest.raises(KeyError):
            get_check_names_with_descriptions("Unknown Type")


class TestGetAllCheckNames:
    """Tests for get_all_check_names()."""

    def test_returns_set(self):
        result = get_all_check_names("SaaS Master Service Agreement")
        assert isinstance(result, set)

    def test_saas_has_21_names(self):
        result = get_all_check_names("SaaS Master Service Agreement")
        assert len(result) == 21

    def test_contains_expected_names(self):
        result = get_all_check_names("SaaS Master Service Agreement")
        assert "Payment Terms" in result
        assert "Exit Assistance" in result

    def test_unknown_agreement_type_raises(self):
        with pytest.raises(KeyError):
            get_all_check_names("Unknown Type")


class TestValidatePlaybook:
    """Tests for validate_playbook() startup validation."""

    def test_validate_succeeds_with_real_playbook(self):
        # Should not raise
        validate_playbook()

    def test_validate_logs_counts(self, caplog):
        import logging

        with caplog.at_level(logging.INFO):
            validate_playbook()
        assert "132" in caplog.text or "playbook" in caplog.text.lower()
