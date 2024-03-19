# Installation

To configure a GitHub repository to use TACOS-GHA, you need to configure a
number of workflows in the `.github/workflows/` directory in the repository.
Examples of these workflow files can be found [here](workflows).

Additionally, the [install-labels](../lib/tacos/install-labels) script can be
used to create the necessary labels that TACOS-GHA looks for.

To ensure the workflows function correctly, certain repository settings must be configured.
Navigate to the repository's settings page and select the "Actions/General" tab.
Under "Workflow Permissions", set it to "Read and write permissions". Also, ensure
that the "Allow GitHub Actions to create and approve pull requests" option is checked.
Make sure to save the changes.
