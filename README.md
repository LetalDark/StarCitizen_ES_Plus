# Star Citizen — Traducción al español (ES Plus)

Traducción al español de Star Citizen, actualizada en cada parche del juego (canales LIVE y PTU). Además de traducir, enriquece los textos con información que el juego no muestra: stats reales de armas y componentes, qué misiones dan planos, reputación por misión y mucho más.

<div align="center">

## ⬇️ Descarga

### [**DESCARGAR LA ÚLTIMA VERSIÓN**](https://github.com/LetalDark/StarCitizen_ES_Plus/releases/latest)

[![Última versión](https://img.shields.io/github/v/release/LetalDark/StarCitizen_ES_Plus?style=for-the-badge&label=%C3%9ALTIMA%20VERSI%C3%93N&color=00a8e8)](https://github.com/LetalDark/StarCitizen_ES_Plus/releases/latest)
[![Descargas](https://img.shields.io/github/downloads/LetalDark/StarCitizen_ES_Plus/total?style=for-the-badge&label=DESCARGAS&color=2ea44f)](https://github.com/LetalDark/StarCitizen_ES_Plus/releases/latest)

</div>

## Versión actual

- **LIVE — Alpha 4.10.0 "Siege of Orison"** (build 12519617): parche completo en español
- Última release: **v1.37.0** — todas las novedades, versión a versión, en el [CHANGELOG](CHANGELOG.md)

## Instalación — cómo poner Star Citizen en español

1. Descarga el ZIP de la [última release](https://github.com/LetalDark/StarCitizen_ES_Plus/releases/latest)
2. Extrae el contenido en la carpeta de instalación de Star Citizen (ej: `C:\Program Files\Roberts Space Industries\StarCitizen\`)
3. La estructura queda así (cada carpeta es el canal del RSI Launcher):
```
StarCitizen/
└── LIVE/
    ├── data/Localization/spanish_(spain)/global.ini
    └── user.cfg
```
> Mientras CIG tenga abierto un canal de pruebas, el ZIP trae además una carpeta `PTU/` con la misma estructura dentro.

4. Inicia el juego desde el RSI Launcher — los textos aparecerán en español

**Actualizar la traducción**: tras cada parche del juego, descarga la release nueva y sobrescribe los archivos. **Volver al inglés**: borra el archivo `user.cfg` de la carpeta del canal (ej. `LIVE/user.cfg`).

## Qué hace este proyecto

Star Citizen no tiene traducción oficial completa al español. Este proyecto la construye de forma independiente sobre la base comunitaria de Thord82 y, además de traducir cada parche, **enriquece los textos con datos reales del juego**:

- **Traducción completa y al día** — cada parche se traduce desde su primer build de pruebas; se restauran textos que el juego retiró pero sigue usando, se completan claves que faltan y se corrigen erratas del propio juego
- **Misiones con toda la información**: marcador `[BP]` (siempre da planos) / `[BP]*` (condicional, con línea «Condición:») y lista «[Posibles Planos]» traducida, con la **zona real** de cada variante regional («Zona: Pyro I, Monox, PYR3 L3-L5», «Zona: Pyro IV, Pyro V y sus lunas Ignis, Vatra, Adir, Fairo, Fuego, Vuur»…); bloque de **Reputación** al final de cada descripción (ganancia real, dónde aplica, penalización por fallo); puntos de **Escenario** en eventos dinámicos; títulos de transporte de carga compactos (rango y tipo de ruta a la vista); y marca `[!]` en sustancias ilegales
- **Stats reales en armas FPS y equipo**: DPS, daño, todos los modos de disparo reales, velocidad, caída de daño, peso de armaduras/ropa/cargadores, tolerancia a fuerza G, daño de granadas y efectos reales de todos los accesorios — extraídos del propio juego en cada parche
- **Stats reales en naves**: 122 armas de nave (DPS, Alpha, cadencia, alcance, capacitor…) y 334 componentes con prefijo compacto de clase/tamaño/grado (ej. `[MIL|2|A] Bracer`)
- **Misiles y bombas identificados**: tipo de tracking (IR/EM/CS) para saber qué contramedida usar, y tamaño en bombas (B3/B5/B10)
- **Minería mejorada**: HUD sin solapamientos, compendio del diario reorganizado por rareza, nombres de láseres y módulos unificados, y cada mineral indica qué se fabrica con él
- **Pantallas legibles**: los terminales y letreros cuya fuente no tiene letras acentuadas (Admin. de Flota, bóveda, estaciones Rest & Relax) muestran textos completos que caben en su panel; HUD y pantallas MFD revisados etiqueta a etiqueta
- **Calidad continua**: terminología unificada (soportes de armamento, etiquetas de stats, miras), gran revisión de la traducción heredada y correcciones constantes a partir de reportes de la comunidad

## Qué incluye el global.ini final

Recuentos hechos sobre el archivo real del canal LIVE:

| Capa | Contenido | Claves |
|---|---|---|
| Traducción al español | Todas las claves del juego, traducidas y mantenidas de forma independiente sobre una base evolutiva propia (origen: comunidad Thord82, hoy auditada al completo) | 90.564 |
| Misiones — planos | Títulos con `[BP]` (375, de ellos 29 condicionales `[BP]*` con línea «Condición:») + listas «[Posibles Planos]» (359, con la zona real de cada variante regional) | 734 |
| Misiones — reputación y eventos | Bloque Reputación (785) + bloque Escenario en eventos dinámicos (78) | 863 |
| Transporte y sustancias ilegales | Títulos de carga compactos con rango y tipo de ruta (4) + marca `[!]` en drogas (8) | 12 |
| Armas FPS | Descripciones con stats y modos de disparo reales: DPS, Alpha, velocidad, caída de daño, todos los modos | 324 |
| Armaduras, ropa y equipo | Claves con la masa real del objeto; incluye 891 piezas con Peso/Stun/Impacto y 872 con tolerancia a fuerza G | 1.751 |
| Armas de nave | Descripciones con el bloque completo de stats (DPS, Alpha, RPM, penetración, capacitor, masa…) | 134 |
| Componentes de nave | Prefijo clase\|tamaño\|grado en el nombre + stats por tipo en la descripción | 383 |
| Misiles y bombas | Prefijo de tracking `IR`/`EM`/`CS` en misiles (137) + tamaño `B#` en bombas (6) | 143 |
| Minería | Nombres abreviados del HUD y compendio del diario reorganizado por rareza | 40 |
| Fabricación en materiales | Bloque "Fabricación" en minerales y materiales (refinado y en bruto) | 50 |
| Correcciones manuales | Registro vivo de la auditoría de la traducción heredada (tildes sistemáticas incluidas) y de los reportes de la comunidad | 8.618 |

**Total: 90 564 claves en LIVE (4.10.0 "Siege of Orison", build 12519617). Parche 4.10 completo en español desde el día de su salida**

## Guía de formatos

<details>
<summary><b>Componentes de nave — prefijo y stats</b></summary>

Los componentes llevan un prefijo con 3 partes separadas por `|`: **Clase + Tamaño + Grado**.

| Clase | Prefijo |
|---|---|
| Militar | `MIL` |
| Civil | `CIV` |
| Competición | `COM` |
| Industrial | `IND` |
| Sigilo | `SIG` |

Grado: A (mejor) a D (peor). Tamaño: 0-4. Ejemplo: `[MIL|2|A] Bracer` = Bracer, clase Militar, tamaño 2, grado A. Las líneas de Tamaño/Grado/Clase se eliminan de las descripciones (ya van en el prefijo y en la UI del juego).

Cada tipo de componente muestra sus stats relevantes. Ejemplos:

**Power Plant:**
```
Energía: 25 | HP: 2700
Disto: 13K | Disipa: 866.67/s | Rec: 19.5s
EM/Seg: 496 | EM Decay: 0.15
2200 kg
```

**Quantum Drive:**
```
Vel: 324 Mm/s | Consumo: 0.024
Carga: 6s | Enfriamiento: 22.86s
Disto: 7K | Disipa: 466.67/s
440 kg | HP: 840 | EM: 26300 | Energía: 4
[Eficiencia/tanque] 1.65 SCU: 1.2 | 5.6 SCU: 4.2
```

**Shield:**
```
Escudo: 13.2K | Regen: 1452/s | Tiempo: 9.1s
Retardo: 5.27s | Caído: 10.5s
Resist. Energía: -10%
Energía: 1-4 | EM: 1650 | HP: 750
```

**Cooler:**
```
Enfriamiento: 60
Energía: 2-5 | EM: 2480 | IR: 12700 | HP: 1800
Disto: 8.5K | Disipa: 566.67/s | Rec: 19.5s
1900 kg
```

**Radar:**
```
Asist: 1300-2184m | Margen: 90m
IR: 90% | EM: 90% | CS: 90% | RS: 100%
Energía: 2-8 | EM: 2160 | HP: 1380
```

**Jump Drive:**
```
Calibración: 0.22 | Alineación: 0.2
Combustible: x1.5
Disto: 1.2K | Disipa: 240/s
320 kg | HP: 350
```

La eficiencia del Quantum Drive depende del tanque cuántico de la nave: se muestra el rango min-max de las naves compatibles con ese tamaño.
</details>

<details>
<summary><b>Misiles y bombas</b></summary>

Los misiles llevan un prefijo con el tipo de tracking:

| Prefijo | Tracking | Contramedida |
|---|---|---|
| `IR` | Infrarrojo | Flares |
| `EM` | Electromagnético | Chaff |
| `CS` | Cross-Section | Sin CM directa |

Las bombas llevan prefijo de tamaño: `B3`, `B5`, `B10`. Ejemplo: `IR Misil Marksman I` = Marksman tamaño 1, tracking infrarrojo.
</details>

<details>
<summary><b>Armas FPS — stats y modos de disparo</b></summary>

Las armas muestran sus modos de fuego etiquetados con stats reales:

```
Fabricante: Desconocido
Tipo de artículo: Rifle de asalto
Clase: Balística
Tamaño del cargador: 45
Accesorios: Óptica, Cañón, Subcañón (S2)
[Auto] DPS: 82.5 | Alpha: 22 | Balístico
[Auto] DPS: 71.25 | Alpha: 19 | Energía
[Combinado] DPS: 153.75 | Alpha: 20.5
Velocidad: 875 m/s
Cargado: 6.1 kg | Descargado: 4.99 kg
[Red. daño] 100% 60m | 45% 300m | 0% 1750m
```

La velocidad de proyectil va en una línea única `Velocidad:`; solo los modos con munición propia (cargados/escopeta divergente) la muestran en su línea. Los modos pueden llevar calificadores: tipo de daño por cañón (`Balístico`/`Energía`) o condición de entrada (p. ej. `40% calor`).

| Etiqueta | Significado |
|---|---|
| `[Auto]` | Modo automático |
| `[Semi]` | Modo semiautomático |
| `[Burst]` | Ráfaga |
| `[Beam]` | Rayo continuo |
| `[Full]` | Disparo cargado |
| `[Hot]` | Modo caliente (heat ramp) |
| `[Slug]` | Proyectil único (escopetas) |
| `[Doble]` | Doble cañón |
| `[Combinado]` | Promedio del ciclo mixto (armas con varios regímenes) |

Valores grandes usan K: `2.1K`, `95K`, `285K`
</details>

<details>
<summary><b>Armas de nave — stats</b></summary>

6 líneas agrupadas por tipo:

```
DPS: 817.9 | Alpha: 65.43 | 750 RPM
1800 m/s | 3006m | Disp: 0.6
Pen: 1 | Radio: 0.05-0.1
Cap: 75 | Coste: 72.7 | Reg: 15/s | CD: 0.84s
375 kg | HP: 1650 | EM: 304 | Energía: 0.9
```

| Línea | Grupo | Contenido |
|---|---|---|
| 1 | Daño | DPS burst, Alpha por disparo, cadencia |
| 2 | Proyectil | Velocidad, rango máximo, dispersión |
| 3 | Penetración | Distancia de penetración, radio de impacto |
| 4 | Sustain | Capacitor (energía) o munición (balística) |
| 5 | Físico/firma | Masa, vida, firma EM, consumo de energía |
| 6 | Solo distorsión | Radio de explosión (AoE) |

Armas balísticas muestran `Mun: X` en vez de capacitor. Armas de distorsión muestran `Alpha: X Dist` y línea AoE. Scatterguns muestran pellets: `Alpha: 560 (8×70)`.
</details>

<details>
<summary><b>Armaduras — nombres de pieza</b></summary>

Todas las piezas siguen el formato unificado `<Set> <Variante> (Parte)`, espejo del inglés oficial: **Pecho**, **Brazos**, **Piernas**, **Casco**. Las variantes "Modificado/a/s" concuerdan en género: `(Pecho Modificado)`, `(Piernas Modificadas)`.

Ejemplos: `Citadel Dark Red (Pecho)`, `ADP-mk4 Big Boss (Casco)`, `ADP-mk4 (Pecho Modificado)`.

- **Mochilas y subtrajes**: `CSP-68L Forest Camo (Mochila)`, `Guardian (Subtraje)`, variantes `(Mochila Modificada)` / `(Subtraje Modificado)`
- **Trajes de exploración** (Novikov, Pembroke, Zeus, Stirling — pieza única in-game): `Novikov (Traje exploración)`, casco `(Casco exploración)`, mochila `(Mochila exploración)`
- **Cascos de carreras** (temáticos de naves/ligas): `Mirai (Casco carreras)`, `Murray Cup (Casco carreras)`
- Los trajes tipo pantalón (Antium, Palatino) usan `(Pantalones)` — son prendas de tela, no armadura rígida
</details>

<details>
<summary><b>Armaduras — stats y tolerancia a fuerza G</b></summary>

Cada pieza muestra tolerancia a fuerza G + peso/stun/impacto tras los metadatos:

```
Mochilas: Medianas, Ligeras
Tolerancia a fuerza G: -25%
5 kg | Stun: 45% | Impacto: 31%
```

Las armaduras con descripción compartida muestran tabla de pesos:

```
Tolerancia a fuerza G: -25%
Stun: 45% | Impacto: 31%
*Descripción compartida entre piezas
Casco: 5 | Pecho: 5 | Brazos: 4 | Piernas: 6 kg
```

**Tolerancia a fuerza G** — penalización o bonus de cada pieza frente a las fuerzas G en cabina:

| Pieza | G |
|---|---|
| Subtraje normal (Odyssey II, Levin…) | +90% |
| Traje de vuelo (Tailwind suit, A23 suit…) | +97.5% |
| Traje de carreras (Mirai full suit) | +100% |
| Casco de carreras (Mirai, Origin, Murray Cup…) | **0%** ← mejor opción para pilotar |
| Casco de vuelo (Tailwind, A23) | −2.5% |
| Casco ligero / medio / pesado | −3.1% / −6.2% / −12.5% |
| Brazos pesados | −12.5% |
| Piernas pesadas | −25% |
| Torso pesado | −50% |
| Bespokesuit (traje pesado completo) | −87.5% |
</details>

## Fuentes y agradecimientos

Aunque el proyecto es independiente y solo recibe deltas automáticos del juego, su base y la inspiración de muchas funcionalidades vienen de estos proyectos comunitarios. Sin su trabajo este parche no existiría — el crédito y el reconocimiento les pertenecen.

| Fuente | Descripción | Enlace |
|---|---|---|
| **Thord82** | Traducción comunitaria al español. Base evolutiva heredada del proyecto | [github.com/Thord82/Star_citizen_ES](https://github.com/Thord82/Star_citizen_ES/) |
| **MrKraken / StarStrings** | Blueprints de misiones, clase/grado de componentes, mejoras de hauling y QoL | [github.com/MrKraken/StarStrings](https://github.com/MrKraken/StarStrings) |
| **ExoAE / ScCompLangPack** | Clase/grado de componentes, blueprints, avisos de sustancias ilegales | [github.com/ExoAE/ScCompLangPack](https://github.com/ExoAE/ScCompLangPack/) |
| **BeltaKoda / ScCompLangPackRemix** | Tracking type de misiles/bombas, prefijos compactos de componentes | [github.com/BeltaKoda/ScCompLangPackRemix](https://github.com/BeltaKoda/ScCompLangPackRemix) |
| **Tests in-game** | DPS, Alpha, Fire Rate medidos in-game (sin y con crafteo) | Spreadsheet comunitario |
| **Data.p4k** | Textos oficiales EN/ES extraídos del propio juego | Instalación local de Star Citizen |
