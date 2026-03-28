# Guía de estilo de traducción — Thord82

Referencia de cómo Thord82 traduce términos en `global_thord82_.ini`. Todos los agentes de traducción deben seguir estas reglas para mantener consistencia.

> **Importante**: esta guía refleja el estado actual. Si Thord82 cambia su estilo en futuras versiones, actualizar esta guía tras el análisis.

## Cabeceras de blueprints

| Inglés | Español |
|---|---|
| `<EM4>Potential Blueprints</EM4>` | `<EM4>Posibles Planos</EM4>` |
| `<EM4>Region XX</EM4>` | Se mantiene en inglés |

## Piezas de armadura

| Inglés | Español |
|---|---|
| Helmet | Casco |
| Arms | Brazos |
| Core | Pechera |
| Legs | Piernas (general) / Pantalones (Antium, Palatino) |

## Preposiciones por set de armadura

### Sin preposición
Antium, Palatino, Morozov-SH, PAB-1, Corbel

Ejemplo: `Brazos Antium`, `Pechera Palatino Sunstone`

### "de la armadura"
Monde, Artimex, Testudo, Aves (core/legs/helmet), Calico, Geist (core/legs), Overlord, Citadel, DustUp, Venture, Defiance, Lynx, Dust Devil, Inquisitor

Ejemplo: `Brazos de la armadura Monde Hiro`, `Pechera de la armadura Artimex Lodestone`

### "para la armadura"
ADP, ADP-mk4 (arms/core), ORC-mkX, ORC-mkV, Strata, Aril, Aves (arms), Geist (arms)

Ejemplo: `Brazos para la armadura ADP Woodland`, `Brazos para la armadura Aves Shrike`

### "de armadura" (sin "la")
Piecemeal

Ejemplo: `Brazos de armadura Piecemeal`

### Excepciones de cascos
- **Con preposición** ("de la armadura"): Testudo, Aves
- **Sin preposición** (resto): `Casco Monde`, `Casco Artimex`, `Casco Calico Tactical`, etc.

## Orden de palabras en armas

Thord82 pone el **tipo antes del nombre** en la mayoría de armas:

| Inglés | Español |
|---|---|
| `Karna Rifle` | `Rifle Karna` |
| `Karna "Brimstone" Rifle` | `Rifle Karna "Brimstone"` |
| `Devastator Shotgun` | `Escopeta Devastator` |
| `Coda Pistol` | `Pistola Coda` |
| `Arclight Pistol` | `Pistola Arclight` |
| `Yubarev Pistol` | `Pistola Yubarev` |
| `LH86 Pistol` | `Pistola LH86` |
| `Ravager-212 Twin Shotgun` | `Escopeta Doble Ravager-212` |

### Excepciones (nombre antes del tipo)
| Inglés | Español |
|---|---|
| `R97 Shotgun` | `R97 Escopeta` |
| `R97 "Kismet" Shotgun` | `R97 Escopeta "Kismet"` |
| `Arrowhead Sniper Rifle` | `Arrowhead Rifle Francotirador` |
| `Scalpel Sniper Rifle` | `Scalpel Rifle Francotirador` |
| `Atzkav Sniper Rifle` | `Atzkav Rifle Francotirador` |

Nota: "Rifle Francotirador" sin "de" (Thord82 omite la preposición).

## Tipos de arma

| Inglés | Español |
|---|---|
| Assault Rifle | Rifle de Asalto |
| Sniper Rifle | Rifle Francotirador |
| Shotgun | Escopeta |
| Pistol | Pistola |
| Laser Pistol | Pistola Láser |
| SMG | SMG (se mantiene) |
| LMG | LMG (se mantiene) |
| Rifle (genérico) | Rifle |

## Armas con patrón especial

| Inglés | Español |
|---|---|
| `Parallax Energy Assault Rifle` | `Rifle de Asalto de Energía Parallax` |
| `Pulse Laser Pistol` | `Pistola Láser de Pulso` |
| `Pulse "Rouge" Laser Pistol` | `Pistola Pulse "Rouge"` |
| `Quartz Energy SMG` | `Subfusil de energía Quartz` |
| `Quartz "Lumen" Energy SMG` | `SMG Quartz de Energía "Lumen"` |
| `Fresnel Energy LMG` | `LMG de energía Fresnel` |
| `Zenith Laser Sniper Rifle` | `Rifle Francotirador Láser Zenith` |

## Baterías y cargadores

Thord82 usa estructuras variadas por arma. Siempre buscar el item_Name exacto en `global_thord82_.ini`.

| Inglés | Español |
|---|---|
| `Parallax Rifle Battery (80 Cap)` | `Batería de rifle Parallax (80 Cap)` |
| `Karna Rifle Battery (35 cap)` | `Cargador del Rifle Karna (35 cap)` |
| `R97 Shotgun Magazine (18 cap)` | `Escopeta R97 Cargador (18 cap)` |
| `Pulse Laser Pistol Battery (60 Cap)` | `Batería para Pistola Láser de Pulso (60 Cap)` |
| `Arrowhead Sniper Rifle Battery (16 cap)` | `Batería (16 cap) del Rifle francotirador Arrowhead` |
| `Arclight Pistol Battery (30 cap)` | `Batería de Pistola Arclight (30 cap)` |

Nota: "(XX Cap)" o "(XX cap)" se mantiene en inglés. En descripciones largas Thord82 usa "Capacidad".

## Colores y variantes

| Inglés | Español |
|---|---|
| Moss Camo | **Camuflaje de Musgo** (corrección del usuario, no "Camo Musgo") |
| Crimson Camo, Delta Camo, Hemlock Camo | Se mantienen en inglés |
| Maroon, Woodland | Se mantienen en inglés |
| Storm, Jet, Sand, Sunstone, Midnight... | Se mantienen en inglés |
| Black (Inquisitor) | **Negro** |
| Grey (Inquisitor) | **Gris** |

## Otros términos

| Inglés | Español |
|---|---|
| (Modified) | (Modificado) — siempre masculino |
| Exploration Suit | Traje de Exploración (nombre después: `Traje de Exploración Pembroke`) |
| Blueprints | Planos |

## Nombres propios (NUNCA traducir)

Parallax, Antium, Monde, Artimex, Karna, Arclight, Aves, Strata, Aril, Morozov-SH, Testudo, Calico, Atzkav, DustUp, Yubarev, Palatino, Geist, Corbel, Zenith, Fresnel, VOLT, Behring, Custodian, Inquisitor, y todos los demás nombres de marca/producto del juego.
