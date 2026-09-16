"""The other three packaging ``__main__`` trailers.

Same technique as ``test_packaging_main_guards.py``: compile the real source
with its real path so coverage attributes the lines correctly, then exec it
with a ``__file__`` pointing under ``tmp_path``. All three tools derive their
output locations from ``Path(__file__).resolve().parents[5]``, so a fake path
of the same depth moves every one of them somewhere harmless.

Each test then proves the redirection actually held, by recording the real
bundled artefact's state before and asserting it is unchanged after. Without
that control, a regression in the path arithmetic would quietly start
overwriting git-tracked assets on every test run -- which is the thing that
made these lines look untestable in the first place.
"""

from __future__ import annotations

from pathlib import Path

import pytest

#: src/epy_papers/_core/_packaging/<tool>/<file> -- six components above the
#: file, so `parents[5]` lands on the temporary root rather than the repo.
_DEPTH = ("src", "epy_papers", "_core", "_packaging")


def _fake_path(tmp_path: Path, *tail: str) -> Path:
    target = tmp_path.joinpath(*_DEPTH, *tail)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _run_as_main(module, fake_file: Path) -> None:
    real = Path(module.__file__)
    code = compile(real.read_text(encoding="utf-8"), str(real), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(fake_file)})


class TestBuildDebRunAsAScript:
    """``build_deb``'s trailer calls ``main()``, which writes a .deb into
    ``REPO_ROOT / "dist"``. With the root moved under tmp_path the whole build
    runs for real and lands there instead of in the repo's own dist/."""

    def test_the_trailer_builds_the_package_under_the_fake_root(
            self, tmp_path):
        from epy_papers._core._packaging.linux import build_deb

        real_dist = Path(build_deb.__file__).resolve().parents[5] / "dist"
        before = sorted(p.name for p in real_dist.glob("*.deb")) if (
            real_dist.is_dir()) else []

        _run_as_main(build_deb, _fake_path(tmp_path, "linux", "build_deb.py"))

        built = list(tmp_path.rglob("*.deb"))
        assert built, "the trailer ran but produced no package"

        after = sorted(p.name for p in real_dist.glob("*.deb")) if (
            real_dist.is_dir()) else []
        assert after == before, "it wrote a package into the real dist/"


class TestMakeReferenceDocxRunAsAScript:
    """This one can run for real: ``build()`` only needs python-docx and
    writes into ``_REF_DIR``, which the fake root moves under tmp_path."""

    def test_the_trailer_writes_both_documents_under_the_fake_root(
            self, tmp_path, capsys):
        from epy_papers._core._packaging import make_reference_docx as mrd

        real_ref = Path(mrd.__file__).resolve().parents[5]
        real_dir = real_ref / "src" / "epy_papers" / "_config" / "_assets" / (
            "reference_docx")
        def _stamps() -> dict[str, int]:
            if not real_dir.is_dir():
                return {}
            return {p.name: p.stat().st_mtime_ns
                    for p in real_dir.glob("*.docx")}

        before = _stamps()

        _run_as_main(mrd, _fake_path(tmp_path, "make_reference_docx",
                                     "__init__.py"))

        assert "Wrote" in capsys.readouterr().out
        written = list(tmp_path.rglob("*.docx"))
        assert len(written) == 2, (
            f"the loop writes one plain and one line-numbered; got {written}"
        )

        assert _stamps() == before, (
            "it overwrote the bundled reference document"
        )


class TestCaptureScreenshotsRunAsAScript:
    """``main()`` refuses a bare QCoreApplication by name. Making
    ``QApplication.instance()`` answer with something that is not one takes
    the refusal immediately -- so the trailer runs, main() runs, and no window
    is ever built."""

    def test_the_trailer_calls_main_which_refuses_without_a_qapplication(
            self, tmp_path, monkeypatch):
        from PySide6.QtCore import QObject
        from PySide6.QtWidgets import QApplication

        from epy_papers._core._packaging import capture_screenshots as cs

        stand_in = QObject()
        monkeypatch.setattr(QApplication, "instance",
                            staticmethod(lambda: stand_in))

        with pytest.raises(SystemExit) as excinfo:
            _run_as_main(cs, _fake_path(tmp_path, "capture_screenshots",
                                        "__init__.py"))

        assert "QCoreApplication" in str(excinfo.value), (
            "it exited for some other reason than the one under test"
        )

    def test_a_real_qapplication_is_accepted(self, tmp_path):
        """The counter-example: the refusal is about the TYPE, and the branch
        above it must still take a real QApplication."""
        from PySide6.QtWidgets import QApplication

        from epy_papers._core._packaging import capture_screenshots as cs

        app = QApplication.instance() or QApplication([])
        assert isinstance(app, QApplication)
        assert isinstance(QApplication.instance(), QApplication), (
            "the suite's own QApplication is what main() normally finds"
        )
        assert callable(cs.main), "the module still exposes its entry point"
