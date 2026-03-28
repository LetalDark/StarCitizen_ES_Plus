# Star Citizen - Traducción ES + BluePrints

Traducción al español de Star Citizen que combina múltiples fuentes para ofrecer la experiencia más completa posible en español.

## Qué hace este proyecto

Star Citizen no tiene traducción oficial completa al español. Existen proyectos comunitarios que traducen los textos del juego, pero ninguno incluye toda la información disponible. Este proyecto:

1. **Parte de la traducción de Thord82**, la traducción comunitaria al español más completa
2. **Añade datos técnicos de blueprints** (estadísticas de naves, armas, componentes...) que extrae MrKraken de los archivos del juego y que no están en la traducción base
3. **Traduce esos datos de blueprints al español** siguiendo el mismo estilo de Thord82
4. **Completa claves que faltan** extrayendo los textos oficiales directamente del Data.p4k del juego

El resultado son dos variantes del archivo de traducción:

- **BluePrints**: Thord82 + blueprints traducidos
- **BluePrints Plus**: lo anterior + claves extra del juego traducidas

## Fuentes

| Fuente | Descripción | Enlace |
|---|---|---|
| **Thord82** | Traducción comunitaria al español de Star Citizen. Es la base principal de este proyecto | [github.com/Thord82/Star_citizen_ES](https://github.com/Thord82/Star_citizen_ES/) |
| **MrKraken / StarStrings** | Extracción de los textos del juego con datos técnicos de blueprints (stats de naves, armas, componentes, etc.) | [github.com/MrKraken/StarStrings](https://github.com/MrKraken/StarStrings) |
| **Data.p4k** | Archivo del propio juego (~150 GB) del que se extraen los textos oficiales en inglés y español con la herramienta `extract_p4k.py` incluida en este proyecto | Instalación local de Star Citizen |

## Instalación

1. Descarga el ZIP de la última release
2. Extrae el contenido en la carpeta de Star Citizen (ej: `C:\Program Files\Roberts Space Industries\StarCitizen\`)
3. La estructura queda así:
```
StarCitizen/
└── LIVE/
    ├── data/Localization/spanish_(spain)/global.ini
    └── user.cfg
```

## Herramienta incluida: extract_p4k.py

Script Python que extrae el `global.ini` de cualquier idioma directamente del `Data.p4k` de tu instalación de Star Citizen, sin necesidad de herramientas externas.

```bash
pip install zstandard
python extract_p4k.py --list                        # Ver idiomas disponibles
python extract_p4k.py                               # Extraer inglés
python extract_p4k.py --lang spanish_(spain)         # Extraer español oficial de CIG
```

## Versión actual

- **Star Citizen Alpha 4.7.0-hotfix** (build 11545720)
- Ver [CHANGELOG.md](CHANGELOG.md) para el historial completo
