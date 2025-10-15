# carbon

Estimates carbon emissions of compute jobs run on the Imperial College London HPC clusters.

## For developers

This is a Python application that uses [uv](https://docs.astral.sh/uv/) for packaging
and dependency management. It also provides [pre-commit](https://pre-commit.com/) hooks
for various linters and formatters and automated tests using
[pytest](https://pytest.org/) and [GitHub Actions](https://github.com/features/actions).
Pre-commit hooks are automatically kept updated with a dedicated GitHub Action.

To get started:

1. [Download and install uv](https://docs.astral.sh/uv/getting-started/installation/) following the instructions for your OS.
1. Clone this repository and make it your working directory
1. Set up the virtual environment:

   ```bash
   uv sync
   ```

1. Install the git hooks:

   ```bash
   uv run pre-commit install
   ```

1. [Activate the virtual environment](https://docs.astral.sh/uv/pip/environments/#using-a-virtual-environment)
(alternatively, you can prefix any Python-related command with `uv run`):

   ```bash
   source .venv/bin/activate
   ```

1. Specify the location of your cluster configuration file:

   ```bash
   export CARBON_CONFIG=/path/to/config.yaml
   ```

1. Run the main app:

   ```bash
   python -m carbon <job ID>
   ```
