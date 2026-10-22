#!/usr/bin/env python3
"""Conservative event-script sanity checks for pokeemerald-expansion.

Run from the project root. Reports manual-review candidates only; it does not
edit or remove scripts and is not a complete parser of the event language.
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
FLAGS_FRLG = ROOT / "include/constants/flags_frlg.h"
VARS = ROOT / "include/constants/vars.h"
VARS_FRLG = ROOT / "include/constants/vars_frlg.h"

LABEL = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*::?\s*(?:@.*)?$", re.M)
# This deliberately conservative target parser handles simple label arguments;
# complex cases/switch expressions are left to the assembler and manual review.
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

    # Count duplicates among map-local labels and common labels separately.
    duplicates = {k:v for k,v in labels.items() if len(v) > 1}
    common_counts = Counter(LABEL.findall(common))
    common_duplicates = sorted(k for k,v in common_counts.items() if v > 1)

    unresolved = []
    for p, txt in texts.items():
        rel = str(p.relative_to(ROOT))
        for m in FLOW.finditer(txt):
            op, args = m.group(1), m.group(2).strip()
            target = args.split(",")[-1].strip().split()[0] if args else ""
            if target and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target) and target not in all_labels and target not in IGNORED:
                unresolved.append((rel, txt[:m.start()].count("\n")+1, op, target))

    # Flags/vars can be conditional on Emerald vs FRLG; check the union to avoid
    # falsely warning on symbols defined only for the alternate game build.
    flag_defs = defs(FLAGS, "FLAG_") | defs(FLAGS_FRLG, "FLAG_")
    var_defs = defs(VARS, "VAR_") | defs(VARS_FRLG, "VAR_")
    flags_used = set(FLAG_NAME.findall(all_text))
    vars_used = set(VAR_NAME.findall(all_text))
    unknown_flags = sorted(flags_used - flag_defs)
    unknown_vars = sorted(vars_used - var_defs)

    json_errors, object_script_review = [], []
    map_ids = Counter()
    for p in maps:
        rel = str(p.relative_to(ROOT))
        try:
            obj = json.loads(read(p))
        except json.JSONDecodeError as exc:
            json_errors.append((rel, str(exc)))
            continue
        map_id = obj.get("id", "")
        map_ids[map_id] += 1
        # Validate object script links; IDs like 0/0x0 denote no script.
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
    print(f"duplicate common labels: {len(common_duplicates)}")
    print(f"possible unresolved flow references: {len(unresolved)}")
    print(f"flag symbols used / not found in selected headers: {len(flags_used)} / {len(unknown_flags)}")
    print(f"var symbols used / not found in selected headers: {len(vars_used)} / {len(unknown_vars)}")
    print(f"invalid JSON files: {len(json_errors)}")
    print(f"object script references needing review: {len(object_script_review)}")
    print(f"duplicate map IDs: {len(dup_ids)}")

    for name, locations in sorted(duplicates.items()):
        print("DUPLICATE_MAP_LABEL", name, "=>", ", ".join(locations))
    for name in common_duplicates:
        print("DUPLICATE_COMMON_LABEL", name)
    for row in unresolved[:250]:
        print("UNRESOLVED_CANDIDATE", *row)
    for name in unknown_flags[:200]:
        print("FLAG_NOT_IN_SELECTED_HEADERS", name)
    for name in unknown_vars[:200]:
        print("VAR_NOT_IN_SELECTED_HEADERS", name)
    for row in json_errors[:100]:
        print("INVALID_JSON", *row)
    for row in object_script_review[:250]:
        print("OBJECT_SCRIPT_REVIEW", *row)
    for name in dup_ids:
        print("DUPLICATE_MAP_ID", name)
    print("Potential false positives include preprocessor branches, generated constants, cross-includes, macros, native-C references, and complex switch syntax. Review every report; do not auto-delete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
