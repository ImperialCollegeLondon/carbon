"""The entry point for the carbon program."""

if __name__ == "__main__":
    import sys
    from datetime import datetime

    from carbon.intensity import CarbonIntensity

    try:
        date_arg = sys.argv[1]
    except IndexError:
        print("Usage: poetry run python -m carbon <time>")
        raise

    when = datetime.fromisoformat(date_arg)

    # Create a CarbonIntensity object with the specified time
    carbon_intensity = CarbonIntensity(when)

    # Fetch carbon intensity data
    intensity = carbon_intensity.fetch()

    print(f"Carbon intensity for datetime {when} is {intensity} gCO2/kWh")
