"""The entry point for the carbon program."""

if __name__ == "__main__":
    import sys

    from carbon.intensity import CarbonIntensity

    try:
        jobID = sys.argv[1]
    except IndexError:
        print("Usage: poetry run python -m carbon <jobID>")
        raise

    # Create a CarbonIntensity object with the specified postcode
    carbon_intensity = CarbonIntensity()

    # Fetch carbon intensity data
    intensity_yesterday = carbon_intensity.get_yesterday()

    print(f"Your jobID is: {jobID}")
    print(
        f"National carbon intensity for "
        f"this time yesterday: {intensity_yesterday} gC02/kWh"
    )
