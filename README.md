# macOS Cleanup Tool

Conservative cleanup of user cache and log files on macOS.

## Features

- **Safe by default**: runs in simulation mode (dry-run) unless `--execute` is passed
- **Two-tier system**:
  - **Level 1 (auto-clean)**: self-regenerating caches — cleaned automatically
  - **Level 2 (confirm)**: prompts `y/N` before each target (or use `--yes` to skip)
- **Broad coverage**: user caches, dev tool caches (npm, Gradle, Go, Rust, Bun), Xcode derived data, iOS Simulator temp files, sandbox container caches, and more
- **Limited scope**: only cleans explicitly allowed user directories — never touches system files
- **Path validation**: ensures all operations stay within allowed paths
- **Symlink protection**: never follows symlinks outside allowed areas
- **Docker awareness**: reports Docker VM disk usage and suggests the safe `docker system prune` command instead of deleting raw VM data

## Targets

### Level 1 — Automatic (self-regenerating, zero risk)

| Target | What it is |
|---|---|
| `~/Library/Caches` | User application caches |
| `~/Library/Logs` | User application logs |
| `~/Library/Application Support/CrashReporter` | Crash reports |
| `~/Library/Saved Application State` | Window restore state |
| `~/.cache` | Dev-tool caches (uv, pip, huggingface, etc.) |
| `~/.npm` | npm package cache |
| `~/.gradle/caches` | Gradle download cache |
| `~/go/pkg/mod/cache` | Go module cache |
| `~/.bun/install/cache` | Bun package cache |
| `~/.cargo/registry/{cache,src}` | Rust crate cache |
| `~/Library/Developer/Xcode/DerivedData` | Xcode build artifacts |
| `~/Library/Developer/Xcode/iOS DeviceSupport` | iOS device symbols |
| `~/Library/Developer/CoreSimulator/Caches` | Simulator caches |
| `$TMPDIR` and `/private/var/tmp` | System temp files |
| `~/Library/Containers/*/Data/Library/Caches` | Sandbox app caches |
| `~/Library/Group Containers/*/Library/Caches` | Shared sandbox caches |

### Level 2 — Requires confirmation

| Target | What it is |
|---|---|
| `~/.Trash` | User Trash |
| `/Applications/Install macOS*.app` | Old macOS installers |

### Reported but never deleted

Docker VM data (`~/Library/Containers/com.docker.docker/Data/vms`) is shown with a suggestion to run `docker system prune -a --volumes` instead.

## Requirements

- macOS
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended)

## Installation

```bash
git clone https://github.com/yourusername/macos-cleanup.git
cd macos-cleanup
uv sync
```

## Quick Start

```bash
# Simulation mode (default) — shows what would be removed, no changes made
uv run macos-cleanup

# Real execution — cleans Level 1, prompts y/N for each Level 2 target
uv run macos-cleanup --execute

# Real execution — auto-confirms everything (no prompts)
uv run macos-cleanup --execute --yes
```

## Documentation

See the [docs](docs/) directory for detailed documentation:

- [Installation](docs/installation.md)
- [Usage](docs/usage.md)
- [Configuration](docs/configuration.md)

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=macos_cleanup
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.