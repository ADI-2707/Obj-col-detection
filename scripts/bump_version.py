import argparse
import re
import sys
from pathlib import Path


def parse_semver(version_str: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str.strip())
    if not match:
        raise ValueError(f"Invalid semver string: {version_str}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def compute_next_version(current_version: str, bump_type: str) -> str:
    major, minor, patch = parse_semver(current_version)
    bump = bump_type.lower().strip()
    if bump == "patch":
        patch += 1
    elif bump == "minor":
        minor += 1
        patch = 0
    elif bump == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")
    return f"{major}.{minor}.{patch}"


def bump_version(bump_type: str = "patch", repo_root: Path | None = None) -> str:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    init_file = repo_root / "mill_motion" / "__init__.py"
    pyproject_file = repo_root / "pyproject.toml"

    init_content = init_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_content)
    if not match:
        raise ValueError("Could not find __version__ in mill_motion/__init__.py")

    current_version = match.group(1)
    new_version = compute_next_version(current_version, bump_type)

    new_init_content = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        init_content,
    )
    init_file.write_text(new_init_content, encoding="utf-8")

    if pyproject_file.exists():
        pyproject_content = pyproject_file.read_text(encoding="utf-8")
        new_pyproject_content = re.sub(
            r'(version\s*=\s*["\'])[^"\']+(["\'])',
            rf"\g<1>{new_version}\g<2>",
            pyproject_content,
            count=1,
        )
        pyproject_file.write_text(new_pyproject_content, encoding="utf-8")

    return new_version


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Automated version bumper")
    parser.add_argument(
        "--type",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Semver bump type",
    )
    args = parser.parse_args(argv)

    try:
        new_ver = bump_version(args.type)
        print(new_ver)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
