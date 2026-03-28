# Traduccion BluePrints — Star Citizen ES

## Proyecto

Localización al español de Star Citizen. Combina la traducción de Thord82 con la info de blueprints de MrKraken/StarStrings para generar un `global.ini` final completo.

## Fuentes externas

| Fuente | Repo | Archivo clave |
|---|---|---|
| Traducción ES | https://github.com/Thord82/Star_citizen_ES/ | `global.ini` |
| Blueprints EN | https://github.com/MrKraken/StarStrings | `global.ini` |

## Archivos del proyecto

| Archivo | Rol |
|---|---|
| `global_thord82_.ini` | Traducción ES base (fuente Thord82, sin blueprints) |
| `global_blueprints.ini` | Inglés completo con info de blueprints (fuente MrKraken) |
| `global_diff.ini` | Bloques de blueprints extraídos en inglés |
| `global_diff_es.ini` | Bloques de blueprints traducidos al español |
| `global.ini` | Archivo final: traducción ES + blueprints ES |

## Flujo de actualización

Cuando se actualicen las fuentes (nueva versión de Thord82 o MrKraken):

1. **Extracción** → Comparar fuentes, generar `global_diff.ini`
2. **Traducción** → Traducir diff al español → `global_diff_es.ini`
3. **Revisión del usuario** → El usuario valida traducciones antes de continuar
4. **Merge** → Combinar `global_thord82_.ini` + `global_diff_es.ini` → `global.ini`
5. **QA** → Validar consistencia del archivo final

## Tabla de routing

| Tarea | Agente |
|---|---|
| Comparar fuentes, detectar diferencias, extraer diffs | Extractor |
| Traducir al español siguiendo estilo Thord82 | Traductor |
| Combinar archivos en global.ini final | Merger |
| Validar consistencia, detectar errores | QA (transversal) |

## Reglas globales

- El usuario siempre valida las traducciones antes del merge
- Los nombres propios del juego (Parallax, Antium, Karna...) nunca se traducen
- Seguir el estilo de Thord82 — ver guía: `.claude/guides/thord82-style.md`
- Formato de archivos: `clave=valor`, codificación UTF-8 con BOM
