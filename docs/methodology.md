# Calculation methodology

This page describes the methodology used to estimate the energy usage and carbon emissions of compute jobs.

## Gathering Compute Resources

Information about the compute job and executing node is gathered from the workload scheduler (PBS).

Internally, carbon performs a subprocess call to the PBS command `qstat` and parses the result.
Therefore, only jobs accessible to `qstat` can be analysed by carbon.
Currently, this means that only jobs which completed in the past two weeks (or jobs in progress) may be analysed.

## Estimating Energy Consumption

ToDo

CPU: (TDP / total cores) *core-hours
GPU: 100% TDP* walltime
MEM: see refs

## Estimating Emissions

ToDo

## Assumptions & Limitations

ToDo

## References

1. ToDo
