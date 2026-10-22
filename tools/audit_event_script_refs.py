#!/usr/bin/env python3
"""Conservative event-script sanity checks for pokeemerald-expansion.

Run from the project root. Reports manual-review candidates only; it does not
edit or remove scripts and is not a complete parser of the event language.
"""
from __future__ import annotations
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "data/maps"
COMMON = ROOT / "data/event_scripts.s"
COMMON_DIR = ROOT / "data/scripts"
FLAGS = ROOT / "include/constants/flags.h"
FLAGS_FRLG = ROOT / "include/constants/flags_frlg.h"
VARS = ROOT / "include/constants/vars.h"
VARS_FRLG = ROOT / "include/constants/vars_frlg.h"
CONFIG_HEADERS = ROOT / "include/config"

LABEL = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*::?\s*(?:@.*)?$", re.M)
FLOW = re.compile(r"^\s*(goto|call|goto_if_[A-Za-z0-9_]+|call_if_[A-Za-z0-9_]+|map_script)\s+([^\n@]+)", re.M)
CASE_REF = re.compile(r"^\s*case\s+[^,\n]+,\s*([A-Za-z_][A-Za-z0-9_]*)", re.M)
MAP_HOOK = re.compile(r"^\s*map_script\s+(MAP_SCRIPT_[A-Z0-9_]+)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)", re.M)
FLAG_NAME = re.compile(r"\b(FLAG_[A-Z0-9_]+)\b")
VAR_NAME = re.compile(r"\b(VAR_[A-Z0-9_]+)\b")
IGNORED = {"TRUE", "FALSE", "YES", "NO", "MULTI_B_PRESSED", "NULL", "null", "0", "0x0"}
NON_LABEL_FLOW_MACROS = {
    "call_if_defeated", "call_if_not_defeated",
    "goto_if_defeated", "goto_if_not_defeated",
}
# These tags are executed immediately by the pinned engine. ON_FRAME_TABLE is
# intentionally excluded because it uses the global script context and yields.
SYNCHRONOUS_HOOKS = {
    "MAP_SCRIPT_ON_LOAD", "MAP_SCRIPT_ON_TRANSITION", "MAP_SCRIPT_ON_RESUME",
    "MAP_SCRIPT_ON_RETURN_TO_FIELD", "MAP_SCRIPT_ON_DIVE_WARP",
    "MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE",
}
BLOCKING_COMMANDS = {
    "waitmovement", "waitmovementat", "waitmovementall", "waitstate", "waitse",
    "waitfanfare", "waitmessage", "waitbuttonpress", "waitdooranim",
    "waitfieldeffect", "waitmoncry",
}
COMMAND_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\b([^\n@]*)", re.M)

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def defs(path: Path, prefix: str) -> set[str]:
    return set(re.findall(r"^\s*#define\s+(" + re.escape(prefix) + r"[A-Z0-9_]+)\b", read(path), re.M))

def strip_comments(text: str) -> str:
    """Strip C block and line comments plus assembler @ comments, respecting strings."""
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    out = []
    for line in text.splitlines():
        quote = None
        escaped = False
        cut = len(line)
        i = 0
        while i < len(line):
            ch = line[i]
            if escaped:
                escaped = False
                i += 1
                continue
            if ch == "\\":
                escaped = True
                i += 1
                continue
            if quote:
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in {"'", '"'}:
                quote = ch
                i += 1
                continue
            if ch == "@" or line.startswith("//", i):
                cut = i
                break
            i += 1
        out.append(line[:cut])
    return "\n".join(out)

def split_labels(path: Path, text: str) -> list[tuple[str, str, int]]:
    matches = list(LABEL.finditer(text))
    result = []
    rel = str(path.relative_to(ROOT))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end():end]
        result.append((match.group(1), body, text[:match.start()].count("\n") + 1))
    return result

