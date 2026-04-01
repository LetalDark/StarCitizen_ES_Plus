# Formato de stats — Componentes de nave

## Principios

1. Mismos principios que armas de nave (ver `weapon-stats-format.md`)
2. Stats entre el header (Fabricante/Tipo) y el flavor text
3. Tamaño, Grado y Clase eliminados de la descripción (redundantes con prefijo `[CLS|tam|grado]` y UI nativa)
4. Agrupar stats relacionados en la misma línea sin hacerla demasiado larga
5. Campos con valor 0 se omiten
6. K para valores >= 1000: `13K`
7. Energía muestra rango min-max: `Energía: 1-4`
8. Min Power = consumption × minimumConsumptionFraction

## Power Plant

```
Fabricante: Amon & Reese Co.
Tipo de artículo: Planta de energía
Energía: 25 | HP: 2700
Disto: 13K | Disipa: 866.67/s | Rec: 19.5s
EM/Seg: 496 | EM Decay: 0.15
2200 kg

El JS-500 es el generador de energía grande...
```

| Línea | Contenido | Fuente DCB |
|---|---|---|
| 1 | Generación + vida | `ItemResource.generation.Power.units`, `SHealthComponentParams.Health` |
| 2 | Distorsión agrupada | `SDistortionParams.Maximum`, `.DecayRate`, `.DecayDelay` + Max/DecayRate |
| 3 | EM por segmento + decay | `EMSignature.nominalSignature / PowerMax`, `EMSignature.decayRate` |
| 4 | Masa | `SEntityPhysicsControllerParams.PhysType.Mass` |

Notas:
- **EM/Seg** = EM nominal / Energía (generación)
- **Rec** = DecayDelay + Maximum / DecayRate (tiempo total de recuperación)
- **Disipa** = velocidad a la que disipa distorsión acumulada

## Quantum Drive

```
Fabricante: Wei-Tek
Tipo de artículo: Quantum Drive
Vel: 324 Mm/s | Consumo: 0.024
Carga: 6s | Enfriamiento: 22.86s
Disto: 7K | Disipa: 466.67/s
440 kg | HP: 840 | EM: 26300 | Energía: 4
[Eficiencia/tanque] 1.65 SCU: 1.2 | 5.6 SCU: 4.2

Wei-Tek puede ser una empresa nueva...
```

| Línea | Contenido | Fuente DCB |
|---|---|---|
| 1 | Velocidad + consumo | `params.driveSpeed`, `quantumFuelRequirement` |
| 2 | Tiempos agrupados | `params.spoolUpTime`, `params.cooldownTime` |
| 3 | Distorsión agrupada | `SDistortionParams.Maximum`, `.DecayRate` |
| 4 | Físico/firma | `Mass`, `Health`, `EMSignature.nominalSignature`, `consumption.Power` |
| 5 | Eficiencia rango | Calculado: tank × speed / (fuelReq × 18000), min/max por tamaño |

Notas:
- **Vel** en Mm/s = driveSpeed / 1e6
- **Consumo** = quantumFuelRequirement (4 decimales)
- **Carga** = spool up time
- **Enfriamiento** = cooldown time
- **Eficiencia** depende del tanque QT de la nave. Se muestra rango min-max
  - Fórmula: `Eficiencia = Tanque_QT(SCU) × Vel(Mm/s) / (Consumo × 18000)`
  - Tanques QT por tamaño QDrive (extraídos de qtnk_* en DCB):
    - S0/S1: 0.90 - 4.00 SCU
    - S2: 1.65 - 5.60 SCU
    - S3: 6.60 - 12.60 SCU
    - S4: 14.60 - 120.00 SCU

## Jump Drive

```
Fabricante: Tarsus
Tipo de artículo: Módulo de salto
Calibración: 0.22 | Alineación: 0.2
Combustible: x1.5
Disto: 1200 | Disipa: 240/s
320 kg | HP: 350

Viaja a través del universo con el módulo de salto Excelsior...
```

| Línea | Contenido | Fuente DCB |
|---|---|---|
| 1 | Tasas de sintonización | `SCItemJumpDriveParams.tuningRate`, `.alignmentRate` |
| 2 | Multiplicador combustible | `SCItemJumpDriveParams.fuelUsageEfficiencyMultiplier` |
| 3 | Distorsión agrupada | `SDistortionParams.Maximum`, `.DecayRate` |
| 4 | Físico (sin EM/Energía si son 0) | `Mass`, `Health` |

## Shield

```
Fabricante: Gorgon Defender Industries
Tipo de artículo: Generador de escudo
Escudo: 13200 | Regen: 1452/s | Tiempo: 9.1s
Retardo: 5.27s | Caído: 10.5s
Resist. Energía: -10%
Energía: 1-4 | EM: 1650 | HP: 750

El FR-76 ofrece una protección de escudo fiable...
```

