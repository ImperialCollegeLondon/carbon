"""The entry point for the carbon program."""

if __name__ == "__main__":
    import sys

    try:
        jobID = sys.argv[1]
    except IndexError:
        print("Usage: poetry run python -m carbon <jobID>")
        raise

    print(f"Your jobID is: {jobID}")
