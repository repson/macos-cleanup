# Usage

## Basic Usage

### Simulation Mode (Default)

Shows what would be removed without actually deleting anything:

```bash
uv run macos-cleanup
```

### Real Execution

Actually removes files (use with caution):

```bash
uv run macos-cleanup --execute
```

## Command Line Options

| Option      | Description                                    |
|-------------|------------------------------------------------|
| `--execute` | Perform real deletion. Without this flag, only shows what would be removed. |

## Cleanup Targets

The tool cleans the following directories (contents only, never the directories themselves):

| Path | Description |
|------|-------------|
| `~/Library/Caches` | Application cache files |
| `~/Library/Logs` | Application log files |
| `~/Library/Application Support/CrashReporter` | Crash reports |

## Understanding the Output

### Simulation Mode

```
Mode: SIMULATION (DRY-RUN)
Allowed paths:
  - /Users/you/Library/Caches
  - /Users/you/Library/Logs
  - /Users/you/Library/Application Support/CrashReporter

[TARGET] /Users/you/Library/Caches (would remove: 1.23 GB)
[DRY-RUN] Would remove: /Users/you/Library/Caches/com.example.app (512.00 MB)
...

Summary:
  Files/symlinks removed: 0
  Directories removed: 0
  Approx space freed: 0.00 B
  Total estimated to remove: 1.23 GB
  Errors: 0

Nothing was deleted. Add --execute to perform real deletion.
```

### Real Execution Mode

```
Mode: REAL EXECUTION
...
[OK] Removed directory: /Users/you/Library/Caches/com.example.app
...

Summary:
  Files/symlinks removed: 1234
  Directories removed: 56
  Approx space freed: 1.23 GB
  ...
```

## Safety Recommendations

1. **Always run simulation first**: Review the output before using `--execute`
2. **Run as regular user**: Never run as root or with sudo
3. **Close applications**: Some apps may recreate cache files while running
4. **Keep backups**: Important data should be backed up regularly
