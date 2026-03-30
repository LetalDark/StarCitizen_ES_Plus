#!/usr/bin/env python3
"""
Explora el contenido del Data.p4k de Star Citizen.

Uso:
    python explore_p4k.py --search blueprint          # Buscar archivos con "blueprint" en el nombre
    python explore_p4k.py --search entityClassDef      # Buscar entityClassDefs
    python explore_p4k.py --search reward              # Buscar archivos de recompensas
    python explore_p4k.py --search loot                # Buscar tablas de loot
    python explore_p4k.py --prefix "Data\\Libs"        # Listar archivos bajo un prefijo
    python explore_p4k.py --extract "ruta/al/archivo"  # Extraer un archivo concreto
    python explore_p4k.py --stats                      # Mostrar estadisticas de carpetas
"""

import argparse
import os
import re
import struct
import sys

try:
    import zstandard
except ImportError:
    print("Error: necesitas instalar zstandard:")
    print("  pip install zstandard")
    sys.exit(1)

# Importar funciones comunes de extract_p4k
from extract_p4k import find_data_p4k, find_eocd, parse_zip64_extra, extract_file


def scan_all_entries(f, cd_offset, total_entries, filter_fn=None):
    """Escanea el Central Directory completo, opcionalmente filtrando."""
    f.seek(cd_offset)
    results = {}

    for i in range(total_entries):
        header = f.read(46)
        if len(header) < 46 or header[:4] != b"PK\x01\x02":
            break

        (
            _, _, _, flags, method, _, _, crc,
            comp_size, uncomp_size, name_len, extra_len, comment_len,
            _, _, _, local_offset,
        ) = struct.unpack("<4sHHHHHHIIIHHHHHII", header)

        name_bytes = f.read(name_len)
        extra_bytes = f.read(extra_len)
        f.read(comment_len)

        name = name_bytes.decode("utf-8", errors="replace")

        if filter_fn and not filter_fn(name):
            continue

        zip64 = parse_zip64_extra(extra_bytes)
        results[name] = {
            "method": method,
            "comp_size": zip64.get("comp_size", comp_size),
            "uncomp_size": zip64.get("uncomp_size", uncomp_size),
            "offset": zip64.get("offset", local_offset),
        }

        if (i + 1) % 100000 == 0:
            print(f"  Escaneadas {i+1:,} entradas...", file=sys.stderr)

    return results


def main():
    parser = argparse.ArgumentParser(description="Explora el Data.p4k de Star Citizen")
    parser.add_argument("--search", help="Buscar archivos cuyo nombre contenga este texto (case-insensitive)")
    parser.add_argument("--regex", help="Buscar archivos con regex en el nombre")
    parser.add_argument("--prefix", help="Listar archivos bajo este prefijo")
    parser.add_argument("--extract", help="Extraer un archivo concreto a stdout o a --output")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadisticas de carpetas de primer nivel")
    parser.add_argument("--sc-path", help="Ruta a la carpeta de SC")
    parser.add_argument("-o", "--output", help="Archivo de salida para --extract")
    parser.add_argument("--max", type=int, default=200, help="Max resultados a mostrar (default: 200)")
    args = parser.parse_args()

    p4k_path = find_data_p4k(args.sc_path)
    file_size = os.path.getsize(p4k_path)
    print(f"Data.p4k: {file_size / (1024**3):.1f} GB", file=sys.stderr)

    with open(p4k_path, "rb") as f:
        print("Leyendo estructura ZIP64...", file=sys.stderr)
        cd_offset, cd_size, total_entries = find_eocd(f, file_size)
        print(f"Entradas totales: {total_entries:,}", file=sys.stderr)

        # Definir filtro
        filter_fn = None
        if args.search:
            term = args.search.lower()
            filter_fn = lambda name: term in name.lower()
        elif args.regex:
            pattern = re.compile(args.regex, re.IGNORECASE)
            filter_fn = lambda name: pattern.search(name) is not None
        elif args.prefix:
            prefix = args.prefix
            filter_fn = lambda name: name.startswith(prefix)
        elif args.extract:
            target = args.extract.replace("/", "\\")
            filter_fn = lambda name: name.replace("/", "\\") == target or name == args.extract

        if args.extract:
            print(f"Buscando: {args.extract}", file=sys.stderr)
            entries = scan_all_entries(f, cd_offset, total_entries, filter_fn)
            if not entries:
                print("No se encontro el archivo.", file=sys.stderr)
                sys.exit(1)
            path, info = next(iter(entries.items()))
            print(f"Extrayendo: {path} ({info['uncomp_size'] / 1024:.1f} KB)", file=sys.stderr)
            data = extract_file(f, info)
            if args.output:
                with open(args.output, "wb") as out:
                    out.write(data)
                print(f"Guardado: {args.output}", file=sys.stderr)
            else:
                # Intentar decodificar como texto
                try:
                    text = data.decode("utf-8-sig")
                    print(text)
                except UnicodeDecodeError:
                    print(f"Archivo binario ({len(data)} bytes). Usa -o para guardarlo.", file=sys.stderr)
            return

        if args.stats:
            print("Escaneando todas las entradas...", file=sys.stderr)
            entries = scan_all_entries(f, cd_offset, total_entries)
            # Agrupar por carpeta de primer y segundo nivel
            folders = {}
            for name in entries:
                parts = name.replace("/", "\\").split("\\")
                key = parts[0] if len(parts) > 0 else "(root)"
                if key not in folders:
                    folders[key] = {"count": 0, "size": 0}
                folders[key]["count"] += 1
                folders[key]["size"] += entries[name]["uncomp_size"]

            print(f"\n{'Carpeta':<50} {'Archivos':>10} {'Tamano':>12}")
            print("-" * 74)
            for folder in sorted(folders, key=lambda k: folders[k]["size"], reverse=True):
                info = folders[folder]
                size_mb = info["size"] / (1024 * 1024)
                print(f"{folder:<50} {info['count']:>10,} {size_mb:>10.1f} MB")
            return

        # Busqueda o listado
        print("Escaneando...", file=sys.stderr)
        entries = scan_all_entries(f, cd_offset, total_entries, filter_fn)

    if not entries:
        print("No se encontraron archivos.")
        return

    print(f"\nEncontrados: {len(entries):,} archivos")
    if len(entries) > args.max:
        print(f"(mostrando primeros {args.max}, usa --max para ver mas)\n")

    for i, (name, info) in enumerate(sorted(entries.items())):
        if i >= args.max:
            break
        size = info["uncomp_size"]
        if size > 1024 * 1024:
            size_str = f"{size / (1024*1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        print(f"  {name:<90} {size_str:>10}")


if __name__ == "__main__":
    main()
