"""A simple hg hook to keep an intree hg-git in sync.

Installation: in .hg/hgrc:

    [hooks]
    update = python:lib.hg.update

"""
from __future__ import annotations

from mercurial.context import changectx

# from hgext_hggit.git_handler import GitHandler
from mercurial.localrepo import localrepository
from mercurial.ui import ui

from lib.sh import sh

# pyright: basic
# mypy: ignore-errors


def hg_git_sync(repo: localrepository, ctx: changectx) -> bool:
    git = repo.githandler  # type: ignore
    git.export_commits()  # equivalent to hg-push, but without network access
    sha = git.map_git_get(ctx.hex())
    if not sha:
        return False

    sh.run(("git", "checkout", "-q", "--detach"))
    sh.run(("git", "reset", "-q", "--mixed", sha))

    try:
        bookmark = ctx.bookmarks()[0]
    except IndexError:
        pass
    else:
        sh.run(("git", "checkout", "-q", sha, "-B", bookmark))

    s = repo.status()
    changed = s.added + s.modified + s.removed
    if changed:
        sh.run(("git", "add") + tuple(sorted(changed)))

    return True


def update(
    ui: ui, repo: localrepository, parent1: bytes, **kwargs: object
) -> None:
    del ui, kwargs

    ctx: changectx = repo[repo.lookup(parent1)]

    hg_git_sync(repo, ctx)


def precommit(
    ui: ui, repo: localrepository, parent1: bytes, **kwargs: object
) -> bool:
    print(1)
    del ui, kwargs

    print(2)
    ctx: changectx = repo[repo.lookup(parent1)]

    print(3)
    try:
        print(3.1)
        if not hg_git_sync(repo, ctx):
            print(3.2)
            return True
        print(3.3)
    except Exception:
        print(3.4)
        print(">" * 79)
        import traceback

        print(traceback.format_exc())
        print("<" * 79)
        raise
    print(3.5)

    print(4)
    print(">" * 79)
    try:
        result = not sh.success(("pre-commit", "run"))
        print("=" * 79)
    except Exception:
        print("|" * 79)
        import traceback

        print(traceback.format_exc())
        raise
    print("<" * 79)
    print("RESULT:", result)
    return result
