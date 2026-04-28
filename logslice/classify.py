"""Record classification based on rule sets.

Rules are evaluated in order; the first matching rule wins.
Each rule is a dict with:
  - ``field``:   field name to inspect (dot-notation supported)
  - ``pattern``: regex pattern to match against the string value
  - ``equals``:  exact equality check (alternative to pattern)
  - ``lt`` / ``gt`` / ``lte`` / ``gte``: numeric comparisons
  - ``label``:   classification label to assign when the rule matches

If no rule matches, the record receives the ``default`` label
(``"unclassified"`` unless overridden).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Iterator, List, Optional

Record = Dict[str, Any]
Rule = Dict[str, Any]


def _get(record: Record, field: str) -> Any:
    """Retrieve a possibly-nested value using dot notation."""
    parts = field.split(".")
    val: Any = record
    for part in parts:
        if not isinstance(val, dict):
            return None
        val = val.get(part)
    return val


def _matches_rule(record: Record, rule: Rule) -> bool:
    """Return True if *record* satisfies every condition in *rule*."""
    field = rule.get("field")
    if field is None:
        return False

    value = _get(record, field)

    # Pattern match (regex against string representation)
    if "pattern" in rule:
        if value is None:
            return False
        try:
            if not re.search(rule["pattern"], str(value)):
                return False
        except re.error:
            return False

    # Exact equality
    if "equals" in rule:
        if value != rule["equals"]:
            return False

    # Numeric comparisons — skip if value cannot be coerced
    if any(k in rule for k in ("lt", "gt", "lte", "gte")):
        try:
            num = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
        if "lt" in rule and not (num < float(rule["lt"])):
            return False
        if "gt" in rule and not (num > float(rule["gt"])):
            return False
        if "lte" in rule and not (num <= float(rule["lte"])):
            return False
        if "gte" in rule and not (num >= float(rule["gte"])):
            return False

    return True


def classify_record(
    record: Record,
    rules: List[Rule],
    *,
    label_field: str = "class",
    default: str = "unclassified",
) -> Record:
    """Return a copy of *record* with a classification label added.

    Rules are evaluated in definition order; the first match wins.
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
    *,
    label_field: str = "class",
    default: str = "unclassified",
) -> Iterator[Record]:
    """Classify every record in *records* according to *rules*."""
    for record in records:
        yield classify_record(
            record, rules, label_field=label_field, default=default
        )


def group_by_class(
    records: Iterable[Record],
    rules: List[Rule],
    *,
    label_field: str = "class",
    default: str = "unclassified",
) -> Dict[str, List[Record]]:
    """Classify records and bucket them by their assigned label.

    Returns a dict mapping label -> list of classified records.
    """
    groups: Dict[str, List[Record]] = {}
    for record in classify_records(
        records, rules, label_field=label_field, default=default
    ):
        label = record.get(label_field, default)
        groups.setdefault(str(label), []).append(record)
    return groups
