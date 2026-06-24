---
title:
  en: "The Inclined Stays of the Brooklyn Bridge: Roebling's Hybrid Answer to the Wind"
  es: "Los tirantes inclinados del Puente de Brooklyn: la respuesta híbrida de Roebling al viento"
language: es
authors:
  - name: Angel Navarro-Mora
    affiliation: ANM Ingeniería, San José, Costa Rica
    email: ahnavarro@anmingenieria.com
    orcid: 0000-0002-0539-7014
    corresponding: true
abstract:
  en: "Completed in 1883, the Brooklyn Bridge is not a pure suspension bridge.
    John A. Roebling coupled the main suspension cables with a fan of inclined
    stays running from the towers to the deck, producing an early hybrid
    cable-stayed/suspension system. This note revisits the engineering history
    of that decision: Roebling distrusted the flexibility of slender suspension
    decks in wind and added the stays to stiffen the structure and provide
    redundancy, decades before aeroelastic instability became infamous. We
    summarize the rationale and contrast, with a simple stiffness argument, the
    wind response of the pure-suspension and the stayed configurations."
  es: "Terminado en 1883, el Puente de Brooklyn no es un puente colgante puro.
    John A. Roebling acopló los cables principales con un abanico de tirantes
    inclinados desde las torres al tablero, dando lugar a un sistema híbrido
    atirantado/colgante temprano. Esta nota revisa la historia de ingeniería de
    esa decisión: Roebling desconfiaba de la flexibilidad de los tableros
    colgantes esbeltos ante el viento y añadió los tirantes para rigidizar la
    estructura y dar redundancia, décadas antes de que la inestabilidad
    aeroelástica se volviera tristemente célebre. Resumimos la motivación y
    contrastamos, con un argumento simple de rigidez, la respuesta al viento de
    la configuración puramente colgante y la atirantada."
keywords:
  en: [suspension bridge, cable-stayed, wind, aeroelastic stiffness, Roebling]
  es: [puente colgante, atirantado, viento, rigidez aeroelástica, Roebling]
highlights:
  - El Puente de Brooklyn combina un sistema colgante con tirantes inclinados.
  - Roebling añadió los tirantes principalmente para rigidizar el tablero ante el viento.
  - El sistema híbrido anticipó las preocupaciones aeroelásticas con décadas de antelación.
declarations:
  competing-interests: "El autor declara que no existen intereses en conflicto."
  ai-disclosure: "El formateo y el ensamblado del borrador se realizaron con epy_papers."
bibliography: refs.bib
---

::: {.disclosure}
Este manuscrito es un ejemplo ilustrativo preparado con asistencia de IA; revise su contenido antes de utilizarlo.
:::

