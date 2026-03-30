#!/usr/bin/env python3
"""
Extrae la cadena completa Mision -> BlueprintPool desde el DCB.
Encuentra BlueprintRewards (462 instancias) embebidos en MissionBrokerEntry,
extrae el pool GUID referenciado, y lo cruza con el MrKraken diff.
"""

import json
import re
import struct
import sys
from parse_dcb import DataForge


def guid_to_bytes(guid_str):
    """Encode GUID in DCB byte order."""
    parts = guid_str.split("-")
    a = int(parts[0], 16)
    b = int(parts[1], 16)
    c = int(parts[2], 16)
    de = int(parts[3], 16)
    d = (de >> 8) & 0xFF
    e = de & 0xFF
    rest = parts[4]
    f_b, g, h, i, j, k = (int(rest[x:x+2], 16) for x in range(0, 12, 2))
    return struct.pack("<HHI8B", c, b, a, k, j, i, h, g, f_b, e, d)


def read_guid_at(data, pos):
    """Read DCB GUID at position, return as string."""
    c, b, a = struct.unpack_from("<HHI", data, pos)
    tail = struct.unpack_from("8B", data, pos + 8)
    k, j, i, h, g, f, e, d = tail
    return f"{a:08x}-{b:04x}-{c:04x}-{d:02x}{e:02x}-{f:02x}{g:02x}{h:02x}{i:02x}{j:02x}{k:02x}"


