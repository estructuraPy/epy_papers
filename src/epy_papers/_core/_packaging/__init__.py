"""Build/release tooling for epy_papers — NOT shipped in the wheel.

Contents:
    installer/    — Windows Inno Setup script + Linux .deb builder.
    assets_build/ — source image + generated .ico for the app icon.
    tools/        — dev-time scripts that regenerate bundled assets
        (screenshots, the reference DOCX).

Invoked directly (``python src/epy_papers/_core/_packaging/...``), never
imported at runtime — excluded from the wheel via
``[tool.hatch.build.targets.wheel] exclude`` in ``pyproject.toml``.
"""
