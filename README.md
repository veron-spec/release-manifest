# Release Manifest

Release Manifest creates a deterministic JSON inventory of a directory. Each file is recorded with its relative path, byte size, and SHA-256 digest so a release can be checked after copying, uploading, or archiving.

## Usage

```bash
python release_manifest.py dist
python release_manifest.py dist --verify
python -m unittest discover -v
```

The default output is `release-manifest.json`. The tool ignores that manifest while building and checking, sorts paths for reproducible output, and never follows directories as data. Exit codes are `0` for success, `1` for verification findings, and `2` for invalid input or a malformed manifest.

## Why use it?

A filename list cannot show whether a file changed. A checksum provides a compact fingerprint that can be compared later without storing the original content. The JSON format stays readable for humans and easy for CI to parse.

The project uses only Python's standard library and performs all work locally. It does not upload file contents or contact a network service.

## License

MIT
