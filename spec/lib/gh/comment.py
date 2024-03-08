from __future__ import annotations

from datetime import datetime
from typing import Self

from lib.parse import Parse
from lib.types import URL

TAG = '\n<!-- {namespace} "{tag}" -->\n'


def _owner_repo(pr_url: str) -> tuple[str, str]:
    """
    >>> _owner_repo('https://github.com/getsentry/ops/pull/9592#issuecomment-1984190310')
    ('getsentry', 'ops')
    """
    netloc, owner, repo, pull_endpoint, rest = pr_url.rsplit("/", 4)

    assert netloc == "https://github.com", netloc
    assert pull_endpoint == "pull", pull_endpoint

    pull, _, _ = rest.partition("#")
    assert pull.isdigit(), pull

    return owner, repo


class Comment(str):
    """
    Comment is just a string with a little bit of metadata.

    >>> comment = Comment("foo", datetime(2024, 1, 3), URL("...#comment-123"))

    >>> print(comment)
    foo

    >>> print(comment.created_at)
    2024-01-03 00:00:00

    >>> comment.id
    123
    """

    created_at: datetime
    url: URL

    def __new__(cls, comment: object, created_at: datetime, url: URL) -> Self:
        del created_at, url  # used for __init__
        self = super().__new__(cls, comment)
        return self

    def __init__(
        self, comment: object, created_at: datetime, url: URL
    ) -> None:
        del comment  # used for __new__
        self.created_at = created_at
        self.url = url
        super().__init__()

    @property
    def id(self) -> int:
        # the api doesn't want the id that it returns (IC_kwDOKu2SPc50T-Ws)
        # it wants the numeric id from the url (...#issuecomment-1951393358)
        id = Parse(self.url).after.last("-")
        return int(id)

    def delete(self) -> None:
        # I could only find how to do this via `gh api` which is considerably harder
        # to use. Please update if you find a more straightforward way.
        owner, repo = _owner_repo(self.url)

        # https://docs.github.com/en/rest/issues/comments#delete-an-issue-comment
        endpoint = f"/repos/{owner}/{repo}/issues/comments/{self.id}"

        from lib.sh import sh

        sh.run(("gh", "api", "-X", "DELETE", endpoint))

    def has_tag(
        self, tag: str, namespace: str = "getsentry/tacos-gha"
    ) -> bool:
        return TAG.format(tag=tag, namespace=namespace) in self

    def __repr__(self):
        """
        >>> Comment("foo", datetime(2024, 1, 3), URL("...#comment-123"))
        Comment('foo', created_at=datetime.datetime(2024, 1, 3, 0, 0), url=URL('...#comment-123'))
        """
        cls = type(self)
        attr_items = sorted(vars(self).items())
        attrs = ", ".join(f"{var}={val!r}" for var, val in attr_items)
        return f"{cls.__name__}({super().__repr__()}, {attrs})"
