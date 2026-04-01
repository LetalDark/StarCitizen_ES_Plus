#!/usr/bin/env python3
"""
extract_ship_weapons.py — Extract ship weapon stats from Game2.dcb.

Reads EntityClassDefinition and AmmoParams records from the DCB to build
a complete stats block for each ship weapon (WeaponGun).

Can be used standalone (prints a summary table) or imported by
inject_weapon_stats.py via load_dcb_ship_weapons().

Usage:
    python extract_ship_weapons.py                    # Summary table
    python extract_ship_weapons.py --json -o out.json # Export all data
    python extract_ship_weapons.py --dry-run          # Show formatted stats blocks
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path
from parse_dcb import DataForge

BASE_DIR = Path(__file__).resolve().parent
VERSIONS_DIR = BASE_DIR / "versions"


# ---------------------------------------------------------------------------
# DCB extraction helpers
# ---------------------------------------------------------------------------

def _get_component(components, type_name):
    """Get first component of a given type from a list of resolved components."""
    for c in components:
        if isinstance(c, dict) and c.get("__type") == type_name:
            return c
    return None


def _flatten_numeric(obj, prefix=""):
    """Recursively find all non-zero numeric values with their paths."""
    results = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("__"):
                continue
            results.update(_flatten_numeric(v, f"{prefix}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.update(_flatten_numeric(item, f"{prefix}[{i}]"))
    elif isinstance(obj, (int, float)) and obj != 0:
        results[prefix] = obj
    return results


def _find_fire_actions(obj, results, depth=0):
    """Recursively find all fire action params in a weapon component."""
    if not isinstance(obj, dict) or depth > 7:
        return
    t = obj.get("__type", "")

    if "SWeaponActionFireBeamParams" == t:
        info = {"type": "beam", "name": obj.get("name", "")}
        dps = obj.get("damagePerSecond", {})
        if isinstance(dps, dict):
            for k, v in dps.items():
                if isinstance(v, (int, float)) and v != 0:
                    info[f"dps_{k}"] = v
        info["fullDamageRange"] = obj.get("fullDamageRange", 0)
        info["zeroDamageRange"] = obj.get("zeroDamageRange", 0)
        info["heatPerSecond"] = obj.get("heatPerSecond", 0)
        results.append(info)
        return

    if "SWeaponActionFireChargedParams" == t:
        info = {"type": "charged", "chargeTime": obj.get("chargeTime", 0),
                "cooldownTime": obj.get("cooldownTime", 0)}
        results.append(info)

    if t in ("SWeaponActionFireSingleParams", "SWeaponActionFireRapidParams"):
        info = {"type": "fire", "name": obj.get("name", ""),
                "fireRate": obj.get("fireRate", 0),
                "heatPerShot": obj.get("heatPerShot", 0)}
        # Spread from launchParams
        lp = obj.get("launchParams", {})
        if isinstance(lp, dict):
            sp = lp.get("spreadParams", {})
            if isinstance(sp, dict):
                info["spread"] = sp.get("max", 0)
            info["pelletCount"] = lp.get("pelletCount", 1) or 1
        results.append(info)
        return

    if "SWeaponActionFireBurstParams" == t:
        info = {"type": "burst", "name": obj.get("name", ""),
                "fireRate": obj.get("fireRate", 0),
                "burstSize": obj.get("shotCount", 1),
                "heatPerShot": obj.get("heatPerShot", 0)}
        lp = obj.get("launchParams", {})
        if isinstance(lp, dict):
            sp = lp.get("spreadParams", {})
            if isinstance(sp, dict):
                info["spread"] = sp.get("max", 0)
            info["pelletCount"] = lp.get("pelletCount", 1) or 1
        results.append(info)
        return

    if "SWeaponActionSequenceParams" == t:
        seq = obj.get("sequenceEntries", [])
        if isinstance(seq, list) and seq:
            first = seq[0] if isinstance(seq[0], dict) else {}
            info = {"type": "sequence",
                    "delay": first.get("delay", 0),
                    "unit": first.get("unit", ""),
                    "repetitions": first.get("repetitions", 1),
                    "entryCount": len(seq)}
            results.append(info)
            # Recurse into sequence entries to find inner fire actions
            for entry in seq:
                if isinstance(entry, dict):
                    wa = entry.get("weaponAction", {})
                    if isinstance(wa, dict):
                        _find_fire_actions(wa, results, depth + 1)
            return

    if "SWeaponActionDynamicConditionParams" == t:
        conds = obj.get("conditionalWeaponActions", [])
        if isinstance(conds, list):
            for cond in conds:
                if isinstance(cond, dict):
                    wa = cond.get("weaponAction", {})
                    if isinstance(wa, dict):
                        _find_fire_actions(wa, results, depth + 1)
        return

    # Generic recursion
    for k, v in obj.items():
        if isinstance(v, dict):
            _find_fire_actions(v, results, depth + 1)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _find_fire_actions(item, results, depth + 1)


def _calc_rpm(fire_actions):
    """
    Calculate effective RPM from fire actions list.

    Rules:
    1. Sequence: base RPM = sequenceEntries[0].delay
    2. Burst in sequence: RPM × shots_per_burst
    3. Conflict seq.delay vs inner fireRate: use the lower
    4. Charged weapons: RPM = 60 / (chargeTime + cooldownTime + 60/innerFireRate)
    5. Beam: no RPM (DPS is direct)
    """
    has_sequence = False
    seq_delay = 0
    has_charged = False
    charge_time = 0
    cooldown_time = 0
    inner_fire_rate = 0
    burst_size = 1
    is_beam = False

    for fa in fire_actions:
        if fa["type"] == "beam":
            is_beam = True
        elif fa["type"] == "sequence":
            has_sequence = True
            seq_delay = fa["delay"]
        elif fa["type"] == "charged":
            has_charged = True
            charge_time = fa.get("chargeTime", 0)
            cooldown_time = fa.get("cooldownTime", 0)
        elif fa["type"] == "fire":
            if fa.get("fireRate", 0) > 0:
                inner_fire_rate = fa["fireRate"]
        elif fa["type"] == "burst":
            burst_size = fa.get("burstSize", 1) or 1
            if fa.get("fireRate", 0) > 0:
                inner_fire_rate = fa["fireRate"]

    if is_beam:
        return 0  # Beam: DPS is direct, no RPM

    if has_charged and inner_fire_rate > 0:
        # Charged weapon: RPM = 60 / (chargeTime + max(cooldownTime, 60/fireRate))
        # cooldown and fire cycle run in parallel — take the longer one
        cycle = charge_time + max(cooldown_time, 60.0 / inner_fire_rate)
        return round(60.0 / cycle, 1) if cycle > 0 else 0

    if has_sequence and seq_delay > 0:
        rpm = seq_delay
        if inner_fire_rate > 0:
            rpm = min(seq_delay, inner_fire_rate)
        # Burst multiplier
        if burst_size > 1:
            rpm = rpm * burst_size
        return round(rpm, 1)

    if inner_fire_rate > 0:
        return round(inner_fire_rate, 1)

    return 0


def extract_weapon_data(df, entity_path, ammo_path=None):
    """
    Extract all relevant stats from a ship weapon entity and its ammo.

    Returns a dict with all stats needed for formatting, or None if not a weapon.
    """
    # Read entity
    entity_matches = df.find_records(entity_path)
    if not entity_matches:
        return None
    entity = df.read_record(entity_matches[0], max_depth=7)
    components = entity.get("Components", [])
    if not isinstance(components, list):
        return None

    # Check it's a WeaponGun
    attachable = _get_component(components, "SAttachableComponentParams")
    if not attachable:
        return None
    attach_def = attachable.get("AttachDef", {})
    if not isinstance(attach_def, dict):
        return None
    if attach_def.get("Type") != "WeaponGun":
        return None

    result = {
        "entity_path": entity_path,
        "type": attach_def.get("Type", ""),
        "subtype": attach_def.get("SubType", ""),
        "size": attach_def.get("Size", 0),
        "grade": attach_def.get("Grade", 0),
        "tags": attach_def.get("Tags", ""),
    }

    # Localization
    loc = attach_def.get("Localization", {})
    if isinstance(loc, dict):
        result["loc_name"] = loc.get("Name", "")
        result["loc_desc"] = loc.get("Description", "")

    # className from loc_desc: @item_Desc{ClassName} or fallback to entity filename
    desc_key = result.get("loc_desc", "")
    if desc_key.startswith("@item_Desc"):
        result["className"] = desc_key[len("@item_Desc"):]
    else:
        # Fallback: derive from entity path filename
        result["className"] = entity_path.split("/")[-1].replace(".xml", "")

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

    # Ammo container
    ammo_container = _get_component(components, "SAmmoContainerComponentParams")
    if ammo_container:
        result["maxAmmoCount"] = ammo_container.get("maxAmmoCount", 0)
        ammo_ref = ammo_container.get("ammoParamsRecord", {})
        if isinstance(ammo_ref, dict):
            result["ammo_guid"] = ammo_ref.get("__ref", "")

    # Weapon component (fire actions, capacitor, spread)
    weapon_comp = _get_component(components, "SCItemWeaponComponentParams")
    if weapon_comp:
        # Capacitor
        regen = weapon_comp.get("weaponRegenConsumerParams", {})
        if isinstance(regen, dict) and regen.get("regenerationCostPerBullet"):
            result["cap_pool"] = regen.get("maxAmmoLoad", 0)
            result["cap_cost"] = regen.get("regenerationCostPerBullet", 0)
            result["cap_regen"] = regen.get("maxRegenPerSec", 0)
            result["cap_cooldown"] = regen.get("regenerationCooldown", 0)

        # Fire actions
        fire_actions = []
        _find_fire_actions(weapon_comp, fire_actions)
        result["_fire_actions"] = fire_actions

        # RPM
        result["rpm"] = _calc_rpm(fire_actions)

        # Extract spread and pelletCount from fire actions
        for fa in fire_actions:
            if fa["type"] in ("fire", "burst") and fa.get("spread", 0) > 0:
                result["spread"] = fa["spread"]
            if fa["type"] in ("fire", "burst") and fa.get("pelletCount", 1) > 1:
                result["pelletCount"] = fa["pelletCount"]
            if fa["type"] == "beam":
                result["is_beam"] = True
                for k, v in fa.items():
                    if k.startswith("dps_"):
                        result.setdefault("beam_dps", {})[k[4:]] = v
                result["beam_fullRange"] = fa.get("fullDamageRange", 0)
                result["beam_zeroRange"] = fa.get("zeroDamageRange", 0)

    # EM and Power draw
    resource = _get_component(components, "ItemResourceComponentParams")
    if resource:
        flat = _flatten_numeric(resource)
        for path, val in flat.items():
            if "EMSignature.nominalSignature" in path:
                result["em"] = val
                break
        for path, val in flat.items():
            if "consumption" in path and "resourceAmountPerSecond" in path:
                result["power_draw"] = val
                break

    # --- Ammo data ---
    if ammo_path:
        ammo_matches = df.find_records(ammo_path)
        if ammo_matches:
            ammo_data = df.read_record(ammo_matches[0], max_depth=5)
            result["speed"] = ammo_data.get("speed", 0)
            result["lifetime"] = ammo_data.get("lifetime", 0)

            pp = ammo_data.get("projectileParams", {})
            if isinstance(pp, dict):
                # Direct damage
                dmg = pp.get("damage", {})
                if isinstance(dmg, dict):
                    for k in ("DamagePhysical", "DamageEnergy", "DamageDistortion",
                              "DamageThermal", "DamageBiochemical", "DamageStun"):
                        v = dmg.get(k, 0)
                        if isinstance(v, (int, float)) and v > 0.001:  # skip 0.0001 tokens
                            result.setdefault("damage", {})[k] = v

                # Detonation damage (distortion weapons)
                det = pp.get("detonationParams", {})
                if isinstance(det, dict) and det.get("__type"):
                    exp = det.get("explosionParams", {})
                    if isinstance(exp, dict):
                        exp_dmg = exp.get("damage", {})
                        if isinstance(exp_dmg, dict):
                            for k in ("DamagePhysical", "DamageEnergy", "DamageDistortion",
                                      "DamageThermal", "DamageBiochemical", "DamageStun"):
                                v = exp_dmg.get(k, 0)
                                if isinstance(v, (int, float)) and v > 0.001:
                                    result.setdefault("explosion_damage", {})[k] = v
                        result["aoe_min"] = exp.get("minRadius", 0)
                        result["aoe_max"] = exp.get("maxRadius", 0)

                # Penetration
                pen = pp.get("penetrationParams", {})
                if isinstance(pen, dict):
                    result["pen_distance"] = pen.get("basePenetrationDistance", 0)
                    result["pen_near"] = pen.get("nearRadius", 0)
                    result["pen_far"] = pen.get("farRadius", 0)

    # --- Calculated fields ---
    speed = result.get("speed", 0)
    lifetime = result.get("lifetime", 0)
    result["range"] = round(speed * lifetime) if speed and lifetime else 0

    # Alpha: direct damage or explosion damage, × pellets
    pellets = result.get("pelletCount", 1)
    dmg = result.get("damage", {})
    exp_dmg = result.get("explosion_damage", {})

    if exp_dmg:
        # Distortion: explosion damage is the real damage
        alpha_per_pellet = sum(exp_dmg.values())
        result["is_distortion"] = True
    elif dmg:
        alpha_per_pellet = sum(dmg.values())
        result["is_distortion"] = False
    elif result.get("is_beam"):
        alpha_per_pellet = 0  # Beam: DPS is direct
        result["is_distortion"] = False
    else:
        alpha_per_pellet = 0
        result["is_distortion"] = False

    result["alpha_per_pellet"] = round(alpha_per_pellet, 2)
    result["alpha"] = round(alpha_per_pellet * pellets, 2)

    # DPS
    rpm = result.get("rpm", 0)
    if result.get("is_beam"):
        beam_dps = result.get("beam_dps", {})
        result["dps"] = round(sum(beam_dps.values()), 1)
    elif rpm > 0 and result["alpha"] > 0:
        result["dps"] = round(result["alpha"] * rpm / 60.0, 1)
    else:
        result["dps"] = 0

    return result


# ---------------------------------------------------------------------------
# Find all ship weapons in the DCB
# ---------------------------------------------------------------------------

def find_all_ship_weapons(df):
    """
    Find all ship weapon entities and their ammo records in the DCB.

    Returns list of (entity_path, ammo_path) tuples.
    """
    weapons = []

    # 1. Find weapon entities
    entity_records = df.find_records("entities/scitem/ships/weapons/")
    weapon_entities = {}
    for ri in entity_records:
        fname = df.record_filename(ri)
        sname = df.struct_name(df.record_defs[ri]["struct_index"])
        if sname != "EntityClassDefinition":
            continue
        if "/parts/" in fname or "lowpoly" in fname or "_mag" in fname or "ammo_rack" in fname:
            continue
        key = fname.split("/")[-1].replace(".xml", "")
        weapon_entities[key] = fname

    # 2. Find ALL vehicle ammo records (separate search)
    ammo_search = df.find_records("ammoparams/vehicle/")
    ammo_records = {}
    for ri in ammo_search:
        fname = df.record_filename(ri)
        sname = df.struct_name(df.record_defs[ri]["struct_index"])
        if sname != "AmmoParams":
            continue
        if "ammoparams/vehicle/" not in fname:
            continue
        key = fname.split("/")[-1].replace(".xml", "")
        ammo_records[key] = fname

    # 3. Match weapons to ammo
    for weapon_key, entity_path in weapon_entities.items():
        ammo_key = weapon_key + "_ammo"
        ammo_path = ammo_records.get(ammo_key)
        if not ammo_path:
            # Try prefix match: weapon name might differ slightly
            # e.g., ammoparams.klwe_laserrepeater_s1_ammo
            for ak, ap in ammo_records.items():
                if weapon_key in ak:
                    ammo_path = ap
                    break
        weapons.append((entity_path, ammo_path))

    return weapons


# ---------------------------------------------------------------------------
# Format stats block for injection
# ---------------------------------------------------------------------------

def fmt_num(v):
    """Format number: integer if whole, else up to 2 decimals."""
    if v is None or v == 0:
        return "0"
    if isinstance(v, float) and v != int(v):
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(int(v))


def format_stats_block(w):
    """
    Build the stats text block for a ship weapon.

    Format (6 line groups, consistent across all types):
      Line 1: DPS, Alpha, RPM              (Daño)
      Line 2: vel, rango, Disp             (Proyectil)
      Line 3: Pen, Radio                   (Penetración)
      Line 4: Cap/Coste/Reg/CD or Mun      (Sustain)
      Line 5: kg, HP, EM, Energía          (Físico/firma)
      Line 6: AoE (distortion only)
    """
    lines = []

    # --- Line 1: Daño ---
    dps = w.get("dps", 0)
    alpha = w.get("alpha", 0)
    rpm = w.get("rpm", 0)
    pellets = w.get("pelletCount", 1)
    is_dist = w.get("is_distortion", False)
    is_beam = w.get("is_beam", False)

    if is_beam:
        # Beam: DPS direct, no Alpha/RPM
        lines.append(f"DPS: {fmt_num(dps)}")
    else:
        alpha_str = fmt_num(alpha)
        if is_dist:
            alpha_str += " Dist"
        if pellets > 1:
            alpha_per = fmt_num(w.get("alpha_per_pellet", 0))
            alpha_str += f" ({pellets}×{alpha_per})"
        parts = [f"DPS: {fmt_num(dps)}", f"Alpha: {alpha_str}", f"{fmt_num(rpm)} RPM"]
        lines.append(" | ".join(parts))

    # --- Line 2: Proyectil ---
    speed = w.get("speed", 0)
    rng = w.get("range", 0)
    spread = w.get("spread", 0)
    parts2 = []
    if speed:
        parts2.append(f"{fmt_num(speed)} m/s")
    if rng:
        parts2.append(f"{rng}m")
    if spread:
        parts2.append(f"Disp: {fmt_num(spread)}")
    if parts2:
        lines.append(" | ".join(parts2))

    # --- Line 3: Penetración ---
    pen_dist = w.get("pen_distance", 0)
    pen_near = w.get("pen_near", 0)
    pen_far = w.get("pen_far", 0)
    parts3 = []
    if pen_dist:
        parts3.append(f"Pen: {fmt_num(pen_dist)}")
    if pen_near or pen_far:
        parts3.append(f"Radio: {fmt_num(pen_near)}-{fmt_num(pen_far)}")
    if parts3:
        lines.append(" | ".join(parts3))

    # --- Line 4: Sustain ---
    cap_pool = w.get("cap_pool", 0)
    max_ammo = w.get("maxAmmoCount", 0)
    if cap_pool:
        parts4 = [
            f"Cap: {fmt_num(cap_pool)}",
            f"Coste: {fmt_num(w.get('cap_cost', 0))}",
            f"Reg: {fmt_num(w.get('cap_regen', 0))}/s",
            f"CD: {fmt_num(w.get('cap_cooldown', 0))}s",
        ]
        lines.append(" | ".join(parts4))
    elif max_ammo > 0:
        lines.append(f"Mun: {max_ammo}")

    # --- Line 5: Físico/firma ---
    mass = w.get("mass", 0)
    hp = w.get("hp", 0)
    em = w.get("em", 0)
    power = w.get("power_draw", 0)
    parts5 = []
    if mass:
        parts5.append(f"{fmt_num(mass)} kg")
    if hp:
        parts5.append(f"HP: {fmt_num(hp)}")
    if em:  # Omit when 0
        parts5.append(f"EM: {fmt_num(em)}")
    if power:  # Omit when 0
        parts5.append(f"Energía: {fmt_num(power)}")
    if parts5:
        lines.append(" | ".join(parts5))

    # --- Line 6: AoE (distortion only) ---
    aoe_min = w.get("aoe_min", 0)
    aoe_max = w.get("aoe_max", 0)
    if aoe_min or aoe_max:
        lines.append(f"AoE: {fmt_num(aoe_min)}-{fmt_num(aoe_max)}m")

    return "\\n".join(lines)


# ---------------------------------------------------------------------------
# Main loader for inject_weapon_stats.py
# ---------------------------------------------------------------------------

def load_dcb_ship_weapons(dcb_path="Game2.dcb"):
    """
    Load all ship weapon stats from the DCB.

    Returns dict: className (lowercase) -> (weapon_data, "ship", stats_block)
    Compatible with inject_weapon_stats.py weapons dict format.
    """
    if not os.path.exists(dcb_path):
        print(f"ERROR: {dcb_path} not found.", file=sys.stderr)
        print("Extract first: python explore_p4k.py --extract \"Data\\Game2.dcb\" -o Game2.dcb",
              file=sys.stderr)
        return {}

    print("Loading DCB for ship weapons...", file=sys.stderr)
    df = DataForge(dcb_path)
    print(f"  Records: {df.record_def_count:,}", file=sys.stderr)

    weapon_pairs = find_all_ship_weapons(df)
    print(f"  Ship weapon entities found: {len(weapon_pairs)}", file=sys.stderr)

    weapons = {}
    skipped = 0
    errors = 0

    for entity_path, ammo_path in weapon_pairs:
        try:
            w = extract_weapon_data(df, entity_path, ammo_path)
        except Exception as e:
            errors += 1
            print(f"  ERROR extracting {entity_path}: {e}", file=sys.stderr)
            continue

        if w is None or w.get("dps", 0) <= 0:
            skipped += 1
            continue

        # Skip Trident LaserBeam (not implemented)
        if "tras_laserbeam" in entity_path.lower():
            skipped += 1
            continue

        class_name = w.get("className", "").lower()
        if not class_name:
            skipped += 1
            continue

        stats_block = format_stats_block(w)
        weapons[class_name] = (w, "ship", stats_block)

    print(f"  Ship weapons with stats: {len(weapons)}", file=sys.stderr)
    if skipped:
        print(f"  Skipped (no DPS / not weapon): {skipped}", file=sys.stderr)
    if errors:
        print(f"  Errors: {errors}", file=sys.stderr)

    return weapons


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract ship weapon stats from Game2.dcb")
    parser.add_argument("--dcb", default="Game2.dcb", help="Path to Game2.dcb")
    parser.add_argument("--json", action="store_true", help="Output full JSON data")
    parser.add_argument("--dry-run", action="store_true", help="Show formatted stats blocks")
    parser.add_argument("-o", "--output", help="Output file")
    args = parser.parse_args()

    if not os.path.exists(args.dcb):
        print(f"ERROR: {args.dcb} not found.")
        sys.exit(1)

    print("Loading DCB...", file=sys.stderr)
    df = DataForge(args.dcb)

    weapon_pairs = find_all_ship_weapons(df)
    print(f"Found {len(weapon_pairs)} weapon entities", file=sys.stderr)

    all_weapons = []
    for entity_path, ammo_path in weapon_pairs:
        try:
            w = extract_weapon_data(df, entity_path, ammo_path)
        except Exception as e:
            print(f"  ERROR: {entity_path}: {e}", file=sys.stderr)
            continue
        if w and w.get("dps", 0) > 0:
            all_weapons.append(w)

    all_weapons.sort(key=lambda w: (w.get("size", 0), w.get("className", "")))

    if args.json:
        # Remove internal fields
        output = []
        for w in all_weapons:
            clean = {k: v for k, v in w.items() if not k.startswith("_")}
            output.append(clean)
        text = json.dumps(output, indent=2, ensure_ascii=False, default=str)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved: {args.output} ({len(output)} weapons)")
        else:
            print(text)
    elif args.dry_run:
        for w in all_weapons:
            cn = w.get("className", "?")
            block = format_stats_block(w)
            print(f"--- {cn} (S{w.get('size', '?')}) ---")
            for line in block.split("\\n"):
                print(f"  {line}")
            print()
        print(f"Total: {len(all_weapons)} weapons")
    else:
        # Summary table
        print(f"\n{'className':<45} {'S':>2} {'DPS':>8} {'Alpha':>8} {'RPM':>6} "
              f"{'Speed':>6} {'Range':>6} {'Pen':>5} {'Disp':>5} {'Ammo':>6} "
              f"{'Mass':>7} {'HP':>7} {'EM':>6}")
        print("-" * 140)
        for w in all_weapons:
            cn = w.get("className", "?")
            print(f"{cn:<45} {w.get('size', 0):>2} {w.get('dps', 0):>8.1f} "
                  f"{w.get('alpha', 0):>8.1f} {w.get('rpm', 0):>6.1f} "
                  f"{w.get('speed', 0):>6.0f} {w.get('range', 0):>6} "
                  f"{w.get('pen_distance', 0):>5.2f} {w.get('spread', 0):>5.2f} "
                  f"{w.get('maxAmmoCount', 0):>6} {w.get('mass', 0):>7.0f} "
                  f"{w.get('hp', 0):>7.0f} {w.get('em', 0):>6.0f}")
        print(f"\nTotal: {len(all_weapons)} weapons")


if __name__ == "__main__":
    main()
