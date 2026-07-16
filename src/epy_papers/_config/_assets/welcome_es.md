---
title:
  en: "epy_papers User Manual"
  es: "Manual de usuario epy_papers"
language: es
authors:
  - name: "Ing. Angel Navarro-Mora M.Sc."
    orcid: "0000-0002-0539-7014"
    affiliation: "Instituto Tecnologico de Costa Rica"
    email: "ahnavarro@itcr.ac.cr"
    corresponding: true
abstract:
  en: >
    epy_papers is a Python library and desktop editor for authoring
    journal submission manuscripts from a single Markdown source.
    The author writes once and exports a journal-compliant draft for
    any of the 50 supported journals, driven by per-journal profiles.
    This manual documents the public API, the authoring format, the
    desktop editor, and the export workflow.
  es: >
    epy_papers es una librería Python y editor de escritorio para la
    redacción de manuscritos de revistas científicas a partir de una
    única fuente Markdown. El autor escribe una vez y exporta un
    borrador conforme a la revista para cualquiera de las 50 revistas
    soportadas, guiado por perfiles por revista. Este manual documenta
    la API pública, el formato de autoría, el editor de escritorio y el
    flujo de exportación.
keywords:
  en: [manuscript, journal, submission, Markdown, Python]
  es: [manuscrito, revista, envío, Markdown, Python]
highlights:
  - Escriba el artículo una sola vez en Markdown y exporte un borrador para cualquier revista soportada.
  - 50 perfiles de revistas en ingeniería civil, estructural y multidisciplinaria.
  - Campos bilingües para revistas latinoamericanas y de habla hispana.
  - Vista previa en vivo con renderizado de portada y cuerpo del manuscrito.
  - Panel de validación que detecta errores de longitud, campos faltantes y filtraciones de identidad.
declarations:
  credit: "A.N.M.: conceptualización, metodología, software, redacción."
  competing-interests: "El autor declara no tener intereses en conflicto."
  data-availability: "Datos y código fuente disponibles en el repositorio del proyecto."
  funding: "Este trabajo no recibió financiamiento externo."
  ai-disclosure: "No se utilizaron herramientas de inteligencia artificial generativa en la redacción de este manual."
bibliography: refs.bib
---

# Introducción

epy_papers resuelve un problema práctico que enfrenta todo investigador que
envía artículos a múltiples revistas: el formato. El contenido del manuscrito
— título, resumen, cuerpo, referencias — siempre es el mismo. Lo que cambia
es la maquetación, el estilo de citas, la fuente y los requisitos estructurales
de cada revista.

El enfoque de epy_papers es simple: escribir el artículo completo **una sola vez**
en un formato Markdown estructurado, y luego exportar un **borrador** compatible
con la revista seleccionada. Un borrador es un archivo Word, LaTeX o PDF listo
para enviar, formateado según los requisitos de la revista. El equipo editorial
se encarga de la composición final en dos columnas y el estilo de la editorial;
lo que se entrega es un manuscrito limpio y bien estructurado, no una copia
pixel a pixel del diseño de la revista.

Este documento está escrito en el formato de autoría de epy_papers. Puede leerlo
en la vista previa a la derecha, usar los menús de la barra de herramientas para
insertar elementos y usar este archivo como punto de partida para su propio
artículo.


# Formato de autoría

Un archivo fuente de artículo es un archivo Markdown de texto plano con un
bloque de metadatos YAML al inicio. El bloque de metadatos contiene toda la
información estructurada; el cuerpo contiene el texto del artículo.

## Bloque YAML de metadatos

El bloque de metadatos está delimitado por tres guiones (`---`). Campos requeridos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `title` | cadena bilingüe o simple | Título del artículo |
| `authors` | lista de objetos autor | Lista de autores |
| `abstract` | cadena bilingüe o simple | Resumen del artículo |
| `keywords` | lista bilingüe o simple | Palabras clave |
| `bibliography` | cadena | Ruta al archivo `.bib` de BibTeX |

Campos opcionales:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `language` | cadena | Idioma primario (`en` o `es`) |
| `highlights` | lista de cadenas | 3-5 destacados (máx. 85 caracteres cada uno) |
| `declarations` | objeto | Declaraciones del autor (crédito, financiamiento, etc.) |

### Campos bilingües

Los campos que aceptan contenido bilingüe usan un diccionario con claves de idioma:

