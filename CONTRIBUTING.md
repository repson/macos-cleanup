# Contributing to macOS Cleanup Tool

Thank you for your interest in contributing to macOS Cleanup Tool! This document provides guidelines and information for contributors.

## Code of Conduct

Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

- Use the GitHub issue tracker
- Describe the bug clearly
- Include steps to reproduce
- Mention your macOS version and Python version

### Suggesting Features

- Use the GitHub issue tracker
- Describe the feature and its benefits
- Consider safety implications

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/macos-cleanup.git
   cd macos-cleanup
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests:
   ```bash
   pytest
   ```

## Code Style

- Follow PEP 8
- Use type hints
- Keep functions focused and small
- Add docstrings to functions and classes
- Maximum line length: 88 characters (Black formatter)

## Testing

- Write tests for new functionality
- Ensure all existing tests pass
- Aim for good test coverage
- Test both dry-run and execute modes

## Safety Considerations

- Never remove system directories
- Always validate paths
- Test thoroughly before submitting
- Consider edge cases and error handling

## Questions?

Feel free to open an issue for any questions about contributing.

Thank you for contributing!
