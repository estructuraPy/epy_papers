"""Qt widgets and windows for epy_papers.

The editor GUI: the main window (``app.py`` stays at the package root),
tabs, dialogs and the theme system. Nothing here is imported by a bare
``import epy_papers`` — Qt stays confined to this sub-package and to
``app.py`` (see ``tests/test_import_isolation.py``).
"""
