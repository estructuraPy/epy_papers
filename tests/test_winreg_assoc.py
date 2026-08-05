"""Tests for the Windows HKCU file-association helpers.

Pure path/command helpers are tested directly. The register/unregister
round-trip runs against the real per-user hive (HKCU) because every key
it touches is app-specific (``epy_papers.Document.1``,
``Applications\\epy_papers.exe``, ``Software\\epy_papers``) and is removed
again in a ``finally`` block, so the test leaves no trace. Mirrors
``epy_reports/tests/test_winreg_assoc.py``.
"""

from __future__ import annotations

import sys

import pytest

from epy_papers._core import winreg_assoc as wa

windows_only = pytest.mark.skipif(
    sys.platform != "win32",
    reason="winreg_assoc only operates on Windows",
)


# ---------------------------------------------------------------------------
# Pure helpers (cross-platform)
# ---------------------------------------------------------------------------


def test_is_windows_matches_platform():
    """``_is_windows`` agrees with sys.platform."""
    assert wa._is_windows() == (sys.platform == "win32")


def test_is_frozen_false_under_pytest():
    """Running under the interpreter is not a frozen bundle."""
    assert wa._is_frozen() is False


def test_open_command_quotes_argument():
    """The open command always passes ``"%1"`` for the file argument."""
    cmd = wa._open_command()
    assert cmd.endswith('"%1"')


def test_icon_source_has_index():
    """The icon source ends with a comma + index."""
    icon = wa._icon_source()
    assert icon.rstrip().endswith(",0")


def test_launcher_path_is_nonempty():
    """A launcher string is always derivable."""
    assert wa._launcher_path()


def test_identity_is_papers():
    """The module carries the epy_papers identity, not the template's."""
    assert wa.APP_NAME == "epy_papers"
    assert wa.PROGID == "epy_papers.Document.1"
    assert wa.APP_KEY == "Applications\\epy_papers.exe"


def test_extensions_are_the_documented_two():
    """The handled extensions are exactly .md / .markdown (no .qmd)."""
    assert wa.EXTENSIONS == (".md", ".markdown")


# ---------------------------------------------------------------------------
# Non-Windows guard branches
# ---------------------------------------------------------------------------


def test_register_raises_off_windows(monkeypatch):
    """``register`` refuses to run on non-Windows platforms."""
    monkeypatch.setattr(wa, "_is_windows", lambda: False)
    with pytest.raises(RuntimeError):
        wa.register()


def test_unregister_raises_off_windows(monkeypatch):
    """``unregister`` refuses to run on non-Windows platforms."""
    monkeypatch.setattr(wa, "_is_windows", lambda: False)
    with pytest.raises(RuntimeError):
        wa.unregister()


def test_open_default_apps_settings_false_off_windows(monkeypatch):
    """Off Windows the Settings launcher reports False."""
    monkeypatch.setattr(wa, "_is_windows", lambda: False)
    assert wa.open_default_apps_settings() is False


# ---------------------------------------------------------------------------
# Real HKCU round-trip (self-cleaning)
# ---------------------------------------------------------------------------


@windows_only
def test_register_then_unregister_round_trip():
    """register writes the documented keys; unregister removes them."""
    import winreg

    try:
        changes = wa.register(make_default=False)
        assert changes
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            f"Software\\Classes\\{wa.APP_KEY}",
        ) as key:
            friendly, _ = winreg.QueryValueEx(key, "FriendlyAppName")
        assert friendly == wa.APP_NAME

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            f"Software\\Classes\\{wa.PROGID}\\shell\\open\\command",
        ) as key:
            cmd, _ = winreg.QueryValueEx(key, None)
        assert "%1" in cmd
    finally:
        removed = wa.unregister()
        assert removed

    with pytest.raises(FileNotFoundError):
        winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{wa.PROGID}"
        )


@windows_only
def test_unregister_is_idempotent():
    """A second unregister on a clean hive does not raise."""
    wa.unregister()
    wa.unregister()


# ---------------------------------------------------------------------------
# CLI wiring (no GUI: registration modes return before QApplication)
# ---------------------------------------------------------------------------


@windows_only
def test_main_unregister_runs_without_gui(capsys):
    """``main(["--unregister"])`` handles the mode and exits cleanly."""
    from epy_papers.app import main

    assert main(["--unregister"]) == 0
    out = capsys.readouterr().out
    assert "Nothing to remove" in out or "Removed" in out


@windows_only
def test_main_register_round_trip_via_cli(capsys):
    """The CLI register/unregister round trip leaves no keys behind."""
    import winreg

    from epy_papers.app import main

    try:
        assert main(["--register"]) == 0
        out = capsys.readouterr().out
        assert "Registered ProgID" in out
    finally:
        assert main(["--unregister"]) == 0

    with pytest.raises(FileNotFoundError):
        winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{wa.PROGID}"
        )
