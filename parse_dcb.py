#!/usr/bin/env python3
"""
Parser del DataForge Binary (Game2.dcb) de Star Citizen.

Lee la base de datos central de gameplay y permite explorar:
- Definiciones de items, armas, armaduras
- Tablas de loot y recompensas de misiones
- Blueprints y recetas de crafting
- Cualquier dato de configuración del juego

Uso:
    python parse_dcb.py                        # Resumen de structs y records
    python parse_dcb.py --list-structs         # Listar todos los tipos de struct
    python parse_dcb.py --search blueprint     # Buscar structs/records con "blueprint"
    python parse_dcb.py --search loot          # Buscar tablas de loot
    python parse_dcb.py --struct MissionBroker # Ver propiedades de un struct
    python parse_dcb.py --records MissionBroker # Listar records de un tipo
    python parse_dcb.py --record <name>        # Volcar un record completo
    python parse_dcb.py --dump <name> -o out.json  # Exportar a JSON
"""

import argparse
import json
import struct
import sys
import os
from collections import defaultdict

# === EDataType ===
DT_BOOLEAN       = 0x0001
DT_INT8          = 0x0002
DT_INT16         = 0x0003
DT_INT32         = 0x0004
DT_INT64         = 0x0005
DT_UINT8         = 0x0006
DT_UINT16        = 0x0007
DT_UINT32        = 0x0008
DT_UINT64        = 0x0009
DT_STRING        = 0x000A
DT_SINGLE        = 0x000B
DT_DOUBLE        = 0x000C
DT_LOCALE        = 0x000D
DT_GUID          = 0x000E
DT_ENUM          = 0x000F
DT_CLASS         = 0x0010
DT_STRONG_PTR    = 0x0110
DT_WEAK_PTR      = 0x0210
DT_REFERENCE     = 0x0310

DT_NAMES = {
    DT_BOOLEAN: "Boolean", DT_INT8: "Int8", DT_INT16: "Int16",
    DT_INT32: "Int32", DT_INT64: "Int64", DT_UINT8: "UInt8",
    DT_UINT16: "UInt16", DT_UINT32: "UInt32", DT_UINT64: "UInt64",
    DT_STRING: "String", DT_SINGLE: "Single", DT_DOUBLE: "Double",
    DT_LOCALE: "Locale", DT_GUID: "Guid", DT_ENUM: "Enum",
    DT_CLASS: "Class", DT_STRONG_PTR: "StrongPointer",
    DT_WEAK_PTR: "WeakPointer", DT_REFERENCE: "Reference",
}

# EConversionType
CT_ATTRIBUTE     = 0x00
CT_COMPLEX_ARRAY = 0x01
CT_SIMPLE_ARRAY  = 0x02
CT_CLASS_ARRAY   = 0x03


