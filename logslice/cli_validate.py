"""CLI helpers for --validate-required / --validate-allowed options."""
from typing import Dict, List, Optional, Tuple


def parse_type_spec(specs: List[str]) -> Dict[str, type]:
    """Parse 'field:type' strings into a {field: type} dict.

    Supported types: str, int, float, bool.
    """
    _map = {"str": str, "int": int, "float": float, "bool": bool}
    result: Dict[str, type] = {}
    for spec in specs or []:
        if ":" not in spec:
            raise ValueError(f"Invalid type spec {spec!r}, expected 'field:type'")
        field, type_name = spec.split(":", 1)
        if type_name not in _map:
            raise ValueError(
                f"Unknown type {type_name!r}. Choose from: {list(_map)}"
            )
        result[field.strip()] = _map[type_name]
    return result


def parse_allowed_spec(specs: List[str]) -> Dict[str, List[str]]:
    """Parse 'field:v1,v2' strings into {field: [v1, v2]}."""
    result: Dict[str, List[str]] = {}
    for spec in specs or []:
        if ":" not in spec:
            raise ValueError(f"Invalid allowed spec {spec!r}, expected 'field:v1,v2'")
        field, values = spec.split(":", 1)
        result[field.strip()] = [v.strip() for v in values.split(",")]
    return result


def add_validate_args(parser) -> None:
    """Attach validation-related arguments to an argparse parser."""
    parser.add_argument(
        "--require",
        metavar="FIELD",
        action="append",
        default=[],
        help="Require this field to be present (repeatable).",
    )
    parser.add_argument(
        "--type",
        metavar="FIELD:TYPE",
        action="append",
        default=[],
        dest="type_specs",
        help="Validate field type, e.g. code:int (repeatable).",
    )
    parser.add_argument(
        "--allowed",
        metavar="FIELD:V1,V2",
        action="append",
        default=[],
        help="Restrict field to allowed values (repeatable).",
    )
    parser.add_argument(
        "--drop-invalid",
        action="store_true",
        default=False,
        help="Drop records that fail validation instead of erroring.",
    )
