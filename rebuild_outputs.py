#!/usr/bin/env python3
"""
Regenera global.ini desde las fuentes.

global.ini = Thord82 + blueprints + p4k + componentes + [BP] + [!] + QoL
"""

import os
import re
import sys


def load_ini(path):
    """Load ini as ordered dict of key=value, preserving order."""
    entries = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line or line.startswith(";"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            entries[key] = val
    return entries


def write_ini(path, entries):
    """Write ini file with BOM, sorted by key."""
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        for key in sorted(entries.keys(), key=str.lower):
            f.write(f"{key}={entries[key]}\n")


def apply_bp_titles(global_ini, exo, p4k):
    """Add [BP] tag at the start of mission titles that award blueprints (from ExoAE)."""
    bp_tag = "<EM4>[BP]</EM4> "
    count = 0
    for key in set(exo.keys()) & set(p4k.keys()):
        if "[BP]" in exo[key] and "[BP]" not in p4k[key]:
            if key in global_ini and "[BP]" not in global_ini[key]:
                global_ini[key] = bp_tag + global_ini[key]
                count += 1
    return count


def apply_components(global_ini, exo, p4k, dcb_components=None):
    """Add [CLS|size|grade] prefix to ship components (ExoAE + DCB fallback)."""
    CLASS_EN = {
        "Military": "MIL", "Civilian": "CIV", "Competition": "COM",
        "Industrial": "IND", "Stealth": "SIG",
    }
    CLASS_ES = {
        "Militar": "MIL", "Civil": "CIV", "Competición": "COM",
        "Industrial": "IND", "Sigilo": "SIG",
    }
    MANUF_CLASS = {
        "AEGS": "MIL", "AMRS": "MIL", "BANU": "MIL", "GODI": "MIL", "WETK": "MIL",
        "ARCC": "CIV", "BEHR": "CIV", "JSPN": "CIV", "LPLT": "CIV", "ORIG": "CIV",
        "RSI": "CIV", "SASU": "CIV", "SECO": "CIV", "TARS": "CIV", "WCPR": "CIV",
        "ACOM": "COM", "ACAS": "COM", "YORM": "COM", "QRDV": "COM",
        "BASL": "IND", "JUST": "IND",
        "ASAS": "SIG", "RACO": "SIG", "TYDT": "SIG",
    }
    COMP_TYPES = {"POWR", "COOL", "SHLD", "QDRV", "JDRV", "RADR"}
    SKIP_MANUF = {"VNCL", "XIAN"}
    BESPOKE = {"hecho a medida", "bespoke", "a medida", "custom"}

    count = 0
    prefixed_keys = set()

    # Pass 1: ExoAE-sourced prefixes (class+grade in ExoAE name)
    for key in set(exo.keys()) & set(p4k.keys()):
        if exo[key] == p4k[key]:
            continue
        if not (key.startswith("item_Name") or key.startswith("item_name")):
            continue
        m = re.match(
            r"(.+?)\s+(Military|Civilian|Competition|Industrial|Stealth)\s+([A-D])$",
            exo[key],
        )
        if not m:
            continue
        cls = CLASS_EN[m.group(2)]
        grade = m.group(3)
        sm = re.search(r"_S(\d+)", key)
        size = sm.group(1).lstrip("0") or "0" if sm else "?"
        prefix = f"[{cls}|{size}|{grade}]"
        if key in global_ini:
            global_ini[key] = f"{prefix} {global_ini[key]}"
            prefixed_keys.add(key)
            count += 1

    # Pass 2: DCB fallback for components without ExoAE class info
    _name_re = re.compile(
        r"^item_[Nn]ame_?(POWR|COOL|SHLD|QDRV|JDRV|RADR)_(\w+?)_S(\d+)", re.IGNORECASE
    )
    for key in list(global_ini.keys()):
        if key in prefixed_keys:
            continue
        m2 = _name_re.match(key)
        if not m2:
            continue
        comp_type, manuf = m2.group(1).upper(), m2.group(2).upper()
        if manuf in SKIP_MANUF or "_V01_" in key or "_PL0" in key:
            continue
        # Skip defaults/controllers
        if global_ini[key].strip().upper() in ("HEAT", "COOLER", "SHIELDS", "RADAR",
                                                 "SHIELD GENERATOR"):
            continue

        # Size from regex match
        size = m2.group(3).lstrip("0") or "0"

        # Class + grade from description
        desc_key = re.sub(r"^item_[Nn]ame", "item_Desc", key)
        desc = global_ini.get(desc_key, "")
        cls = None
        grade_letter = None
        for part in desc.split("\\n"):
            part = part.strip()
            if part.startswith("Clase:") or part.startswith("Class:"):
                cls_text = part.split(":", 1)[1].strip()
                cls = CLASS_ES.get(cls_text) or CLASS_EN.get(cls_text)
            elif part.startswith("Grado:") or part.startswith("Grade:"):
                grade_text = part.split(":", 1)[1].strip()
                if grade_text in ("A", "B", "C", "D"):
                    grade_letter = grade_text
                elif grade_text.lower() in BESPOKE:
                    grade_letter = "A"  # Bespoke = A per DCB/SPViewer/Erkul

        # Fallback class from manufacturer
        if not cls:
            cls = MANUF_CLASS.get(manuf)
        if not cls:
            continue

        # Fallback grade from DCB
        if not grade_letter and dcb_components:
            # className: strip item_Name/item_name prefix (with optional underscore)
            class_name = re.sub(r"^item_[Nn]ame_?", "", key).lower()
            dcb_entry = dcb_components.get(class_name)
            if dcb_entry:
                gl = dcb_entry[0].get("grade_letter", "?")
                if gl != "?":
                    grade_letter = gl

        # Build prefix
        if grade_letter:
            prefix = f"[{cls}|{size}|{grade_letter}]"
        else:
            prefix = f"[{cls}|{size}]"
        global_ini[key] = f"{prefix} {global_ini[key]}"
        count += 1

    return count


def strip_component_tgc(global_ini):
    """Remove Tamaño/Grado/Clase lines from ship component descriptions (redundant with prefix)."""
    _comp_re = re.compile(
        r"^item_[Dd]esc_?(?:POWR|COOL|SHLD|QDRV|JDRV|RADR)_", re.IGNORECASE
    )
    TGC = ("Tamaño:", "Grado:", "Clase:", "Size:", "Grade:", "Class:")
    count = 0
    for key in global_ini:
        if not _comp_re.match(key):
            continue
        val = global_ini[key]
        parts = val.split("\\n")
        new_parts = [p for p in parts if not p.strip().startswith(TGC)]
        new_val = "\\n".join(new_parts)
        while "\\n\\n\\n" in new_val:
            new_val = new_val.replace("\\n\\n\\n", "\\n\\n")
        if new_val != val:
            global_ini[key] = new_val
            count += 1
    return count


def apply_missiles_bombs(global_ini, belt, p4k):
    """Add tracking type (IR/EM/CS) to missiles and size (B#) to bombs (from BeltaKoda)."""
    count = 0
    for key in set(belt.keys()) & set(p4k.keys()):
        if belt[key].strip() == p4k[key].strip():
            continue
        bv = belt[key]
        # Missiles with tracking type
        m = re.match(r"(?:G-)?(IR|EM|CS)\s+(.+)", bv)
        if m and ("MISL" in key or "GMISL" in key):
            tracking = m.group(1)
            if key in global_ini:
                global_ini[key] = f"{tracking} {global_ini[key]}"
                count += 1
            continue
        # Bombs with size prefix
        m = re.match(r"(B\d+)\s+(.+)", bv)
        if m and "BOMB" in key:
            bomb_prefix = m.group(1)
            if key in global_ini:
                global_ini[key] = f"{bomb_prefix} {global_ini[key]}"
                count += 1
    return count


def apply_illegal_substances(global_ini):
    """Add [!] warning prefix to illegal substances."""
    drug_keys = [
        "items_commodities_widow",
        "items_commodities_slam",
        "items_commodities_maze",
        "items_commodities_neon",
        "items_commodities_etam",
        "items_commodities_altruciatoxin",
        "items_commodities_altruciatoxin_unprocessed",
        "items_commodities_GaspingWeevilEggs",
    ]
    prefix = "<EM3>[!]</EM3> "
    count = 0
    for key in drug_keys:
        if key in global_ini and not global_ini[key].startswith(prefix):
            global_ini[key] = prefix + global_ini[key]
            count += 1
    return count


def apply_hud_mining(global_ini):
    """Shorten HUD mining labels to avoid overlap."""
    changes = {
        "hud_mining_scanning_instability": "Inest:",
        "hud_mining_scanning_resistance": "Res:",
    }
    count = 0
    for key, val in changes.items():
        if key in global_ini:
            global_ini[key] = val
            count += 1
    return count


def apply_heph_and_raw(global_ini):
    """Shorten Hephaestanite to Heph and unify (Raw)/(Crudo) to (Bruto)."""
    count = 0
    # Heph shortening
    if "items_commodities_hephaestanite" in global_ini:
        global_ini["items_commodities_hephaestanite"] = "Heph"
        count += 1
    # Unify all raw minerals to (Bruto)
    for key in global_ini:
        if key.startswith("items_commodities_") and (
            "(Raw)" in global_ini[key] or "(Crudo)" in global_ini[key]
        ):
            global_ini[key] = (
                global_ini[key].replace("(Raw)", "(Bruto)").replace("(Crudo)", "(Bruto)")
            )
            count += 1
    return count


def apply_hauling_titles(global_ini):
    """Improve hauling titles with route and compact format (from MrKraken)."""
    hauling = {
        "Covalex_HaulCargo_AToB_title": "<EM2>~mission(ReputationRank)</EM2> | <EM3>DIRECTO</EM3> ~mission(CargoRouteToken) ~mission(CargoGradeToken)",
        "Covalex_HaulCargo_LinearChain_title": "~mission(ReputationRank) | ~mission(CargoRouteToken) ~mission(CargoGradeToken)",
        "Covalex_HaulCargo_MultiToSingle_title": "~mission(ReputationRank) | ~mission(CargoRouteToken) ~mission(CargoGradeToken)",
        "Covalex_HaulCargo_RoundDelivery_title": "~mission(ReputationRank) | ~mission(CargoRouteToken) ~mission(CargoGradeToken) Circuito",
        "Covalex_HaulCargo_SingleToMulti_title": "~mission(ReputationRank) | ~mission(CargoRouteToken) ~mission(CargoGradeToken)",
    }
    count = 0
    for key, val in hauling.items():
        if key in global_ini:
            global_ini[key] = val
            count += 1
    return count


def strip_trailing_spaces(global_ini):
    """Remove trailing whitespace from all values."""
    count = 0
    for key in global_ini:
        stripped = global_ini[key].rstrip()
        if stripped != global_ini[key]:
            global_ini[key] = stripped
            count += 1
    return count


def main():
    base = "versions/4.7.0-LIVE_11545720"

    print("Cargando fuentes...")
    thord82 = load_ini(f"{base}/sources/global_thord82.ini")
    diff_es = load_ini(f"{base}/diff/global_diff_es.ini")
    diff_p4k_es = load_ini(f"{base}/diff/global_diff_p4k_es.ini")
    exo = load_ini(f"{base}/sources/global_exoae.ini")
    belt = load_ini(f"{base}/sources/global_beltakoda.ini")
    p4k = load_ini(f"{base}/sources/global_p4k_en.ini")

    print(f"  Thord82: {len(thord82)} claves")
    print(f"  Diff ES (blueprints): {len(diff_es)} claves")
    print(f"  Diff P4K ES: {len(diff_p4k_es)} claves")
    print(f"  ExoAE: {len(exo)} claves")
    print(f"  BeltaKoda: {len(belt)} claves")
    print(f"  P4K EN: {len(p4k)} claves")

    # Step 1: Thord82 base
    global_ini = dict(thord82)

    # Step 2: Append blueprint info to existing descriptions
    bp_appended = 0
    bp_new = 0
    for key, bp_val in diff_es.items():
        if key in global_ini:
            global_ini[key] = global_ini[key] + bp_val
            bp_appended += 1
        else:
            global_ini[key] = bp_val
            bp_new += 1

    # Step 3: Overlay p4k translations
    p4k_added = 0
    p4k_overwritten = 0
    for key, val in diff_p4k_es.items():
        if key in global_ini:
            p4k_overwritten += 1
        else:
            p4k_added += 1
        global_ini[key] = val

    # Step 4: [BP] tags on mission titles (ExoAE)
    bp_titles = apply_bp_titles(global_ini, exo, p4k)

    # Step 5: Component class/grade prefixes (ExoAE + DCB fallback)
    dcb_components = None
    dcb_path = "Game2.dcb"
    if os.path.exists(dcb_path):
        try:
            from extract_ship_components import load_dcb_ship_components
            dcb_components = load_dcb_ship_components(dcb_path)
        except Exception as e:
            print(f"  Aviso: No se pudo cargar DCB para prefijos: {e}")
    components = apply_components(global_ini, exo, p4k, dcb_components)

    # Step 5b: Strip Tamaño/Grado/Clase from component descriptions
    tgc_stripped = strip_component_tgc(global_ini)

    # Step 6: Missile tracking type + bomb size (BeltaKoda)
    missiles = apply_missiles_bombs(global_ini, belt, p4k)

    # Step 7: Illegal substance warnings
    drugs = apply_illegal_substances(global_ini)

    # Step 8: HUD mining abbreviations
    hud = apply_hud_mining(global_ini)

    # Step 9: Heph shortening + raw minerals unification
    minerals = apply_heph_and_raw(global_ini)

    # Step 10: Hauling titles with route (MrKraken)
    hauling = apply_hauling_titles(global_ini)

    # Step 11: Strip trailing whitespace
    trimmed = strip_trailing_spaces(global_ini)

    # Report
    print(f"\nResultado:")
    print(f"  Blueprints appended: {bp_appended}, new: {bp_new}")
    print(f"  P4K added: {p4k_added}, overwritten: {p4k_overwritten}")
    print(f"  [BP] titulos: {bp_titles}")
    print(f"  Componentes [CLS|tam|grado]: {components}")
    print(f"  Desc Tamaño/Grado/Clase eliminados: {tgc_stripped}")
    print(f"  Misiles/bombas tracking: {missiles}")
    print(f"  [!] drogas: {drugs}")
    print(f"  HUD mining: {hud}")
    print(f"  Minerales (Heph + Bruto): {minerals}")
    print(f"  Hauling titles: {hauling}")
    print(f"  Trailing spaces eliminados: {trimmed}")
    print(f"\n  Total claves: {len(global_ini)}")

    write_ini(f"{base}/output/global.ini", global_ini)
    print(f"  Guardado: {base}/output/global.ini")


if __name__ == "__main__":
    main()