```yaml
title:
  en: "Nonlinear Pushover Analysis of RC Frames"
  es: "Análisis pushover no lineal de marcos de concreto"
abstract:
  en: "This paper presents..."
  es: "Este artículo presenta..."
keywords:
  en: [pushover, seismic, reinforced concrete]
  es: [pushover, sísmico, concreto reforzado]
```

Cuando un campo es una cadena simple, se trata como el valor del idioma primario.

### Objetos de autor

Cada entrada en la lista `authors` puede incluir:

```yaml
authors:
  - name: "Ing. Angel Navarro-Mora M.Sc."
    orcid: "0000-0002-0539-7014"
    affiliation: "Instituto Tecnologico de Costa Rica"
    email: "ahnavarro@itcr.ac.cr"
    corresponding: true
```

Todos los campos excepto `name` son opcionales. Establezca `corresponding: true`
para el autor de correspondencia.

### Declaraciones

El bloque `declarations` acepta cualquier par clave-valor. Las claves comunes
reconocidas por los perfiles de revistas incluyen:

- `credit` — declaración de contribución CRediT
- `competing-interests` — declaración de conflicto de intereses
- `data-availability` — declaración de disponibilidad de datos
- `funding` — fuentes de financiamiento
- `ai-disclosure` — declaración de uso de inteligencia artificial

### Destacados (Highlights)

Los destacados son puntos breves que resumen los principales hallazgos. El
sistema de validación verifica:

- Que existan entre 3 y 5 destacados.
- Que cada destacado tenga máximo 85 caracteres.

## Cuerpo del artículo

El cuerpo es Markdown estándar, colocado después del `---` de cierre del bloque
de metadatos. Se admiten todas las características estándar de Markdown:

- `# Título 1`, `## Título 2`, `### Título 3`
- `**negrita**`, `*cursiva*`
- Listas con viñetas y numeradas
- Bloques de código delimitados
- Tablas con barras verticales
- Imágenes con títulos

### Referencias cruzadas y etiquetas

Use etiquetas de estilo Quarto para crear elementos con referencia cruzada.
La etiqueta va entre llaves `{#tipo-N}` inmediatamente después del elemento:

```markdown
![Figura 1: Descripción](figuras/fig1.png){#fig-1 width=80%}

: Tabla 1: Título {#tbl-1}

| A | B |
|---|---|
| 1 | 2 |

$$
\sigma = E \varepsilon
$$ {#eq-1}
```

Cite estos elementos con `@fig-1`, `@tbl-1`, `@eq-1` en el texto.

### Citas bibliográficas

Cite entradas bibliográficas con `[@clave]` o `@clave`. La clave debe existir
en el archivo `.bib` enlazado. El estilo de cita lo determina el perfil de la
revista.

```markdown
El resultado se sigue de la teoría clásica de vigas [@timoshenko_1951].
```


# API pública

epy_papers expone una API Python limpia y mínima. Todos los símbolos públicos
son importables desde el paquete principal.

## Clase Paper

La clase central es `Paper`. Encapsula el fuente del manuscrito y provee
métodos para validación y exportación.

```python
from epy_papers import Paper

# Crear desde texto fuente
paper = Paper(texto_fuente, base_dir=Path("."))

# Crear desde una ruta de archivo
paper = Paper.from_file(Path("manuscrito.md"))
```

**Firma del constructor:**

```python
Paper(source: str, base_dir: Path | str | None = None)
```

- `source`: Texto fuente Markdown completo incluyendo el bloque YAML.
- `base_dir`: Directorio usado para resolver rutas relativas (imágenes,
  bibliografía). Por defecto es el directorio de trabajo actual.

### Paper.from_file

```python
@classmethod
Paper.from_file(path: Path | str) -> Paper
```

Lee el archivo en `path`, establece `base_dir` como el directorio padre del
archivo, y retorna una instancia de `Paper`. Equivalente a:

```python
path = Path(path)
paper = Paper(path.read_text(encoding="utf-8"), base_dir=path.parent)
```

### Paper.validate

```python
paper.validate(journal_id: str) -> ValidationResult
```

Valida el manuscrito contra el perfil de `journal_id`. Retorna un
`ValidationResult` que es iterable (entrega objetos `Warning`) y evalúa a
`True` cuando no hay hallazgos de severidad ERROR.

```python
result = paper.validate("asce_journal_structural_engineering")
if not result.ok:
    for advertencia in result:
        print(advertencia)  # [ERROR] El resumen supera las 250 palabras
```

