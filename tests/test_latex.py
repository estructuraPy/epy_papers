"""Tests for ``epy_papers._core._latex``: engine discovery and the
on-demand TinyTeX installer.

Nothing here performs a real network download or runs a real installer
executable: ``install_tinytex`` normally fetches a ~70 MB bundle from
GitHub and, on Windows, launches a self-extracting ``.exe`` -- every test
below replaces ``urllib.request.urlretrieve``, ``subprocess.run`` and
``tarfile.open`` with recording stand-ins. This machine already has a
real TinyTeX installed (``find_engine()`` resolves it), which the
engine-discovery tests use directly instead of faking a PATH lookup for
every case.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from epy_papers._core import _latex

# ---------------------------------------------------------------------------
# managed_root
# ---------------------------------------------------------------------------


def test_managed_root_on_windows_uses_appdata(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(_latex.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\Users\someone\AppData\Roaming")
    assert _latex.managed_root() == Path(
        r"C:\Users\someone\AppData\Roaming"
    ) / "TinyTeX"


def test_managed_root_on_windows_falls_back_to_home_without_appdata(
    monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(_latex.sys, "platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    assert _latex.managed_root() == Path.home() / "TinyTeX"


def test_managed_root_on_macos(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(_latex.sys, "platform", "darwin")
    assert _latex.managed_root() == Path.home() / "Library" / "TinyTeX"


def test_managed_root_on_linux(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(_latex.sys, "platform", "linux")
    assert _latex.managed_root() == Path.home() / ".TinyTeX"


# ---------------------------------------------------------------------------
# _engine_in
# ---------------------------------------------------------------------------


def test_engine_in_returns_none_with_no_bin_directory(tmp_path: Path):
    assert _latex._engine_in(tmp_path) is None


def test_engine_in_returns_none_with_an_empty_bin_directory(tmp_path: Path):
    (tmp_path / "bin" / "windows").mkdir(parents=True)
    assert _latex._engine_in(tmp_path) is None


def test_engine_in_finds_a_known_engine_under_an_arch_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(_latex.sys, "platform", "win32")
    arch = tmp_path / "bin" / "windows"
    arch.mkdir(parents=True)
    engine = arch / "pdflatex.exe"
    engine.write_text("", encoding="utf-8")
    assert _latex._engine_in(tmp_path) == engine


def test_engine_in_tries_engines_in_preference_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """xelatex must not shadow pdflatex when both exist: Pandoc's default
    (and the bundled journal classes) target pdflatex specifically.
    """
    monkeypatch.setattr(_latex.sys, "platform", "win32")
    arch = tmp_path / "bin" / "windows"
    arch.mkdir(parents=True)
    (arch / "xelatex.exe").write_text("", encoding="utf-8")
    (arch / "pdflatex.exe").write_text("", encoding="utf-8")
    assert _latex._engine_in(tmp_path) == arch / "pdflatex.exe"


def test_engine_in_uses_no_suffix_off_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(_latex.sys, "platform", "linux")
    arch = tmp_path / "bin" / "x86_64-linux"
    arch.mkdir(parents=True)
    engine = arch / "pdflatex"
    engine.write_text("", encoding="utf-8")
    assert _latex._engine_in(tmp_path) == engine


# ---------------------------------------------------------------------------
# find_engine
# ---------------------------------------------------------------------------


def test_find_engine_prefers_the_one_on_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    on_path = tmp_path / "pdflatex.exe"
    monkeypatch.setattr(
        _latex.shutil,
        "which",
        lambda name: str(on_path) if name == "pdflatex" else None,
    )
    assert _latex.find_engine() == on_path


def test_find_engine_falls_back_to_managed_root_when_nothing_is_on_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(_latex.shutil, "which", lambda _name: None)
    managed_engine = tmp_path / "bin" / "windows" / "pdflatex.exe"
    managed_engine.parent.mkdir(parents=True)
    managed_engine.write_text("", encoding="utf-8")
    monkeypatch.setattr(_latex, "managed_root", lambda: tmp_path)
    assert _latex.find_engine() == managed_engine


def test_find_engine_is_none_when_nothing_exists_anywhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(_latex.shutil, "which", lambda _name: None)
    monkeypatch.setattr(_latex, "managed_root", lambda: tmp_path / "nothing")
    assert _latex.find_engine() is None


def test_a_real_latex_engine_is_actually_discoverable():
    """CONTROL: this development machine has a real TinyTeX (verified
    manually before writing this suite). If this ever returns None, the
    ``fmt="pdf"`` export tests in ``test_public_api_coverage.py`` would
    be silently exercising a code path they cannot actually reach.
    """
    assert _latex.find_engine() is not None


# ---------------------------------------------------------------------------
# install_tinytex -- no real download, no real installer execution
# ---------------------------------------------------------------------------


def test_install_tinytex_on_windows_downloads_and_runs_the_installer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dl_dir = tmp_path / "dl"
    dl_dir.mkdir()
    monkeypatch.setattr(_latex.sys, "platform", "win32")
    monkeypatch.setattr(
        _latex.tempfile, "mkdtemp", lambda prefix="": str(dl_dir)
    )
    downloaded: list[tuple[str, str]] = []
    monkeypatch.setattr(
        _latex.urllib.request,
        "urlretrieve",
        lambda url, path: downloaded.append((url, str(path))),
    )
    ran: list[list[str]] = []
    monkeypatch.setattr(
        _latex.subprocess, "run", lambda cmd, **_k: ran.append(cmd)
    )
    fake_engine = tmp_path / "pdflatex.exe"
    monkeypatch.setattr(_latex, "find_engine", lambda: fake_engine)
    logs: list[str] = []

    result = _latex.install_tinytex(log=logs.append)

    assert result == fake_engine
    assert downloaded and downloaded[0][0].startswith(
        "https://github.com/rstudio/tinytex-releases/"
    )
    assert downloaded[0][0].endswith(f"windows-{_latex._TINYTEX_TAG}.exe")
    assert len(ran) == 1  # the installer, not a tar extraction
    assert any("Downloading" in m for m in logs)
    assert any("Installing" in m for m in logs)


def test_install_tinytex_with_no_log_callback_does_not_raise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dl_dir = tmp_path / "dl"
    dl_dir.mkdir()
    monkeypatch.setattr(_latex.sys, "platform", "win32")
    monkeypatch.setattr(
        _latex.tempfile, "mkdtemp", lambda prefix="": str(dl_dir)
    )
    monkeypatch.setattr(
        _latex.urllib.request, "urlretrieve", lambda url, path: None
    )
    monkeypatch.setattr(_latex.subprocess, "run", lambda cmd, **_k: None)
    engine = tmp_path / "pdflatex.exe"
    monkeypatch.setattr(_latex, "find_engine", lambda: engine)
    assert _latex.install_tinytex() == engine


def test_install_tinytex_extracts_a_tarball_off_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(_latex.sys, "platform", "linux")
    monkeypatch.setattr(
        _latex.tempfile, "mkdtemp", lambda prefix="": str(tmp_path / "dl")
    )
    (tmp_path / "dl").mkdir()
    monkeypatch.setattr(
        _latex.urllib.request, "urlretrieve", lambda url, path: None
    )
    root = tmp_path / "managed" / "TinyTeX"
    monkeypatch.setattr(_latex, "managed_root", lambda: root)

    extracted_to: list[Path] = []

    class _FakeTar:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def extractall(self, path):  # noqa: A003 - matches tarfile's API
            extracted_to.append(Path(path))

    monkeypatch.setattr(_latex.tarfile, "open", lambda _path: _FakeTar())
    fake_engine = root / "bin" / "x86_64-linux" / "pdflatex"
    monkeypatch.setattr(_latex, "find_engine", lambda: fake_engine)

    result = _latex.install_tinytex()

    assert extracted_to == [root.parent]
    assert root.parent.is_dir()  # mkdir(parents=True, exist_ok=True) ran
    assert result == fake_engine


def test_install_tinytex_raises_when_the_download_yields_no_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The counter-example every success test above depends on: a
    download/install that runs to completion but leaves no usable engine
    must be reported as failure, not returned as a bogus path.
    """
    monkeypatch.setattr(_latex.sys, "platform", "win32")
    monkeypatch.setattr(
        _latex.tempfile, "mkdtemp", lambda prefix="": str(tmp_path)
    )
    monkeypatch.setattr(
        _latex.urllib.request, "urlretrieve", lambda url, path: None
    )
    monkeypatch.setattr(_latex.subprocess, "run", lambda cmd, **_k: None)
    monkeypatch.setattr(_latex, "find_engine", lambda: None)

    with pytest.raises(_latex.LatexMissingError):
        _latex.install_tinytex()


def test_install_tinytex_cleans_up_its_temp_dir_even_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dl_dir = tmp_path / "dl"
    dl_dir.mkdir()
    monkeypatch.setattr(_latex.sys, "platform", "win32")
    monkeypatch.setattr(
        _latex.tempfile, "mkdtemp", lambda prefix="": str(dl_dir)
    )

    def _boom(_url, _path):
        raise OSError("network unreachable")

    monkeypatch.setattr(_latex.urllib.request, "urlretrieve", _boom)

    with pytest.raises(OSError, match="network unreachable"):
        _latex.install_tinytex()

    assert not dl_dir.exists()  # the finally: shutil.rmtree ran
