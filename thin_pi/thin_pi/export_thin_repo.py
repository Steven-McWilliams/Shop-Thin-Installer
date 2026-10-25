#!/usr/bin/env python3
"""
Export a thin-only working tree (for publishing to a separate public repo).

This copies only the files listed in `thin_pi/thin_repo_manifest.txt` into an
output directory, preserving paths.

Usage:
  python3 thin_pi/export_thin_repo.py --out dist/qr-system-thin
  python3 thin_pi/export_thin_repo.py --out ../QR-system-thin
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def read_manifest(repo_root: Path) -> list[str]:
    manifest = repo_root / "thin_pi" / "thin_repo_manifest.txt"
    lines = []
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        lines.append(s)
    return lines


def _rm_tree(path: Path) -> None:
    """Remove a file/dir tree (best-effort on Windows locked/readonly files)."""
    def _onerror(func, p, exc_info):
        try:
            os.chmod(p, 0o777)
            func(p)
        except Exception:
            pass

    if path.is_dir():
        shutil.rmtree(path, onerror=_onerror)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def clean_out_dir_preserve_git(out_dir: Path) -> None:
    """
    Clean output directory but preserve an existing .git directory.

    This allows `dist/QR-system-thin` to be a real repo you can keep pushing,
    while regenerating its working tree from the manifest.
    """
    if not out_dir.exists():
        return
    for child in out_dir.iterdir():
        if child.name == ".git":
            continue
        _rm_tree(child)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export thin-only repo tree based on manifest.")
    ap.add_argument("--out", required=True, help="Output directory for the thin repo tree.")
    ap.add_argument("--clean", action="store_true", help="Delete output directory first if it exists.")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    out_dir = Path(args.out).expanduser().resolve()

    if args.clean and out_dir.exists():
        # If out_dir is already a git repo, preserve .git so we can keep history/remotes.
        if (out_dir / ".git").exists():
            clean_out_dir_preserve_git(out_dir)
        else:
            _rm_tree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = read_manifest(repo_root)
    missing = []

    for rel in paths:
        src = (repo_root / rel).resolve()
        dst = (out_dir / rel)
        if not src.exists():
            missing.append(rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            # Manifest should list files; but be tolerant.
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    # Add a minimal README if not present (thin repo should be self-explanatory)
    readme = out_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# QR-system Thin\n\n"
            "This repository contains only the files required to run the Innosaw Thin Pi image.\n"
            "See `thin_pi/README.md`.\n",
            encoding="utf-8",
        )

    if missing:
        print("WARNING: missing paths from manifest:")
        for p in missing:
            print(f"- {p}")
        return 2

    print(f"Exported thin tree to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


