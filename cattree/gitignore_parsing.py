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

    original_pattern = pattern
    
    # Check if pattern ends with / (directory only)
    is_dir_only = pattern.endswith("/")
    if is_dir_only:
        pattern = pattern.rstrip("/")
    
    # Check if pattern starts with / (root-relative)
    is_root_relative = pattern.startswith("/")
    if is_root_relative:
        pattern = pattern.lstrip("/")
    
    # Escape special regex characters before processing wildcards
    pattern = re.escape(pattern)
    
    # Convert .gitignore wildcards to regex equivalents
    pattern = pattern.replace(r"\*\*", "DOUBLESTAR")  # Placeholder
    pattern = pattern.replace(r"\*", "[^/]*")  # * matches anything except /
    pattern = pattern.replace(r"\?", "[^/]")  # ? matches single char except /
    pattern = pattern.replace("DOUBLESTAR", ".*")  # ** matches anything including /
    
    # Build the final regex
    if is_root_relative:
        # Pattern like /build/ or /file.txt - match from root
        if is_dir_only:
            return f"^{pattern}(/.*)?$"
        else:
            return f"^{pattern}$"
    else:
        # Pattern like build/ or *.pyc - match anywhere in the tree
        if is_dir_only:
            # Match directory name anywhere and everything inside it
            return f"(^|/){pattern}(/.*)?$"
        else:
            # Match file/directory name anywhere
            return f"(^|/){pattern}$"


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
