#!/usr/bin/env python3
"""
inject_weapon_stats.py — Inject real weapon stats into global.ini descriptions.

Patches the description lines in global.ini so they show accurate DPS, alpha,
penetration, etc.

Sources:
  --source scunpacked (default): stats from scunpacked fps-items.json (required)
  --source tested: stats from tested spreadsheet CSVs (tab_Item.csv),
                   name mapping from global.ini, penetration from scunpacked
                   (optional — fps-items.json not required)

Usage:
    python inject_weapon_stats.py [--version 4.7.0-LIVE_11545720] [--dry-run]
    python inject_weapon_stats.py --source tested [--dry-run]
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
VERSIONS_DIR = BASE_DIR / "versions"

# Header prefixes — lines that belong to the "header" section of a description
# All comparisons are done case-insensitive (see _startswith_any)
HEADER_PREFIXES = (
    "fabricante:",
    "tipo de artículo:",
    "tipo de articulo:",
    "tipo de ítem:",
    "tipo de item:",
    "clase:",
    "tamaño:",
    "item type:",
    "manufacturer:",
    "class:",
    "size:",
    "attachment",
    "attachments:",
    "accesorios:",
    "accesorio:",
    "acoples:",
    "tamaño del cargador:",
    "tamaño de cargador:",
    "tamaño de la bateria:",
    "tamaño de la batería:",
    "tamaño de bateria:",
    "tamaño de batería:",
    "capacidad del cargador:",
    "magazine size:",
    "battery size:",
)

# Old stats prefixes — CIG's descriptive stats to replace
# Only cadencia/alcance — NOT cargador/batería (those stay)
# All comparisons are done case-insensitive
OLD_STATS_PREFIXES = (
    "cadencia de fuego:",
    "cadencia de tiro:",
    "cadencia de disparo:",
    "alcance efectivo:",
    "alcance eficaz:",
    "rate of fire:",
    "effective range:",
    "tasa de fuego:",
    "tasa de disparo:",
    "tasa de flujo:",
    "velocidad de disparo:",
    "velocidad de incendio:",
    "rango efectivo:",
)

# Also match our own previously-injected stats so re-runs update them
OWN_STATS_PREFIXES = (
    "DPS:",
    "Alpha:",
    "Dmg/Cargador:",
    "Vel. Proyectil:",
    "Daño completo:",
    "Caída daño:",
    "Cero daño:",
    "[Auto]",
    "[Semi]",
    "[Beam]",
    "[Full]",
    "[Burst]",
    "[Burst5]",
    "[Slug]",
    "[Hot]",
    "[Doble]",
    "[Red. daño]",
    "Caída daño:",
    "No pierde daño",
    "Cargado:",
    "Descargado:",
    "Dmg/Cargador:",
    # Ship weapon stats (from DCB)
    "Pen:",
    "Radio:",
    "Cap:",
    "Coste:",
    "Reg:",
    "CD:",
    "Mun:",
    "Disp:",
    "AoE:",
    "EM:",
    "Energía:",
    "Energia:",
)

DAMAGE_LABELS = {
    "Physical": "Físico",
    "Energy": "Energía",
    "Distortion": "Distorsión",
    "Thermal": "Térmico",
    "Biochemical": "Bioquímico",
    "Stun": "Aturdimiento",
}

# Manual overrides for weapons with complex mechanics that scunpacked can't parse.
# Calculated from individual JSONs in items_beam/.
MANUAL_OVERRIDES = {
    # Parallax: hybrid projectile(210 DPS)->beam(260 DPS)
    "volt_rifle_energy_01": {
        "category": "custom",
        "stats_line": "DPS: 210-260 | Alpha: 21\\nDmg/Cargador: 1680 | Vel. Proyectil: 600 m/s",
    },
    # Fresnel: sequence x3 barrels, heat ramp (RPM baja, alpha sube)
    "volt_lmg_energy_01": {
        "category": "energy",
        "DpsTotal": 82.5, "AlphaTotal": 9,
        "Dps": {"Physical": 0, "Energy": 82.5, "Distortion": 0},
        "MaxPerMag": 1485, "Speed": 1100,
    },
    # Prism: heat ramp, 200-450 rpm, 5.75 dmg/shot
    "volt_shotgun_energy_01": {
        "category": "custom",
        "stats_line": "DPS: 19.2-43.1 | Alpha: 5.8\\nDmg/Cargador: 115 | Vel. Proyectil: 300 m/s",
    },
    # Tripledown: parallel x3 barrels, 12 dmg * 3 * 60 rpm / 60
    "none_pistol_ballistic_01": {
        "category": "ballistic",
        "DpsTotal": 36, "AlphaTotal": 36,
        "Dps": {"Physical": 36, "Energy": 0, "Distortion": 0},
        "MaxPerMag": 432, "Speed": 550,
        "DamageDropDist": 10,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_num(v):
    """Format a number: integer if whole, else minimal decimals (no trailing zeros)."""
    if v is None:
        return "0"
    if isinstance(v, float) and v != int(v):
        # Use up to 2 decimals, strip trailing zeros
        return f"{v:.2f}".rstrip('0').rstrip('.')
    return str(int(v))


def fmt_k(v):
    """Format a number with K suffix for values >= 1000. For DPS, Alpha, Dmg/Cargador."""
    if v is None:
        return "0"
    if isinstance(v, str):
        try:
            v = float(v)
        except ValueError:
            return v
    if abs(v) >= 1000:
        k = v / 1000
        rounded = round(k, 1)
        if rounded == int(rounded):
            return f"{int(rounded)}K"
        return f"{rounded:.1f}K"
    if isinstance(v, float) and v != int(v):
        return f"{v:.1f}"
    return str(int(v))


def detect_latest_version():
    """Return the most recently modified version directory name."""
    if not VERSIONS_DIR.is_dir():
        return None
    versions = [d for d in VERSIONS_DIR.iterdir() if d.is_dir()]
    if not versions:
        return None
    # Sort by modification time, newest first
    versions.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return versions[0].name


def get_damage_drop_distance(ammo):
    """Get the first non-zero DamageDropMinDistance value."""
    drop = ammo.get("DamageDropMinDistance", {})
    if not drop:
        return 0
    for key in ("Physical", "Energy", "Distortion", "Thermal", "Biochemical", "Stun"):
        v = drop.get(key, 0)
        if v and v > 0:
            return v
    return 0


def get_pellets(weapon_data):
    """Get PelletsPerShot from the first fire mode, default 1."""
    modes = weapon_data.get("Modes", [])
    if modes:
        return modes[0].get("PelletsPerShot", 1) or 1
    return weapon_data.get("PelletsPerShot", 1) or 1


def build_damage_label(dps_dict, alpha_dict):
    """Build the damage type label based on which types have DPS > 0."""
    active = {}
    for key, label in DAMAGE_LABELS.items():
        v = dps_dict.get(key, 0) or 0
        if v > 0:
            active[label] = v
    return active


def classify_weapon(item):
    """
    Classify a weapon into a category for stat formatting.
    Returns: 'beam', 'shotgun', 'ballistic', 'energy', 'mixed', 'launcher', or None to skip.
    """
    si = item.get("stdItem", {})
    weapon = si.get("Weapon", {})
    damage = weapon.get("Damage", {})
    ammo = si.get("Ammunition", {})
    beam = si.get("BeamData")

    dps_total = damage.get("DpsTotal") or 0
    alpha_total = damage.get("AlphaTotal") or 0
    dps_dict = damage.get("Dps", {})

    # Beam weapons
    if beam and (beam.get("FullDamageRange", 0) > 0 or beam.get("ZeroDamageRange", 0) > 0):
        if dps_total > 0:
            return "beam"

    if dps_total <= 0:
        return None

    # Count active damage types
    active_types = {k: v for k, v in dps_dict.items() if (v or 0) > 0}

    # Shotgun (check before launcher — shotguns have high alpha due to pellets)
    pellets = get_pellets(weapon)
    if pellets > 1:
        return "shotgun"

    # Launcher / Railgun: very high alpha, single damage type
    if alpha_total > 100 and len(active_types) <= 1:
        return "launcher"

    # Mixed damage
    if len(active_types) >= 2:
        return "mixed"

    # Ballistic vs Energy
    drop_dist = get_damage_drop_distance(ammo)
    if drop_dist > 0:
        return "ballistic"

    # Check if physical damage
    if (dps_dict.get("Physical") or 0) > 0:
        return "ballistic"

    return "energy"


def build_stats_block(item, category):
    """Build the stats lines for a weapon."""
    si = item.get("stdItem", {})
    weapon = si.get("Weapon", {})
    damage = weapon.get("Damage", {})
    ammo = si.get("Ammunition", {})
    beam = si.get("BeamData")

    dps_total = damage.get("DpsTotal") or 0
    alpha_total = damage.get("AlphaTotal") or 0
    max_per_mag = damage.get("MaxPerMag") or 0
    dps_dict = damage.get("Dps", {})
    alpha_dict = damage.get("Alpha", {})

    speed = ammo.get("Speed", 0) or 0
    penetration = ammo.get("MaxPenetrationThickness", 0) or 0
    drop_dist = get_damage_drop_distance(ammo)
    pellets = get_pellets(weapon)

    # Detect burst fire mode
    is_burst = False
    modes = weapon.get("Modes", [])
    if modes:
        fire_type = modes[0].get("FireType", "")
        if fire_type == "burst":
            is_burst = True

    # Sanitize absurd penetration values (data errors in scunpacked)
    # P4-AR: 5000m, Prism: 20m — clearly wrong
    if penetration > 10:
        penetration = 0

    active_dps = build_damage_label(dps_dict, alpha_dict)
    lines = []
    burst_tag = " (burst)" if is_burst else ""

    if category == "beam":
        # DPS line with breakdown
        if len(active_dps) == 1:
            label = list(active_dps.keys())[0]
            lines.append(f"DPS: {fmt_num(dps_total)} ({label})")
        else:
            parts = [f"{fmt_num(v)} {k}" for k, v in active_dps.items()]
            lines.append(f"DPS: {fmt_num(dps_total)} ({' + '.join(parts)})")
        full_range = beam.get("FullDamageRange", 0) or 0
        zero_range = beam.get("ZeroDamageRange", 0) or 0
        lines.append(f"Daño completo: 0-{fmt_num(full_range)}m | Cero daño: {fmt_num(zero_range)}m")

    elif category == "shotgun":
        if len(active_dps) >= 2:
            parts = [f"{fmt_num(v)} {k}" for k, v in active_dps.items()]
            lines.append(f"DPS: {fmt_num(dps_total)}{burst_tag} ({' + '.join(parts)}) | Alpha: {fmt_num(alpha_total)} | {pellets} perdigones")
        else:
            lines.append(f"DPS: {fmt_num(dps_total)}{burst_tag} | Alpha: {fmt_num(alpha_total)} | {pellets} perdigones")
        lines.append(f"Dmg/Cargador: {fmt_num(max_per_mag)} | Vel. Proyectil: {fmt_num(speed)} m/s")
        extras = []
        if 0 < penetration <= 10:
            extras.append(f"Penetración: {fmt_num(penetration)}m")
        if drop_dist > 0:
            extras.append(f"Caída daño: desde {fmt_num(drop_dist)}m")
        if extras:
            lines.append(" | ".join(extras))

    elif category == "ballistic":
        lines.append(f"DPS: {fmt_num(dps_total)}{burst_tag} | Alpha: {fmt_num(alpha_total)}")
        lines.append(f"Dmg/Cargador: {fmt_num(max_per_mag)} | Vel. Proyectil: {fmt_num(speed)} m/s")
        extras = []
        if penetration > 0:
            extras.append(f"Penetración: {fmt_num(penetration)}m")
        if drop_dist > 0:
            extras.append(f"Caída daño: desde {fmt_num(drop_dist)}m")
        if extras:
            lines.append(" | ".join(extras))

    elif category == "energy":
        lines.append(f"DPS: {fmt_num(dps_total)}{burst_tag} | Alpha: {fmt_num(alpha_total)}")
        lines.append(f"Dmg/Cargador: {fmt_num(max_per_mag)} | Vel. Proyectil: {fmt_num(speed)} m/s")
        if penetration > 0:
            lines.append(f"Penetración: {fmt_num(penetration)}m")

    elif category == "mixed":
        parts = [f"{fmt_num(v)} {k}" for k, v in active_dps.items()]
        lines.append(f"DPS: {fmt_num(dps_total)} ({' + '.join(parts)})")
        lines.append(f"Alpha: {fmt_num(alpha_total)} | Dmg/Cargador: {fmt_num(max_per_mag)}")
        lines.append(f"Vel. Proyectil: {fmt_num(speed)} m/s | Penetración: {fmt_num(penetration)}m")

    elif category == "launcher":
        lines.append(f"DPS: {fmt_num(dps_total)}{burst_tag} | Alpha: {fmt_num(alpha_total)}")
        lines.append(f"Dmg/Cargador: {fmt_num(max_per_mag)} | Vel. Proyectil: {fmt_num(speed)} m/s")
        lines.append(f"Penetración: {fmt_num(penetration)}m")

    return "\\n".join(lines)


def _startswith_any(text, prefixes):
    """Case-insensitive check if text starts with any of the prefixes."""
    lower = text.lower()
    return any(lower.startswith(p) for p in prefixes)


def parse_description(desc):
    """
    Parse a weapon description into (header_lines, old_stats_lines, flavor_text).
    Lines are separated by literal '\\n' in the ini value.
    """
    parts = desc.split("\\n")

    header = []
    old_stats = []
    flavor_parts = []
    section = "header"  # header -> stats -> flavor

    def _is_stat_line(s):
        """Check if a line is a stat line (old or own-injected)."""
        if _startswith_any(s, OLD_STATS_PREFIXES):
            return True
        if any(s.startswith(p) for p in OWN_STATS_PREFIXES):
            return True
        # Lines like "4 kg | Dmg/Cargador: 518.4" or "0.1 kg"
        if re.match(r'^\d+\.?\d*\s*kg\b', s):
            return True
        return False

    for part in parts:
        stripped = part.strip()

        if section == "header":
            if stripped == "":
                continue  # skip blank lines (will be compacted)
            is_header = _startswith_any(stripped, HEADER_PREFIXES)

            if is_header:
                header.append(part)
            elif _is_stat_line(stripped):
                section = "stats"
                old_stats.append(part)
            else:
                # No stats found, this is already flavor text
                section = "flavor"
                flavor_parts.append(part)
        elif section == "stats":
            is_header = _startswith_any(stripped, HEADER_PREFIXES)
            if _is_stat_line(stripped):
                old_stats.append(part)
            elif is_header:
                header.append(part)
            elif stripped == "":
                # Empty line — skip it (will be compacted later)
                continue
            else:
                section = "flavor"
                flavor_parts.append(part)
        elif section == "flavor":
            flavor_parts.append(part)

    # Clean up: simplify "Clase: energía (Laser)" -> "Clase: Laser"
    for i, h in enumerate(header):
        m = re.match(r'^(Clase:\s*)(?:[Ee]nerg[ií]a\s*\((.+?)\))(.*)$', h)
        if m:
            header[i] = m.group(1) + m.group(2) + m.group(3)

    # Clean up: remove trailing empty strings from header
    while header and header[-1].strip() == "":
        header.pop()

    # Clean up: remove leading empty strings from flavor
    while flavor_parts and flavor_parts[0].strip() == "":
        flavor_parts.pop(0)

    header_str = "\\n".join(header)
    flavor_str = "\\n".join(flavor_parts)

    return header_str, old_stats, flavor_str


def rebuild_description(header_str, stats_block, flavor_str):
    """Rebuild the full description value. Compact: no blank lines except before flavor."""
    # Remove any blank lines within header
    header_lines = [l for l in header_str.split("\\n") if l.strip() != ""]
    top = "\\n".join(header_lines)
    if stats_block:
        top += "\\n" + stats_block
    if flavor_str:
        return top + "\\n\\n" + flavor_str
    return top


# ---------------------------------------------------------------------------
# Tested source: load stats from spreadsheet CSV
# ---------------------------------------------------------------------------

# Category headers in the CSV to skip
EXCEL_CATEGORY_HEADERS = {
    "ASSAULT RIFLE", "LMG", "PISTOL", "SHOTGUN", "SMG", "SNIPER RIFLE",
    "HEAVY / MOUNTED", "GRENADE", "GADGET", "GRENADE LAUNCHER", "RAILGUN",
    "MOUNTED GUN", "ROCKET LAUNCHER",
}


def _parse_csv_float(val):
    """Parse a CSV numeric value, handling commas and empty strings."""
    if not val or not val.strip():
        return 0.0
    return float(val.strip().replace(",", ""))


def _build_scunpacked_name_map(fps_items):
    """
    Build a mapping from simplified display name -> base className.

    From scunpacked fps-items.json, extract WeaponPersonal items,
    strip quoted skin names from stdItem.Name, normalize nbsp,
    and pick the shortest className (base variant) for each name.
    """
    from collections import defaultdict
    name_to_cns = defaultdict(list)

    for item in fps_items:
        if item.get("type") != "WeaponPersonal":
            continue
        cn = item.get("className", "")
        name = item.get("stdItem", {}).get("Name", "")
        if not name or "PLACEHOLDER" in name:
            continue
        # Remove quoted skin suffix: "Rager", "Boneyard", etc.
        simplified = re.sub(r'"[^"]*"\s*', '', name).strip()
        # Normalize non-breaking spaces
        simplified = simplified.replace('\xa0', ' ')
        name_to_cns[simplified.lower()].append(cn)

    # For each name, pick the shortest className (base variant without skin suffix)
    name_map = {}
    for sname, cns in name_to_cns.items():
        cns.sort(key=len)
        name_map[sname] = cns[0]

    return name_map


def _build_name_map_from_ini(version_dir):
    """
    Build a mapping from simplified display name -> base className.

    Uses global_p4k_en.ini (English names from game files) because the Excel
    uses English weapon names. Falls back to global.ini (Spanish) if EN not found.
    Parses all item_Name{className}={display name} lines.
    """
    from collections import defaultdict
    name_to_cns = defaultdict(list)
    name_pattern = re.compile(r"^item_Name(.+?)=(.+)", re.IGNORECASE)

    # Prefer English (matches Excel names), fallback to Spanish
    en_path = version_dir / "sources" / "global_p4k_en.ini"
    es_path = version_dir / "output" / "global.ini"
    ini_path = en_path if en_path.is_file() else es_path
    print(f"Name mapping from: {ini_path}")

    with open(ini_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            m = name_pattern.match(line.rstrip("\n").rstrip("\r"))
            if not m:
                continue
            cn = m.group(1)
            # Skip _short name variants — they have no item_Desc counterpart
            if cn.lower().endswith("_short"):
                continue
            name = m.group(2).strip()
            if not name or "PLACEHOLDER" in name:
                continue
            # Remove quoted skin suffix: "Rager", "Boneyard", etc.
            simplified = re.sub(r'"[^"]*"\s*', '', name).strip()
            # Normalize non-breaking spaces
            simplified = simplified.replace('\xa0', ' ')
            if simplified:
                name_to_cns[simplified.lower()].append(cn)

    # For each name, pick the shortest className (base variant without skin suffix)
    name_map = {}
    for sname, cns in name_to_cns.items():
        cns.sort(key=len)
        name_map[sname] = cns[0]

    return name_map


def _build_penetration_map(fps_items):
    """Build className -> MaxPenetrationThickness from scunpacked data."""
    pen_map = {}
    for item in fps_items:
        if item.get("type") != "WeaponPersonal":
            continue
        cn = item.get("className", "").lower()
        ammo = item.get("stdItem", {}).get("Ammunition", {})
        pen = ammo.get("MaxPenetrationThickness", 0) or 0
        if pen > 100:
            pen = 0  # Sanitize absurd values
        if pen > 0:
            pen_map[cn] = pen
    return pen_map


def _match_excel_name(excel_name, name_map):
    """
    Try to match an Excel weapon name to a scunpacked className.

    First tries exact match, then tries matching with common extra words
    removed (Energy, Laser, Energy Assault, etc.).
    """
    key = excel_name.lower()

    # Collect all matches (exact + variants), pick shortest className
    candidates = []
    if key in name_map:
        candidates.append(name_map[key])

    # Try adding common prefixes/infixes that scunpacked uses
    # e.g., "Fresnel LMG" -> "Fresnel Energy LMG"
    #        "Prism Shotgun" -> "Prism Laser Shotgun"
    #        "Parallax Rifle" -> "Parallax Energy Assault Rifle"
    #        "Pulse Pistol" -> "Pulse Laser Pistol"
    variants = []
    words = key.split()
    if len(words) >= 2:
        base = words[0]
        weapon_type = words[-1]
        # Try "Base Energy Type", "Base Laser Type", "Base Energy Assault Type"
        for infix in ["energy", "laser", "energy assault"]:
            variant = f"{base} {infix} {weapon_type}"
            variants.append(variant)
        # Try "Base Laser Type" for compound names like "Pulse Pistol"
        # Also try just the first word + type with all known infixes
    for v in variants:
        if v in name_map:
            candidates.append(name_map[v])

    if not candidates:
        return None
    # Pick shortest className (base variant)
    candidates.sort(key=len)
    return candidates[0]


def classify_weapon_tested(fire_mode, pellets, alpha, dps_sustained, dps_burst, drop_dist):
    """
    Classify a weapon from tested/Excel data.

    Returns: 'beam', 'shotgun', 'ballistic', 'energy', 'launcher', or None.
    """
    mode_lower = fire_mode.lower()

    if "beam" in mode_lower:
        return "beam"

    if "charge" in mode_lower and alpha > 100:
        return "launcher"

    if pellets > 1:
        return "shotgun"

    if drop_dist > 0:
        return "ballistic"

    return "energy"


def _fire_mode_label(mode_str):
    """Convert raw fire mode string to a clean label."""
    ml = mode_str.lower().strip()
    if "charge burst" in ml:
        return "Full"
    if "charge" in ml:
        return "Full"
    if "combined s" in ml:
        return "Hot"  # combined slug mode = hot (Prism)
    if "combined" in ml:
        return "Auto"  # combined damage types = auto mode
    if "heat 50%" in ml or "hot" in ml:
        return "Hot"
    if ml.startswith("rapid") or ml.startswith("auto"):
        return "Auto"
    if ml.startswith("single") or ml.startswith("semi"):
        return "Semi"
    if "burst 5" in ml:
        return "Burst5"
    if "burst 3" in ml or ml.startswith("burst"):
        return "Burst"
    if "rapid burst" in ml:
        return "Burst"
    if ml.startswith("beam"):
        return "Beam"
    if ml.startswith("slug"):
        return "Slug"
    if ml.startswith("double"):
        return "Doble"
    return ml.split()[0].capitalize()


def build_stats_block_tested(item, category):
    """
    Build stats block for tested source data.

    Format: one line per fire mode with label, then shared stats lines.
    """
    si = item.get("stdItem", {})
    weapon = si.get("Weapon", {})
    damage = weapon.get("Damage", {})
    ammo = si.get("Ammunition", {})

    dps_total = damage.get("DpsTotal") or 0
    alpha_total = damage.get("AlphaTotal") or 0
    max_per_mag = damage.get("MaxPerMag") or 0
    speed = ammo.get("Speed", 0) or 0
    drop_dist = get_damage_drop_distance(ammo)

    # Get all modes from item
    all_modes = item.get("_all_modes", [])

    lines = []

    # Collect mode drop info: (label, drop_start, min_pct, min_at, range)
    mode_drops = []

    if all_modes and len(all_modes) >= 1:
        for m in all_modes:
            label = _fire_mode_label(m["mode"])
            if label is None:
                continue
            m_speed = m.get("speed", 0) or 0
            dps_parts = [f"[{label}] DPS: {fmt_k(m['dps_sus'])} | Alpha: {fmt_k(m['alpha'])}"]
            if m_speed > 0:
                dps_parts.append(f"{fmt_num(m_speed)} m/s")
            lines.append(" | ".join(dps_parts))

            m_dd = m.get("drop_dist", 0) or 0
            m_dm = m.get("drop_pm", 0) or 0
            m_alpha = m.get("alpha", 0) or 0
            m_min_dmg = m.get("min_dmg", 0) or 0
            m_range = m.get("range", 0) or 0
            m_drop_zero_col = m.get("drop_zero", 0) or 0

            if m_dd > 0 and m_dm > 0 and m_alpha > 0:
                if m_min_dmg > 0 and m_min_dmg < m_alpha:
                    min_at = m_dd + ((m_alpha - m_min_dmg) / m_dm)
                    min_pct = round(m_min_dmg / m_alpha * 100)
                    if min_at > m_range and m_range > 0:
                        # Min damage never reached — calc % at max range
                        dmg_at_r = m_alpha - (m_range - m_dd) * m_dm
                        pct_at_r = round(max(0, dmg_at_r) / m_alpha * 100)
                        mode_drops.append((label, m_dd, pct_at_r, int(m_range), int(m_range)))
                    else:
                        mode_drops.append((label, m_dd, min_pct, int(min_at), int(m_range)))
                elif m_min_dmg >= m_alpha:
                    # Min damage equals alpha — no real drop
                    mode_drops.append((label, m_dd, 100, int(m_range), int(m_range)))
                else:
                    # No min damage — drops to 0
                    if m_drop_zero_col > 0:
                        zero_at = m_drop_zero_col
                    else:
                        zero_at = m_dd + (m_alpha / m_dm)
                        if m_range > 0 and zero_at > m_range:
                            zero_at = m_range
                    mode_drops.append((label, m_dd, 0, int(zero_at), int(m_range)))
            elif m_dd > 0:
                # Has drop start but no rate
                mode_drops.append((label, m_dd, -1, 0, int(m_range)))
            # else: no drop data for this mode
    else:
        fire_mode = weapon.get("FireMode", "")
        label = _fire_mode_label(fire_mode) or "Auto"
        dps_parts = [f"[{label}] DPS: {fmt_k(dps_total)} | Alpha: {fmt_k(alpha_total)}"]
        if speed > 0:
            dps_parts.append(f"{fmt_num(speed)} m/s")
        lines.append(" | ".join(dps_parts))

        ammo_range = ammo.get("Range", 0) or 0
        if drop_dist > 0:
            drop_pm_val = next(iter((ammo.get("DamageDropPerMeter") or {}).values()), 0)
            min_dmg_val = next(iter((ammo.get("DamageDropMinDamage") or {}).values()), 0)
            if drop_pm_val > 0 and alpha_total > 0:
                if min_dmg_val > 0 and min_dmg_val < alpha_total:
                    min_at = drop_dist + ((alpha_total - min_dmg_val) / drop_pm_val)
                    min_pct = round(min_dmg_val / alpha_total * 100)
                    if min_at > ammo_range and ammo_range > 0:
                        dmg_at_r = alpha_total - (ammo_range - drop_dist) * drop_pm_val
                        pct_at_r = round(max(0, dmg_at_r) / alpha_total * 100)
                        mode_drops.append((label, drop_dist, pct_at_r, int(ammo_range), int(ammo_range)))
                    else:
                        mode_drops.append((label, drop_dist, min_pct, int(min_at), int(ammo_range)))
                else:
                    drop_zero_col = 0
                    # check col531 via ammo
                    if drop_pm_val > 0:
                        zero_at = drop_dist + (alpha_total / drop_pm_val)
                        if ammo_range > 0 and zero_at > ammo_range:
                            zero_at = ammo_range
                        mode_drops.append((label, drop_dist, 0, int(zero_at), int(ammo_range)))
            else:
                mode_drops.append((label, drop_dist, -1, 0, int(ammo_range)))

    # Shared stats: Dmg/Cargador
    if max_per_mag > 0:
        lines.append(f"Dmg/Cargador: {fmt_k(max_per_mag)}")

    # Mass line (separate)
    mass = si.get("Mass", 0) or 0
    mass_loaded = item.get("_mass_loaded", 0) or 0
    if mass_loaded > 0 and mass > 0 and abs(mass_loaded - mass) > 0.01:
        lines.append(f"Cargado: {fmt_num(mass_loaded)} kg | Descargado: {fmt_num(mass)} kg")
    elif mass > 0:
        lines.append(f"{fmt_num(mass)} kg")

    # Damage distance line
    max_range = ammo.get("Range", 0) or 0
    if all_modes:
        for m in all_modes:
            mr = m.get("range", 0) or 0
            if mr > max_range:
                max_range = mr

    if mode_drops:
        # mode_drops: (label, drop_start, min_pct, min_at_dist, range)
        # min_pct: 0=drops to zero, >0=floor pct, 100=no real drop, -1=unknown rate
        d = mode_drops[0]
        drop_start = d[1]

        # Check if all modes produce same result
        drop_results = [(md[2], md[3]) for md in mode_drops]
        all_same = len(set(drop_results)) <= 1

        if all_same or len(mode_drops) == 1:
            pct, dist, rng = d[2], d[3], d[4]
            if pct == 0:
                lines.append(f"[Red. daño] 100% {fmt_num(drop_start)}m | 0% {fmt_num(dist)}m")
            elif pct == 100:
                lines.append(f"[Red. daño] Max: {fmt_num(rng)}m")
            elif pct == -1:
                lines.append(f"[Red. daño] 100% {fmt_num(drop_start)}m | 0% {fmt_num(rng)}m")
            elif dist - drop_start < 5:
                # Very short drop (< 5m) — simplify: show min% at drop start
                if dist >= rng:
                    lines.append(f"[Red. daño] {pct}% {fmt_num(drop_start)}m")
                else:
                    lines.append(f"[Red. daño] {pct}% {fmt_num(drop_start)}m | 0% {fmt_num(rng)}m")
            elif dist >= rng:
                # Min pct reached at or beyond max range — no separate 0% line
                lines.append(f"[Red. daño] 100% {fmt_num(drop_start)}m | {pct}% {fmt_num(dist)}m")
            else:
                lines.append(f"[Red. daño] 100% {fmt_num(drop_start)}m | {pct}% {fmt_num(dist)}m | 0% {fmt_num(rng)}m")
        else:
            # Different per mode
            parts = [f"100% {fmt_num(drop_start)}m"]
            for label, dd, pct, dist, rng in mode_drops:
                if pct == 0:
                    parts.append(f"{label} 0% {fmt_num(dist)}m")
                elif pct > 0 and pct < 100:
                    parts.append(f"{label} {pct}% {fmt_num(dist)}m")
            # Add 0% at max range if any mode has min_pct > 0
            any_has_floor = any(md[2] > 0 and md[2] < 100 for md in mode_drops)
            if any_has_floor:
                rng = max(md[4] for md in mode_drops)
                parts.append(f"0% {fmt_num(rng)}m")
            lines.append("[Red. daño] " + " | ".join(parts))
    else:
        if max_range > 0:
            lines.append(f"[Red. daño] Max: {fmt_num(max_range)}m")

    return "\\n".join(lines)


def load_tested_weapons(version_dir, global_ini_path):
    """
    Load weapon stats from tested spreadsheet CSV.

    Args:
        version_dir: Path to the version directory.
        global_ini_path: Path to global.ini (used for name mapping).
        fps_items: Optional list from fps-items.json (used for penetration data
                   and skin variant mapping). Can be None.

    Returns: dict of className -> (item_dict, category, stats_block)
    """
    csv_path = version_dir / "sources" / "tested" / "sin_crafteo" / "tab_Item.csv"
    if not csv_path.is_file():
        print(f"ERROR: {csv_path} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"CSV: {csv_path}")

    # Build name mapping from English game files (global_p4k_en.ini)
    name_map = _build_name_map_from_ini(version_dir)

    # Penetration removed — only came from scunpacked, not from game files or Excel

    # Parse CSV: group rows by weapon (sub-rows have empty col 0)
    raw_weapons = []  # list of (name, [(row_data), ...])
    current_name = None
    current_rows = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            if len(row) < 20:
                continue

            name = row[0].strip().replace('\xa0', ' ')

            if name:
                # Check if it's a category header
                if name in EXCEL_CATEGORY_HEADERS:
                    # Save previous weapon if any
                    if current_name and current_rows:
                        raw_weapons.append((current_name, current_rows))
                    current_name = None
                    current_rows = []
                    continue

                # Check if it looks like a sub-header row (all 1's or empty DPS)
                dps_val = row[19].strip() if len(row) > 19 else ''
                dps_burst_val = row[20].strip() if len(row) > 20 else ''
                fire_mode = row[7].strip() if len(row) > 7 else ''
                if not fire_mode or (dps_val in ('', '1') and dps_burst_val in ('', '1')):
                    # Sub-header or separator row
                    if current_name and current_rows:
                        raw_weapons.append((current_name, current_rows))
                    current_name = None
                    current_rows = []
                    continue

                # New weapon
                if current_name and current_rows:
                    raw_weapons.append((current_name, current_rows))
                current_name = name
                current_rows = [row]
            else:
                # Sub-row (alternate fire mode)
                if current_name:
                    current_rows.append(row)

        # Don't forget last weapon
        if current_name and current_rows:
            raw_weapons.append((current_name, current_rows))

    # Process each weapon: select best fire mode
    weapons = {}
    skipped_zero_dps = 0
    skipped_no_match = 0
    matched = 0

    for weapon_name, rows in raw_weapons:
        # Parse all modes for this weapon
        parsed_modes = []
        weapon_mass = 0  # mass from first row, propagate to sub-rows
        weapon_mass_loaded = 0
        for row in rows:
            fm = row[7].strip() if len(row) > 7 else ''
            if not fm:
                continue
            try:
                dps_s = _parse_csv_float(row[19]) if len(row) > 19 and row[19].strip() else 0
            except ValueError:
                dps_s = 0
            try:
                dps_b = _parse_csv_float(row[20]) if len(row) > 20 and row[20].strip() else 0
            except ValueError:
                dps_b = 0
            # Fallback: if sustained is 0 but burst exists, use burst
            if dps_s <= 0 and dps_b > 0:
                dps_s = dps_b
            try:
                a = _parse_csv_float(row[16]) if len(row) > 16 and row[16].strip() else 0
            except ValueError:
                a = 0
            pel = int(_parse_csv_float(row[12])) if len(row) > 12 and row[12].strip() else 1
            if pel < 1:
                pel = 1
            m_speed = _parse_csv_float(row[8]) if len(row) > 8 else 0
            m_range = _parse_csv_float(row[10]) if len(row) > 10 else 0
            m_mass = _parse_csv_float(row[5]) if len(row) > 5 and row[5].strip() else 0
            m_mass_loaded = _parse_csv_float(row[6]) if len(row) > 6 and row[6].strip() else 0
            if m_mass > 0:
                weapon_mass = m_mass  # first row sets the mass
            if m_mass_loaded > 0:
                weapon_mass_loaded = m_mass_loaded
            m_drop_dist = _parse_csv_float(row[26]) if len(row) > 26 and row[26].strip() else 0
            m_drop_pm = _parse_csv_float(row[27]) if len(row) > 27 and row[27].strip() else 0
            m_drop_zero = _parse_csv_float(row[531]) if len(row) > 531 and row[531].strip() else 0
            m_min_dmg = _parse_csv_float(row[28]) if len(row) > 28 and row[28].strip() else 0
            parsed_modes.append({"row": row, "mode": fm, "dps_sus": dps_s, "dps_burst": dps_b, "alpha": a, "pellets": pel, "speed": m_speed, "range": m_range, "mass": weapon_mass, "drop_dist": m_drop_dist, "drop_pm": m_drop_pm, "drop_zero": m_drop_zero, "min_dmg": m_min_dmg})

        if not parsed_modes:
            skipped_zero_dps += 1
            continue

        # Detect multi-mode type and select primary/secondary
        mode_types = [m["mode"].lower() for m in parsed_modes]
        has_combined = any("combined" in mt for mt in mode_types)
        has_heat = any("heat 50%" in mt for mt in mode_types)
        has_charge = any("charge" in mt for mt in mode_types)

        # Force heat detection for weapons with slug->pellet heat ramp (Prism)
        if not has_heat and "slug" in mode_types and len(parsed_modes) >= 2:
            has_heat = True

        # Select primary mode
        if has_combined:
            primary = next(m for m in parsed_modes if "combined" in m["mode"].lower())
        else:
            primary = max(parsed_modes, key=lambda m: m["dps_sus"])

        if primary["dps_sus"] <= 0:
            skipped_zero_dps += 1
            continue

        # Build multi-mode DPS tag
        multi_mode_tag = ""
        multi_mode_alpha = ""
        if has_heat and len(parsed_modes) >= 2:
            # Standard heat: "Heat" + "Heat 50%"
            cold = next((m for m in parsed_modes if "heat" in m["mode"].lower() and "50%" not in m["mode"]), None)
            hot = next((m for m in parsed_modes if "50%" in m["mode"]), None)
            # Slug->pellet heat (Prism): "Slug" is cold, other mode is hot
            if not cold or not hot:
                slug = next((m for m in parsed_modes if "slug" in m["mode"].lower()), None)
                other = next((m for m in parsed_modes if "slug" not in m["mode"].lower() and "combined" not in m["mode"].lower()), None)
                if slug and other:
                    cold = slug
                    hot = other
            if cold and hot and abs(cold["dps_sus"] - hot["dps_sus"]) > 1:
                primary = cold  # Use cold as primary (starting DPS)
                multi_mode_tag = f" (caliente: {fmt_num(hot['dps_sus'])})"
                if abs(cold["alpha"] - hot["alpha"]) > 0.5:
                    multi_mode_alpha = f"{fmt_num(cold['alpha'])}-{fmt_num(hot['alpha'])}"
        elif has_charge and not has_combined:
            normal = next((m for m in parsed_modes if "charge" not in m["mode"].lower()), None)
            charged = next((m for m in parsed_modes if "charge" in m["mode"].lower()), None)
            if normal and charged and charged["dps_sus"] > 0:
                primary = normal  # Use normal as primary
                multi_mode_tag = f" (cargado: {fmt_num(charged['dps_sus'])})"
        elif len(parsed_modes) >= 2 and not has_combined:
            # Selectable modes (Rapid/Single, Double/Single, etc.)
            modes_by_dps = sorted(parsed_modes, key=lambda m: m["dps_sus"], reverse=True)
            primary = modes_by_dps[0]
            secondary = modes_by_dps[1]
            if secondary["dps_sus"] > 0 and secondary["dps_sus"] != primary["dps_sus"]:
                # Describe secondary mode briefly
                sec_name = secondary["mode"].split()[0].lower()
                if sec_name in ("single", "semi"):
                    sec_label = "semi"
                elif sec_name in ("burst"):
                    sec_label = "burst"
                elif sec_name in ("rapid", "auto"):
                    sec_label = "auto"
                elif sec_name in ("double"):
                    sec_label = "doble"
                else:
                    sec_label = sec_name
                multi_mode_tag = f" / {fmt_num(secondary['dps_sus'])} ({sec_label})"

        # Extract stats from primary row
        best_row = primary["row"]
        fire_mode = primary["mode"]
        alpha = primary["alpha"]
        pellets = primary["pellets"]
        dps_sustained = primary["dps_sus"]
        dps_burst = primary["dps_burst"]
        speed = _parse_csv_float(best_row[8]) if len(best_row) > 8 else 0
        range_m = _parse_csv_float(best_row[10]) if len(best_row) > 10 else 0
        drop_dist = _parse_csv_float(best_row[26]) if len(best_row) > 26 else 0
        drop_pm = _parse_csv_float(best_row[27]) if len(best_row) > 27 else 0
        drop_min = _parse_csv_float(best_row[28]) if len(best_row) > 28 else 0
        dmg_mag = _parse_csv_float(best_row[98]) if len(best_row) > 98 else 0

        # Match to className
        class_name = _match_excel_name(weapon_name, name_map)
        if not class_name:
            skipped_no_match += 1
            print(f"  WARNING: No className match for '{weapon_name}'")
            continue

        class_name_lower = class_name.lower()

        # Classify weapon
        category = classify_weapon_tested(fire_mode, pellets, alpha, dps_sustained, dps_burst, drop_dist)
        if category is None:
            skipped_zero_dps += 1
            continue

        # Detect burst
        is_burst = "burst" in fire_mode.lower()

        # Build list of all displayable modes
        # If a Combined mode exists, use it instead of the individual damage types
        combined = [m for m in parsed_modes if "combined" in m["mode"].lower() and m["dps_sus"] > 0]
        has_slug = any("slug" in m["mode"].lower() for m in parsed_modes)
        if combined and not has_slug:
            # Pure combined (e.g., Killshot): only show combined
            all_modes = combined
        elif combined and has_slug:
            # Slug + Combined (e.g., Prism): show Slug as cold, Combined as hot
            slug_modes = [m for m in parsed_modes if "slug" in m["mode"].lower() and m["dps_sus"] > 0]
            all_modes = slug_modes + combined
        else:
            all_modes = [m for m in parsed_modes if m["dps_sus"] > 0]

        # Remove duplicate modes with same DPS (e.g., Quartz Beam Heat + Beam Heat 50% both 225)
        deduped = []
        seen_dps = set()
        for m in all_modes:
            key = (round(m["dps_sus"], 1), round(m["alpha"], 1))
            if key not in seen_dps:
                seen_dps.add(key)
                deduped.append(m)
        all_modes = deduped

        # Get mass from primary mode
        mass = primary.get("mass", 0) or 0

        # Build item dict in scunpacked-compatible format
        item = {
            "className": class_name,
            "_all_modes": all_modes,
            "_mass_loaded": weapon_mass_loaded,
            "stdItem": {
                "Mass": mass,
                "Weapon": {
                    "Damage": {
                        "DpsTotal": dps_sustained,
                        "AlphaTotal": alpha,
                        "MaxPerMag": dmg_mag,
                        "Dps": {},
                        "Alpha": {},
                    },
                    "Modes": [{"FireType": "burst" if is_burst else fire_mode.lower(), "PelletsPerShot": pellets}],
                    "FireMode": fire_mode,
                },
                "Ammunition": {
                    "Speed": speed,
                    "Range": range_m,
                    "DamageDropMinDistance": {"Physical": drop_dist} if drop_dist > 0 else {},
                    "DamageDropPerMeter": {"Physical": drop_pm} if drop_pm > 0 else {},
                    "DamageDropMinDamage": {"Physical": drop_min} if drop_min > 0 else {},
                },
            },
        }

        # Build stats block
        stats_block = build_stats_block_tested(item, category)
        if stats_block is None:
            continue

        # Store for ALL skins of this base weapon
        # The base className maps to the item_Desc key
        weapons[class_name_lower] = (item, category, stats_block)

        # Also map all skin variants — use the shortest common prefix
        # Strip known skin suffixes to find base (e.g., _blue01 -> base)
        base_cn = re.sub(
            r'_(blue\d*|black\d*|gold\d*|green\d*|white\d*|tan\d*|red\d*|grey\d*|brown\d*|pink\d*|chromic\d*|'
            r'engraved\d*|iron|mat\d*|tint\d*|store\d*|collector\d*|firerats\d*|luminalia\d*|xenothreat\d*|'
            r'iae\d*|headhunters\d*|yellow\w*|blue_\w+|contestedzonereward|300|civilian\w*|spc)$',
            '', class_name_lower, flags=re.IGNORECASE)
        for sname, cn in name_map.items():
            cn_lower = cn.lower()
            if cn_lower.startswith(base_cn) and cn_lower != class_name_lower and cn_lower not in weapons:
                # Skin variant — copy same stats
                skin_item = dict(item)
                skin_item["className"] = cn
                weapons[cn_lower] = (skin_item, category, stats_block)

        matched += 1

    # Also map all skins from scunpacked that share a base className
    # We need to find ALL classNames in fps_items that share the same base
    base_classes = {}  # base_cn_lower -> stats tuple
    for cn_lower, val in list(weapons.items()):
        base_classes[cn_lower] = val

    # Map skin variants from name_map (built from game files)
    for sname, cn in name_map.items():
        cn_lower = cn.lower()
        if cn_lower in weapons:
            continue
        for base_cn, val in base_classes.items():
            if cn_lower.startswith(base_cn + "_") or cn_lower.startswith(base_cn):
                skin_item = dict(val[0])
                skin_item["className"] = cn
                weapons[cn_lower] = (skin_item, val[1], val[2])
                break

    print(f"Weapons matched from CSV: {matched}")
    print(f"  Total entries (incl. skins): {len(weapons)}")
    print(f"  Skipped (zero DPS): {skipped_zero_dps}")
    print(f"  Skipped (no className match): {skipped_no_match}")
    print()

    return weapons


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_scunpacked_weapons(fps_items):
    """
    Load weapon stats from scunpacked fps-items.json (original behavior).

    Returns: dict of className -> (item_dict, category, stats_block)
    """
    weapons = {}
    skipped_no_data = 0
    skipped_zero_dps = 0
    skipped_penetration = 0

    for item in fps_items:
        if item.get("type") != "WeaponPersonal":
            continue

        class_name = item.get("className", "").lower()
        si = item.get("stdItem", {})
        weapon = si.get("Weapon")

        # Check for manual override (base className, strip skin suffixes)
        override = None
        for base_cn, ov in MANUAL_OVERRIDES.items():
            if class_name == base_cn or class_name.startswith(base_cn + "_"):
                override = ov
                break

        if override:
            category = override["category"]
            if category == "custom":
                stats_block = override["stats_line"]
            else:
                if not weapon:
                    weapon = {"Damage": {}, "Modes": []}
                    si["Weapon"] = weapon
                damage = weapon.setdefault("Damage", {})
                damage["DpsTotal"] = override["DpsTotal"]
                damage["AlphaTotal"] = override["AlphaTotal"]
                damage["Dps"] = override["Dps"]
                damage["MaxPerMag"] = override.get("MaxPerMag", 0)
                ammo = si.setdefault("Ammunition", {})
                if "Speed" in override:
                    ammo["Speed"] = override["Speed"]
                if "Penetration" in override:
                    ammo["MaxPenetrationThickness"] = override["Penetration"]
                if "DamageDropDist" in override:
                    ammo["DamageDropMinDistance"] = {"Physical": override["DamageDropDist"]}
                if "BeamData" in override:
                    si["BeamData"] = override["BeamData"]
                stats_block = build_stats_block(item, category)
        else:
            if not weapon:
                skipped_no_data += 1
                continue

            damage = weapon.get("Damage", {})
            dps_total = damage.get("DpsTotal") or 0
            has_beam = "BeamData" in si

            if dps_total <= 0 and not has_beam:
                skipped_zero_dps += 1
                continue

            if has_beam and dps_total <= 0:
                beam = si.get("BeamData", {})
                if not beam.get("FullDamageRange") and not beam.get("ZeroDamageRange"):
                    skipped_zero_dps += 1
                    continue

            category = classify_weapon(item)
            if category is None:
                skipped_zero_dps += 1
                continue

            stats_block = build_stats_block(item, category)

        if stats_block is None:
            skipped_penetration += 1
            continue

        weapons[class_name] = (item, category, stats_block)

    print(f"Weapons with stats: {len(weapons)}")
    print(f"  Skipped (no weapon data): {skipped_no_data}")
    print(f"  Skipped (zero DPS / non-combat): {skipped_zero_dps}")
    print(f"  Skipped (bad penetration data): {skipped_penetration}")
    print()

    return weapons


def main():
    parser = argparse.ArgumentParser(description="Inject real weapon stats into global.ini")
    parser.add_argument("--version", type=str, default=None,
                        help="Version directory name (default: auto-detect latest)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show changes without writing")
    parser.add_argument("--source", choices=["tested", "dcb", "game", "scunpacked"], default="tested",
                        help="Data source: tested (FPS from CSV), dcb (ship weapons from Game2.dcb)")
    parser.add_argument("--output", type=str, default=None,
                        help="Write to a different file instead of overwriting global.ini")
    parser.add_argument("--verify", action="store_true",
                        help="Run verification: no text lost, no orphans, no dupes, idempotent")
    args = parser.parse_args()

    # Resolve version
    version = args.version or detect_latest_version()
    if not version:
        print("ERROR: No version directory found.", file=sys.stderr)
        sys.exit(1)

    version_dir = VERSIONS_DIR / version
    fps_json_path = version_dir / "sources" / "scunpacked" / "fps-items.json"
    global_ini_path = version_dir / "output" / "global.ini"

    if not global_ini_path.is_file():
        print(f"ERROR: {global_ini_path} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Version: {version}")
    print(f"Source: {args.source}")
    print(f"global.ini: {global_ini_path}")
    print()

    # Load weapons based on source
    if args.source == "tested":
        weapons = load_tested_weapons(version_dir, global_ini_path)
    elif args.source == "dcb":
        from extract_ship_weapons import load_dcb_ship_weapons
        dcb_path = BASE_DIR / "Game2.dcb"
        weapons = load_dcb_ship_weapons(str(dcb_path))
        if not weapons:
            print("ERROR: No se pudieron extraer armas del DCB.", file=sys.stderr)
            sys.exit(1)
    elif args.source == "game":
        print("ERROR: --source game no implementado todavía. Usa --source tested o dcb.",
              file=sys.stderr)
        sys.exit(1)
    else:
        print("ERROR: --source scunpacked desactivado. Usa --source tested o dcb.",
              file=sys.stderr)
        sys.exit(1)

    # Load global.ini (UTF-8 with BOM)
    with open(global_ini_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    # Build index: lowercase className -> set of line indices
    # Pattern: item_Desc{className}=
    desc_pattern = re.compile(r"^item_Desc(.+?)=", re.IGNORECASE)

    patched = 0
    not_found = []
    modified_lines = list(lines)

    # --- Clean up MrKraken X-prefixed blueprint markers ---
    # These are untranslated template fields like XMAnFacturer, XTipo, XXMAGAZINE, etc.
    blueprint_cleaned = 0
    _bp_replacements = [
        (r"XMAnFacturer:\s*GreyCat\s+Industrialxx", "Fabricante: Greycat Industrial"),
        (r"XTipo de art[ií]culo:\s*Utility", "Tipo de artículo: Utilidad"),
        (r"(?<=\\n)Class:\s*Gadget", "Clase: Gadget"),
        (r"XXMAZ[AG]ZINE\s+TIEMPLE\s+de\s+fuego:\s*N\s*/\s*A\s*\(Beam\)\s*", "Batería: Integrada"),
        (r"XEFective\s+Range:\s*[\d.]+\s*M\s*", ""),
        (r"XXE\s+Pyro\s+de\s+Greycat", "El Pyro de Greycat"),
    ]
    for i, line in enumerate(modified_lines):
        if "XMAnFacturer" not in line and "XXMAZ" not in line:
            continue
        new_line = line
        for pattern, replacement in _bp_replacements:
            new_line = re.sub(pattern, replacement, new_line, flags=re.IGNORECASE)
        # Clean up artifacts: double \\n from removed lines, trailing spaces before \\n
        new_line = re.sub(r" \\n", r"\\n", new_line)
        new_line = re.sub(r"(\\n){3,}", r"\\n\\n", new_line)
        if new_line != line:
            modified_lines[i] = new_line
            blueprint_cleaned += 1

    # Keep immutable copy for skin lookups (weapons gets consumed)
    base_weapons = dict(weapons)

    for i, line in enumerate(lines):
        m = desc_pattern.match(line)
        if not m:
            continue

        key_classname = m.group(1).lower()
        # Skip magazine descriptions — they get their own separate injection
        if "_mag" in key_classname:
            continue
        # Strip ,P suffix and try exact match first
        key_clean = re.sub(r',p$', '', key_classname, flags=re.IGNORECASE)
        # Helper: get from weapons OR base_weapons (never consumed)
        def _get_weapon(k):
            v = weapons.get(k)
            if v is not None:
                return v
            return base_weapons.get(k)

        match = _get_weapon(key_classname) or _get_weapon(key_clean)
        # Fuzzy: strip known skin suffixes and try base match
        if not match:
            key_base = re.sub(
                r'_(iae\d+|blue_gold_?\d*|blue_white\d*|shin\d*|cen\d*|imp\d*|iron|mat\d*|,p)$',
                '', key_clean, flags=re.IGNORECASE)
            match = _get_weapon(key_base)
            if not match:
                for suffix in ['_01', '_02', '_03', '']:
                    match = _get_weapon(key_base + suffix)
                    if match:
                        break
        # Fuzzy: try swapping _02 <-> _01 suffix (e.g., silenced/civilian variants)
        if not match:
            swap = re.sub(r'_02\b', '_01', key_clean)
            if swap != key_clean:
                match = _get_weapon(swap)
            if not match:
                swap = re.sub(r'_01\b', '_02', key_clean)
                if swap != key_clean:
                    match = _get_weapon(swap)
        # Fuzzy: try if any base weapon className is a prefix (or vice versa)
        if not match:
            for base_cn, val in base_weapons.items():
                if val is None:
                    continue
                if key_clean.startswith(base_cn + "_") or key_clean.startswith(base_cn):
                    match = val
                    break
                # Reverse: base weapon is more specific (e.g., _civilian variant)
                if base_cn.startswith(key_base + "_") or base_cn.startswith(key_base):
                    match = val
                    break
        if not match:
            continue

        item, category, stats_block = match

        # Extract key=value
        eq_pos = line.index("=")
        key_part = line[:eq_pos + 1]
        value_part = line[eq_pos + 1:].rstrip("\n").rstrip("\r")

        # Parse description
        header_str, old_stats, flavor_str = parse_description(value_part)

        # Rebuild with new stats
        new_value = rebuild_description(header_str, stats_block, flavor_str)
        new_line = key_part + new_value + "\n"

        if new_line != line:
            if args.dry_run and patched < 5:
                print(f"--- {item['className']} [{category}]")
                print(f"  OLD: ...{value_part[:200]}...")
                print(f"  NEW: ...{new_value[:200]}...")
                print()

            modified_lines[i] = new_line
            patched += 1

        # Mark as found (don't consume — skins share base)
        if key_classname in weapons:
            weapons[key_classname] = None

    # --- Patch magazine descriptions with mass ---
    mag_patched = 0
    if args.source == "tested":
        mag_csv = version_dir / "sources" / "tested" / "sin_crafteo" / "tab_Magazine.csv"
        if mag_csv.is_file():
            mag_mass = {}
            with open(mag_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    filename = row[13].strip().lower() if len(row) > 13 else ""
                    mass_str = row[12].strip() if len(row) > 12 else ""
                    if filename and mass_str:
                        try:
                            mag_mass[filename] = float(mass_str)
                        except ValueError:
                            pass


            # Also index by name from p4k for fallback matching
            mag_name_mass = {}  # english name lower -> mass
            en_ini = version_dir / "sources" / "global_p4k_en.ini"
            mag_name_to_cn = {}  # name -> className
            if en_ini.is_file():
                with open(en_ini, "r", encoding="utf-8-sig") as f:
                    for ln in f:
                        m = re.match(r"item_Name(.+?)=(.+)", ln.strip(), re.IGNORECASE)
                        if m:
                            mag_name_to_cn[m.group(2).strip().replace('\xa0', ' ').lower()] = m.group(1).lower()
            # Build reverse: className from ini -> mass from CSV (via name)
            mag_cn_from_name = {}
            mag_csv2 = version_dir / "sources" / "tested" / "sin_crafteo" / "tab_Magazine.csv"
            if mag_csv2.is_file():
                with open(mag_csv2, "r", encoding="utf-8") as f:
                    reader2 = csv.reader(f)
                    next(reader2)
                    for row in reader2:
                        mname = row[0].strip().replace('\xa0', ' ').lower() if row[0].strip() else ""
                        mmass = row[12].strip() if len(row) > 12 else ""
                        if mname and mmass:
                            cn = mag_name_to_cn.get(mname)
                            if cn:
                                try:
                                    mag_cn_from_name[cn] = float(mmass)
                                except ValueError:
                                    pass

            mag_pattern = re.compile(r"^item_Desc(.+_mag[^=]*)=", re.IGNORECASE)
            for i, line in enumerate(modified_lines):
                mm = mag_pattern.match(line)
                if not mm:
                    continue
                mag_cn = mm.group(1).lower()
                mass = mag_mass.get(mag_cn, 0)
                # Fuzzy: swap suffix around _mag (e.g., _02_civilian_mag ↔ _02_mag_civilian)
                if mass <= 0:
                    cn_no_mag = mag_cn.replace("_mag", "")
                    for csv_cn, csv_mass in mag_mass.items():
                        csv_no_mag = csv_cn.replace("_mag", "")
                        if cn_no_mag == csv_no_mag:
                            mass = csv_mass
                            break
                # Fallback: match via p4k name mapping
                if mass <= 0:
                    mass = mag_cn_from_name.get(mag_cn, 0)

                eq_pos = line.index("=")
                key_part = line[:eq_pos + 1]
                value_part = line[eq_pos + 1:].rstrip("\n").rstrip("\r")

                # Clean weapon stats that were incorrectly injected into magazines
                if "DPS:" in value_part:
                    header_str, old_stats, flavor_str = parse_description(value_part)
                    new_value = rebuild_description(header_str, "", flavor_str)
                    modified_lines[i] = key_part + new_value + "\n"
                    value_part = new_value
                    mag_patched += 1

                if mass <= 0:
                    continue

                # Check if mass already injected correctly (exact match: "Capacidad: X | Y kg")
                expected_cap = f"| {fmt_num(mass)} kg"
                if expected_cap in value_part and re.search(r"(?:Capacidad|Capacity):\s*\d+\s*\| " + re.escape(fmt_num(mass)) + r" kg", value_part):
                    continue

                # Remove any existing kg values (weapon mass leaked into mag descriptions)
                value_clean = value_part
                # Strip "| X kg" segments from Capacidad lines (but not the correct one)
                value_clean = re.sub(r"((?:Capacidad|Capacity):\s*\d+)(?:\s*\|[^\\]*kg)+", r"\1", value_clean)
                # Remove standalone mass lines
                value_clean = re.sub(r"\\n\d+\.?\d*\s*kg(?:\s*\|[^\\]*)?(?=\\n)", "", value_clean)
                # Remove "Cargado: X kg | Descargado: Y kg" lines
                value_clean = re.sub(r"\\nCargado:\s*[\d.]+\s*kg\s*\|\s*Descargado:\s*[\d.]+\s*kg", "", value_clean)
                # Remove "Dmg/Cargador: X" lines
                value_clean = re.sub(r"\\nDmg/Cargador:\s*[\d.K]+", "", value_clean)
                # Clean triple+ newlines
                value_clean = re.sub(r"(\\n){3,}", r"\\n\\n", value_clean)
                if value_clean != value_part:
                    value_part = value_clean
                    modified_lines[i] = key_part + value_part + "\n"
                    mag_patched += 1

                # Check again after cleanup
                if f"{fmt_num(mass)} kg" in value_part:
                    continue

                # Find "Capacidad: X" or "Capacity: X" and append mass
                new_value = re.sub(
                    r"(Capacidad:\s*\d+|Capacity:\s*\d+)",
                    rf"\1 | {fmt_num(mass)} kg",
                    value_part,
                    count=1
                )
                if new_value != value_part:
                    modified_lines[i] = key_part + new_value + "\n"
                    mag_patched += 1
                else:
                    # No Capacidad pattern — insert mass before last \n\n
                    last_sep = value_part.rfind("\\n\\n")
                    if last_sep >= 0:
                        new_value = value_part[:last_sep] + "\\n" + f"{fmt_num(mass)} kg" + value_part[last_sep:]
                    else:
                        new_value = value_part + "\\n" + f"{fmt_num(mass)} kg"
                    if new_value != value_part:
                        modified_lines[i] = key_part + new_value + "\n"
                        mag_patched += 1

    # --- Patch armor descriptions with mass, stun, impact ---
    armor_patched = 0
    # Map damage reduction % to tier stats from Excel
    # The game shows "Reducción de daño: X%" — we match on that to determine tier
    ARMOR_TIER_STATS = {
        "40": {"stun": 60, "impact": 35, "mass_by_slot": {"Helmet": 5, "Torso": 7, "Arms": 6, "Legs": 8}},   # Heavy
        "75": {"stun": 60, "impact": 35, "mass_by_slot": {"Helmet": 5, "Torso": 7, "Arms": 6, "Legs": 8}},   # Hv AI
        "25": {"stun": 60, "impact": 35, "mass_by_slot": {"Helmet": 5, "Torso": 7, "Arms": 6, "Legs": 8}},   # Hv Util / Bespokesuit
        "30": {"stun": 45, "impact": 31, "mass_by_slot": {"Helmet": 5, "Torso": 5, "Arms": 4, "Legs": 6}},   # Medium
        "20": {"stun": 30, "impact": 10, "mass_by_slot": {"Helmet": 5, "Torso": 3, "Arms": 2, "Legs": 3}},   # Light
        "15": {"stun": 25, "impact": 10, "mass_by_slot": {"Helmet": 5, "Torso": 3, "Arms": 2, "Legs": 3}},   # Flightsuit
        "10": {"stun": 15, "impact": 0, "mass_by_slot": {"Undersuit": 1, "Helmet": 5, "Torso": 1}},    # Undersuit/Flightsuit
    }

    # Armor mass from tier-based data (no scunpacked dependency)

    reduction_pattern = re.compile(r"[Rr]educci[oó]n de da[nñ]os?:\s*(\d+)%")
    for i, line in enumerate(modified_lines):
        if not line.lower().startswith("item_desc"):
            continue

        eq_pos = line.index("=")
        key_cn = line[9:eq_pos].lower()
        value_part = line[eq_pos + 1:].rstrip("\n").rstrip("\r")

        # Must have damage reduction line
        rm = reduction_pattern.search(value_part)
        if not rm:
            continue

        # Already has shared weight table — skip
        if "Descripción compartida" in value_part:
            continue

        # Remove ALL existing stats lines (Stun/Impacto/kg) wherever they are — will re-insert in correct position
        if "Stun:" in value_part:
            # Remove all occurrences (not just first)
            while re.search(r"\\n\d+\s*kg\s*\|\s*Stun:\s*\d+%\s*\|\s*Impacto:\s*\d+%", value_part):
                value_part = re.sub(r"\\n\d+\s*kg\s*\|\s*Stun:\s*\d+%\s*\|\s*Impacto:\s*\d+%", "", value_part, count=1)
            while re.search(r"\\n\d+\s*kg\s*\|\s*Stun:\s*\d+%", value_part):
                value_part = re.sub(r"\\n\d+\s*kg\s*\|\s*Stun:\s*\d+%", "", value_part, count=1)
            while re.search(r"\\nStun:\s*\d+%\s*\|\s*Impacto:\s*\d+%", value_part):
                value_part = re.sub(r"\\nStun:\s*\d+%\s*\|\s*Impacto:\s*\d+%", "", value_part, count=1)
            while re.search(r"\\nStun:\s*\d+%", value_part):
                value_part = re.sub(r"\\nStun:\s*\d+%", "", value_part, count=1)
            # Clean triple+ newlines
            value_part = re.sub(r"(\\n){3,}", r"\\n\\n", value_part)

        red_pct = rm.group(1)
        tier = ARMOR_TIER_STATS.get(red_pct)
        if not tier:
            continue

        # Tier-based mass: detect slot from className
        mass = 0
        if "mass_by_slot" in tier:
            cn_lower = key_cn.lower().lstrip('_')
            # Split into parts for word-boundary matching
            cn_parts = re.split(r'[_\s]+', cn_lower)
            slot = None
            if "core" in cn_parts or "torso" in cn_parts:
                slot = "Torso"
            elif "legs" in cn_parts or "leg" in cn_parts:
                slot = "Legs"
            elif "arms" in cn_parts or "arm" in cn_parts:
                slot = "Arms"
            elif "helmet" in cn_parts or "helm" in cn_parts:
                slot = "Helmet"
            elif "undersuit" in cn_parts:
                slot = "Undersuit"
            elif "pants" in cn_parts or "pantalones" in cn_parts:
                slot = "Legs"
            elif any(w in cn_parts for w in ("suit", "flightsuit", "jacket", "agent", "unified", "explorer")):
                # Full suits, jackets, agents, unified sets → Torso weight
                slot = "Torso"
            if slot:
                mass = tier["mass_by_slot"].get(slot, 0)
            elif red_pct == "10":
                # Tier 10% without recognized slot = undersuit variant
                mass = tier["mass_by_slot"].get("Undersuit", 0)

        parts = []
        if mass > 0:
            parts.append(f"{fmt_num(mass)} kg")
        if tier["stun"] > 0:
            parts.append(f"Stun: {tier['stun']}%")
        if tier["impact"] > 0:
            parts.append(f"Impacto: {tier['impact']}%")

        if not parts:
            continue

        # Shared description (no slot detected, multiple pieces) → weight table
        if mass <= 0 and "mass_by_slot" in tier:
            mbs = tier["mass_by_slot"]
            # Only add table if tier has multiple piece types (not just Undersuit/Helmet)
            piece_weights = []
            for piece, label in [("Helmet", "Casco"), ("Torso", "Pechera"), ("Arms", "Brazos"), ("Legs", "Piernas")]:
                if piece in mbs and piece != "Undersuit":
                    piece_weights.append(f"{label}: {mbs[piece]}")
            if len(piece_weights) >= 2:
                stats_line = " | ".join(parts)
                stats_line += "\\n*Descripción compartida entre piezas\\n" + " | ".join(piece_weights) + " kg"
            else:
                stats_line = " | ".join(parts)
        else:
            stats_line = " | ".join(parts)

        # Remove old stats line if partially injected (e.g., Stun without kg)
        value_part = re.sub(r"\\n\d+\s*kg\s*\|\s*Stun:\s*\d+%\s*\|\s*Impacto:\s*\d+%", "", value_part)
        value_part = re.sub(r"\\nStun:\s*\d+%\s*\|\s*Impacto:\s*\d+%", "", value_part)

        # Insert before first \n\n (after metadata, before description text)
        first_sep = value_part.find("\\n\\n")
        if first_sep >= 0:
            new_value = value_part[:first_sep] + "\\n" + stats_line + value_part[first_sep:]
        else:
            new_value = value_part + "\\n" + stats_line

        modified_lines[i] = line[:eq_pos + 1] + new_value + "\n"
        armor_patched += 1

    # --- Patch backpack descriptions with mass ---
    backpack_patched = 0
    BACKPACK_MASS = 6  # All backpacks weigh 6 kg (from Excel tab_Armor.csv)
    backpack_pattern = re.compile(r"[Mm]ochila\s+(?:pesada|media|ligera)|[Hh]eavy\s+[Bb]ackpack|[Mm]edium\s+[Bb]ackpack|[Ll]ight\s+[Bb]ackpack", re.IGNORECASE)
    for i, line in enumerate(modified_lines):
        if not line.lower().startswith("item_desc"):
            continue
        eq_pos = line.index("=")
        value_part = line[eq_pos + 1:].rstrip("\n").rstrip("\r")

        # Must be a backpack
        if not backpack_pattern.search(value_part):
            continue
        # Already injected?
        if f"{fmt_num(BACKPACK_MASS)} kg" in value_part:
            continue

        stats_line = f"{fmt_num(BACKPACK_MASS)} kg"
        last_sep = value_part.rfind("\\n\\n")
        if last_sep >= 0:
            new_value = value_part[:last_sep] + "\\n" + stats_line + value_part[last_sep:]
        else:
            new_value = value_part + "\\n" + stats_line

        modified_lines[i] = line[:eq_pos + 1] + new_value + "\n"
        backpack_patched += 1

    # --- Patch clothing/accessory descriptions with mass ---
    clothing_patched = 0
    # Mass by type from Excel tab_Armor.csv (fixed per category)
    CLOTHING_TYPES = [
        # (key_pattern, mass, label)
        (re.compile(r"_(shirt|tshirt|tanktop)_", re.IGNORECASE), 0.25, "Shirt"),
        (re.compile(r"_(jacket|hoodie|vest|coat)_", re.IGNORECASE), 0.5, "Jacket"),
        (re.compile(r"_(pants|jeans|shorts|trouser)_", re.IGNORECASE), 0.4, "Pants"),
        (re.compile(r"_(hat|cap|beret|beanie)_", re.IGNORECASE), 0.25, "Hat"),
        (re.compile(r"_(shoes|boots|footwear)_|_feet_", re.IGNORECASE), 0.3, "Feet"),
        (re.compile(r"_(gloves|glove)_|_hands_", re.IGNORECASE), 0.1, "Gloves"),
        (re.compile(r"(mobiglas|mobi_glas)", re.IGNORECASE), 0.5, "MobiGlas"),
    ]
    for i, line in enumerate(modified_lines):
        if not line.lower().startswith("item_desc"):
            continue
        eq_pos = line.index("=")
        key_part = line[:eq_pos].lower()
        value_part = line[eq_pos + 1:].rstrip("\n").rstrip("\r")

        # Skip if already has stats
        if "kg" in value_part or "DPS:" in value_part or "Stun:" in value_part:
            continue

        mass = 0
        for pattern, m, label in CLOTHING_TYPES:
            if pattern.search(key_part):
                mass = m
                break
        if mass <= 0:
            continue

        stats_line = f"{fmt_num(mass)} kg"
        # Insert mass at the top: before first \n\n (so it shows right under volume)
        first_sep = value_part.find("\\n\\n")
        if first_sep >= 0:
            # Check if there's a "Capacidad de carga" before first separator
            before = value_part[:first_sep]
            if re.search(r"Capacidad de carga:", before, re.IGNORECASE):
                # Put mass after Capacidad line
                new_value = before + "\\n" + stats_line + value_part[first_sep:]
            else:
                # Put mass before the first separator (top of description)
                new_value = stats_line + "\\n\\n" + value_part
        else:
            new_value = stats_line + "\\n\\n" + value_part

        modified_lines[i] = line[:eq_pos + 1] + new_value + "\n"
        clothing_patched += 1

    # --- Patch all FPS item descriptions with mass/stats from Excel ---
    fps_item_patched = 0
    if args.source == "tested":
        item_csv = version_dir / "sources" / "tested" / "sin_crafteo" / "tab_Item.csv"
        if item_csv.is_file():
            # Build name->className map from p4k
            en_ini = version_dir / "sources" / "global_p4k_en.ini"
            fps_name_to_cn = {}  # english name lower -> className
            if en_ini.is_file():
                with open(en_ini, "r", encoding="utf-8-sig") as f:
                    for ln in f:
                        m = re.match(r"item_Name(.+?)=(.+)", ln.strip(), re.IGNORECASE)
                        if m and not m.group(1).lower().endswith("_short"):
                            fps_name_to_cn[m.group(2).strip().replace('\xa0', ' ').lower()] = m.group(1).lower()

            # Read item data from Excel
            fps_items_data = {}  # className_lower -> {mass, alpha, rad_min, rad_max, type}
            with open(item_csv, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    name = row[0].strip()
                    if not name or name.upper() == name:
                        continue
                    mass = _parse_csv_float(row[5]) if len(row) > 5 and row[5].strip() else 0
                    mass_loaded = _parse_csv_float(row[6]) if len(row) > 6 and row[6].strip() else 0
                    alpha = _parse_csv_float(row[16]) if len(row) > 16 and row[16].strip() else 0
                    rad_min = _parse_csv_float(row[79]) if len(row) > 79 and row[79].strip() else 0
                    rad_max = _parse_csv_float(row[80]) if len(row) > 80 and row[80].strip() else 0
                    item_type = row[512].strip() if len(row) > 512 else ""
                    if mass <= 0:
                        continue
                    # Skip mining head gadgets (not in global.ini)
                    if item_type.lower() == "gadget":
                        continue

                    name_lower = name.replace('\xa0', ' ').lower()
                    # Find className via name_map
                    cn = fps_name_to_cn.get(name_lower)
                    if not cn:
                        # Try partial
                        simplified = re.sub(r'"[^"]*"\s*', '', name_lower).strip()
                        cn = fps_name_to_cn.get(simplified)

                    data = {
                        "mass": mass, "mass_loaded": mass_loaded, "alpha": alpha,
                        "rad_min": rad_min, "rad_max": rad_max,
                        "type": item_type, "name": name,
                    }

                    if cn:
                        fps_items_data[cn] = data
                    # Also store by name keywords for fallback matching
                    fps_items_data["__name__" + name_lower] = data

            # Now patch descriptions
            for i, line in enumerate(modified_lines):
                if not line.lower().startswith("item_desc"):
                    continue
                # Skip items already handled (weapons with DPS, armor with Stun, backpacks, mags)
                eq_pos = line.index("=")
                key_cn = line[9:eq_pos].lower()
                value_part = line[eq_pos + 1:].rstrip("\n").rstrip("\r")

                # Skip if already has mass/stats from other injections
                if "DPS:" in value_part or "Stun:" in value_part:
                    continue
                if "_mag" in key_cn:
                    continue
                # Skip accessories (handled by attachment patcher)
                if "DEBE COMPRAR" in value_part or "MUST PURCHASE" in value_part:
                    continue
                if re.search(r'\d+\.?\d*\s*kg', value_part):
                    continue

                # Try to find data for this item
                data = fps_items_data.get(key_cn)
                if not data:
                    # Try prefix match (skin variants inherit base stats)
                    for base_cn, v in fps_items_data.items():
                        if base_cn.startswith("__name__"):
                            continue
                        if key_cn.startswith(base_cn + "_") or key_cn.startswith(base_cn):
                            data = v
                            break
                if not data:
                    # Try keyword matching against grenade names
                    cn_parts = set(re.split(r'[_\s]+', key_cn))
                    for k, v in fps_items_data.items():
                        if not k.startswith("__name__"):
                            continue
                        gname = k[8:]
                        gname_parts = set(re.split(r'[\s\-]+', gname))
                        if len(cn_parts & gname_parts) >= 2:
                            data = v
                            break

                if not data:
                    continue

                # Build stats line
                parts = []
                if data["alpha"] > 0 and data["type"].lower() in ("grenade", "fps_consumable"):
                    parts.append(f"Alpha: {fmt_k(data['alpha'])}")
                if data["rad_min"] > 0 and data["rad_max"] > 0:
                    parts.append(f"Radio: {fmt_num(data['rad_min'])}-{fmt_num(data['rad_max'])}m")
                mass_loaded = data.get("mass_loaded", 0) or 0
                mass_empty = data.get("mass", 0) or 0
                if mass_loaded > 0 and mass_empty > 0 and abs(mass_loaded - mass_empty) > 0.01:
                    parts.append(f"Cargado: {fmt_num(mass_loaded)} kg | Descargado: {fmt_num(mass_empty)} kg")
                elif mass_empty > 0:
                    parts.append(f"{fmt_num(mass_empty)} kg")

                if not parts:
                    continue

                stats_line = " | ".join(parts)
                last_sep = value_part.rfind("\\n\\n")
                if last_sep >= 0:
                    new_value = value_part[:last_sep] + "\\n" + stats_line + value_part[last_sep:]
                else:
                    new_value = value_part + "\\n" + stats_line

                if new_value != value_part:
                    modified_lines[i] = line[:eq_pos + 1] + new_value + "\n"
                    fps_item_patched += 1

    # --- Patch attachment descriptions with Excel stats ---
    attach_patched = 0
    if args.source == "tested":
        attach_csv = version_dir / "sources" / "tested" / "con_crafteo" / "tab_Attachment.csv"
        if not attach_csv.is_file():
            attach_csv = version_dir / "sources" / "tested" / "sin_crafteo" / "tab_Attachment.csv"
        if attach_csv.is_file():
            import csv as csv_mod
            # Build name->className map from p4k
            en_ini = version_dir / "sources" / "global_p4k_en.ini"
            attach_name_map = {}
            if en_ini.is_file():
                with open(en_ini, "r", encoding="utf-8-sig") as f:
                    for ln in f:
                        m = re.match(r"item_Name(.+?)=(.+)", ln.strip(), re.IGNORECASE)
                        if m and not m.group(1).lower().endswith("_short"):
                            attach_name_map[m.group(2).strip().replace('\xa0', ' ').lower()] = m.group(1)

            def _attach_pct(val_str):
                """Convert multiplier to percentage string."""
                try:
                    v = float(val_str.strip())
                    if v == 1 or v == 0:
                        return None
                    p = round((v - 1) * 100, 1)
                    if p == int(p):
                        p = int(p)
                    return f"+{p}%" if p > 0 else f"{p}%"
                except (ValueError, TypeError):
                    return None

            # Read Excel data
            attach_data = {}  # className_lower -> stats dict
            with open(attach_csv, "r", encoding="utf-8-sig") as f:
                reader = csv_mod.reader(f)
                a_header = next(reader)
                for row in reader:
                    name = row[0].strip().replace('\xa0', ' ')
                    if not name:
                        continue
                    # Match to className
                    cn = attach_name_map.get(name.lower())
                    if not cn:
                        # Partial match: substring
                        for k, v in attach_name_map.items():
                            if name.lower() in k or k in name.lower():
                                cn = v
                                break
                    if not cn:
                        # Word match: all words from Excel name must be in p4k name (min 2 words)
                        name_words = set(re.split(r'[\s"()\-]+', name.lower())) - {'', 'edition'}
                        if len(name_words) >= 2:
                            best_match = None
                            best_score = 0
                            for k, v in attach_name_map.items():
                                k_words = set(re.split(r'[\s"()\-]+', k)) - {''}
                                common = name_words & k_words
                                if len(common) >= len(name_words) and len(common) > best_score:
                                    best_score = len(common)
                                    best_match = v
                            cn = best_match
                    if not cn:
                        # Direct className: if name looks like a className, use it
                        if "_" in name and name == name.lower():
                            cn = name
                    if not cn:
                        continue

                    mass = row[2].strip() if row[2].strip() else "0.1"
                    stats = []
                    zoom_time = _attach_pct(row[5]) if len(row) > 5 and row[5].strip() else None
                    fire_rate = _attach_pct(row[7]) if len(row) > 7 and row[7].strip() else None
                    dmg = _attach_pct(row[8]) if len(row) > 8 and row[8].strip() else None
                    proj_speed = _attach_pct(row[9]) if len(row) > 9 and row[9].strip() else None
                    heat = _attach_pct(row[13]) if len(row) > 13 and row[13].strip() else None
                    sound = _attach_pct(row[14]) if len(row) > 14 and row[14].strip() else None
                    spread = _attach_pct(row[119]) if len(row) > 119 and row[119].strip() else None
                    aim_recoil = _attach_pct(row[42]) if len(row) > 42 and row[42].strip() else None
                    vis_recoil = _attach_pct(row[62]) if len(row) > 62 and row[62].strip() else None
                    flash = _attach_pct(row[125]) if len(row) > 125 and row[125].strip() else None

                    if zoom_time:
                        stats.append(f"Tiempo de apuntado: {zoom_time}")
                    if fire_rate:
                        stats.append(f"Cadencia: {fire_rate}")
                    if dmg:
                        stats.append(f"Daño: {dmg}")
                    if proj_speed:
                        stats.append(f"Vel. proyectil: {proj_speed}")
                    if spread:
                        stats.append(f"Dispersión: {spread}")
                    if aim_recoil:
                        stats.append(f"Retroceso al apuntar: {aim_recoil}")
                    if vis_recoil:
                        stats.append(f"Retroceso visual: {vis_recoil}")
                    if heat:
                        stats.append(f"Calor: {heat}")
                    if sound:
                        stats.append(f"Alcance audible: {sound}")
                    if flash:
                        stats.append(f"Flash: {flash}")

                    attach_data[cn.lower()] = {
                        "mass": mass,
                        "stats": stats,
                        "name": name,
                    }
                    # Also map skin variants
                    cn_lower = cn.lower().rstrip(',p').rstrip(',')
                    if cn_lower not in attach_data:
                        attach_data[cn_lower] = attach_data[cn.lower()]
                    # Map base without _base suffix for skin matching
                    cn_no_base = re.sub(r'_base$', '', cn_lower)
                    if cn_no_base != cn_lower and cn_no_base not in attach_data:
                        attach_data[cn_no_base] = attach_data[cn.lower()]

            # Now patch descriptions
            # Attachment descriptions have: header fields \n\n stats \n\n flavor
            # We replace the stats block and add mass
            attach_desc_pattern = re.compile(r"^item_Desc(.+?)=", re.IGNORECASE)
            # Stats line patterns to detect and remove
            old_stat_patterns = [
                # English stats from p4k
                r"(?:Aim |Recoil )?Time:?\s*[+-]",
                r"(?:Aim |Visual )?Recoil:?\s*[+-]",
                r"(?:Horizontal |Vertical )?Aim Recoil:?\s*[+-]",
                r"Spread:?\s*[+-]",
                r"Fire Rate:?\s*[+-]",
                r"Damage:?\s*[+-]",
                r"Projectile Speed:?\s*[+-]",
                r"Audible Range:?\s*[+-]",
                r"Heat:?\s*[+-]",
                r"Recoil Stability:?\s*[+-]",
                r"Recoil Smoothness:?\s*[+-]",
                r"Muzzle Flash:?\s*[+-]",
                r"Burst Shots:?\s*[+-]",
                # Spanish stats (translated by Thord82 or us)
                r"Tiempo de apuntado:?\s*[+-]",
                r"Retroceso al apuntar:?\s*[+-]",
                r"Retroceso visual:?\s*[+-]",
                r"Dispersi[oó]n:?\s*[+-]",
                r"Cadencia.*:?\s*[+-]",
                r"Da.o:?\s*[+-]",
                r"Vel.*proyectil:?\s*[+-]",
                r"Velocidad del proyectil:?\s*[+-]",
                r"Alcance audible:?\s*[+-]",
                r"Calor:?\s*[+-]",
                r"Flash:?\s*[+-]",
                r"Disparos adicionales",
                r"Estabilidad de retroceso",
                r"Suavidad de retroceso",
                # Weight line
                r"^\d+\.?\d*\s*kg$",
            ]
            old_stat_re = re.compile("|".join(old_stat_patterns), re.IGNORECASE)

            for i, line in enumerate(modified_lines):
                m = attach_desc_pattern.match(line)
                if not m:
                    continue
                cn_key = m.group(1).lower().rstrip(',p').rstrip(',')
                data = attach_data.get(cn_key)
                if not data:
                    # Try prefix match for skin variants
                    for base_cn, base_data in attach_data.items():
                        if cn_key.startswith(base_cn + "_") or cn_key.startswith(base_cn):
                            data = base_data
                            break
                if not data:
                    continue

                eq_pos = line.index("=")
                value_part = line[eq_pos + 1:].rstrip("\n").rstrip("\r")

                # Skip if already has correct mass (idempotency)
                if f"{data['mass']} kg" in value_part:
                    # Check if all stats are present too
                    all_present = all(s in value_part for s in data["stats"])
                    if all_present:
                        continue

                # Simple approach: remove old stats, remove old mass, insert new before first \n\n
                # Step 1: Remove old stat lines and old mass lines
                cleaned = value_part
                for pat in old_stat_patterns:
                    cleaned = re.sub(r"\\n" + pat + r"[^\\]*", "", cleaned, flags=re.IGNORECASE)
                # Remove standalone mass lines
                cleaned = re.sub(r"\\n\d+\.?\d*\s*kg(?=\\n|$)", "", cleaned)
                # Clean up triple+ \n
                cleaned = re.sub(r"(\\n){3,}", r"\\n\\n", cleaned)

                # Step 2: Build stats + mass block
                new_stats = list(data["stats"])
                new_stats.append(f"{data['mass']} kg")
                stats_block = "\\n".join(new_stats)

                # Step 3: Find insertion point
                # For accessories with "DEBE COMPRAR": insert after "Clase:" line
                # For others: insert before first \n\n
                clase_match = re.search(r"(Clase:[^\\]*)", cleaned)
                if clase_match and "DEBE COMPRAR" in cleaned:
                    insert_pos = clase_match.end()
                    new_value = cleaned[:insert_pos] + "\\n" + stats_block + cleaned[insert_pos:]
                elif (first_sep := cleaned.find("\\n\\n")) >= 0:
                    new_value = cleaned[:first_sep] + "\\n" + stats_block + cleaned[first_sep:]
                else:
                    new_value = cleaned + "\\n" + stats_block

                new_line = line[:eq_pos + 1] + new_value + "\n"
                if new_line != line:
                    modified_lines[i] = new_line
                    attach_patched += 1

    # Report unmatched weapons (exclude _mag and _short)
    unmatched = [cn for cn, val in weapons.items() if val is not None and "_mag" not in cn and not cn.endswith("_short")]

    if blueprint_cleaned:
        print(f"Cleaned: {blueprint_cleaned} blueprint X-prefix markers")
    print(f"Patched: {patched} descriptions")
    if mag_patched:
        print(f"Patched: {mag_patched} magazine descriptions (mass)")
    if armor_patched:
        print(f"Patched: {armor_patched} armor descriptions (mass/stun/impact)")
    if backpack_patched:
        print(f"Patched: {backpack_patched} backpack descriptions (mass)")
    if clothing_patched:
        print(f"Patched: {clothing_patched} clothing/accessory descriptions (mass)")
    if fps_item_patched:
        print(f"Patched: {fps_item_patched} FPS item descriptions (mass/stats)")
    if attach_patched:
        print(f"Patched: {attach_patched} attachment descriptions (stats/mass)")
    if unmatched:
        print(f"Unmatched weapons (no item_Desc found): {len(unmatched)}")
        for cn in sorted(unmatched):
            print(f"  - {cn}")

    # Write output
    if not args.dry_run:
        output_path = args.output if args.output else global_ini_path
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            f.writelines(modified_lines)
        print(f"\nWritten: {output_path}")
    else:
        print(f"\n[DRY RUN] No changes written.")

    # --- Verify mode ---
    if args.verify and not args.dry_run:
        print("\n=== VERIFY ===")
        errors = 0

        # 1. No orphan lines (lines without =)
        orphans = sum(1 for l in modified_lines if l.strip() and "=" not in l.strip())
        if orphans:
            print(f"FAIL: {orphans} orphan lines (no '=' sign)")
            errors += 1
        else:
            print(f"OK: 0 orphan lines")

        # 2. No duplicate keys
        seen_keys = {}
        dupes = 0
        for i, l in enumerate(modified_lines, 1):
            if "=" in l:
                k = l.split("=", 1)[0]
                if k in seen_keys:
                    dupes += 1
                    if dupes <= 3:
                        print(f"  DUPE: {k} (lines {seen_keys[k]} and {i})")
                seen_keys[k] = i
        if dupes:
            print(f"FAIL: {dupes} duplicate keys")
            errors += 1
        else:
            print(f"OK: 0 duplicate keys")

        # 3. No double kg (except Cargado/Descargado)
        double_kg = 0
        for l in modified_lines:
            if not l.startswith("item_Desc"):
                continue
            val = l.split("=", 1)[1]
            kg_matches = re.findall(r"\d+\.?\d*\s*kg", val)
            if len(kg_matches) >= 2 and "Cargado:" not in val:
                double_kg += 1
                if double_kg <= 3:
                    print(f"  DOUBLE KG: {l.split('=')[0]}: {kg_matches}")
        if double_kg:
            print(f"FAIL: {double_kg} items with double kg")
            errors += 1
        else:
            print(f"OK: 0 double kg")

        # 4. No text lost (compare original vs modified — description text must not shrink >20%)
        lost = 0
        for orig, mod in zip(lines, modified_lines):
            if not orig.startswith("item_Desc"):
                continue
            ok = orig.split("=", 1)[0]
            mk = mod.split("=", 1)[0]
            if ok != mk:
                continue
            ov = orig.split("=", 1)[1]
            mv = mod.split("=", 1)[1]
            # Strip stats to compare core text
            def _strip(v):
                v = re.sub(r"\\n\d+\.?\d*\s*kg[^\\]*", "", v)
                v = re.sub(r"\\nCargado:[^\\]*", "", v)
                v = re.sub(r"\\nStun:[^\\]*", "", v)
                v = re.sub(r"\\nDPS:[^\\]*", "", v)
                v = re.sub(r"\\nAlpha:[^\\]*", "", v)
                v = re.sub(r"\\nDmg/Cargador:[^\\]*", "", v)
                v = re.sub(r"\\n\[(?:Auto|Semi|Beam|Full|Burst|Hot|Slug|Doble|Red\. daño)\][^\\]*", "", v)
                return v
            ov_clean = _strip(ov)
            mv_clean = _strip(mv)
            if len(mv_clean) < len(ov_clean) * 0.8 and len(ov_clean) > 50:
                lost += 1
                if lost <= 3:
                    print(f"  LOST TEXT: {ok} ({len(ov_clean)} -> {len(mv_clean)} chars)")
        if lost:
            print(f"FAIL: {lost} items lost >20% text")
            errors += 1
        else:
            print(f"OK: 0 items lost text")

        # 5. Idempotency (re-run on output, compare)
        import tempfile, shutil
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", encoding="utf-8-sig",
                                         newline="", delete=False) as tmp:
            tmp.writelines(modified_lines)
            tmp_path = tmp.name
        # Re-run inject on the output
        import subprocess
        result = subprocess.run(
            [sys.executable, __file__,
             "--source", args.source,
             "--version", version,
             "--output", tmp_path + ".run2"],
            capture_output=True, text=True,
            env={**os.environ, "_INJECT_INPUT": tmp_path}
        )
        # Can't easily re-run with different input... compare by running with --output
        # Simpler: just read tmp and compare
        # Actually, re-read the output we wrote and re-process in memory
        with open(output_path, "r", encoding="utf-8-sig") as f:
            run1_lines = f.readlines()
        # Save run1, swap input, run again to tmp
        shutil.copy2(output_path, tmp_path)
        result2 = subprocess.run(
            [sys.executable, sys.argv[0],
             "--source", args.source,
             "--version", version,
             "--output", tmp_path + ".run2"],
            capture_output=True, text=True
        )
        if os.path.exists(tmp_path + ".run2"):
            with open(tmp_path + ".run2", "r", encoding="utf-8-sig") as f:
                run2_lines = f.readlines()
            diffs = sum(1 for a, b in zip(run1_lines, run2_lines) if a != b)
            if diffs:
                print(f"FAIL: {diffs} lines differ on 2nd run (not idempotent)")
                errors += 1
            else:
                print(f"OK: idempotent (0 diffs on 2nd run)")
            os.unlink(tmp_path + ".run2")
        else:
            print(f"WARN: could not run idempotency test")
        os.unlink(tmp_path)

        # 6. Compare vs p4k (missing keys)
        p4k_en = version_dir / "sources" / "global_p4k_en.ini"
        if p4k_en.is_file():
            p4k_keys = set()
            with open(p4k_en, "r", encoding="utf-8-sig") as f:
                for l in f:
                    if "=" in l:
                        p4k_keys.add(l.split("=", 1)[0])
            our_keys = set(l.split("=", 1)[0] for l in modified_lines if "=" in l)
            # Case-insensitive comparison
            our_lower = {k.lower() for k in our_keys}
            missing = [k for k in p4k_keys if k.lower() not in our_lower]
            if missing:
                print(f"INFO: {len(missing)} keys in p4k missing from output (case-insensitive)")
            else:
                print(f"OK: all p4k keys present")

        print(f"\n{'=== ALL CHECKS PASSED ===' if errors == 0 else f'=== {errors} CHECKS FAILED ==='}")


if __name__ == "__main__":
    main()
