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
COMMON_DIR = ROOT / "data/scripts"
MACROS = ROOT / "asm/macros/event.inc"
FLAGS = ROOT / "include/constants/flags.h"
FLAGS_FRLG = ROOT / "include/constants/flags_frlg.h"
VARS = ROOT / "include/constants/vars.h"
VARS_FRLG = ROOT / "include/constants/vars_frlg.h"

LABEL = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*::?\s*(?:@.*)?$", re.M)
FLOW = re.compile(r"^\s*(goto|call|goto_if_[A-Za-z0-9_]+|call_if_[A-Za-z0-9_]+|map_script)\s+([^\n@]+)", re.M)
FLAG_NAME = re.compile(r"\b(FLAG_[A-Z0-9_]+)\b")
VAR_NAME = re.compile(r"\b(VAR_[A-Z0-9_]+)\b")
IGNORED = {"TRUE", "FALSE", "YES", "NO", "MULTI_B_PRESSED", "NULL", "0", "0x0"}
# These are command macros, not branch-to-label commands. Their arguments are
# trainer IDs or other values, not script-label destinations.
NON_LABEL_FLOW_MACROS = {
    "call_if_defeated", "call_if_not_defeated",
    "goto_if_defeated", "goto_if_not_defeated",
}

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def defs(path: Path, prefix: str) -> set[str]:
    return set(re.findall(r"^\s*#define\s+(" + re.escape(prefix) + r"[A-Z0-9_]+)\b", read(path), re.M))

def strip_asm_comments(text: str) -> str:
    """Remove @ comments without stripping @ characters inside quoted strings."""
    out = []
    for line in text.splitlines():
        quote = None
        escaped = False
        cut = len(line)
        for i, ch in enumerate(line):
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if quote:
                if ch == quote:
                    quote = None
                continue
            if ch in {"'", '"'}:
                quote = ch
            elif ch == "@":
                cut = i
                break
        out.append(line[:cut])
    return "\n".join(out)

def main() -> int:
    if not MAPS.is_dir():
        print(f"ERROR: map directory missing: {MAPS}")
        return 2
    files = sorted(MAPS.glob("*/scripts.inc"))
    maps = sorted(MAPS.glob("*/map.json"))
    shared_files = sorted(COMMON_DIR.rglob("*.inc")) if COMMON_DIR.is_dir() else []
    if not files:
        print(f"ERROR: no map scripts found under {MAPS}")
        return 2

    texts = {p: read(p) for p in files}
    shared_texts = {p: read(p) for p in shared_files}
    labels: dict[str, list[str]] = defaultdict(list)
    for p, txt in texts.items():
        for label in LABEL.findall(strip_asm_comments(txt)):
            labels[label].append(str(p.relative_to(ROOT)))
    for p, txt in shared_texts.items():
        for label in LABEL.findall(strip_asm_comments(txt)):
            labels[label].append(str(p.relative_to(ROOT)))

    common = read(COMMON)
    common_clean = strip_asm_comments(common)
    common_labels = set(LABEL.findall(common_clean))
    all_labels = set(labels) | common_labels
    clean_texts = [strip_asm_comments(x) for x in texts.values()]
    clean_shared = [strip_asm_comments(x) for x in shared_texts.values()]
    all_text = "\n".join(clean_texts) + "\n" + "\n".join(clean_shared) + "\n" + common_clean

    # Duplicates in mutually exclusive assembler conditionals can be legitimate.
    # Categorize same-file duplicates separately for human inspection.
    duplicates = {k:v for k,v in labels.items() if len(v) > 1}
    cross_file_duplicates = {k:v for k,v in duplicates.items() if len(set(v)) > 1}
    same_file_duplicates = {k:v for k,v in duplicates.items() if len(set(v)) == 1}
    common_counts = Counter(LABEL.findall(common_clean))
    common_duplicates = sorted(k for k,v in common_counts.items() if v > 1)

    unresolved = []
    for p, raw_txt in list(texts.items()) + list(shared_texts.items()):
        txt = strip_asm_comments(raw_txt)
        rel = str(p.relative_to(ROOT))
        for m in FLOW.finditer(txt):
            op, args = m.group(1), m.group(2).strip()
            if op in NON_LABEL_FLOW_MACROS:
                continue
            target = args.split(",")[-1].strip().split()[0] if args else ""
            if target and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target) and target not in all_labels and target not in IGNORED:
                unresolved.append((rel, txt[:m.start()].count("\n")+1, op, target))

    # Flags/vars can be conditional on Emerald vs FRLG; take both headers.
    flag_defs = defs(FLAGS, "FLAG_") | defs(FLAGS_FRLG, "FLAG_")
    var_defs = defs(VARS, "VAR_") | defs(VARS_FRLG, "VAR_")
    json_texts = []
    json_errors, object_script_review = [], []
    map_ids = Counter()
    for p in maps:
        rel = str(p.relative_to(ROOT))
        raw = read(p)
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            json_errors.append((rel, str(exc)))
            continue
        json_texts.append(raw)
        map_ids[obj.get("id", "")] += 1
        for event in obj.get("object_events", []):
            script = event.get("script")
            if isinstance(script, str) and script not in {"0", "0x0", "NULL", "null", ""} and script not in all_labels:
                object_script_review.append((rel, script))
    dup_ids = sorted(k for k,v in map_ids.items() if k and v > 1)

    # Exclude comments from assembly/script sources; retain parsed JSON fields.
    symbol_text = all_text + "\n" + "\n".join(json_texts)
    flags_used = set(FLAG_NAME.findall(symbol_text))
    vars_used = set(VAR_NAME.findall(symbol_text))
    unknown_flags = sorted(flags_used - flag_defs)
    unknown_vars = sorted(vars_used - var_defs)

    print("Event-script static scan (heuristics; manual confirmation required)")
    print(f"scripts.inc files: {len(files)}")
    print(f"map.json files: {len(maps)}")
    print(f"shared scripts files: {len(shared_files)}")
    print(f"map/shared labels indexed: {len(labels)}")
    print(f"labels in data/event_scripts.s itself: {len(common_labels)}")
    print(f"duplicate map/shared labels: {len(duplicates)}")
    print(f"  cross-file duplicate candidates: {len(cross_file_duplicates)}")
    print(f"  same-file conditional duplicate candidates: {len(same_file_duplicates)}")
    print(f"duplicate labels in data/event_scripts.s: {len(common_duplicates)}")
    print(f"possible unresolved flow references: {len(unresolved)}")
    print(f"flag symbols used / not found in selected headers: {len(flags_used)} / {len(unknown_flags)}")
    print(f"var symbols used / not found in selected headers: {len(vars_used)} / {len(unknown_vars)}")
    print(f"invalid JSON files: {len(json_errors)}")
    print(f"object script references needing review: {len(object_script_review)}")
    print(f"duplicate map IDs: {len(dup_ids)}")

    for name, locations in sorted(cross_file_duplicates.items()):
        print("CROSS_FILE_DUPLICATE_LABEL", name, "=>", ", ".join(locations))
    for name, locations in sorted(same_file_duplicates.items()):
        print("SAME_FILE_DUPLICATE_REVIEW", name, "=>", ", ".join(locations), "(may be mutually exclusive .if branches)")
    for name in common_duplicates:
        print("DUPLICATE_COMMON_AGGREGATOR_LABEL", name)
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
    print("Potential false positives remain for preprocessor branches, generated constants, macros, native-C references, and complex switch syntax. Review every report; do not auto-delete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
