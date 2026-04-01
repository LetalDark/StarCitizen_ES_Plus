#!/usr/bin/env python3
"""
extract_ship_components.py — Extract ship component stats from Game2.dcb.

Reads EntityClassDefinition records from the DCB for PowerPlants, QuantumDrives,
JumpDrives, Shields, Coolers and Radars. Formats stats blocks for injection.

Can be used standalone (prints summary tables) or imported by
inject_weapon_stats.py via load_dcb_ship_components().

Usage:
    python extract_ship_components.py                    # Summary table
    python extract_ship_components.py --json -o out.json # Export all data
    python extract_ship_components.py --dry-run          # Show formatted stats blocks
    python extract_ship_components.py --type Shield      # Filter by type
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path
from parse_dcb import DataForge

BASE_DIR = Path(__file__).resolve().parent

# Component types and their DCB search paths
COMPONENT_TYPES = {
    "PowerPlant":   "ships/powerplant/powr_",
    "QuantumDrive": "ships/quantumdrive/qdrv_",
    "JumpDrive":    "ships/jumpdrive/jdrv_",
    "Shield":       "ships/shieldgenerator/shld_",
    "Cooler":       "ships/cooler/cool_",
    "Radar":        "ships/radar/radr_",
}

# Grade number -> letter
GRADE_MAP = {1: "A", 2: "B", 3: "C", 4: "D"}

# Quantum fuel tank capacity range per QDrive size (min, max in SCU)
# Extracted from DCB: ResourceContainer.capacity on qtnk_* entities
QT_TANK_RANGE = {
    0: (0.90, 4.00),   # S0 (same as S1, few vehicles)
    1: (0.90, 4.00),   # S1: Wolf(0.9) to Terrapin Medic(4.0)
    2: (1.65, 5.60),   # S2: Shiv(1.65) to Constellation Aquila(5.6)
    3: (6.60, 12.60),  # S3: Starlifter/Hammerhead(6.6) to Polaris(12.6)
    4: (14.60, 120.00), # S4: 890 Jump(14.6) to Idris(120)
}

# Class keyword -> Spanish label
CLASS_MAP = {
    "Military": "Militar",
    "Civilian": "Civil",
    "Competition": "Competición",
    "Industrial": "Industrial",
    "Stealth": "Sigilo",
}


# ---------------------------------------------------------------------------
# DCB extraction helpers
# ---------------------------------------------------------------------------

def _get_component(components, type_name):
    """Get first component of a given type from a list of resolved components."""
    for c in components:
        if isinstance(c, dict) and c.get("__type") == type_name:
            return c
    return None


def _get_resource_data(resource):
    """Extract generation, consumption, EM and IR from ItemResourceComponentParams."""
    result = {
        "power_gen": 0, "power_draw": 0, "power_min_fraction": 0,
        "em": 0, "em_decay": 0, "ir": 0,
    }
    if not resource:
        return result

    for state in resource.get("states", []):
        if not isinstance(state, dict) or state.get("name") != "Online":
            continue
        for delta in state.get("deltas", []):
            if not isinstance(delta, dict):
                continue
            # Generation
            gen = delta.get("generation", {})
            if isinstance(gen, dict) and gen.get("resource"):
                amt = gen.get("resourceAmountPerSecond", {})
                if isinstance(amt, dict):
                    v = amt.get("units", 0) or amt.get("standardResourceUnits", 0)
                    if v:
                        result[f"gen_{gen['resource']}"] = v
                        if gen["resource"] == "Power":
                            result["power_gen"] = v

            # Consumption
            cons = delta.get("consumption", {})
            if isinstance(cons, dict) and cons.get("resource"):
                amt = cons.get("resourceAmountPerSecond", {})
                if isinstance(amt, dict):
                    v = amt.get("units", 0) or amt.get("standardResourceUnits", 0)
                    if v and cons["resource"] == "Power":
                        result["power_draw"] = v
                min_frac = delta.get("minimumConsumptionFraction", 0)
                if min_frac and cons.get("resource") == "Power":
                    result["power_min_fraction"] = min_frac

        # Signatures
        sig = state.get("signatureParams", {})
        if isinstance(sig, dict):
            em = sig.get("EMSignature", {})
            if isinstance(em, dict):
                result["em"] = em.get("nominalSignature", 0)
                result["em_decay"] = em.get("decayRate", 0)
            ir = sig.get("IRSignature", {})
            if isinstance(ir, dict):
                result["ir"] = ir.get("nominalSignature", 0)
    return result


# ---------------------------------------------------------------------------
# Extract component data
# ---------------------------------------------------------------------------

def extract_component_data(df, record_index):
    """
    Extract all relevant stats from a ship component entity.
    Returns a dict with all stats, or None if not a valid component.
    """
    data = df.read_record(record_index, max_depth=7)
    components = data.get("Components", [])
    if not isinstance(components, list):
        return None

    attachable = _get_component(components, "SAttachableComponentParams")
    if not attachable:
        return None
    attach_def = attachable.get("AttachDef", {})
    if not isinstance(attach_def, dict):
        return None

    comp_type = attach_def.get("Type", "")
    if comp_type not in COMPONENT_TYPES:
        return None

    result = {
        "type": comp_type,
        "size": attach_def.get("Size", 0),
        "grade": attach_def.get("Grade", 0),
        "grade_letter": GRADE_MAP.get(attach_def.get("Grade", 0), "?"),
    }

    # Localization keys
    loc = attach_def.get("Localization", {})
    if isinstance(loc, dict):
        result["loc_name"] = loc.get("Name", "")
        result["loc_desc"] = loc.get("Description", "")

    # className from loc_desc
    desc_key = result.get("loc_desc", "")
    if desc_key.startswith("@item_Desc") or desc_key.startswith("@item_desc"):
        result["className"] = desc_key.split("@item_Desc")[-1].split("@item_desc")[-1]
    else:
        fname = df.record_filename(record_index)
        result["className"] = fname.split("/")[-1].replace(".xml", "")

    # Entity path
    result["entity_path"] = df.record_filename(record_index)

    # HP
    health = _get_component(components, "SHealthComponentParams")
    if health:
        result["hp"] = health.get("Health", 0)

    # Mass
    physics = _get_component(components, "SEntityPhysicsControllerParams")
    if physics:
        phys_type = physics.get("PhysType", {})
        if isinstance(phys_type, dict):
            result["mass"] = phys_type.get("Mass", 0)

    # Distortion
    disto = _get_component(components, "SDistortionParams")
    if disto:
        result["disto_max"] = disto.get("Maximum", 0)
        result["disto_decay"] = disto.get("DecayRate", 0)
        result["disto_delay"] = disto.get("DecayDelay", 0)
        if result["disto_decay"] > 0 and result["disto_max"] > 0:
            result["disto_rec"] = round(
                result["disto_delay"] + result["disto_max"] / result["disto_decay"], 1)

    # Resource network (power, EM, IR)
    resource = _get_component(components, "ItemResourceComponentParams")
    res_data = _get_resource_data(resource)
    result.update(res_data)

    # --- Type-specific params ---

    if comp_type == "PowerPlant":
        # EM per segment
        if result["power_gen"] > 0 and result["em"] > 0:
            result["em_per_seg"] = round(result["em"] / result["power_gen"], 1)

    elif comp_type == "QuantumDrive":
        qd = _get_component(components, "SCItemQuantumDriveParams")
        if qd:
            params = qd.get("params", {})
            if isinstance(params, dict):
                result["drive_speed"] = params.get("driveSpeed", 0)
                result["cooldown_time"] = params.get("cooldownTime", 0)
                result["spool_time"] = params.get("spoolUpTime", 0)
                result["stage1_accel"] = params.get("stageOneAccelRate", 0)
                result["stage2_accel"] = params.get("stageTwoAccelRate", 0)
                result["calibration_rate"] = params.get("calibrationRate", 0)
            result["fuel_req"] = qd.get("quantumFuelRequirement", 0)
            result["jump_range"] = qd.get("jumpRange", 0)
            result["disconnect_range"] = qd.get("disconnectRange", 0)
            # Heat
            heat = qd.get("heatParams", {})
            if isinstance(heat, dict):
                result["heat_in_flight"] = heat.get("inFlightThermalEnergyDraw", 0)
            # Efficiency range (depends on ship QT tank size)
            speed_mm = result.get("drive_speed", 0) / 1e6
            fuel = result.get("fuel_req", 0)
            size = result.get("size", 0)
            if speed_mm > 0 and fuel > 0 and size in QT_TANK_RANGE:
                t_min, t_max = QT_TANK_RANGE[size]
                result["eff_min"] = round(t_min * speed_mm / (fuel * 18000), 1)
                result["eff_max"] = round(t_max * speed_mm / (fuel * 18000), 1)
                result["tank_min"] = t_min
                result["tank_max"] = t_max

    elif comp_type == "JumpDrive":
        jd = _get_component(components, "SCItemJumpDriveParams")
        if jd:
            result["tuning_rate"] = jd.get("tuningRate", 0)
            result["tuning_decay"] = jd.get("tuningDecayRate", 0)
            result["alignment_rate"] = jd.get("alignmentRate", 0)
            result["alignment_decay"] = jd.get("alignmentDecayRate", 0)
            result["fuel_multiplier"] = jd.get("fuelUsageEfficiencyMultiplier", 0)

    elif comp_type == "Shield":
        sh = _get_component(components, "SCItemShieldGeneratorParams")
        if sh:
            result["shield_hp"] = sh.get("MaxShieldHealth", 0)
            result["shield_regen"] = sh.get("MaxShieldRegen", 0)
            if result["shield_regen"] > 0:
                result["shield_regen_time"] = round(
                    result["shield_hp"] / result["shield_regen"], 1)
            result["damaged_delay"] = sh.get("DamagedRegenDelay", 0)
            result["downed_delay"] = sh.get("DownedRegenDelay", 0)
            result["decay_ratio"] = sh.get("DecayRatio", 0)
            # Shield resistances [Physical, Energy, Distortion, Thermal, Bio, Stun]
            resistances = sh.get("ShieldResistance", [])
            if isinstance(resistances, list) and len(resistances) > 1:
                energy_res = resistances[1]
                if isinstance(energy_res, dict):
                    result["resist_energy"] = energy_res.get("Max", 0)

    elif comp_type == "Cooler":
        # Cooling is in resource generation (gen_Coolant)
        result["cooling"] = res_data.get("gen_Coolant", 0)

    elif comp_type == "Radar":
        radar = _get_component(components, "SCItemRadarComponentParams")
        if radar:
            # Aim assist
            aim = radar.get("aimAssist", {})
            if isinstance(aim, dict):
                result["aim_min"] = aim.get("distanceMinAssignment", 0)
                result["aim_max"] = aim.get("distanceMaxAssignment", 0)
                result["aim_buffer"] = aim.get("outsideRangeBufferDistance", 0)
            # Signature detection sensitivities
            sigs = radar.get("signatureDetection", [])
            sig_names = ["ir_sens", "em_sens", "cs_sens", "rs_sens"]
            for idx, name in enumerate(sig_names):
                if idx < len(sigs) and isinstance(sigs[idx], dict):
                    result[name] = sigs[idx].get("sensitivity", 0)

    return result


# ---------------------------------------------------------------------------
# Find all components in the DCB
# ---------------------------------------------------------------------------

def find_all_components(df, type_filter=None):
    """
    Find all ship component entities in the DCB.
    Returns list of record indices for EntityClassDefinition records.
    """
    results = []
    types_to_search = COMPONENT_TYPES
    if type_filter:
        types_to_search = {k: v for k, v in COMPONENT_TYPES.items() if k == type_filter}

    for comp_type, search_path in types_to_search.items():
        matches = df.find_records(search_path)
        for ri in matches:
            sname = df.struct_name(df.record_defs[ri]["struct_index"])
            if sname != "EntityClassDefinition":
                continue
            fname = df.record_filename(ri)
            if "template" in fname:
                continue
            results.append(ri)

    return results


# ---------------------------------------------------------------------------
# Format stats blocks
# ---------------------------------------------------------------------------

def fmt_num(v):
    """Format number: integer if whole, else up to 2 decimals."""
    if v is None or v == 0:
        return "0"
    if isinstance(v, float) and v != int(v):
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(int(v))


def fmt_k(v):
    """Format with K suffix for values >= 1000."""
    if v is None or v == 0:
        return "0"
    if abs(v) >= 1000:
        k = v / 1000
        rounded = round(k, 1)
        if rounded == int(rounded):
            return f"{int(rounded)}K"
        return f"{rounded:.1f}K"
    if isinstance(v, float) and v != int(v):
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(int(v))


def format_stats_block(c):
    """Build the stats text block for a ship component."""
    comp_type = c.get("type", "")
    lines = []

    if comp_type == "PowerPlant":
        # Line 1: Energía + HP
        lines.append(f"Energía: {fmt_num(c.get('power_gen', 0))} | HP: {fmt_num(c.get('hp', 0))}")
        # Line 2: Distorsión agrupada
        disto_max = c.get("disto_max", 0)
        if disto_max:
            parts = [f"Disto: {fmt_k(disto_max)}",
                     f"Disipa: {fmt_num(c.get('disto_decay', 0))}/s"]
            rec = c.get("disto_rec", 0)
            if rec:
                parts.append(f"Rec: {fmt_num(rec)}s")
            lines.append(" | ".join(parts))
        # Line 3: EM por segmento + EM Decay
        em_seg = c.get("em_per_seg", 0)
        em_decay = c.get("em_decay", 0)
        parts3 = []
        if em_seg:
            parts3.append(f"EM/Seg: {fmt_num(em_seg)}")
        if em_decay:
            parts3.append(f"EM Decay: {fmt_num(em_decay)}")
        if parts3:
            lines.append(" | ".join(parts3))
        # Line 4: Masa
        mass = c.get("mass", 0)
        if mass:
            lines.append(f"{fmt_num(mass)} kg")

    elif comp_type == "QuantumDrive":
        # Line 1: Velocidad + Consumo
        speed_mm = c.get("drive_speed", 0) / 1e6 if c.get("drive_speed") else 0
        fuel = c.get("fuel_req", 0)
        parts1 = [f"Vel: {fmt_num(speed_mm)} Mm/s"]
        if fuel:
            # More precision for fuel (values like 0.02398)
            fuel_str = f"{fuel:.4f}".rstrip("0").rstrip(".")
            parts1.append(f"Consumo: {fuel_str}")
        lines.append(" | ".join(parts1))
        # Line 2: Tiempos
        spool = c.get("spool_time", 0)
        cooldown = c.get("cooldown_time", 0)
        parts2 = []
        if spool:
            parts2.append(f"Carga: {fmt_num(spool)}s")
        if cooldown:
            parts2.append(f"Enfriamiento: {fmt_num(cooldown)}s")
        if parts2:
            lines.append(" | ".join(parts2))
        # Line 3: Distorsión
        disto_max = c.get("disto_max", 0)
        if disto_max:
            parts = [f"Disto: {fmt_k(disto_max)}",
                     f"Disipa: {fmt_num(c.get('disto_decay', 0))}/s"]
            lines.append(" | ".join(parts))
        # Line 4: Físico/firma
        parts4 = []
        mass = c.get("mass", 0)
        if mass:
            parts4.append(f"{fmt_num(mass)} kg")
        hp = c.get("hp", 0)
        if hp:
            parts4.append(f"HP: {fmt_num(hp)}")
        em = c.get("em", 0)
        if em:
            parts4.append(f"EM: {fmt_num(em)}")
        pw = c.get("power_draw", 0)
        if pw:
            parts4.append(f"Energía: {fmt_num(pw)}")
        if parts4:
            lines.append(" | ".join(parts4))
        # Line 5: Eficiencia min-max
        eff_min = c.get("eff_min", 0)
        eff_max = c.get("eff_max", 0)
        if eff_min and eff_max:
            t_min = c.get("tank_min", 0)
            t_max = c.get("tank_max", 0)
            lines.append(
                f"[Eficiencia/tanque] {fmt_num(t_min)} SCU: {fmt_num(eff_min)}"
                f" | {fmt_num(t_max)} SCU: {fmt_num(eff_max)}")

    elif comp_type == "JumpDrive":
        # Line 1: Calibración + Alineación
        parts1 = []
        tr = c.get("tuning_rate", 0)
        ar = c.get("alignment_rate", 0)
        if tr:
            parts1.append(f"Calibración: {fmt_num(tr)}")
        if ar:
            parts1.append(f"Alineación: {fmt_num(ar)}")
        if parts1:
            lines.append(" | ".join(parts1))
        # Line 2: Combustible
        fuel = c.get("fuel_multiplier", 0)
        if fuel:
            lines.append(f"Combustible: x{fmt_num(fuel)}")
        # Line 3: Distorsión
        disto_max = c.get("disto_max", 0)
        if disto_max:
            parts = [f"Disto: {fmt_k(disto_max)}",
                     f"Disipa: {fmt_num(c.get('disto_decay', 0))}/s"]
            lines.append(" | ".join(parts))
        # Line 4: Físico
        parts4 = []
        mass = c.get("mass", 0)
        if mass:
            parts4.append(f"{fmt_num(mass)} kg")
        hp = c.get("hp", 0)
        if hp:
            parts4.append(f"HP: {fmt_num(hp)}")
        em = c.get("em", 0)
        if em:
            parts4.append(f"EM: {fmt_num(em)}")
        if parts4:
            lines.append(" | ".join(parts4))

    elif comp_type == "Shield":
        # Line 1: Escudo + Regen + Tiempo
        parts1 = [f"Escudo: {fmt_k(c.get('shield_hp', 0))}",
                   f"Regen: {fmt_num(c.get('shield_regen', 0))}/s"]
        regen_time = c.get("shield_regen_time", 0)
        if regen_time:
            parts1.append(f"Tiempo: {fmt_num(regen_time)}s")
        lines.append(" | ".join(parts1))
        # Line 2: Retardos
        parts2 = []
        dd = c.get("damaged_delay", 0)
        if dd:
            parts2.append(f"Retardo: {fmt_num(dd)}s")
        dwd = c.get("downed_delay", 0)
        if dwd:
            parts2.append(f"Caído: {fmt_num(dwd)}s")
        if parts2:
            lines.append(" | ".join(parts2))
        # Line 3: Resistencia
        resist_e = c.get("resist_energy", 0)
        if resist_e != 0:
            lines.append(f"Resist. Energía: {int(resist_e * 100)}%")
        # Line 4: Físico/firma
        parts4 = []
        pw = c.get("power_draw", 0)
        pw_min_frac = c.get("power_min_fraction", 0)
        if pw:
            pw_min = int(pw * pw_min_frac) if pw_min_frac else 0
            if pw_min:
                parts4.append(f"Energía: {pw_min}-{fmt_num(pw)}")
            else:
                parts4.append(f"Energía: {fmt_num(pw)}")
        em = c.get("em", 0)
        if em:
            parts4.append(f"EM: {fmt_num(em)}")
        hp = c.get("hp", 0)
        if hp:
            parts4.append(f"HP: {fmt_num(hp)}")
        if parts4:
            lines.append(" | ".join(parts4))

    elif comp_type == "Cooler":
        # Line 1: Enfriamiento
        cooling = c.get("cooling", 0)
        if cooling:
            lines.append(f"Enfriamiento: {fmt_num(cooling)}")
        # Line 2: Energía/firma
        parts2 = []
        pw = c.get("power_draw", 0)
        pw_min_frac = c.get("power_min_fraction", 0)
        if pw:
            pw_min = int(pw * pw_min_frac) if pw_min_frac else 0
            if pw_min:
                parts2.append(f"Energía: {pw_min}-{fmt_num(pw)}")
            else:
                parts2.append(f"Energía: {fmt_num(pw)}")
        em = c.get("em", 0)
        if em:
            parts2.append(f"EM: {fmt_num(em)}")
        ir = c.get("ir", 0)
        if ir:
            parts2.append(f"IR: {fmt_num(ir)}")
        hp = c.get("hp", 0)
        if hp:
            parts2.append(f"HP: {fmt_num(hp)}")
        if parts2:
            lines.append(" | ".join(parts2))
        # Line 3: Distorsión
        disto_max = c.get("disto_max", 0)
        if disto_max:
            parts3 = [f"Disto: {fmt_k(disto_max)}",
                       f"Disipa: {fmt_num(c.get('disto_decay', 0))}/s"]
            rec = c.get("disto_rec", 0)
            if rec:
                parts3.append(f"Rec: {fmt_num(rec)}s")
            lines.append(" | ".join(parts3))
        # Line 4: Masa
        mass = c.get("mass", 0)
        if mass:
            lines.append(f"{fmt_num(mass)} kg")

    elif comp_type == "Radar":
        # Line 1: Asistencia de apuntado
        aim_min = c.get("aim_min", 0)
        aim_max = c.get("aim_max", 0)
        parts1 = []
        if aim_min or aim_max:
            parts1.append(f"Asist: {fmt_num(aim_min)}-{fmt_num(aim_max)}m")
        aim_buf = c.get("aim_buffer", 0)
        if aim_buf:
            parts1.append(f"Margen: {fmt_num(aim_buf)}m")
        if parts1:
            lines.append(" | ".join(parts1))
        # Line 2: Sensibilidades
        parts2 = []
        for key, label in [("ir_sens", "IR"), ("em_sens", "EM"),
                           ("cs_sens", "CS"), ("rs_sens", "RS")]:
            v = c.get(key, 0)
            if v:
                parts2.append(f"{label}: {int(v * 100)}%")
        if parts2:
            lines.append(" | ".join(parts2))
        # Line 3: Físico/firma
        parts3 = []
        pw = c.get("power_draw", 0)
        pw_min_frac = c.get("power_min_fraction", 0)
        if pw:
            pw_min = int(pw * pw_min_frac) if pw_min_frac else 0
            if pw_min:
                parts3.append(f"Energía: {pw_min}-{fmt_num(pw)}")
            else:
                parts3.append(f"Energía: {fmt_num(pw)}")
        em = c.get("em", 0)
        if em:
            parts3.append(f"EM: {fmt_num(em)}")
        hp = c.get("hp", 0)
        if hp:
            parts3.append(f"HP: {fmt_num(hp)}")
        if parts3:
            lines.append(" | ".join(parts3))

    return "\\n".join(lines)


# ---------------------------------------------------------------------------
# Main loader for inject_weapon_stats.py
# ---------------------------------------------------------------------------

def load_dcb_ship_components(dcb_path="Game2.dcb"):
    """
    Load all ship component stats from the DCB.

    Returns dict: className (lowercase) -> (component_data, comp_type_lowercase, stats_block)
    Compatible with inject_weapon_stats.py weapons dict format.
    """
    if not os.path.exists(dcb_path):
        print(f"ERROR: {dcb_path} not found.", file=sys.stderr)
        print("Extract first: python explore_p4k.py --extract \"Data\\Game2.dcb\" -o Game2.dcb",
              file=sys.stderr)
        return {}

    print("Loading DCB for ship components...", file=sys.stderr)
    df = DataForge(dcb_path)
    print(f"  Records: {df.record_def_count:,}", file=sys.stderr)

    record_indices = find_all_components(df)
    print(f"  Component entities found: {len(record_indices)}", file=sys.stderr)

    components = {}
    skipped = 0
    errors = 0
    by_type = {}

    for ri in record_indices:
        try:
            c = extract_component_data(df, ri)
        except Exception as e:
            errors += 1
            fname = df.record_filename(ri)
            print(f"  ERROR extracting {fname}: {e}", file=sys.stderr)
            continue

        if c is None:
            skipped += 1
            continue

        class_name = c.get("className", "").lower()
        if not class_name:
            skipped += 1
            continue

        stats_block = format_stats_block(c)
        if not stats_block:
            skipped += 1
            continue

        comp_type = c["type"]
        components[class_name] = (c, comp_type.lower(), stats_block)
        by_type[comp_type] = by_type.get(comp_type, 0) + 1

    print(f"  Components with stats: {len(components)}", file=sys.stderr)
    for t, count in sorted(by_type.items()):
        print(f"    {t}: {count}", file=sys.stderr)
    if skipped:
        print(f"  Skipped: {skipped}", file=sys.stderr)
    if errors:
        print(f"  Errors: {errors}", file=sys.stderr)

    return components


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract ship component stats from Game2.dcb")
    parser.add_argument("--dcb", default="Game2.dcb", help="Path to Game2.dcb")
    parser.add_argument("--json", action="store_true", help="Output full JSON data")
    parser.add_argument("--dry-run", action="store_true", help="Show formatted stats blocks")
    parser.add_argument("--type", choices=list(COMPONENT_TYPES.keys()),
                        help="Filter by component type")
    parser.add_argument("-o", "--output", help="Output file")
    args = parser.parse_args()

    if not os.path.exists(args.dcb):
        print(f"ERROR: {args.dcb} not found.")
        sys.exit(1)

    print("Loading DCB...", file=sys.stderr)
    df = DataForge(args.dcb)

    record_indices = find_all_components(df, type_filter=args.type)
    print(f"Found {len(record_indices)} component entities", file=sys.stderr)

    all_components = []
    for ri in record_indices:
        try:
            c = extract_component_data(df, ri)
        except Exception as e:
            print(f"  ERROR: {df.record_filename(ri)}: {e}", file=sys.stderr)
            continue
        if c:
            all_components.append(c)

    all_components.sort(key=lambda c: (c.get("type", ""), c.get("size", 0),
                                       c.get("className", "")))

    if args.json:
        output = [{k: v for k, v in c.items() if not k.startswith("_")}
                  for c in all_components]
        text = json.dumps(output, indent=2, ensure_ascii=False, default=str)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved: {args.output} ({len(output)} components)")
        else:
            print(text)

    elif args.dry_run:
        for c in all_components:
            cn = c.get("className", "?")
            block = format_stats_block(c)
            print(f"--- {cn} (S{c.get('size', '?')} {c['type']}) ---")
            for line in block.split("\\n"):
                print(f"  {line}")
            print()
        print(f"Total: {len(all_components)} components")

    else:
        # Summary tables by type
        current_type = None
        for c in all_components:
            if c["type"] != current_type:
                current_type = c["type"]
                print(f"\n{'=' * 80}")
                print(f" {current_type}")
                print(f"{'=' * 80}")

                if current_type == "PowerPlant":
                    print(f"{'className':<45} {'S':>2} {'G':>2} {'PwrMax':>7} "
                          f"{'HP':>7} {'Disto':>7} {'EM/Seg':>7} {'Mass':>7}")
                elif current_type == "QuantumDrive":
                    print(f"{'className':<45} {'S':>2} {'G':>2} {'Vel Mm/s':>9} "
                          f"{'Spool':>6} {'CD':>7} {'HP':>7} {'EM':>7} {'Pwr':>4}")
                elif current_type == "JumpDrive":
                    print(f"{'className':<45} {'S':>2} {'G':>2} {'Tune':>6} "
                          f"{'Align':>6} {'Fuel':>5} {'HP':>7}")
                elif current_type == "Shield":
                    print(f"{'className':<45} {'S':>2} {'G':>2} {'Pool':>7} "
                          f"{'Regen':>7} {'Time':>6} {'DmgDly':>7} {'DwnDly':>7} "
                          f"{'EnRes':>6} {'HP':>7}")
                elif current_type == "Cooler":
                    print(f"{'className':<45} {'S':>2} {'G':>2} {'Cool':>6} "
                          f"{'EM':>7} {'IR':>7} {'HP':>7}")
                elif current_type == "Radar":
                    print(f"{'className':<45} {'S':>2} {'G':>2} {'AimMin':>7} "
                          f"{'AimMax':>7} {'Buf':>5} {'EM':>7} {'HP':>7}")
                print("-" * 100)

            cn = c.get("className", "?")
            s = c.get("size", 0)
            g = c.get("grade", 0)

            if current_type == "PowerPlant":
                print(f"{cn:<45} {s:>2} {g:>2} {c.get('power_gen', 0):>7} "
                      f"{c.get('hp', 0):>7.0f} {c.get('disto_max', 0):>7.0f} "
                      f"{c.get('em_per_seg', 0):>7.1f} {c.get('mass', 0):>7.0f}")
            elif current_type == "QuantumDrive":
                spd = c.get("drive_speed", 0) / 1e6 if c.get("drive_speed") else 0
                print(f"{cn:<45} {s:>2} {g:>2} {spd:>9.0f} "
                      f"{c.get('spool_time', 0):>6.1f} {c.get('cooldown_time', 0):>7.2f} "
                      f"{c.get('hp', 0):>7.0f} {c.get('em', 0):>7.0f} "
                      f"{c.get('power_draw', 0):>4.0f}")
            elif current_type == "JumpDrive":
                print(f"{cn:<45} {s:>2} {g:>2} {c.get('tuning_rate', 0):>6.2f} "
                      f"{c.get('alignment_rate', 0):>6.2f} "
                      f"{c.get('fuel_multiplier', 0):>5.1f} {c.get('hp', 0):>7.0f}")
            elif current_type == "Shield":
                er = c.get("resist_energy", 0)
                print(f"{cn:<45} {s:>2} {g:>2} {c.get('shield_hp', 0):>7.0f} "
                      f"{c.get('shield_regen', 0):>7.0f} "
                      f"{c.get('shield_regen_time', 0):>6.1f} "
                      f"{c.get('damaged_delay', 0):>7.2f} "
                      f"{c.get('downed_delay', 0):>7.1f} "
                      f"{int(er * 100):>5}% {c.get('hp', 0):>7.0f}")
            elif current_type == "Cooler":
                print(f"{cn:<45} {s:>2} {g:>2} {c.get('cooling', 0):>6.0f} "
                      f"{c.get('em', 0):>7.0f} {c.get('ir', 0):>7.0f} "
                      f"{c.get('hp', 0):>7.0f}")
            elif current_type == "Radar":
                print(f"{cn:<45} {s:>2} {g:>2} {c.get('aim_min', 0):>7.0f} "
                      f"{c.get('aim_max', 0):>7.0f} {c.get('aim_buffer', 0):>5.0f} "
                      f"{c.get('em', 0):>7.0f} {c.get('hp', 0):>7.0f}")

        print(f"\nTotal: {len(all_components)} components")


if __name__ == "__main__":
    main()