| Línea | Contenido | Fuente DCB |
|---|---|---|
| 1 | Pool + regeneración + tiempo | `MaxShieldHealth`, `MaxShieldRegen`, Health/Regen |
| 2 | Retardos de regeneración | `DamagedRegenDelay`, `DownedRegenDelay` |
| 3 | Resistencia de escudo | `ShieldResistance[1].Max` (Energy) × 100 |
| 4 | Físico/firma | `consumption.Power` min-max, `EMSignature`, `Health` |

Notas:
- **Escudo** = MaxShieldHealth (HP del escudo, no del componente)
- **Tiempo** = MaxShieldHealth / MaxShieldRegen
- **Retardo** = DamagedRegenDelay (tras recibir daño)
- **Caído** = DownedRegenDelay (tras escudo destruido)
- **Resist. Energía** = ShieldResistance[1].Max × 100 (negativo = más débil vs energía)

## Cooler

```
Fabricante: Aegis Dynamics
Tipo de artículo: Enfriador
Enfriamiento: 60
Energía: 2-5 | EM: 2480 | IR: 12700 | HP: 1800
Disto: 8.5K | Disipa: 566.67/s | Rec: 19.5s
1900 kg

Los mecanicos de la Marina trabajaron con los ingenieros de Aegis...
```

| Línea | Contenido | Fuente DCB |
|---|---|---|
| 1 | Capacidad de refrigeración | `ItemResource.generation.Coolant` |
| 2 | Físico/firma | `consumption.Power` min-max, `EMSignature`, `IRSignature`, `Health` |
| 3 | Distorsión agrupada | `SDistortionParams.Maximum`, `.DecayRate`, `.DecayDelay` + Max/DecayRate |
| 4 | Masa | `SEntityPhysicsControllerParams.PhysType.Mass` |

Notas:
- **Enfriamiento** = generación de coolant
- **IR** se incluye porque coolers emiten calor (relevante para stealth)
- **Disto/Disipa/Rec** = misma fórmula que Power Plant

## Radar

```
Fabricante: Grunpa
Tipo de artículo: Radar
Asist: 1300-2184m | Margen: 90m
IR: 90% | EM: 90% | CS: 90% | RS: 100%
Energía: 2-8 | EM: 2160 | HP: 1380

El V801-12 proporciona capacidades avanzadas...
```

| Línea | Contenido | Fuente DCB |
|---|---|---|
| 1 | Asistencia de apuntado | `aimAssist.distanceMinAssignment`-`distanceMaxAssignment`, `.outsideRangeBufferDistance` |
| 2 | Sensibilidades detección | `signatureDetection[0-3].sensitivity` × 100 (IR/EM/CS/RS) |
| 3 | Físico/firma | `consumption.Power` min-max, `EMSignature`, `Health` |

Notas:
- **Asist** = rango de asistencia de apuntado (aim assist min-max)
- **Margen** = distancia extra que mantiene seguimiento fuera de rango
- **IR/EM/CS/RS** = sensibilidades de detección por tipo de firma

## Entidades DCB por componente

| Tipo | Path pattern | Ejemplo |
|---|---|---|
| PowerPlant | `ships/powerplant/powr_*_scitem` | `powr_amrs_s03_js500_scitem` |
| QuantumDrive | `ships/quantumdrive/qdrv_*_scitem` | `qdrv_wetk_s02_xl1_scitem` |
| JumpDrive | `ships/jumpdrive/jdrv_*_scitem` | `jdrv_tars_s02_excelsior_scitem` |
| Shield | `ships/shieldgenerator/shld_*_scitem` | `shld_godi_s02_fr76_scitem` |
| Cooler | `ships/cooler/cool_*_scitem` + legacy | `cool_*` via search |
| Radar | `ships/radar/radr_*` | `radr_grnp_s02_vb80112` |

## Terminología español

| Inglés (spviewer) | Español (nuestro) |
|---|---|
| Pool HP / HP Pool | Escudo |
| Regen Rate | Regen |
| Regen Time | Tiempo |
| Damaged Delay | Retardo |
| Downed Delay | Caído |
| Energy Resistance | Resist. Energía |
| Cooling Unit/Generation | Enfriamiento |
| Spool | Carga |
| Cooldown | Enfriamiento |
| Max Speed | Vel |
| Efficiency | Eficiencia |
| Tuning Rate | Calibración |
| Alignment Rate | Alineación |
| Fuel Usage | Combustible |
| Disto Max Dmg | Disto |
| Disto Decay | Disipa |
| Disto Recovery | Rec |
| Aim Min/Max | Asist |
| Outside Range Buffer | Margen |
| EM Decay | EM Decay |
| EM per Segment | EM/Seg |
