# Calculation methodology

This page describes the methodology used to estimate the energy usage and carbon emissions of compute jobs.

## Gathering Compute Resources

Information about the compute job and executing node is gathered from the workload scheduler (PBS).

Internally, _carbon_ performs a subprocess call to the PBS command `qstat` and parses the result.
Therefore, only jobs accessible to `qstat` can be analysed by _carbon_.
Currently, this means that only jobs which completed in the past two weeks (or jobs in progress) may be analysed.

## Estimating Energy Consumption

The energy consumed by a job is estimated following the methodology behind the [Green Algorithms project](https://www.green-algorithms.org/),
led by Loïc Lannelongue at the University of Cambridge [\[1\]](#references).
This involves estimating the energy consumed using the compute resources assigned/used by the job,
and information about the power draw of compute components provided by the component manufacturers.
An additional factor is included in the calculation which accounts for the power usage effectiveness (PUE) of the data centre.

This method of estimating energy consumption may be compared to two alternative options [\[2\]](#references),[\[3\]](#references):

1. Hardware-based measurements (e.g., a physical power meter attached to the compute node or rack)
1. Software tools (e.g., [Perf](https://perf.wiki.kernel.org/index.php/Main_Page), [PowerStat](https://github.com/ColinIanKing/powerstat), [CodeCarbon](https://codecarbon.io/), which typically make use of Intel's [RAPL](https://greencompute.uk/Measurement/RAPL) interface under the hood.)

Measuring energy consumption directly via hardware tools will generally lead to the most accurate values, with software tools being less accurate but typically more practical [\[3\]](#references).
Compared to both these methods, estimating energy consumption based on compute resource usage will tend to be even less accurate.
However, it has two major practical advantages that motivated the adoption of this approach for _carbon_:

1. It is significantly less 'invasive', requiring no installation of additional hardware or software tools on the compute nodes/racks of the HPC cluster.
1. It can much more straightforwardly estimate the energy consumption associated with a particular user/process in a situation were a compute node may be shared between multiple users/processes.

In order to validate this approach, I am currently in the process of collating energy consumption estimates using _carbon_, with the aim of comparing these to statistics provided by the data center hosting the CX3 and HX1 clusters (i.e., benchmarking).

The following equation is used to estimate energy consumption (adapted from [\[1\]](#references)):

$$ E = t \times (P_c \times u_c + P_g \times n_g + P_m \times n_m) \times \epsilon, $$

where $t$ is the runtime of the compute job, $P_c$ is the per-core power draw of the CPU(s), $u_c$ is the usage factor of the CPU cores (which can vary between 0 and $n_c$, where $n_c$ is the number of cores utilised by the job), $P_g$ is the per-component power draw of the GPU(s), $n_g$ is the number of GPUs employed, $P_m$ is the power draw of the memory (per GB), $n_m$ is the amount of memory allocated to the job (in GB), and $\epsilon$ is the PUE of the data center.

Following assumptions are made. These are largely required based on the information that is held by the workload scheduler.
CPU: (TDP / total cores) times core-hours (which takes into account usage).
GPU: 100% TDP times walltime (assumes GPU is running at 100% usage during full run time)
MEM: see refs

## Estimating Emissions

ToDo

## Assumptions & Limitations

ToDo

## References

1. [L. Lannelongue, J. Grealey, M. Inouye, __Green Algorithms: Quantifying the Carbon Footprint of Computation__, _Advanced Science_, 02 May 2021](https://doi.org/10.1002/advs.202100707)
1. [L. Lannelongue, M. Inouye, __Carbon footprint estimation for computational research__, _Nature Reviews Methods Primers_, 16 February 2023](https://doi.org/10.1038/s43586-023-00202-5)
1. [U. Asgher, T. Malik, __Evaluating Hardware and Software Power Measurement Tools: Assessing Accuracy in Measuring Application Energy Consumption for Data-Parallel Workloads__, _Proceedings of the Fourth International Conference on Innovations in Computing Research_, 27 June 2025](https://doi.org/10.1007/978-3-031-95652-2_39)
1. ToDo: memory energy consumption
1. ToDo: Links to manufacturer TDPs
1. ToDo: Links to sources for comparisons
