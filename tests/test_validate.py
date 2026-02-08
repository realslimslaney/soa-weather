"""Tests for soa_weather.validate."""

import polars as pl
import pytest

from soa_weather.validate import SchemaValidationError, validate_schema


@pytest.fixture()
def sample_schema():
    return pl.Schema(
        {
            "id": pl.String,
            "value": pl.Float64,
            "count": pl.Int64,
        }
    )


def _make_df(schema: pl.Schema) -> pl.DataFrame:
    """Create an empty DataFrame with the given schema."""
    return pl.DataFrame(schema=schema)


# --- happy path ---


def test_matching_schema_returns_no_issues(sample_schema):
    df = _make_df(sample_schema)
    issues = validate_schema(df, sample_schema)
    assert issues == []


def test_matching_schema_with_data(sample_schema):
    df = pl.DataFrame({"id": ["a", "b"], "value": [1.0, 2.0], "count": [10, 20]})
    issues = validate_schema(df, sample_schema)
    assert issues == []


# --- missing columns ---


def test_missing_column_detected(sample_schema):
    df = pl.DataFrame({"id": ["a"], "value": [1.0]})
    issues = validate_schema(df, sample_schema)
    assert len(issues) == 1
    assert "Missing column" in issues[0]
    assert "'count'" in issues[0]


def test_multiple_missing_columns(sample_schema):
    df = pl.DataFrame({"id": ["a"]})
    issues = validate_schema(df, sample_schema)
    missing = [i for i in issues if "Missing" in i]
    assert len(missing) == 2


# --- extra columns ---


def test_extra_column_detected(sample_schema):
    df = _make_df(sample_schema).with_columns(pl.lit("x").alias("bonus"))
    issues = validate_schema(df, sample_schema)
    assert len(issues) == 1
    assert "Unexpected column" in issues[0]
    assert "'bonus'" in issues[0]


# --- dtype mismatches ---


def test_dtype_mismatch_detected(sample_schema):
    bad_schema = pl.Schema({"id": pl.String, "value": pl.Int64, "count": pl.Int64})
    df = _make_df(bad_schema)
    issues = validate_schema(df, sample_schema)
    assert len(issues) == 1
    assert "Dtype mismatch" in issues[0]
    assert "'value'" in issues[0]


# --- combined issues ---


def test_multiple_issue_types_at_once(sample_schema):
    # id wrong type, missing value+count, extra bonus
    df = pl.DataFrame({"id": [1], "bonus": ["x"]})
    issues = validate_schema(df, sample_schema)
    missing = [i for i in issues if "Missing" in i]
    extra = [i for i in issues if "Unexpected" in i]
    dtype = [i for i in issues if "Dtype" in i]
    assert len(missing) == 2
    assert len(extra) == 1
    assert len(dtype) == 1


# --- strict mode ---


def test_strict_false_does_not_raise(sample_schema):
    df = pl.DataFrame({"id": ["a"]})
    issues = validate_schema(df, sample_schema, strict=False)
    assert len(issues) > 0


def test_strict_true_raises(sample_schema):
    df = pl.DataFrame({"id": ["a"]})
    with pytest.raises(SchemaValidationError, match="Schema validation failed"):
        validate_schema(df, sample_schema, strict=True)


def test_strict_true_no_raise_on_valid(sample_schema):
    df = _make_df(sample_schema)
    issues = validate_schema(df, sample_schema, strict=True)
    assert issues == []
