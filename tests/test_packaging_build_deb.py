"""Tests for ``epy_papers._core._packaging.linux.build_deb``.

Dev-only release tooling excluded from the wheel (see the module's own
docstring); nothing here exercised it before. ``main()`` is tested with
``OUT_DIR`` monkeypatched to a ``tmp_path`` so a real run never writes a
build artifact into this repository's own ``dist/``.
"""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from epy_papers._core._packaging.linux import build_deb as bd

# ---------------------------------------------------------------------------
# _read_pyproject_version
# ---------------------------------------------------------------------------


def test_read_pyproject_version_matches_the_real_project_version():
    """CONTROL: the value already bound at import time (``PKG_VERSION``)
    came from this exact function reading the real ``pyproject.toml``.
    """
    import epy_papers

    assert epy_papers.__version__ == bd.PKG_VERSION
    assert bd._read_pyproject_version() == epy_papers.__version__


def test_read_pyproject_version_falls_back_to_init_when_pyproject_unreadable(
    monkeypatch: pytest.MonkeyPatch,
):
    real_read_text = Path.read_text

    def _flaky_read_text(self, *a, **k):
        if self.name == "pyproject.toml":
            raise OSError("pretend pyproject.toml is unreadable")
        return real_read_text(self, *a, **k)

    monkeypatch.setattr(Path, "read_text", _flaky_read_text)
    import epy_papers

    assert bd._read_pyproject_version() == epy_papers.__version__


def test_read_pyproject_version_falls_back_when_no_version_line_matches(
    monkeypatch: pytest.MonkeyPatch,
):
    real_read_text = Path.read_text

    def _no_version_line(self, *a, **k):
        if self.name == "pyproject.toml":
            return "[project]\nname = 'x'\n"  # no `version = "..."` line
        return real_read_text(self, *a, **k)

    monkeypatch.setattr(Path, "read_text", _no_version_line)
    import epy_papers

    assert bd._read_pyproject_version() == epy_papers.__version__


def test_read_pyproject_version_is_0_0_0_when_everything_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    def _always_fails(self, *a, **k):
        raise OSError("nothing is readable")

    monkeypatch.setattr(Path, "read_text", _always_fails)
    assert bd._read_pyproject_version() == "0.0.0"


# ---------------------------------------------------------------------------
# ar(5) helpers
# ---------------------------------------------------------------------------


def test_ar_header_is_exactly_60_bytes_and_ends_with_the_magic():
    header = bd._ar_header("control.tar.gz", 1234)
    assert len(header) == 60
    assert header.endswith(b"\x60\n")
    assert header.startswith(b"control.tar.gz")


def test_ar_header_encodes_size_and_mode():
    header = bd._ar_header("x", 42, mode=0o100755)
    text = header.decode("ascii")
    assert "42" in text
    assert "100755" in text


def test_ar_pad_leaves_even_length_data_untouched():
    assert bd._ar_pad(b"1234") == b"1234"


def test_ar_pad_appends_a_newline_to_odd_length_data():
    assert bd._ar_pad(b"123") == b"123\n"


