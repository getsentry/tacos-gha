module.exports = async ({ github, context, label }) => {
  try {
    await github.rest.issues.removeLabel({
      issue_number: context.issue.number,
      owner: context.repo.owner,
      repo: context.repo.repo,
      name: label,
    });
  } catch (error) {
    if (error.status === 404 && error.message === "Label does not exist") {
      console.log("Label not found");
    } else {
      throw error;
    }
  }
};
