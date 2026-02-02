# cattree

`tree` + `cat` = see your codebase structure and file contents in one command.

## Quick Start

```bash
# Install
uv pip install cattree

# Basic usage
cattree .

# Only specific files/dirs (great for LLMs!)
cattree . --only src/main.py --only tests/ --max-lines 20

# Respect .gitignore
cattree . --gitignore
```

## Why?

Perfect for quickly sharing code context with LLMs or reviewing project structure. One command, complete picture.

## Options

```bash
cattree PATH [OPTIONS]

  -o, --only          Specific files/dirs to include (maintains hierarchy)
  -g, --gitignore     Respect .gitignore patterns
  -i, --include       Regex pattern to include files/dirs
  -e, --exclude       Regex pattern to exclude files/dirs
  -m, --max-lines     Limit lines per file
  -c, --compact       Remove extra whitespace
```

## Examples

```bash
# Show only Python files from src/ and tests/
cattree . --only src/ --only tests/ -i ".*\.py$"

# Quick overview with truncated files
cattree . --gitignore --max-lines 10

# Generate context for an LLM discussion
cattree . -o backend/api.py -o models/user.py -m 50
```

## Default Filters

- **Allowed**: `.py`, `.md`, `.txt`, `.yml`, `.yaml`, `.json`, `.toml`, `.cpp`, `.h`, `.c`
- **Auto-excluded**: Hidden files (`.git`), `__pycache__`, binary files
