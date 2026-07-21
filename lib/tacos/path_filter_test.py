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

    def test_disabled_message_custom(self, tmp_path: OSPath) -> None:
        pf = PathFilter(allowed=frozenset())
        slice_dir = tmp_path / "terraform" / "slice-0"
        slice_dir.mkdir(parents=True)
        (slice_dir / ".tacos-disabled").write_text("Managed by Spacelift now.")
        assert pf.disabled_message(str(slice_dir)) == "Managed by Spacelift now."

    def test_disabled_message_default(self, tmp_path: OSPath) -> None:
        pf = PathFilter(allowed=frozenset())
        slice_dir = tmp_path / "terraform" / "slice-0"
        slice_dir.mkdir(parents=True)
        (slice_dir / ".tacos-disabled").touch()
        assert pf.disabled_message(str(slice_dir)) == "This slice has been disabled in TACOS-GHA."

    def test_disabled_message_from_parent(self, tmp_path: OSPath) -> None:
        pf = PathFilter(allowed=frozenset())
        parent = tmp_path / "terraform"
        parent.mkdir(parents=True)
        (parent / ".tacos-disabled").write_text("Entire subtree migrated.")
        slice_dir = parent / "slice-0"
        slice_dir.mkdir()
        assert pf.disabled_message(str(slice_dir)) == "Entire subtree migrated."

    def test_symlink_sentinel_ignored_on_disk(self, tmp_path: OSPath) -> None:
        pf = PathFilter(allowed=frozenset())
        slice_dir = tmp_path / "terraform" / "slice-0"
        slice_dir.mkdir(parents=True)
        target = tmp_path / "secret"
        target.write_text("token=s3cret")
        (slice_dir / ".tacos-disabled").symlink_to(target)
        assert not pf._is_disabled_from_disk(str(slice_dir))

    def test_symlink_sentinel_message_returns_default(self, tmp_path: OSPath) -> None:
        pf = PathFilter(allowed=frozenset())
        slice_dir = tmp_path / "terraform" / "slice-0"
        slice_dir.mkdir(parents=True)
        target = tmp_path / "secret"
        target.write_text("token=s3cret")
        (slice_dir / ".tacos-disabled").symlink_to(target)
        assert pf.disabled_message(str(slice_dir)) == "This slice has been disabled in TACOS-GHA."


class TestPathFilterAllowlist:
    def test_empty_allows_all(self) -> None:
        pf = PathFilter(allowed=frozenset())
        assert pf.match("anything/at/all")

    def test_pattern_match(self) -> None:
        pf = PathFilter(allowed=frozenset({"terraform/*"}))
        assert pf.match("terraform/slice-0")
        assert not pf.match("other/slice-0")
