"""The entry point for the carbon program."""

if __name__ == "__main__":
    import os
    import sys

    import yaml

    from carbon.clusterconfig import ClusterConfig
    from carbon.energy import Energy
    from carbon.intensity import CarbonIntensity
    from carbon.job import Job

    # Get cluster config file path from environment variable
    config_path = os.environ.get("CARBON_CONFIG")
    if not config_path:
        print(
            "Error: Please set the CARBON_CONFIG environment variable "
            "to the path of your cluster config file."
        )
        sys.exit(1)

    # Load the cluster configuration
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)
    cluster_config = ClusterConfig(**config_dict)

    try:
        id = sys.argv[1]
    except IndexError:
        print("Usage: poetry run python -m carbon <jobID>")
        raise

    # Get the job data
    if cluster_config.dummy_job:
        # Use dummy job data for testing
        job = Job.fromResources(
            id,
            cluster_config.dummy_job.run_time,
            cluster_config.dummy_job.cpu_time,
            cluster_config.dummy_job.ngpus,
            cluster_config.dummy_job.memory_usage,
        )
    else:
        # Fetch job data from the cluster's job scheduler (e.g., PBS)
        job = Job.fromPBS(id)

    # Fetch carbon intensity at job startime time
    carbon_intensity = CarbonIntensity(job.starttime)
    intensity = carbon_intensity.fetch()

    # Calculate energy consumption
    energy = Energy(job.cputime, job.runtime, job.memory, job.ngpus)
    energy_consumed = energy.calculate()

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