class DataForge:
    def __init__(self, filepath):
        with open(filepath, "rb") as f:
            self.data = f.read()
        self.pos = 0
        self._parse_header()
        self._parse_definitions()
        self._parse_value_arrays()
        self._parse_string_tables()
        self._build_data_offset_map()
        self._build_record_index()

    # --- Low-level readers ---

    def _read(self, fmt, size=None):
        if size is None:
            size = struct.calcsize(fmt)
        val = struct.unpack_from(fmt, self.data, self.pos)
        self.pos += size
        return val[0] if len(val) == 1 else val

    def _read_at(self, fmt, offset):
        val = struct.unpack_from(fmt, self.data, offset)
        return val[0] if len(val) == 1 else val

    def _read_guid(self, offset=None):
        if offset is not None:
            self.pos = offset
        c, b, a = struct.unpack_from("<hhI", self.data, self.pos)
        self.pos += 8
        tail = struct.unpack_from("8B", self.data, self.pos)
        self.pos += 8
        k, j, i, h, g, f, e, d = tail
        return f"{a:08x}-{b & 0xFFFF:04x}-{c & 0xFFFF:04x}-{d:02x}{e:02x}-{f:02x}{g:02x}{h:02x}{i:02x}{j:02x}{k:02x}"

    def _get_text(self, offset):
        """Read null-terminated string from text table."""
        start = self.text_offset + offset
        end = self.data.index(b"\x00", start)
        return self.data[start:end].decode("utf-8", errors="replace")

    def _get_blob(self, offset):
        """Read null-terminated string from blob table."""
        start = self.blob_offset + offset
        end = self.data.index(b"\x00", start)
        return self.data[start:end].decode("utf-8", errors="replace")

    def _get_name(self, name_offset):
        """Get name from blob (or text for legacy)."""
        if self.is_legacy:
            return self._get_text(name_offset)
        return self._get_blob(name_offset)

    # --- Header ---

    def _parse_header(self):
        self.pos = 0
        self._read("<HH")  # temp00
        self.file_version = self._read("<I")
        self.is_legacy = self.file_version < 6 or len(self.data) < 0x0e2e00

        if not self.is_legacy:
            self._read("<4H")  # skip 4 uint16

        field_names = [
            "struct_def_count", "prop_def_count", "enum_def_count",
            "data_mapping_count", "record_def_count",
            "bool_count", "int8_count", "int16_count", "int32_count", "int64_count",
            "uint8_count", "uint16_count", "uint32_count", "uint64_count",
            "single_count", "double_count", "guid_count",
            "string_count", "locale_count", "enum_val_count",
            "strong_count", "weak_count", "ref_count", "enum_opt_count",
        ]
        for name in field_names:
            setattr(self, name, self._read("<I"))

        self.text_length = self._read("<I")
        self.blob_length = 0 if self.is_legacy else self._read("<I")

        self.header_end = self.pos

    # --- Definitions ---

    def _parse_definitions(self):
        self.pos = self.header_end

        # Struct definitions (16 bytes each)
        self.struct_defs = []
        for _ in range(self.struct_def_count):
            name_off, parent_idx, prop_count, first_prop, record_size = \
                struct.unpack_from("<IIHHI", self.data, self.pos)
            self.pos += 16
            self.struct_defs.append({
                "name_offset": name_off,
                "parent_index": parent_idx,
                "prop_count": prop_count,
                "first_prop": first_prop,
                "record_size": record_size,
            })

        # Property definitions (12 bytes each)
        self.prop_defs = []
        for _ in range(self.prop_def_count):
            name_off, index, data_type, conv_type, variant = \
                struct.unpack_from("<IHHHH", self.data, self.pos)
            self.pos += 12
            self.prop_defs.append({
                "name_offset": name_off,
                "index": index,
                "data_type": data_type,
                "conv_type": conv_type & 0xFF,
                "variant": variant,
            })

        # Enum definitions (8 bytes each)
        self.enum_defs = []
        for _ in range(self.enum_def_count):
            name_off, val_count, first_val = \
                struct.unpack_from("<IHH", self.data, self.pos)
            self.pos += 8
            self.enum_defs.append({
                "name_offset": name_off,
                "value_count": val_count,
                "first_value": first_val,
            })

        # Data mappings
        self.data_mappings = []
        if self.is_legacy:
            for _ in range(self.data_mapping_count):
                sc, si = struct.unpack_from("<HH", self.data, self.pos)
                self.pos += 4
                self.data_mappings.append({"struct_count": sc, "struct_index": si})
        else:
            for _ in range(self.data_mapping_count):
                sc, si = struct.unpack_from("<II", self.data, self.pos)
                self.pos += 8
                self.data_mappings.append({"struct_count": sc, "struct_index": si})

        # Record definitions (32 bytes for modern)
        self.record_defs = []
        for _ in range(self.record_def_count):
            name_off = self._read("<I")
            if not self.is_legacy:
                filename_off = self._read("<I")
            else:
                filename_off = 0
            struct_idx = self._read("<I")
            guid = self._read_guid()
            variant_idx, other_idx = struct.unpack_from("<HH", self.data, self.pos)
            self.pos += 4
            self.record_defs.append({
                "name_offset": name_off,
                "filename_offset": filename_off,
                "struct_index": struct_idx,
                "guid": guid,
                "variant_index": variant_idx,
                "other_index": other_idx,
            })

    # --- Value arrays ---

    def _parse_value_arrays(self):
        # Read value arrays in the correct order
        # Order: Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64,
        #        Boolean, Single, Double, Guid, String, Locale, Enum,
        #        Strong, Weak, Reference, EnumOption

        def read_array(count, fmt, size):
            arr = []
            for _ in range(count):
                arr.append(struct.unpack_from(fmt, self.data, self.pos))
                self.pos += size
            return arr

        self.int8_values = read_array(self.int8_count, "<b", 1)
        self.int16_values = read_array(self.int16_count, "<h", 2)
        self.int32_values = read_array(self.int32_count, "<i", 4)
        self.int64_values = read_array(self.int64_count, "<q", 8)
        self.uint8_values = read_array(self.uint8_count, "<B", 1)
        self.uint16_values = read_array(self.uint16_count, "<H", 2)
        self.uint32_values = read_array(self.uint32_count, "<I", 4)
        self.uint64_values = read_array(self.uint64_count, "<Q", 8)
        self.bool_values = read_array(self.bool_count, "<B", 1)
        self.single_values = read_array(self.single_count, "<f", 4)
        self.double_values = read_array(self.double_count, "<d", 8)

        # Guid values (16 bytes each, special order)
        self.guid_values = []
        for _ in range(self.guid_count):
            self.guid_values.append(self._read_guid())

        # String/Locale/Enum values (4 bytes = offset into text)
        self.string_values = read_array(self.string_count, "<I", 4)
        self.locale_values = read_array(self.locale_count, "<I", 4)
        self.enum_values = read_array(self.enum_val_count, "<I", 4)

        # Strong pointers (8 bytes: uint32 struct_index + uint16 variant + uint16 pad)
        self.strong_values = read_array(self.strong_count, "<IHH", 8)
        self.weak_values = read_array(self.weak_count, "<IHH", 8)

        # References (20 bytes: uint32 + guid)
        self.ref_values = []
        for _ in range(self.ref_count):
            item1 = self._read("<I")
            guid = self._read_guid()
            self.ref_values.append((item1, guid))

        # Enum options
        self.enum_options = read_array(self.enum_opt_count, "<I", 4)

    # --- String tables ---

    def _parse_string_tables(self):
        self.text_offset = self.pos
        self.pos += self.text_length
        self.blob_offset = self.pos
        self.pos += self.blob_length
        self.data_offset = self.pos  # Start of struct instance data

    # --- Data offset map ---

    def _build_data_offset_map(self):
        self.struct_data_offsets = {}
        offset = 0
        for i in range(self.data_mapping_count):
            dm = self.data_mappings[i]
            sd = self.struct_defs[i]  # parallel arrays
            self.struct_data_offsets[dm["struct_index"]] = offset
            offset += dm["struct_count"] * sd["record_size"]

    def _build_record_index(self):
        """Build lookup tables for records."""
        self.records_by_struct = defaultdict(list)
        self.guid_to_record = {}
        for i, rec in enumerate(self.record_defs):
            self.records_by_struct[rec["struct_index"]].append(i)
            if rec["guid"] != "00000000-0000-0000-0000-000000000000":
                self.guid_to_record[rec["guid"]] = i

    # --- Struct/property name resolution ---

    def struct_name(self, idx):
        if idx >= len(self.struct_defs) or idx == 0xFFFFFFFF:
            return "<none>"
        return self._get_name(self.struct_defs[idx]["name_offset"])

    def prop_name(self, idx):
        return self._get_name(self.prop_defs[idx]["name_offset"])

    def enum_name(self, idx):
        return self._get_name(self.enum_defs[idx]["name_offset"])

    def record_name(self, idx):
        return self._get_text(self.record_defs[idx]["name_offset"])

    def record_filename(self, idx):
        off = self.record_defs[idx]["filename_offset"]
        if off == 0:
            return ""
        return self._get_text(off)

    # --- Get all properties for a struct (with inheritance) ---

    def struct_properties(self, struct_idx):
        """Return all properties for a struct, including inherited ones."""
        props = []
        hierarchy = []
        idx = struct_idx
        while idx != 0xFFFFFFFF and idx < len(self.struct_defs):
            hierarchy.append(idx)
            idx = self.struct_defs[idx]["parent_index"]
        # Parents first
        for si in reversed(hierarchy):
            sd = self.struct_defs[si]
            for pi in range(sd["first_prop"], sd["first_prop"] + sd["prop_count"]):
                props.append(pi)
        return props

    # --- Read a struct instance from the data blob ---

    def read_instance(self, struct_idx, variant_idx, depth=0, max_depth=8):
        """Read a struct instance, returning a dict of property values."""
        if depth > max_depth:
            return {"__type": self.struct_name(struct_idx), "__truncated": True}

        if struct_idx >= len(self.struct_defs):
            return {"__type": f"<invalid_struct_{struct_idx}>"}

        sd = self.struct_defs[struct_idx]
        base_offset = self.data_offset + self.struct_data_offsets.get(struct_idx, 0)
        instance_offset = base_offset + sd["record_size"] * variant_idx

        result = {"__type": self.struct_name(struct_idx)}
        pos = instance_offset
        props = self.struct_properties(struct_idx)

        for pi in props:
            pd = self.prop_defs[pi]
            pname = self.prop_name(pi)
            dt = pd["data_type"]
            ct = pd["conv_type"]

            if ct == CT_ATTRIBUTE:
                val, pos = self._read_value_inline(dt, pos, pd, depth, max_depth)
                result[pname] = val
            else:
                # Array: read count + first_index
                array_count, first_index = struct.unpack_from("<II", self.data, pos)
                pos += 8
                if ct == CT_CLASS_ARRAY or (ct in (CT_COMPLEX_ARRAY, CT_SIMPLE_ARRAY) and dt == DT_CLASS):
                    items = []
                    for ai in range(array_count):
                        items.append(self.read_instance(pd["index"], first_index + ai, depth + 1, max_depth))
                    result[pname] = items
                else:
                    result[pname] = self._read_array_values(dt, first_index, array_count)

        return result

    def _read_value_inline(self, dt, pos, pd, depth, max_depth):
        """Read a single value inline from the data blob."""
        if dt == DT_BOOLEAN:
            v = struct.unpack_from("<B", self.data, pos)[0]
            return bool(v), pos + 1
        elif dt == DT_INT8:
            v = struct.unpack_from("<b", self.data, pos)[0]
            return v, pos + 1
        elif dt == DT_INT16:
            v = struct.unpack_from("<h", self.data, pos)[0]
            return v, pos + 2
        elif dt == DT_INT32:
            v = struct.unpack_from("<i", self.data, pos)[0]
            return v, pos + 4
        elif dt == DT_INT64:
            v = struct.unpack_from("<q", self.data, pos)[0]
            return v, pos + 8
        elif dt == DT_UINT8:
            v = struct.unpack_from("<B", self.data, pos)[0]
            return v, pos + 1
        elif dt == DT_UINT16:
            v = struct.unpack_from("<H", self.data, pos)[0]
            return v, pos + 2
        elif dt == DT_UINT32:
            v = struct.unpack_from("<I", self.data, pos)[0]
            return v, pos + 4
        elif dt == DT_UINT64:
            v = struct.unpack_from("<Q", self.data, pos)[0]
            return v, pos + 8
        elif dt == DT_SINGLE:
            v = struct.unpack_from("<f", self.data, pos)[0]
            return round(v, 6), pos + 4
        elif dt == DT_DOUBLE:
            v = struct.unpack_from("<d", self.data, pos)[0]
            return round(v, 10), pos + 8
        elif dt == DT_STRING:
            off = struct.unpack_from("<I", self.data, pos)[0]
            try:
                v = self._get_text(off)
            except (ValueError, IndexError):
                v = f"<string@{off}>"
            return v, pos + 4
        elif dt == DT_LOCALE:
            off = struct.unpack_from("<I", self.data, pos)[0]
            try:
                v = self._get_text(off)
            except (ValueError, IndexError):
                v = f"<locale@{off}>"
            return v, pos + 4
        elif dt == DT_ENUM:
            off = struct.unpack_from("<I", self.data, pos)[0]
            try:
                v = self._get_text(off)
            except (ValueError, IndexError):
                v = f"<enum@{off}>"
            return v, pos + 4
        elif dt == DT_GUID:
            old_pos = self.pos
            self.pos = pos
            v = self._read_guid()
            pos = self.pos
            self.pos = old_pos
            return v, pos
        elif dt == DT_STRONG_PTR:
            si, vi, _ = struct.unpack_from("<IHH", self.data, pos)
            if si == 0xFFFFFFFF or si >= len(self.struct_defs):
                return None, pos + 8
            if depth < max_depth:
                return self.read_instance(si, vi, depth + 1, max_depth), pos + 8
            return {"__ptr": f"{self.struct_name(si)}[{vi}]"}, pos + 8
        elif dt == DT_WEAK_PTR:
            si, vi, _ = struct.unpack_from("<IHH", self.data, pos)
            if si == 0xFFFFFFFF or si >= len(self.struct_defs):
                return None, pos + 8
            return {"__weakref": f"{self.struct_name(si)}[{vi}]"}, pos + 8
        elif dt == DT_REFERENCE:
            item1 = struct.unpack_from("<I", self.data, pos)[0]
            old_pos = self.pos
            self.pos = pos + 4
            guid = self._read_guid()
            pos = self.pos
            self.pos = old_pos
            if guid == "00000000-0000-0000-0000-000000000000":
                return None, pos
            return {"__ref": guid}, pos
        elif dt == DT_CLASS:
            return self.read_instance(pd["index"], 0, depth + 1, max_depth), pos
        else:
            return f"<unknown_dt_{dt:#x}>", pos + 4

    def _read_array_values(self, dt, first_index, count):
        """Read values from the typed value arrays."""
        values = []
        for i in range(count):
            idx = first_index + i
            if dt == DT_BOOLEAN and idx < len(self.bool_values):
                values.append(bool(self.bool_values[idx][0]))
            elif dt == DT_INT8 and idx < len(self.int8_values):
                values.append(self.int8_values[idx][0])
            elif dt == DT_INT16 and idx < len(self.int16_values):
                values.append(self.int16_values[idx][0])
            elif dt == DT_INT32 and idx < len(self.int32_values):
                values.append(self.int32_values[idx][0])
            elif dt == DT_INT64 and idx < len(self.int64_values):
                values.append(self.int64_values[idx][0])
            elif dt == DT_UINT8 and idx < len(self.uint8_values):
                values.append(self.uint8_values[idx][0])
            elif dt == DT_UINT16 and idx < len(self.uint16_values):
                values.append(self.uint16_values[idx][0])
            elif dt == DT_UINT32 and idx < len(self.uint32_values):
                values.append(self.uint32_values[idx][0])
            elif dt == DT_UINT64 and idx < len(self.uint64_values):
                values.append(self.uint64_values[idx][0])
            elif dt == DT_SINGLE and idx < len(self.single_values):
                values.append(round(self.single_values[idx][0], 6))
            elif dt == DT_DOUBLE and idx < len(self.double_values):
                values.append(round(self.double_values[idx][0], 10))
            elif dt == DT_STRING and idx < len(self.string_values):
                try:
                    values.append(self._get_text(self.string_values[idx][0]))
                except (ValueError, IndexError):
                    values.append(f"<string@{idx}>")
            elif dt == DT_LOCALE and idx < len(self.locale_values):
                try:
                    values.append(self._get_text(self.locale_values[idx][0]))
                except (ValueError, IndexError):
                    values.append(f"<locale@{idx}>")
            elif dt == DT_ENUM and idx < len(self.enum_values):
                try:
                    values.append(self._get_text(self.enum_values[idx][0]))
                except (ValueError, IndexError):
                    values.append(f"<enum@{idx}>")
            elif dt == DT_STRONG_PTR and idx < len(self.strong_values):
                si, vi, _ = self.strong_values[idx]
                if si == 0xFFFFFFFF:
                    values.append(None)
                else:
                    values.append({"__ptr": f"{self.struct_name(si)}[{vi}]"})
            elif dt == DT_WEAK_PTR and idx < len(self.weak_values):
                si, vi, _ = self.weak_values[idx]
                if si == 0xFFFFFFFF:
                    values.append(None)
                else:
                    values.append({"__weakref": f"{self.struct_name(si)}[{vi}]"})
            elif dt == DT_REFERENCE and idx < len(self.ref_values):
                item1, guid = self.ref_values[idx]
                if guid == "00000000-0000-0000-0000-000000000000":
                    values.append(None)
                else:
                    values.append({"__ref": guid})
            elif dt == DT_GUID and idx < len(self.guid_values):
                values.append(self.guid_values[idx])
            else:
                values.append(f"<array_{DT_NAMES.get(dt, hex(dt))}@{idx}>")
        return values

    # --- Read a record ---

    def read_record(self, record_idx, max_depth=8):
        """Read a complete record by index."""
        rec = self.record_defs[record_idx]
        data = self.read_instance(rec["struct_index"], rec["variant_index"], max_depth=max_depth)
        data["__record_name"] = self.record_name(record_idx)
        data["__record_filename"] = self.record_filename(record_idx)
        data["__guid"] = rec["guid"]
        return data

    # --- High-level queries ---

    def find_structs(self, pattern):
        """Find struct indices whose name matches a pattern (case-insensitive)."""
        pattern = pattern.lower()
        results = []
        for i, sd in enumerate(self.struct_defs):
            name = self._get_name(sd["name_offset"]).lower()
            if pattern in name:
                results.append(i)
        return results

    def find_records(self, pattern):
        """Find record indices whose name or filename matches a pattern."""
        pattern = pattern.lower()
        results = []
        for i, rec in enumerate(self.record_defs):
            name = self.record_name(i).lower()
            fname = self.record_filename(i).lower()
            if pattern in name or pattern in fname:
                results.append(i)
        return results

    def print_struct_info(self, struct_idx):
        """Print struct definition with all properties."""
        sd = self.struct_defs[struct_idx]
        name = self.struct_name(struct_idx)
        parent = self.struct_name(sd["parent_index"])
        dm = self.data_mappings[struct_idx] if struct_idx < len(self.data_mappings) else None
        instance_count = dm["struct_count"] if dm else "?"

        print(f"\n{'=' * 60}")
        print(f"Struct: {name}")
        print(f"  Parent: {parent}")
        print(f"  RecordSize: {sd['record_size']} bytes")
        print(f"  Instances: {instance_count}")
        print(f"  Properties ({sd['prop_count']}):")

        all_props = self.struct_properties(struct_idx)
        for pi in all_props:
            pd = self.prop_defs[pi]
            pname = self.prop_name(pi)
            dtype = DT_NAMES.get(pd["data_type"], f"0x{pd['data_type']:04x}")
            conv = pd["conv_type"]
            conv_str = ""
            if conv == CT_COMPLEX_ARRAY:
                conv_str = " [ComplexArray]"
            elif conv == CT_SIMPLE_ARRAY:
                conv_str = " [SimpleArray]"
            elif conv == CT_CLASS_ARRAY:
                conv_str = " [ClassArray]"
            extra = ""
            if pd["data_type"] in (DT_CLASS, DT_STRONG_PTR, DT_WEAK_PTR):
                extra = f" -> {self.struct_name(pd['index'])}"
            elif pd["data_type"] == DT_ENUM:
                if pd["index"] < len(self.enum_defs):
                    extra = f" ({self.enum_name(pd['index'])})"
            print(f"    {pname:40s} {dtype:20s}{conv_str}{extra}")


