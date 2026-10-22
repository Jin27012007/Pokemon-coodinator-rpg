#!/usr/bin/env python3
"""Conservative, zero-dependency event script reference audit.

Run from the pokeemerald-expansion repository root. Reports candidates for
manual review only; never auto-edits event scripts or treats heuristics as proof.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MAPS = DATA / "maps"
COMMON = DATA / "event_scripts.s"
FLAGS = ROOT / "include/constants/flags.h"
VARS = ROOT / "include/constants/vars.h"
MAP_SCRIPT_CONSTANTS = ROOT / "include/constants/map_scripts.h"

LABEL = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*::?\s*(?:@.*)?$", re.M)
# Script commands whose arguments contain one or more label references.
FLOW = re.compile(
    r"^\s*(goto|call|goto_if_[A-Za-z0-9_]+|call_if_[A-Za-z0-9_]+|"
    r"map_script|case)\s+([^\n@]+)", re.M
)
FLAG_NAME = re.compile(r"\b(FLAG_[A-Z0-9_]+)\b")
VAR_NAME = re.compile(r"\b(VAR_[A-Z0-9_]+)\b")
OBJECT_NAME = re.compile(r"\b(LOCALID_[A-Z0-9_]+)\b")
MOVEMENT_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*Movement[A-Za-z0-9_]*)\s*::?\s*$", re.M)
IGNORED_TARGETS = {"TRUE", "FALSE", "YES", "NO", "MULTI_B_PRESSED"}

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def names_from_header(path: Path, prefix: str) -> set[str]:
    text = read(path)
    return set(re.findall(r"^\s*#define\s+(" + re.escape(prefix) + r"[A-Z0-9_]+)\b", text, re.M))

def main() -> int:
    if not MAPS.is_dir():
        print(f"ERROR: map directory missing: {MAPS}")
        return 2
    scripts = sorted(MAPS.glob("*/scripts.inc"))
    map_jsons = sorted(MAPS.glob("*/map.json"))
    if not scripts:
        print("ERROR: no data/maps/*/scripts.inc found")
        return 2

    script_labels: dict[str, list[str]] = defaultdict(list)
    all_texts: dict[Path, str] = {}
    for path in scripts:
        txt = read(path)
        all_texts[path] = txt
        for label in LABEL.findall(txt):
            script_labels[label].append(str(path.relative_to(ROOT)))

    common_text = read(COMMON)
    common_labels = set(LABEL.findall(common_text))
    all_labels = set(script_labels) | common_labels
    all_text = "\n".join(all_texts.values()) + "\n" + common_text

    duplicate_labels = {name: paths for name, paths in script_labels.items() if len(paths) > 1}
    unresolved = []
    for path, txt in all_texts.items():
        rel = str(path.relative_to(ROOT))
        for m in FLOW.finditer(txt):
            op, args = m.group(1), m.group(2)
            # Conservatively examine last comma-delimited argument for flow targets.
            target = args.strip().split(",")[-1].strip()
            target = target.split()[0] if target else ""
            if target and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target):
                if target not in all_labels and target not in IGNORED_TARGETS:
                    unresolved.append((rel, txt[:m.start()].count("\n") + 1, op, target))

    # Use sets of definitions as a coarse cross-reference inventory. Macro and
    # generated references are intentionally included in the global text to
    # reduce false positives; counts remain candidates, not verdicts.
    flags_defined = names_from_header(FLAGS, "FLAG_")
    vars_defined = names_from_header(VARS, "VAR_")
    flags_used = set(FLAG_NAME.findall(all_text))
    vars_used = set(VAR_NAME.findall(all_text))
    unknown_flags = sorted(flags_used - flags_defined)
    unknown_vars = sorted(vars_used - vars_defined)

    # Duplicate JSON IDs and invalid references between map JSON objects/scripts.
    map_ids = Counter()
    map_names = set()
    json_script_refs = []
    json_object_flags = []
    for path in map_jsons:
        rel = str(path.relative_to(ROOT))
        try:
            obj = json.loads(read(path))
        except json.JSONDecodeError as exc:
            json_script_refs.append((rel, 0, "INVALID_JSON", str(exc)))
            continue
        map_ids[obj.get("id", "")] += 1
        map_names.add(obj.get("name", ""))
        for event in obj.get("object_events", []):
            script = event.get("script")
            if isinstance(script, str) and script not in {"0x0", "0"} and script not in all_labels:
                json_script_refs.append((rel, 0, "OBJECT_SCRIPT", script))
            flag = event.get("flag")
            if isinstance(flag, str) and flag not in {"0", ""}:
                json_object_flags.append((rel, flag))
    duplicate_map_ids = sorted(k for k, v in map_ids.items() if k and v > 1)

    print("=== Event-script audit (heuristic; manual confirmation required) ===")
    print(f"Map script files: {len(scripts)}")
    print(f"Map JSON files: {len(map_jsons)}")
    print(f"Map-local labels indexed: {len(script_labels)}")
    print(f"Shared event-script labels: {len(common_labels)}")
    print(f"Duplicate map-local labels: {len(duplicate_labels)}")
    print(f"Possible unresolved flow references: {len(unresolved)}")
    print(f"Flag symbols used / not found in selected header: {len(flags_used)} / {len(unknown_flags)}")
    print(f"Var symbols used / not found in selected header: {len(vars_used)} / {len(unknown_vars)}")
    print(f"JSON object references requiring review: {len(json_script_refs)}")
    print(f"Duplicate map IDs: {len(duplicate_map_ids)}")

    for name, paths in sorted(duplicate_labels.items()):
        print("DUPLICATE_LABEL:", name, "=>", ", ".join(paths))
    for path, line, op, target in unresolved[:250]:
        print(f"UNRESOLVED_CANDIDATE: {path}:{line}: {op} -> {target}")
    for name in unknown_flags[:200]:
        print("FLAG_NOT_IN_SELECTED_HEADER:", name)
    for name in unknown_vars[:200]:
        print("VAR_NOT_IN_SELECTED_HEADER:", name)
    for path, _, kind, ref in json_script_refs[:200]:
        print(f"JSON_REFERENCE_REVIEW: {path}: {kind} -> {ref}")
    for map_id in duplicate_map_ids:
        print("DUPLICATE_MAP_ID:", map_id)
    print("NOTE: missing/unused candidates may be valid through generated constants, macros, C code, or cross-file includes. Review before acting; do not auto-delete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
