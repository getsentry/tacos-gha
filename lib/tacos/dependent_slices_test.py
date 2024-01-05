from contextlib import chdir
from subprocess import run

from . import dependent_slices as D

PATHS = (
    D.Path("env/prod/slice-0/thing.tf"),
    D.Path("env/prod/terragrunt-prod.hcl"),
    D.Path("env/dev/slice-0/main.tf"),
    D.Path("env/dev/slice-0/module/thing.tf"),
    D.Path("module/foo/foo.tf"),
    D.Path("terragrunt-base.hcl"),
    D.Path("README.md"),
)
FS = D.FileSystem.from_paths(PATHS)


class TestFileSystem:
    def test_from_paths(self):
        fs = D.FileSystem.from_paths(
            (
                D.Path("d/e/e.txt"),
                D.Path("a/aa/aa.txt"),
                D.Path("a/b/c/c.txt"),
                D.Path("a/a.txt"),
            )
        )
        assert fs == D.FileSystem(
            files=frozenset(
                {
                    D.File(D.PurePath("d/e/e.txt")),
                    D.File(D.PurePath("a/aa/aa.txt")),
                    D.File(D.PurePath("a/b/c/c.txt")),
                    D.File(D.PurePath("a/a.txt")),
                }
            ),
            dirs=frozenset(
                {
                    D.Dir(D.PurePath("d/e")),
                    D.Dir(D.PurePath("a/aa")),
                    D.Dir(D.PurePath("a/b/c")),
                    D.Dir(D.PurePath("a")),
                }
            ),
        )

    def test_from_git(self, tmp_path: D.PurePath):
        with chdir(tmp_path):
            run(("git", "init"), check=True)
            run(("mkdir", "-p", "a/b/c", "a/aa", "d/e"), check=True)
            run(
                ("touch", "a/a.txt", "a/aa/aa.txt", "a/b/c/c.txt", "d/e/e.txt"),
                check=True,
            )
            run(("git", "add", "."), check=True)

            fs = D.FileSystem.from_git()

        assert fs == D.FileSystem(
            files=frozenset(
                {
                    D.File(D.PurePath("d/e/e.txt")),
                    D.File(D.PurePath("a/aa/aa.txt")),
                    D.File(D.PurePath("a/b/c/c.txt")),
                    D.File(D.PurePath("a/a.txt")),
                }
            ),
            dirs=frozenset(
                {
                    D.Dir(D.PurePath("d/e")),
                    D.Dir(D.PurePath("a/aa")),
                    D.Dir(D.PurePath("a/b/c")),
                    D.Dir(D.PurePath("a")),
                }
            ),
        )


class TestTFCategorized:
    def test_from_fs(self):
        categorized = D.TFCategorized.from_fs(FS)
        assert categorized == D.TFCategorized(
            slices=frozenset(
                {
                    D.TopLevelTFModule(
                        D.TFModule(D.Dir(D.PurePath("env/prod/slice-0")))
                    ),
                    D.TopLevelTFModule(
                        D.TFModule(D.Dir(D.PurePath("env/dev/slice-0")))
                    ),
                }
            ),
            shared_dirs=frozenset(
                {
                    D.TFSharedModulesDir(D.Dir(D.PurePath("module"))),
                    D.TFSharedModulesDir(D.Dir(D.PurePath("env/dev/slice-0/module"))),
                }
            ),
            config_files=frozenset(
                {
                    D.TFConfigFile(D.File(D.PurePath("terragrunt-base.hcl"))),
                    D.TFConfigFile(D.File(D.PurePath("env/prod/terragrunt-prod.hcl"))),
                },
            ),
        )

    def test_config_deps(self):
        categorized = D.TFCategorized.from_fs(FS)
        assert categorized.config_deps() == {
            D.PurePath("."): frozenset(
                {
                    D.PurePath("env/prod/slice-0"),
                    D.PurePath("env/dev/slice-0"),
                }
            ),
            D.PurePath("env/dev/slice-0"): frozenset(
                {
                    D.PurePath("env/dev/slice-0"),
                }
            ),
            D.PurePath("env/prod"): frozenset({D.PurePath("env/prod/slice-0")}),
        }

    def test_from_modified(self):
        modified = D.TFCategorized.from_modified_files(
            (
                D.Path("env/prod/terragrunt-prod.hcl"),
                D.Path("env/dev/slice-0/module/thing.tf"),
            ),
            FS,
        )
        assert modified == D.TFCategorized(
            slices=frozenset(),
            shared_dirs=frozenset(
                {
                    D.TFSharedModulesDir(D.Dir(D.PurePath("env/dev/slice-0/module"))),
                }
            ),
            config_files=frozenset(
                {D.TFConfigFile(D.File(D.Path("env/prod/terragrunt-prod.hcl")))}
            ),
        )
        assert modified.config_dirs == frozenset(
            {D.Path("env/dev/slice-0"), D.Path("env/prod")}
        )


class TestDependentSlices:
    def test_direct(self):
        slices = tuple(
            D.dependent_slices(
                (D.Path("env/prod/slice-0/thing.tf"),),
                FS,
            )
        )
        assert slices == (
            D.Path(
                "env/prod/slice-0",
            ),
        )

    def test_indirect_module(self):
        slices = tuple(
            D.dependent_slices(
                (D.Path("env/dev/slice-0/module/thing.tf"),),
                FS,
            )
        )
        assert slices == (
            D.Path(
                "env/dev/slice-0",
            ),
        )

    def test_indirect_terragrunt(self):
        slices = tuple(
            D.dependent_slices(
                (D.Path("env/prod/terragrunt-prod.hcl"),),
                FS,
            )
        )
        assert slices == (
            D.Path(
                "env/prod/slice-0",
            ),
        )

    def test_unique(self):
        # we editted everything!
        slices = tuple(D.dependent_slices(PATHS, FS))
        assert slices == (
            D.Path("env/dev/slice-0"),
            D.Path(
                "env/prod/slice-0",
            ),
        )


class TestRegressions:
    """Real-world cases that (initially) weren't caught by unit-tests."""

    def test_root_is_slice(self):
        modified = {
            D.Path("proj/control/_import.tf"),
            D.Path("proj/service.hcl"),
        }
        all = modified | {D.Path("terragrunt.hcl")}
        all = D.FileSystem.from_paths(all)
        categorized = D.TFCategorized.from_fs(D.FileSystem.from_paths(modified), all)
        assert categorized == D.TFCategorized(
            slices=frozenset(
                {D.TopLevelTFModule(D.TFModule(D.Dir(D.Path("proj/control"))))}
            ),
            shared_dirs=frozenset(),
            config_files=frozenset(
                {D.TFConfigFile(D.File(D.Path("proj/service.hcl")))}
            ),
        )
        assert categorized.config_deps() == {
            D.Path("proj"): frozenset({D.Path("proj/control")})
        }
        slices = tuple(D.dependent_slices(modified, all))
        assert slices == (D.Path("proj/control"),)
