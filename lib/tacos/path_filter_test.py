from __future__ import annotations

from lib.types import OSPath
from lib.types import Path

from .path_filter import PathFilter


class TestPathFilterDisabled:
    def test_not_disabled_by_default(self) -> None:
        pf = PathFilter(allowed=frozenset())
        fs_files: frozenset[Path] = frozenset({
            Path("terraform/slice-0/main.tf"),
        })
        assert not pf.is_disabled("terraform/slice-0", fs_files)

    def test_disabled_by_sentinel_in_slice(self) -> None:
        pf = PathFilter(allowed=frozenset())
        fs_files: frozenset[Path] = frozenset({
            Path("terraform/slice-0/main.tf"),
            Path("terraform/slice-0/.tacos-disabled"),
        })
        assert pf.is_disabled("terraform/slice-0", fs_files)

    def test_disabled_by_sentinel_in_parent(self) -> None:
        pf = PathFilter(allowed=frozenset())
        fs_files: frozenset[Path] = frozenset({
            Path("terraform/slice-0/main.tf"),
            Path("terraform/.tacos-disabled"),
        })
        assert pf.is_disabled("terraform/slice-0", fs_files)

    def test_disabled_does_not_affect_sibling(self) -> None:
        pf = PathFilter(allowed=frozenset())
        fs_files: frozenset[Path] = frozenset({
            Path("terraform/slice-0/main.tf"),
            Path("terraform/slice-0/.tacos-disabled"),
            Path("terraform/slice-1/main.tf"),
        })
        assert pf.is_disabled("terraform/slice-0", fs_files)
        assert not pf.is_disabled("terraform/slice-1", fs_files)

    def test_match_ignores_disabled(self) -> None:
        """match() only checks the allowlist; disabled filtering is the caller's job."""
        pf = PathFilter(allowed=frozenset({"terraform/*"}))
        assert pf.match("terraform/slice-0")

    def test_disabled_at_disk(self, tmp_path: OSPath) -> None:
        pf = PathFilter(allowed=frozenset())
        slice_dir = tmp_path / "terraform" / "slice-0"
        slice_dir.mkdir(parents=True)
        (slice_dir / ".tacos-disabled").touch()
        assert pf._is_disabled_from_disk(str(slice_dir))

    def test_not_disabled_at_disk(self, tmp_path: OSPath) -> None:
        pf = PathFilter(allowed=frozenset())
        slice_dir = tmp_path / "terraform" / "slice-0"
        slice_dir.mkdir(parents=True)
        assert not pf._is_disabled_from_disk(str(slice_dir))


class TestPathFilterAllowlist:
    def test_empty_allows_all(self) -> None:
        pf = PathFilter(allowed=frozenset())
        assert pf.match("anything/at/all")

    def test_pattern_match(self) -> None:
        pf = PathFilter(allowed=frozenset({"terraform/*"}))
        assert pf.match("terraform/slice-0")
        assert not pf.match("other/slice-0")
