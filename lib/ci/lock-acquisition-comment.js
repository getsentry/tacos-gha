module.exports = ({ github, context, lockObtained }) => {
  comment(github, context, JSON.parse(lockObtained));
};

function comment(github, context, lockObtained) {
  if (lockObtained) {
    github.rest.issues.createComment({
      issue_number: context.issue.number,
      owner: context.repo.owner,
      repo: context.repo.repo,
      body: "✅🔒 Obtained lock",
    });
  } else {
    github.rest.issues.createComment({
      issue_number: context.issue.number,
      owner: context.repo.owner,
      repo: context.repo.repo,
      // FIXME: need to let them know who has the lock, if you can
      body: "❌🔒 Unable to obtain lock",
    });
  }
}
