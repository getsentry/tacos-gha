"""Usage: gha-pr-comment PR_URL UNIQ FILE...

Post comments to the specified github Pull Request. Comments previously
uploaded using the "uniqueness tag" UNIQ will be deleted (upon success).

This command may post more than one comment if the input is larger than 64KB.
Comment "hunks" will be divided along a file boundary of the inputs.
"""

from __future__ import annotations

from typing import Iterable

from lib.types import URL
from lib.types import ExitCode
from lib.types import OSPath
from lib.user_error import UserError
from spec.lib.gh.pr import PR

USAGE = __doc__

TAG_NAMESPACE = "getsentry/tacos-gha/bin/gha-pr-comment"

File = OSPath  # but beeg
Files = Iterable[File]


def ensmallen(file: File, size: int) -> None:
    del file, size


# if a file is too big,
# leave a note that it's too big, and a breadcrumb to user guide

### def hunkof(files: Files, size: int) -> Iterable[list[File]]:
###     buf: list[File] = []
###     bufsize = 0
###
###     for file in files:
###         content = ensmallen(file, size * 2 / 3)
###         contentsize = file.stat().st_size
###
###         if filesize > size:
###             ...
###         elif bufsize + filesize < size:
###             buf.append(file)
###             bufsize += filesize
###         else:
###             yield buf
###             buf = [file]
###             bufsize = filesize


def hunkof(files: Files, size: int) -> Iterable[list[File]]:
    buf: list[File] = []
    bufsize = 0

    files = iter(files)
    file = next(files)

    while True:
        filesize = file.stat().st_size

        if filesize > size:
            pass

        elif bufsize + filesize < size:
            buf.append(file)
            bufsize += filesize
            file = next(files)
        else:
            yield buf
            buf = []
            bufsize = 0


def pr_comment(pr_url: URL, uniq_tag: str, commentary: Files) -> ExitCode:
    pr = PR.from_gh(pr_url)

    print(pr)
    comments = tuple(pr.comments())
    print(comments)

    old_comments = [
        comment
        for comment in comments
        if comment.has_tag(uniq_tag, TAG_NAMESPACE)
    ]

    # comment size limit is https://github.com/orgs/community/discussions/27190#discussioncomment-3254953
    for commentary_hunk in hunkof(commentary, size=2**15):
        del commentary_hunk

    for comment in old_comments:
        comment.delete()

    return None


@UserError.handler
def main() -> ExitCode:
    from sys import argv

    if len(argv) < 3:
        return USAGE

    pr_url = URL(argv[1])
    uniq_tag = argv[2]
    files = [File(path) for path in argv[3:]]

    return pr_comment(pr_url, uniq_tag, files)


if __name__ == "__main__":
    raise SystemExit(main())
