#!/usr/bin/env python3
"""Auditoría completa de los diffs de blueprints."""

import re
import sys


def audit_file(path, label):
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    lines = content.strip().split("\n")
    print(f"=== {label} ({path.split('/')[-1]}) ===")
    print(f"Lineas: {len(lines)}")

    issues = []
    entries = {}

    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if "=" not in line:
            issues.append((i, "Sin =", line[:80]))
            continue
        key, val = line.split("=", 1)

        # Store for cross-check
        entries[key] = val

        # 1. NULL GUID
        if "00000000-0000-0000-0000-000000000000" in val:
            issues.append((i, "GUID NULO", key))

        # 2. Extract items (literal \n in file = two chars \ and n)
        items = re.findall(r"\\n- ([^\\]+)", val)
        items = [it.strip() for it in items if it.strip()]

        # 3. Duplicate items
        seen = set()
        for item in items:
            if item in seen:
                issues.append((i, f"Item duplicado: '{item}'", key))
            seen.add(item)

        # 4. EM4 tags
        if "Potential Blueprints" in val or "Posibles Planos" in val:
            # Check balanced tags
            opens = val.count("<EM4>")
            closes = val.count("</EM4>")
            if opens != closes:
                issues.append((i, f"EM4 tags desbalanceados: {opens} open, {closes} close", key))

            # Check region tags not empty
            for m in re.finditer(r"<EM4>Region\s*([^<]*)</EM4>", val):
                if not m.group(1).strip():
                    issues.append((i, "Region vacia", key))

        # 5. Items that look like internal names (not display names)
        for item in items:
            if re.match(r"^[a-z]+_[a-z]+_[a-z]+_\d+", item):
                issues.append((i, f"Nombre interno?: '{item}'", key))

        # 6. Encoding issues
        if "\x00" in val:
            issues.append((i, "Null byte en valor", key))

        # 7. Empty blueprint section
        if ("Potential Blueprints" in val or "Posibles Planos" in val) and len(items) == 0:
            issues.append((i, "Blueprint section sin items", key))

        # 8. Very long GUID-like strings that aren't the null GUID
        for m in re.finditer(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", val):
            guid = m.group(0)
            if guid != "00000000-0000-0000-0000-000000000000":
                issues.append((i, f"GUID no-nulo en texto: {guid}", key))

    if issues:
        print(f"\nProblemas encontrados: {len(issues)}")
        for lineno, issue_type, detail in issues:
            print(f"  L{lineno}: [{issue_type}] {detail}")
    else:
        print("\nSin problemas")

    print()
    return entries, issues


def main():
    en_entries, en_issues = audit_file(
        "versions/4.7.0-LIVE_11545720/diff/global_diff.ini", "EN"
    )
    es_entries, es_issues = audit_file(
        "versions/4.7.0-LIVE_11545720/diff/global_diff_es.ini", "ES"
    )

    # Cross-check: same keys in both?
    print("=== CROSS-CHECK EN vs ES ===")
    en_keys = set(en_entries.keys())
    es_keys = set(es_entries.keys())

    only_en = en_keys - es_keys
    only_es = es_keys - en_keys

    if only_en:
        print(f"\nClaves solo en EN ({len(only_en)}):")
        for k in sorted(only_en):
            print(f"  {k}")

    if only_es:
        print(f"\nClaves solo en ES ({len(only_es)}):")
        for k in sorted(only_es):
            print(f"  {k}")

    if not only_en and not only_es:
        print(f"Mismas {len(en_keys)} claves en ambos archivos")

    # Check item count per key matches
    print("\n=== ITEM COUNT CHECK ===")
    mismatches = 0
    for key in sorted(en_keys & es_keys):
        en_items = re.findall(r"\\n- ([^\\]+)", en_entries[key])
        es_items = re.findall(r"\\n- ([^\\]+)", es_entries[key])
        en_items = [it.strip() for it in en_items if it.strip()]
        es_items = [it.strip() for it in es_items if it.strip()]
        if len(en_items) != len(es_items):
            mismatches += 1
            print(f"  {key}: EN={len(en_items)} items, ES={len(es_items)} items")

    if mismatches == 0:
        print(f"Todas las {len(en_keys & es_keys)} claves tienen el mismo numero de items")

    # Check region consistency
    print("\n=== REGION CHECK ===")
    region_mismatches = 0
    for key in sorted(en_keys & es_keys):
        en_regions = re.findall(r"<EM4>Region\s*([^<]+)</EM4>", en_entries[key])
        es_regions = re.findall(r"<EM4>Region\s*([^<]+)</EM4>", es_entries[key])
        # Regions should NOT be translated
        if en_regions != es_regions:
            region_mismatches += 1
            print(f"  {key}: EN regions={en_regions}, ES regions={es_regions}")

    if region_mismatches == 0:
        print(f"Regiones consistentes en todas las claves")

    # Summary
    print("\n=== RESUMEN ===")
    total_issues = len(en_issues) + len(es_issues)
    print(f"Issues EN: {len(en_issues)}")
    print(f"Issues ES: {len(es_issues)}")
    print(f"Cross-check keys: {'OK' if not only_en and not only_es else 'FAIL'}")
    print(f"Item count: {'OK' if mismatches == 0 else f'{mismatches} mismatches'}")
    print(f"Regions: {'OK' if region_mismatches == 0 else f'{region_mismatches} mismatches'}")


if __name__ == "__main__":
    main()
