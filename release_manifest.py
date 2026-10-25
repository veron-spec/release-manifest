#!/usr/bin/env python3
"""Create and verify deterministic SHA-256 manifests for release directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def digest(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_manifest(root: Path, manifest_name: str) -> dict:
    entries = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == manifest_name:
            continue
        entries.append({"path": path.relative_to(root).as_posix(), "sha256": digest(path), "bytes": path.stat().st_size})
    return {"format": 1, "algorithm": "sha256", "files": entries}


def load_manifest(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read manifest: {exc}") from exc
    if payload.get("format") != 1 or payload.get("algorithm") != "sha256" or not isinstance(payload.get("files"), list):
        raise ValueError("unsupported manifest format")
    return payload


def verify(root: Path, manifest_path: Path) -> list[str]:
    payload = load_manifest(manifest_path)
    expected = {item.get("path"): item for item in payload["files"] if isinstance(item, dict)}
    problems = []
    actual_paths = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path != manifest_path}
    for relative in sorted(set(expected) - actual_paths):
        problems.append(f"missing: {relative}")
    for relative in sorted(actual_paths - set(expected)):
        problems.append(f"unexpected: {relative}")
    for relative in sorted(actual_paths & set(expected)):
        path = root / relative
        item = expected[relative]
        if item.get("sha256") != digest(path):
            problems.append(f"changed: {relative}")
        if item.get("bytes") != path.stat().st_size:
            problems.append(f"size changed: {relative}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or verify a SHA-256 release manifest.")
    parser.add_argument("root", type=Path, help="directory containing release files")
    parser.add_argument("--manifest", default="release-manifest.json", help="manifest filename")
    parser.add_argument("--verify", action="store_true", help="verify files against the existing manifest")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    manifest_path = root / args.manifest
    if not root.is_dir():
        print(f"error: directory not found: {root}", file=sys.stderr)
        return 2
    if args.verify:
        try:
            problems = verify(root, manifest_path)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        for problem in problems:
            print(problem)
        print(f"Verified {len(problems)} problem(s) in {manifest_path.name}")
        return 1 if problems else 0
    manifest_path.write_text(json.dumps(build_manifest(root, args.manifest), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path} ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
