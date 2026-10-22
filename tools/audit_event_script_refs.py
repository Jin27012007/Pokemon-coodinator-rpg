#!/usr/bin/env python3
"""Static sanity checks for map script references in the pinned pokeemerald-expansion tree.

This is a conservative checker, not a full event-language parser. It flags likely
missing script labels and unreferenced labels for manual review; it must not be
used to automatically delete scripts.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "data" / "maps"
EVENT_INC = ROOT / "data" / "event_scripts.s"
SCRIPT_MACROS = ROOT / "asm" / "macros" / "event.inc"

LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:::|:)\s*$", re.M)
CMD_REF_RE = re.compile(
    r"^\s*(?:map_script\s+[^,]+,|(?:goto|call|goto_if_[^,]+|call_if_[^,]+|"
    r"switch\s+[^\n]+|case\s+[^,]+,)\s*([A-Za-z_][A-Za-z0-9_]*)",
    re.M,
)
SCRIPT_FILE_RE = re.compile(r"^data/maps/.+/scripts\.inc$")

def main() -> int:
    if not MAPS.is_dir():
        print(f"ERROR: expected map directory at {MAPS}")
        return 2
    files = sorted(MAPS.glob("*/scripts.inc"))
    if not files:
        print("ERROR: no map scripts found")
        return 2

    labels: dict[str, list[str]] = {}
    texts: dict[Path, str] = {}
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        texts[path] = text
        for label in LABEL_RE.findall(text):
            labels.setdefault(label, []).append(str(path.relative_to(ROOT)))

    # Include common/global scripts since map scripts frequently jump/call them.
    global_text = EVENT_INC.read_text(encoding="utf-8", errors="replace") if EVENT_INC.exists() else ""
    all_text = "\n".join(texts.values()) + "\n" + global_text
    known_labels = set(labels)
    known_labels.update(LABEL_RE.findall(global_text))

    missing: list[tuple[str, str, str]] = []
    for path, text in texts.items():
        rel = str(path.relative_to(ROOT))
        for match in CMD_REF_RE.finditer(text):
            target = match.group(1)
            # Labels in these scripts may be defined in common includes outside
            # map scripts; avoid overclaiming missing when not in indexed sources.
            if target not in known_labels and target not in {"TRUE", "FALSE", "NO", "YES"}:
                missing.append((rel, target, text[:match.start()].count("\n") + 1))

    # Label usage count is approximate: count only textual references in indexed
    # map and common scripts. Object references, generated scripts, and C-native
    # references can legitimately be outside these files.
    unreferenced: list[tuple[str, str]] = []
    for label, locations in labels.items():
        if len(locations) == 1 and len(re.findall(r"\b" + re.escape(label) + r"\b", all_text)) <= 1:
            unreferenced.append((label, locations[0]))

    print("Static event-script scan")
    print(f"Map script files: {len(files)}")
    print(f"Map script labels: {len(labels)}")
    print(f"Potential unresolved references: {len(missing)}")
    print(f"Possibly unreferenced labels (manual review only): {len(unreferenced)}")
    for path, target, line in missing[:200]:
        print(f"UNRESOLVED? {path}:{line}: {target}")
    for label, path in unreferenced[:200]:
        print(f"UNREFERENCED? {path}: {label}")
    # Deliberately do not fail the build on heuristic warnings at initial rollout.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
