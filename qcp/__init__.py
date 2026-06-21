"""QCP package metadata."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("qcp-cli")
except PackageNotFoundError:
    __version__ = "0+unknown"
