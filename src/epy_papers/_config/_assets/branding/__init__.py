"""Bundled branding images for epy_papers.

Contains:
    epy_papers.png    — application logo / window icon (cobra over "P")
    estructurapy.png  — estructuraPy org logo
    imagotipo_anm.png — ANM Ingenieria logotype

Use ``importlib.resources.files`` to read these images so they work both
from a source install and from a frozen PyInstaller build (zip archive)::

    from importlib.resources import files
    pkg = files("epy_papers._config._assets.branding")
    data = (pkg / "epy_papers.png").read_bytes()
"""
