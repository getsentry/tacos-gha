from __future__ import annotations

from contextlib import chdir
from subprocess import run

from lib.types import OSPath
from lib.types import Path

from . import dependent_slices as D

PATHS = (
    OSPath("env/prod/slice-0/thing.tf"),
    OSPath("env/prod/terragrunt-prod.hcl"),
    OSPath("env/dev/slice-0/main.tf"),
    OSPath("env/dev/slice-0/module/thing.tf"),
    OSPath("module/foo/foo.tf"),
    OSPath("terragrunt-base.hcl"),
    OSPath("README.md"),
)
FS = D.FileSystem.from_paths(PATHS)


class TestFileSystem:
    def test_from_paths(self) -> None:
        fs = D.FileSystem.from_paths(
            (
                OSPath("d/e/e.txt"),
                OSPath("a/aa/aa.txt"),
                OSPath("a/b/c/c.txt"),
                OSPath("a/a.txt"),
            )
        )
        assert fs == D.FileSystem(
            files=frozenset(
                {
                    D.File(Path("d/e/e.txt")),
                    D.File(Path("a/aa/aa.txt")),
                    D.File(Path("a/b/c/c.txt")),
                    D.File(Path("a/a.txt")),
                }
            ),
            dirs=frozenset(
                {
                    D.Dir(Path("d/e")),
                    D.Dir(Path("a/aa")),
                    D.Dir(Path("a/b/c")),
                    D.Dir(Path("a")),
                }
            ),
        )

    def test_from_git(self, tmp_path: Path) -> None:
        with chdir(tmp_path):
            run(("git", "init"), check=True)
            run(("mkdir", "-p", "a/b/c", "a/aa", "d/e"), check=True)
            run(
                (
                    "touch",
                    "a/a.txt",
                    "a/aa/aa.txt",
                    "a/b/c/c.txt",
                    "d/e/e.txt",
                ),
                check=True,
            )
            run(("git", "add", "."), check=True)

            fs = D.FileSystem.from_git()

        assert fs == D.FileSystem(
            files=frozenset(
                {
                    D.File(Path("d/e/e.txt")),
                    D.File(Path("a/aa/aa.txt")),
                    D.File(Path("a/b/c/c.txt")),
                    D.File(Path("a/a.txt")),
                }
            ),
            dirs=frozenset(
                {
                    D.Dir(Path("d/e")),
                    D.Dir(Path("a/aa")),
                    D.Dir(Path("a/b/c")),
                    D.Dir(Path("a")),
                }
            ),
        )


class TestTFCategorized:
    def test_from_fs(self) -> None:
        categorized = D.TFCategorized.from_fs(FS)
        assert categorized == D.TFCategorized(
            slices=frozenset(
                {
                    D.TopLevelTFModule(
                        D.TFModule(D.Dir(Path("env/prod/slice-0")))
                    ),
                    D.TopLevelTFModule(
                        D.TFModule(D.Dir(Path("env/dev/slice-0")))
                    ),
                }
            ),
            shared_dirs=frozenset(
                {
                    D.TFSharedModulesDir(D.Dir(Path("module"))),
                    D.TFSharedModulesDir(
                        D.Dir(Path("env/dev/slice-0/module"))
                    ),
                }
            ),
            config_files=frozenset(
                {
                    D.TFConfigFile(D.File(Path("terragrunt-base.hcl"))),
                    D.TFConfigFile(
                        D.File(Path("env/prod/terragrunt-prod.hcl"))
                    ),
                }
            ),
        )

    def test_config_deps(self) -> None:
        categorized = D.TFCategorized.from_fs(FS)
        assert categorized.config_deps() == {
            Path("."): frozenset(
                {Path("env/prod/slice-0"), Path("env/dev/slice-0")}
            ),
            Path("env/dev/slice-0"): frozenset({Path("env/dev/slice-0")}),
            Path("env/prod"): frozenset({Path("env/prod/slice-0")}),
        }

    def test_from_modified(self) -> None:
        modified = D.TFCategorized.from_modified_files(
            (
                OSPath("env/prod/terragrunt-prod.hcl"),
                OSPath("env/dev/slice-0/module/thing.tf"),
            ),
            FS,
        )
        assert modified == D.TFCategorized(
            slices=frozenset(),
            shared_dirs=frozenset(
                {D.TFSharedModulesDir(D.Dir(Path("env/dev/slice-0/module")))}
            ),
            config_files=frozenset(
                {D.TFConfigFile(D.File(Path("env/prod/terragrunt-prod.hcl")))}
            ),
        )
        assert modified.config_dirs == frozenset(
            {
                D.TFConfigDir(D.Dir(Path("env/dev/slice-0"))),
                D.TFConfigDir(D.Dir(Path("env/prod"))),
            }
        )


class TestDependentSlices:
    def test_direct(self) -> None:
        slices = tuple(
            D.dependent_slices((OSPath("env/prod/slice-0/thing.tf"),), FS)
        )
        assert slices == (
            D.TopLevelTFModule(D.TFModule(D.Dir(Path("env/prod/slice-0")))),
        )

    def test_indirect_module(self) -> None:
        slices = tuple(
            D.dependent_slices(
                (OSPath("env/dev/slice-0/module/thing.tf"),), FS
            )
        )
        assert slices == (
            D.TopLevelTFModule(D.TFModule(D.Dir(Path("env/dev/slice-0")))),
        )

    def test_indirect_terragrunt(self) -> None:
        slices = tuple(
            D.dependent_slices((OSPath("env/prod/terragrunt-prod.hcl"),), FS)
        )
        assert slices == (
            D.TopLevelTFModule(D.TFModule(D.Dir(Path("env/prod/slice-0")))),
        )

    def test_unique(self) -> None:
        # we edited everything!
        slices = tuple(D.dependent_slices(PATHS, FS))
        assert slices == (
            D.TopLevelTFModule(D.TFModule(D.Dir(Path("env/dev/slice-0")))),
            D.TopLevelTFModule(D.TFModule(D.Dir(Path("env/prod/slice-0")))),
        )


class TestRegressions:
    """Real-world cases that (initially) weren't caught by unit-tests."""

    def test_root_is_slice(self) -> None:
        modified = {
            OSPath("proj/control/_import.tf"),
            OSPath("proj/service.hcl"),
        }
        all_paths = modified | {OSPath("terragrunt.hcl")}
        all = D.FileSystem.from_paths(all_paths)
        categorized = D.TFCategorized.from_fs(
            D.FileSystem.from_paths(modified), all
        )
        assert categorized == D.TFCategorized(
            slices=frozenset(
                {D.TopLevelTFModule(D.TFModule(D.Dir(Path("proj/control"))))}
            ),
            shared_dirs=frozenset(),
            config_files=frozenset(
                {D.TFConfigFile(D.File(Path("proj/service.hcl")))}
            ),
        )
        assert categorized.config_deps() == {
            D.Dir(Path("proj")): frozenset(
                {D.TopLevelTFModule(D.TFModule(D.Dir(Path("proj/control"))))}
            )
        }
        slices = tuple(D.dependent_slices(modified, all))
        assert slices == (
            D.TopLevelTFModule(D.TFModule(D.Dir(Path("proj/control")))),
        )
