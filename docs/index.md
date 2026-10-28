# rmc_dft

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/rmc_dft/en/index.html)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/rmc_dft/ja/index.html)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Frmc_dft-181717?logo=github)](https://github.com/ohara-lab-su/rmc_dft/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/rmc_dft/en/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.en.html)

`rmc_dft` is a Python package for constructing and running RMC-DFT workflows that alternate the generation of
three-dimensional structural models consistent with experimental data using Reverse Monte Carlo (RMC) and
energy/force-based structural relaxation using DFT.

The current working implementation uses **RMC_POT + VASP**. It contains the practical machinery required for repeated
RMC/VASP calculations, parameter updates, restart handling, per-run initialization scripts, and result archiving.

## Current status

Originally, `rmc_dft` contained both the RMC_POT utility layer and the RMC-DFT workflow implementation.

In v0.7.0, the RMC_POT input, execution, and analysis functionality was separated into the independent [
`rmc_util`](https://pypi.org/project/rmc-util/) package. The current `rmc_dft` package is responsible for the VASP side
and the RMC-DFT workflow, while RMC_POT handling is provided by `rmc_util`.

New code should import RMC_POT-related classes directly from `rmc_util`.

```python
from rmc_dft import Config, Vasp, VaspIncar, VaspKpoints
from rmc_util import RmcPot, RmcPotDat, RmcPotHst
```

This separation gives the packages distinct roles: standalone RMC_POT handling belongs to `rmc_util`, while workflows
combining RMC and DFT belong to `rmc_dft`.

## Installing example scripts

`rmc_dft install <category>` copies **all files** in the selected category into the current directory without creating a category directory. Supported categories: `analyze`, `check`, `edit`, `job`, `make`, `plot`, `run`, and `tools`.

```bash
rmc_dft install analyze
rmc_dft install check
rmc_dft install edit
rmc_dft install job
rmc_dft install make
rmc_dft install plot
rmc_dft install run
rmc_dft install tools
rmc_dft install all
rmc_dft install plot --force
```

Existing files prevent copying unless `--force` is supplied. All 44 original files must be packaged under `src/rmc_dft/scripts/` with their original directory structure.

## Installation

Install the released package from PyPI:

```bash
pip install rmc-dft
```

Current RMC_POT-based workflows use `rmc_util`.

The RMC_POT and VASP executables themselves are not included in this package. They must be installed and configured
separately to run the current RMC-DFT workflow.

## Current functionality

### Iterative RMC_POT / VASP execution

The current production workflow alternates RMC_POT and VASP calculations:

```text
initial structure
      |
      v
   RMC_POT
      |
      v
     VASP
      |
      v
   RMC_POT
      |
      v
     VASP
      |
     ...
```

The RMC side uses classes such as `RmcPot`, `RmcPotDat`, `RmcPotLog`, and `RmcPotHst` from `rmc_util`. The DFT side uses
classes such as `Vasp`, `VaspIncar`, `VaspKpoints`, and `VaspLog` from `rmc_dft`.

### Scripted calculation parameters

RMC and VASP parameters can be modified from Python initialization scripts.

The current workflow mainly uses:

```text
rmc_init.py
rmc_vasp_init.py
```

Numbered initialization files can be used to change parameters for specific runs:

```text
rmc_init_N.py
rmc_vasp_init_N.py
```

`CONTINUE_NUMBERED_INIT` controls whether a numbered initialization remains active for subsequent runs or returns to the
normal initialization file. Initialization files are loaded immediately before the corresponding run, allowing later
calculation parameters to be changed while a long RMC-DFT calculation is still running.

### Restart

Restart utilities inspect saved RMC/VASP results and determine whether execution should resume from the RMC or VASP
stage.

Results are archived in per-run directories such as `rmc_log*` and `dft_log*`, providing the state required for
continued calculations and inspection of calculation history.

### VASP handling

The current VASP implementation includes functionality for:

- reading and updating `INCAR`
- configuring `KPOINTS`
- building `POTCAR`
- local, MPI, and job-based VASP execution
- reading VASP output such as `OUTCAR`
- archiving calculation results
- transferring structures between POSCAR/CONTCAR and RMC CFG
- helper analysis of structures, atomic motion, and forces

## `RmcDft`

`RmcDft` is the integrated class for alternating RMC and DFT calculations.

```python
from rmc_dft import Config, RmcDft

config = Config("config.yml")

rmc_dft = RmcDft(
    config=config,
)

rmc_dft.run()
```

`Config` currently contains backend-selection settings such as:

```python
rmc_code = "RmcPot"
dft_code = "Vasp"
```

and `RmcDft` has a structure for selecting RMC and DFT implementations by name.

However, **the backends actually connected at present are RMC_POT and VASP**. Other names such as RMCProfile or Quantum
ESPRESSO are not currently available simply by changing these configuration values.

## Practical RMC-DFT scripts

The current working code also includes lower-level workflow scripts in addition to the `RmcDft` class.

`rmc_vasp_script.py` handles alternating RMC/VASP execution, restart, numbered initialization files, and log-directory
management.

`rmc_vasp_script_sequence.py` supports manually specified RMC/VASP execution sequences as well as continuation into the
normal RMC-DFT loop.

Some files retain the historical `rmc_vasp` name. The package and the overall workflow are now named `rmc_dft`.

## Design goal and future direction

The essential idea of RMC-DFT is not to permanently bind the workflow to one RMC program and one DFT program. The
workflow consists of:

1. using RMC to generate a three-dimensional structural model consistent with experimental data,
2. using DFT to relax that structure according to energy and atomic forces, and
3. repeatedly transferring the structure between these two stages.

The current implementation realizes this workflow with RMC_POT and VASP. The longer-term design goal of `rmc_dft` is to
make the workflow independent of a specific **RMC code or DFT code**.

The energy/force-based relaxation stage also does not necessarily have to remain DFT-only. For systems where it is
appropriate, the intended architecture should allow structural relaxation using a machine-learning potential (MLP). This
would allow DFT and MLP relaxation to be selected according to the required accuracy, system size, and computational
cost.

Conceptually, the intended future architecture is:

```text
                    RMC modeling / experimental-data fitting
                              |
                    +---------+---------+
                    |                   |
                 RMC_POT            other RMC
                    |                   |
                    +---------+---------+
                              |
                           structure
                              |
                    +---------+---------+
                    |                   |
                    DFT                MLP
              (VASP, etc.)      structure relaxation
                    |                   |
                    +---------+---------+
                              |
                           structure
                              |
                             ...
```

This is a **design goal**, not a statement that all of these backends are already implemented. The currently operational
backends are RMC_POT and VASP.

## Relationship with `rmc_util`

General RMC_POT functionality has been separated into `rmc_util`.

`rmc_util` can be used independently for RMC_POT fixed/free-format input handling, structural constraints, execution,
and analysis of log, HST, FIT, and PPCF output.

`rmc_dft` uses that layer for the RMC side and focuses on structure transfer between RMC and DFT, iterative execution,
restart handling, VASP calculation setup and execution, and overall workflow control.

This separation allows the general RMC_POT functionality to be reused outside RMC-DFT while keeping `rmc_dft` focused on
the coupled workflow.

## Documentation

- [API Reference](api/modules.html)
- [Tutorials](tutorials/index.html)

## References

- [rmc_util on PyPI](https://pypi.org/project/rmc-util/)
- [RMC_POT](https://www.szfki.hu/~nphys/rmc++/opening.html)
- [VASP](https://www.vasp.at/)

`rmc_dft install all` copies all eight categories into their respective subdirectories under the current directory. Only category names or `all` are accepted; individual file paths are not supported.


```{toctree}
:maxdepth: 2
:hidden:

tutorials/index
api/modules
```
