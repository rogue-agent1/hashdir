#!/usr/bin/env python3
"""hashdir - Directory tree checksums for integrity verification.

One file. Zero deps. Verifies nothing changed.

Usage:
  hashdir.py hash <path> [--algo sha256|md5|sha1] [--exclude PATTERN] [-o FILE]
  hashdir.py verify <manifest>
  hashdir.py diff <manifest1> <manifest2>
"""

import argparse
import hashlib
import json
import os
import sys
import fnmatch
import time
from pathlib import Path


def hash_file(path: str, algo: str = "sha256", buf_size: int = 65536) -> str:
    """Hash a single file."""
    h = hashlib.new(algo)
    try:
        with open(path, "rb") as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                h.update(data)
    except (PermissionError, OSError) as e:
        return f"ERROR:{e}"
    return h.hexdigest()


def walk_tree(root: str, excludes: list[str] | None = None) -> list[str]:
    """Walk directory tree, return sorted relative paths."""
    root = os.path.abspath(root)
    files = []
    excludes = excludes or []
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter excluded dirs in-place
        dirnames[:] = [
            d for d in dirnames
            if not any(fnmatch.fnmatch(d, p) for p in excludes)
        ]
        for fname in sorted(filenames):
            if any(fnmatch.fnmatch(fname, p) for p in excludes):
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)
            files.append(rel)
    return sorted(files)


def cmd_hash(args):
    """Generate manifest for a directory."""
    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 1

    excludes = args.exclude or []
    files = walk_tree(root, excludes)

    manifest = {
        "root": root,
        "algo": args.algo,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "files": {},
    }

    errors = 0
    for rel in files:
        full = os.path.join(root, rel)
        digest = hash_file(full, args.algo)
        if digest.startswith("ERROR:"):
            errors += 1
            print(f"  SKIP {rel}: {digest}", file=sys.stderr)
        else:
            manifest["files"][rel] = digest

    total = len(manifest["files"])
    print(f"Hashed {total} files ({errors} errors) with {args.algo}", file=sys.stderr)

    output = json.dumps(manifest, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output + "\n")
        print(f"Manifest written to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


def cmd_verify(args):
    """Verify files against a manifest."""
    with open(args.manifest) as f:
        manifest = json.load(f)

    root = manifest["root"]
    algo = manifest["algo"]
    expected = manifest["files"]

    if not os.path.isdir(root):
        print(f"Error: root {root} not found", file=sys.stderr)
        return 1

    ok = changed = missing = added = 0

    # Check expected files
    for rel, expected_hash in sorted(expected.items()):
        full = os.path.join(root, rel)
        if not os.path.exists(full):
            print(f"  MISSING  {rel}")
            missing += 1
            continue
        actual = hash_file(full, algo)
        if actual == expected_hash:
            ok += 1
        else:
            print(f"  CHANGED  {rel}")
            changed += 1

    # Check for new files
    current = set(walk_tree(root))
    for rel in sorted(current - set(expected.keys())):
        print(f"  ADDED    {rel}")
        added += 1

    total = ok + changed + missing + added
    print(f"\n{total} files: {ok} ok, {changed} changed, {missing} missing, {added} added", file=sys.stderr)
    return 1 if (changed or missing) else 0


def cmd_diff(args):
    """Diff two manifests."""
    with open(args.manifest1) as f:
        m1 = json.load(f)
    with open(args.manifest2) as f:
        m2 = json.load(f)

    f1 = set(m1["files"].keys())
    f2 = set(m2["files"].keys())

    removed = f1 - f2
    added = f2 - f1
    common = f1 & f2
    changed = {f for f in common if m1["files"][f] != m2["files"][f]}
    unchanged = common - changed

    for f in sorted(removed):
        print(f"  - {f}")
    for f in sorted(added):
        print(f"  + {f}")
    for f in sorted(changed):
        print(f"  ~ {f}")

    print(f"\n{len(unchanged)} unchanged, {len(changed)} changed, {len(added)} added, {len(removed)} removed", file=sys.stderr)
    return 1 if (changed or added or removed) else 0


def main():
    parser = argparse.ArgumentParser(description="Directory tree checksums")
    sub = parser.add_subparsers(dest="command")

    h = sub.add_parser("hash", help="Hash directory tree")
    h.add_argument("path", help="Directory to hash")
    h.add_argument("--algo", default="sha256", choices=["sha256", "md5", "sha1"])
    h.add_argument("--exclude", "-x", action="append", help="Glob pattern to exclude")
    h.add_argument("--output", "-o", help="Output manifest file")

    v = sub.add_parser("verify", help="Verify against manifest")
    v.add_argument("manifest", help="Manifest JSON file")

    d = sub.add_parser("diff", help="Diff two manifests")
    d.add_argument("manifest1")
    d.add_argument("manifest2")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    cmds = {"hash": cmd_hash, "verify": cmd_verify, "diff": cmd_diff}
    return cmds[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
