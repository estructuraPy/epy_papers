---
title:
  en: "The Inclined Stays of the Brooklyn Bridge: Roebling's Hybrid Answer to the Wind"
  es: "Los tirantes inclinados del Puente de Brooklyn: la respuesta híbrida de Roebling al viento"
language: en
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
  - The Brooklyn Bridge couples a suspension system with inclined stays.
  - Roebling added the stays primarily to stiffen the deck against wind.
  - The hybrid system anticipated aeroelastic concerns by decades.
declarations:
  competing-interests: "The author declares no competing interests."
  ai-disclosure: "Formatting and draft assembly performed with epy_papers."
bibliography: refs.bib
---

::: {.disclosure}
This manuscript is an illustrative example prepared with the assistance of AI; review its content before relying on it.
:::

**About this example** — a worked example of *epy_papers*, part of the
open-source ePy document suite. Source and the sibling examples on GitHub:
[epy_papers · Brooklyn Bridge](https://github.com/estructuraPy/epy_papers/tree/main/examples/brooklyn_bridge),
[epy_slides · Empire State](https://github.com/estructuraPy/epy_slides/tree/main/examples/empire_state_building),
[epy_reports · Newmark](https://github.com/estructuraPy/epy_reports/tree/main/examples/newmark).

# Introduction

The Brooklyn Bridge, opened in 1883, is remembered as a triumph of the
suspension form. Yet a close look at its deck reveals a second, distinct cable
system: a fan of straight, inclined stays anchored at the towers and fastened
to the deck, superimposed on the familiar vertical suspenders that hang from
the parabolic main cables. The structure is therefore a hybrid —
cable-stayed *and* suspended at once [@mccullough1972; @billington1983].

This duality is not an ornament. It is the physical record of a design
philosophy in which stiffness, not slenderness, was the governing criterion.
Where the nineteenth-century suspension bridge aspired to lightness, Roebling
deliberately traded some of that lightness for the deck-level rigidity he
believed the wind demanded. The present note has three aims. First, to set the
decision in its historical context, recalling why a suspension specialist of
Roebling's generation would distrust a slender suspended deck. Second, to
describe the two coexisting load paths and explain, in plain mechanical terms,
why a straight stay behaves so differently from a hanging suspender. Third, to
make that intuition quantitative-but-illustrative through a simple stiffness
argument, contrasting the pure-suspension and the stayed configurations and
showing how the addition of near-axial restraint shifts the deck's fundamental
frequency. Throughout, the emphasis is on the engineering reasoning rather than
on any measured response of the existing structure.

# Historical context: a bridge built against the wind

The choice was deliberate. John A. Roebling had spent his career with
suspension bridges and was acutely aware of their weakness: a slender,
flexible deck is vulnerable to the wind. Nineteenth-century suspension spans
had failed in storms, and Roebling designed the Brooklyn Bridge to be stiff
first and elegant second. He sized the structure with a large margin and
stated that the inclined stays alone could hold the deck even if the main
cables were lost [@roebling1867]. The stays were, in his words, a guarantee of
stiffness and safety — a redundant system whose purpose was to resist the
wind and damp the motion of the deck.

That margin was a response to lived experience, not to abstract caution. The
generation of long-span suspension bridges that preceded the East River
crossing had taught engineers a hard lesson: a roadway hung from cables and
left otherwise unbraced can gather energy from a steady or gusting wind and
move in ways that grow rather than decay. Roebling's own report to the New York
Bridge Company argued the point in the language of permanence, insisting that
the crossing be built to outlast the doubts of its critics and the worst
weather of the East River [@roebling1867]. Billington, writing a century later,
read the bridge in the same key — as a work in which structural art and
structural safety were never separated, and in which the visible stays declare
the engineer's intention to the eye [@billington1983].

This was foresight. It would be more than half a century before the 1940
collapse of the Tacoma Narrows Bridge made aeroelastic instability a textbook
subject [@billington1983]. Roebling reached the same practical conclusion —
*stiffen the deck* — from experience rather than from a theory of flutter. The
distinction matters: he could not have written the modern equations of
wind-induced instability, yet his design encodes their central remedy. A deck
that is stiff in bending and torsion, and whose natural frequencies sit well
above the range a gusty wind excites comfortably, is far less likely to enter
the large, self-feeding oscillations that destroyed Tacoma Narrows. The
inclined stays are the most direct expression of that remedy.

# The hybrid system

Two load paths share the deck:

- the **suspension system**: vertical suspenders transfer deck load to the
  parabolic main cables and thence to the towers and anchorages;
- the **stay system**: inclined stays carry deck load directly to the towers
  in near-straight lines.

A straight stay is far stiffer than a hanging suspender of the same material,
because it resists load with little change of geometry. A hanging suspender,
by contrast, shares load with the main cable through a system whose shape must
change before it can carry more — the parabola deepens, the deck dips, and the
geometry does part of the work that stiffness would otherwise do. The stay
short-circuits that mechanism: anchored high on the tower and pinned to the
deck, it opposes a downward or fluctuating load almost entirely through its
axial elongation, which for a taut steel element is very small. Adding the
stays therefore raises the deck's effective stiffness and its natural
frequencies, moving the structure away from the low-frequency, wind-sensitive
regime of a pure suspension deck.

Equally important is what the second load path does for safety. With two
independent systems supporting the same roadway, the loss or degradation of one
does not leave the deck unsupported. Roebling claimed exactly this redundancy
for the stays, asserting that they could hold the deck even in the absence of
the main cables [@roebling1867]. Whether or not the bridge would ever be called
upon to demonstrate that reserve, the redundancy changes the character of the
structure: failure is no longer a single event along a single chain, and the
designer's margin is structural as well as numerical.

The design rationale can be stated as a short, ordered list:

1. Treat deck stiffness against wind as the governing design criterion, ahead
   of minimum weight or maximum slenderness.
2. Retain the suspension system as the primary gravity-carrying mechanism for
   its efficiency over the long main span.
3. Superimpose inclined stays so that a second, near-axial load path acts in
   parallel with the suspenders.
4. Use the stays to raise the deck's effective stiffness and lift its natural
   frequencies away from the band a gusting wind excites most strongly.
5. Accept the stays simultaneously as a redundant system, so that the integrity
   of the deck does not depend on any single cable family.

# A simple stiffness argument

Model a deck segment as a taut element of length $L$, tension $T$ and mass per
unit length $\mu$. Its fundamental frequency is

$$ f_1 = \frac{1}{2L}\sqrt{\frac{T}{\mu}} $$

This taut-string idealization is, of course, a caricature of a real bridge
deck, which also carries bending and torsional stiffness; but it isolates the
single effect we wish to follow — the influence of an added near-axial
restraint on the lowest natural frequency.

The role of the inclined stays can be folded into this picture through an
*effective tension*. Let $T_0$ be the tension the suspension system alone
imparts to the deck segment, and let the stays contribute an additional
near-axial restraint of stiffness $k_s$ acting over the same segment. To first
order, the stays raise the tension the deck "feels" to a combined value

$$ T_{\mathrm{eff}} = T_0 + k_s\,L $$

so that the segment behaves as if more tightly drawn than the suspenders alone
would draw it. Here $k_s$ stands for the axial restraint of the stay fan
resolved onto the deck; a steeper stay and a stiffer cable both increase it.
The expression is illustrative — it is meant to show the *direction* of the
effect, not to predict a value for the real bridge.

Substituting $T_{\mathrm{eff}}$ for $T$ in the frequency relation gives the
ratio of the stayed (hybrid) fundamental frequency to that of the
pure-suspension deck:

$$ \frac{f_{1,\mathrm{hybrid}}}{f_{1,\mathrm{susp}}}
   = \sqrt{\frac{T_{\mathrm{eff}}}{T_0}}
   = \sqrt{1 + \frac{k_s\,L}{T_0}} $$

The ratio exceeds unity for any positive stay restraint $k_s$, and it grows
without bound as the stay contribution $k_s L$ comes to dominate the
suspension tension $T_0$. By the frequency relation, a higher effective tension
raises $f_1$, separating the structure from the frequency band where gust
energy and self-excited (aeroelastic) forces are most damaging. The qualitative
result — a stiffer, higher-frequency deck — is exactly what Roebling sought,
and the algebra simply records that adding a parallel, near-axial load path can
only move the fundamental frequency upward.

# Discussion: pure suspension versus the hybrid configuration

The contrast between the two configurations is best seen side by side. The
following table summarizes, in qualitative terms, how the addition of the
inclined stays changes the behavior of the deck.

| Property | Pure-suspension deck | Hybrid (suspension + inclined stays) |
| --- | --- | --- |
| Stiffness contribution | Suspenders only; deck stiffness depends on shape change of the main cable | Suspenders **plus** near-axial stay restraint acting in parallel |
| Geometric change under load | Larger; load is carried partly by deepening of the cable parabola | Smaller; the straight stays resist with little change of geometry |
| Fundamental frequency tendency | Lower, $f_{1,\mathrm{susp}}$ | Higher, $f_{1,\mathrm{hybrid}} = f_{1,\mathrm{susp}}\sqrt{1 + k_s L / T_0}$ |
| Redundancy | Single primary load path | Two independent load paths; deck supported even if one is degraded |
| Wind sensitivity | Greater; low frequencies sit closer to the gust- and flutter-prone band | Reduced; higher frequencies move the deck away from that band |

Three points deserve emphasis. First, the gains are coupled: the same straight
geometry that limits the deck's movement under load is what raises its
frequency and what supplies the second load path. Stiffness, low displacement,
and redundancy are not three separate benefits but three faces of one decision.
Second, the argument is robust to its own crudeness. Even when the taut-string
model is replaced by a deck with genuine bending and torsional stiffness, the
sign of the effect is unchanged: a parallel near-axial restraint adds to the
restoring action and lifts the natural frequencies. The illustrative algebra of
the previous section therefore captures the engineering truth even though it
does not capture the engineering numbers. Third, the redundancy the stays
provide is qualitatively different from a larger factor of safety on a single
system; it changes the *topology* of the load paths, and it is this change that
gives the hybrid its margin against the unforeseen [@billington1983].

It is worth resisting two temptations in reading the bridge. One is to credit
Roebling with the modern theory of flutter; he had experience and judgment, not
the equations, and the present note claims only that his remedy and the modern
remedy coincide [@billington1983]. The other is to treat the stiffness argument
above as a measurement of the existing structure; it is not. No numeric result
for the Brooklyn Bridge is asserted here. The value of the argument is
explanatory: it shows *why* an inclined stay, added in parallel to a suspension
deck, must stiffen it and raise its frequency, which is precisely the behavior
Roebling described in non-mathematical language to the bridge company
[@roebling1867; @mccullough1972].

# Conclusion

The Brooklyn Bridge is a hybrid because its designer refused to trust a
slender suspended deck to the wind. The inclined stays were added to stiffen
and to provide redundancy, anticipating by decades the aeroelastic lessons of
the twentieth century. A simple stiffness argument makes the intuition
concrete: by adding a near-axial restraint, the stays raise the deck's
effective tension and lift its fundamental frequency by a factor
$\sqrt{1 + k_s L / T_0}$, moving the structure away from the wind-sensitive,
low-frequency regime of a pure suspension deck — and, in doing so, they leave
the roadway supported by two independent load paths rather than one. The bridge
endures, in part, because of a cable system most people never notice, and
because the engineer who drew it chose stiffness over slenderness when the two
could not both be had [@mccullough1972; @billington1983].
