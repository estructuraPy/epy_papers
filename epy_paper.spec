# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for epy_paper: portable onedir build.

from pathlib import Path as _Path
import shutil as _shutil
import pypandoc
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

# Icon: try to use epy_paper.ico; fall back to epy_reports.ico.
_ICON_PATH = _Path("assets_build/epy_paper.ico")
if not _ICON_PATH.exists():
    _sibling = _Path("../epy_reports/assets_build/epy_reports.ico")
    if _sibling.exists():
        _ICON_PATH.parent.mkdir(exist_ok=True)
        _shutil.copy(_sibling, _ICON_PATH)
_ICON = str(_ICON_PATH) if _ICON_PATH.exists() else None

datas = []
datas += collect_data_files("pypandoc", include_py_files=False)

_ASSETS = _Path("src/epy_paper/assets")
datas += [
    (str(p), str(_Path("epy_paper") / p.relative_to("src/epy_paper").parent))
    for p in _ASSETS.rglob("*")
    if p.is_file() and p.suffix != ".py"
]

_DATA = _Path("src/epy_paper/data")
datas += [
    (str(p), str(_Path("epy_paper") / p.relative_to("src/epy_paper").parent))
    for p in _DATA.rglob("*")
    if p.is_file() and p.suffix != ".py"
]

binaries = []
binaries += collect_dynamic_libs("pypandoc")
_pandoc = pypandoc.get_pandoc_path()
# On Windows, pypandoc-binary ships pandoc.exe; on Linux/macOS it ships
# a plain `pandoc` binary.  Append .exe only on Windows so the spec
# works unmodified on both platforms.
import sys as _sys
if _sys.platform == "win32" and not _pandoc.lower().endswith(".exe"):
    _pandoc += ".exe"
binaries.append((_pandoc, "pypandoc/files"))

hiddenimports = collect_submodules("pypandoc") + [
    "epy_paper.assets",
    "epy_paper.assets.csl",
    "epy_paper.assets.latex",
    "epy_paper.assets.templates",
    "epy_paper.assets.reference_docx",
    "epy_paper.data",
    "PIL",
    "PIL.Image",
]

a = Analysis(
    ["src/epy_paper/__main__.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "test", "unittest",
        "PyQt5", "PyQt6",
        "matplotlib", "pandas", "numpy",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="epy_paper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=_ICON,
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="epy_paper",
)
