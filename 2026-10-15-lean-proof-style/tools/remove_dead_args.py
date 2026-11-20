#!/usr/bin/env python3
"""Remove the `simp`/`grind` arguments that Lean itself reports as dead.

Input: a `lake build` log. Two core-Lean warnings are acted on, and nothing else:

* `linter.unusedSimpArgs` -- "This simp argument is unused: <arg>";
* `grind` -- "this parameter is redundant, environment already contains `<lemma>` annotated ...".

Each warning carries the file, line and column of the argument. The argument is removed only when
the text at that exact position is the reported argument (optionally behind `←`), together with
one adjacent comma. An argument list left empty is removed with its brackets. Anything that does
not match is reported and left alone. Files whose text is pinned elsewhere (`HandoffV3/`) are
skipped. The build decides whether each removal was right; this tool decides nothing.

Usage: remove_dead_args.py BUILD_LOG [--dry-run]
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKIP_PREFIXES = ("HandoffV3/",)
MSG = re.compile(r"\n(?=(?:warning|info|error): |[✔ℹ⚠✖] \[)")


def dead_args(log: str) -> list[tuple[str, int, int, str]]:
    out = []
    for part in MSG.split(log):
        m = re.match(r"warning: (\S+?):(\d+):(\d+): (.*)", part, re.S)
        if not m:
            continue
        f, line, col, msg = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        if "simp argument is unused" in msg:
            arg = msg.split("\n")[1].strip()
        elif "parameter is redundant" in msg:
            arg = re.search(r"contains `([^`]*)`", msg).group(1)
        else:
            continue
        out.append((f, line, col, arg))
    return sorted(set(out))


def remove(text: str, col: int, arg: str) -> str | None:
    rest = text[col:]
    lead = re.match(r"(←\s*|-\s*)?", rest).group(0)
    if not rest[len(lead):].startswith(arg):
        return None
    end = col + len(lead) + len(arg)
    if end < len(text) and (text[end].isalnum() or text[end] in "_.'"):
        return None  # the reported name is only a prefix of what is written here
    after = re.match(r"\s*,\s*", text[end:])
    if after:
        return text[:col] + text[end + after.end():]
    before = re.search(r",\s*$", text[:col])
    if before:
        return text[:before.start()] + text[end:]
    # sole argument: drop the brackets too
    lb = re.search(r"\s*\[\s*$", text[:col])
    rb = re.match(r"\s*\]", text[end:])
    if lb and rb:
        return text[:lb.start()] + text[end + rb.end():]
    return None


def main(argv: list[str]) -> int:
    log = Path(argv[1]).read_text()
    dry = "--dry-run" in argv
    by_file: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for f, line, col, arg in dead_args(log):
        if f.startswith(SKIP_PREFIXES):
            print(f"skip (pinned): {f}:{line}:{col} {arg}")
            continue
        by_file[f].append((line, col, arg))
    done = failed = 0
    for f, sites in sorted(by_file.items()):
        path = ROOT / f
        lines = path.read_text().split("\n")
        # right to left within a line, so earlier columns stay valid
        for line, col, arg in sorted(sites, key=lambda s: (s[0], -s[1])):
            new = remove(lines[line - 1], col, arg)
            if new is None:
                print(f"no match: {f}:{line}:{col} {arg!r}: {lines[line - 1].strip()}")
                failed += 1
                continue
            lines[line - 1] = new
            done += 1
        if not dry:
            path.write_text("\n".join(lines))
    print(f"removed {done}, left {failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
