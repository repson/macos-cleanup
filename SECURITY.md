# macOS Cleanup Tool - Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **DO NOT** open a public issue
2. Email the maintainer directly
3. Include details about the vulnerability
4. Allow time for response before public disclosure

## Security Considerations

This tool is designed with safety in mind:

- **Read-only by default**: Only shows what would be removed
- **Limited scope**: Only cleans specific user directories
- **No system access**: Never touches system directories
- **Path validation**: Ensures operations stay within allowed paths
- **Symlink protection**: Never follows symlinks outside allowed areas

## Best Practices

- Always review dry-run output before using `--execute`
- Run as regular user, never as root
- Keep backups of important data
- Test in a safe environment first

## Security Features

- Conservative cleanup targets
- Path validation and sanitization
- No external network calls
- No data collection or telemetry
- Open source and auditable
