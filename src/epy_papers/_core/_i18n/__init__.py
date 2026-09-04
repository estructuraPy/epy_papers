"""Lightweight in-app internationalization (English / Spanish).

English is the source language and the lookup key; Spanish strings live in
``_ES``. Missing keys fall back to the English text. Widgets register a
relabel callback via :func:`on_language_changed`, so switching the language
re-applies every callback and the running UI updates live, with no restart.

The product name ``epy_papers``, code identifiers, keyboard shortcuts and
journal/format names stay in English.
"""

from __future__ import annotations

from collections.abc import Callable

#: Supported languages: code -> endonym shown in the Language menu.
LANGUAGES: dict[str, str] = {"en": "English", "es": "Español"}

_lang = "en"
_observers: list[Callable[[], None]] = []

# English -> Spanish. Neutral / professional Spanish (no regional voseo).
# Keys MUST match the source strings exactly (including trailing "..."
# vs "…" ellipsis and Qt "&" menu accelerators).
_ES: dict[str, str] = {
    # --- top-level menus (with & accelerator) ---
    "&File": "&Archivo",
    "&Text": "&Texto",
    "&Paper": "&Artículo",
    "E&xport": "E&xportar",
    "&View": "&Ver",
    "&Help": "&Ayuda",
    # --- toolbar dropdown buttons (no accelerator) ---
    "File": "Archivo",
    "Text": "Texto",
    "Paper": "Artículo",
    "Export": "Exportar",
    "View": "Ver",
    "Help": "Ayuda",
    "Language": "Idioma",
    # --- submenu titles ---
    "Theme": "Tema",
    "Autosave": "Guardado automático",
    "Autosaved: {path}": "Guardado automático: {path}",
    "Disclosure": "Declaración",
    # --- File menu ---
    "New": "Nuevo",
    "Open...": "Abrir...",
    "Save": "Guardar",
    "Save As...": "Guardar como...",
    "Reload": "Recargar",
    "Close Tab": "Cerrar pestaña",
    "Quit": "Salir",
    # --- Text menu ---
    "Bold": "Negrita",
    "Italic": "Cursiva",
    "Insert Link...": "Insertar enlace...",
    # --- Paper menu ---
    "Insert Title Block": "Insertar bloque de título",
    "Insert Authors": "Insertar autores",
    "Insert Abstract": "Insertar resumen",
    "Insert Keywords": "Insertar palabras clave",
    "Insert Highlights": "Insertar destacados",
    "Insert Declarations": "Insertar declaraciones",
    "Insert Figure": "Insertar figura",
    "Insert Table": "Insertar tabla",
    "Insert Equation": "Insertar ecuación",
    "Insert Citation": "Insertar cita",
    "Insert Code Block": "Insertar bloque de código",
    "Design block…": "Bloque de diseño…",
    "Add Journal...": "Agregar revista...",
    # --- Export menu ---
    "Export DOCX...": "Exportar DOCX...",
    "Export LaTeX...": "Exportar LaTeX...",
    "Export PDF...": "Exportar PDF...",
    "Export HTML...": "Exportar HTML...",
    # --- View menu ---
    "Page View": "Vista de página",
    "Browse themes…": "Explorar temas…",
    # --- Help menu ---
    "User Manual (English)": "Manual de usuario (Inglés)",
    "User Manual (Spanish)": "Manual de usuario (Español)",
    "About epy_papers...": "Acerca de epy_papers...",
    # --- Journal selector / toolbar ---
    "Journal:": "Revista:",
    "Validate": "Validar",
    # --- Validation dock ---
    "Validation": "Validación",
    "No issues found": "No se encontraron problemas",
    # --- Severity labels ---
    "ERROR": "ERROR",
    "WARNING": "ADVERTENCIA",
    "INFO": "INFO",
    # --- Dialog labels ---
    "About epy_papers": "Acerca de epy_papers",
    "Design block": "Bloque de diseño",
    "Choose a design block:": "Elija un bloque de diseño:",
    "Themes": "Temas",
    "Choose a theme:": "Elija un tema:",
    "Close": "Cerrar",
    "OK": "Aceptar",
    "Cancel": "Cancelar",
    # --- About dialog ---
    "Paper authoring editor with live preview":
        "Editor de artículos científicos con vista previa en vivo",
    # --- editor placeholder ---
    "Type paper Markdown here. Preview updates on the right.": (
        "Escriba aquí el Markdown del artículo. "
        "La vista previa se actualiza a la derecha."
    ),
    # --- status messages ---
    "Exported: {name}": "Exportado: {name}",
    "An export is already running.": "Ya hay una exportación en curso.",
    # --- message boxes ---
    "Install LaTeX for PDF export": "Instalar LaTeX para exportar a PDF",
    "Unsaved changes": "Cambios sin guardar",
    "TinyTeX install failed": "Error al instalar TinyTeX",
    "Export HTML failed": "Error al exportar HTML",
    "Discard unsaved changes and reload from disk?":
        "¿Descartar los cambios sin guardar y recargar desde el disco?",
}


def tr(text: str) -> str:
    """Return ``text`` in the current language (English is the identity)."""
    if _lang == "en":
        return text
    return _ES.get(text, text)


def set_language(lang: str) -> None:
    """Switch the active language and relabel every registered widget."""
    global _lang
    if lang not in LANGUAGES or lang == _lang:
        return
    _lang = lang
    for callback in list(_observers):
        callback()


def current_language() -> str:
    """Return the active language code."""
    return _lang


def on_language_changed(callback: Callable[[], None]) -> None:
    """Register a relabel callback fired on every language change."""
    _observers.append(callback)


def translate_widget(root) -> None:
    """Translate the window title and labelled children of a widget tree.

    Reads the current language at call time, so it is meant to be called
    at the end of a modal dialog's ``__init__``. Only strings present in
    ``_ES`` change; user data and untranslated labels pass through unchanged.
    """
    if _lang == "en":
        return
    from PySide6.QtWidgets import (
        QAbstractButton,
        QGroupBox,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
    )

    title = root.windowTitle()
    if title:
        root.setWindowTitle(tr(title))
    for label in root.findChildren(QLabel):
        text = label.text()
        if text:
            label.setText(tr(text))
    for button in root.findChildren(QAbstractButton):
        text = button.text()
        if text:
            button.setText(tr(text))
    for box in root.findChildren(QGroupBox):
        text = box.title()
        if text:
            box.setTitle(tr(text))
    for field in root.findChildren(QLineEdit):
        placeholder = field.placeholderText()
        if placeholder:
            field.setPlaceholderText(tr(placeholder))
    for area in root.findChildren(QPlainTextEdit):
        placeholder = area.placeholderText()
        if placeholder:
            area.setPlaceholderText(tr(placeholder))
