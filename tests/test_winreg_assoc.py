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

IS_WINDOWS = sys.platform == "win32"

# The four cases at the bottom of this file used to carry
# ``@pytest.mark.skipif(sys.platform != "win32")``. The suite's test job
# runs on ubuntu-latest (.github/workflows/ci.yml), so that marker silenced
# them on every CI run while reporting green. They assert the documented
# contract for the platform they are actually on instead: the real HKCU
# round trip on Windows, the documented RuntimeError refusal elsewhere.
# Both halves are real behaviour of ``winreg_assoc``; neither is a skip.


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
# Launcher / icon / command resolution: frozen vs. checkout, on-PATH vs. not
# ---------------------------------------------------------------------------


def test_launcher_path_uses_sys_executable_when_frozen(monkeypatch):
    monkeypatch.setattr(wa, "_is_frozen", lambda: True)
    assert wa._launcher_path() == wa.sys.executable


def test_launcher_path_falls_back_to_python_dash_m_off_path(monkeypatch):
    monkeypatch.setattr(wa, "_is_frozen", lambda: False)
    monkeypatch.setattr(wa.shutil, "which", lambda _name: None)
    launcher = wa._launcher_path()
    assert launcher == f'"{wa.sys.executable}" -m {wa.APP_NAME}'


def test_icon_source_uses_sys_executable_when_frozen(monkeypatch):
    monkeypatch.setattr(wa, "_is_frozen", lambda: True)
    assert wa._icon_source() == f'"{wa.sys.executable}",0'


def test_icon_source_falls_back_to_pythonw_off_path(monkeypatch):
    monkeypatch.setattr(wa, "_is_frozen", lambda: False)
    monkeypatch.setattr(wa.shutil, "which", lambda _name: None)
    icon = wa._icon_source()
    assert icon.endswith('pythonw.exe",0')


def test_open_command_does_not_double_quote_an_already_quoted_launcher(
    monkeypatch,
):
    """The ``python -m epy_papers`` fallback is already quoted around the
    interpreter path; wrapping it AGAIN would produce a broken command
    string like ``""C:\\...python.exe" -m epy_papers" "%1"``.
    """
    monkeypatch.setattr(
        wa, "_launcher_path", lambda: '"C:\\py\\python.exe" -m epy_papers'
    )
    cmd = wa._open_command()
    assert cmd == '"C:\\py\\python.exe" -m epy_papers "%1"'


def test_open_command_quotes_an_unquoted_launcher(monkeypatch):
    monkeypatch.setattr(
        wa, "_launcher_path", lambda: "C:\\bin\\epy_papers.exe"
    )
    cmd = wa._open_command()
    assert cmd == '"C:\\bin\\epy_papers.exe" "%1"'


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


def test_open_default_apps_settings_true_on_windows(monkeypatch):
    """On Windows the per-app Settings URI is launched via os.startfile.

    Mocked: a real call would pop the actual Windows Settings app on the
    machine running the suite.
    """
    monkeypatch.setattr(wa, "_is_windows", lambda: True)
    seen: list[str] = []
    monkeypatch.setattr(wa.os, "startfile", lambda uri: seen.append(uri))
    assert wa.open_default_apps_settings() is True
    assert seen == [
        "ms-settings:defaultapps?registeredAppMachineKey="
        f"Software\\RegisteredApplications\\{wa.APP_NAME}"
    ]


def test_open_default_apps_settings_falls_back_to_the_generic_uri(
    monkeypatch,
):
    """If the per-app URI fails to resolve (older Windows builds), the
    generic 'Default apps' pane is tried before giving up.
    """
    monkeypatch.setattr(wa, "_is_windows", lambda: True)
    seen: list[str] = []

    def _startfile(uri):
        seen.append(uri)
        if "registeredAppMachineKey" in uri:
            raise OSError("no such URI handler")

    monkeypatch.setattr(wa.os, "startfile", _startfile)
    assert wa.open_default_apps_settings() is True
    assert seen == [
        "ms-settings:defaultapps?registeredAppMachineKey="
        f"Software\\RegisteredApplications\\{wa.APP_NAME}",
        "ms-settings:defaultapps",
    ]


