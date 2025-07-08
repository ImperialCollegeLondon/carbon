"""The entry point for the carbon program."""

if __name__ == "__main__":
    import sys

    from carbon.energy import Energy
    from carbon.intensity import CarbonIntensity
    from carbon.job import Job

    try:
        id = sys.argv[1]
    except IndexError:
        print("Usage: poetry run python -m carbon <jobID>")
        raise

    # Get the job data
    job = Job(id)

    # Fetch carbon intensity at job startime time
    carbon_intensity = CarbonIntensity(job._starttime)
    intensity = carbon_intensity.fetch()

    # Calculate energy consumption
    energy = Energy(job._cputime, job._runtime, job._memory)
    energy_consumed = energy.calculate()

    # Calculate emissions
    emissions = intensity * energy_consumed

    print(f"Carbon intensity for {job._starttime} is {intensity} gCO2/kWh")
    print(
        f"Energy consumed from {job._cputime:.2f} CPU-hours "
        f"is {energy_consumed:.2f} kWh"
    )
    print(f"Estimated emissions is {round(emissions)} gCO2")
