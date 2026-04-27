"""classify.py — Assign a category label to log records based on field rules.

Each rule is a dict with:
  - field:    the record field to inspect
  - pattern:  a regex pattern to match against the string value (optional)
  - value:    an exact value to compare against (optional)
  - label:    the category string to assign when the rule matches

Rules are evaluated in order; the first match wins.  If no rule matches,
the record receives the *default* label (empty string by default).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Iterator, List, Optional

Record = Dict[str, Any]
Rule = Dict[str, Any]


def _get(record: Record, field: str) -> Optional[Any]:
    """Return the value at *field*, supporting simple dot-notation nesting."""
    parts = field.split(".")
    obj: Any = record
    for part in parts:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def _matches_rule(record: Record, rule: Rule) -> bool:
    """Return True if *record* satisfies *rule*."""
    field = rule.get("field", "")
    value = _get(record, field)

    # Exact value match
    if "value" in rule:
        return value == rule["value"]

    # Regex pattern match (coerce field value to string)
    if "pattern" in rule:
        if value is None:
            return False
        try:
            return bool(re.search(rule["pattern"], str(value)))
        except re.error:
            return False

    # A rule with only a field name matches when the field is present and truthy
    return bool(value)


def classify_record(
    record: Record,
    rules: List[Rule],
    label_field: str = "category",
    default: str = "",
) -> Record:
    """Return a copy of *record* with a classification label added.

    Args:
        record:      The input log record.
        rules:       Ordered list of rule dicts (see module docstring).
        label_field: The key under which the label is stored.
        default:     Label to use when no rule matches.

    Returns:
        A new dict with *label_field* set to the matched label or *default*.
    """
    result = dict(record)
    for rule in rules:
        if _matches_rule(record, rule):
            result[label_field] = rule.get("label", default)
            return result
    result[label_field] = default
    return result


def classify_records(
    records: Iterable[Record],
    rules: List[Rule],
    label_field: str = "category",
    default: str = "",
) -> Iterator[Record]:
    """Yield classified copies of every record in *records*.

    Args:
        records:     Iterable of log record dicts.
        rules:       Ordered list of classification rules.
        label_field: Destination field for the label.
        default:     Fallback label when no rule matches.
    """
    for record in records:
        yield classify_record(record, rules, label_field=label_field, default=default)


def group_by_class(
    records: Iterable[Record],
    rules: List[Rule],
    label_field: str = "category",
    default: str = "",
) -> Dict[str, List[Record]]:
    """Classify all records and bucket them by label.

    Returns:
        A dict mapping each label to the list of records that received it.
    """
    buckets: Dict[str, List[Record]] = {}
    for record in classify_records(records, rules, label_field=label_field, default=default):
        label = record.get(label_field, default)
        buckets.setdefault(label, []).append(record)
    return buckets
