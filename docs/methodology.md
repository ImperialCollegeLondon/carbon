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

$$ E = t \times (P_c \times u_c + P_g \times n_g + P_m \times n_m) \times \epsilon, \tag{1} $$

where $t$ is the runtime of the compute job, $P_c$ is the per-core power draw of the CPU(s), $u_c$ is the usage factor of the CPU cores (which can vary between 0 and $n_c$, where $n_c$ is the number of cores utilised by the job), $P_g$ is the per-component power draw of the GPU(s), $n_g$ is the number of GPUs employed, $P_m$ is the power draw of the memory (per GB), $n_m$ is the amount of memory allocated to the job (in GB), and $\epsilon$ is the PUE of the data center.

To estimate values for the power draw of the processors ($P_c$ and $P_g$), the thermal design power (TDP) of the component is used.
TDPs are sourced from the website of the relevant manufacturer (see [Sources](./sources.md#component-thermal-design-powers-tdps)).
The PBS workload manager used for Imperial's CX3 and HX1 systems is configured to allow the sharing of nodes between multiple jobs (there is no node exclusivity).
This holds also for the CPUs, with cores being able to be distributed among concurrent jobs.
The TDP of the full CPU component is therefore divided by the number of cores to yield an approximater per-core power draw, $P_c$.
For the CPU, the workload manager tracks the utilisation of the cores, $u_c$, over the job runtime.
This is used to scale the energy consumption due to the CPU.
(Note that PBS reports the variable `cput`, which is the CPU core-time of a job, accounting for utilisation. This variable, equivalent to $t \times u_c$, is used in the code, slightly changing the form of the energy calculation equation compared to (1))

For the GPU, exclusive use of the component by a job is assumed, so the full TDP is used for estimating power draw, $P_g$.
Since the workload managed is not configured to track the utilisation of the GPU, we assume 100% utilisation over the runtime of the job.

To estimate the power draw of memory (RAM), we follow the methodology laid out in [\[1\]](#references).
In that work, the authors describe how the power draw of memory is mainly dependent on the total quantity mobilised, rather than the amount actively in use or the nature of the workload [\[1,4\]](#references).
Therefore, the amount of memory allocated to a job is used to determine the power draw due to memory, using a per-GB power of 0.3725 GB/W [\[1\]](#references).

MEM: see refs. Based on GA methodology, we use 0.3725 W/GB (this value comes from ...). For comparison, CodeCarbon v2 uses 0.375 W/GB. CodeCarbon v3 estimates power draw of RAM based on size of the compute node, and the number of physical RAM slots it is likely to have, with each slot drawing 5 W. Aside from the dedicated large-memory nodes, the other compute nodes in CX3 have either 500GB or 1TB RAM. Assuming, 128 GB RAM per DIMM, this means the nodes have 4 or 8 DIMMs respectively. Under the codecarbon v3 convention, this would lead to per-node memory power draws of 20 W and 40 W respectively (These values will be higher if less RAM is supplied per DIMM). This may be compared to estimates of 186 W and 372 W that arise from our convention of 0.3725  W/GB. Still, we stick to a per GB estimate, as it is more suitable for shared/non-exculsive node use.

## Estimating Emissions

ToDo

## Assumptions & Limitations

ToDo

## References

1. [L. Lannelongue, J. Grealey, M. Inouye, __Green Algorithms: Quantifying the Carbon Footprint of Computation__, _Advanced Science_, 02 May 2021](https://doi.org/10.1002/advs.202100707)
1. [L. Lannelongue, M. Inouye, __Carbon footprint estimation for computational research__, _Nature Reviews Methods Primers_, 16 February 2023](https://doi.org/10.1038/s43586-023-00202-5)
1. [U. Asgher, T. Malik, __Evaluating Hardware and Software Power Measurement Tools: Assessing Accuracy in Measuring Application Energy Consumption for Data-Parallel Workloads__, _Proceedings of the Fourth International Conference on Innovations in Computing Research_, 27 June 2025](https://doi.org/10.1007/978-3-031-95652-2_39)
1. [A. Karyakin, K. Salem, __An Analysis of Memory Power Consumption in Database Systems__, _Proceedings of the 13th International Workshop on Data Management on New Hardware_, 15 May 2017](http://dx.doi.org/10.1145/3076113.3076117)
