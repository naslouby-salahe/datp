from pathlib import Path

def test_sweep_default_data_root():
    import inspect
    from datp.cli.sweep import sweep

    sig = inspect.signature(sweep)
    assert sig.parameters["data_root"].default.default == Path(".")
