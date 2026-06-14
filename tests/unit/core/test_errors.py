from __future__ import annotations

from datp.core.errors import fmt, fmt_missing


class TestFmt:
    def test_formats_module_problem_expected_got(self) -> None:
        result = fmt("core.device", "CUDA missing", "True", "False")
        assert result == "[core.device] CUDA missing. Expected: True. Got: False."

    def test_empty_strings_produce_valid_output(self) -> None:
        result = fmt("", "", "", "")
        assert result == "[] . Expected: . Got: ."

    def test_special_characters_in_fields(self) -> None:
        result = fmt("a.b", "x: y", "<value>", "[none]")
        assert result == "[a.b] x: y. Expected: <value>. Got: [none]."

    def test_output_is_always_a_string(self) -> None:
        result = fmt("m", "p", "e", "g")
        assert isinstance(result, str)


class TestFmtMissing:
    def test_formats_module_and_what_not_found(self) -> None:
        result = fmt_missing("scoring.loading", "score directory /tmp/x")
        assert result == "[scoring.loading] score directory /tmp/x not found."

    def test_empty_module_and_what(self) -> None:
        result = fmt_missing("", "")
        assert result == "[]  not found."

    def test_special_characters_in_fields(self) -> None:
        result = fmt_missing("data.audit", "file: /path/to/[data]")
        assert result == "[data.audit] file: /path/to/[data] not found."

    def test_output_is_always_a_string(self) -> None:
        result = fmt_missing("m", "w")
        assert isinstance(result, str)
