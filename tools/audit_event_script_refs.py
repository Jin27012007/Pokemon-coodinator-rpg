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
SPECIALS = ROOT / "data/specials.inc"
GLOBAL_MOVEMENTS = ROOT / "data/scripts/movement.inc"
EVENT_MACROS = ROOT / "asm/macros/event.inc"
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
MOVEMENT_REF = re.compile(r"^\s*applymovement(?:at)?\s+[^,\n]+,\s*([A-Za-z_][A-Za-z0-9_]*)", re.M)
SPECIAL_REF = re.compile(r"^\s*(special|specialvar)\s+([^\n@]+)", re.M)
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
# Commands that wait on a frame-driven animation/state. Inside RunScriptImmediately
# these are the high-confidence deadlock candidates (the boat bug used waitmovement).
FRAME_WAIT_COMMANDS = {
    "delay", "animateflash", "fadescreen", "fadescreenspeed", "fadescreenswapbuffers",
    "waitmovement", "waitmovementat", "waitmovementall", "waitse", "waitfanfare",
    "fadeoutbgm", "waitmessage", "waitdooranim", "waitfieldeffect", "waitmoncry",
    "hidemonpic", "hidefollower", "lock", "lockall", "lockfortrainer",
}
# These stop or redirect the global script context or launch another game flow.
# In an immediate map callback they need semantic review, but are not the same as
# a native wait that spins until frame-driven work finishes.
CONTEXT_SENSITIVE_COMMANDS = {
    "waitstate", "waitbuttonpress", "callstd", "yesnobox", "dynmultichoice", "multichoice",
    "multichoicedefault", "multichoicegrid", "drawboxtext", "showcontestpainting",
    "dotrainerbattle", "dowildbattle", "pokemart", "pokemartdecoration",
    "pokemartdecoration2", "playslotmachine", "choosecontestmon", "startcontest",
    "showcontestresults", "contestlinktransfer",
}
ASYNC_RISK_COMMANDS = {
    "callnative", "gotonative", "warp", "warpsilent", "warpdoor", "warphole",
    "warpteleport", "warpmossdeepgym", "warpspinenter", "warpwhitefade",
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

def macro_risk_catalog(path: Path, special_waits: set[str]) -> dict[str, set[str]]:
    """Conservatively identify event macros that expand into blocking/context commands."""
    text = strip_comments(read(path))
    macros: dict[str, list[str]] = {}
    current: str | None = None
    body: list[str] = []
    for line in text.splitlines():
        start = re.match(r"^\s*\.macro\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if start:
            if current is not None:
                macros[current] = body
            current = start.group(1).lower()
            body = []
            continue
        if re.match(r"^\s*\.endm\b", line):
            if current is not None:
                macros[current] = body
            current = None
            body = []
            continue
        if current is not None:
            body.append(line)
    if current is not None:
        macros[current] = body

    risk: dict[str, set[str]] = {name: set() for name in macros}
    dependencies: dict[str, set[str]] = {name: set() for name in macros}
    for name, body_lines in macros.items():
        for line in body_lines:
            match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\b(.*)$", line)
            if not match:
                continue
            command = match.group(1).lower()
            args = match.group(2).strip()
            if command in FRAME_WAIT_COMMANDS:
                risk[name].add("frame-wait")
            if command in CONTEXT_SENSITIVE_COMMANDS:
                # The base special/specialvar macro encodes a conditional waitstate;
                # actual special names are checked against data/specials.inc separately.
                if not (name in {"special", "specialvar"} and command == "waitstate"):
                    risk[name].add("context")
            if command in ASYNC_RISK_COMMANDS:
                risk[name].add("async")
            if command in {"special", "specialvar"}:
                special_name = args.split()[0].strip(",") if args else ""
                if special_name in special_waits:
                    risk[name].add("context")
                elif not special_name or "\\" in special_name:
                    risk[name].add("special")
            if command in macros and command != name:
                dependencies[name].add(command)

    # Propagate risks through nested macro expansions until the graph stabilizes.
    changed = True
    while changed:
        changed = False
        for name, deps in dependencies.items():
            combined = set(risk[name])
            for dep in deps:
                combined.update(risk[dep])
            if combined != risk[name]:
                risk[name] = combined
                changed = True
    return risk


def split_labels(path: Path, text: str) -> list[tuple[str, str, int]]:
    matches = list(LABEL.finditer(text))
    result = []
    rel = str(path.relative_to(ROOT))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end():end]
        result.append((match.group(1), body, text[:match.start()].count("\n") + 1))
    return result

def flow_target(op: str, args: str) -> str:
    args = args.strip()
    if not args:
        return ""
    # These macros take trainer ID and label as whitespace-separated operands.
    if op in NON_LABEL_FLOW_MACROS:
        return args.split()[-1].strip(",")
    return args.split(",")[-1].strip().split()[0]

def flow_targets(body: str, all_labels: set[str]) -> set[str]:
    targets = set()
    for match in FLOW.finditer(body):
        op, args = match.group(1), match.group(2).strip()
        if op == "map_script":
            continue
        target = flow_target(op, args)
        if target in all_labels:
            targets.add(target)
    for match in CASE_REF.finditer(body):
        target = match.group(1)
        if target in all_labels:
            targets.add(target)
    return targets

def collect_script_fields(value, prefix: str = ""):
    """Yield paths and string values for script fields at any map-event depth."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}" if prefix else key
            if key == "script" and isinstance(child, str):
                yield child_path, child
            yield from collect_script_fields(child, child_path)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from collect_script_fields(child, f"{prefix}[{i}]")

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
    common_definitions = split_labels(COMMON, common)
    for label, body, line in common_definitions:
        label_bodies[label].append((str(COMMON.relative_to(ROOT)), body, line))
    common_labels = set(LABEL.findall(common))
    all_labels = set(label_locations) | common_labels
    all_text = "\n".join(clean_texts.values()) + "\n" + "\n".join(clean_shared.values()) + "\n" + common

    duplicates = {k:v for k,v in label_locations.items() if len(v) > 1}
    cross_file_duplicates = {k:v for k,v in duplicates.items() if len(set(v)) > 1}
    same_file_duplicates = {k:v for k,v in duplicates.items() if len(set(v)) == 1}
    common_counts = Counter(LABEL.findall(common))
    common_duplicates = sorted(k for k,v in common_counts.items() if v > 1)

    movement_terminator_findings = []
    # Movement scripts normally finish with step_end. Sentinels used to delimit
    # the follower-safe movement range are labels, not executable movements.
    for label, definitions in label_bodies.items():
        if "Movement_" not in label or label.endswith("FollowerSafeStart"):
            continue
        for src_path, body, start_line in definitions:
            instructions = [
                line.strip() for line in body.splitlines()
                if line.strip() and not line.strip().startswith(".")
            ]
            if not instructions:
                continue
            terminal = instructions[-1].split()[0].lower()
            if terminal not in {"step_end", "end"}:
                movement_terminator_findings.append((src_path, start_line, label, terminal))

    # Specials with waitstate=1 cause the special macro to emit a waitstate
    # automatically. These also need review if reachable from a synchronous hook.
    special_waits = set()
    special_defs = set()
    for line in strip_comments(read(SPECIALS)).splitlines():
        match = re.match(r"^\s*def_special\s+([A-Za-z_][A-Za-z0-9_]*)(.*)$", line)
        if match:
            special_defs.add(match.group(1))
            if re.search(r"\bwaitstate\s*=\s*1\b", match.group(2)):
                special_waits.add(match.group(1))

    macro_risks = macro_risk_catalog(EVENT_MACROS, special_waits)
    macro_frame_waits = {name for name, risks in macro_risks.items() if "frame-wait" in risks}
    macro_context_risks = {name for name, risks in macro_risks.items() if "context" in risks}
    macro_async_risks = {name for name, risks in macro_risks.items() if "async" in risks or "special" in risks}

    unresolved = []
    movement_ref_findings = []
    special_ref_findings = []
    for p, txt in list(clean_texts.items()) + list(clean_shared.items()) + [(COMMON, common)]:
        rel = str(p.relative_to(ROOT))
        for m in FLOW.finditer(txt):
            op, args = m.group(1), m.group(2).strip()
            target = flow_target(op, args)
            if target and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", target) and target not in all_labels and target not in IGNORED:
                unresolved.append((rel, txt[:m.start()].count("\n")+1, op, target))
        for m in CASE_REF.finditer(txt):
            target = m.group(1)
            if target not in all_labels and target not in IGNORED:
                unresolved.append((rel, txt[:m.start()].count("\n")+1, "case", target))
        for m in MOVEMENT_REF.finditer(txt):
            target = m.group(1)
            if target not in all_labels:
                movement_ref_findings.append((rel, txt[:m.start()].count("\n")+1, target))
        for m in SPECIAL_REF.finditer(txt):
            op, args = m.group(1), m.group(2).strip()
            target = args.split(",")[-1].strip().split()[0] if op == "specialvar" else (args.split()[0].strip(",") if args else "")
            if target and target not in special_defs:
                special_ref_findings.append((rel, txt[:m.start()].count("\n")+1, op, target))



    # Look through reachable script calls from synchronous map hooks for waits
    # that need a live field-frame update. This is a conservative call-graph pass.
    blocking_hook_findings = []
    context_hook_findings = []
    async_hook_findings = []
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
                        args = command.group(2).strip()
                        line_no = start_line + body[:command.start()].count("\n")
                        if command_name in FRAME_WAIT_COMMANDS:
                            blocking_hook_findings.append((map_path, tag, root, src_path, line_no, command_name, " -> ".join(chain)))
                        elif command_name == "special":
                            special_name = args.split()[0] if args else ""
                            if special_name in special_waits:
                                context_hook_findings.append((map_path, tag, root, src_path, line_no, "special(waitstate=1):" + special_name, " -> ".join(chain)))
                        elif command_name in CONTEXT_SENSITIVE_COMMANDS:
                            context_hook_findings.append((map_path, tag, root, src_path, line_no, command_name, " -> ".join(chain)))
                        elif command_name in ASYNC_RISK_COMMANDS:
                            async_hook_findings.append((map_path, tag, root, src_path, line_no, command_name, " -> ".join(chain)))

                        # Macros can hide waits/native calls behind one apparent command.
                        if command_name not in {"special", "specialvar"}:
                            if command_name in macro_frame_waits:
                                blocking_hook_findings.append((map_path, tag, root, src_path, line_no, "macro expands to frame wait: " + command_name, " -> ".join(chain)))
                            if command_name in macro_context_risks:
                                context_hook_findings.append((map_path, tag, root, src_path, line_no, "macro expands to context control: " + command_name, " -> ".join(chain)))
                            if command_name in macro_async_risks:
                                async_hook_findings.append((map_path, tag, root, src_path, line_no, "macro expands to native/special: " + command_name, " -> ".join(chain)))
                    for next_label in flow_targets(body, all_labels):
                        if next_label not in seen:
                            queue.append((next_label, chain + (next_label,)))

    config_headers = sorted(CONFIG_HEADERS.rglob("*.h")) if CONFIG_HEADERS.is_dir() else []
    flag_defs = defs(FLAGS, "FLAG_") | defs(FLAGS_FRLG, "FLAG_")
    var_defs = defs(VARS, "VAR_") | defs(VARS_FRLG, "VAR_")
    for config_header in config_headers:
        flag_defs |= defs(config_header, "FLAG_")
        var_defs |= defs(config_header, "VAR_")
    json_errors = []
    script_ref_findings = []
    duplicate_local_ids = []
    connection_map_findings = []
    warp_map_findings = []
    destination_warp_findings = []
    map_ids = Counter()
    json_sources: dict[str, str] = {}
    map_data: dict[str, tuple[str, dict]] = {}
    for p in maps:
        rel = str(p.relative_to(ROOT))
        raw = read(p)
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            json_errors.append((rel, str(exc)))
            continue
        json_sources[rel] = raw
        map_id = obj.get("id", "")
        map_ids[map_id] += 1
        map_data[map_id] = (rel, obj)
        local_id_locations: dict[str, list[int]] = defaultdict(list)
        for event_index, event in enumerate(obj.get("object_events", [])):
            local_id = event.get("local_id")
            if isinstance(local_id, str) and local_id not in {"", "0", "0x0"}:
                local_id_locations[local_id].append(event_index)
        for local_id, locations in local_id_locations.items():
            if len(locations) > 1:
                duplicate_local_ids.append((rel, map_id, local_id, locations))
        for field_path, script in collect_script_fields(obj):
            if script not in {"0", "0x0", "NULL", "null", ""} and script not in all_labels:
                script_ref_findings.append((rel, field_path, script))

    # Check every map connection and warp destination against the same map.json catalog.
    for source_id, (rel, obj) in map_data.items():
        for connection in obj.get("connections") or []:
            dest = connection.get("map")
            if dest and dest not in map_data:
                connection_map_findings.append((rel, source_id, dest))
        for warp_index, warp in enumerate(obj.get("warp_events", [])):
            dest = warp.get("dest_map")
            if not dest:
                continue
            if dest not in map_data:
                warp_map_findings.append((rel, f"warp[{warp_index}]", dest))
                continue
            dest_warp = warp.get("dest_warp_id")
            try:
                dest_index = int(str(dest_warp), 0)
            except (TypeError, ValueError):
                continue
            # 255 is WARP_ID_NONE: coordinates are supplied instead of a target warp.
            if dest_index not in {-1, 255}:
                target_obj = map_data[dest][1]
                target_warps = target_obj.get("warp_events") or []
                if dest_index < 0 or dest_index >= len(target_warps):
                    destination_warp_findings.append(
                        (rel, f"warp[{warp_index}]", dest, dest_index, len(target_warps))
                    )
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
    print(f"movement references needing review: {len(movement_ref_findings)}")
    print(f"movement terminator candidates: {len(movement_terminator_findings)}")
    print(f"special references not defined in data/specials.inc: {len(special_ref_findings)}")
    print(f"flag symbols used / not found in selected headers: {len(flags_used)} / {len(unknown_flags)}")
    print(f"var symbols used / not found in selected headers: {len(vars_used)} / {len(unknown_vars)}")
    print(f"invalid JSON files: {len(json_errors)}")
    print(f"map event script references needing review: {len(script_ref_findings)}")
    print(f"duplicate symbolic local IDs within maps: {len(duplicate_local_ids)}")
    print(f"unknown connection map references: {len(connection_map_findings)}")
    print(f"unknown warp destination maps: {len(warp_map_findings)}")
    print(f"destination warp index candidates outside target map range: {len(destination_warp_findings)}")
    print(f"duplicate map IDs: {len(dup_ids)}")
    print(f"synchronous map hook roots inspected: {hook_count}")
    print(f"ON_WARP_INTO_MAP_TABLE roots manually discovered: {table_hook_reviews}")
    print(f"frame-wait deadlock candidates reachable from synchronous hooks: {len(blocking_hook_findings)}")
    print(f"global-context control candidates reachable from synchronous hooks: {len(context_hook_findings)}")
    print(f"native/warp-risk candidates reachable from synchronous hooks: {len(async_hook_findings)}")
    print(f"specials with implicit waitstate defined: {len(special_waits)}")
    print(f"event macros indexed: {len(macro_risks)}")
    print(f"macros expanding to frame waits: {len(macro_frame_waits)}")
    print(f"macros expanding to context controls: {len(macro_context_risks)}")
    print(f"macros expanding to native/special flows: {len(macro_async_risks)}")

    for name, locations in sorted(cross_file_duplicates.items()):
        print("CROSS_FILE_DUPLICATE_LABEL", name, "=>", ", ".join(locations))
    for name, locations in sorted(same_file_duplicates.items()):
        print("SAME_FILE_DUPLICATE_REVIEW", name, "=>", ", ".join(locations), "(may be mutually exclusive .if branches)")
    for name in common_duplicates:
        print("DUPLICATE_COMMON_AGGREGATOR_LABEL", name)
    for row in unresolved[:250]:
        print("UNRESOLVED_CANDIDATE", *row)
    for row in movement_ref_findings[:250]:
        print("MOVEMENT_REFERENCE_REVIEW", *row)
    for row in movement_terminator_findings[:250]:
        print("MOVEMENT_TERMINATOR_REVIEW", *row)
    for row in special_ref_findings[:250]:
        print("SPECIAL_REFERENCE_REVIEW", *row)
    for name in unknown_flags[:200]:
        print("FLAG_NOT_IN_SELECTED_HEADERS", name)
    for name in unknown_vars[:200]:
        print("VAR_NOT_IN_SELECTED_HEADERS", name)
    for row in json_errors[:100]:
        print("INVALID_JSON", *row)
    for row in script_ref_findings[:250]:
        print("MAP_EVENT_SCRIPT_REFERENCE_REVIEW", *row)
    for row in duplicate_local_ids[:250]:
        print("DUPLICATE_OBJECT_LOCAL_ID_REVIEW", *row)
    for row in connection_map_findings[:250]:
        print("UNKNOWN_CONNECTION_MAP", *row)
    for row in warp_map_findings[:250]:
        print("UNKNOWN_WARP_MAP", *row)
    for row in destination_warp_findings[:250]:
        print("DESTINATION_WARP_INDEX_REVIEW", *row)
    for row in blocking_hook_findings[:250]:
        print("FRAME_WAIT_SYNC_HOOK_CANDIDATE", *row)
    for row in context_hook_findings[:250]:
        print("GLOBAL_CONTEXT_SYNC_HOOK_REVIEW", *row)
    for row in async_hook_findings[:250]:
        print("ASYNC_SYNC_HOOK_REVIEW", *row)
    for name in dup_ids:
        print("DUPLICATE_MAP_ID", name)
    print("Limitations: conditional branches, pointer tables, generated constants, native-C effects, and fallthrough are only partially modeled. All candidates require review; this tool must never auto-delete or modify events.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
