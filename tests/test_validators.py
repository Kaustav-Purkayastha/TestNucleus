import pytest
from testnucleus.models.results import CheckStatus
from testnucleus.validators.completeness import not_null, completeness_rate
from testnucleus.validators.uniqueness import unique
from testnucleus.validators.conformity import email_format, no_trailing_spaces, max_length
from testnucleus.validators.validity import min_value, between, date_format, in_set
from testnucleus.validators.consistency import referential_integrity


# ── completeness ─────────────────────────────────────────────────────────────

def test_not_null_passes_when_no_nulls(sample_engine):
    status, _, _ = not_null(sample_engine, "users", "id", {}, False)
    assert status == CheckStatus.PASS


def test_not_null_fails_when_nulls_present(sample_engine):
    status, _, details = not_null(sample_engine, "users", "email", {}, False)
    assert status == CheckStatus.FAIL
    assert details["null_count"] == 1


def test_completeness_rate_pass(sample_engine):
    # 4/5 non-null emails = 80%
    status, _, details = completeness_rate(sample_engine, "users", "email", {"threshold": 80.0}, False)
    assert status == CheckStatus.PASS
    assert details["rate"] == 80.0


def test_completeness_rate_fail(sample_engine):
    status, _, _ = completeness_rate(sample_engine, "users", "email", {"threshold": 90.0}, False)
    assert status == CheckStatus.FAIL


# ── uniqueness ────────────────────────────────────────────────────────────────

def test_unique_passes_on_id(sample_engine):
    status, _, _ = unique(sample_engine, "users", "id", {}, False)
    assert status == CheckStatus.PASS


def test_unique_fails_on_duplicate_emails(sample_engine):
    status, _, details = unique(sample_engine, "users", "email", {}, False)
    assert status == CheckStatus.FAIL
    assert details["duplicates"] >= 1


# ── conformity ────────────────────────────────────────────────────────────────

def test_email_format_skips_nulls_detects_invalid(sample_engine):
    # nullable=True → skip NULL; "invalid-email" should fail
    status, _, details = email_format(sample_engine, "users", "email", {}, nullable=True)
    assert status == CheckStatus.FAIL
    assert details["invalid_count"] == 1


def test_no_trailing_spaces_detects_spaces(sample_engine):
    status, _, details = no_trailing_spaces(sample_engine, "users", "name", {}, False)
    assert status == CheckStatus.FAIL
    assert details["violating_count"] == 1


def test_max_length_passes(sample_engine):
    status, _, _ = max_length(sample_engine, "users", "name", {"max": 50}, False)
    assert status == CheckStatus.PASS


# ── validity ──────────────────────────────────────────────────────────────────

def test_min_value_fails_on_negative_age(sample_engine):
    status, _, details = min_value(sample_engine, "users", "age", {"min": 0}, False)
    assert status == CheckStatus.FAIL
    assert details["violating_count"] == 1


def test_between_passes_within_range(sample_engine):
    status, _, _ = between(sample_engine, "users", "id", {"min": 1, "max": 10}, False)
    assert status == CheckStatus.PASS


def test_in_set_fails_on_unknown_value(sample_engine):
    status, _, details = in_set(sample_engine, "users", "id", {"values": [1, 2, 3]}, False)
    assert status == CheckStatus.FAIL
    assert details["violating_count"] == 2  # ids 4 and 5 not in set


def test_in_set_missing_param_returns_error(sample_engine):
    status, _, _ = in_set(sample_engine, "users", "id", {}, False)
    assert status == CheckStatus.ERROR


# ── consistency ───────────────────────────────────────────────────────────────

def test_referential_integrity_missing_params(sample_engine):
    status, _, _ = referential_integrity(sample_engine, "users", "id", {}, False)
    assert status == CheckStatus.ERROR
