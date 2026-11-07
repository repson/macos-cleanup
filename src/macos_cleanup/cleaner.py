#!/usr/bin/env python3
"""
Conservative cleanup of user cache and log files on macOS.

For safety, this script runs in simulation mode by default.
It only removes content inside explicitly allowed paths and
never attempts to remove system directories.

Targets are divided into two tiers:
    Level 1 (auto):  self-regenerating caches — always cleaned.
    Level 2 (confirm): requires per-target y/N confirmation.

Usage:
    uv run macos-cleanup                   # dry-run (show all)
    uv run macos-cleanup --execute         # clean with confirmations
    uv run macos-cleanup --execute --yes   # auto-confirm everything
"""

from __future__ import annotations

import argparse
import errno
import glob
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


# ═══════════════════════════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════════════════════════

@dataclass
class CleanupStats:
    files_deleted: int = 0
    dirs_deleted: int = 0
    bytes_deleted: int = 0
    bytes_would_delete: int = 0
    target_bytes_would_delete: Dict[str, int] = field(default_factory=dict)
    errors: int = 0


# ═══════════════════════════════════════════════════════════════
# Path constants
# ═══════════════════════════════════════════════════════════════

HOME = Path.home().resolve()
TMPDIR = Path(os.environ.get("TMPDIR", "/tmp")).resolve()


# ═══════════════════════════════════════════════════════════════
# Level 1 — auto-cleaned targets (self-regenerating, zero risk)
# ═══════════════════════════════════════════════════════════════

AUTO_TARGETS: List[Path] = [
    # Core user caches & logs
    HOME / "Library" / "Caches",
    HOME / "Library" / "Logs",
    HOME / "Library" / "Application Support" / "CrashReporter",
    HOME / "Library" / "Saved Application State",
    # Developer & package-manager download caches
    HOME / ".cache",
    HOME / ".npm",
    HOME / ".gradle" / "caches",
    HOME / "go" / "pkg" / "mod" / "cache",
    HOME / ".bun" / "install" / "cache",
    HOME / ".cargo" / "registry" / "cache",
    HOME / ".cargo" / "registry" / "src",
    # Xcode & iOS Simulator
    HOME / "Library" / "Developer" / "Xcode" / "DerivedData",
    HOME / "Library" / "Developer" / "Xcode" / "iOS DeviceSupport",
    HOME / "Library" / "Developer" / "CoreSimulator" / "Caches",
    # Temp directories (Unix semantics: unlinking open files is safe)
    TMPDIR,
    Path("/private/var/tmp"),
]

# Sandbox container caches — expanded at runtime via glob
CONTAINER_CACHE_GLOBS: List[str] = [
    str(HOME / "Library" / "Containers" / "*" / "Data" / "Library" / "Caches"),
    str(HOME / "Library" / "Group Containers" / "*" / "Library" / "Caches"),
]


# ═══════════════════════════════════════════════════════════════
# Level 2 — targets requiring per-target y/N confirmation
# ═══════════════════════════════════════════════════════════════

CONFIRM_TARGETS: List[Path] = [
    HOME / ".Trash",
]

# Glob for "Install macOS" app bundles discovered in /Applications
INSTALL_MACOS_GLOB: str = "/Applications/Install macOS*.app"

# Docker VM data — reported for info, not auto-deleted
DOCKER_VM_PATH: Path = (
    HOME / "Library" / "Containers" / "com.docker.docker" / "Data" / "vms"
)


# ═══════════════════════════════════════════════════════════════
# Utility helpers
# ═══════════════════════════════════════════════════════════════

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


def expand_container_caches() -> List[Path]:
    """Expand glob patterns for sandbox container caches."""
    result: List[Path] = []
    seen: set[str] = set()
    for pattern in CONTAINER_CACHE_GLOBS:
        for path_str in sorted(glob.glob(pattern)):
            p = Path(path_str)
            key = str(p.resolve())
            if key not in seen and p.is_dir():
                seen.add(key)
                result.append(p)
    return result


def find_install_macos_apps() -> List[Path]:
    """Find 'Install macOS *.app' bundles in /Applications."""
    return [
        Path(p) for p in sorted(glob.glob(INSTALL_MACOS_GLOB))
        if Path(p).is_dir()
    ]


def estimate_target_contents(target: Path) -> int:
    """Estimate the total size of a target directory's contents."""
    if not target.exists():
        return 0
    if not target.is_dir() and not target.is_symlink():
        return 0
    if target.is_symlink() or target.is_file():
        try:
            return target.lstat().st_size
        except OSError:
            return 0
    try:
        return sum(estimate_size(item) for item in target.iterdir())
    except PermissionError:
        return 0
    except OSError:
        return 0


def ask_confirm(prompt: str) -> bool:
    """Prompt for y/N confirmation. Returns True on 'y' or 'yes'."""
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ("y", "yes")


