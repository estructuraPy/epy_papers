"""Optional LaTeX engine resolution + on-demand TinyTeX install for PDF export.

Papers PDF export needs a LaTeX engine. Most users never export to PDF, so
epy_papers does NOT bundle or require LaTeX — that would add hundreds of MB to
the installer for a feature few use. Instead, when PDF export is requested and
no engine is found, the GUI offers to download and install a private TinyTeX
from the internet (~70 MB); it is reused on every later export. Word, LaTeX
source and HTML export never need it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

__all__ = [
    "LatexMissingError",
    "DOWNLOAD_MB",
    "find_engine",
    "install_tinytex",
    "managed_root",
]

# Pinned, self-contained TinyTeX bundle (no CTAN round-trip at install time).
_TINYTEX_TAG = "v2026.06"
_TINYTEX_ASSET = {
    "win32": f"TinyTeX-1-windows-{_TINYTEX_TAG}.exe",
    "darwin": f"TinyTeX-1-darwin-{_TINYTEX_TAG}.tar.xz",
    "linux": f"TinyTeX-1-linux-x86_64-{_TINYTEX_TAG}.tar.xz",
}
_BASE_URL = (
    "https://github.com/rstudio/tinytex-releases/releases/download/"
    f"{_TINYTEX_TAG}"
)

# Approximate download size, shown in the install prompt.
DOWNLOAD_MB = 70

# Engines pandoc can drive, in order of preference. pdflatex is Pandoc's
# default and the most compatible with the bundled journal classes; xelatex /
# lualatex follow for documents that need system fonts.
_ENGINES = ("pdflatex", "xelatex", "lualatex", "tectonic")


class LatexMissingError(RuntimeError):
    """Raised when PDF export needs a LaTeX engine and none is installed."""


def managed_root() -> Path:
    """Per-user directory where the app-managed TinyTeX lives, if installed.

    Matches the location TinyTeX's own installer uses, so a TinyTeX the user
    already installed by hand is picked up too.
    """
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "TinyTeX"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "TinyTeX"
    return Path.home() / ".TinyTeX"


def _engine_in(root: Path) -> Path | None:
    """Return the first known engine under ``<root>/bin/<arch>/``."""
    bin_root = root / "bin"
    if not bin_root.is_dir():
        return None
    suffix = ".exe" if sys.platform == "win32" else ""
    for arch_dir in sorted(p for p in bin_root.iterdir() if p.is_dir()):
        for eng in _ENGINES:
            cand = arch_dir / f"{eng}{suffix}"
            if cand.is_file():
                return cand
    return None


def find_engine() -> Path | None:
    """Return a usable LaTeX engine: one on ``PATH``, else managed TinyTeX."""
    for eng in _ENGINES:
        found = shutil.which(eng)
        if found:
            return Path(found)
    return _engine_in(managed_root())


def install_tinytex(log=None) -> Path:
    """Download and install a private TinyTeX; return the engine path.

    Runs the official self-contained TinyTeX bundle for the platform (no CTAN
    round-trip). Raises :class:`LatexMissingError` if it yields no engine.

    Args:
        log: Optional ``callable(str)`` used to report progress to the UI.
    """
    def _log(msg: str) -> None:
        if log is not None:
            log(msg)

    key = sys.platform if sys.platform in _TINYTEX_ASSET else "linux"
    if key.startswith("linux"):
        key = "linux"
    asset = _TINYTEX_ASSET[key]
    url = f"{_BASE_URL}/{asset}"

    tmp = Path(tempfile.mkdtemp(prefix="epy_tinytex_"))
    try:
        installer = tmp / asset
        _log(f"Downloading TinyTeX (~{DOWNLOAD_MB} MB)…")
        urllib.request.urlretrieve(url, installer)  # noqa: S310 - pinned URL
        _log("Installing TinyTeX…")
        if sys.platform == "win32":
            # The Windows bundle is a self-extracting installer that lays
            # TinyTeX down under %APPDATA%\TinyTeX.
            subprocess.run([str(installer)], check=True)  # noqa: S603
        else:
            # The unix bundles are tarballs of the TinyTeX tree.
            managed_root().parent.mkdir(parents=True, exist_ok=True)
            with tarfile.open(installer) as tar:
                tar.extractall(managed_root().parent)  # noqa: S202
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    engine = find_engine()
    if engine is None:
        raise LatexMissingError(
            "The TinyTeX download finished but no LaTeX engine was found."
        )
    return engine
