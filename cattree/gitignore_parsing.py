import re
from pathlib import Path
from typing import Optional


def _parse_gitignore(gitignore_path: Path) -> list[str]:
    """
    Parse a .gitignore file and return a list of patterns.

    Args:
        gitignore_path (Path): Path to the .gitignore file.

    Returns:
        List[str]: A list of patterns from the .gitignore file.
    """
    if not gitignore_path.exists():
        return []

    with gitignore_path.open("r", encoding="utf-8") as file:
        return [
            line.strip() for line in file if line.strip() and not line.startswith("#")
        ]


def _convert_gitignore_to_regex(pattern: str) -> Optional[str]:
    """
    Convert a single .gitignore pattern to a regex string.

    Args:
        pattern (str): A .gitignore pattern.

    Returns:
        Optional[str]: The equivalent regex pattern or None if the pattern is invalid.
    """
    # Ignore completely generic patterns like '*'
    if pattern in ["*", "**"]:
        return None

    # Handle special cases: `**` matches zero or more directories
    pattern = pattern.replace("**/", "(?:.*/)?")
    pattern = pattern.replace("**", ".*")  # ** also matches any sequence of characters

    # Escape special regex characters
    pattern = re.escape(pattern)

    # Convert .gitignore wildcards to regex equivalents
    pattern = pattern.replace(r"\*", ".*")  # Match zero or more characters
    pattern = pattern.replace(r"\?", ".")  # Match a single character

    if pattern.endswith(r"/"):
        # Match directories (trailing slash in .gitignore)
        return f"^{pattern}.*$"
    return f"^{pattern}$"


def build_gitignore_regex(directory: Path) -> str:
    """
    Build a single regex pattern from all .gitignore files in the directory tree.

    Args:
        directory (Path): Root directory to search for .gitignore files.

    Returns:
        str: A single regex pattern combining all .gitignore entries.
    """
    patterns = []

    for gitignore_file in directory.glob("**/.gitignore"):
        patterns.extend(_parse_gitignore(gitignore_file))

    regex_patterns = [
        regex for pattern in patterns if (regex := _convert_gitignore_to_regex(pattern))
    ]

    combined_regex = "|".join(regex_patterns)
    return combined_regex
