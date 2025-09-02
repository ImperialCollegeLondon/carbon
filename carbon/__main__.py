"""The entry point for the carbon program.

This module provides a CLI for estimating and displaying the carbon emissions of a
compute job, optionally comparing the emissions to other activities such as travel and
food consumption.
"""

import click


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
@click.argument("job_id", type=str)
def main(job_id: str, compare: bool, verbose: bool, config_path: str) -> None:
    """Estimate and display the carbon emissions of a compute job.

    Args:
        job_id (str): The job identifier to analyze.
        compare (bool): If True, compare emissions to other activities.
        verbose (bool): If True, provide verbose output.
        config_path (str): Path to the cluster configuration file.

    Returns:
        None
    """
    import sys
    from pathlib import Path

    import yaml

    from carbon.clusterconfig import ClusterConfig
    from carbon.energy import Energy
    from carbon.intensity import CarbonIntensity
    from carbon.job import Job, UnknownJobIDError

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

    # Get the job data and node hardware info
    from carbon.node import Node

    if config.dummy_job:
        # Use dummy job data for testing
        dummy = config.dummy_job
        job = Job(
            job_id,
            dummy.start_time,
            dummy.run_time,
            dummy.cpu_time,
            dummy.ngpus,
            dummy.memory_usage,
            dummy.node,
        )
        node = Node(
            name=dummy.node,
            cpu_type=dummy.cpu_type,
            gpu_type=dummy.gpu_type,
            mem_type=dummy.mem_type,
            per_core_power_watts=config.cpus[dummy.cpu_type]["per_core_power_watts"],
            per_gpu_power_watts=config.gpus[dummy.gpu_type]["per_gpu_power_watts"]
            if dummy.gpu_type
            else 0.0,
            per_gb_power_watts=config.memory[dummy.mem_type]["per_gb_power_watts"],
        )
    else:
        # Remove suffix to make IDs more uniform
        id = job_id.split(".")[0]

        if id.endswith("[]"):
            print("Error: Handling of array jobs not currently implemented.")
            sys.exit()

        # Fetch job data from the cluster's job scheduler
        try:
            job = Job.fromPBS(id)
        except UnknownJobIDError as e:
            print(f"Error: {e}. Please check the job ID.")
            sys.exit()
        node = Node.fromPBS(
            job.node,
            {
                "cpus": config.cpus,
                "gpus": config.gpus,
                "memory": config.memory,
            },
        )

    # Calculate energy consumption
    energy = Energy(
        node.per_core_power_watts,
        node.per_gpu_power_watts if node.per_gpu_power_watts is not None else 0.0,
        node.per_gb_power_watts,
        config.pue,
    )
    energy_consumed = energy.calculate(job.cputime, job.runtime, job.memory, job.ngpus)

    # Fetch carbon intensity at job startime time
    carbon_intensity = CarbonIntensity(job.starttime)
    intensity = carbon_intensity.fetch()

    # Calculate emissions
    emissions = intensity * energy_consumed

    if verbose:
        print(
            f"Cluster information:"
            f"\n    Name: {config.cluster_name}"
            f"\n    PUE: {config.pue}"
            f"\nNode information:"
            f"\n    Name: {node.name}"
            f"\n    CPU model: {node.cpu_type}"
            f"\n    GPU model: {node.gpu_type}"
            f"\n    Memory type: {node.mem_type}"
            f"\n    CPU power draw (per core): {node.per_core_power_watts} W"
            f"\n    GPU power draw (per GPU): {node.per_gpu_power_watts} W"
            f"\n    Memory power draw (per GB): {node.per_gb_power_watts} W"
            f"\nCalculation information:"
            f"\n    Estimate is for scope 2 emissions only "
            f"(i.e., indirect emissions due to purchased electricity)."
            f"\n    Estimate is performed AS IF carbon intensity was London average at "
            f"job start time, although electricity to Imperial's clusters is certified "
            f"as 100% renewable."
            f"\n    Estimates use the methodology of the Green Algorithms project by "
            f"the Lannelongue group at the University of Cambridge "
            f"(https://www.green-algorithms.org/, "
            f"https://doi.org/10.1002/advs.202100707)"
        )

    gpuhours = job.ngpus * job.runtime
    memhours = job.memory * job.runtime
    print(
        f"Estimated energy consumed from {job.cputime:.2f} CPU-hours "
        f"and {gpuhours:.2f} GPU-hours "
        f"and {memhours:.2f} GB-hours "
        f"is {energy_consumed:.2f} kWh"
    )
    print(f"Carbon intensity for {job.starttime} is {intensity} gCO2e/kWh")
    print(f"Estimated emissions is {round(emissions)} gCO2e")

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
