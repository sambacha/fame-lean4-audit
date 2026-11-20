#!/usr/bin/env python3
"""Rewrite each `show` that `linter.style.show` reported as goal-changing into `change` (rule R8).

Input: the per-file `.out` logs written by `scripts/lean_style_linters.sh`. Only the reported
line:column is touched, and only when the source text at that column is exactly the token `show`;
anything else is printed as skipped. The result must be rebuilt: `show` can also select a goal that
is not the main one, which `change` cannot, so a site that fails to build is reverted by hand.

    python3 show_to_change.py LINT_OUTDIR [--dry-run] [--only PREFIX]
"""
import collections, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
PAT = re.compile(r"^(\S+\.lean):(\d+):(\d+): warning: The `show` tactic should only be used")

def main(argv):
    outdir = pathlib.Path(argv[0]); dry = "--dry-run" in argv
    only = argv[argv.index("--only") + 1] if "--only" in argv else ""
    sites = collections.defaultdict(set)
    for p in outdir.glob("*.out"):
        for line in p.read_text(errors="replace").splitlines():
            m = PAT.match(line)
            if m and m.group(1).startswith(only):
                sites[m.group(1)].add((int(m.group(2)), int(m.group(3))))
    done = skipped = 0
    for f, locs in sorted(sites.items()):
        path = ROOT / f
        lines = path.read_text().split("\n")
        for ln, col in sorted(locs):
            text = lines[ln - 1]
            # Lean columns count code points; Python str indices do too.
            if text[col:col + 4] == "show" and (len(text) == col + 4 or not (text[col + 4].isalnum() or text[col + 4] in "_'!?")):
                lines[ln - 1] = text[:col] + "change" + text[col + 4:]
                done += 1
            else:
                print(f"skipped {f}:{ln}:{col}: {text.strip()[:80]}")
                skipped += 1
        if not dry:
            path.write_text("\n".join(lines))
    print(f"rewrote {done} site(s) in {len(sites)} file(s); skipped {skipped}")

if __name__ == "__main__":
    main(sys.argv[1:])