### Paper.to_draft

```python
paper.to_draft(
    journal_id: str,
    out_path: Path,
    *,
    fmt: str | None = None,
) -> Path
```

Exporta un borrador conforme a la revista en `out_path`. El formato se infiere
de `out_path.suffix` cuando no se especifica `fmt`. Valores admitidos para `fmt`:

- `"docx"` — documento Word con la plantilla de referencia de la revista
- `"tex"` — fuente LaTeX con la clase de documento de la revista
- `"pdf"` — PDF compilado desde LaTeX con `pdflatex`
- `"html"` — vista previa HTML independiente

```python
ruta = paper.to_draft("ieee_access", Path("borrador_ieee.docx"))
```

Lanza `PandocMissingError` cuando Pandoc no está instalado y `OSError` para
fallos de entrada/salida.

### Paper.render_notes

```python
paper.render_notes(journal_id: str, fmt: str) -> list[str]
```

Retorna una lista de notas sobre la exportación sin realizarla. Las notas
describen soluciones alternativas, activos faltantes y brechas específicas
del formato.

```python
notas = paper.render_notes("elsevier_energy", "docx")
for nota in notas:
    print(nota)
```

## Funciones del catálogo

### available_journals

```python
from epy_papers import available_journals

revistas = available_journals()
# Retorna: [("asce_journal_structural_engineering", "ASCE Journal of ..."), ...]
```

Retorna una lista de tuplas `(journal_id, nombre_revista)` para los 50 perfiles
de revistas incluidos, ordenados alfabéticamente por nombre.

### journal_profile

```python
from epy_papers import journal_profile

perfil = journal_profile("ieee_access")
# Retorna: {"name": "IEEE Access", "formats": ["docx", "tex"], ...}
```

Retorna el diccionario de perfil sin procesar para un `journal_id` dado.

### load_journals

```python
from epy_papers import load_journals

todos_los_perfiles = load_journals()
# Retorna: {"asce_journal_structural_engineering": {...}, ...}
```

Carga y retorna el diccionario completo de revistas. Las claves que comienzan
con `_` son eliminadas (son metadatos internos).

### add_journal

```python
from epy_papers import add_journal, available_journals

add_journal(
    "mi-revista",
    {"name": "Mi Revista", "columns": 1, "spacing": "double",
     "line_numbers": "continuous", "font_size_pt": 12,
     "page_size": "letter", "csl": "ieee", "formats": ["docx", "tex"]},
)
```

Agrega o actualiza un perfil de revista en el catálogo de usuario escribible
(`~/.epy_papers/journals.json`, o `$EPY_PAPERS_USER_JOURNALS`), combinado sobre el
catálogo incluido para que sobreviva a las actualizaciones de la app. En el
editor, el botón **+** junto al selector de revista abre un diálogo equivalente
y la nueva revista aparece de inmediato en el selector. `remove_user_journal(id)`
elimina una entrada de usuario.

Al seleccionar una revista, tanto la vista previa como el borrador exportado se
reformatean según las reglas de envío de esa revista — columna simple/doble,
interlineado, tamaño de fuente, tamaño de página y numeración de líneas
continua — para que el borrador no solo se valide sino que quede formateado
listo para enviar.

## API de validación

```python
from epy_papers import Severity, Warning, ValidationResult
```

- `Severity.ERROR` — debe corregirse antes del envío
- `Severity.WARNING` — debe revisarse
- `Severity.INFO` — nota informativa

`Warning(code, severity, message)` es un dataclass inmutable. `str(warning)`
retorna `"[SEVERIDAD] mensaje"`.

`ValidationResult` es iterable, tiene `len()`, y la propiedad `.ok` es `True`
cuando no hay hallazgos de severidad ERROR.

## Clases de excepción

```python
from epy_papers import PandocMissingError
```

Lanzada por `Paper.to_draft` y `Paper.render_notes` cuando Pandoc no se
encuentra en el PATH del sistema o a través de `pypandoc-binary`.


# Editor de escritorio

El editor de escritorio de epy_papers (`python -m epy_papers`) provee un editor
Markdown con múltiples pestañas y una vista previa académica en vivo a la derecha.

![El editor de un vistazo: la fuente Markdown a la izquierda, la vista previa
formateada según la revista en el centro, el selector de revista y los menús
arriba, y el panel de validación a la derecha.](__SHOT_EDITOR__)