def flow_targets(body: str, all_labels: set[str]) -> set[str]:
    targets = set()
    for match in FLOW.finditer(body):
        op, args = match.group(1), match.group(2).strip()
        if op == "map_script" or op in NON_LABEL_FLOW_MACROS:
            continue
        target = args.split(",")[-1].strip().split()[0] if args else ""
        if target in all_labels:
            targets.add(target)
    for match in CASE_REF.finditer(body):
        target = match.group(1)
        if target in all_labels:
            targets.add(target)
    return targets

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

    raw_texts = {p: read(p) for p in files}
    raw_shared = {p: read(p) for p in shared_files}
    clean_texts = {p: strip_comments(txt) for p, txt in raw_texts.items()}
    clean_shared = {p: strip_comments(txt) for p, txt in raw_shared.items()}

    label_locations: dict[str, list[str]] = defaultdict(list)
    label_bodies: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    map_hooks: list[tuple[str, str, str]] = []
    for p, txt in list(clean_texts.items()) + list(clean_shared.items()):
        rel = str(p.relative_to(ROOT))
        for label, body, line in split_labels(p, txt):
            label_locations[label].append(rel)
            label_bodies[label].append((rel, body, line))
        if p in clean_texts:
            for hook in MAP_HOOK.finditer(txt):
                map_hooks.append((rel, hook.group(1), hook.group(2)))

    common = strip_comments(read(COMMON))
    common_labels = set(LABEL.findall(common))
    all_labels = set(label_locations) | common_labels
    all_text = "\n".join(clean_texts.values()) + "\n" + "\n".join(clean_shared.values()) + "\n" + common

    duplicates = {k:v for k,v in label_locations.items() if len(v) > 1}
    cross_file_duplicates = {k:v for k,v in duplicates.items() if len(set(v)) > 1}
    same_file_duplicates = {k:v for k,v in duplicates.items() if len(set(v)) == 1}
    common_counts = Counter(LABEL.findall(common))
    common_duplicates = sorted(k for k,v in common_counts.items() if v > 1)

    unresolved = []
    for p, txt in list(clean_texts.items()) + list(clean_shared.items()):
        rel = str(p.relative_to(ROOT))
        for m in FLOW.finditer(txt):
            op, args = m.group(1), m.group(2).strip()
            if op == "map_script" or op in NON_LABEL_FLOW_MACROS:
                continue
            target = args.split(",")[-1].strip().split()[0] if args else ""
            if target and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target) and target not in all_labels and target not in IGNORED:
                unresolved.append((rel, txt[:m.start()].count("\n")+1, op, target))

    # Look through reachable script calls from synchronous map hooks for waits
    # that need a live field-frame update. This is a conservative call-graph pass.
    blocking_hook_findings = []
    hook_count = 0
    table_hook_reviews = 0
    for map_path, tag, target in map_hooks:
        if tag not in SYNCHRONOUS_HOOKS:
            continue
        roots = []
        if tag == "MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE":
            table_hook_reviews += 1
            for _, table_body, _ in label_bodies.get(target, []):
                # The table stores script pointers as .4byte entries.
                for ptr in re.findall(r"^\s*\.4byte\s+([A-Za-z_][A-Za-z0-9_]*)", table_body, re.M):
                    if ptr in all_labels:
                        roots.append(ptr)
        elif target in all_labels:
            roots.append(target)
        for root in roots:
            hook_count += 1
            queue = deque([(root, (root,))])
            seen = set()
            while queue:
                label, chain = queue.popleft()
                if label in seen:
                    continue
                seen.add(label)
                for src_path, body, start_line in label_bodies.get(label, []):
                    for command in COMMAND_RE.finditer(body):
                        command_name = command.group(1).lower()
                        if command_name in BLOCKING_COMMANDS:
                            line_no = start_line + body[:command.start()].count("\n")
                            blocking_hook_findings.append((map_path, tag, root, src_path, line_no, command_name, " -> ".join(chain)))
                    for next_label in flow_targets(body, all_labels):
                        if next_label not in seen:
                            queue.append((next_label, chain + (next_label,)))

    config_headers = sorted(CONFIG_HEADERS.rglob("*.h")) if CONFIG_HEADERS.is_dir() else []
    flag_defs = defs(FLAGS, "FLAG_") | defs(FLAGS_FRLG, "FLAG_")
    var_defs = defs(VARS, "VAR_") | defs(VARS_FRLG, "VAR_")
    for config_header in config_headers:
        flag_defs |= defs(config_header, "FLAG_")
        var_defs |= defs(config_header, "VAR_")
    json_errors, object_script_review = [], []
    map_ids = Counter()
    json_sources: dict[str, str] = {}
    for p in maps:
        rel = str(p.relative_to(ROOT))
        raw = read(p)
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            json_errors.append((rel, str(exc)))
            continue
        json_sources[rel] = raw
        map_ids[obj.get("id", "")] += 1
        for event in obj.get("object_events", []):
            script = event.get("script")
            if isinstance(script, str) and script not in {"0", "0x0", "NULL", "null", ""} and script not in all_labels:
                object_script_review.append((rel, script))
    dup_ids = sorted(k for k,v in map_ids.items() if k and v > 1)

    symbol_sources = {str(p.relative_to(ROOT)): t for p,t in clean_texts.items()}
    symbol_sources.update({str(p.relative_to(ROOT)): t for p,t in clean_shared.items()})
    symbol_sources["data/event_scripts.s"] = common
    symbol_sources.update(json_sources)
    symbol_text = "\n".join(symbol_sources.values())
    flags_used = set(FLAG_NAME.findall(symbol_text))
    vars_used = set(VAR_NAME.findall(symbol_text))
    unknown_flags = sorted(flags_used - flag_defs)
    unknown_vars = sorted(vars_used - var_defs)

    print("Event-script static scan (heuristics; manual confirmation required)")
    print(f"scripts.inc files: {len(files)}")
    print(f"map.json files: {len(maps)}")
    print(f"shared scripts files: {len(shared_files)}")
    print(f"config headers searched for extra flag/var definitions: {len(config_headers)}")
    print(f"map/shared labels indexed: {len(label_locations)}")
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
    print(f"synchronous map hook roots inspected: {hook_count}")
    print(f"ON_WARP_INTO_MAP_TABLE roots manually discovered: {table_hook_reviews}")
    print(f"blocking-command candidates reachable from synchronous hooks: {len(blocking_hook_findings)}")

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
    for row in blocking_hook_findings[:250]:
        print("BLOCKING_SYNC_HOOK_CANDIDATE", *row)
    for name in dup_ids:
        print("DUPLICATE_MAP_ID", name)
    print("Limitations: conditional branches, pointer tables, generated constants, native-C effects, and fallthrough are only partially modeled. All candidates require review; this tool must never auto-delete or modify events.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
