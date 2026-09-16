"""The packaging tools' ``__main__`` trailers, run where coverage sees them.

These four lines looked untestable, and the first answer here was a
``# pragma: no cover`` claiming they need a subprocess coverage hook. That
claim was WRONG, and the technique below is why.

Each tool computes its output paths from ``__file__`` at import, and those
paths resolve inside ``src/`` (or the repo's real ``dist/``). Re-executing the
module with ``runpy`` therefore writes over bundled assets, which is why the
naive approach is unusable.

But ``__file__`` is just a plain global the script's own ``Path(__file__)``
arithmetic reads -- it is independent of the filename baked into the compiled
code object. So: compile the REAL source with its REAL path, so coverage
attributes the executed lines to the file being measured, then exec it with a
``__file__`` pointing under ``tmp_path``. The guard runs, the paths resolve
somewhere harmless, and nothing under ``src/`` is touched.

Every test below proves that last part rather than assuming it: it records a
real bundled artefact's mtime before and asserts it is unchanged after.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def _run_as_main(module, fake_file: Path) -> None:
    """Execute ``module``'s real source as ``__main__`` with a fake path."""
    real = Path(module.__file__)
    code = compile(real.read_text(encoding="utf-8"), str(real), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(fake_file)})


class TestMakeIconRunAsAScript:
    def test_the_trailer_generates_icons_under_the_fake_root(self, tmp_path,
                                                             capsys):
        from epy_papers._core._packaging import make_icon

        real_root = Path(make_icon.__file__).resolve().parent.parent
        real_assets = real_root / "assets_build"
        real_png = real_assets / "epy_papers.png"

        fake_assets = tmp_path / "_packaging" / "assets_build"
        fake_assets.mkdir(parents=True)
        shutil.copyfile(real_png, fake_assets / "epy_papers.png")
        fake_init = tmp_path / "_packaging" / "make_icon" / "__init__.py"

        _run_as_main(make_icon, fake_init)

        out = capsys.readouterr().out
        assert "Generating epy_papers icons" in out
        assert "Done." in out
        assert (fake_assets / "epy_papers.ico").is_file()

    def test_the_real_bundled_icon_was_not_touched(self, tmp_path):
        """The control that makes the test above safe to keep. Without it,
        a regression in the path redirection would quietly start overwriting
        a git-tracked asset on every test run."""
        from epy_papers._core._packaging import make_icon

        real_root = Path(make_icon.__file__).resolve().parent.parent
        real_assets = real_root / "assets_build"
        real_ico = real_assets / "epy_papers.ico"
        # Asserted, not skipped past: the .ico ships inside the package
        # (``_core/_packaging/assets_build/``), so an absent one is a broken
        # checkout and this control -- which exists to prove the redirection
        # never overwrites a git-tracked asset -- would be silently retired.
        assert real_ico.exists(), (
            f"no bundled icon at {real_ico}; the guard below cannot run and "
            f"the test it protects would start writing to a tracked asset")
        before = real_ico.stat().st_mtime_ns

        fake_assets = tmp_path / "_packaging" / "assets_build"
        fake_assets.mkdir(parents=True)
        shutil.copyfile(real_assets / "epy_papers.png",
                        fake_assets / "epy_papers.png")
        _run_as_main(make_icon,
                     tmp_path / "_packaging" / "make_icon" / "__init__.py")

        assert real_ico.stat().st_mtime_ns == before, (
            "the script wrote over the bundled icon"
        )
