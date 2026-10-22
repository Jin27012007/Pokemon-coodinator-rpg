#!/usr/bin/env python3
"""Conservative event-script sanity checks for pokeemerald-expansion.

Run from the project root. This reports manual-review candidates only; it is
not a complete parser and never edits or removes events automatically.
"""
from __future__ import annotations
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "data/maps"
COMMON = ROOT / "data/event_scripts.s"
FLAGS = ROOT / "include/constants/flags.h"
VARS = ROOT / "include/constants/vars.h"

LABEL = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*::?\s*(?:@.*)?$", re.M)
FLOW = re.compile(r"^\s*(goto|call|goto_if_[A-Za-z0-9_]+|call_if_[A-Za-z0-9_]+|map_script)\s+([^\n@]+)", re.M)
FLAG_NAME = re.compile(r"\b(FLAG_[A-Z0-9_]+)\b")
VAR_NAME = re.compile(r"\b(VAR_[A-Z0-9_]+)\b")
IGNORED = {"TRUE", "FALSE", "YES", "NO", "MULTI_B_PRESSED"}

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def defs(path: Path, prefix: str) -> set[str]:
    return set(re.findall(r"^\s*#define\s+(" + re.escape(prefix) + r"[A-Z0-9_]+)\b", read(path), re.M))

def main() -> int:
    if not MAPS.is_dir():
        print(f"ERROR: map directory missing: {MAPS}")
        return 2
    files = sorted(MAPS.glob("*/scripts.inc"))
    maps = sorted(MAPS.glob("*/map.json"))
    if not files:
        print("ERROR: no map scripts found")
        return 2
    texts = {p: read(p) for p in files}
    labels: dict[str, list[str]] = defaultdict(list)
    for p, txt in texts.items():
        for label in LABEL.findall(txt):
            labels[label].append(str(p.relative_to(ROOT)))
    common = read(COMMON)
    common_labels = set(LABEL.findall(common))
    all_labels = set(labels) | common_labels
    all_text = "\n".join(texts.values()) + "\n" + common

    duplicates = {k:v for k,v in labels.items() if len(v) > 1}
    missing = []
    for p, txt in texts.items():
        for m in FLOW.finditer(txt):
            op, args = m.group(1), m.group(2).strip()
            target = args.split(",")[-1].strip().split()[0] if args else ""
            if target and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target) and target not in all_labels and target not in IGNORED:
                missing.append((str(p.relative_to(ROOT)), txt[:m.start()].count("\n")+1, op, target))

    flag_defs, var_defs = defs(FLAGS, "FLAG_"), defs(VARS, "VAR_")
    unknown_flags = sorted(set(FLAG_NAME.findall(all_text)) - flag_defs)
    unknown_vars = sorted(set(VAR_NAME.findall(all_text)) - var_defs)
    json_errors, object_script_review = [], []
    map_ids = Counter()
    for p in maps:
        rel = str(p.relative_to(ROOT))
        try:
            obj = json.loads(read(p))
        except json.JSONDecodeError as exc:
            json_errors.append((rel, str(exc)))
            continue
        map_ids[obj.get("id", "")] += 1
        for event in obj.get("object_events", []):
            script = event.get("script")
            if isinstance(script, str) and script not in {"0", "0x0"} and script not in all_labels:
                object_script_review.append((rel, script))
    dup_ids = sorted(k for k,v in map_ids.items() if k and v > 1)

    print("Event-script static scan (heuristics; manual confirmation required)")
    print(f"scripts.inc files: {len(files)}")
    print(f"map.json files: {len(maps)}")
    print(f"map-local labels: {len(labels)}")
    print(f"common event labels: {len(common_labels)}")
    print(f"duplicate map-local labels: {len(duplicates)}")
    print(f"possible unresolved references: {len(missing)}")
    print(f"flag symbols outside selected header: {len(unknown_flags)}")
    print(f"var symbols outside selected header: {len(unknown_vars)}")
    print(f"invalid JSON files: {len(json_errors)}")
    print(f"object script references needing review: {len(object_script_review)}")
    print(f"duplicate map IDs: {len(dup_ids)}")
    for name, locations in sorted(duplicates.items()):
        print("DUPLICATE_LABEL", name, "=>", ", ".join(locations))
    for row in missing[:250]:
        print("UNRESOLVED_CANDIDATE", *row)
    for name in unknown_flags[:200]:
        print("FLAG_NOT_IN_SELECTED_HEADER", name)
    for name in unknown_vars[:200]:
        print("VAR_NOT_IN_SELECTED_HEADER", name)
    for row in json_errors[:100]:
        print("INVALID_JSON", *row)
    for row in object_script_review[:250]:
        print("OBJECT_SCRIPT_REVIEW", *row)
    for name in dup_ids:
        print("DUPLICATE_MAP_ID", name)
    print("Potential false positives include generated constants, cross-includes, macros, native-C references, and alternative game configurations. Review every report; do not auto-delete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
