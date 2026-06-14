# SPDX-License-Identifier: Proprietary

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from datp.core.enums import Regime
from datp.core.errors import fmt

P = ParamSpec("P")
R = TypeVar("R")

_MODULE = "core.regime"


def enforce_regime(*allowed: Regime) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that restricts a function to specific regimes.

    Raises ``TypeError`` at decoration time if any allowed value is not a ``Regime``.
    Raises ``TypeError`` at call time if the ``regime`` keyword argument is missing
    or is not a ``Regime`` enum.
    Raises ``ValueError`` at call time if the regime is not in the allowed set.
    """
    for r in allowed:
        if not isinstance(r, Regime):
            raise TypeError(
                f"enforce_regime: allowed values must be Regime, got {type(r)!r}"
            )

    allowed_set: frozenset[Regime] = frozenset(allowed)

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            regime = kwargs.get("regime")
            if regime is None:
                raise TypeError(
                    fmt(
                        _MODULE,
                        f"{fn.__qualname__} requires 'regime' keyword argument",
                        f"one of {sorted(r.value for r in allowed_set)}",
                        "missing",
                    )
                )
            if not isinstance(regime, Regime):
                raise TypeError(
                    fmt(
                        _MODULE,
                        f"{fn.__qualname__} requires regime as Regime enum",
                        f"one of {sorted(r.value for r in allowed_set)}",
                        f"got {type(regime)!r}",
                    )
                )
            if regime not in allowed_set:
                raise ValueError(
                    fmt(
                        _MODULE,
                        f"{fn.__qualname__} restricted to regime(s) {sorted(r.value for r in allowed_set)}",
                        f"one of {sorted(r.value for r in allowed_set)}",
                        f"regime='{regime.value}'",
                    )
                )
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
