#!/usr/bin/env python3
"""
Arregla los diffs de blueprints:
1. Quita GUIDs nulos (00000000-0000-0000-0000-000000000000)
2. Quita items duplicados dentro de la misma region
3. Anade los 3 pools que faltan
4. Quita LOC_UNINITIALIZED (clave invalida)
"""

import re
import sys


def fix_diff(path, new_entries, is_es=False):
    """Fix a diff file and return stats."""
    with open(path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    fixed_lines = []
    stats = {"guid_removed": 0, "dupes_removed": 0, "loc_removed": 0, "added": 0}

    for line in lines:
        line = line.rstrip("\n").rstrip("\r")
        if not line.strip() or "=" not in line:
            fixed_lines.append(line)
            continue

        key, val = line.split("=", 1)

        # Skip LOC_UNINITIALIZED - not a real mission key
        if key == "LOC_UNINITIALIZED":
            stats["loc_removed"] += 1
            continue

        # Remove null GUIDs
        if "00000000-0000-0000-0000-000000000000" in val:
            before = val
            # Remove \n- 00000000-0000-0000-0000-000000000000
            val = val.replace("\\n- 00000000-0000-0000-0000-000000000000", "")
            if val != before:
                stats["guid_removed"] += 1

        # Remove duplicate items within each region
        # Parse into regions
        parts = val.split("\\n")
        new_parts = []
        seen_in_region = set()
        current_region = None

        for part in parts:
            part_stripped = part.strip()

            # Check if this is a region header
            if re.match(r"<EM4>Region\s", part_stripped):
                current_region = part_stripped
                seen_in_region = set()
                new_parts.append(part)
                continue

            # Check if this is an item
            m = re.match(r"^- (.+)$", part_stripped)
            if m:
                item = m.group(1).strip()
                if item in seen_in_region:
                    stats["dupes_removed"] += 1
                    continue  # Skip duplicate
                seen_in_region.add(item)

            new_parts.append(part)

        val = "\\n".join(new_parts)
        fixed_lines.append(f"{key}={val}")

    # Add new entries
    for entry_key, entry_val in new_entries.items():
        fixed_lines.append(f"{entry_key}={entry_val}")
        stats["added"] += 1

    # Sort by key (maintaining format)
    header_lines = []
    entry_lines = []
    for line in fixed_lines:
        if "=" in line and not line.startswith(";"):
            entry_lines.append(line)
        else:
            header_lines.append(line)

    entry_lines.sort(key=lambda x: x.split("=", 1)[0].lower())

    # Write back
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        for line in entry_lines:
            f.write(line + "\n")

    return stats


def main():
    base = "versions/4.7.0-LIVE_11545720/diff"

    # New entries for EN
    new_en = {
        # Pool: asd3 - Hockrow FacilityDelve P3Repeat
        "Hockrow_FacilityDelve_P3Repeat_desc":
            '\\n<EM4>Potential Blueprints</EM4>'
            '\\n- Zenith "Darkwave" Laser Sniper Rifle'
            '\\n- Fresnel "Molten" Energy LMG'
            '\\n- Geist Armor Arms ASD Edition'
            '\\n- Geist Armor Core ASD Edition'
            '\\n- Geist Armor Legs ASD Edition'
            '\\n- Geist Armor Helmet ASD Edition'
            '\\n- Zenith Laser Sniper Rifle Battery (22 Cap)'
            '\\n',

        # Pool: bountyhuntersguild_paf_eliminatespecific
        "Headhunters_EliminateSpecific_PAF_desc_001":
            '\\n<EM4>Potential Blueprints</EM4>'
            '\\n- P8-AR Rifle'
            '\\n- Palatino Arms'
            '\\n- Palatino Core'
            '\\n- Palatino Legs'
            '\\n- Palatino Helmet'
            '\\n- Palatino Arms Moonfall'
            '\\n- Palatino Core Moonfall'
            '\\n- Palatino Legs Moonfall'
            '\\n- Palatino Helmet Moonfall'
            '\\n- P8-AR Rifle Magazine (15 Cap)'
            '\\n',

        # Pool: rayari_recoveritem_irradiated
        "RAIN_CollectResources_IrradiatedPearls_Desc_001":
            '\\n<EM4>Potential Blueprints</EM4>'
            '\\n- Prism Laser Shotgun'
            '\\n- Prism "Deep Sea" Laser Shotgun'
            '\\n- Prism "Bonedust" Laser Shotgun'
            '\\n- Prism "Firesteel" Laser Shotgun'
            '\\n- Stirling Exploration Suit'
            '\\n- Siebe Helmet'
            '\\n- Prism Laser Shotgun Battery (20 cap)'
            '\\n',

        # Additional keys for rayari irradiated (storm missions also use this pool)
        "RAIN_CollectResources_storm_desc_001":
            '\\n<EM4>Potential Blueprints</EM4>'
            '\\n- Prism Laser Shotgun'
            '\\n- Prism "Deep Sea" Laser Shotgun'
            '\\n- Prism "Bonedust" Laser Shotgun'
            '\\n- Prism "Firesteel" Laser Shotgun'
            '\\n- Stirling Exploration Suit'
            '\\n- Siebe Helmet'
            '\\n- Prism Laser Shotgun Battery (20 cap)'
            '\\n',

        "RAIN_CollectResources_storm_desc_002":
            '\\n<EM4>Potential Blueprints</EM4>'
            '\\n- Prism Laser Shotgun'
            '\\n- Prism "Deep Sea" Laser Shotgun'
            '\\n- Prism "Bonedust" Laser Shotgun'
            '\\n- Prism "Firesteel" Laser Shotgun'
            '\\n- Stirling Exploration Suit'
            '\\n- Siebe Helmet'
            '\\n- Prism Laser Shotgun Battery (20 cap)'
            '\\n',

        "RAIN_CollectResources_storm_desc_003":
            '\\n<EM4>Potential Blueprints</EM4>'
            '\\n- Prism Laser Shotgun'
            '\\n- Prism "Deep Sea" Laser Shotgun'
            '\\n- Prism "Bonedust" Laser Shotgun'
            '\\n- Prism "Firesteel" Laser Shotgun'
            '\\n- Stirling Exploration Suit'
            '\\n- Siebe Helmet'
            '\\n- Prism Laser Shotgun Battery (20 cap)'
            '\\n',

        "RAIN_CollectResources_storm_desc_004":
            '\\n<EM4>Potential Blueprints</EM4>'
            '\\n- Prism Laser Shotgun'
            '\\n- Prism "Deep Sea" Laser Shotgun'
            '\\n- Prism "Bonedust" Laser Shotgun'
            '\\n- Prism "Firesteel" Laser Shotgun'
            '\\n- Stirling Exploration Suit'
            '\\n- Siebe Helmet'
            '\\n- Prism Laser Shotgun Battery (20 cap)'
            '\\n',
    }

    # New entries for ES
    new_es = {
        "Hockrow_FacilityDelve_P3Repeat_desc":
            '\\n<EM4>Posibles Planos</EM4>'
            '\\n- Rifle de Francotirador Laser Zenith "Darkwave"'
            '\\n- LMG de Energia Fresnel "Molten"'
            '\\n- Brazos de la armadura Geist Edicion ASD'
            '\\n- Pechera de la armadura Geist Edicion ASD'
            '\\n- Piernas de la armadura Geist Edicion ASD'
            '\\n- Casco de la armadura Geist Edicion ASD'
            '\\n- Bateria del Rifle de Francotirador Laser Zenith (22 cap)'
            '\\n',

        "Headhunters_EliminateSpecific_PAF_desc_001":
            '\\n<EM4>Posibles Planos</EM4>'
            '\\n- Rifle P8-AR'
            '\\n- Brazos de la armadura Palatino'
            '\\n- Pechera de la armadura Palatino'
            '\\n- Piernas de la armadura Palatino'
            '\\n- Casco de la armadura Palatino'
            '\\n- Brazos de la armadura Palatino Moonfall'
            '\\n- Pechera de la armadura Palatino Moonfall'
            '\\n- Piernas de la armadura Palatino Moonfall'
            '\\n- Casco de la armadura Palatino Moonfall'
            '\\n- Cargador del Rifle P8-AR (15 cap)'
            '\\n',

        "RAIN_CollectResources_IrradiatedPearls_Desc_001":
            '\\n<EM4>Posibles Planos</EM4>'
            '\\n- Escopeta Laser Prism'
            '\\n- Escopeta Laser Prism "Deep Sea"'
            '\\n- Escopeta Laser Prism "Bonedust"'
            '\\n- Escopeta Laser Prism "Firesteel"'
            '\\n- Traje de Exploracion Stirling'
            '\\n- Casco Siebe'
            '\\n- Bateria de Escopeta Laser Prism (20 cap)'
            '\\n',

        "RAIN_CollectResources_storm_desc_001":
            '\\n<EM4>Posibles Planos</EM4>'
            '\\n- Escopeta Laser Prism'
            '\\n- Escopeta Laser Prism "Deep Sea"'
            '\\n- Escopeta Laser Prism "Bonedust"'
            '\\n- Escopeta Laser Prism "Firesteel"'
            '\\n- Traje de Exploracion Stirling'
            '\\n- Casco Siebe'
            '\\n- Bateria de Escopeta Laser Prism (20 cap)'
            '\\n',

        "RAIN_CollectResources_storm_desc_002":
            '\\n<EM4>Posibles Planos</EM4>'
            '\\n- Escopeta Laser Prism'
            '\\n- Escopeta Laser Prism "Deep Sea"'
            '\\n- Escopeta Laser Prism "Bonedust"'
            '\\n- Escopeta Laser Prism "Firesteel"'
            '\\n- Traje de Exploracion Stirling'
            '\\n- Casco Siebe'
            '\\n- Bateria de Escopeta Laser Prism (20 cap)'
            '\\n',

        "RAIN_CollectResources_storm_desc_003":
            '\\n<EM4>Posibles Planos</EM4>'
            '\\n- Escopeta Laser Prism'
            '\\n- Escopeta Laser Prism "Deep Sea"'
            '\\n- Escopeta Laser Prism "Bonedust"'
            '\\n- Escopeta Laser Prism "Firesteel"'
            '\\n- Traje de Exploracion Stirling'
            '\\n- Casco Siebe'
            '\\n- Bateria de Escopeta Laser Prism (20 cap)'
            '\\n',

        "RAIN_CollectResources_storm_desc_004":
            '\\n<EM4>Posibles Planos</EM4>'
            '\\n- Escopeta Laser Prism'
            '\\n- Escopeta Laser Prism "Deep Sea"'
            '\\n- Escopeta Laser Prism "Bonedust"'
            '\\n- Escopeta Laser Prism "Firesteel"'
            '\\n- Traje de Exploracion Stirling'
            '\\n- Casco Siebe'
            '\\n- Bateria de Escopeta Laser Prism (20 cap)'
            '\\n',
    }

    print("=== Arreglando global_diff.ini (EN) ===")
    stats_en = fix_diff(f"{base}/global_diff.ini", new_en)
    print(f"  GUIDs nulos quitados: {stats_en['guid_removed']}")
    print(f"  Duplicados quitados: {stats_en['dupes_removed']}")
    print(f"  LOC_UNINITIALIZED: {stats_en['loc_removed']}")
    print(f"  Entradas nuevas: {stats_en['added']}")

    print("\n=== Arreglando global_diff_es.ini (ES) ===")
    stats_es = fix_diff(f"{base}/global_diff_es.ini", new_es, is_es=True)
    print(f"  GUIDs nulos quitados: {stats_es['guid_removed']}")
    print(f"  Duplicados quitados: {stats_es['dupes_removed']}")
    print(f"  LOC_UNINITIALIZED: {stats_es['loc_removed']}")
    print(f"  Entradas nuevas: {stats_es['added']}")


if __name__ == "__main__":
    main()
