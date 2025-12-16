# carbon

Estimates carbon emissions of compute jobs run on high-performance computing clusters.

The tool estimates the energy consumption of a job using information gathered from the workload scheduler.
Since it has been developed for use at Imperial College London,
it is currently set up to communicate with the scheduler in use on Imperial's clusters, PBS Professional v2024.1.
However, the structure of the code has been designed with the view of potential extension for use on other clusters
and with other workload schedulers.

By default, the tool requires an internet connection in order to request data from the [NESO's carbon intensity API](https://carbonintensity.org.uk/).
If required, this request can be skipped in favour of a hardcoded carbon intensity value using the `--average-intensity` flag.

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
   carbon <job ID>
   ```
