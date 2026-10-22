#!/usr/bin/env python3
"""Conservative inventory and cross-reference audit for pokeemerald event scripts.

Static findings are candidates for review, not proof of runtime defects. The tool never
changes game data. Run it against the exact upstream revision used by the build.
"""
from __future__ import annotations
import argparse, collections, json, re, sys
from pathlib import Path

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
GLOBAL_LABEL = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)::\s*(?:@.*)?$")
ANY_LABEL = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)(::|:)\s*(?:@.*)?$")
INCLUDE = re.compile(r'^\s*\.include\s+"([^"]+)"')
CONSTANT_DEF = re.compile(r"^\s*#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)\b")
COMMAND_NAME = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\b(.*)$")
DIRECT_FIRST = {"goto", "call", "msgbox", "message", "braillemessage"}
DIRECT_LAST = {"map_script"}
MOVEMENT_LAST = {"applymovement", "applymovement_at"}
CONDITIONAL_TARGET = re.compile(r"^(?:goto|call)_if_[A-Za-z0-9_]+$")
IGNORED = {"0", "0x0", "NULL", "NONE"}

def strip_comment(line):
    quote = None
    escaped = False
    for i, ch in enumerate(line):
        if escaped:
            escaped = False
            continue
        if ch == "\\" and quote:
            escaped = True
            continue
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "@":
            return line[:i]
    return line

def split_args(text):
    parts, current = [], []
    quote = None
    escaped = False
    depth = 0
    for ch in text:
        if escaped:
            current.append(ch); escaped = False; continue
        if ch == "\\" and quote:
            current.append(ch); escaped = True; continue
        if quote:
            current.append(ch)
            if ch == quote: quote = None
        elif ch in ("'", '"'):
            quote = ch; current.append(ch)
        elif ch == "(": depth += 1; current.append(ch)
        elif ch == ")" and depth: depth -= 1; current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip()); current = []
        else: current.append(ch)
    if current or text.strip(): parts.append("".join(current).strip())
    return parts

def symbols_from_file(path):
    result = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        clean = strip_comment(raw).strip()
        match = ANY_LABEL.match(clean)
        if match:
            result.append((match.group(1), match.group(2) == "::", line_no))
    return result

