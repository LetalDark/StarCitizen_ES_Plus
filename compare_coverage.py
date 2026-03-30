#!/usr/bin/env python3
"""
Comparacion definitiva MrKraken vs DCB.
Resuelve nombres internos a display names y compara item por item.
"""

import json
import re


def build_name_map(p4k_path):
    """Build internal_name -> display_name from p4k english."""
    names = {}
    with open(p4k_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            kl = key.lower()
            if kl.startswith("item_name"):
                item_id = key[9:]  # after 'item_Name'
                names[item_id.lower()] = val
    return names


def resolve_bp_name(bp_internal, p4k_names):
    """Resolve internal blueprint name to display name."""
    # Direct match
    if bp_internal.lower() in p4k_names:
        return p4k_names[bp_internal.lower()]

    # Try scitem_ prefix
    if ("scitem_" + bp_internal).lower() in p4k_names:
        return p4k_names[("scitem_" + bp_internal).lower()]

    # Try without underscores
    clean = bp_internal.replace("_", "").lower()
    for k, v in p4k_names.items():
        if clean == k.replace("_", ""):
            return v

    return None


def parse_mk_diff(path):
    """Parse global_diff.ini -> {key: {region: [items]}}."""
    result = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, val = line.split("=", 1)
            if "Potential Blueprints" not in val:
                continue
            regions = {}
            current_region = "ALL"
            parts = val.split("\\n")
            for part in parts:
                part = part.strip()
                m = re.match(r"<EM4>Region\s*(.+?)</EM4>", part)
                if m:
                    current_region = m.group(1).strip()
                    continue
                m = re.match(r"^- (.+)$", part)
                if m:
                    item = m.group(1).strip()
                    if current_region not in regions:
                        regions[current_region] = []
                    regions[current_region].append(item)
            if regions:
                result[key] = regions
    return result


def main():
    # Load p4k names
    p4k_names = build_name_map("versions/4.7.0-LIVE_11545720/sources/global_p4k_en.ini")

    # Load DCB pools
    with open("bp_pools.json") as f:
        pools_raw = json.load(f)
    with open("bp_records.json") as f:
        bp_recs = json.load(f)

    bp_guid_to_file = {}
    for rec in bp_recs:
        fname = rec["__record_filename"].split("/")[-1].replace(".xml", "").replace("bp_craft_", "")
        bp_guid_to_file[rec["__guid"]] = fname

    # Build pool -> [display_names]
    dcb_pools = {}
    dcb_pools_internal = {}
    for p in pools_raw:
        pname = p["__record_filename"].split("/")[-1].replace(".xml", "")
        short = pname.replace("bp_missionreward_", "")
        internals = []
        display_names = []
        for r in p.get("blueprintRewards", []):
            ref = r.get("blueprintRecord")
            if ref and isinstance(ref, dict) and "__ref" in ref:
                bp = bp_guid_to_file.get(ref["__ref"], "?")
                internals.append(bp)
                dn = resolve_bp_name(bp, p4k_names)
                display_names.append(dn if dn else f"[{bp}]")
        dcb_pools[short] = sorted(display_names)
        dcb_pools_internal[short] = internals

    # Load DCB missions
    with open("dcb_mission_pools_verified.json") as f:
        dcb_missions = json.load(f)

    # Load MrKraken
    mk = parse_mk_diff("versions/4.7.0-LIVE_11545720/diff/global_diff.ini")

    # === Flatten MrKraken: each region becomes a separate set ===
    mk_flat = {}  # "key" or "key@REGION" -> sorted items
    for key, regions in mk.items():
        if len(regions) == 1 and "ALL" in regions:
            mk_flat[key] = sorted(regions["ALL"])
        else:
            for region, items in regions.items():
                mk_flat[f"{key}@{region}"] = sorted(items)

    # === For each DCB pool, find MrKraken sets that match by display names ===
    print("=" * 110)
    print("VERIFICACION POOL POR POOL: DCB vs MrKraken")
    print("=" * 110)

    all_matched_mk_keys = set()
    pools_ok = 0
    pools_partial = 0
    pools_nomatch = 0

    for short in sorted(dcb_pools.keys()):
        dcb_items = dcb_pools[short]
        dcb_set = set(dcb_items)
        n_missions = sum(1 for m in dcb_missions
                         if f"bp_missionreward_{short}" in m["pools"])

        # Find MK sets where items are a subset/superset/exact match
        exact_matches = []
        partial_matches = []

        for mk_key, mk_items in mk_flat.items():
            mk_set = set(mk_items)

            if mk_set == dcb_set:
                exact_matches.append(mk_key)
            elif mk_set & dcb_set:
                # Some overlap
                overlap = mk_set & dcb_set
                only_mk = mk_set - dcb_set
                only_dcb = dcb_set - mk_set
                if len(overlap) >= 2:  # meaningful overlap
                    partial_matches.append({
                        "key": mk_key,
                        "overlap": len(overlap),
                        "only_mk": only_mk,
                        "only_dcb": only_dcb,
                    })

        # Output
        if exact_matches:
            status = "OK"
            pools_ok += 1
        elif partial_matches:
            status = "PARCIAL"
            pools_partial += 1
        else:
            status = "NO MATCH"
            pools_nomatch += 1

        print(f"\n[{status:8s}] {short} ({n_missions} misiones DCB, {len(dcb_items)} bps)")

        if exact_matches:
            all_matched_mk_keys.update(exact_matches)
            print(f"  Exact match con {len(exact_matches)} claves MK")
            print(f"  Ejemplo: {exact_matches[0]}")
        elif partial_matches:
            # Sort by overlap descending
            partial_matches.sort(key=lambda x: -x["overlap"])
            best = partial_matches[0]
            print(f"  Mejor match parcial: {best['key']} ({best['overlap']}/{len(dcb_items)} items coinciden)")
            if best["only_dcb"]:
                print(f"  Solo en DCB: {best['only_dcb']}")
            if best["only_mk"]:
                print(f"  Solo en MK:  {best['only_mk']}")
        else:
            print(f"  DCB items: {dcb_items}")

    # === MrKraken keys not matched to any pool ===
    all_mk_keys_in_flat = set(mk_flat.keys())
    unmatched_mk = all_mk_keys_in_flat - all_matched_mk_keys
    # Filter to non-region keys
    unmatched_base = set()
    for k in unmatched_mk:
        base = k.split("@")[0]
        unmatched_base.add(base)

    print()
    print("=" * 110)
    print("RESUMEN")
    print("=" * 110)
    print(f"  DCB pools:     {len(dcb_pools)}")
    print(f"  Exactos:       {pools_ok}")
    print(f"  Parciales:     {pools_partial}")
    print(f"  Sin match MK:  {pools_nomatch}")
    print()
    print(f"  MK claves originales:       {len(mk)}")
    print(f"  MK claves (con regiones):   {len(mk_flat)}")
    print(f"  MK matched exacto a pool:   {len(all_matched_mk_keys)}")
    print(f"  MK sin match exacto:        {len(unmatched_mk)}")


if __name__ == "__main__":
    main()
