from pathlib import Path
from typer.testing import CliRunner

from datp.cli.diagnostic import diagnostic, diagnostic_b, diagnostic_c
import typer

app = typer.Typer()
app.command()(diagnostic)
app.command()(diagnostic_b)
app.command()(diagnostic_c)

runner = CliRunner()

def test_diagnostic_default_data_root():
    # Since we changed data_root default to Path("."), let's test if it handles it.
    # We will test the defaults via introspection of the function signatures.
    import inspect
    from datp.cli.diagnostic import diagnostic, diagnostic_b, diagnostic_c

    sig_a = inspect.signature(diagnostic)
    assert sig_a.parameters["data_root"].default.default == Path(".")

    sig_b = inspect.signature(diagnostic_b)
    assert sig_b.parameters["data_root"].default.default == Path(".")

    sig_c = inspect.signature(diagnostic_c)
    assert sig_c.parameters["data_root"].default.default == Path(".")
