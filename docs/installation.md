# Installation

## Prerequisites

- **macOS**: This tool is designed specifically for macOS
- **Python 3.10+**: Required to run the cleanup script
- **uv** (recommended): Fast Python package manager

## Install uv

If you don't have uv installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Install from source

```bash
git clone https://github.com/yourusername/macos-cleanup.git
cd macos-cleanup
uv sync
```

## Verify installation

```bash
uv run macos-cleanup
```

This will run in simulation mode and show what would be cleaned up without actually removing anything.
