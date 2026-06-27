"""Smoke tests verifying the package is importable and versioned without torch."""

import importlib

import pico_nlu


def test_version_is_string() -> None:
    assert isinstance(pico_nlu.__version__, str)
    assert pico_nlu.__version__


def test_version_value() -> None:
    assert pico_nlu.__version__ == "0.1.0"


def test_importing_core_does_not_pull_in_torch() -> None:
    """Importing the top-level package must never transitively import torch.

    This guards the ARCHITECTURE.md §4.1 rule: core must not require torch.
    """
    importlib.import_module("pico_nlu")
    import sys

    assert "torch" not in sys.modules


def test_error_hierarchy_is_subclassed_from_pico_error() -> None:
    from pico_nlu.errors import (
        DatasetValidationError,
        ExtraNotInstalledError,
        ModelNotTrainedError,
        PersistenceError,
        PicoError,
    )

    assert issubclass(DatasetValidationError, PicoError)
    assert issubclass(ModelNotTrainedError, PicoError)
    assert issubclass(PersistenceError, PicoError)
    assert issubclass(ExtraNotInstalledError, PicoError)


def test_cli_main_no_args_returns_zero(capsys: object) -> None:
    from pico_nlu.cli import main

    assert main([]) == 0
