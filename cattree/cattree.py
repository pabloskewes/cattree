from typing import Optional
from pathlib import Path
import re


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


def generate_cattree(
    directory: Path,
    include_files: bool = True,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> str:
    """
    Generate a directory tree structure with optional file content and
    regex filtering.

    Args:
        directory (Path): Path to the root directory.
        include_files (bool): Whether to include file contents in the output.
        include_pattern (str): Regex pattern to include specific files
        or directories.
        exclude_pattern (str): Regex pattern to exclude specific files
        or directories.

    Returns:
        str: A string representing the directory tree structure.
    """

    def traverse_dir(path: Path, prefix: str = "") -> str:
        tree_structure = []
        entries = sorted(
            path.iterdir(),
            key=lambda p: (p.is_file(), p.name.lower()),
        )

        for i, entry in enumerate(entries):
            # Skip entries that don't match the regex patterns
            if not _matches_pattern(
                entry, include=include_pattern, exclude=exclude_pattern
            ):
                continue

            connector = "├── " if i < len(entries) - 1 else "└── "
            tree_structure.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir():
                sub_prefix = "│   " if i < len(entries) - 1 else "    "
                tree_structure.append(traverse_dir(entry, prefix + sub_prefix))
            elif include_files:
                try:
                    content = entry.read_text(errors="replace")
                    tree_structure.append(f"\n{prefix}    [Content of {entry.name}]\n")
                    tree_structure.append(f"{prefix}    {content[:200]}...\n")
                except Exception as e:
                    tree_structure.append(f"{prefix}    [Error reading file: {e}]\n")

        return "\n".join(tree_structure)

    if not directory.is_dir():
        raise ValueError(f"The path {directory} is not a valid directory.")

    return traverse_dir(directory)


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
        "--include-files",
        action="store_true",
        help="Include file contents in the output.",
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

    args = parser.parse_args()
    root_path = Path(args.path)
    try:
        print(
            generate_cattree(
                root_path,
                include_files=args.include_files,
                include_pattern=args.include_pattern,
                exclude_pattern=args.exclude_pattern,
            )
        )
    except ValueError as e:
        print(e)
