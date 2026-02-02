import logging
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from cattree.gitignore_parsing import build_gitignore_regex

LOGGER = logging.getLogger(__name__)

ALLOWED_PATTERNS = [
    r".*\.py$",
    r".*\.md$",
    r".*\.txt$",
    r".*\.yml$",
    r".*\.yaml$",
    r".*\.json$",
    r".*\.toml$",
    r".*\.cpp$",
    r".*\.h$",
    r".*\.hpp$",
    r".*\.c$",
]
ALLOWED_REGEX = re.compile("|".join(ALLOWED_PATTERNS))

BLACKLISTED_PATTERNS = [
    r"^\.",
    r"__pycache__",
]
BLACKLISTED_REGEX = re.compile("|".join(BLACKLISTED_PATTERNS))


@dataclass(frozen=True)
class DirectoryEntry:
    path: Path
    depth: int


def _matches_pattern(
    path: Path,
    root_path: Path,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
) -> bool:
    """
    Check if a file or directory matches the include, exclude, and blacklist
    regex patterns.

    Args:
        path (Path): The path to check.
        root_path (Path): The root directory path for relative path calculation.
        include (Optional[str]): Regex pattern to include specific files
            or directories.
        exclude (Optional[str]): Regex pattern to exclude specific files
            or directories.

    Returns:
        bool: True if the path matches the patterns, False otherwise.
    """
    name = path.name
    # Get relative path from root for gitignore-style matching
    try:
        relative_path = str(path.relative_to(root_path))
    except ValueError:
        relative_path = name

    if path.is_file() and not ALLOWED_REGEX.match(name):
        return False
    if BLACKLISTED_REGEX.match(name):
        return False
    # Check against both name and relative path for gitignore compatibility
    if exclude and (re.search(exclude, name) or re.search(exclude, relative_path)):
        return False
    if include and not (re.search(include, name) or re.search(include, relative_path)):
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

    root_path = directory
    stack = deque([(directory, 0)])
    while stack:
        current_path, depth = stack.pop()

        if not _matches_pattern(
            current_path, root_path, include=include_pattern, exclude=exclude_pattern
        ):
            LOGGER.debug(f"Skipping {current_path}")
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
    compact_code: bool = False,
) -> str:
    """
    Read the content of a file up to a specified number of lines,
    with an option to remove whitespace.

    Args:
        path (Path): Path to the file.
        root_path (Path): Root path to use for relative paths.
        max_lines (Optional[int]): Maximum number of lines to read.
            If None, read the entire file.
        compact_code (bool): Whether to remove whitespace from the
            file content.

    Returns:
        str: The content of the file with '...' appended if truncated.
    """
    if not path.is_file():
        raise ValueError(f"The path {path} is not a valid file.")

    lines = [f"{path.relative_to(root_path)}:\n"]
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.readlines()
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to read file {path}") from e

    if max_lines is not None:
        content = content[:max_lines]
        if len(content) == max_lines:
            content.append("...")

    if compact_code:
        content = [re.sub(r"\s+", " ", line).strip() for line in content]

    lines.extend(content)

    return "".join(lines)


def _is_path_allowed(path: Path, only_paths: set[Path], root: Path) -> bool:
    """
    Check if a path should be included based on --only filter.

    Args:
        path (Path): Path to check.
        only_paths (set[Path]): Set of allowed paths from --only.
        root (Path): Root directory.

    Returns:
        bool: True if path is allowed, False otherwise.
    """
    path_resolved = path.resolve()

    # Check if path is explicitly in the set
    if path_resolved in only_paths:
        return True

    # Check if path is a descendant of any allowed directory
    for allowed in only_paths:
        if allowed.is_dir():
            try:
                path_resolved.relative_to(allowed)
                return True
            except ValueError:
                continue

    # Check if path is an ancestor of any allowed path
    for allowed in only_paths:
        try:
            allowed.relative_to(path_resolved)
            return True
        except ValueError:
            continue

    return False


def generate_cattree(
    directory: Path,
    only_paths: Optional[list[str]] = None,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
    gitignore: bool = False,
    max_lines: Optional[int] = None,
    compact_code: bool = False,
) -> str:
    """
    Generate a directory tree structure with optional file content
    and regex filtering.

    Args:
        directory (Path): Path to the root directory.
        only_paths (Optional[list[str]]): Specific paths to include (maintains hierarchy).
            Takes priority over include_pattern.
        include_pattern (Optional[str]): Regex pattern to include specific
            files or directories.
        exclude_pattern (Optional[str]): Regex pattern to exclude specific
            files or directories.
        gitignore (bool): Whether to use .gitignore files to filter paths.
        max_lines (Optional[int]): Maximum number of lines to read per file.
        compact_code (bool): Whether to remove whitespace from the
            file content.

    Returns:
        str: A string representing the directory tree structure.
    """
    # Build allowed paths set if --only is specified
    only_paths_set = None
    if only_paths:
        only_paths_set = {(directory / p).resolve() for p in only_paths}
        # --only takes priority over --include-pattern
        include_pattern = None

    if gitignore:
        gitignore_pattern = build_gitignore_regex(directory)
        exclude_pattern = f"{exclude_pattern or ''}|{gitignore_pattern}".strip("|")

    LOGGER.debug(f"Final exclude pattern: {exclude_pattern}")

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

        # If --only is specified, skip paths not allowed
        if only_paths_set and not _is_path_allowed(
            entry.path, only_paths_set, directory
        ):
            continue

        # Build the tree prefix based on depth
        prefix = "    " * (entry.depth - 1)
        connector = "├── " if entry.path.is_dir() else "└── "
        tree_structure.append(f"{prefix}{connector}{entry.path.name}")

        if entry.path.is_file():
            file_contents.append(
                format_file_content(
                    path=entry.path,
                    root_path=directory,
                    max_lines=max_lines,
                    compact_code=compact_code,
                )
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
        "--only",
        type=str,
        action="append",
        help="Specific files or directories to include (maintains hierarchy). Can be used multiple times.",
    )
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
    parser.add_argument(
        "--gitignore",
        action="store_true",
        help="Use .gitignore files to filter paths.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    _root_path = Path(args.path)
    try:
        print(
            generate_cattree(
                _root_path,
                only_paths=args.only,
                include_pattern=args.include_pattern,
                exclude_pattern=args.exclude_pattern,
                gitignore=args.gitignore,
            )
        )
    except ValueError as e:
        print(e)