def main():
    parser = argparse.ArgumentParser(description="Parser de DataForge (Game2.dcb)")
    parser.add_argument("dcb", nargs="?", default="Game2.dcb", help="Ruta al Game2.dcb")
    parser.add_argument("--list-structs", action="store_true", help="Listar todos los structs")
    parser.add_argument("--search", help="Buscar structs/records con este texto")
    parser.add_argument("--struct", help="Ver propiedades de un struct")
    parser.add_argument("--records", help="Listar records de un tipo de struct")
    parser.add_argument("--record", help="Volcar un record por nombre")
    parser.add_argument("--dump", help="Exportar records de un tipo a JSON")
    parser.add_argument("--max-depth", type=int, default=4, help="Profundidad max al resolver punteros")
    parser.add_argument("-o", "--output", help="Archivo de salida para --dump")
    parser.add_argument("--max", type=int, default=50, help="Max resultados a mostrar")
    args = parser.parse_args()

    if not os.path.exists(args.dcb):
        print(f"Error: no se encuentra {args.dcb}")
        print("Extrae primero: python explore_p4k.py --extract \"Data\\Game2.dcb\" -o Game2.dcb")
        sys.exit(1)

    print("Cargando DataForge...", file=sys.stderr)
    df = DataForge(args.dcb)
    print(f"  Structs: {df.struct_def_count:,}", file=sys.stderr)
    print(f"  Records: {df.record_def_count:,}", file=sys.stderr)
    print(f"  Properties: {df.prop_def_count:,}", file=sys.stderr)
    print(f"  Enums: {df.enum_def_count:,}", file=sys.stderr)
    print(f"  Data offset: {df.data_offset:#x}", file=sys.stderr)
    print(f"  Loaded.", file=sys.stderr)

    if args.list_structs:
        print(f"\n{'Struct':<50} {'Props':>6} {'Size':>6} {'Instances':>10}")
        print("-" * 76)
        for i in range(df.struct_def_count):
            sd = df.struct_defs[i]
            name = df.struct_name(i)
            dm = df.data_mappings[i] if i < len(df.data_mappings) else None
            inst = dm["struct_count"] if dm else 0
            if inst > 0 or sd["prop_count"] > 0:
                print(f"{name:<50} {sd['prop_count']:>6} {sd['record_size']:>6} {inst:>10,}")

    elif args.search:
        structs = df.find_structs(args.search)
        if structs:
            print(f"\n=== Structs con '{args.search}' ({len(structs)}) ===")
            for i in structs[:args.max]:
                sd = df.struct_defs[i]
                dm = df.data_mappings[i] if i < len(df.data_mappings) else None
                inst = dm["struct_count"] if dm else 0
                print(f"  [{i:>5}] {df.struct_name(i):<50} ({inst:,} instances, {sd['record_size']}B)")

        records = df.find_records(args.search)
        if records:
            print(f"\n=== Records con '{args.search}' ({len(records)}) ===")
            for i in records[:args.max]:
                rec = df.record_defs[i]
                name = df.record_name(i)
                sname = df.struct_name(rec["struct_index"])
                fname = df.record_filename(i)
                print(f"  [{i:>6}] {name:<40} type={sname:<30} {fname}")

        if not structs and not records:
            print(f"No se encontro nada con '{args.search}'")

    elif args.struct:
        matches = df.find_structs(args.struct)
        if not matches:
            print(f"Struct '{args.struct}' no encontrado")
        else:
            for i in matches[:5]:
                df.print_struct_info(i)

    elif args.records:
        matches = df.find_structs(args.records)
        if not matches:
            print(f"Struct '{args.records}' no encontrado")
        else:
            for si in matches[:3]:
                recs = df.records_by_struct.get(si, [])
                print(f"\n=== Records de {df.struct_name(si)} ({len(recs)}) ===")
                for ri in recs[:args.max]:
                    name = df.record_name(ri)
                    fname = df.record_filename(ri)
                    print(f"  [{ri:>6}] {name:<50} {fname}")

    elif args.record:
        matches = df.find_records(args.record)
        if not matches:
            print(f"Record '{args.record}' no encontrado")
        else:
            for ri in matches[:3]:
                data = df.read_record(ri, max_depth=args.max_depth)
                print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

    elif args.dump:
        matches = df.find_structs(args.dump)
        if not matches:
            print(f"Struct '{args.dump}' no encontrado")
            sys.exit(1)
        si = matches[0]
        recs = df.records_by_struct.get(si, [])
        print(f"Exportando {len(recs)} records de {df.struct_name(si)}...", file=sys.stderr)
        all_data = []
        for ri in recs:
            try:
                data = df.read_record(ri, max_depth=args.max_depth)
                all_data.append(data)
            except Exception as e:
                all_data.append({"__error": str(e), "__record_index": ri})
        output = json.dumps(all_data, indent=2, ensure_ascii=False, default=str)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Guardado: {args.output} ({len(all_data)} records)", file=sys.stderr)
        else:
            print(output)

    else:
        # Default: summary
        print(f"\nResumen del DataForge (v{df.file_version}):")
        print(f"  Structs:    {df.struct_def_count:>10,}")
        print(f"  Properties: {df.prop_def_count:>10,}")
        print(f"  Enums:      {df.enum_def_count:>10,}")
        print(f"  Records:    {df.record_def_count:>10,}")
        print(f"  Strings:    {df.string_count:>10,}")
        print(f"  Locales:    {df.locale_count:>10,}")
        print(f"  StrongPtrs: {df.strong_count:>10,}")
        print(f"  WeakPtrs:   {df.weak_count:>10,}")
        print(f"  References: {df.ref_count:>10,}")
        print(f"\nTop structs por numero de instances:")

        by_count = []
        for i in range(df.data_mapping_count):
            dm = df.data_mappings[i]
            if dm["struct_count"] > 0:
                by_count.append((dm["struct_count"], i, dm["struct_index"]))
        by_count.sort(reverse=True)
        for count, mi, si in by_count[:30]:
            print(f"  {count:>8,}  {df.struct_name(si)}")


if __name__ == "__main__":
    main()
