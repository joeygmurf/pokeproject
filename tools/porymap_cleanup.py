#!/usr/bin/env python3
"""Repair and de-noise the JSON files Porymap rewrites.

    python3 tools/porymap_cleanup.py            # report only
    python3 tools/porymap_cleanup.py --apply    # fix in place

Porymap runs on Windows and writes into the WSL filesystem over the
\\\\wsl.localhost\\ share, which can leave a write partially flushed at a page
boundary. The observed damage is a single byte near the 8 KB mark - a "}," that
loses its comma - which makes the file unparseable and fails the build with an
opaque JSONPROC_ERROR.

Porymap also rewrites files it has not meaningfully changed, reordering keys and
producing thousands of lines of diff noise.

For each tracked .json that differs from HEAD this script decides:

  CORRUPT          -> repair the known pattern; restore from HEAD if that fails
  FORMATTING ONLY  -> restore from HEAD (parses, but identical content)
  REAL CHANGE      -> leave alone

Run it after any Porymap session, before building.
"""
import argparse
import json
import re
import subprocess
import sys


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def repair(text):
    """Re-insert a comma lost between two array elements."""
    return re.sub(r"\}\n\s*\n(\s*\{)", r"},\n\1", text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes instead of reporting")
    ap.add_argument("--repair-only", action="store_true",
                    help="only repair corrupt files; never restore formatting-only ones. "
                         "Safe to run from the Makefile, where discarding files would surprise.")
    args = ap.parse_args()
    if args.repair_only:
        args.apply = True

    changed = [f for f in git("diff", "--name-only").split() if f.endswith(".json")]
    if not changed:
        print("no modified json files")
        return 0

    corrupt, noise, real, failed = [], [], [], []
    for f in changed:
        text = open(f, encoding="utf-8").read()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            fixed = repair(text)
            try:
                parsed = json.loads(fixed)
            except json.JSONDecodeError:
                failed.append(f)
                continue
            corrupt.append(f)
            if args.apply:
                open(f, "w", encoding="utf-8").write(fixed)
            text = fixed

        if args.repair_only:
            continue
        try:
            if json.loads(git("show", f"HEAD:{f}")) == parsed:
                noise.append(f)
                if args.apply:
                    subprocess.run(["git", "checkout", "--", f], check=True)
            else:
                real.append(f)
        except json.JSONDecodeError:
            real.append(f)

    verb = "repaired" if args.apply else "would repair"
    done = "restored" if args.apply else "would restore"
    for f in corrupt: print(f"  CORRUPT         {verb}: {f}")
    for f in noise:   print(f"  formatting only {done}: {f}")
    for f in real:    print(f"  REAL CHANGE     kept:     {f}")
    for f in failed:  print(f"  UNRECOVERABLE   needs a manual look: {f}")

    if not args.apply and (corrupt or noise):
        print("\nre-run with --apply to make these changes")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
