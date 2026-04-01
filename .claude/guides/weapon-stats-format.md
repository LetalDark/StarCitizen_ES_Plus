# Formato de stats — inject_weapon_stats.py

## Fuentes de datos (--source tested)

1. **Excel testeado in-game** (tab_Item.csv) — DPS, Alpha, FR, Velocidad, Peso, Caída de daño, Modos de fuego
2. **Excel testeado in-game** (tab_Magazine.csv) — Peso de cargadores
3. **Excel testeado in-game** (tab_Armor.csv) — Peso de armaduras, mochilas, ropa por tipo
4. **Excel testeado in-game** (tab_Attachment.csv) — Stats de accesorios de arma
5. **Data.p4k del juego** (global_p4k_en.ini) — Mapeo nombre inglés → className

## Principios

1. Solo inyectar stats que el juego NO muestra
2. NO duplicar cadencia, retroceso, dispersión (el juego los muestra)
3. Cargador/batería y accesorios de la descripción original SE QUEDAN
4. `Clase: energía (Laser)` → `Clase: Laser` (quitar "energía" redundante)
5. Formato compacto: sin líneas en blanco entre secciones, solo `\n\n` antes del flavor text
6. Modos entre corchetes: `[Auto]`, `[Semi]`, `[Full]`, `[Hot]`, `[Beam]`, `[Slug]`, `[Doble]`, `[Burst]`, `[Burst5]`
7. K para DPS/Alpha/Dmg >= 1000: `2.1K`, `95K`, `285K`
8. Vel/Rango/Peso: número normal (metros, m/s, kg)
9. Peso SIEMPRE arriba, junto a metadatos, antes de la descripción
10. Decimales: hasta 2, sin ceros finales (2.32, no 2.30)

## Formato armas FPS

```
[Auto] DPS: 162 | Alpha: 12 | 550 m/s
[Semi] DPS: 84 | Alpha: 12 | 550 m/s
Dmg/Cargador: 480
Cargado: 3.7 kg | Descargado: 3.2 kg
[Red. daño] 100% 40m | 83% 80m | 0% 1100m
```

### Caída de daño

- `[Red. daño] 100% 30m | 0% 80m` — cae a 0 a 80m
- `[Red. daño] 100% 30m | 50% 45m | 0% 80m` — floor al 50% a 45m, luego 0 a 80m
- `[Red. daño] 100% 30m | 50% 45m` — floor al 50%, nunca llega a 0
- `[Red. daño] Max: 1750m` — sin caída, solo rango máximo

## Formato cargadores

```
Tipo de artículo: Cargador
Capacidad: 45 | 0.6 kg
```
Stats de arma heredados se limpian automáticamente.

## Formato armaduras

### Con slot detectado (peso específico)
```
Mochilas: ligeras
3 kg | Stun: 30% | Impacto: 10%

La armadura sigilosa Geist...
```

### Sin slot (descripción compartida entre piezas)
```
Stun: 45% | Impacto: 31%
*Descripción compartida entre piezas
Casco: 5 | Pechera: 5 | Brazos: 4 | Piernas: 6 kg

Fuerza y velocidad...
```

### Pesos por tier (del Excel tab_Armor.csv)

| Tier | Casco | Pechera | Brazos | Piernas |
|---|---|---|---|---|
| Heavy (40%) | 5 | 7 | 6 | 8 |
| Hv Util (25%) | 5 | 7 | 6 | 8 |
| Medium (30%) | 5 | 5 | 4 | 6 |
| Light (20%) | 5 | 3 | 2 | 3 |
| Flightsuit (15%) | 5 | 3 | 2 | 3 |
| Undersuit (10%) | 5 (casco) | 1 (traje) | — | — |

## Formato ropa y accesorios

Peso al principio, antes de la descripción:
```
0.25 kg

La gorra Bantam de 987 ofrece...
```

Con Capacidad de carga:
```
Capacidad de carga: 1K µSCU
0.5 kg

Confeccionada a partir de un tejido...
```

### Pesos por tipo (del Excel tab_Armor.csv)

| Tipo | Peso |
|---|---|
| Camiseta (Shirt) | 0.25 kg |
| Chaqueta (Jacket) | 0.5 kg |
| Pantalón (Pants) | 0.4 kg |
| Gorro (Hat) | 0.25 kg |
| Calzado (Shoes/Boots) | 0.3 kg |
| Guantes (Gloves) | 0.1 kg |
| MobiGlas | 0.5 kg |
| Mochila | 6 kg |

## Formato accesorios de arma

Stats van antes del primer `\n\n`:
```
Fabricante: ArmaMod
Tipo: Compensador
Punto de acoplamiento: Cañón
Tamaño: 1
Tiempo de apuntado: +15%
Cadencia: +7.5%
Dispersión: -20%
0.1 kg

El Torrent Compensator1...
```

## Formato accesorios multitool

Peso después de "Clase:":
```
DEBE COMPRAR UNA MULTIHERRAMIENTA BASE...

Fabricante: Greycat Industrial
Tipo de artículo: Accesorio multiherramienta
Clase: Rayo Tractor
0.1 kg

Ya sea que sus pies estén en el piso...
```

## Formato items FPS varios

Peso al principio:
```
Alpha: 114 | Radio: 4-5.5m | 0.4 kg

Fabricante: Behring
Tipo de artículo: Granada
...
```

## Limpieza automática

- Marcadores X-prefix de MrKraken (XMAnFacturer → Fabricante, XXMAZAZINE → Batería)
- Stats de arma heredados en cargadores (DPS, kg del arma)
- Stats duplicados en re-runs

## Flags del script

```bash
python inject_weapon_stats.py --source tested          # datos testeados (default)
python inject_weapon_stats.py --dry-run                # preview sin escribir
python inject_weapon_stats.py --output test.ini        # escribir a otro fichero
python inject_weapon_stats.py --verify                 # 6 checks de calidad
python inject_weapon_stats.py --version 4.7.0-LIVE_*   # versión específica
```

## Etiquetas de modo

| FireMode del Excel | Etiqueta |
|---|---|
| Rapid, Rapid Heat, Rapid Physical | [Auto] |
| Single, Semi | [Semi] |
| Burst 3, Burst | [Burst] |
| Burst 5 | [Burst5] |
| Beam, Beam Heat | [Beam] |
| Slug | [Slug] |
| Double | [Doble] |
| Charge Single, Charge Burst | [Full] |
| Heat 50% | [Hot] |
| Combined R | [Auto] |
| Combined S (slug) | [Hot] |
