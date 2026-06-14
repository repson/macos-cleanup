# Configuration

## Cleanup Targets

The cleanup targets are defined in `src/macos_cleanup/cleaner.py`:

```python
SAFE_TARGETS: list[Path] = [
    HOME / "Library" / "Caches",
    HOME / "Library" / "Logs",
    HOME / "Library" / "Application Support" / "CrashReporter",
]
```

### Modifying Targets

To add or remove cleanup targets, edit the `SAFE_TARGETS` list in `cleaner.py`.

**Warning**: Be very careful when modifying targets. The tool is designed to only clean directories where data loss is acceptable.

### Safety Rules

The tool enforces these safety rules regardless of configuration:

1. **Contents only**: Only removes contents inside target directories, never the target directory itself
2. **Path validation**: All paths are validated to ensure they stay within allowed targets
3. **No symlink following**: Symlinks pointing outside allowed paths are never followed
4. **No system directories**: System directories are never touched

## Adding New Cleanup Targets

Example: Adding a custom cache directory

```python
SAFE_TARGETS: list[Path] = [
    HOME / "Library" / "Caches",
    HOME / "Library" / "Logs",
    HOME / "Library" / "Application Support" / "CrashReporter",
    HOME / "Library" / "Application Support" / "MyApp" / "Cache",  # New target
]
```

## Excluding Paths

Currently, the tool does not support path exclusions. If you need to exclude specific paths, consider:

1. Removing the parent target from `SAFE_TARGETS`
2. Adding more specific subdirectory targets that exclude the path you want to keep
