"""The entry point for the carbon program."""

import click


@click.command()
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
def main(job_id: str, compare: bool, config_path: str) -> None:
    """Estimate and display the carbon emissions of a compute job."""
    import sys
    from pathlib import Path

    import yaml

    from carbon.clusterconfig import ClusterConfig
    from carbon.energy import Energy
    from carbon.intensity import CarbonIntensity
    from carbon.job import Job

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
    cluster_config = ClusterConfig(**config_dict)

    # Get the job data
    if cluster_config.dummy_job:
        # Use dummy job data for testing
        job = Job(
            job_id,
            cluster_config.dummy_job.start_time,
            cluster_config.dummy_job.run_time,
            cluster_config.dummy_job.cpu_time,
            cluster_config.dummy_job.ngpus,
            cluster_config.dummy_job.memory_usage,
        )
    else:
        # Fetch job data from the cluster's job scheduler (e.g., PBS)
        job = Job.fromPBS(job_id)

    # Fetch carbon intensity at job startime time
    carbon_intensity = CarbonIntensity(job.starttime)
    intensity = carbon_intensity.fetch()

    # Calculate energy consumption
    energy = Energy(
        cluster_config.cpus.per_core_power_watts,
        cluster_config.gpus.per_gpu_power_watts,
        cluster_config.memory.per_gb_power_watts,
        cluster_config.pue,
    )
    energy_consumed = energy.calculate(job.cputime, job.runtime, job.memory, job.ngpus)

    # Calculate emissions
    emissions = intensity * energy_consumed

    gpuhours = job.ngpus * job.runtime
    print(
        f"Energy consumed from {job.cputime:.2f} CPU-hours "
        f"and {gpuhours:.2f} GPU-hours "
        f"is {energy_consumed:.2f} kWh"
    )
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
