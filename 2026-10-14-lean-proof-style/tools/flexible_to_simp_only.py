#!/usr/bin/env python3
"""Squeeze each non-terminal `simp` that `linter.flexible` reported into the `simp only [...]` the
linter derived at that exact site (rules R10b and R10d).

Input: the per-file `.out` logs written by `scripts/lean_style_linters.sh`. A site is rewritten only
when all of the following hold:
* the warning carries a `Try this: [apply] simp only [...]` suggestion (the list comes from `simp?`
  run at that site, never copied from a look-alike goal);
* the tactic text the warning quotes (`'simp [foo] at h'`) appears verbatim in the source at the
  reported line and column, on one line.
Anything else is listed as skipped and left for review. The result must be rebuilt.

    python3 flexible_to_simp_only.py LINT_OUTDIR [--dry-run] [--only PREFIX]
"""
import collections, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
HEAD = re.compile(r"^(\S+\.lean):(\d+):(\d+): warning: '(.*)' is a flexible tactic modifying")


def blocks(text):
    cur = []
    for line in text.splitlines():
        if re.match(r"^\S+\.lean:\d+:\d+: ", line) and cur:
            yield cur
            cur = []
        cur.append(line)
    if cur:
        yield cur


def main(argv):
    outdir = pathlib.Path(argv[0]); dry = "--dry-run" in argv
    only = argv[argv.index("--only") + 1] if "--only" in argv else ""
    sites = collections.defaultdict(dict)  # one entry per site: a site is reported once per later use
    skipped = []
    for p in sorted(outdir.glob("*.out")):
        for b in blocks(p.read_text(errors="replace")):
            m = HEAD.match(b[0])
            if not m or not m.group(1).startswith(only):
                continue
            f, ln, col, quoted = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
            sugg = None
            for i, line in enumerate(b):
                if line.strip().startswith("[apply] simp only"):
                    parts = [line.strip()[len("[apply] "):]]
                    for cont in b[i + 1:]:
                        if cont.startswith("    ") and not cont.strip().startswith("["):
                            parts.append(cont.strip())
                        else:
                            break
                    sugg = " ".join(parts)
                    break
            if sugg is None:
                if (ln, col) not in sites[f]:
                    sites[f][(ln, col)] = None
                    skipped.append(f"{f}:{ln}:{col}: no simp only suggestion for '{quoted}'")
                continue
            sites[f][(ln, col)] = (ln, col, quoted, sugg)
    done = 0
    for f, items in sorted(sites.items()):
        path = ROOT / f
        lines = path.read_text().split("\n")
        todo = [v for v in items.values() if v is not None]
        if not todo:
            continue
        for ln, col, quoted, sugg in sorted(todo, reverse=True):
            text = lines[ln - 1]
            if text[col:col + len(quoted)] == quoted:
                lines[ln - 1] = text[:col] + sugg + text[col + len(quoted):]
                done += 1
            else:
                skipped.append(f"{f}:{ln}:{col}: quoted text not found verbatim: '{quoted}'")
        if not dry:
            path.write_text("\n".join(lines))
    for s in skipped:
        print("skipped", s)
    print(f"rewrote {done} site(s) in {len(sites)} file(s); skipped {len(skipped)}")


if __name__ == "__main__":
    main(sys.argv[1:])
