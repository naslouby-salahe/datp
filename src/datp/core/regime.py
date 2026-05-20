# SPDX-License-Identifier: Proprietary

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from datp.core.enums import Regime
from datp.core.errors import fmt

F = TypeVar("F", bound=Callable[..., Any])


def enforce_regime(*allowed: Regime) -> Callable[[F], F]:
    """Decorator that restricts a function to specific regimes. Raises TypeError/ValueError for invalid or disallowed regime values."""
    for r in allowed:
        if not isinstance(r, Regime):
            raise TypeError(f"enforce_regime: allowed values must be Regime, got {type(r)!r}")

    allowed_set: frozenset[Regime] = frozenset(allowed)

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            regime = kwargs.get("regime")
            if regime is None:
                raise TypeError(
                    fmt("core.regime", f"{fn.__qualname__} requires 'regime' keyword argument",
                        f"one of {sorted(r.value for r in allowed_set)}", "missing")
                )
            if not isinstance(regime, Regime):
                raise TypeError(
                    fmt("core.regime", f"{fn.__qualname__} requires regime as Regime enum",
                        f"one of {sorted(r.value for r in allowed_set)}", f"got {type(regime)!r}")
                )
            if regime not in allowed_set:
                raise ValueError(
                    fmt("core.regime", f"{fn.__qualname__} restricted to regime(s) {sorted(r.value for r in allowed_set)}",
                        f"one of {sorted(r.value for r in allowed_set)}", f"regime='{regime.value}'")
                )
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
