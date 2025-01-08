from typing import Optional, Iterator
from pathlib import Path
from collections import deque
import re

from pydantic import BaseModel

BLACKLISTED_PATTERNS = [
    r"^\.",
    r"__pycache__",
    r".*\.png",
    r".*\.jpg",
    r".*\.jpeg",
    r".*\.gif",
    r".*\.bmp",
    r".*\.tiff",
    r".*\.ico",
    r".*\.svg",
    r".*\.pdf",
    r".*\.db",
]
BLACKLISTED_REGEX = re.compile("|".join(BLACKLISTED_PATTERNS))


class DirectoryEntry(BaseModel):
    path: Path
    depth: int


def _matches_pattern(
    path: Path,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
) -> bool:
    """
    Check if a file or directory matches the include, exclude, and blacklist
    regex patterns.

    Args:
        path (Path): The path to check.
        include (Optional[str]): Regex pattern to include specific files
            or directories.
        exclude (Optional[str]): Regex pattern to exclude specific files
            or directories.

    Returns:
        bool: True if the path matches the patterns, False otherwise.
    """
    name = path.name

    if BLACKLISTED_REGEX.search(name):
        return False

    if exclude and re.search(exclude, name):
        return False

    if include and not re.search(include, name):
        return False

    return True


def traverse_directory_dfs(
    directory: Path,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> Iterator[DirectoryEntry]:
    """
    Traverse a directory in DFS order and yield DirectoryEntry objects.

    Args:
        directory (Path): The root directory to traverse.
        include_pattern (Optional[str]): Regex pattern to include specific
            files or directories.
        exclude_pattern (Optional[str]): Regex pattern to exclude specific
            files or directories.

    Yields:
        DirectoryEntry: Pydantic model with path and depth.
    """
    if not directory.is_dir():
        raise ValueError(f"The path {directory} is not a valid directory.")

    stack = deque([(directory, 0)])  # Using deque as a stack for clarity
    while stack:
        current_path, depth = stack.pop()

        if not _matches_pattern(
            current_path, include=include_pattern, exclude=exclude_pattern
        ):
            continue

        yield DirectoryEntry(path=current_path, depth=depth)

        if current_path.is_dir():
            entries = sorted(
                current_path.iterdir(),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
            for entry in reversed(entries):
                stack.append((entry, depth + 1))


def format_file_content(
    path: Path,
    root_path: Path,
    max_lines: Optional[int] = None,
) -> str:
    """
    Read the content of a file up to a specified number of lines.

    Args:
        path (Path): Path to the file.
        root_path (Path): Root path to use for relative paths.
        max_lines (Optional[int]): Maximum number of lines to read.
            If None, read the entire file.

    Returns:
        str: The content of the file with '...' appended if truncated.
    """
    if not path.is_file():
        raise ValueError(f"The path {path} is not a valid file.")

    lines = [f"{path.relative_to(root_path)}:\n"]
    try:
        with open(path, "r", encoding="utf-8") as file:
            for i, line in enumerate(file):
                if max_lines is not None and i >= max_lines:
                    lines.append("...")
                    break
                lines.append(line)
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to read file {path}") from e

    return "".join(lines)


def generate_cattree(
    directory: Path,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> str:
    """
    Generate a directory tree structure with optional file content
    and regex filtering.

    Args:
        directory (Path): Path to the root directory.
        include_pattern (Optional[str]): Regex pattern to include specific
            files or directories.
        exclude_pattern (Optional[str]): Regex pattern to exclude specific
            files or directories.

    Returns:
        str: A string representing the directory tree structure.
    """
    tree_structure: list[str] = [directory.name]
    file_contents: list[str] = [""]

    for entry in traverse_directory_dfs(
        directory,
        include_pattern=include_pattern,
        exclude_pattern=exclude_pattern,
    ):
        if entry.depth == 0:
            # Skip reprinting the root directory itself
            continue

        # Build the tree prefix based on depth
        prefix = "    " * (entry.depth - 1)
        connector = "├── " if entry.path.is_dir() else "└── "
        tree_structure.append(f"{prefix}{connector}{entry.path.name}")

        if entry.path.is_file():
            file_contents.append(
                format_file_content(path=entry.path, root_path=directory)
            )
        else:
            file_contents.append("")  # Empty line for directories

    formatted_directory_tree = "\n".join(tree_structure)
    formatted_file_contents = f"{'-' * 80}\n".join(
        (content for content in file_contents if content)
    )
    return f"{formatted_directory_tree}\n{formatted_file_contents}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Generate a directory tree with regex "
            "filtering and optional file contents."
        )
    )
    parser.add_argument("path", type=str, help="Path to the root directory.")
    parser.add_argument(
        "--include-pattern",
        type=str,
        help="Regex pattern to include specific files or directories.",
    )
    parser.add_argument(
        "--exclude-pattern",
        type=str,
        help="Regex pattern to exclude specific files or directories.",
    )

    args = parser.parse_args()
    _root_path = Path(args.path)
    try:
        print(
            generate_cattree(
                _root_path,
                include_pattern=args.include_pattern,
                exclude_pattern=args.exclude_pattern,
            )
        )
    except ValueError as e:
        print(e)
