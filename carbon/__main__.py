"""The entry point for the carbon program."""

if __name__ == "__main__":
    import sys
    from datetime import datetime

    from carbon.energy import Energy
    from carbon.intensity import CarbonIntensity

    try:
        date_arg = sys.argv[1]
        walltime_arg = sys.argv[2]
        ncores_arg = sys.argv[3]
    except IndexError:
        print(
            "Usage: poetry run python -m carbon "
            "<date_arg / date> <walltime / hours> <ncores>"
        )
        raise

    when = datetime.fromisoformat(date_arg)
    walltime = float(walltime_arg)
    ncores = int(ncores_arg)

    # Create a CarbonIntensity object with the specified time
    carbon_intensity = CarbonIntensity(when)

    # Create an Energy object with the specified number of CPU cores and walltime
    energy = Energy(ncores, walltime)

    # Fetch carbon intensity data
    intensity = carbon_intensity.fetch()

    # Calculate energy consumption
    energy_consumed = energy.calculate()

    # Calculate emissions
    emissions = intensity * energy_consumed

    print(f"Carbon intensity for datetime {when} is {intensity} gCO2/kWh")
    print(
        f"Energy consumed for {walltime} hours on {ncores} cores "
        f"is {energy_consumed} kWh"
    )
    print(f"Estimated emissions is {round(emissions)} gCO2")
