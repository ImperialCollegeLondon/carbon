"""The entry point for the carbon program.

This module provides a CLI for estimating and displaying the carbon emissions of a
compute job, optionally comparing the emissions to other activities such as travel and
food consumption.
"""

from pathlib import Path

import click

from carbon import RunResult, run
from carbon.clusterconfig import ClusterConfig


@click.command()
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose output")
@click.option(
    "--compare",
    is_flag=True,
    help="Compare the carbon emissions of the compute job with other activities.",
)
@click.option(
    "--config_path",
    envvar="CARBON_CONFIG",
    type=click.Path(),
    help="Path to the cluster configuration file.",
)
@click.option(
    "--default_intensity",
    is_flag=True,
    help="Use a default value for the carbon intensity (137 gCO2/kWh)",
)
@click.option(
    "--split_jobs",
    is_flag=True,
    help="Show separate results for each job when multiple IDs are input. "
    "Without this flag, only the aggregate of the jobs is displayed.",
)
@click.option(
    "--ignore_failed",
    is_flag=True,
    help="Quietly ignore jobs that couldn't be parsed or analysed correctly. "
    "Useful when analysing large batches of jobs.",
)
@click.argument("job_ids", type=str, nargs=-1)
def main(
    job_ids: tuple[str, ...],
    compare: bool,
    verbose: bool,
    config_path: str,
    default_intensity: bool,
    split_jobs: bool,
    ignore_failed: bool,
) -> None:
    """Estimate and display the carbon emissions of a compute job.

    \b
    Args:
        job_ids (tuple[str]): Identifier(s) of the job(s) to analyze.
        compare (bool): If True, compare emissions to other activities.
        verbose (bool): If True, provide verbose output.
        config_path (str): Path to the cluster configuration file.
        default_intensity (bool): If True, use a default carbon intensity value.
        split_jobs (bool): If True, show separate results for each job when multiple IDs
            provided.
        ignore_failed (bool): If True, quietly ignore jobs that can't be parsed or
            analysed correctly, rather than crashing out.

    \b
    Returns:
        None
    """
    import sys
    from datetime import datetime

    import yaml

    from carbon.job import (
        Job,
        JobState,
        JobStateError,
        MalformedJobIDError,
        UnknownJobIDError,
        UnsupportedJobType,
    )

    # Get cluster config file path from environment variable
    if not config_path:
        print(
            "Error: Missing CARBON_CONFIG path. Please set the CARBON_CONFIG "
            "environment variable to the path of your cluster config file OR "
            "use the --config_path option to specify the path."
        )
        sys.exit(1)

    # Load the cluster configuration
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)
    config = ClusterConfig(**config_dict)

    # Run the carbon calculation
    try:
        results = run(job_ids, config, default_intensity, ignore_failed)
    except (UnknownJobIDError, MalformedJobIDError) as e:
        print(f"Error: {e}. Please check the job ID.")
        sys.exit(1)
    except JobStateError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except UnsupportedJobType as e:
        print(f"Error: Handling of {e.job_type} jobs not currently implemented.")
        sys.exit(1)

    # Warn if any jobs are still running
    for result in results:
        if result.job.state == JobState.RUNNING:
            if len(results) == 1:
                print("Job is still running. ", end="")
            else:
                print("Some jobs are still running. ", end="")
            print(
                "Note that energy and emissions estimates will be for only the "
                "completed portion of the job and may not reflect total emissions."
            )
            break

    # Print output
    if not results and not ignore_failed:
        print("No results to show. Issue in parsing or analysing job(s).")
    elif len(results) == 1:
        output_result(results[0], compare, verbose, default_intensity, config)
    elif split_jobs:
        for result in results:
            print(f"Job ID: {result.job.id}")
            output_result(result, compare, verbose, default_intensity, config)
            print("")
    else:
        # Aggregate estimates over multiple jobs
        intensity_list = []
        earliest_startime = datetime.max
        total_runtime = 0.0
        total_cputime = 0.0
        total_gputime = 0.0
        total_memtime = 0.0

        total_energy_consumed = 0.0
        total_emissions = 0.0

        agg_state = JobState.FINISHED

        for result in results:
            job = result.job
            if job.starttime < earliest_startime:
                earliest_startime = job.starttime
            total_runtime += job.runtime
            total_cputime += job.cputime
            total_gputime += job.gputime
            total_memtime += job.memtime

            total_energy_consumed += result.energy_consumed
            total_emissions += result.emissions
            intensity_list.append(result.carbon_intensity)

            # If any jobs are still running, label the aggregate job as still running
            if job.state == JobState.RUNNING:
                agg_state = JobState.RUNNING

        agg_job = Job(
            id="Aggregate",
            starttime=earliest_startime,
            runtime=total_runtime,
            cputime=total_cputime,
            gputime=total_gputime,
            memtime=total_memtime,
            node="Multiple",
            state=agg_state,
        )
        agg_result = RunResult(
            node=results[0].node,  # Just use first node for now
            emissions=total_emissions,
            energy_consumed=total_energy_consumed,
            job=agg_job,
            carbon_intensity=sum(intensity_list) / len(intensity_list),
        )
        output_result(agg_result, compare, verbose, default_intensity, config, True)