def test_open_default_apps_settings_false_when_both_uris_fail(monkeypatch):
    monkeypatch.setattr(wa, "_is_windows", lambda: True)
    monkeypatch.setattr(
        wa.os,
        "startfile",
        lambda _uri: (_ for _ in ()).throw(OSError("no handler")),
    )
    assert wa.open_default_apps_settings() is False


# ---------------------------------------------------------------------------
# Real HKCU round-trip (self-cleaning)
# ---------------------------------------------------------------------------


def test_register_then_unregister_round_trip():
    """register writes the documented keys; unregister removes them."""
    if not IS_WINDOWS:
        with pytest.raises(RuntimeError, match="only supported on Windows"):
            wa.register(make_default=False)
        with pytest.raises(RuntimeError, match="only supported on Windows"):
            wa.unregister()
        return
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
            # winreg's stubs type ``name`` as str, but None addresses the
            # key's default value at runtime.
            cmd, _ = winreg.QueryValueEx(
                key,
                None,  # pyright: ignore[reportArgumentType]
            )
        assert "%1" in cmd
    finally:
        removed = wa.unregister()
        assert removed

    with pytest.raises(FileNotFoundError):
        winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{wa.PROGID}"
        )


def _read_default_value(root, path: str):
    """Return the key's default (unnamed) value, or None if unset/absent."""
    import winreg

    try:
        with winreg.OpenKey(root, path) as k:
            value, _ = winreg.QueryValueEx(
                k, None  # pyright: ignore[reportArgumentType]
            )
            return value
    except (FileNotFoundError, OSError):
        return None


def test_register_make_default_writes_and_unregister_clears_it():
    """``make_default=True`` writes the legacy per-extension default, and
    ``unregister`` clears it back out -- but only when it still equals
    this app's ProgID (``unregister`` does not restore whatever a THIRD
    PARTY app's default was before ``register`` overwrote it, so this
    test restores the real pre-test state itself rather than trusting
    that symmetry, keeping this developer machine's actual file
    associations untouched either way).
    """
    if not IS_WINDOWS:
        with pytest.raises(RuntimeError, match="only supported on Windows"):
            wa.register(make_default=True)
        return
    import winreg

    root = winreg.HKEY_CURRENT_USER
    originals = {
        ext: _read_default_value(root, f"Software\\Classes\\{ext}")
        for ext in wa.EXTENSIONS
    }
    try:
        changes = wa.register(make_default=True)
        assert any("Wrote legacy default" in line for line in changes)
        for ext in wa.EXTENSIONS:
            value = _read_default_value(root, f"Software\\Classes\\{ext}")
            assert value == wa.PROGID
    finally:
        removed = wa.unregister()
        assert any("Cleared legacy default" in line for line in removed)
        # Restore whatever was really there before this test touched it.
        for ext in wa.EXTENSIONS:
            original = originals[ext]
            now = _read_default_value(root, f"Software\\Classes\\{ext}")
            if original is not None and now != original:
                with winreg.CreateKey(
                    root, f"Software\\Classes\\{ext}"
                ) as k:
                    wa._set_value(k, None, original)

    for ext in wa.EXTENSIONS:
        assert (
            _read_default_value(root, f"Software\\Classes\\{ext}")
            == originals[ext]
        )


def test_unregister_is_idempotent():
    """A second unregister on a clean hive does not raise."""
    if not IS_WINDOWS:
        with pytest.raises(RuntimeError, match="only supported on Windows"):
            wa.unregister()
        return
    wa.unregister()
    assert wa.unregister() == []


# ---------------------------------------------------------------------------
# CLI wiring (no GUI: registration modes return before QApplication)
# ---------------------------------------------------------------------------


def test_main_unregister_runs_without_gui(capsys):
    """``main(["--unregister"])`` handles the mode and exits cleanly."""
    from epy_papers.app import main

    if not IS_WINDOWS:
        assert main(["--unregister"]) == 2
        assert "only supported on Windows" in capsys.readouterr().err
        return
    assert main(["--unregister"]) == 0
    out = capsys.readouterr().out
    assert "Nothing to remove" in out or "Removed" in out


def test_main_register_round_trip_via_cli(capsys):
    """The CLI register/unregister round trip leaves no keys behind."""
    from epy_papers.app import main

    if not IS_WINDOWS:
        assert main(["--register"]) == 2
        assert "only supported on Windows" in capsys.readouterr().err
        return
    import winreg

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
