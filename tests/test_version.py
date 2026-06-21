from importlib.metadata import version

from click.testing import CliRunner

from qcp import __version__
from qcp.cli import main


def test_package_version_comes_from_distribution_metadata():
    assert __version__ == version("qcp")


def test_cli_prints_project_version():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == f"qcp, version {version('qcp')}"
