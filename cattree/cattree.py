from typing import Optional, Iterator
from pathlib import Path
from collections import deque
import re

from pydantic import BaseModel


class DirectoryEntry(BaseModel):
    path: Path
    depth: int


def _matches_pattern(
    path: Path,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
) -> bool:
    name = path.name
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

    return "\n".join(tree_structure)


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
    root_path = Path(args.path)
    try:
        print(
            generate_cattree(
                root_path,
                include_pattern=args.include_pattern,
                exclude_pattern=args.exclude_pattern,
            )
        )
    except ValueError as e:
        print(e)
