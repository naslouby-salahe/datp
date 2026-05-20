from __future__ import annotations


def fmt(module: str, problem: str, expected: str, got: str) -> str:
    """Return ``[module] Problem. Expected: X. Got: Y.``"""
    return f"[{module}] {problem}. Expected: {expected}. Got: {got}."


def fmt_missing(module: str, what: str) -> str:
    """Return ``[module] <what> not found.``"""
    return f"[{module}] {what} not found."


def fmt_constraint(module: str, constraint: str) -> str:
    """Return ``[module] <constraint>``"""
    return f"[{module}] {constraint}"
