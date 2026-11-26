# rmc_dft

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/rmc_dft/en/index.html)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/rmc_dft/ja/index.html)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Frmc_dft-181717?logo=github)](https://github.com/ohara-lab-su/rmc_dft/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/rmc_dft/en/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.en.html)

`rmc_dft` coordinates an iterative workflow that models structures against experimental data with RMC_POT and relaxes them with VASP using energies and atomic forces.

## Package responsibilities

| Package | Responsibility |
| --- | --- |
| `rmc_dft` | Structure transfer between RMC and VASP, iteration, restart, manual sequencing, shared configuration, and analysis examples |
| [`rmc_util`](https://ohara-lab-su.github.io/rmc_util/en/) | RMC_POT DAT, FNC, and TOP inputs, standalone execution, and log, FIT, HST, and PPCF analysis |
| [`vasp_util`](https://ohara-lab-su.github.io/vasp_util/en/) | VASP input preparation, standalone execution, result archiving, and analysis of POSCAR, OUTCAR, and trajectories |

The RMC_POT and VASP implementations were extracted from the original `rmc_dft` in stages. Import each API from its owning package in new code. Compatibility re-exports cover selected names.

```python
from rmc_dft import Config, RmcDft
from rmc_util import RmcPot, RmcPotDat
from vasp_util import Vasp, VaspIncar, VaspPoscar
```

## Installation and script setup

Python 3.10 or later is required. Combined calculations also require separate RMC_POT and VASP installations.

```bash
pip install rmc-dft
rmc_dft install list
rmc_dft install run
```

`list` shows each bundled file with its category and a one-line description. `install <category>` copies the contents of the selected category to the current directory. Categories are `analyze`, `check`, `edit`, `job`, `make`, `plot`, `run`, and `tools`. `install all` copies all files into their category directories. Copies are selected by category. The command stops before copying if any destination exists. Use `--force` to overwrite.

The standalone RMC plotting scripts `plot_fit.py`, `plot_hst.py`, `plot_ppcf.py`, and `plot_ppcf2.py` are available from `rmc_util` 0.1.12. Scripts for comparing multiple runs or plotting combined RMC–VASP convergence remain available through `rmc_dft install plot`.

## Preparing and running a combined calculation

1. Run `rmc_dft install run`. In the copied `config.yml`, set the structure name, experimental data, executable paths, and VASP execution mode. For a fresh run, prepare `POSCAR0`, the RMC DAT and experimental data, and VASP's INCAR, KPOINTS, and POTCAR.
2. To update calculation settings immediately before runs, supply a `run_rmc_init()` function in `rmc_init.py` and a `run_vasp_init()` function in `rmc_vasp_init.py`. The `rmc_init.py` from `rmc_util` and `vasp_init.py` from `vasp_util` are starting points. Save the VASP file under the name the combined runner reads, `rmc_vasp_init.py`. The `scripts/run/` category supplies the shared configuration and sequence template. Prepare integration init files separately.
3. Launch the runner from the working directory.

```bash
python -m rmc_dft.runners.rmc_vasp_script
```

The standard runner passes the RMC_POT result to VASP as `POSCAR` and uses the CFG generated during VASP postprocessing for the next RMC run. Results are saved in `logNN_rmc` and `logNN_dft`. Pass `restart` to the same module to select the next stage from the latest log name. Numbered init files (`rmc_init_N.py` and `rmc_vasp_init_N.py`) are read immediately before the matching run. Set `CONTINUE_NUMBERED_INIT` to keep those settings active in subsequent runs.

For a manual sequence, edit `manual_sequence` and `continue_rmc_dft` in `rmc_vasp_script_sequence_dat.py`, then run `python -m rmc_dft.runners.rmc_vasp_script_sequence`. Prepare the referenced numbered init files in the working directory.

The `RmcDft` class provides a Python API for alternating runs. The runners above manage numbered init files, restart, and manual sequencing. RMC_POT and VASP are the implemented backends. The longer-term design allows for other RMC engines and structural relaxation using machine-learned potentials.

## Using existing examples

Some analysis and constraint-generation examples still reflect the package split. The examples under `analyze/` and `check/check_rmc_*.py` refer to moved modules. `make/make_analyze_qn.py` and `make/make_qn_fnc_top.py` reference separate `qn` modules. The PBS examples under `job/` have cluster-specific settings and an older local launcher path. Adapt those examples to your cluster and the current runner entry point.

```{toctree}
:maxdepth: 2
:hidden:

tutorials/index
api/modules
```