**Sobre este ejemplo** — un ejemplo de *epy_papers*, parte de la suite de
documentos ePy (código abierto). Fuente y ejemplos hermanos en GitHub:
[epy_papers · Puente de Brooklyn](https://github.com/estructuraPy/epy_papers/tree/main/examples/brooklyn_bridge),
[epy_slides · Empire State](https://github.com/estructuraPy/epy_slides/tree/main/examples/empire_state_building),
[epy_reports · Newmark](https://github.com/estructuraPy/epy_reports/tree/main/examples/newmark).

# Introducción

El Puente de Brooklyn, inaugurado en 1883, es recordado como un triunfo de
la tipología colgante. Sin embargo, una mirada atenta a su tablero revela un
segundo sistema de cables, distinto del primero: un abanico de tirantes rectos
e inclinados anclados en las torres y fijados al tablero, superpuesto a las
clásicas péndolas verticales que cuelgan de los cables principales parabólicos.
La estructura es, por tanto, un sistema híbrido — atirantado *y* colgante a la
vez [@mccullough1972; @billington1983].

Esta dualidad no es ornamental. Es el registro físico de una filosofía de diseño
en la que la rigidez, y no la esbeltez, constituía el criterio rector. Allí donde
el puente colgante del siglo XIX aspiraba a la ligereza, Roebling cedió
deliberadamente parte de esa ligereza a cambio de la rigidez en el plano del
tablero que consideraba exigida por el viento. La presente nota tiene tres
objetivos. Primero, situar la decisión en su contexto histórico, recordando por
qué un especialista en puentes colgantes de la generación de Roebling desconfiaba
de un tablero colgante esbelto. Segundo, describir las dos trayectorias de cargas
coexistentes y explicar, en términos mecánicos claros, por qué un tirante recto
se comporta de manera tan diferente a una péndola colgante. Tercero, cuantificar
esa intuición de forma ilustrativa mediante un argumento simple de rigidez, que
contrasta las configuraciones puramente colgante y atirantada y muestra cómo la
incorporación de una restricción casi axial desplaza la frecuencia fundamental del
tablero hacia valores más altos. A lo largo del texto, el énfasis recae en el
razonamiento de ingeniería y no en ninguna respuesta medida de la estructura
existente.

# Contexto histórico: un puente construido contra el viento

La decisión fue deliberada. John A. Roebling había dedicado su carrera a los
puentes colgantes y era plenamente consciente de su punto débil: un tablero
esbelto y flexible es vulnerable al viento. Los vanos colgantes del siglo XIX
habían colapsado durante tormentas, y Roebling diseñó el Puente de Brooklyn para
que fuera rígido en primer lugar, y elegante en segundo. Dimensionó la estructura
con un amplio margen y declaró que los tirantes inclinados por sí solos podrían
sostener el tablero aunque se perdieran los cables principales [@roebling1867].
Los tirantes eran, en sus propias palabras, una garantía de rigidez y seguridad —
un sistema redundante cuyo propósito era resistir el viento y amortiguar el
movimiento del tablero.

Ese margen respondía a la experiencia vivida, no a una cautela abstracta. La
generación de puentes colgantes de gran luz que precedió al cruce del East River
enseñó a los ingenieros una dura lección: un tablero suspendido de cables y
carente de arriostramiento puede absorber energía de un viento constante o en
ráfagas y moverse de maneras que crecen en lugar de disiparse. El propio informe
de Roebling a la New York Bridge Company planteó la cuestión en términos de
permanencia, insistiendo en que el cruce debía construirse para sobrevivir a las
dudas de sus críticos y a los peores temporales del East River [@roebling1867].
Billington, escribiendo un siglo después, interpretó el puente en la misma clave
— como una obra en la que el arte estructural y la seguridad estructural nunca
estuvieron separados, y en la que los tirantes visibles declaran a la vista la
intención del ingeniero [@billington1983].

Esto fue una visión anticipada. Pasaría más de medio siglo antes de que el
colapso en 1940 del Puente de Tacoma Narrows convirtiera la inestabilidad
aeroelástica en materia de libro de texto [@billington1983]. Roebling llegó a la
misma conclusión práctica — *rigidizar el tablero* — a partir de la experiencia
y no de una teoría del flameo. La distinción es relevante: no habría podido
escribir las ecuaciones modernas de la inestabilidad inducida por el viento, y
sin embargo su diseño contiene su remedio central. Un tablero con rigidez a
flexión y a torsión, cuyas frecuencias naturales se sitúan muy por encima del
rango que un viento en ráfagas excita con mayor eficacia, tiene muchas menos
probabilidades de entrar en las grandes oscilaciones autoalimentadas que
destruyeron Tacoma Narrows. Los tirantes inclinados son la expresión más directa
de ese remedio.

# El sistema híbrido

Dos trayectorias de cargas comparten el tablero:

- el **sistema colgante**: las péndolas verticales transfieren la carga del
  tablero a los cables principales parabólicos y de ahí a las torres y
  anclajes;
- el **sistema de tirantes**: los tirantes inclinados llevan la carga del
  tablero directamente a las torres siguiendo líneas casi rectas.

Un tirante recto es mucho más rígido que una péndola colgante del mismo material,
porque resiste la carga con un cambio de geometría mínimo. Una péndola colgante,
en cambio, comparte la carga con el cable principal a través de un sistema cuya
forma debe cambiar antes de poder soportar más — la parábola se profundiza, el
tablero desciende, y la geometría realiza parte del trabajo que en otro caso
correspondería a la rigidez. El tirante cortocircuita ese mecanismo: anclado en
la parte alta de la torre y articulado al tablero, se opone a una carga vertical
o fluctuante casi en su totalidad mediante su alargamiento axial, que en un
elemento de acero tensado es muy pequeño. La incorporación de los tirantes eleva,
por tanto, la rigidez efectiva del tablero y sus frecuencias naturales, alejando
la estructura del régimen de bajas frecuencias, sensible al viento, propio de un
tablero puramente colgante.

Igualmente importante es lo que la segunda trayectoria de cargas aporta a la
seguridad. Al existir dos sistemas independientes que soportan el mismo tablero,
la pérdida o degradación de uno no deja el tablero sin sustento. Roebling
reivindicó exactamente esta redundancia para los tirantes, afirmando que podían
sostener el tablero incluso en ausencia de los cables principales [@roebling1867].
Independientemente de que el puente llegue o no a demostrar esa reserva, la
redundancia modifica el carácter de la estructura: el fallo deja de ser un evento
único en una cadena única, y el margen del proyectista es estructural además de
numérico.

La justificación del diseño puede enunciarse como una lista breve y ordenada:

1. Tratar la rigidez del tablero frente al viento como el criterio de diseño
   rector, por delante del peso mínimo o la esbeltez máxima.
2. Conservar el sistema colgante como mecanismo primario para la transmisión de
   cargas gravitacionales, dada su eficiencia en el gran vano principal.
3. Superponer tirantes inclinados de manera que una segunda trayectoria de
   cargas casi axial actúe en paralelo con las péndolas.
4. Emplear los tirantes para elevar la rigidez efectiva del tablero y desplazar
   sus frecuencias naturales fuera de la banda que más fuertemente excita el
   viento en ráfagas.
5. Aceptar simultáneamente los tirantes como sistema redundante, de modo que la
   integridad del tablero no dependa de una única familia de cables.

# Un argumento simple de rigidez

Se modela un segmento de tablero como un elemento tensado de longitud $L$,
tensión $T$ y masa por unidad de longitud $\mu$. Su frecuencia fundamental es

$$ f_1 = \frac{1}{2L}\sqrt{\frac{T}{\mu}} $$

Esta idealización de cuerda tensa es, naturalmente, una caricatura de un tablero
de puente real, que también posee rigidez a flexión y a torsión; sin embargo,
aísla el único efecto que se desea seguir — la influencia de una restricción
casi axial añadida sobre la frecuencia natural más baja.

El papel de los tirantes inclinados puede incorporarse a este esquema mediante
una *tensión efectiva*. Sea $T_0$ la tensión que el sistema colgante por sí solo
imparte al segmento de tablero, y supóngase que los tirantes contribuyen una
restricción axial adicional de rigidez $k_s$ actuando sobre el mismo segmento.
En primera aproximación, los tirantes elevan la tensión que el tablero "percibe"
a un valor combinado

$$ T_{\mathrm{eff}} = T_0 + k_s\,L $$

de modo que el segmento se comporta como si estuviera más tensado de lo que las
péndolas solas lo tensarían. Aquí $k_s$ representa la restricción axial del
abanico de tirantes proyectada sobre el tablero; un tirante más inclinado y un
cable más rígido la incrementan ambos. La expresión es ilustrativa — pretende
mostrar la *dirección* del efecto, no predecir un valor para el puente real.

Sustituyendo $T_{\mathrm{eff}}$ por $T$ en la relación de frecuencias se obtiene
el cociente entre la frecuencia fundamental del sistema atirantado (híbrido) y la
del tablero puramente colgante:

$$ \frac{f_{1,\mathrm{hybrid}}}{f_{1,\mathrm{susp}}}
   = \sqrt{\frac{T_{\mathrm{eff}}}{T_0}}
   = \sqrt{1 + \frac{k_s\,L}{T_0}} $$

El cociente es mayor que la unidad para cualquier restricción positiva $k_s$, y
crece sin límite a medida que la contribución de los tirantes $k_s L$ llega a
dominar la tensión de suspensión $T_0$. Por la relación de frecuencias, una
tensión efectiva más alta eleva $f_1$, alejando la estructura de la banda de
frecuencias donde la energía de las ráfagas y las fuerzas autoexcitadas
(aeroelásticas) son más perjudiciales. El resultado cualitativo — un tablero más
rígido y de mayor frecuencia — es exactamente lo que Roebling buscaba, y el
álgebra simplemente registra que añadir una trayectoria de cargas paralela y casi
axial solo puede desplazar la frecuencia fundamental hacia valores más altos.

# Discusión: configuración puramente colgante frente al sistema híbrido

El contraste entre ambas configuraciones se aprecia mejor en una comparación
directa. La tabla siguiente resume, en términos cualitativos, cómo la
incorporación de los tirantes inclinados modifica el comportamiento del tablero.

| Propiedad | Tablero puramente colgante | Sistema híbrido (colgante + tirantes inclinados) |
| --- | --- | --- |
| Contribución a la rigidez | Solo péndolas; la rigidez del tablero depende del cambio de forma del cable principal | Péndolas **más** restricción casi axial de los tirantes actuando en paralelo |
| Cambio geométrico bajo carga | Mayor; la carga se soporta en parte mediante la profundización de la parábola del cable | Menor; los tirantes rectos resisten con escaso cambio de geometría |
| Tendencia de la frecuencia fundamental | Más baja, $f_{1,\mathrm{susp}}$ | Más alta, $f_{1,\mathrm{hybrid}} = f_{1,\mathrm{susp}}\sqrt{1 + k_s L / T_0}$ |
| Redundancia | Una única trayectoria de cargas primaria | Dos trayectorias de cargas independientes; el tablero queda sustentado aunque una se degrade |
| Sensibilidad al viento | Mayor; las bajas frecuencias se sitúan más próximas a la banda propensa al flameo y a las ráfagas | Reducida; las frecuencias más altas alejan el tablero de esa banda |

Tres aspectos merecen énfasis. Primero, las ventajas están acopladas: la misma
geometría recta que limita el desplazamiento del tablero bajo carga es la que
eleva su frecuencia y la que proporciona la segunda trayectoria de cargas.
Rigidez, desplazamiento reducido y redundancia no son tres beneficios separados,
sino tres facetas de una misma decisión. Segundo, el argumento es robusto frente
a su propia simplicidad. Incluso cuando el modelo de cuerda tensa se sustituye
por un tablero con rigidez real a flexión y a torsión, el signo del efecto no
cambia: una restricción casi axial paralela suma a la acción restauradora y eleva
las frecuencias naturales. El álgebra ilustrativa de la sección anterior captura,
por tanto, la verdad de ingeniería aunque no capture los números de ingeniería.
Tercero, la redundancia que aportan los tirantes es cualitativamente diferente de
un mayor coeficiente de seguridad sobre un sistema único; modifica la *topología*
de las trayectorias de cargas, y es este cambio el que otorga al sistema híbrido
su margen frente a lo imprevisto [@billington1983].

Conviene resistir dos tentaciones en la lectura del puente. Una es atribuir a
Roebling la teoría moderna del flameo; disponía de experiencia y criterio, no de
las ecuaciones, y la presente nota solo sostiene que su remedio y el remedio
moderno coinciden [@billington1983]. La otra es tratar el argumento de rigidez
anterior como una medición de la estructura existente; no lo es. Aquí no se
afirma ningún resultado numérico para el Puente de Brooklyn. El valor del
argumento es explicativo: muestra *por qué* un tirante inclinado, añadido en
paralelo a un tablero colgante, debe rigidizarlo y elevar su frecuencia, que es
precisamente el comportamiento que Roebling describió en lenguaje no matemático a
la empresa del puente [@roebling1867; @mccullough1972].

# Conclusión

El Puente de Brooklyn es un sistema híbrido porque su proyectista se negó a
confiar al viento un tablero colgante esbelto. Los tirantes inclinados se
incorporaron para rigidizar y para proporcionar redundancia, anticipando con
décadas las lecciones aeroelásticas del siglo XX. Un argumento simple de rigidez
materializa la intuición: al añadir una restricción casi axial, los tirantes
elevan la tensión efectiva del tablero y desplazan su frecuencia fundamental por
un factor $\sqrt{1 + k_s L / T_0}$, alejando la estructura del régimen de bajas
frecuencias, sensible al viento, de un tablero puramente colgante — y, al hacerlo,
dejan el tablero sustentado por dos trayectorias de cargas independientes en lugar
de una. El puente perdura, en parte, gracias a un sistema de cables que la
mayoría de las personas nunca advierte, y porque el ingeniero que lo proyectó
eligió la rigidez sobre la esbeltez cuando ambas no podían coexistir
[@mccullough1972; @billington1983].