def main():
    print("Cargando DataForge...", file=sys.stderr)
    df = DataForge("Game2.dcb")

    # Load pool data
    with open("bp_pools.json") as f:
        pools = json.load(f)
    with open("bp_records.json") as f:
        bp_records = json.load(f)

    # GUID -> pool name + blueprints
    bp_guid_to_file = {}
    for rec in bp_records:
        fname = rec["__record_filename"].split("/")[-1].replace(".xml", "").replace("bp_craft_", "")
        bp_guid_to_file[rec["__guid"]] = fname

    pool_by_guid = {}
    for pool in pools:
        pname = pool["__record_filename"].split("/")[-1].replace(".xml", "")
        bps = []
        for reward in pool.get("blueprintRewards", []):
            ref = reward.get("blueprintRecord")
            if ref and isinstance(ref, dict) and "__ref" in ref:
                bps.append(bp_guid_to_file.get(ref["__ref"], "?"))
        pool_by_guid[pool["__guid"]] = {"name": pname, "blueprints": bps}

    # Find BlueprintRewards struct (462 instances, 32B each)
    # It has: missionResults (ClassArray, 8B), chance (Single, 4B), blueprintPool (Reference, 20B)
    # So blueprintPool starts at offset 12 within the struct
    # The reference is: 4 bytes item1 + 16 bytes GUID

    br_si = None
    for i, sd in enumerate(df.struct_defs):
        if df.struct_name(i) == "BlueprintRewards":
            br_si = i
            break

    br_sd = df.struct_defs[br_si]
    br_dm = df.data_mappings[br_si]
    br_base = df.data_offset + df.struct_data_offsets.get(br_si, 0)
    print(f"BlueprintRewards: {br_dm['struct_count']} instances at {br_base:#x}, {br_sd['record_size']}B each", file=sys.stderr)

    # Read all BlueprintRewards instances - extract pool GUID
    br_to_pool = {}  # br_instance_index -> pool_guid
    for vi in range(br_dm["struct_count"]):
        inst = br_base + br_sd["record_size"] * vi
        # blueprintPool is a Reference at offset 12
        # Reference = 4 bytes item1 + 16 bytes GUID
        pool_guid = read_guid_at(df.data, inst + 12 + 4)
        if pool_guid != "00000000-0000-0000-0000-000000000000":
            br_to_pool[vi] = pool_guid

    print(f"  {len(br_to_pool)} BlueprintRewards con pool asignado", file=sys.stderr)

    # Now find which MissionBrokerEntry contains each BlueprintRewards
    # BlueprintRewards inherits from ContractResultBase
    # ContractResults.contractResults is a StrongPointer array to ContractResultBase
    # We need to find StrongPointer values pointing to BlueprintRewards struct

    # Search in strong pointer array for pointers to br_si
    br_ptr_refs = {}  # strong_ptr_index -> br_variant_index
    for i, (si, vi, pad) in enumerate(df.strong_values):
        if si == br_si:
            br_ptr_refs[i] = vi

    print(f"  {len(br_ptr_refs)} strong pointers to BlueprintRewards", file=sys.stderr)

    # Now find MissionBrokerEntry records
    mbe_si = None
    for i, sd in enumerate(df.struct_defs):
        if df.struct_name(i) == "MissionBrokerEntry":
            mbe_si = i
            break

    mbe_sd = df.struct_defs[mbe_si]
    mbe_base = df.data_offset + df.struct_data_offsets.get(mbe_si, 0)

    # For each MBE, read description key and find its blueprint pools
    # We need to find the modifiers/properties that contain StrongPointers to BlueprintRewards

    # First, let's find which property offset contains the relevant data
    # MissionBrokerEntry has 'modifiers' (StrongPointer array to BaseMissionModifier)
    # and 'properties' (ClassArray of MissionProperty)

    # Actually, let's search through ALL StrongPointer arrays in MBE data
    # to find which ones reference BlueprintRewards

    # Let me find ContractResults struct first
    cr_si = None
    for i, sd in enumerate(df.struct_defs):
        if df.struct_name(i) == "ContractResults":
            cr_si = i
            break

    cr_sd = df.struct_defs[cr_si]
    cr_dm = df.data_mappings[cr_si]
    cr_base = df.data_offset + df.struct_data_offsets.get(cr_si, 0)
    print(f"ContractResults: {cr_dm['struct_count']} instances, {cr_sd['record_size']}B", file=sys.stderr)

    # ContractResults has contractResults: StrongPointer array (8B = count + firstIndex)
    # Read each ContractResults instance to find which ones contain BlueprintRewards pointers
    cr_to_br = {}  # ContractResults variant -> [BlueprintRewards variant indices]
    for vi in range(cr_dm["struct_count"]):
        inst = cr_base + cr_sd["record_size"] * vi
        # contractResults is first property (offset 0), it's an array: count(4) + firstIndex(4)
        count, first = struct.unpack_from("<II", df.data, inst)
        for ai in range(count):
            ptr_idx = first + ai
            if ptr_idx in br_ptr_refs:
                if vi not in cr_to_br:
                    cr_to_br[vi] = []
                cr_to_br[vi].append(br_ptr_refs[ptr_idx])

    print(f"  {len(cr_to_br)} ContractResults con BlueprintRewards", file=sys.stderr)

    # Now find MBE -> ContractResults link
    # MBE has 'partialRewardPayout' which is StrongPointer to PartialContractRewards
    # Look for PartialContractRewards
    pcr_si = None
    for i, sd in enumerate(df.struct_defs):
        if df.struct_name(i) == "PartialContractRewards":
            pcr_si = i
            break

    if pcr_si:
        pcr_sd = df.struct_defs[pcr_si]
        pcr_dm = df.data_mappings[pcr_si]
        pcr_base = df.data_offset + df.struct_data_offsets.get(pcr_si, 0)
        print(f"PartialContractRewards: {pcr_dm['struct_count']} instances, {pcr_sd['record_size']}B", file=sys.stderr)

        # Show PartialContractRewards struct
        props = df.struct_properties(pcr_si)
        print("  Properties:", file=sys.stderr)
        for pi in props:
            pd = df.prop_defs[pi]
            pname = df.prop_name(pi)
            from parse_dcb import DT_NAMES
            dtype = DT_NAMES.get(pd["data_type"], hex(pd["data_type"]))
            ct = pd["conv_type"]
            print(f"    {pname}: {dtype} (conv={ct})", file=sys.stderr)

    # Alternative approach: search for which structs have StrongPointer to ContractResults
    print("\nBuscando structs con punteros a ContractResults...", file=sys.stderr)
    for pi, pd in enumerate(df.prop_defs):
        if pd["data_type"] in (0x0110, 0x0210) and pd["index"] == cr_si:
            pname = df.prop_name(pi)
            # find parent struct
            for si2, sd2 in enumerate(df.struct_defs):
                if sd2["first_prop"] <= pi < sd2["first_prop"] + sd2["prop_count"]:
                    print(f"  {df.struct_name(si2)}.{pname} -> ContractResults", file=sys.stderr)
                    break

    # Find PartialContractRewards -> ContractResults connection
    print("\nBuscando PartialContractRewards -> ContractResults...", file=sys.stderr)
    for pi, pd in enumerate(df.prop_defs):
        pname = df.prop_name(pi)
        if pd["data_type"] in (0x0110, 0x0010) and pd["index"] == cr_si:
            for si2, sd2 in enumerate(df.struct_defs):
                if sd2["first_prop"] <= pi < sd2["first_prop"] + sd2["prop_count"]:
                    print(f"  {df.struct_name(si2)}.{pname} -> ContractResults (dt={pd['data_type']:#x})", file=sys.stderr)

    # Let's check StrongPointers to ContractResults
    cr_ptrs = {}
    for i, (si, vi, pad) in enumerate(df.strong_values):
        if si == cr_si:
            cr_ptrs[i] = vi

    print(f"  {len(cr_ptrs)} strong pointers to ContractResults", file=sys.stderr)

    # PartialContractRewards - read instances and find ContractResults refs
    if pcr_si:
        pcr_to_cr = {}
        for vi in range(pcr_dm["struct_count"]):
            inst = pcr_base + pcr_sd["record_size"] * vi
            # Read the full instance to find ContractResults pointers
            # Need to know the layout - let's read it with parse_dcb
            data = df.read_instance(pcr_si, vi, max_depth=1)
            # Look for any key that might reference ContractResults
            for k, v in data.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and item.get("__type") == "ContractResults":
                            # Found it!
                            pcr_to_cr[vi] = data
                            break

        print(f"  {len(pcr_to_cr)} PartialContractRewards con ContractResults", file=sys.stderr)

    # Now find MBE -> PartialContractRewards link
    # MBE.partialRewardPayout is a StrongPointer to PartialContractRewards
    # Find the offset of partialRewardPayout in MBE

    props = df.struct_properties(mbe_si)
    offset = 0
    partial_offset = None

    for pi in props:
        pd = df.prop_defs[pi]
        pname = df.prop_name(pi)
        ct = pd["conv_type"]
        dt = pd["data_type"]

        if pname == "partialRewardPayout":
            partial_offset = offset

        # Calculate size
        if ct != 0:  # array
            offset += 8
        elif dt == 0x0001:
            offset += 1
        elif dt in (0x0002, 0x0006):
            offset += 1
        elif dt in (0x0003, 0x0007):
            offset += 2
        elif dt in (0x0004, 0x0008):
            offset += 4
        elif dt in (0x0005, 0x0009):
            offset += 8
        elif dt in (0x000A, 0x000D, 0x000F):
            offset += 4
        elif dt == 0x000B:
            offset += 4
        elif dt == 0x000C:
            offset += 8
        elif dt == 0x000E:
            offset += 16
        elif dt in (0x0110, 0x0210):
            offset += 8
        elif dt == 0x0310:
            offset += 20
        elif dt == 0x0010:
            sub_sd = df.struct_defs[pd["index"]]
            offset += sub_sd["record_size"]
        else:
            offset += 4

    print(f"\npartialRewardPayout offset in MBE: {partial_offset}", file=sys.stderr)

    # Also find description offset
    desc_offset = 37  # from previous analysis
    title_offset = 29

    # For each MBE, read: description, title, partialRewardPayout pointer
    mission_pools = []  # {desc, title, filename, pools: [pool_name]}

    pcr_ptrs = {}
    for i, (si, vi, pad) in enumerate(df.strong_values):
        if si == pcr_si:
            pcr_ptrs[i] = vi

    for ri in df.records_by_struct.get(mbe_si, []):
        rec = df.record_defs[ri]
        inst = mbe_base + mbe_sd["record_size"] * rec["variant_index"]

        # Read description
        desc_off = struct.unpack_from("<I", df.data, inst + desc_offset)[0]
        title_off_val = struct.unpack_from("<I", df.data, inst + title_offset)[0]
        try:
            desc = df._get_text(desc_off)
        except:
            desc = ""
        try:
            title = df._get_text(title_off_val)
        except:
            title = ""

        # Read partialRewardPayout (StrongPointer: uint32 struct_idx, uint16 variant, uint16 pad)
        ptr_si, ptr_vi, _ = struct.unpack_from("<IHH", df.data, inst + partial_offset)

        pools_for_mission = []
        if ptr_si == pcr_si and ptr_vi < pcr_dm["struct_count"]:
            # Read the PartialContractRewards instance
            pcr_inst = pcr_base + pcr_sd["record_size"] * ptr_vi
            # Read its properties to find ContractResults
            pcr_data = df.read_instance(pcr_si, ptr_vi, max_depth=3)

            # Recursively search for blueprintPool references
            def find_pools(obj, depth=0):
                results = []
                if depth > 5:
                    return results
                if isinstance(obj, dict):
                    if "__ref" in obj:
                        guid = obj["__ref"]
                        if guid in pool_by_guid:
                            results.append(pool_by_guid[guid]["name"])
                    for v in obj.values():
                        results.extend(find_pools(v, depth + 1))
                elif isinstance(obj, list):
                    for item in obj:
                        results.extend(find_pools(item, depth + 1))
                return results

            pools_for_mission = find_pools(pcr_data)

        if pools_for_mission:
            fname = df.record_filename(ri)
            mission_pools.append({
                "description": desc,
                "title": title,
                "filename": fname,
                "pools": pools_for_mission,
            })

    print(f"\n{len(mission_pools)} misiones con blueprint pools encontrados", file=sys.stderr)

    # Output results
    for m in sorted(mission_pools, key=lambda x: x["description"]):
        print(f"\n{m['description']}")
        print(f"  Title: {m['title']}")
        print(f"  File: {m['filename']}")
        for p in m["pools"]:
            pool_data = None
            for guid, info in pool_by_guid.items():
                if info["name"] == p:
                    pool_data = info
                    break
            if pool_data:
                print(f"  Pool: {p} ({len(pool_data['blueprints'])} blueprints)")
                for bp in pool_data["blueprints"]:
                    print(f"    - {bp}")
            else:
                print(f"  Pool: {p}")

    # Save
    with open("mission_blueprint_map.json", "w", encoding="utf-8") as f:
        json.dump(mission_pools, f, indent=2, ensure_ascii=False)
    print(f"\nGuardado: mission_blueprint_map.json", file=sys.stderr)


if __name__ == "__main__":
    main()
