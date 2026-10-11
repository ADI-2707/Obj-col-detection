import re
from pathlib import Path

import pytest

import mill_motion
from scripts.bump_version import bump_version, compute_next_version, parse_semver


class TestVersionAttributes:
    def test_version_is_non_empty_string(self):
        assert isinstance(mill_motion.__version__, str)
        assert len(mill_motion.__version__) > 0

    def test_version_format_is_semver(self):
        assert re.match(r"^\d+\.\d+\.\d+$", mill_motion.__version__)

    def test_pyproject_version_matches_init_version(self):
        pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        assert match is not None
        assert match.group(1) == mill_motion.__version__


class TestSemverComputation:
    def test_parse_semver_valid(self):
        assert parse_semver("1.0.0") == (1, 0, 0)
        assert parse_semver("2.14.3") == (2, 14, 3)

    def test_parse_semver_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_semver("1.0")

    def test_compute_patch_bump(self):
        assert compute_next_version("1.0.0", "patch") == "1.0.1"

    def test_compute_minor_bump(self):
        assert compute_next_version("1.0.0", "minor") == "1.1.0"
        assert compute_next_version("1.2.5", "minor") == "1.3.0"

    def test_compute_major_bump(self):
        assert compute_next_version("1.0.0", "major") == "2.0.0"
        assert compute_next_version("1.4.9", "major") == "2.0.0"

    def test_compute_unknown_bump_raises(self):
        with pytest.raises(ValueError):
            compute_next_version("1.0.0", "unknown")


class TestBumpVersionExecution:
    def test_bump_version_in_temp_directory(self, tmp_path):
        pkg_dir = tmp_path / "mill_motion"
        pkg_dir.mkdir()
        init_file = pkg_dir / "__init__.py"
        pyproject_file = tmp_path / "pyproject.toml"

        init_file.write_text('__version__ = "1.0.0"\n', encoding="utf-8")
        pyproject_file.write_text(
            '[project]\nname = "mill-motion"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )

        new_ver = bump_version("patch", repo_root=tmp_path)
        assert new_ver == "1.0.1"
        assert '__version__ = "1.0.1"' in init_file.read_text(encoding="utf-8")
        assert 'version = "1.0.1"' in pyproject_file.read_text(encoding="utf-8")

        new_minor = bump_version("minor", repo_root=tmp_path)
        assert new_minor == "1.1.0"
        assert '__version__ = "1.1.0"' in init_file.read_text(encoding="utf-8")
        assert 'version = "1.1.0"' in pyproject_file.read_text(encoding="utf-8")
