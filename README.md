# Star Citizen — Traducción al español (ES Plus)

Traducción al español de Star Citizen que combina múltiples fuentes para ofrecer la experiencia más completa posible en español. Compatible con la última versión del juego (canales LIVE y PTU cuando hay parche en pruebas), actualizada en cada parche.

## Que hace este proyecto

Star Citizen no tiene traduccion oficial completa al español. Existen proyectos comunitarios que traducen los textos del juego, pero ninguno incluye toda la informacion disponible. Este proyecto:

1. **Hereda y construye sobre la traduccion comunitaria de Thord82** como base evolutiva. Desde v1.9.0 el proyecto es independiente: cada version arranca de la anterior y aplica solo el delta del juego, sin re-mergear automaticamente fuentes externas
2. **Añade datos de blueprints** de las misiones que dan planos, con la lista de posibles recompensas traducida al español
3. **Añade clase/grado a los componentes** de naves (coolers, power plants, quantum drives, shields, radars) con prefijo compacto (ej: `[MIL|2|A] Bracer` = Militar, Tamaño 2, Grado A)
4. **Añade tracking type a misiles** (IR/EM/CS) y tamaño a bombas (B3/B5/B10) para saber que contramedida usar
5. **Marca misiones con blueprints** al principio del titulo para identificarlas rapidamente: `[BP]` = siempre dan planos; `[BP]*` = planos condicionales (v1.31.4) — el juego usa el mismo titulo para varias misiones y solo algunas dan planos, asi que la descripcion incluye una linea «Condición:» que explica cuando los da (segun el sistema, el proveedor, el recurso, la ubicacion, la region, si es repetible, el objetivo o el rango)
6. **Marca sustancias ilegales** con `[!]` para avisar antes de transportarlas
7. **Mejora titulos de hauling** añadiendo la ruta (origen>destino) al titulo del contrato
8. **Acorta nombres largos** en el HUD de mineria para evitar solapamiento (Hephaestanite → Heph, ore → (Mnl), raw → (Bto), Inestabilidad → Inest:)
9. **Reestructura el compendio de mineria** del diario del juego en 6 secciones por rareza (Legendario, Epico, Raro, Poco comun, Comun, Minables a mano) con orden alfabetico dentro
10. **Inyecta stats reales de armas FPS** (DPS, Alpha, Velocidad, Peso, Caida de daño) con datos testeados in-game
11. **Inyecta stats de armaduras** (Peso, Reduccion Stun, Reduccion Impacto, Tolerancia a fuerza G), peso de cargadores, mochilas, ropa, accesorios y mas. Datos extraidos directamente del juego — captan los rebalances entre versiones (ej. en 4.8.0 los subtrajes pasaron de 15% a 10% Stun)
12. **Inyecta stats de armas de nave** (DPS, Alpha, RPM, Velocidad, Rango, Penetracion, Capacitor, Masa, HP, EM, AoE) extraidos directamente de los datos del juego (122 armas). v1.27.1: 4 cadencias que el juego expone ambiguas (BRVS, Echion, PyroBurst, Slayer) corregidas a su valor real
13. **Inyecta stats de componentes de nave** (334 componentes): Power Plants, Quantum Drives, Jump Drives, Shields, Coolers y Radars con datos del juego
14. **Completa claves que faltan** extrayendo los textos oficiales directamente del Data.p4k del juego
15. **Corrige errores** de las fuentes originales (GUIDs nulos, pools faltantes, nombres de armadura incorrectos)
16. **Limpieza automatica** de claves obsoletas que el juego ya no usa (renombres antiguos, contenido retirado), con migracion automatica de las traducciones a los nombres nuevos
17. **Bloque de reputación en cada misión** (v1.20.0, formato mejorado v1.32.5): añade al final de la descripción la reputación que da la misión con su facción y sub-carrera (scope), la penalización por fallar y el daño cross-faction si aplica. Las misiones que dan varias recompensas de reputación a la vez muestran el TOTAL real (ej. `Reputación: +160 Recco Battaglia (General)`), y las misiones donde varias dificultades comparten descripción listan los valores de menor a mayor con la nota «según dificultad». Desde v1.33.6, cuando el juego reutiliza la misma descripción para contratos que dan recompensas distintas, cada línea indica dónde aplica («solo en Stanton y Pyro», «solo en Nyx», «según contrato»). 782 misiones cubiertas. v1.22.3 traduce además el panel de reputación y las jurisdicciones
18. **Información de escenario en eventos dinámicos** (v1.21.0): muestra los puntos que otorga cada contrato de evento (Clean Air, Resource Gathering, Return of Xenothreat) y si se reparten entre el equipo. 60 contratos
19. **Formato de stats y etiquetas unificado** (v1.22.0): el mismo dato deja de aparecer con varios nombres distintos heredados (etiquetas de armadura, accesorios de armas, etc.); además el tipo y la reducción de daño de las armaduras se corrigen para cuadrar con los valores reales del juego
20. **Gran revisión de la traducción** (v1.25.0): limpieza masiva de fallos arrastrados de la base — acentos, falsos amigos, nombres propios restaurados, "Livery"→"Pintura", frases rotas reconstruidas
21. **Soportes de armamento unificados** (v1.26.2): los racks de misiles, bombas y torpedos usan los cuatro nombres del juego (Soporte de misiles/bombas/torpedos, Lanzamisiles), sin nombres a medio traducir ni variantes heredadas
22. **Información de fabricación en materiales** (v1.26.4, completado v1.29.3): la descripción de cada mineral o material indica qué se fabrica con él — componentes de nave (por clase y grado), armas de nave, armas FPS, armaduras y equipo de minería. Las recetas de un único resultado se nombran (ej. "Cañón Singe"). Desde v1.29.3 incluye las gemas de minado a mano (Aphorite, Dolivine, Hadanite…) y el mineral en bruto ("Fabricación (tras refinar):")
23. **Stats reales en todos los accesorios de arma** (v1.29.3): los accesorios que el juego no documenta llevan sus efectos reales en la descripción — incluidos los compensadores Vera/Torrent/Stark, supresores Quell/Stoic y ediciones especiales, y la reducción de retroceso percibido de varias miras ("Sacudida/Subida (retroceso)"). Etiquetas unificadas ("Tiempo de apuntado", "Punto de acoplamiento", "Aumento", "Fogonazo")
24. **Correcciones de precisión** (v1.29.4): los ocultadores de fogonazo y supresores muestran su supresión total del fogonazo ("Fogonazo: -100%" — el juego omite este dato); la lista de "Posibles Planos" solo aparece en las misiones que de verdad dan planos (las misiones Covalex de rango bajo mostraban las recompensas del rango superior sin darlas — reporte de la comunidad); 12 nombres de accesorios y armas corregidos (las miras Behr recuperan su nombre oficial EE04/EE08, ediciones "Tweaker" reordenadas, restos sin traducir; v1.29.5: la Ballesta Novian edición Xy'kara ya no dice "Ballesta Novia")
25. **Daño real en granadas** (v1.29.6, corregido v1.29.7): las granadas letales muestran su daño verdadero en la descripción, junto al tipo de daño — la MK-4 con el valor real de cada canal (20 en LIVE, 120 en PTU tras el buff de 4.9), y la granada de plasma Scorch el daño de su zona de peligro persistente ("Daño total: 250 (25/s) | Radio: 4.25m") en lugar del daño simbólico de su impacto. El Lanzamisiles Animus documenta además su peso cargado real (25.57 kg) y la capacidad de su cargador (3 misiles)
26. **Todos los modos de disparo reales + limpieza de planos fantasma** (v1.29.8): las armas con regímenes mixtos muestran todos sus modos — el rifle Parallax estrena su haz (`[Beam] DPS: 210 | Alpha: 7 | 40% calor`, entra solo al calentar el arma) y su promedio `[Combinado]`; la Killshot separa sus dos cañones (`Balístico` / `Energía`) con el combinado real a 450 rpm; y la escopeta Prism corrige su ficha invertida (el modo frío dispara 8 perdigones a 46 de daño y el Slug es el régimen caliente). La velocidad de proyectil pasa a una línea única "Velocidad:" en todas las armas. La mira OT4-RF "Scorched" muestra sus stats reales (+5% de apuntado y Sacudida -10%, no las del modelo base). Y las misiones de transporte de Red Wind dejan de anunciar "Posibles Planos" que no dan (reporte de la comunidad; en PTU 4.9 también las de defensa de naves de Foxwell, cuyos planos retiró el parche)
27. **Retroceso real en accesorios y fichas corregidas** (v1.29.10): las líneas de retroceso de los accesorios de cañón muestran el efecto que el juego aplica DE VERDAD — el compensador Sion "Tweaker" decía -20% de retroceso al apuntar cuando en realidad lo empeora un +35%, y los ocultadores Veil ya no muestran reducciones que el juego ignora. El Lanzamisiles Animus corrige velocidad y alcance a los del misil real (1000 m/s y 30 km; antes 700 m/s / 3000 m) y su DPS pasa a sostenido (11.8K). Los SMG de electrones Quartz y Ripper SB corrigen su línea de caída de daño (mostraba un alcance imposible de 1 m; el haz llega a 25/35 m). Y masas reales donde quedaban valores antiguos: pistola de juguete WowBlast Desperado (0.21/0.1 kg) y dispositivo médico ParaMed (1.75/1 kg)
28. **Marcado de misiones con planos revisado misión a misión** (v1.29.13): ahora **todas** las misiones que dan planos llevan el marcador `[BP]` y su lista de "Posibles Planos", y las que no dan (o no están activas) ya no lo muestran. Se añadieron las defensas de nave contra los Shattered Blade (Citizens for Prosperity y Eckhart) y las 30 misiones de derechos mineros de Shubin (estaciones QV Breaker), entre otras; se retiró el marcador de misiones no activas; y **"Proyecto Hyperion" (Hockrow) vuelve a marcar planos** (la corrección anterior se lo quitó por error — esa misión sí los da). Verificado contra un listado comunitario independiente
29. **Marcador de planos condicionales `[BP]*`** (v1.31.4): algunas misiones comparten el mismo título entre varias variantes y solo algunas dan planos (reporte de la comunidad). Antes esos títulos quedaban sin marcador; ahora llevan **`[BP]*`** ("puede dar planos") y la descripción incluye una línea **«Condición:»** que explica cuándo los da: por sistema (p. ej. las de Foxwell solo en Stanton), por proveedor (las de recuperación de caja negra solo las de BitZeros, no las de Hockrow), por recurso (las de recolección de Rayari solo con Perla u Ojos de Valakkar irradiados), por ubicación, región, si es la versión repetible, el objetivo, o el rango (las de carga de Covalex solo a rango Máster). Así distingues de un vistazo `[BP]` (siempre da) de `[BP]*` (mira la condición). 23 familias de misión
30. **Listas de planos completas y correcciones de traducción** (v1.32.4): las listas de "Posibles Planos" ya no pierden recompensas — las misiones de escaneo de Recco Battaglia listaban 2 de sus 4 planos reales (faltaban el láser S00 Hofstede y la boquilla RN-7s; reporte de la comunidad) y decenas de misiones más ganan su marcador y su lista completa, verificado misión a misión contra un listado comunitario independiente. Además: todas las miras usan un formato único `(Tipo Aumento)` — Holográfica, Telescópica, Réflex, Punto rojo —, los 4 lanzadores explosivos (GP-33, Scourge, Animus, Boomtube) muestran el daño real del parche 4.9, el lema de la People's Alliance aparece traducido ("Más fuertes cuando estamos unidos"), los minerales reales van en español (Berilo, Corindón), la interfaz de repostaje unifica "brazo", y otras 20+ correcciones menores (estaciones de Nyx, Centro de llegadas de Crusader, rangos, unidades)
31. **Terminal de flota (Admin. de Flota) legible** (v1.33.0, reporte de la comunidad): la pantalla de ese terminal usa una fuente del juego que no tiene letras acentuadas en mayúscula y las pintaba como huecos ("VEH CULOS") — también le pasa al propio texto oficial del juego. Todos sus textos van ahora sin tildes para que se lean completos, los botones "Asegurar" y "Guardar" caben en su columna (antes se partían en 2-3 líneas), el panel de llamada de ascensor muestra "LLAMAR" / "EN CAMINO" sin cortar palabras y el quiosco de refinería dice "CENTRO DE REFINADO" sin desbordarse. Además, los soportes de armamento quedan unificados también en los tipos y puertos de nave que faltaban ("Bastidor/Estante/Puerto de misiles" → **Soporte de misiles**; "Lanzador de misiles" → **Lanzamisiles**; 105 textos)
32. **Más pantallas y avisos legibles** (v1.33.1, segunda tanda de reportes de la comunidad): los letreros LED de la bóveda usan otra fuente sin letras acentuadas y "BÓVEDA CERRADA" salía como "B VEDA CERRADA" — ahora muestran el estado con decoración que cabe en el panel pequeño (`||CERRADA||`, `**ABRIENDOSE**`, `**CERRANDOSE**`, `**ABIERTA**`); el aviso de compra en las tiendas de estantería decía "COMPRA - ESPERANDO \[F\]" cuando hay que MANTENER la tecla — ahora "Mantener"; los avisos de teclas ya no se cortan ("AGUANTAR RESPIRACIÓN" perdía letras porque la tecla mostraba "Mayus izquierda" donde el juego usa nombres cortos — ahora "Mayús izq.", "Ctrl der.", "Num +", etc.; el ajuste de mira del francotirador dice "Dist. de mira +/-"); el botón "Recuperar" del gestor de flota pasa a **"Pedir"** (cabía partido); se corrige el falso amigo "Propenso (salida)" al ir cuerpo a tierra (**"Tumbarse (salir)"** / **"Levantarse"**); las placas Comp-Board del hangar ejecutivo estrenan descripción coherente con su nombre; y el contrato de recuperación de caja negra ya no repite el nombre del contratista dos veces en el título
33. **HUD y pantallas MFD repasados a fondo** (v1.33.2): las 657 etiquetas cortas del HUD y las pantallas multifunción revisadas una a una contra el inglés actual — fuera malas traducciones de siempre ("MISILES DE BRAZO"→"ARMAR MISILES", "VELOCIDAD MACH"→"IGUALAR VEL.", "HUELGA"→"ATAQUE", "SENTIDOS"→sensores), textos que seguían en inglés (Engineering Override, STANDBY, WPN, Fixed - Precision), la contramedida "CHAFF"→"RUIDO" (término actual del juego), "CrimeStat" unificado, ~35 tildes recuperadas (minería, escaneo, avisos) y rótulos que desbordaban su panel recortados al hueco real ("CONFIG. DE ARMAS", "Órdenes completas", "Comprar ya")
34. **Letreros de estaciones Rest & Relax legibles** (v1.33.3, reporte de la comunidad): la fuente de los letreros físicos de las estaciones no tiene vocales acentuadas y pintaba huecos — "HUR-L5 ESTACI N HIGH COURSE". Los nombres de las 24 estaciones de Stanton y las clínicas van ahora sin tilde ("Estacion"/"Clinica") para que el letrero se lea completo; las descripciones del mobiGlas conservan todos los acentos
35. **Nombres del equipo de minería unificados** (v1.33.4, reporte de la comunidad): "Impact" y "Torrent" son nombres de producto y vuelven al original — "Impacto I Laser Minero" pasa a **"Láser de minería Impact I"** y "Modulo Torrente II" a **"Módulo Torrent II"**; los 20 láseres mineros siguen ahora un único patrón ("Láser de minería Arbor MH1", "... Helix I", "... Impact II") y los módulos, raspadores y consumibles recuperan la tilde de "Módulo". Las listas de "Posibles Planos" de 49 misiones (Recco Battaglia, Shubin, Adagio) muestran los nombres corregidos
36. **Reputación honesta por contrato y título corregido** (v1.33.6, reporte de la comunidad): varias familias de misiones (Headhunters, Foxwell, búsqueda de desaparecidos, Eckhart...) anunciaban dos ramas de reputación cuando cada contrato solo da UNA — el juego reutiliza los mismos textos para contratos de Stanton, Pyro y Nyx con recompensas distintas. Ahora cada línea de reputación indica dónde aplica: «+2.000 Headhunters (Combate de Naves; solo en Stanton y Pyro)» / «+150 Headhunters (General; solo en Nyx)», y «según contrato» cuando varía por zona o contratista (60 misiones). Además, el título «Segura Nuestro Espacio Aéreo» recupera la A que le faltaba: **«Asegura Nuestro Espacio Aéreo»**
37. **Estadísticas de 4 armas al día con el parche** (v1.33.7): las descripciones de la escopeta R97, la pistola Yubarev, el francotirador Atzkav y la LMG Fresnel mostraban daños y cadencias de un parche anterior — ahora reflejan los valores actuales del juego (la R97, por ejemplo, hace 32 de daño por cartucho a 375 disparos/min, no 28.8)

## Fuentes y agradecimientos

Aunque desde v1.9.0 el proyecto es independiente y solo recibe deltas automaticos del juego, su base y la inspiracion para muchas de las funcionalidades vienen de los siguientes proyectos comunitarios. Sin su trabajo este parche no existiria — el credito y el reconocimiento les pertenecen.

| Fuente | Descripcion | Enlace |
|---|---|---|
| **Thord82** | Traduccion comunitaria al español. Base evolutiva heredada del proyecto | [github.com/Thord82/Star_citizen_ES](https://github.com/Thord82/Star_citizen_ES/) |
| **MrKraken / StarStrings** | Blueprints de misiones, clase/grado de componentes, mejoras de hauling y QoL | [github.com/MrKraken/StarStrings](https://github.com/MrKraken/StarStrings) |
| **ExoAE / ScCompLangPack** | Clase/grado de componentes, blueprints, avisos de sustancias ilegales | [github.com/ExoAE/ScCompLangPack](https://github.com/ExoAE/ScCompLangPack/) |
| **BeltaKoda / ScCompLangPackRemix** | Tracking type de misiles/bombas, prefijos compactos de componentes | [github.com/BeltaKoda/ScCompLangPackRemix](https://github.com/BeltaKoda/ScCompLangPackRemix) |
| **Tests in-game** | DPS, Alpha, Fire Rate medidos in-game (sin y con crafteo) | Spreadsheet comunitario |
| **Data.p4k** | Textos oficiales EN/ES extraidos del propio juego | Instalacion local de Star Citizen |

## Que incluye el global.ini final

| # | Capa | Descripcion | Claves | Fuente |
|---|---|---|---|---|
| 1 | Traduccion base ES | Traduccion comunitaria completa al español | 87.591 | Thord82 |
| 2 | Blueprints misiones | Planos posibles en misiones, traducidos al ES + correcciones | 502 | MrKraken + nuestras |
| 3 | Traducciones p4k | Claves que faltan en Thord82, traducidas del ingles oficial | 529 | Data.p4k CIG |
| 4 | [BP] en titulos | Marca `[BP]` (siempre da) o `[BP]*` (condicional, con «Condición:» en la desc — v1.31.4) en misiones que dan blueprints; v1.32.4: +53 misiones marcadas al completarse la resolución de recompensas | 372 | datos del juego |
| 5 | Posibles Planos auto-generados | Bloque "Posibles Planos" en descripciones, generado automaticamente desde los datos del juego resolviendo cada blueprint a su nombre español (v1.10.0); desde v1.29.8 solo en misiones que DE VERDAD dan planos (fósiles de contratos retirados barridos); v1.32.4: listas COMPLETAS — ninguna recompensa se pierde por quedar sin resolver (reporte comunidad: Recco Battaglia listaba 2 de 4) | 352 | datos del juego |
| 6 | Componentes clase/grado | Prefijo `[MIL\|2\|A]`, `[CIV\|1\|C]`, etc. en componentes de naves | 382 | datos del juego |
| 7 | Misiles y bombas | Tracking type `IR`/`EM`/`CS` en misiles, tamaño `B#` en bombas (estilo uniforme) | 136 | datos del juego |
| 8 | Sustancias ilegales | Marca `[!]` en drogas (WiDoW, SLAM, Maze, etc.) | 8 | ExoAE |
| 9 | HUD mining | Abreviaturas para evitar solapamiento (Inest:, Res:) | 2 | MrKraken/ExoAE |
| 10 | Minerales | Heph + ore (Mnl) + raw (Bto) + ajustes nombres largos (max 14 chars) | 47 | MrKraken/ExoAE |
| 11 | Hauling titles | Ruta origen>destino en titulos de transporte de carga | 5 | MrKraken |
| 12 | Limpieza | Trailing spaces eliminados | 607 | BeltaKoda |
| 13 | Stats armas FPS | DPS, Alpha, Peso, Caida de daño y TODOS los modos de fuego reales (v1.29.8: [Combinado] en armas mixtas, calificadores como "40% calor", velocidad en línea única "Velocidad:") | 303 | Tests in-game + Data.p4k |
| 14 | Stats cargadores | Peso del cargador | 42 | Tests in-game |
| 15 | Stats armaduras | Peso, Reduccion Stun, Reduccion Impacto (datos del juego desde v1.14.1) | 787 | Datos del juego |
| 15b | Tolerancia a fuerza G | Penalización/bonus de tolerancia a fuerzas G por pieza (subtrajes +90/+97.5/+100%, armadura pesada −12.5/−25/−50%, cascos vuelo −2.5%, cascos carreras 0%) — v1.14.1 | 790 | Datos del juego |
| 16 | Stats ropa y accesorios | Peso de ropa, calzado, mochilas, accesorios arma, multitools, granadas y mas. Desde v1.29.6 las granadas letales muestran su daño (y las de zona, daño total + daño por segundo + radio) | 910 | Datos del juego |
| 17 | Correcciones manuales | Nombres armadura normalizados al formato `<Set> (Parte)`, trajes de exploración Novikov/Pembroke/Zeus/Stirling con `(Traje exploración)`, cascos de carreras (refactor v1.14.0: `Traje vuelo carreras`), traducciones recuperadas, fixes doble paréntesis, nombres de componente corregidos (v1.18.1), **gran auditoría de la traducción base v1.25.0 (+1.886: acentos, falsos amigos, contrasentidos, nombres propios, Livery→Pintura, frases rotas)**, fixes v1.26.2 (textos duplicados de la MISC Hull B, avisos de transferencia de dinero entre jugadores: tuteo y espaciado), fixes v1.28.2 (etiquetas del panel de minería acortadas para que no se solapen con los números), correcciones v1.32.4 (minerales reales en español — Berilo, Corindón —, Sistema Pyro/Stanton, miras con formato único, lema de la People's Alliance, interfaz de repostaje unificada a "brazo", pantallas de comm arrays hackeados en español y 20+ menores), tandas de reportes de la comunidad v1.33.0/v1.33.1 (terminal de flota y letreros de bóveda legibles, avisos de teclas que caben, "Mantener"/"Pedir", falso amigo "Propenso"→"Tumbarse", descs Comp-Board), **repaso completo del HUD/MFD v1.33.2** (657 etiquetas cortas contra el inglés actual: "ARMAR MISILES", "IGUALAR VEL.", "ATAQUE", "RUIDO", "CrimeStat", tildes de minería/escaneo, rótulos que caben — "CONFIG. DE ARMAS", "Órdenes completas", "Comprar ya"), título «Asegura Nuestro Espacio Aéreo» v1.33.6 | 2.705 | Verificacion manual |
| 18 | Stats armas de nave | DPS, Alpha, RPM, Vel, Rango, Penetracion, Dispersión, Capacitor, Masa, HP, EM, Energía, AoE | 122 | Datos del juego |
| 19 | Stats componentes nave | Power Plants, Quantum Drives, Jump Drives, Shields, Coolers, Radars | 334 | Datos del juego |
| 20 | Loadout Calculator JSON | Masa y fórmulas de velocidad (Sprint, Run, ADS, Duration) para calculadora externa | 199 | Tests in-game |
| 21 | CIG missing strings parcheados (v1.13.2) | Items que el juego mostraba con texto crudo `@ITEM_NAME_...` por faltar la entrada de localización: set Wrecker base + variantes ropa civil. Se retira el override cuando el juego los localice | 14 | Verificacion manual |
| 22 | Textos restaurados del sistema de Repostaje (v1.16.0) | El juego retiró 254 textos del rework de Repostaje (hints, notificaciones, diario, diálogos NPC, tooltips) pero su código sigue consultándolos. Restauramos las traducciones del build anterior hasta que el juego se reconcilie | 254 | Restauración automática |
| 23 | Contratos curados con marca asterisco (v1.16.0) | 97 contratos nuevos del juego sin texto oficial (Adagio Component, GoblinG, Certificaciones BHG, Mods ATLS, EliminateAll Rockcracker, Highpoint Killanimals, Maintenance, KillShip_FF, etc.). Texto provisional siguiendo el estilo de cada facción + marca `*` al inicio para distinguir traducción provisional. Se retira cuando el juego los localice | 97 | Verificacion manual |
| 24 | Auto-placeholders para contratos sin texto (v1.16.0) | Referencias internas del juego a textos que aún no existen en ningún idioma oficial. Mostramos un nombre humanizado con marca `*` para que el panel no aparezca con un código crudo. v1.18.2: retirados 194 placeholders que tapaban indebidamente texto real del juego en misiones como el Guantelete de Combate | 48 | Auto-generado |
| 25 | Bloque Reputación en descripciones (v1.20.0, formato mejorado v1.32.5) | Bloque al final de cada descripción con la rep que da la misión: ganancia (total real cuando la misión da varias recompensas a la vez), daño cross-faction, penalización por fallo. Misiones multi-dificultad con lista de valores + «según dificultad». 45 sub-carreras/scopes resueltos | 782 | Datos del juego |
| 26 | Soportes de armamento unificados (v1.26.2) | Los racks de misiles, bombas y torpedos usan ahora los cuatro nombres que distingue el propio juego: *Soporte de misiles*, *Soporte de bombas*, *Soporte de torpedos* y *Lanzamisiles* (lanzadores integrados como los del MOTH, Reliant Tana o Ares). Elimina los nombres a medio traducir en inglés (p.ej. "Missile Rack") y las variantes inconsistentes heredadas ("Riel", "Bastidor", "Puerto"…) | 64 | Datos del juego |
| 27 | Información de fabricación en materiales (v1.26.4, completado v1.29.3) | La descripción de cada mineral o material indica qué puedes fabricar con él: componentes de nave (por clase — Militar, Sigilo, Industrial, Civil, Competición — y grado), armas de nave, armas FPS, armaduras y equipo de minería. Las recetas de un único resultado se nombran (ej. *Cañón Singe*, *CSP-68L*). Desde v1.29.3 incluye las gemas de minado a mano y el mineral en bruto ("Fabricación (tras refinar):") | 50 | Datos del juego |
| 28 | Terminología de armas unificada (v1.26.4) | "Mass Driver" pasa a *impulsor de masa* en nombres, tipos y descripciones; "Neutron" a *Neutrón*. Queda coherente con los nombres que ya se usaban para los cañones de taquiones y de neutrones | 17 | Datos del juego |
| 29 | Bloque Escenario en descripciones (v1.21.0) | Bloque con los puntos que otorga cada contrato de evento dinámico (Clean Air, Resource Gathering, Return of Xenothreat) y si se reparten entre el equipo | 60 | Datos del juego |
| 30 | Mejoras en la lista de "Posibles Planos" (v1.21.0) | Etiqueta de dificultad en la cabecera (*Posibles Planos (Dificultad: X)*) en los grupos con escalado verificado, y tipo de componente tras cada plano de componente principal (ej. *[SIG\|1\|A] Mirage (Escudo)*: Generador / Enfriador / Escudo / Radar / Quantum Drive / Jump Drive) | 869 | Datos del juego |
| 31 | Compendio de minería por rareza | El compendio de minería del diario del juego se reorganiza en 6 secciones por rareza (Legendario, Épico, Raro, Poco común, Común, Minables a mano), con orden alfabético dentro de cada una | 1 | Reorganización |
| 32 | Etiquetas unificadas (armadura, accesorios, varios) (v1.22.0, ampliado v1.29.3) | El mismo dato deja de aparecer con varios nombres heredados: las etiquetas de stats de armadura, la línea de accesorios de armas y varias etiquetas (Tipo de artículo, Cargador, Batería, Clase) se unifican a una forma canónica. Además el tipo y la reducción de daño de las armaduras se corrigen para cuadrar con los valores reales del juego (v1.22.2). v1.29.3 unifica las de los accesorios de arma ("Tiempo de apuntado", "Punto de acoplamiento", "Aumento", "Fogonazo") | ~2.116 | Reorganización |
| 33 | Stats reales en todos los accesorios de arma (v1.29.3) | Los accesorios que el juego no documenta llevan sus efectos reales en la descripción: compensadores Vera/Torrent/Stark, supresores Quell/Stoic, estabilizadores, ediciones especiales; y la reducción de retroceso percibido de varias miras y el compensador Sion 1 ("Sacudida/Subida (retroceso)") | 70 | Datos del juego |

**Total: 90 344 claves (4.9.0 "Frontier Tensions" — LIVE 12248363). Parche 4.9.0 completo en español: Asedio de Orison 2, People's Alliance, Ayuda a Orison, misiones de Recco Battaglia, el vehículo Grey's Basher y más**

## Instalación — cómo poner Star Citizen en español

1. Descarga el ZIP de la [última release](https://github.com/LetalDark/StarCitizen_ES_Plus/releases/latest)
2. Extrae el contenido en la carpeta de instalación de Star Citizen (ej: `C:\Program Files\Roberts Space Industries\StarCitizen\`)
3. La estructura queda así (cada carpeta es el canal del RSI Launcher; el ZIP incluye LIVE y, si hay parche en pruebas, también PTU):
```
StarCitizen/
├── LIVE/
│   ├── data/Localization/spanish_(spain)/global.ini
│   └── user.cfg
└── PTU/
    ├── data/Localization/spanish_(spain)/global.ini
    └── user.cfg
```
4. Inicia el juego desde el RSI Launcher — los textos aparecerán en español

**Actualizar la traducción**: tras cada parche del juego, descarga la release nueva y sobrescribe los archivos.

**Volver al inglés**: borra el archivo `user.cfg` de la carpeta del canal (`LIVE/user.cfg`).

## Formato de componentes

Los componentes de naves llevan un prefijo con 3 partes separadas por `|`: **Clase + Tamaño + Grado**

| Clase | Prefijo |
|---|---|
| Militar | `MIL` |
| Civil | `CIV` |
| Competicion | `COM` |
| Industrial | `IND` |
| Sigilo | `SIG` |

Grado: A (mejor) a D (peor). Tamaño: 0-4.

Ejemplo: `[MIL|2|A] Bracer` = Bracer, clase Militar, tamaño 2, grado A.

Las lineas de Tamaño, Grado y Clase se han eliminado de las descripciones ya que esta informacion se muestra en el prefijo del nombre y en los campos nativos del UI del juego.

## Formato de misiles y bombas

Los misiles llevan un prefijo con el tipo de tracking:

| Prefijo | Tracking | Contramedida |
|---|---|---|
| `IR` | Infrarrojo | Flares |
| `EM` | Electromagnetico | Chaff |
| `CS` | Cross-Section | Sin CM directa |

Las bombas llevan prefijo de tamaño: `B3`, `B5`, `B10`.

Ejemplo: `IR Misil Marksman I` = Marksman tamaño 1, tracking infrarrojo.

## Formato de stats de armas FPS

Las armas muestran modos de fuego etiquetados con stats reales testeados in-game:

```
Fabricante: Kastak Arms
Tipo de artículo: SMG
Clase: Laser
Tamaño de la bateria: 60
Accesorios: optica (S1), Cañon (S1), Debajo del cañon (S1)
[Auto] DPS: 173.3 | Alpha: 13 | 600 m/s
[Burst] DPS: 48.8 | Alpha: 39 | 600 m/s
[Full] DPS: 44.6 | Alpha: 171.6 | 600 m/s
Dmg/Cargador: 780
Cargado: 3.18 kg | Descargado: 2.75 kg
[Red. daño] 100% 15m | 73% 77m | 0% 950m
```

| Etiqueta | Significado |
|---|---|
| `[Auto]` | Modo automatico |
| `[Semi]` | Modo semiautomatico |
| `[Burst]` | Rafaga |
| `[Beam]` | Rayo continuo |
| `[Full]` | Disparo cargado |
| `[Hot]` | Modo caliente (heat ramp) |
| `[Slug]` | Proyectil unico (escopetas) |
| `[Doble]` | Doble cañon |

Valores grandes usan K: `2.1K`, `95K`, `285K`

## Formato de nombres de armadura

Desde v1.9.5 todas las piezas de armadura siguen el formato unificado `<Set> <Variante> (Parte)`, mirror del inglés oficial del juego. Las 4 partes usan etiquetas en español consistentes:

- **Pecho** (core)
- **Brazos** (arms)
- **Piernas** (legs)
- **Casco** (helmet)

Las variantes "Modificado/a/s" concuerdan en género con la parte: `(Pecho Modificado)`, `(Piernas Modificadas)`, `(Brazos Modificados)`, `(Casco Modificado)`.

Ejemplos: `Citadel Dark Red (Pecho)`, `Aves Starchaser (Piernas)`, `ADP-mk4 Big Boss (Casco)`, `DCP Camuflaje Cazador (Brazos)`, `ADP-mk4 (Pecho Modificado)`.

Los trajes tipo pantalón (Antium, Palatino) usan `(Pantalones)` como variante para reflejar que son prendas de tela, no armadura rígida.

**Mochilas y subtrajes (v1.9.6)** siguen el mismo esquema:
- **Mochila** → `CSP-68L Forest Camo (Mochila)`, `Aril Black Cherry (Mochila)`, variante modificada `(Mochila Modificada)`
- **Subtraje** → calco ES de "undersuit". `TCS-4 Woodland (Subtraje)`, `Guardian (Subtraje)`, variante modificada `(Subtraje Modificado)`

**Trajes de exploración** (Novikov, Pembroke, Zeus, Stirling) son una pieza única integrada in-game (brazos+piernas+pecho+subtraje) y llevan marcadores propios:
- Traje completo → `Novikov (Traje exploración)`, `Stirling Sediment Edition (Traje exploración)`
- Casco (item separado) → `Zeus Starscape (Casco exploración)`
- Mochila (item separada) → `Pembroke RSI Sunburst Edition (Mochila exploración)`

**Cascos de carreras** (flightsuit helmets temáticos de naves/ligas) usan `(Casco carreras)`: `Mirai (Casco carreras)`, `Murray Cup (Casco carreras)`, `Origin 350r (Casco carreras)`.

## Formato de stats de armaduras

Cada pieza de armadura muestra tolerancia a fuerza G + peso/stun/impacto justo despues de los metadatos. Datos extraidos directamente del juego (v1.14.1):

```
Mochilas: Medianas, Ligeras
Tolerancia a fuerza G: -25%
5 kg | Stun: 45% | Impacto: 31%

Fuerza y velocidad se combinan...
```

Las armaduras con descripcion compartida (sin pieza especifica) muestran tabla de pesos:

```
Tolerancia a fuerza G: -25%
Stun: 45% | Impacto: 31%
*Descripción compartida entre piezas
Casco: 5 | Pecho: 5 | Brazos: 4 | Piernas: 6 kg
```

**Tolerancia a fuerza G** (v1.14.1) — penalización o bonus que cada pieza aporta a la tolerancia del piloto frente a las fuerzas G en cabina:

| Pieza | G |
|---|---|
| Subtraje normal (Odyssey II, Levin…) | +90% |
| Traje de vuelo (Tailwind suit, A23 suit…) | +97.5% |
| Traje de carreras (Mirai full suit) | +100% |
| Casco de carreras (Mirai, Origin, Murray Cup…) | **0%** ← mejor opción para pilotar |
| Casco de vuelo (Tailwind, A23) | −2.5% |
| Casco ligero | −3.1% |
| Casco medio | −6.2% |
| Casco pesado (Caudillo) | −12.5% |
| Brazos pesados | −12.5% |
| Piernas pesadas | −25% |
| Torso pesado | −50% |
| Bespokesuit (traje pesado completo) | −87.5% |

## Formato de stats de armas de nave

Stats extraidos directamente de los datos del juego. 6 lineas agrupadas por tipo:

```
DPS: 817.9 | Alpha: 65.43 | 750 RPM
1800 m/s | 3006m | Disp: 0.6
Pen: 1 | Radio: 0.05-0.1
Cap: 75 | Coste: 72.7 | Reg: 15/s | CD: 0.84s
375 kg | HP: 1650 | EM: 304 | Energía: 0.9
```

| Linea | Grupo | Contenido |
|---|---|---|
| 1 | Daño | DPS burst, Alpha por disparo, cadencia |
| 2 | Proyectil | Velocidad, rango maximo, dispersion |
| 3 | Penetracion | Distancia de penetracion, radio de impacto |
| 4 | Sustain | Capacitor (energia) o Municion (balistica) |
| 5 | Fisico/firma | Masa, vida, firma EM, consumo energia |
| 6 | Solo distortion | Radio de explosion (AoE) |

Armas balisticas muestran `Mun: X` en vez de capacitor. Armas de distorsion muestran `Alpha: X Dist` y linea AoE. Scatterguns muestran pellets: `Alpha: 560 (8×70)`.

## Formato de stats de componentes de nave

Stats extraidos de los datos del juego. Cada tipo de componente muestra stats relevantes:

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

La eficiencia del Quantum Drive depende del tanque cuantico de la nave. Se muestra el rango min-max para todas las naves compatibles con ese tamaño de QDrive.

## Version actual

El ZIP contiene el `global.ini` del canal activo de Star Citizen (con 4.9.0 ya en LIVE vuelve a haber un solo canal).

- **Canal LIVE: Star Citizen Alpha 4.9.0-LIVE "Frontier Tensions"** (build 12248363) — v1.33.7: estadísticas de 4 armas actualizadas al parche (R97, Yubarev, Atzkav, Fresnel — sus descripciones mostraban daños y cadencias antiguos); v1.33.6: reputación honesta por contrato (las líneas de reputación indican dónde aplica cada recompensa — «solo en Stanton y Pyro», «solo en Nyx», «según contrato» — porque el juego reutiliza los mismos textos para contratos con recompensas distintas; 60 misiones) y título «Asegura Nuestro Espacio Aéreo» corregido; v1.33.4: nombres del equipo de minería unificados ("Impacto I Laser Minero" → "Láser de minería Impact I", "Módulo Torrent" recupera su nombre, tildes de "Módulo" y un único patrón en los 20 láseres; 49 misiones muestran los nombres corregidos en sus "Posibles Planos"); v1.33.3: letreros de las estaciones Rest & Relax legibles (su fuente no tiene vocales acentuadas y "ESTACIÓN" salía "ESTACI N"; los nombres van sin tilde, las descripciones del mobiGlas conservan los acentos); v1.33.2: repaso completo del HUD y las pantallas MFD (657 etiquetas cortas revisadas contra el inglés actual: malas traducciones corregidas — "ARMAR MISILES", "IGUALAR VEL.", "ATAQUE" —, textos en inglés traducidos, contramedida "RUIDO", 35 tildes recuperadas y rótulos que desbordaban recortados — "CONFIG. DE ARMAS", "Órdenes completas", "Comprar ya"); v1.33.1: segunda tanda de reportes de la comunidad (letreros de bóveda legibles con estado que cabe, "Mantener" en las tiendas de estantería, avisos de teclas sin cortar — "Mayús izq.", "Num +", "Dist. de mira +/-" —, botón "Pedir", "Tumbarse (salir)" en vez de "Propenso", descs de las placas Comp-Board y título del contrato de caja negra sin duplicar); v1.33.0: compatibilidad con el build 12248363 (sin cambios de textos por parte del juego) + terminal Admin. de Flota legible (su fuente no tiene mayúsculas acentuadas y pintaba huecos; textos sin tildes, botones "Asegurar"/"Guardar" que caben, ascensor "LLAMAR"/"EN CAMINO", "CENTRO DE REFINADO" sin desbordes) + soportes de armamento unificados también en tipos y puertos de nave (105 textos) + lema de la People's Alliance blindado en 42 misiones. Parche 4.9.0 completo en español: vuelve el Asedio de Orison, misiones de Ayuda a Orison, la People's Alliance de Levski, misiones de Recco Battaglia, nuevas armas y componentes. Novedades del build: el vehículo Grey's Basher con sus cuatro pinturas (Razorburn, Corroded, Nightmare, Blue Blossom), sus armas (Gatling Deathroll S2 y Repetidor Snapper S2) y su bodykit Chopper; además, corrección de las estadísticas de 31 armas de nave (los rocket pods estrenan bloque de stats y la PyroBurst Scattergun muestra por fin sus valores reales); v1.32.1 corrige además el DPS del Leonids Cannon (1810,7 real) y las masas de los módulos de la Multi-Tool y los contenedores de salvamento; v1.32.3 corrige las líneas de modo de disparo del Rifle CQ7 (su segundo modo es una ráfaga de 4, antes salía como un segundo [Auto]) y del Lumin V SMG ([Burst]); v1.32.4 completa las listas de "Posibles Planos" (las misiones de Recco Battaglia listaban 2 de 4 recompensas), unifica el formato de todas las miras, muestra el daño real 4.9 de los lanzadores explosivos y aplica 31 correcciones de traducción (minerales en español, lema de la People's Alliance, repostaje, y más)
- Ver [CHANGELOG.md](CHANGELOG.md) para el historial completo
