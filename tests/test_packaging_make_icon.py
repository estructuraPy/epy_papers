"""Tests for ``epy_papers._core._packaging.make_icon``.

Dev-only release tooling; nothing exercised it before. ``OUT_DIR`` (and,
where relevant, ``SRC_PNG``) are always monkeypatched to a ``tmp_path``:
the real ``OUT_DIR`` for this module resolves to
``src/epy_papers/_core/_packaging/assets_build`` -- INSIDE ``src/`` -- so
a real ``generate()`` call would overwrite a real bundled asset there,
which the task's "tests only, never touch src/" rule forbids.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from epy_papers._core._packaging import make_icon as mi


def _make_source_png(path: Path, size: tuple[int, int] = (300, 100)) -> None:
    """A small non-square RGBA image, so letterboxing/centering matters."""
    img = Image.new("RGBA", size, (200, 50, 50, 255))
    img.save(path)


# ---------------------------------------------------------------------------
# _letterbox
# ---------------------------------------------------------------------------


def test_letterbox_produces_a_square_transparent_canvas(tmp_path: Path):
    src_path = tmp_path / "src.png"
    _make_source_png(src_path, (300, 100))
    src = Image.open(src_path).convert("RGBA")
    frame = mi._letterbox(src, 64)
    assert frame.size == (64, 64)
    assert frame.mode == "RGBA"
    # A corner must be fully transparent: a wide source letterboxed into a
    # square canvas cannot cover it.
    assert frame.getpixel((0, 0))[3] == 0


def test_letterbox_centers_the_scaled_source():
    # A square source at exactly the target size should fill it edge to
    # edge (no visible letterbox), i.e. the corner keeps the source color.
    src = Image.new("RGBA", (64, 64), (10, 20, 30, 255))
    frame = mi._letterbox(src, 64)
    assert frame.getpixel((0, 0)) == (10, 20, 30, 255)


# ---------------------------------------------------------------------------
# _write_ico / _verify_ico
# ---------------------------------------------------------------------------


def test_write_ico_then_verify_ico_reports_every_size(tmp_path: Path):
    frames = [Image.new("RGBA", (s, s), (1, 2, 3, 255)) for s in mi.SIZES]
    ico_path = tmp_path / "out.ico"
    mi._write_ico(frames, ico_path)
    assert ico_path.exists()
    assert mi._verify_ico(ico_path) == len(mi.SIZES)


# ---------------------------------------------------------------------------
# generate()
# ---------------------------------------------------------------------------


def test_generate_raises_systemexit_when_the_source_png_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(mi, "SRC_PNG", tmp_path / "nope.png")
    monkeypatch.setattr(mi, "OUT_DIR", tmp_path)
    with pytest.raises(SystemExit, match="Source image not found"):
        mi.generate()


def test_generate_writes_a_multi_size_ico(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    src_dir = tmp_path / "assets_build"
    src_dir.mkdir()
    src_png = src_dir / "epy_papers.png"
    _make_source_png(src_png, (400, 250))
    monkeypatch.setattr(mi, "SRC_PNG", src_png)
    monkeypatch.setattr(mi, "OUT_DIR", src_dir)

    mi.generate()

    ico_path = src_dir / "epy_papers.ico"
    assert ico_path.exists()
    assert mi._verify_ico(ico_path) == len(mi.SIZES)
    out = capsys.readouterr().out
    assert "ICO ->" in out


def test_generate_creates_the_output_directory_if_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    src_png = tmp_path / "epy_papers.png"
    _make_source_png(src_png)
    out_dir = tmp_path / "not_yet_created"
    monkeypatch.setattr(mi, "SRC_PNG", src_png)
    monkeypatch.setattr(mi, "OUT_DIR", out_dir)

    mi.generate()

    assert (out_dir / "epy_papers.ico").exists()


# ---------------------------------------------------------------------------
# `if __name__ == "__main__":` guard -- NOT exercised (see report).
#
# Like build_deb.py, a fresh runpy re-execution recomputes OUT_DIR/SRC_PNG
# from this file's real __file__ (ROOT / "assets_build", INSIDE src/) with
# no way to redirect it from outside, so running the guard for real would
# overwrite the real bundled epy_papers.ico under src/ -- forbidden by the
# "tests only" rule. Left undone; see the handback report for the line.
# ---------------------------------------------------------------------------