def output_result(
    result: RunResult,
    compare: bool,
    verbose: bool,
    default_intensity: bool,
    config: ClusterConfig,
    isaggregate: bool = False,
) -> None:
    """Output a carbon estimation result to the user.

    Args:
        result (RunResult): The result to display
        compare (bool): If True, compare emissions to other activities.
        verbose (bool): If True, provide verbose output.
        default_intensity (bool): If True, indicate that default carbon intensity value
            was used.
        config (ClusterConfig): The cluster configuration.
        isaggregate (bool): If True, show average carbon intensity.

    Returns:
        None
    """
    node = result.node
    emissions = result.emissions
    energy_consumed = result.energy_consumed
    job = result.job
    intensity = result.carbon_intensity

    if verbose:
        print(
            f"Cluster information:"
            f"\n    Name: {config.cluster_name}"
            f"\n    PUE: {config.pue}"
            f"\nNode information (first node/job, if multiple nodes/jobs involved):"
            f"\n    CPU model: {node.cpu_type}"
            f"\n    GPU model: {node.gpu_type}"
            f"\n    Memory type: {node.mem_type}"
            f"\n    CPU power draw (per core): {node.per_core_power_watts} W"
            f"\n    GPU power draw (per GPU): {node.per_gpu_power_watts} W"
            f"\n    Memory power draw (per GB): {node.per_gb_power_watts} W"
            f"\nCalculation information:"
            f"\n    Estimate is for scope 2 CO2 emissions only "
            f"(i.e., indirect emissions due to purchased electricity)."
            f"\n    Estimate is performed AS IF carbon intensity was London average at "
            f"job start time, although electricity to Imperial's clusters is certified "
            f"as 100% renewable."
            f"\n    Estimates use the methodology of the Green Algorithms project by "
            f"the Lannelongue group at the University of Cambridge "
            f"(https://www.green-algorithms.org/, "
            f"https://doi.org/10.1002/advs.202100707)"
        )

    if isaggregate:
        print("Aggregating estimates over multiple jobs.")

    print(f"Job run on node: {node.name}")
    print(
        f"Estimated energy consumed from {job.cputime:.2f} CPU-hours "
        f"and {job.gputime:.2f} GPU-hours "
        f"and {job.memtime:.2f} GB-hours "
        f"is {energy_consumed:.2f} kWh"
    )
    if default_intensity:
        print(f"Using UK average carbon intensity of {intensity} gCO2/kWh")
    elif isaggregate:
        print(f"Average carbon intensity across multiple jobs is {intensity} gCO2/kWh")
    else:
        print(f"Carbon intensity for {job.starttime} is {intensity} gCO2/kWh")
    print(f"Estimated emissions is {round(emissions)} gCO2")

    # Do comparisons if requested
    if compare:
        from carbon.comparisons import Food, Travel

        TRAVEL_PATH = Path(__file__).parent / "data" / "travel.csv"
        FOOD_PATH = Path(__file__).parent / "data" / "food.csv"

        if not TRAVEL_PATH.exists():
            print(
                f"Error: Missing comparisons data file at {TRAVEL_PATH}. "
                "Please ensure the data directory is present and "
                "contains the travel.csv file."
            )
        else:
            print("----- Travel Comparisons -----")
            travel_comparer = Travel(TRAVEL_PATH)
            travel_comparer.print_comparisons(emissions)

        if not FOOD_PATH.exists():
            print(
                f"Error: Missing comparisons data file at {FOOD_PATH}. "
                "Please ensure the data directory is present and "
                "contains the food.csv file."
            )
        else:
            print("----- Food Comparisons -----")
            food_comparer = Food(FOOD_PATH)
            food_comparer.print_comparisons(emissions)


if __name__ == "__main__":
    main()
