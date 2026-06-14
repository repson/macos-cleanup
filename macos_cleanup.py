#!/usr/bin/env python3
"""
Conservative cleanup of user cache and log files on macOS.

For safety, this script runs in simulation mode by default.
It only removes content inside explicitly allowed paths and
never attempts to remove system directories.

Usage:
    - Simulation (default):
      uv run safe_macos_cleanup.py
    - Real execution:
      uv run safe_macos_cleanup.py --execute
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class CleanupStats:
    files_deleted: int = 0
    dirs_deleted: int = 0
    bytes_deleted: int = 0
    bytes_would_delete: int = 0
    target_bytes_would_delete: Dict[str, int] = None
    errors: int = 0

    def __post_init__(self) -> None:
        if self.target_bytes_would_delete is None:
            self.target_bytes_would_delete = {}


HOME = Path.home().resolve()
SAFE_TARGETS: list[Path] = [
    HOME / "Library" / "Caches",
    HOME / "Library" / "Logs",
    HOME / "Library" / "Application Support" / "CrashReporter",
]


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{num_bytes} B"


def is_within(parent: Path, child: Path) -> bool:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    try:
        child_resolved.relative_to(parent_resolved)
        return True
    except ValueError:
        return False


def estimate_size(path: Path) -> int:
    if not path.exists() and not path.is_symlink():
        return 0
    try:
        if path.is_symlink() or path.is_file():
            return path.lstat().st_size
    except OSError:
        return 0

    total = 0
    for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
        root_path = Path(root)
        for name in files:
            fp = root_path / name
            try:
                total += fp.lstat().st_size
            except OSError:
                pass
        for name in dirs:
            dp = root_path / name
            try:
                if dp.is_symlink():
                    total += dp.lstat().st_size
            except OSError:
                pass
    return total


def delete_path(path: Path, execute: bool, stats: CleanupStats) -> None:
    size = estimate_size(path)
    stats.bytes_would_delete += size

    if not execute:
        print(f"[DRY-RUN] Would remove: {path} ({human_size(size)})")
        return

    try:
        if path.is_symlink() or path.is_file():
            path.unlink()
            stats.files_deleted += 1
            stats.bytes_deleted += size
            print(f"[OK] Removed file/symlink: {path}")
            return

        # Real directory deletion: bottom-up, never follow symlinks.
        for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
            root_path = Path(root)

            for name in files:
                fp = root_path / name
                try:
                    file_size = fp.lstat().st_size
                except OSError:
                    file_size = 0
                try:
                    fp.unlink()
                    stats.files_deleted += 1
                    stats.bytes_deleted += file_size
                except OSError as exc:
                    stats.errors += 1
                    print(f"[ERROR] Could not remove file {fp}: {exc}")

            for name in dirs:
                dp = root_path / name
                try:
                    if dp.is_symlink():
                        link_size = dp.lstat().st_size
                        dp.unlink()
                        stats.files_deleted += 1
                        stats.bytes_deleted += link_size
                    else:
                        dp.rmdir()
                        stats.dirs_deleted += 1
                except OSError as exc:
                    stats.errors += 1
                    print(f"[ERROR] Could not remove directory {dp}: {exc}")

        try:
            path.rmdir()
            stats.dirs_deleted += 1
        except OSError as exc:
            stats.errors += 1
            print(f"[ERROR] Could not remove root directory {path}: {exc}")

        print(f"[OK] Removed directory: {path}")

    except OSError as exc:
        stats.errors += 1
        print(f"[ERROR] Failed processing {path}: {exc}")


def cleanup_target_contents(target: Path, execute: bool, stats: CleanupStats) -> None:
    if not target.exists():
        print(f"[INFO] Not found, skipping: {target}")
        return

    if not target.is_dir():
        print(f"[WARN] Not a directory, skipping: {target}")
        return

    try:
        children = list(target.iterdir())
    except OSError as exc:
        stats.errors += 1
        print(f"[ERROR] Could not list {target}: {exc}")
        return

    target_total = sum(estimate_size(item) for item in children)
    stats.target_bytes_would_delete[str(target)] = target_total
    if not execute:
        print(f"\n[TARGET] {target} (would remove: {human_size(target_total)})")
    else:
        print(f"\n[TARGET] {target}")

    if not children:
        print("[INFO] Already empty.")
        return

    for item in children:
        # Critical guardrail: never operate outside the allowed target.
        if not is_within(target, item):
            stats.errors += 1
            print(f"[ERROR] Path outside target, skipping: {item}")
            continue
        delete_path(item, execute=execute, stats=stats)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safe cleanup of user cache/log files on macOS. "
            "Simulation only by default (dry-run)."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform real deletion. Without this flag, it only shows what it would remove.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    execute = args.execute

    mode = "REAL EXECUTION" if execute else "SIMULATION (DRY-RUN)"
    print(f"Mode: {mode}")
    print("Allowed paths:")
    for target in SAFE_TARGETS:
        print(f"  - {target}")

    stats = CleanupStats()
    for target in SAFE_TARGETS:
        cleanup_target_contents(target, execute=execute, stats=stats)

    print("\nSummary:")
    print(f"  Files/symlinks removed: {stats.files_deleted}")
    print(f"  Directories removed: {stats.dirs_deleted}")
    print(f"  Approx space freed: {human_size(stats.bytes_deleted)}")
    print(f"  Total estimated to remove: {human_size(stats.bytes_would_delete)}")
    print(f"  Errors: {stats.errors}")

    if stats.target_bytes_would_delete:
        print("  Per analyzed folder totals:")
        for target, total in stats.target_bytes_would_delete.items():
            print(f"    - {target}: {human_size(total)}")

    if not execute:
        print("\nNothing was deleted. Add --execute to perform real deletion.")

    return 0 if stats.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
