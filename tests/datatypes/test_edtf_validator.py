# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""The EDTF fast path must reach the verdict the EDTF grammar would reach.

Values the fast path does not decide itself are handed to
``marshmallow_utils.fields.edtfdatestring.parse_edtf`` (a pyparsing grammar costing
~1.4 ms per value), so these tests compare both routes value by value.
"""

from __future__ import annotations

import edtf
import pytest
from marshmallow import ValidationError
from marshmallow_utils.fields.edtfdatestring import EDTFValidator

from oarepo_model.datatypes.date import MultilayerEDTFValidator

TYPES = {
    "date": [edtf.Date],
    "interval": [edtf.Interval],
    "date or interval": [edtf.Date, edtf.Interval],
    "date and time or date": [edtf.DateAndTime, edtf.Date],
    "any": [],
}

VALUES = [
    # strict dates
    "2024-01-01",
    "0001-01-01",
    "9999-12-31",
    "2024-02-29",
    # strict intervals
    "2024-01-01/2024-02-01",
    "2024-01-01/2024-01-01",
    "2024-02-29/2024-02-29",
    # dates that are not strict
    "2024-1-1",
    "24-01-01",
    "2024-01-01 ",
    "0000-01-01",
    # dates that do not exist
    "2023-02-29",
    "2024-13-01",
    "2024-01-32",
    # intervals that are not strict, or not chronological
    "1964/2008",
    "2004-06/2006-08",
    "2004-02-01/2005",
    "2024-01-01/..",
    "../2024-01-01",
    "2024-01-01/2024-02-01/2024-03-01",
    "2024-02-01/2024-01-01",
    "2023-02-28/2023-02-29",
    # qualified, fuzzy and otherwise non-strict values
    "2024-01-01?",
    "2024-01-01~",
    "2024?",
    "2024-01?",
    "2024-XX-01",
    "2024-21",
    "2024-01-01T12:00:00",
    "2024-01-01T12:00:00/2024-02-01",
    "{2024-01-01, 2024-02-01}",
    "",
    "not a date",
]


def _outcome(validator, value: str) -> str:
    """How a validator reacts: accepted, rejected, or the error it dies with.

    The grammar path dies on some inputs (``2024-21`` makes ``edtf``'s ``Season`` blow
    up, an open bound makes the chronological comparison raise). Those inputs are
    included on purpose: the fast path must not change what happens to them either.
    """
    try:
        validator(value)
        return "valid"
    except ValidationError:
        return "invalid"
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__


@pytest.mark.parametrize("value", VALUES)
@pytest.mark.parametrize("kind", list(TYPES))
def test_fast_path_agrees_with_the_grammar(value: str, kind: str) -> None:
    fast = MultilayerEDTFValidator(types=TYPES[kind])
    grammar = EDTFValidator(types=TYPES[kind])

    assert _outcome(fast, value) == _outcome(grammar, value)


def test_interval_validator_rejects_a_bare_date() -> None:
    """The fast path used to accept anything that parses as a date, types be damned."""
    with pytest.raises(ValidationError):
        MultilayerEDTFValidator(types=[edtf.Interval])("2024-01-01")


def test_date_validator_rejects_an_interval() -> None:
    with pytest.raises(ValidationError):
        MultilayerEDTFValidator(types=[edtf.Date])("2024-01-01/2024-02-01")


def test_strict_values_are_validated_without_the_grammar(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_grammar(_value):
        raise AssertionError("strict input must not reach the EDTF grammar")

    monkeypatch.setattr("marshmallow_utils.fields.edtfdatestring.parse_edtf", no_grammar)

    assert MultilayerEDTFValidator(types=[edtf.Date])("2024-01-01") == "2024-01-01"
    assert MultilayerEDTFValidator(types=[edtf.Interval])("2024-01-01/2024-02-01") == "2024-01-01/2024-02-01"
    assert MultilayerEDTFValidator(types=[edtf.Date, edtf.Interval])("2024-01-01/2024-02-01")
    assert MultilayerEDTFValidator(types=[])("2024-01-01") == "2024-01-01"


def test_values_the_fast_path_cannot_decide_go_to_the_grammar() -> None:
    validator = MultilayerEDTFValidator(types=[edtf.Date, edtf.Interval])

    for value in ("2024-01-01T12:00:00", "1964/2008", "2024-01-01?", "not-a-date", ""):
        assert validator._accepts_strict_value(value) is False

    assert validator._accepts_strict_value("2024-01-01") is True
    assert validator._accepts_strict_value("2024-01-01/2024-02-01") is True


def test_non_string_values_are_left_to_the_grammar() -> None:
    validator = MultilayerEDTFValidator(types=[edtf.Date])

    assert validator._accepts_strict_value(2024) is False
    assert validator._accepts_strict_value(None) is False
