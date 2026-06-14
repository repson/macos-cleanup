# macOS Cleanup Tool

Conservative cleanup of user cache and log files on macOS.

## Features

- **Safe by default**: Runs in simulation mode (dry-run) unless explicitly told otherwise
- **Limited scope**: Only cleans specific user directories (`~/Library/Caches`, `~/Library/Logs`, `~/Library/Application Support/CrashReporter`)
- **No system access**: Never touches system directories
- **Path validation**: Ensures all operations stay within allowed paths
- **Symlink protection**: Never follows symlinks outside allowed areas

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
# Simulation mode (default) - shows what would be removed
uv run macos-cleanup

# Real execution - actually removes files
uv run macos-cleanup --execute
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

MIT License - see [LICENSE](LICENSE) for details.
