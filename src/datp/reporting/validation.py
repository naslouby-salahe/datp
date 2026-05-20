from datp.core.enums import MAIN_BODY_BASELINES, Baseline


def validate_main_body_role(baselines: list[str]) -> None:
    for b in baselines:
        try:
            bl = Baseline(b)
        except ValueError:
            bl = None
        if bl not in MAIN_BODY_BASELINES:
            raise ValueError(
                f"[reporting] Baseline '{b}' is not permitted in main-body "
                f"figures/tables. "
                f"Allowed: {sorted(b.value for b in MAIN_BODY_BASELINES)}"
            )
