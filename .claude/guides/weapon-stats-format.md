# Formato de stats de armas — inject_weapon_stats.py

## Principios

1. Solo inyectar stats que el juego NO muestra (DPS, Alpha, Dmg/Cargador, Vel. Proyectil, Penetración, Caída daño)
2. NO duplicar lo que el juego ya muestra abajo de la descripción (cadencia, retroceso, dispersión)
3. Cargador/batería de la descripción original SE QUEDA
4. Accesorios de la descripción original SE QUEDA
5. Tipo de daño solo cuando hay daño mixto, no cuando es obvio por la Clase
6. `Clase: energía (Laser)` se simplifica a `Clase: Laser` (quitar "energía" redundante)
7. Formato compacto: sin líneas en blanco entre secciones, solo `\n\n` antes del flavor text
8. Armas burst marcan `DPS: X (burst)`

## Formato por tipo de arma

### Balística (un solo tipo de daño físico)
```
DPS: 220 | Alpha: 22
Dmg/Cargador: 990 | Vel. Proyectil: 875 m/s
Penetración: 0.5m | Caída daño: desde 60m
```

### Energía (un solo tipo de daño energía)
```
DPS: 173.3 | Alpha: 13
Dmg/Cargador: 780 | Vel. Proyectil: 600 m/s
Penetración: 0.5m
```

### Burst (cualquier tipo, modo burst)
```
DPS: 315 (burst) | Alpha: 21
Dmg/Cargador: 945 | Vel. Proyectil: 1200 m/s
Penetración: 0.3m
```

### Shotgun (perdigones)
```
DPS: 242.7 | Alpha: 32 | 8 perdigones
Dmg/Cargador: 576 | Vel. Proyectil: 225 m/s
Penetración: 0.5m | Caída daño: desde 12m
```

### Daño mixto (Yubarev, Atzkav)
```
DPS: 239.2 (189.6 Energía + 43.8 Distorsión + 5.8 Aturdimiento)
Alpha: 41 | Dmg/Cargador: 410
Vel. Proyectil: 500 m/s | Penetración: 0.5m
```

### Beam (Quartz, Ripper)
```
DPS: 275 (225 Energía + 50 Distorsión)
Daño completo: 0-10m | Cero daño: 25m
```

### Launcher / Railgun
```
DPS: 3600 | Alpha: 9000
Dmg/Cargador: 45000 | Vel. Proyectil: 50 m/s
Penetración: 2.5m
```

## Ejemplo completo in-game

```
Fabricante: Klaus & Werner
Tipo de artículo: Rifle de asalto
Clase: Laser
Tamaño de la bateria: 45
DPS: 315 (burst) | Alpha: 21
Dmg/Cargador: 945 | Vel. Proyectil: 1200 m/s
Penetración: 0.3m
Accesorios: optica (S2), Cañon (S2), Debajo del cañon (S2)

Las armas de asalto fiables nunca fallan...
```

## Datos con problemas conocidos

- **Penetración > 100m**: Dato erróneo (P4-AR tiene 5000m). Se omite la línea de penetración.
- **DPS de scunpacked vs juego**: La cadencia de scunpacked no siempre coincide con el juego (ej: Killshot 600rpm scunpacked vs 535rpm in-game). Los DPS pueden estar inflados.
- **Armas beam sin datos**: Parallax y Fresnel son híbridas (proyectil→beam), scunpacked no tiene sus datos de DPS.
- **DPS burst**: Es la cadencia teórica dentro de la ráfaga, no el DPS sostenido real. Se marca con `(burst)`.

## Fuente de datos

scunpacked-data (GitHub: StarCitizenWiki/scunpacked-data) — mismos datos que erkul.games y spviewer.eu.
Los datos vienen del Game2.dcb extraído del Data.p4k del juego.
