"""Tests for logslice.cli_validate helpers."""
import argparse
import pytest
from logslice.cli_validate import parse_type_spec, parse_allowed_spec, add_validate_args


class TestParseTypeSpec:
    def test_single_str(self):
        assert parse_type_spec(["level:str"]) == {"level": str}

    def test_multiple(self):
        result = parse_type_spec(["code:int", "ratio:float"])
        assert result == {"code": int, "ratio": float}

    def test_bool(self):
        assert parse_type_spec(["ok:bool"]) == {"ok": bool}

    def test_empty_list(self):
        assert parse_type_spec([]) == {}

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="Invalid type spec"):
            parse_type_spec(["levelstr"])

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown type"):
            parse_type_spec(["level:bytes"])

    def test_strips_whitespace(self):
        assert parse_type_spec([" code : int"]) == {"code": int}


class TestParseAllowedSpec:
    def test_single_value(self):
        assert parse_allowed_spec(["level:info"]) == {"level": ["info"]}

    def test_multiple_values(self):
        result = parse_allowed_spec(["level:info,warn,error"])
        assert result == {"level": ["info", "warn", "error"]}

    def test_multiple_fields(self):
        result = parse_allowed_spec(["level:info,warn", "env:prod,staging"])
        assert result["env"] == ["prod", "staging"]

    def test_empty_list(self):
        assert parse_allowed_spec([]) == {}

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="Invalid allowed spec"):
            parse_allowed_spec(["levelinfo"])

    def test_strips_whitespace(self):
        result = parse_allowed_spec(["level: info , warn "])
        assert result == {"level": ["info", "warn"]}


class TestAddValidateArgs:
    def _parser(self):
        p = argparse.ArgumentParser()
        add_validate_args(p)
        return p

    def test_require_arg(self):
        args = self._parser().parse_args(["--require", "level", "--require", "msg"])
        assert args.require == ["level", "msg"]

    def test_type_spec_arg(self):
        args = self._parser().parse_args(["--type", "code:int"])
        assert args.type_specs == ["code:int"]

    def test_allowed_arg(self):
        args = self._parser().parse_args(["--allowed", "level:info,warn"])
        assert args.allowed == ["level:info,warn"]

    def test_drop_invalid_default_false(self):
        args = self._parser().parse_args([])
        assert args.drop_invalid is False

    def test_drop_invalid_flag(self):
        args = self._parser().parse_args(["--drop-invalid"])
        assert args.drop_invalid is True
