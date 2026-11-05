#!/usr/bin/env python3
"""
Estadísticas del estado de lanzamientos (state/releases.json).

Uso:
    python tools/state_stats.py
    python tools/state_stats.py --compact   # reescribe el JSON sin indentación
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "state" / "releases.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stats de state/releases.json")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Reescribe el archivo en JSON compacto (menos espacio en disco)",
    )
    args = parser.parse_args()

    if not STATE_FILE.exists():
        print(f"No existe {STATE_FILE}")
        return 1

    raw = STATE_FILE.read_text(encoding="utf-8")
    size_bytes = len(raw.encode("utf-8"))
    estado = json.loads(raw)

    version = estado.get("version")
    canciones = estado.get("canciones", [])
    if not isinstance(canciones, list):
        print("Formato inesperado: 'canciones' no es una lista")
        return 1

    prefixes = Counter()
    for clave in canciones:
        if not isinstance(clave, str):
            prefixes["(no-str)"] += 1
            continue
        if ":" in clave:
            prefixes[clave.split(":", 1)[0]] += 1
        else:
            prefixes["(sin-prefijo)"] += 1

    print("=" * 50)
    print("STATE / releases.json")
    print("=" * 50)
    print(f"Archivo:     {STATE_FILE}")
    print(f"Versión:     {version}")
    print(f"Claves:      {len(canciones):,}")
    print(f"Tamaño:      {size_bytes:,} bytes ({size_bytes / 1024:.1f} KB)")
    print()
    print("Prefijos de claves:")
    for pref, n in prefixes.most_common():
        print(f"  {pref:20} {n:,}")
    print()

    compact = json.dumps(
        {"version": version, "canciones": sorted(canciones)},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    compact_size = len(compact.encode("utf-8"))
    print(f"Tamaño compacto estimado: {compact_size:,} bytes ({compact_size / 1024:.1f} KB)")
    print(f"Ahorro potencial:         {size_bytes - compact_size:,} bytes")

    if args.compact:
        STATE_FILE.write_text(compact + "\n", encoding="utf-8")
        print()
        print(f"Reescrito en formato compacto -> {STATE_FILE}")

    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