def read_defs(path, prefix):
    names = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = CONSTANT_DEF.match(line)
            if match and match.group(1).startswith(prefix):
                names.add(match.group(1))
    return names

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--markdown", type=Path, default=Path("event-script-audit.md"))
    ap.add_argument("--json", dest="json_path", type=Path, default=Path("event-script-audit.json"))
    args = ap.parse_args()
    src = args.source.resolve()
    if not (src / "data/event_scripts.s").exists():
        print("ERROR: data/event_scripts.s missing from source checkout", file=sys.stderr)
        return 2

    map_files = sorted((src / "data/maps").glob("**/scripts.inc"))
    shared_files = sorted((src / "data/scripts").glob("**/*.inc"))
    scan_files = sorted(set(map_files + shared_files))
    labels = collections.defaultdict(list)
    global_labels = collections.defaultdict(list)
    file_stats = {}
    command_counts = collections.Counter()
    refs = []
    used_flags, used_vars = collections.Counter(), collections.Counter()
    movement_candidates = []

    for path in scan_files:
        rel = path.relative_to(src).as_posix()
        raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        current_label = "(preamble)"
        start_line = 1
        block = collections.Counter()
        local_commands = collections.Counter()
        label_names = []
        line_count = len(raw_lines)

        def finish_block(end_line):
            if block["applymovement"] and not block["waitmovement"]:
                movement_candidates.append({
                    "file": rel, "label": current_label, "line": start_line,
                    "applymovement_count": block["applymovement"],
                    "note": "Review only: no waitmovement in this label block; may be intentional."
                })

        for line_no, raw in enumerate(raw_lines, 1):
            clean = strip_comment(raw).strip()
            if not clean:
                continue
            lm = ANY_LABEL.match(clean)
            if lm:
                finish_block(line_no - 1)
                current_label, start_line = lm.group(1), line_no
                block = collections.Counter()
                label_names.append(current_label)
                entry = {"file": rel, "line": line_no, "global": lm.group(2) == "::"}
                labels[current_label].append(entry)
                if lm.group(2) == "::":
                    global_labels[current_label].append(entry)
                continue
            if clean.startswith(("#", ".", ";")):
                continue
            cm = COMMAND_NAME.match(clean)
            if not cm:
                continue
            command, arg_text = cm.group(1).lower(), cm.group(2).strip()
            args_list = split_args(arg_text)
            if command in {
                "goto", "call", "goto_if_set", "goto_if_unset", "goto_if_eq", "goto_if_ne",
                "goto_if_lt", "goto_if_gt", "goto_if_le", "goto_if_ge", "call_if_set",
                "call_if_unset", "call_if_eq", "call_if_ne", "map_script", "applymovement",
                "applymovement_at", "msgbox", "message", "braillemessage", "lock", "lockall",
                "release", "releaseall", "end", "return", "waitmovement", "waitstate",
                "special", "setflag", "clearflag", "setvar", "addvar", "subvar",
                "setobjectxyperm", "addobject", "removeobject", "hideobjectat",
                "showobjectat", "warp", "warpdoor", "setescapewarp", "trainerbattle",
                "playse", "delay", "checkflag", "checkitem", "checkplayergender"
            } or command.startswith(("goto_if_", "call_if_")):
                command_counts[command] += 1
                local_commands[command] += 1
                block[command] += 1

            target = None
            target_kind = ""
            if command in DIRECT_FIRST and args_list:
                target, target_kind = args_list[0], "script-or-message"
            elif command in DIRECT_LAST and args_list:
                target, target_kind = args_list[-1], "script"
            elif command in MOVEMENT_LAST and len(args_list) >= 2:
                target, target_kind = args_list[-1], "movement"
            elif CONDITIONAL_TARGET.match(command) and args_list:
                target, target_kind = args_list[-1], "script"
            elif command == "case" and args_list:
                target, target_kind = args_list[-1], "script-case"
            if target:
                target = target.strip()
                if IDENT.fullmatch(target) and target not in IGNORED:
                    refs.append({"file": rel, "line": line_no, "label": current_label,
                                 "command": command, "target": target, "kind": target_kind})
            for token in re.findall(r"\b(?:FLAG|VAR)_[A-Z0-9_]+\b", clean):
                if token.startswith("FLAG_"): used_flags[token] += 1
                elif token.startswith("VAR_"): used_vars[token] += 1
        finish_block(line_count)
        file_stats[rel] = {"lines": line_count, "label_count": len(label_names),
                           "global_label_count": sum(1 for x in label_names if any(
                               d["file"] == rel and d["global"] for d in labels[x])),
                           "commands": dict(local_commands), "labels": label_names}

    known = set(labels)
    unresolved = [r for r in refs if r["target"] not in known]
    duplicates = [{"name": name, "definitions": defs}
                  for name, defs in sorted(global_labels.items()) if len(defs) > 1]

    maps = []
    map_missing_scripts = []
    map_json_files = sorted((src / "data/maps").glob("**/map.json"))
    for path in map_json_files:
        rel = path.relative_to(src).as_posix()
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            maps.append({"file": rel, "json_error": str(exc)})
            continue
        map_id = obj.get("id", path.parent.name)
        objects = obj.get("object_events") or []
        script_count = 0
        for event in objects:
            script = str(event.get("script", "0x0")).strip()
            if script not in ("0", "0x0", "NULL", ""):
                script_count += 1
                if script not in known:
                    map_missing_scripts.append({"map": map_id, "file": rel,
                        "object": event.get("local_id", event.get("graphics_id", "?")),
                        "script": script})
        maps.append({"id": map_id, "file": rel, "object_events": len(objects),
            "object_scripts": script_count, "warp_events": len(obj.get("warp_events") or []),
            "coord_events": len(obj.get("coord_events") or []),
            "bg_events": len(obj.get("bg_events") or [])})

    flag_defs = read_defs(src / "include/constants/flags.h", "FLAG_")
    var_defs = read_defs(src / "include/constants/vars.h", "VAR_")
    undefined_flags = [{"name": n, "uses": count} for n, count in sorted(used_flags.items()) if n not in flag_defs]
    undefined_vars = [{"name": n, "uses": count} for n, count in sorted(used_vars.items()) if n not in var_defs]

    includes = []
    for line_no, raw in enumerate((src / "data/event_scripts.s").read_text(
            encoding="utf-8", errors="replace").splitlines(), 1):
        match = INCLUDE.match(raw)
        if match and ("scripts.inc" in match.group(1) or match.group(1).startswith("data/scripts/")):
            includes.append({"line": line_no, "path": match.group(1),
                             "exists": (src / match.group(1)).exists()})

    report = {
        "upstream_source_path": str(src),
        "scope": {"map_script_files": len(map_files), "shared_script_files": len(shared_files),
                  "map_json_files": len(map_json_files), "direct_event_script_includes": len(includes),
                  "scanned_script_lines": sum(v["lines"] for v in file_stats.values())},
        "labels": {"distinct_names": len(labels), "definitions": sum(len(v) for v in labels.values()),
                   "global_symbols": len(global_labels), "duplicate_global_candidates": duplicates},
        "command_counts": dict(sorted(command_counts.items())),
        "references": {"checked_script_like_targets": len(refs), "unresolved_candidates": unresolved,
                       "map_object_missing_script_candidates": map_missing_scripts},
        "constant_candidates": {"flags_used": len(used_flags), "undefined_flags": undefined_flags,
                                "vars_used": len(used_vars), "undefined_vars": undefined_vars},
        "movement_wait_review_candidates": movement_candidates,
        "maps": maps, "includes": includes, "per_file": file_stats
    }
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total_lines = report["scope"]["scanned_script_lines"]
    md = [
        "# Full Event Script Inventory",
        "",
        "This is a conservative static inventory, not proof of runtime safety. Findings may include false positives due to conditional assembly, macros, and intentional control transfers.",
        "",
        "## Scope",
        "",
        f"- Map scripts.inc files: {len(map_files)}",
        f"- Shared data/scripts include files: {len(shared_files)}",
        f"- Map JSON files: {len(map_json_files)}",
        f"- Direct includes listed by data/event_scripts.s: {len(includes)}",
        f"- Source lines scanned: {total_lines}",
        f"- Distinct label names: {len(labels)}",
        f"- Label definitions: {sum(len(v) for v in labels.values())}",
        f"- Global symbols: {len(global_labels)}",
        "",
        "## Findings requiring triage",
        "",
        f"- Duplicate global-label candidates: {len(duplicates)}",
        f"- Unresolved script-like target candidates: {len(unresolved)}",
        f"- Map object script labels missing from scanned labels: {len(map_missing_scripts)}",
        f"- Undefined flag candidates: {len(undefined_flags)}",
        f"- Undefined variable candidates: {len(undefined_vars)}",
        f"- applymovement label blocks without waitmovement: {len(movement_candidates)} (review only, may be intentional)",
        "",
        "No static finding is auto-treated as a confirmed defect. Review source context and conditional compilation before changing code.",
        "",
        "## Command counts",
        "",
        "| Command | Occurrences |",
        "|---|---:|"
    ]
    for name, count in sorted(command_counts.items(), key=lambda item: (-item[1], item[0])):
        md.append(f"| {name} | {count} |")
    md += ["", "## Duplicate global symbol candidates", ""]
    if duplicates:
        for item in duplicates:
            locations = ", ".join(f"{d['file']}:{d['line']}" for d in item["definitions"])
            md.append(f"- {item['name']}: {locations}")
    else: md.append("- None detected.")
    md += ["", "## Unresolved script-like target candidates", ""]
    if unresolved:
        for item in unresolved[:500]:
            md.append(f"- {item['file']}:{item['line']}: {item['command']} -> {item['target']} (label {item['label']}, {item['kind']})")
        if len(unresolved) > 500: md.append(f"- Markdown truncated; {len(unresolved)-500} more are in JSON.")
    else: md.append("- None detected.")
    md += ["", "## Map object script candidates", ""]
    if map_missing_scripts:
        for item in map_missing_scripts[:500]:
            md.append(f"- {item['file']} map {item['map']}, object {item['object']} -> {item['script']}")
        if len(map_missing_scripts) > 500: md.append(f"- Markdown truncated; {len(map_missing_scripts)-500} more are in JSON.")
    else: md.append("- None detected.")
    md += ["", "## Undefined flag and variable candidates", "",
           "Flags: " + (", ".join(f"{x['name']} ({x['uses']})" for x in undefined_flags[:200]) or "none detected"),
           "",
           "Vars: " + (", ".join(f"{x['name']} ({x['uses']})" for x in undefined_vars[:200]) or "none detected"),
           "", "## Movement/wait review candidates", ""]
    if movement_candidates:
        for item in movement_candidates[:300]:
            md.append(f"- {item['file']}:{item['line']} label {item['label']}: {item['applymovement_count']} movement command(s) with no wait in the same label block.")
        if len(movement_candidates) > 300: md.append(f"- Markdown truncated; {len(movement_candidates)-300} more are in JSON.")
    else: md.append("- None detected.")
    md += ["", "## Per-map script inventory", "",
           "| Map folder | Script labels | Commands summary | File |",
           "|---|---:|---|---|"]
    for path in map_files:
        rel = path.relative_to(src).as_posix()
        st = file_stats[rel]
        commands = st["commands"]
        summary = ", ".join(f"{k}={v}" for k, v in sorted(commands.items())
                            if k in {"map_script", "goto", "call", "applymovement", "waitmovement", "lock", "release", "warp"})
        md.append(f"| {path.parent.name} | {st['global_label_count']} | {summary or '-'} | {rel} |")
    md += ["", "## Event script include graph", ""]
    for item in includes:
        md.append(f"- {'OK' if item['exists'] else 'MISSING'} {item['path']} (event_scripts.s line {item['line']})")
    md += ["", "## Every scanned script file", "", "| File | Lines | Labels | Commands |", "|---|---:|---:|---:|"]
    for rel, st in sorted(file_stats.items()):
        md.append(f"| {rel} | {st['lines']} | {st['label_count']} | {sum(st['commands'].values())} |")
    md += ["", "## Required review gates", "",
        "1. Manually triage duplicate symbol candidates, unresolved references and undefined flags/vars, accounting for build-time conditionals.",
        "2. Review movement/wait candidates in context; the checker cannot infer every legal control-flow path.",
        "3. Run git apply --check against a clean source tree and compile with the exact pinned toolchain.",
        "4. For every changed event, test new game, enter/exit map, re-enter, save/load, relevant NPC interaction, battle transition and normal ferry flows.",
        "5. Never replace the previously tested ROM baseline before a new build is verified.",
        "",
        "The inventory does not edit any source code. It intentionally exits successfully so the initial findings can be reviewed before deciding which checks should block CI."]
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({
        "map_script_files": len(map_files), "shared_script_files": len(shared_files),
        "map_json_files": len(map_json_files), "distinct_label_names": len(labels),
        "duplicate_global_candidates": len(duplicates), "unresolved_target_candidates": len(unresolved),
        "missing_map_object_scripts": len(map_missing_scripts), "undefined_flag_candidates": len(undefined_flags),
        "undefined_var_candidates": len(undefined_vars), "movement_wait_candidates": len(movement_candidates),
        "markdown": str(args.markdown.resolve()), "json": str(args.json_path.resolve())
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
