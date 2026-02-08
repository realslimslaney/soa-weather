"""Validation helpers for checking DataFrames against expected schemas."""

import logging

import polars as pl

log = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when a DataFrame fails schema validation in strict mode."""


def validate_schema(
    df: pl.DataFrame,
    expected: pl.Schema,
    *,
    strict: bool = False,
) -> list[str]:
    """Validate that *df* matches *expected* columns and dtypes.

    Parameters
    ----------
    df:
        The DataFrame to validate.
    expected:
        The expected :class:`polars.Schema` (ordered mapping of column names to dtypes).
    strict:
        If ``True``, raise :class:`SchemaValidationError` on the first mismatch.
        If ``False`` (default), log each mismatch as a warning and return the list
        of issues found.

    Returns
    -------
    list[str]
        A list of human-readable issue descriptions.  Empty when the schema matches.
    """
    issues: list[str] = []
    actual = df.schema

    expected_cols = set(expected.names())
    actual_cols = set(actual.names())

    # Missing columns
    for col in expected.names():
        if col not in actual_cols:
            issues.append(f"Missing column: '{col}' (expected {expected[col]})")

    # Extra columns
    for col in actual.names():
        if col not in expected_cols:
            issues.append(f"Unexpected column: '{col}' ({actual[col]})")

    # Dtype mismatches (only for columns present in both)
    for col in expected.names():
        if col in actual_cols and actual[col] != expected[col]:
            issues.append(
                f"Dtype mismatch for '{col}': got {actual[col]}, expected {expected[col]}"
            )

    if issues:
        for issue in issues:
            if strict:
                log.error(issue)
            else:
                log.warning(issue)
        if strict:
            raise SchemaValidationError(
                f"Schema validation failed with {len(issues)} issue(s):\n"
                + "\n".join(f"  - {i}" for i in issues)
            )

    return issues