def test_write_ar_round_trips_through_verify_deb(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    path = tmp_path / "test.deb"
    bd._write_ar(
        path,
        [
            ("debian-binary", b"2.0\n"),
            ("control.tar.gz", b"fake control data"),
            ("data.tar.gz", b"fake data payload, a bit longer"),
        ],
    )
    raw = path.read_bytes()
    assert raw.startswith(bd.AR_MAGIC)

    bd._verify_deb(path)
    out = capsys.readouterr().out
    assert "debian-binary" in out
    assert "control.tar.gz" in out
    assert "data.tar.gz" in out
    assert "structure OK" in out


def test_verify_deb_rejects_a_bad_magic(tmp_path: Path):
    path = tmp_path / "bad.deb"
    path.write_bytes(b"NOT-AN-AR-FILE-AT-ALL...")
    with pytest.raises(ValueError, match="Bad ar magic"):
        bd._verify_deb(path)


def test_verify_deb_rejects_a_truncated_header(tmp_path: Path):
    path = tmp_path / "truncated.deb"
    # Valid magic, then a header cut short (< 60 bytes) with nothing after.
    path.write_bytes(bd.AR_MAGIC + b"debian-binary   0" * 3)
    with pytest.raises(ValueError, match="Truncated ar header"):
        bd._verify_deb(path)


# ---------------------------------------------------------------------------
# tar helpers
# ---------------------------------------------------------------------------


def test_tar_add_data_writes_the_exact_bytes():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        bd._tar_add_data(tf, "./hello.txt", b"hello world", mode=0o644)
    buf.seek(0)
    with tarfile.open(fileobj=buf, mode="r:gz") as tf:
        member = tf.getmember("./hello.txt")
        assert member.mode == 0o644
        assert tf.extractfile(member).read() == b"hello world"


def test_tar_add_dir_creates_a_directory_entry():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        bd._tar_add_dir(tf, "./usr/bin")
    buf.seek(0)
    with tarfile.open(fileobj=buf, mode="r:gz") as tf:
        member = tf.getmember("./usr/bin")
        assert member.isdir()


def test_tar_add_tree_recurses_and_skips_pycache_and_packaging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    src = tmp_path / "srcpkg"
    (src / "sub").mkdir(parents=True)
    (src / "sub" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    (src / "__pycache__").mkdir()
    (src / "__pycache__" / "mod.cpython-310.pyc").write_bytes(b"\x00")
    # Simulate this very _packaging directory, which must never ship.
    packaging_like = src / "_core" / "_packaging"
    packaging_like.mkdir(parents=True)
    (packaging_like / "build_tool.py").write_text("y = 2\n", encoding="utf-8")

    monkeypatch.setattr(bd, "PKG_ROOT", packaging_like)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        bd._tar_add_tree(tf, src, "./dst")
    buf.seek(0)
    with tarfile.open(fileobj=buf, mode="r:gz") as tf:
        names = tf.getnames()

    assert "./dst/sub/mod.py" in names
    assert not any("__pycache__" in n for n in names)
    assert not any("_packaging" in n for n in names)


# ---------------------------------------------------------------------------
# _build_control_tar
# ---------------------------------------------------------------------------


def test_build_control_tar_contains_the_maintainer_scripts():
    data = bd._build_control_tar()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        names = tf.getnames()
        assert set(names) == {
            "./control",
            "./postinst",
            "./prerm",
            "./postrm",
        }
        control = tf.extractfile("./control").read().decode()
        assert f"Package: {bd.PKG_NAME}" in control
        assert bd.PKG_VERSION in control
        postinst = tf.extractfile("./postinst").read().decode()
        assert "python3 -m venv" in postinst


# ---------------------------------------------------------------------------
# _build_data_tar
# ---------------------------------------------------------------------------


def test_build_data_tar_includes_the_icon_when_present(tmp_path: Path):
    png = tmp_path / "epy_papers.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    data = bd._build_data_tar(png)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        names = tf.getnames()
        assert (
            "./usr/share/icons/hicolor/256x256/apps/epy_papers.png" in names
        )
        assert f"./usr/bin/{bd.PKG_NAME}" in names
        launcher = tf.extractfile(f"./usr/bin/{bd.PKG_NAME}").read().decode()
        assert "epy_papers.app import main" in launcher
        # the real epy_papers package tree is bundled
        assert any(
            n.startswith(f"./usr/lib/{bd.PKG_NAME}/epy_papers/")
            for n in names
        )
        assert any(
            n.startswith(f"./usr/lib/{bd.PKG_NAME}/pypandoc/") for n in names
        )


def test_build_data_tar_warns_and_continues_without_an_icon(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    missing_png = tmp_path / "does_not_exist.png"
    data = bd._build_data_tar(missing_png)
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "not found" in err
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        names = tf.getnames()
        # Only the app-icon slot is skipped; the bundled epy_papers
        # package (which legitimately carries its own branding PNG under
        # _config/_assets/) still ships regardless.
        assert (
            "./usr/share/icons/hicolor/256x256/apps/epy_papers.png"
            not in names
        )


def test_build_data_tar_excludes_stray_binary_extensions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The real pypandoc install on this machine has no bare ``.so``/
    ``.bin`` files to trigger this guard (only the ``pandoc``-stem check
    above ever fires for real) -- a fake pypandoc tree with one proves
    the second, otherwise-dead-looking check is real and independent.
    """
    fake_pypandoc = tmp_path / "pypandoc"
    fake_pypandoc.mkdir()
    (fake_pypandoc / "__init__.py").write_text("", encoding="utf-8")
    (fake_pypandoc / "helper.so").write_bytes(b"\x00")
    monkeypatch.setattr(bd, "PYPANDOC_SRC", fake_pypandoc)

    data = bd._build_data_tar(Path("/does/not/exist.png"))
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        names = tf.getnames()
    assert not any(n.endswith("helper.so") for n in names)
    assert any(n.endswith("__init__.py") for n in names)  # sibling ships


def test_build_data_tar_excludes_pandoc_binaries():
    """The apt ``pandoc`` dependency provides the binary; bundling
    pypandoc's own copy would ship two, architecture-mismatched pandocs.
    """
    data = bd._build_data_tar(Path("/does/not/exist.png"))
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        names = tf.getnames()
    assert not any(
        n.endswith((".exe", ".bin", ".so")) for n in names
    )
    assert not any(Path(n).stem == "pandoc" for n in names)


# ---------------------------------------------------------------------------
# main() -- full orchestration, redirected away from the real dist/
# ---------------------------------------------------------------------------


def test_main_builds_a_real_deb_into_a_temp_out_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setattr(bd, "OUT_DIR", tmp_path)
    bd.main()
    out = capsys.readouterr().out
    assert "Building control.tar.gz" in out
    assert "Building data.tar.gz" in out
    assert "structure OK" in out
    produced = list(tmp_path.glob("*.deb"))
    assert len(produced) == 1
    assert (
        produced[0].name == f"{bd.PKG_NAME}_{bd.PKG_VERSION}_{bd.PKG_ARCH}.deb"
    )
    assert produced[0].stat().st_size > 1000


# ---------------------------------------------------------------------------
# `if __name__ == "__main__":` guard -- NOT exercised (see report)
#
# runpy.run_module(..., run_name="__main__") re-executes the module fresh,
# recomputing OUT_DIR = REPO_ROOT / "dist" from this file's real __file__
# with no way to redirect it (main() takes no arguments and there is no
# env-var override) -- unlike app.py's guard, running this one for real
# would write an actual .deb into THIS repository's real dist/ as a side
# effect of the test suite. Left undone rather than doing that; see the
# handback report for the exact line.
# ---------------------------------------------------------------------------
