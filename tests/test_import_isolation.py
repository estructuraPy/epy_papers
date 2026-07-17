"""Import-isolation gate (headless / no-GUI-toolkit contract).

``epy_papers``'s root package facade (``Paper`` / journal-catalog functions)
imports only ``_authoring``, ``_render`` and ``_validation`` at module level —
none of those pull in ``PySide6`` at import time; Qt is confined to the
editor widgets (``app.py``, ``tab.py``, dialog modules, ``_previews.py``)
that a bare ``import epy_papers`` never touches. This test proves the
facade/scripting entry point stays importable and usable even when no Qt
binding is installed, so headless/CI usage of ``Paper.from_file(...).to_draft(...)``
never accidentally grows a hard Qt dependency. The hook runs in a fresh
subprocess BEFORE anything imports epy_papers, so a cached module can never
mask a regression.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")


def _run_isolated(blocked_modules: tuple[str, ...], probe: str) -> subprocess.CompletedProcess:
    header = (
        "import builtins\n"
        "_real_import = builtins.__import__\n"
        f"_blocked = {blocked_modules!r}\n"
        "\n"
        "def _fake_import(name, *args, **kwargs):\n"
        "    if any(name == b or name.startswith(b + '.') for b in _blocked):\n"
        "        raise ImportError('blocked for isolation test: ' + name)\n"
        "    return _real_import(name, *args, **kwargs)\n"
        "\n"
        "builtins.__import__ = _fake_import\n"
        "\n"
    )
    script = header + textwrap.dedent(probe).strip() + "\n"
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = _SRC_DIR + (os.pathsep + existing if existing else "")
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=120, env=env,
    )


class TestImportWithoutPySide6:
    def test_import_succeeds(self):
        result = _run_isolated(("PySide6", "PyQt6", "PyQt5", "PySide2"), "import epy_papers\nprint('OK')")
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_facade_class_still_available(self):
        probe = """
            import epy_papers
            assert hasattr(epy_papers, "Paper")
            assert hasattr(epy_papers, "Manuscript")
            print('OK')
        """
        result = _run_isolated(("PySide6", "PyQt6", "PyQt5", "PySide2"), probe)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_paper_builds_and_validates_without_qt(self):
        # The scripting entry point (Paper.from_file/validate) must work headless
        # (e.g. CI/CLI usage) with no Qt binding present at all.
        probe = """
            import epy_papers
            paper = epy_papers.Paper("---\\ntitle: {en: T}\\n---\\n# Body")
            result = paper.validate("eng-structures")
            assert result is not None
            print('OK')
        """
        result = _run_isolated(("PySide6", "PyQt6", "PyQt5", "PySide2"), probe)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout
