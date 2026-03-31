# Formato de stats — inject_weapon_stats.py

## Fuentes de datos (--source tested)

1. **Excel testeado in-game** (tab_Item.csv) — DPS, Alpha, FR, Velocidad, Rango, Peso, Caída de daño, Modos de fuego
2. **Data.p4k del juego** (global_p4k_en.ini) — Mapeo nombre inglés → className

No se usa scunpacked para --source tested. Scunpacked solo se usa como fuente alternativa con --source scunpacked.

## Principios

1. Solo inyectar stats que el juego NO muestra
2. NO duplicar cadencia, retroceso, dispersión (el juego los muestra)
3. Cargador/batería y accesorios de la descripción original SE QUEDAN
4. Tipo de daño solo cuando hay daño mixto
5. `Clase: energía (Laser)` → `Clase: Laser` (quitar "energía" redundante)
6. Formato compacto: sin líneas en blanco entre secciones, solo `\n\n` antes del flavor text
7. Modos entre corchetes: `[Auto]`, `[Semi]`, `[Full]`, `[Hot]`, `[Beam]`, `[Slug]`, `[Doble]`, `[Burst]`, `[Burst5]`
8. K para DPS/Alpha/Dmg >= 1000: `2.1K`, `95K`, `285K`
9. Vel/Rango/Peso: siempre número normal (metros, m/s, kg)
10. Sin perdigones en línea de DPS

## Formato armas FPS

### Modo único
```
[Auto] DPS: 182.8 | Alpha: 22 | 875 m/s | 1750m
3.5 kg | Dmg/Cargador: 990
Caída daño: desde 60m
```

### Modos seleccionables (P4-AR, R97, Gallant)
```
[Auto] DPS: 162 | Alpha: 12 | 550 m/s | 1100m
[Semi] DPS: 84 | Alpha: 12 | 550 m/s | 1100m
3.2 kg | Dmg/Cargador: 480
Caída daño: desde 40m
```

### Heat ramp (Fresnel, Pulse, Prism)
```
[Auto] DPS: 173.2 | Alpha: 9 | 1100 m/s | 4400m
[Hot] DPS: 156.8 | Alpha: 31.5 | 1100 m/s | 4400m
15 kg | Dmg/Cargador: 1.5K
```

### Charge (Scourge, Zenith, Karna)
```
[Semi] DPS: 89.8 | Alpha: 77 | 50 m/s | 200m
[Full] DPS: 2.1K | Alpha: 6.1K | 2500 m/s | 10000m
15 kg | Dmg/Cargador: 385
```

### 3 modos (Custodian, Karna)
```
[Auto] DPS: 173.3 | Alpha: 13 | 600 m/s | 1200m
[Burst] DPS: 48.8 | Alpha: 39 | 600 m/s | 1200m
[Full] DPS: 44.6 | Alpha: 171.6 | 600 m/s | 1200m
2.8 kg | Dmg/Cargador: 780
```

### Beam (Quartz, Ripper)
```
[Beam] DPS: 225 | Alpha: 7.5 | 25m
2.8 kg | Dmg/Cargador: 1.4K
Caída daño: desde 10m
```

## Formato cargadores
```
Tipo de artículo: Cargador
Capacidad: 45 | 0.6 kg
```

## Formato armaduras
```
7 kg | Stun: 60% | Impacto: 35%
```
Peso por tier del Excel. Stun e Impacto son % de reducción.

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

## Datos eliminados

- **Penetración** (MaxPenetrationThickness) — solo venía de scunpacked, eliminada
- **Pierceability** — no se usa en el juego
- **Perdigones** en línea de DPS — eliminados para compactar