# ═══════════════════════════════════════════════════════════════
# Deletion (unchanged logic from original)
# ═══════════════════════════════════════════════════════════════

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
    except PermissionError:
        # macOS sandbox blocks access to many system container Caches dirs
        print(f"[INFO] Permission denied (sandbox), skipping: {target}")
        return
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


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

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
        help="Perform real deletion. Without this flag, only shows what would be removed.",
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Auto-confirm all Level 2 targets (skip per-target prompts).",
    )
    return parser.parse_args()


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main() -> int:
    args = parse_args()
    execute = args.execute
    auto_yes = args.yes

    mode = "REAL EXECUTION" if execute else "SIMULATION (DRY-RUN)"
    print(f"Mode: {mode}")

    # ── Resolve targets ──────────────────────────────────────────
    auto_targets: List[Path] = list(AUTO_TARGETS)
    auto_targets.extend(expand_container_caches())

    confirm_targets: List[Path] = list(CONFIRM_TARGETS)
    install_apps = find_install_macos_apps()
    confirm_targets.extend(install_apps)

    # Deduplicate across both tiers (keep auto priority over confirm)
    seen: set[str] = set()
    deduped_auto: List[Path] = []
    for t in auto_targets:
        key = str(t.resolve())
        if key not in seen:
            seen.add(key)
            deduped_auto.append(t)
    auto_targets = deduped_auto

    deduped_confirm: List[Path] = []
    for t in confirm_targets:
        key = str(t.resolve())
        if key not in seen:
            seen.add(key)
            deduped_confirm.append(t)
    confirm_targets = deduped_confirm

    # ── Phase 1: estimate & report all targets ───────────────────
    print("\n── Level 1 (auto-clean) ──")
    auto_sizes: Dict[str, int] = {}
    total_auto = 0
    for target in auto_targets:
        size = estimate_target_contents(target)
        key = str(target)
        auto_sizes[key] = size
        total_auto += size
        if size > 0:
            print(f"  {target}  →  {human_size(size)}")

    if total_auto == 0:
        print("  (nothing found)")

    print("\n── Level 2 (needs confirmation) ──")
    confirm_sizes: Dict[str, int] = {}
    total_confirm = 0
    for target in confirm_targets:
        size = estimate_target_contents(target)
        key = str(target)
        confirm_sizes[key] = size
        total_confirm += size
        if size > 0:
            print(f"  {target}  →  {human_size(size)}")

    if total_confirm == 0:
        print("  (nothing found)")

    # Docker VM — report size, suggest official prune command
    if DOCKER_VM_PATH.exists():
        vm_size = estimate_size(DOCKER_VM_PATH)
        if vm_size > 0:
            print(f"\n[DOCKER] VM data: {DOCKER_VM_PATH}  →  {human_size(vm_size)}")
            print("  → To reclaim space safely, run:  docker system prune -a --volumes")

    grand_total = total_auto + total_confirm
    print(f"\n── Totals ──")
    print(f"  Level 1 (auto):    {human_size(total_auto)}")
    print(f"  Level 2 (confirm): {human_size(total_confirm)}")
    print(f"  Combined:           {human_size(grand_total)}")

    if not execute:
        print("\nNothing was deleted. Add --execute to perform real deletion.")
        return 0

    if grand_total == 0:
        print("\nNothing to delete — all targets are already empty.")
        return 0

    # ── Phase 2: execute ─────────────────────────────────────────
    stats = CleanupStats()

    # Auto-clean Level 1
    if auto_targets:
        print("\n━━━ Cleaning Level 1 (auto) ━━━")
        for target in auto_targets:
            cleanup_target_contents(target, execute=True, stats=stats)

    # Prompt for Level 2
    if confirm_targets:
        print("\n━━━ Level 2 confirmations ━━━")
        for target in confirm_targets:
            key = str(target)
            sz = confirm_sizes.get(key, 0)
            if sz == 0 and not target.exists():
                print(f"[INFO] Not found, skipping: {target}")
                continue

            label = f"  Clean {target} ({human_size(sz)})?"
            if auto_yes:
                print(f"{label} [y/N]: y (--yes)")
                cleanup_target_contents(target, execute=True, stats=stats)
            elif ask_confirm(label):
                cleanup_target_contents(target, execute=True, stats=stats)
            else:
                print(f"  [SKIP] {target}")

    # ── Final summary ────────────────────────────────────────────
    print("\nSummary:")
    print(f"  Files/symlinks removed: {stats.files_deleted}")
    print(f"  Directories removed:    {stats.dirs_deleted}")
    print(f"  Approx space freed:     {human_size(stats.bytes_deleted)}")
    print(f"  Errors:                 {stats.errors}")

    if stats.target_bytes_would_delete:
        print("  Per-target breakdown:")
        for target_name, total in sorted(stats.target_bytes_would_delete.items()):
            print(f"    - {target_name}: {human_size(total)}")

    return 0 if stats.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())