## Iniciar el editor

```bash
python -m epy_papers                  # abrir con pestaña de bienvenida
python -m epy_papers manuscrito.md    # abrir un archivo específico
python -m epy_papers --version        # mostrar versión
```

O use el punto de entrada GUI instalado:

```bash
epy_papers manuscrito.md
```

## Menús de la barra de herramientas

La barra de herramientas contiene seis menús desplegables:

| Menú | Contenido |
|------|-----------|
| **File** | Nuevo, Abrir, Guardar, Guardar como, Recargar, Cerrar pestaña, Salir |
| **Text** | Negrita, Cursiva, Insertar enlace |
| **Paper** | Insertar bloques de metadatos y elementos del cuerpo |
| **Export** | Exportar DOCX, LaTeX, PDF, HTML |
| **View** | Tema (si epy_reports está instalado), Idioma |
| **Help** | Manual (Inglés), Manual (Español), Acerca de |

## Selector de revista

La barra de herramientas contiene un menú desplegable **Journal** con los 50
perfiles de revistas incluidos. Seleccione una revista antes de validar o
exportar para aplicar los requisitos y el estilo de cita de esa revista.

La revista seleccionada se persiste entre sesiones.

## Temas

*View ▸ Theme ▸ Browse themes…* abre una galería de identidades visuales. Elija
una para dar estilo a la vista previa y a la exportación HTML; el tema elegido se
recuerda entre sesiones.

![La galería de temas — elija una identidad visual para la vista previa y la
exportación HTML.](__SHOT_THEME_GALLERY__)

## Panel de validación

El panel de validación a la derecha lista todos los problemas del artículo
actual contra la revista seleccionada. Cada elemento tiene color según la
severidad:

- Rojo — ERROR (debe corregirse antes del envío)
- Naranja — WARNING (debe revisarse)
- Azul — INFO (informativo)

Haga clic en el botón **Validate** o presione `Ctrl+Shift+V` para ejecutar la
validación. La validación también se ejecuta automáticamente al cambiar de
pestaña o de revista.

## Menú Paper — Insertar elementos

El menú **Paper** permite insertar todos los elementos estructurados con un clic:

| Acción | Atajo | Inserta |
|--------|-------|---------|
| Insert Title Block | Ctrl+Shift+Y | Plantilla completa de metadatos YAML |
| Insert Authors | — | Bloque YAML de autores |
| Insert Abstract | — | Bloque de resumen bilingüe |
| Insert Keywords | — | Bloque de palabras clave bilingüe |
| Insert Highlights | — | Lista de destacados |
| Insert Declarations | — | Bloque de declaraciones |
| Insert Figure | Ctrl+Shift+F | Figura Markdown con etiqueta |
| Insert Table | Ctrl+Shift+T | Tabla con título |
| Insert Equation | Ctrl+Shift+Q | Ecuación de display con etiqueta |
| Insert Citation | Ctrl+Shift+C | Marcador de cita |
| Insert Code Block | Ctrl+Shift+K | Bloque de código delimitado |

**Design block…** abre un selector de callouts y notas predefinidos — incluidos
los *Disclosure* (asistencia de IA, integridad del documento, confidencialidad,
borrador) — para insertarlos en el manuscrito con un clic:

![El selector de bloques de diseño: elija un callout o disclosure para
insertar.](__SHOT_DESIGN_BLOCK__)


# Formatos de exportación

## DOCX (Word)

La exportación DOCX usa Pandoc con la plantilla DOCX de referencia de la
revista. El documento de referencia establece los estilos (fuentes de títulos,
espaciado de párrafos, formato de citas) para que el archivo resultante esté
listo para enviar.

**Atajo:** `Ctrl+Shift+D`

```python
paper.to_draft("asce_journal_structural_engineering",
               Path("envio.docx"), fmt="docx")
```

## LaTeX

La exportación LaTeX usa la clase de documento de la revista cuando está
incluida. Para revistas sin clase incluida, se usa una plantilla LaTeX genérica.

```python
paper.to_draft("elsevier_energy", Path("borrador.tex"), fmt="tex")
```

El archivo `.tex` resultante se puede compilar con `pdflatex` o enviar a
portales de revistas que acepten fuente LaTeX.

## PDF

La exportación PDF compila el fuente LaTeX con `pdflatex`. Requiere una
instalación de LaTeX funcional además de Pandoc.

