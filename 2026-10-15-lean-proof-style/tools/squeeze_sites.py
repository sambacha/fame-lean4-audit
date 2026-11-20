#!/usr/bin/env python3
"""Squeeze non-terminal `simp`/`simp_all` calls to the `simp only [...]` list `simp?` reports *at that
site* (LEAN_PROOF_STYLE.md R10b/R10d).

    squeeze_sites.py mark SITES.txt          # put `?` on the first bare simp of each listed line
    squeeze_sites.py apply SITES.txt LOG     # replace each marked call by its own `Try this`

SITES.txt holds `file:line` rows. `apply` reads the `Try this` suggestions from a `lake build` log,
keyed by file, line and the column of the marked call. A call with no suggestion, or with more than
one distinct suggestion (it ran in several goals, e.g. under `<;>`), is unmarked again and left as
it was: no single list is right for it. The build decides whether the result stands.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STATE = Path("/tmp/squeeze_marks.json")
BARE = re.compile(r"\b(simp_all|simp)\b(?!\?)(?! only)")


def sites(path: str) -> list[tuple[str, int]]:
    out = []
    for row in Path(path).read_text().split():
        f, l = row.rsplit(":", 1)
        out.append((f, int(l)))
    return out


def tactic_end(text: str, start: int) -> int:
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c in "[(⟨{":
            depth += 1
        elif c in "])⟩}":
            if depth == 0:
                return i
            depth -= 1
        elif depth == 0 and (text.startswith(";", i) or text.startswith("<;>", i)):
            return i
        i += 1
    return len(text)


def mark(path: str) -> int:
    marks = []
    for f, l in sites(path):
        p = ROOT / f
        lines = p.read_text().split("\n")
        m = BARE.search(lines[l - 1])
        if not m:
            print(f"no bare simp: {f}:{l}")
            continue
        lines[l - 1] = lines[l - 1][:m.end()] + "?" + lines[l - 1][m.end():]
        p.write_text("\n".join(lines))
        marks.append((f, l, m.start()))
    STATE.write_text(json.dumps(marks))
    print(f"marked {len(marks)}")
    return 0


def suggestions(log: str) -> dict[tuple[str, int, int], set[str]]:
    """`Try this` texts by (file, line, column). A long suggestion is wrapped over several log
    lines; continuation lines are indented and are joined back with single spaces."""
    out: dict[tuple[str, int, int], set[str]] = {}
    lines = log.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"info: (\S+?):(\d+):(\d+): Try this:\s*$", line)
        if not m:
            continue
        body = []
        for nxt in lines[i + 1:]:
            if not nxt.startswith(" ") or not nxt.strip():
                break
            body.append(nxt.strip())
        text = re.sub(r"^\[apply\]\s*", "", " ".join(body))
        out.setdefault((m.group(1), int(m.group(2)), int(m.group(3))), set()).add(text)
    return out


def apply(path: str, logpath: str) -> int:
    sugg = suggestions(Path(logpath).read_text())
    marks = json.loads(STATE.read_text())
    done = 0
    for f, l, col in sorted(marks, key=lambda x: (x[0], x[1], -x[2])):
        p = ROOT / f
        lines = p.read_text().split("\n")
        text = lines[l - 1]
        got = sugg.get((f, l, col), set())
        end = tactic_end(text, col)
        if len(got) == 1:
            new = next(iter(got))
            seg = text[col:end]
            trail = seg[len(seg.rstrip()):]
            lines[l - 1] = text[:col] + new + trail + text[end:]
            done += 1
        else:
            lines[l - 1] = text[:col] + text[col:].replace("?", "", 1)
            print(f"left as is ({len(got)} suggestions): {f}:{l}")
        p.write_text("\n".join(lines))
    print(f"squeezed {done} of {len(marks)}")
    return 0


if __name__ == "__main__":
    if sys.argv[1] == "mark":
        sys.exit(mark(sys.argv[2]))
    sys.exit(apply(sys.argv[2], sys.argv[3]))
