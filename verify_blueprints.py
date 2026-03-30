#!/usr/bin/env python3
"""Verifica blueprints de MrKraken contra Game2.dcb."""

import json
import re
import sys


def parse_diff(path):
    """Parse global_diff.ini -> {mission_key: {items: [], regions: []}}."""
    result = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, val = line.split("=", 1)
            if "Potential Blueprints" not in val:
                continue
            # Items: literal \n- ItemName\n in file
            items = re.findall(r"\\n- ([^\\]+)", val)
            items = [i.strip() for i in items if i.strip()]
            regions = re.findall(r"<EM4>Region\s*([^<]+)</EM4>", val)
            if items:
                result[key] = {"items": items, "regions": regions}
    return result


def load_dcb(pools_path, records_path):
    """Load DCB pools -> {pool_name: [internal_bp_names]}."""
    with open(pools_path) as f:
        pools = json.load(f)
    with open(records_path) as f:
        records = json.load(f)

    guid_to_bp = {}
    for rec in records:
        fname = rec["__record_filename"].split("/")[-1]
        fname = fname.replace(".xml", "").replace("bp_craft_", "")
        guid_to_bp[rec["__guid"]] = fname

    dcb_pools = {}
    for pool in pools:
        pname = pool["__record_filename"].split("/")[-1].replace(".xml", "")
        bps = []
        for reward in pool.get("blueprintRewards", []):
            ref = reward.get("blueprintRecord")
            if ref and isinstance(ref, dict) and "__ref" in ref:
                bps.append(guid_to_bp.get(ref["__ref"], f"?:{ref['__ref'][:8]}"))
        dcb_pools[pname] = bps

    return dcb_pools


def main():
    mk = parse_diff("versions/4.7.0-LIVE_11545720/diff/global_diff.ini")
    dcb = load_dcb("bp_pools.json", "bp_records.json")

    print(f"MrKraken: {len(mk)} misiones con blueprints")
    print(f"DCB: {len(dcb)} pools, {sum(len(v) for v in dcb.values())} blueprints total\n")

    # Group MrKraken by unique item set
    mk_groups = {}
    for key, data in mk.items():
        fp = tuple(sorted(data["items"]))
        if fp not in mk_groups:
            mk_groups[fp] = {"keys": [], "regions": data["regions"], "items": data["items"]}
        mk_groups[fp]["keys"].append(key)

    print(f"MrKraken: {len(mk_groups)} conjuntos unicos de blueprints\n")

    # For each MrKraken group, check item count vs DCB pool
    ok = 0
    diff = 0
    nomatch = 0

    for fp, info in sorted(mk_groups.items(), key=lambda x: -len(x[1]["keys"])):
        mk_count = len(fp)
        n_missions = len(info["keys"])
        example = info["keys"][0]
        regions = info["regions"]

        # Count per-region if regions exist
        if regions:
            # Items split across regions - total count includes all regions
            pass

        # Try match DCB pool
        best = None
        for pool_name in dcb.keys():
            ps = pool_name.replace("bp_missionreward_", "").lower()
            el = example.lower()
            # Match by significant substrings
            parts = [p for p in ps.split("_") if len(p) > 3]
            if any(p in el for p in parts):
                if best is None or len(ps) > len(best.replace("bp_missionreward_", "")):
                    best = pool_name

        dcb_count = len(dcb[best]) if best else 0
        status = ""
        if best is None:
            status = "NO MATCH"
            nomatch += 1
        elif regions:
            # Multi-region: MrKraken items = sum of all regions, DCB has separate pools
            status = f"MULTI-REGION ({len(regions)} regiones)"
        elif mk_count == dcb_count:
            status = "OK"
            ok += 1
        else:
            status = f"DIFERENTE (MK:{mk_count} vs DCB:{dcb_count})"
            diff += 1

        pool_short = best.replace("bp_missionreward_", "") if best else "?"
        print(f"[{status:20s}] {n_missions:>3} misiones, {mk_count:>2} items | pool: {pool_short:50s} | ej: {example}")
        if status.startswith("DIFERENTE"):
            print(f"  MrKraken items: {sorted(fp)[:5]}...")
            print(f"  DCB items:      {dcb[best][:5]}...")

    print(f"\n{'=' * 60}")
    print(f"OK:         {ok:>4} conjuntos (items coinciden)")
    print(f"Diferente:  {diff:>4} conjuntos")
    print(f"Multi-reg:  {len([g for g in mk_groups.values() if g['regions']]):>4} conjuntos (necesitan verificacion manual)")
    print(f"Sin match:  {nomatch:>4} conjuntos")
    print(f"Total:      {len(mk_groups):>4} conjuntos ({len(mk)} misiones)")


if __name__ == "__main__":
    main()