```python
paper.to_draft("ieee_access", Path("borrador.pdf"), fmt="pdf")
```

## HTML

La exportación HTML produce una página de vista previa independiente. Es útil
para revisión y compartir antes del envío, pero no es un formato de envío.

```python
paper.to_draft("nature", Path("vista_previa.html"), fmt="html")
```


# Revistas soportadas

epy_papers incluye 50 perfiles de revistas para principales venues de ingeniería
civil, estructural y multidisciplinaria. Algunos ejemplos:

| ID | Nombre de la revista |
|----|---------------------|
| `asce_journal_structural_engineering` | ASCE Journal of Structural Engineering |
| `asce_journal_bridge_engineering` | ASCE Journal of Bridge Engineering |
| `elsevier_energy` | Elsevier Energy |
| `elsevier_engineering_structures` | Engineering Structures (Elsevier) |
| `ieee_access` | IEEE Access |
| `nature` | Nature |
| `springer_bulletin_earthquake_engineering` | Bulletin of Earthquake Engineering |

Use `available_journals()` para obtener la lista completa de forma programática.


# Ejemplo de figura

El flujo de trabajo de epy_papers es simple: el autor escribe una vez en
Markdown, selecciona una revista en el menú desplegable y exporta un borrador
compatible. El perfil de la revista controla la plantilla, el estilo de cita y
las reglas de validación. Una figura se inserta con una imagen etiquetada para
poder referenciarla:

```markdown
![Figura 1: Flujo de exportación de epy_papers](figures/workflow.png){#fig-1 width=80%}
```


# Ejemplo de tabla

La tabla @tbl-1 resume los formatos de exportación soportados.

: Tabla 1: Formatos de exportación y sus características. {#tbl-1}

| Formato | Extensión | Notas |
|---------|-----------|-------|
| DOCX    | .docx     | Documento Word con plantilla de referencia de la revista |
| LaTeX   | .tex      | Clase de la revista si está incluida; plantilla genérica si no |
| PDF     | .pdf      | Compilado desde LaTeX con pdflatex |
| HTML    | .html     | Solo vista previa; no es un formato de envío |


# Ejemplo de ecuación

La equivalencia energía-masa de la relatividad especial (@eq-1) es un ejemplo
clásico de ecuación de display en epy_papers:

$$
E = mc^2
$$ {#eq-1}

Las ecuaciones se numeran automáticamente en las salidas LaTeX y DOCX. En la
vista previa en vivo, las ecuaciones de display se muestran como texto plano;
instale el paquete `markdown` con extensiones matemáticas para una vista previa
más rica.


# Ejemplo de código

El siguiente fragmento muestra el uso completo de la API de epy_papers:

```python
from pathlib import Path
from epy_papers import Paper, available_journals

# Listar todas las revistas soportadas
for jid, jname in available_journals():
    print(f"{jid}: {jname}")

# Cargar un archivo fuente de artículo
paper = Paper.from_file(Path("manuscrito.md"))

# Validar contra una revista
result = paper.validate("asce_journal_structural_engineering")
if result.ok:
    print("No se encontraron errores.")
else:
    for w in result:
        print(w)

# Exportar un borrador DOCX
borrador = paper.to_draft(
    "asce_journal_structural_engineering",
    Path("envio.docx"),
    fmt="docx",
)
print(f"Borrador escrito en: {borrador}")
```


# Ejemplo de cita

Este manual cita el trabajo previo del autor en análisis estructural y evaluación
sísmica [@navarro_mora_2024]. Los detalles completos de la cita están en el
archivo de bibliografía enlazado `refs.bib`.

Para citas múltiples, use una lista separada por punto y coma:
`[@autor_2020; @autor_2021]`.


# Lista de verificación de inicio rápido

1. Abra epy_papers desde la línea de comandos: `python -m epy_papers`
2. Use **Paper > Insert Title Block** para insertar la plantilla de metadatos.
3. Complete su título, autores, resumen, palabras clave y ruta de bibliografía.
4. Escriba el cuerpo del artículo en Markdown usando el menú Paper para insertar
   figuras, tablas, ecuaciones y citas.
5. Seleccione la revista objetivo en el selector de la barra de herramientas.
6. Presione `Ctrl+Shift+V` para validar. Corrija los errores antes de exportar.
7. Use **Export > Export DOCX** (`Ctrl+Shift+D`) para generar el borrador.
8. Envíe el borrador al portal de manuscritos de la revista.
