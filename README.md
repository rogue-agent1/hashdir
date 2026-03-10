# hashdir

Directory tree checksums for integrity verification.

One file. Zero deps. Verifies nothing changed.

## Usage

```bash
# Generate manifest
python3 hashdir.py hash /path/to/dir -o manifest.json

# Verify against manifest
python3 hashdir.py verify manifest.json

# Diff two manifests
python3 hashdir.py diff old.json new.json

# Exclude patterns
python3 hashdir.py hash . -x "*.pyc" -x ".git" -x "__pycache__"

# Use different algorithm
python3 hashdir.py hash . --algo md5
```

## Output

Hash generates a JSON manifest:
```json
{
  "root": "/path/to/dir",
  "algo": "sha256",
  "timestamp": "2026-03-10T13:28:10-0700",
  "files": {
    "src/main.py": "abc123...",
    "README.md": "def456..."
  }
}
```

Verify reports: `MISSING`, `CHANGED`, `ADDED`.
Diff reports: `+` added, `-` removed, `~` changed.

## Requirements

Python 3.8+. No dependencies.

## License

MIT
