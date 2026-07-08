# CHANGELOG
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/shimane-dev/rmc_dft/blob/main/CHANGELOG.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/shimane-dev/rmc_dft/blob/main/CHANGELOG.ja.md)

## v0.4.28 nakada

Reorganized the Qn network analysis and RMC_POT input generation workflow by redesigning the class structure.

- `qn_network.py`
  - Added the `VaspStructure` class to encapsulate VASP/POSCAR loading and structural data management.
  - Added the `QnNetworkAnalysis` class to consolidate Qn network construction, analysis, statistics, and report generation.
  - Moved the generation of `qn.csv`, `network_bonds.csv`, and `report.txt` into `QnNetworkAnalysis`.
  - Added the `RmcConstraintWriter` class to consolidate generation of RMC_POT FNC, topology, and DAT snippet files.
  - Moved analysis and output routines from scattered module-level functions into their corresponding classes.
  - Reimplemented `QnNetworkBuilder` as a compatibility facade while preserving the existing public interface.

- `analyze_sio2_qn.py`
  - Refactored into an analysis-only utility based on `QnNetworkAnalysis`.
  - Limited the script to analysis outputs without generating RMC_POT FNC or topology files.
  - Changed the output naming to use the input structure name as the filename prefix.

## v0.4.27 nakada

Reorganized the RMC_POT topology generation workflow and refined the default output behavior and configuration structure.

- `qn_network.py`
  - Refactored the topology generation workflow to clearly separate RMC_POT topology generation from FNC generation.
  - Restored the independent-unit topology as the default topology output instead of the current-network topology.
  - Reorganized the output file naming for topology, FNC, and DAT snippet files.
  - Removed compatibility handling for the legacy JSON configuration and unified the implementation with the new JSON hierarchy.
  - Updated topology-related messages and report output for consistency.

- `make_sio2_qn_fnc.py`
  - Removed the dependency on the installed package and enabled standalone execution within the calculation directory.
  - Removed duplicated topology generation.
  - Updated the displayed output file names to match the new naming convention.

- `qn_config_sio2.json`
  - Reorganized the topology configuration structure.
  - Updated the configuration order to make the independent-unit topology the default configuration.
  - Added and reorganized topology-related configuration entries.

## v0.4.26 nakada

Reorganized the configuration structure for Qn-network generation and RMC_POT topology generation.

- `qn_config_sio2.json`
  - Separated the responsibilities of Qn-network generation and topology generation.
  - Reorganized topology-related settings under the `top` section.
  - Moved `[ atoms ]` parameters into `top.atoms`.
  - Stored `charge` and `mass` on a per atom-type basis.
  - Clarified that `charge` is written to the `[ atoms ]` section of the generated topology.
  - Simplified and reorganized the configuration hierarchy.

- `qn_network.py`
  - Updated to support the revised JSON structure.
  - Read `charge` and `mass` from `top.atoms` when generating the `[ atoms ]` section.
  - Cleaned up topology generation and configuration handling.

Notes:

- Non-bonded Coulomb potential generation is not enabled in the current implementation.
- `charge` is currently retained only as topology information for compatibility with the `[ atoms ]` section.
- The relationship between `charge` and the non-bonded potential in RMC_POT will be further verified against the official User Guide and source code.
 
## v0.4.25 nakada

Bug-fix release for the experimental FNC=4 topology generation introduced in v0.4.24.

- Fixed multiple issues in the SiO2 FNC=4 topology generation workflow.
  - Corrected topology generation based on the actual requirements of RMC_POT rather than a plain GROMACS topology.
  - Fixed molecule and topology generation logic in `qn_network.py`.
  - Improved generation of the example script `example/fnc/SiO2_03/make_sio2_qn_fnc.py`.
  - Corrected inconsistencies found while validating generated topology files with RMC_POT.
- Updated comments and internal implementation to clarify the differences between GROMACS topology files and RMC_POT topology files.

Notes:

- The FNC=4 topology generation remains experimental.
- Further validation against the official RMC_POT topology specification is still in progress.
 
## v0.4.24 nakada

Added experimental support for generating RMC_POT FNC / Qn-network files for SiO2 glass.

This release freezes the current implementation state first, regardless of whether the new workflow is already fully validated.

- Added `src/rmc_dft/rmc_pot/fnc/`.
  - Added `qn_network.py`.
  - Collected the basic functionality for Qn-network analysis, FNC=3 `.fnc` generation, and FNC=4 GROMACS-style topology generation.
  - The package-side implementation is treated as a generic `central - bridge - second` Qn-network analyzer, not as a SiO2-specific module.
- Moved SiO2-specific settings to the example side.
  - Added `example/fnc/SiO2_03/make_sio2_qn_fnc.py`.
  - Added `example/fnc/SiO2_03/qn_config_sio2.json`.
  - SiO2-specific settings such as `central=Si`, `bridge=O`, `second=Si`, FNC distance ranges, and FNC=4 topology parameters are collected in the JSON configuration.
- Cleaned up intermediate scripts that are no longer needed.
  - The package-side `make_qn_network_constraints.py` is marked for removal because its functionality has been moved into `qn_network.py`.
  - The package-side `sio2.py` is marked for removal because SiO2-specific defaults should not live in the generic module.
  - SiO2-specific helper code is kept only under the example directory.
- Clarified the role of FNC files.
  - FNC=3 is used to generate distance-window `.fnc` constraints from the extracted network.
  - FNC=4 is used to generate a flexible-molecule topology for RMC_POT.
  - A GROMACS BKS-MD `.top` file and an RMC_POT FNC=4 topology are treated as different files with different purposes.
- Added docstrings and comments.
  - Added explanations for the Qn definition, RMC index handling, assumptions about POSCAR/cfg atom order, and the roles of FNC=3 and FNC=4.
  - The current code is organized as an explanatory implementation for understanding and further refinement.

Notes:

- The Qn/FNC generation feature in v0.4.24 is experimental. Before production use, the generated `.fnc` / `.top` files, RMC_POT acceptance ratio, Qn distribution, bond-length distribution, and angle distribution must be checked.
- The numerical parameters for SiO2 are initial values and are expected to be tuned based on RMC fitting against the experimental profile.

## v0.4.23 nakada

Bug-fix release for the FNC distance-range editing feature introduced in v0.4.22.

- Fixed FNC header parsing in `RmcPotDat.set_fnc_distance_ranges()`.
  - Removed fixed line-index parsing such as `lines[1]`.
  - The parser now searches for the `No. of possible rmin-rmax pairs` line and reads the type count, rmin line, and rmax line after it.
  - `.fnc` files containing title lines or blank lines are now handled correctly.
- Preserved the FNC file existence check.
  - Missing `.fnc` files raise `FileNotFoundError`.
  - RMC no longer proceeds silently with a missing or unintended FNC file when FNC is enabled.
- Preserved `get_fnc_distance_ranges()`, `set_fnc_distance_ranges()`, and `_resolve_fnc_path()`.
  - Existing FNC pair definitions, neighbor indices, and constraint type assignments are not changed.
  - Only the rmin/rmax values in the FNC header are rewritten.
- Organized the FNC range setting example in `rmc_init.py` so that it specifies only constraint types that actually exist in the `.fnc` file.
  - In the current Li3PO4 example, only type 1 P-O is targeted.
  - The assumption that O-O is not constrained by FNC is preserved.

## v0.4.22 nakada

Improved FNC configuration handling during RMC execution so that FNC settings can be adjusted from `rmc_init.py`.

- Added methods to `RmcPotDat` for handling FNC file distance ranges.
  - Added `get_fnc_distance_ranges()`.
  - Added `set_fnc_distance_ranges()`.
  - By default, handles `.fnc` files with the same basename as the cfg/dat files, such as `aaa.fnc`.
  - Rewrites only the rmin/rmax values in the FNC header without changing FNC pair definitions or constraint type assignments.
- Made it possible to change distance ranges for each FNC constraint type from `rmc_init.py` before running RMC.
  - Example: adjust the PO4 shape-retention range by treating type 1 as P-O and type 2 as O-O.
- Added files to the RMC log backup targets.
  - Added `*.fnc`.
  - Added `rmc_init.py`.
  - Both files are copied to `logNN_rmc` only when they exist; missing files are skipped.

## v0.4.21 nakada

- Improved FNC switch handling in `RmcPotDat`.
  - Added bool-based enable/disable support.
  - Added methods to retrieve FNC options.
  - Fixed handling of `fnc=4` define options so they are preserved.

## v0.4.20 nakada

The sample `rmc.py` did not call `rmc_init.py` because that line had been commented out.
This was not wrong in terms of the original purpose of `rmc.py`, but it was extremely inconvenient for RMC testing.
Therefore, `rmc.py` now calls `rmc_init.py` by uncommenting that call.

## v0.4.19 nakada

- The Packmol-related functionality was enhanced and moved into an independent package, `packmol_util`, so the Packmol-related code was removed from the `rmc-dft` tree.
- The Packmol-related examples were replaced with examples from `packmol_util`.
  - Removed `make_amorphous.py`.
  - Added `make_FeSiB.py`.
  - Added `make_Li3PO4.py`.

## v0.4.18 nakada

Added default VASP/RMC_POT sample settings for Fugaku.

## v0.4.17 nakada

The flow of configuration values during RMC-DFT execution was reorganized because duplicate definitions were mixed between `config` and initialization scripts.

### Main organization policy

The priority of values from the following sources was clarified:

- values in `aaa.dat`
- values in `config.yml`
- values set by `set_*()` in the initialization script

On the RMC side, the review assumes that values are overwritten in the following order:

- `aaa.dat` / initial template values
- `config.yml`
- `set_*()` calls in the initialization script

### RMC side

- Values set through `RmcPotDat` `set_*()` methods are now reflected not only in the current state of `.dat`, but also in `Config`.
- For the experimental data filename (`exp_filename`), `get_exp_filename()` now prioritizes the current state and falls back to the default value in `config.yml` only when necessary.
- The pre-execution existence check for `RMC` was reviewed on the assumption that it refers to the current state of the `RmcPotDat` instance.

### VASP side

- The assumption that `VaspIncar` / `VaspKpoints` are handled with a shared `config` was organized.
- `run_vasp_init()` / `run_vasp()` were reviewed so that settings shared through helper instances remain consistent.
- In the setting resolution of `Vasp.run()`, values explicitly specified on the script side now take priority over `config`.

### Notes

- `restart` remains not only for inheriting the log number, but also for determining whether to restart from `RMC` or `VASP` by checking existing `logNN_rmc` / `logNN_dft` directories.
- Normal startup begins from initialization, but the log directory name uses the number following the current maximum existing number.

## v0.4.16 nakada

As a continuation of the configuration cleanup started in v0.4.15, minor inconsistencies in the VASP execution system were fixed.

- Fixed remaining typos around VASP execution.
- Improved error handling when `dft_bin` is unset or does not exist on `PATH`.
- Organized command construction and log output in `Vasp.run()`.
- Removed unused processing in `vasp_kpoints.py`.
- Fixed inconsistent variable names in `xdatcar2poscar.py`.

Updated the version to `0.4.16`.

## v0.4.15 nakada

The configuration handling was reorganized.

Previously, values changed by `set_*()` on the script side could become inconsistent with the values observed by other classes through `config`.
This made consistency fragile across RMC/DFT loops or when another class referred to configuration values.

The current policy is:

- explicitly set values have the highest priority;
- those values are also reflected in the `Config` instance;
- `Config` defaults are used only when there is no explicit setting;
- if neither exists, the value is treated as unset.

### RMC side

- Major `set_*()` methods in `RmcPotDat` now update not only the corresponding `.dat` line, but also the mirror value on the `Config` side.
  - comment
  - density
  - cutoffs
  - maximum moves
  - r spacing
  - moveout option
  - time and save
  - data flags
  - exp filename
  - exp range
  - sigma factor
  - number of atoms per move

- The behavior for retrieving the `xsq` filename (`get_exp_filename`) was organized.
  - First, use the current value on line 11 of `.dat`.
  - Only when no value exists on the `.dat` side, use `config.rmc_exp_filename`.
  - If neither exists, raise an unset-value error.

This makes values set by `set_exp_filename()` in `run_rmc_init()` also be used directly by the existence check in `RmcPot.preprocess()`.

### VASP side

- `Config` can now be shared with `VaspIncar` / `VaspKpoints`.
- Values set by `set_tag()` or `set_mode()` / `set_grid()` / `set_shift()` on the script side are now reflected not only inside the helper class, but also on the `Config` side.
- When creating `Vasp`, the same `Config` is passed to the internally created `VaspIncar` / `VaspKpoints`.
- Values changed by `set_mpi()` / `set_job_cmd()` are also reflected in `Config`.

### Overall RMC-DFT

- `RmcDft.set_cfg_name()` and `RmcDft.set_max_rmc_dft_loop()` now reflect their values not only internally, but also in `Config`.
- `example/rmc_vasp_script.py` now creates `VaspIncar` / `VaspKpoints` with shared `config`.

### Remaining cautions

- `Config` still serves both as a user-facing mirror and as a shared data container across classes.
- Therefore, when adding new `set_*()` methods, the principle should be to update not only the internal state but also `Config`.
- Getter-side behavior also needs to be aligned so that current values in `.dat` / `INCAR` / `KPOINTS` are prioritized, and only absent values fall back to `Config` defaults.

## v0.4.14 nakada

Because the tag/branch was forgotten, the following content is carried over to v0.4.15.

- Various fixes to realize basic RMC-DFT runs (`rmc` / `vasp` / `rmc-dft`) on Fugaku.
- Existing issues:
  - parameters that should be set in `config`;
  - parameters that should be edited in the script.
- These had become somewhat chaotic, although they worked through an empirically tuned balance.
  This state is recognized as a problem and is expected to be resolved in v0.4.15.

## v0.4.13 nakada

### Changes

- OpenMP thread counts can now be set separately for RMC execution and VASP execution.
- `rmc_omp_num_threads` is applied only to `OMP_NUM_THREADS` when running `rmc_pot`.
- `dft_omp_num_threads` is applied only to `OMP_NUM_THREADS` when running VASP.
- This prevents the VASP side from being constrained by the OpenMP thread count specified for the RMC side.

### Fixes

- The asynchronous execution path of `rmc_pot` now also passes the configured environment variables to the child process.
- The OpenMP setting description in `example/config.yml` was corrected to valid YAML format.

### Configuration

Example:

```yaml
mpi_cmd: "mpiexec"
mpi_flag: null

rmc_omp_num_threads: 8
dft_omp_num_threads: 1
```

## v0.4.12 nakada

In previous example scripts, the RMC-side and DFT-side input-file setting updates and execution processing were grouped into the same functions.
Therefore, when changing parameters for each RMC-DFT loop, it was necessary to edit the internal processing of `run_rmc` / `run_vasp` directly, making it somewhat difficult to create custom RMC-DFT scripts.

In this change, the RMC side was separated into

```text
run_rmc_init()
run_rmc()
```

and the DFT side was also separated into

```text
run_vasp_init()
run_vasp()
```

These are now called directly from `rmc_vasp_script`.

From the `rmc_vasp_script.py` side, this makes the flow clearer:

```text
RMC input setting
RMC execution
DFT input setting
DFT execution
```

Specifically, on the RMC side, `run_rmc_init()` calls the `set_*` methods of `RmcPotDat` and updates the contents of the `.dat` file, then `run_rmc()` executes RMC_POT.
On the DFT side, `run_vasp_init()` updates input conditions such as `INCAR`, and then `run_vasp()` executes VASP.

With this structure, RMC and DFT parameters can be changed explicitly from the script side for each loop.
For example, changing RMC conditions only for the first few loops, or changing VASP convergence conditions midway, can now be written relatively directly in `run_rmc_init()` / `run_vasp_init()`.

Structurally, this was the originally intended usage, but functionality had gradually been pushed into subfunctions for convenience, which ultimately made the scripts harder to use.

With this change, the example script may look slightly longer at first glance, but the responsibilities of RMC input setting, RMC execution, DFT input setting, and DFT execution are separated at the top-level loop-control stage.
This should make it easier to create custom RMC-DFT calculation scripts.
In effect, the structure returns to the early-version style of instance calls on the RMC-DFT side.

## v0.4.11 nakada

The log numbering rule in normal mode was aligned with the automated log-numbering rule in restart mode.
The numbering is now made a simple complete sequence.

When RMC automatic convergence detection, which is still unstable, is used, the NEW-style numbering may become:

```aiignore
log1_rmc
...
log10_dft
log11_rmc
...
```

Because `rmc` and `dft` no longer necessarily form a one-to-one correspondence, the previous OLD-style counting, where one RMC-DFT pair was counted as one loop, is no longer used even in normal mode:

```aiignore
log1_rmc
log1_dft
log2_rmc
log2_dft
...
```

Restart mode already used the NEW-style from the beginning.
For example, if the calculation directory already ended with:

```aiignore
...
log10_dft
```

then running `rmc_vasp_script.py restart` with the restart option gives:

```aiignore
...
log10_dft
log11_rmc
log12_dft
```

The same applies when the calculation ended with RMC.
If `log11_rmc` exists and `rmc_vasp_script.py` is run, `log12_dft` starts.
These directories are result-storage directories.

These functions make it much easier to recover calculations midway.
The reliability of calculation restart depends on each calculation result, so the script does not check that.
In earlier versions, the script unnecessarily checked calculation completion, which made conditional branching very complicated and made casual restarts feel risky.
This has been simplified.

## v0.4.10 nakada

Mainly bug fixes for the restart function.

## v0.4.9 nakada

Bug fix for the example `rmc.py`.

## v0.4.8 nakada

- Bug fix: improved behavior that could cause circular imports depending on usage.

## v0.4.7 nakada

- Restored the restart-related functionality that existed in older versions to the newer 0.4.x series.
- When reading `rmc_vasp`, stopped using the `run_dft` naming and standardized again on `run_vasp`.

## v0.4.6 nakada

- Changed the default to manual because RMC automatic convergence is still somewhat unsatisfactory.
- Slightly modified the sample scripts.

## v0.4.5 nakada

- Added functionality related to automatic RMC convergence.
  - Adjusted sample files related to `rmc_vasp_script` / `rmc_vasp` / `rmc` accordingly.
  - **Caution: when running RMC for a short time, the number of steps in `hst` is small, so automatic determination can enter an endless state.**

## v0.4.4 nakada

- Renamed density-related methods and converted the relevant code into standalone executable main Python scripts.

## v0.4.3 nakada

Added functionality so that `cfg2poscar` itself can receive `element_info` as an argument in the following ways:

1. read a `list(str)` as a file and treat content such as `Fe,Si,B` written in that file as `"Fe,Si,B"`;
2. if reading the `list(str)` as a file fails, treat that string itself as `"Fe,Si,B"`;
3. accept a list such as `["Fe", "Si", "B"]`.

## v0.4.2 nakada

- Bug fix.

## v0.4.1 nakada

- Modified log analysis so that it can do the equivalent of `hst`, or rather use more raw information.
- Made Hst/Log analysis use methods that are as similar as possible, although the concepts may differ between `total` and `global`.
- Added Hst analysis in a form that can extract all information.

## v0.4.0 nakada

- Investigated and implemented restart handling for cases where RMC-DFT is stopped midway.

Policy:

- In the current working directory, assumed to be the current directory, determine whether the calculation ended during RMC or during DFT.
  - Add a termination-detection method, meaning detection of whether the program ended normally, not convergence detection.
- On the script side, find which termination flag is missing and restart that calculation.
- Since RMC_POT writes usable judgment information only to standard output, the code was modified so that this output can be saved.

- `RMC_POT.py`
  - Added switching between blocking and non-blocking subprocess execution.
  - Added the ability to record subprocess standard output to a file.
    - Expanded the `rmc_pot_log.py` class so that log files can be analyzed and organized.
    - The log file is normally obtained as RMC_POT standard output, but even when it is obtained as a job-file log, RMC_POT start/end can now be detected from log-file behavior.

## v0.3.25 nakada

- Bug fixes.
  - Mainly plot-related.

## v0.3.24 nakada

- Plotting when data are missing, such as plotting during an incomplete calculation.
  - `plot_multi_converge`
  - `plot_multi_fit`

(*) Some bugs may still remain in the standalone version.

## v0.3.23 nakada

- Added a cell-size utility tool.

## v0.3.22 nakada

- Bug fix.

## v0.3.21 nakada

- Fixed a problem where `multi_plot` stops when the program is still running.
- Added a termination-detection method to `VaspOutcar`.
- Added an INCAR comparison method to `VaspIncar`.
  - RMC_DFT collects convenient tools for both DFT and RMC.

## v0.3.20 nakada

- Added several items to `config`.
- Moved some script-side variables into `config` (`make_amarphous.py`).

## v0.3.19 nakada

- `packmol_inp.py`, a helper class for creating Packmol input files.
- Script to display the shortest interatomic distances.
- Fix for the periodic boundary condition option (PBC) introduced in Packmol 20.15.0.
  - Test.

## v0.3.18 nakada

- Bug fix for v0.3.17.
- Fixed error handling in `vasp.run()`.
- Migrated POSCAR-related code from the `x_poscar` repository.
- `plot_distance_histgram.py`
  - Creates histograms of interatomic distances.
  - Used for validation when creating initial structures with Packmol.

## v0.3.17 nakada

Label update.

- Bug fixes.
- Made it work when a list such as `["Fe", "Si", "B"]` is given instead of `label.txt`.
- Stopped automatic checking of the `label.txt` file and added argument checks instead.

Python package for simplifying Packmol usage (nakada).

- Generalization related to `make_amorphous`.
  - Most functionality was pushed into the `pkmol` class.

Docs:

- Removed many errors.

## v0.3.16 nakada

Caution:

- Simplified the default branch for `None`. This does not necessarily mean there is no possibility of bugs.

Main changes:

- Added the S(Q) filename to the default settings of `config.yml` / `config.py`.
- Bug fix for `rmc_vasp_script`, RMC preprocessing.
- Added file checks related to RMC in `rmc_vasp_script`.

Classes:

- Changed the exception-handling policy for DFT-related `rmc_vasp.run()`: even when an exception occurs, execution proceeds to RMC.

## v0.3.15 nakada

- Example bug fix.

## v0.3.14 nakada

- Fixed docstrings to address errors with `sphinx`.
  - Not completely fixed, but reduced.

Amorphous structure creation:

- `make_amarphous.py`
- `rmc_dft/packmol.py`

## v0.3.13 nakada

Classes for DFT-related plotting:

- Created `VaspOutcar.py`.
- `plot_energy.py`
- `plot_multi_energy.py`
- `plot_mulit_converge.py`

## v0.3.12 nakada

RMC:

- `multi_plot`
- Bug fix.

## v0.3.11 nakada

Basic classes for plotting/analysis:

- `rmc_pot_fit.py`
- `rmc_pot_hst.py`
- `rmc_pot_ppcf.py`

Example plotting programs:

- `plot_fit.py`
- `plot_hst.py`
- `plot_ppcf.py`

## v0.3.10 nakada

Reviewed:

- `VaspPoscarBuilder()`
- `VaspIncar()`
- `VaspKpoints()`

and prepared individual example scripts for execution:

- `data_edit_dat.py` (RMC_POT)
- `data_edit_incar.py` (RMC_POT)
- `data_edit_kpoints.py` (RMC_POT)
- `data_edit_potcar.py` (RMC_POT)

These were incorporated into the RMC-DFT example script:

- `rmc_vasp.py`

They were also incorporated into the RMC-DFT example script:

- `rmc_vasp_script.py`

The Pythonization of the create/run system seems reasonably complete for RMC/DFT.
However, after writing this much, it became clear that the VASP side should have used `pymatgen` / `ase` more extensively.
Because the design direction changed midway, the classes became large.

## v0.3.9 nakada,kobayashi

- Implemented and tested operation modes related to MPI jobs.
  - Put scripts such as `run_vasp.py` directly into the job script.
  - Set MPI options, CPU counts, and similar values to `null` in `config`.
  - Run commands such as `mpirun vasp_std`.
  - This makes the job script itself operate as the long RMC-DFT driver.
- Expanded docs, mainly the RMC tutorial, mainly by Kobayashi.
- Created a skeleton for planned DFT-related docs.

## v0.3.8 nakada

- Bug fix.

## v0.3.7 nakada

- Bug fix.

## v0.3.6 nakada

- Modified `setup.py` so that Python 3.6 on HPCS and other Python versions can be switched based on the Python version.

## v0.3.5 nakada

- Renamed:
  - `vasp_bin` --> `dft_bin`

## v0.3.4 nakada

- Tested and adjusted for Python 3.6 / HPCS (IDSS).
  - Individual VASP/RMC tests are mostly complete.
  - Started testing with the `DFT_RMC` class.

## v0.3.3 nakada

- Python 3.6 compatibility.
  - Fixed several parts that were not compatible with 3.6.
- Added required-file checks before VASP / RMC execution.
- For major classes such as `Vasp` / `RmcPot`, changed the specification so that when delegated log-result classes such as `VaspLog()` or `RmcPotLog()` are `None`, they are created in the constructor.
  The previous style is also supported.

## v0.3.2 nakada

- Python 3.6 compatibility.
  - Fixed several parts that were not compatible with 3.6.

## v0.3.1 nakada

- Support for Python 3.6 and non-network environments, corresponding to the Ohara Lab HPCS environment.
  - Added `setup.py`, coexisting with TOML.
  - Removed Python 3.10-or-later syntax such as `config: str | None = None`.
    - Changed to forms that also work with Python 3.6, such as `config: Optional[str] = None`.
    - Moved `dataclass` from the internal module to an external module, `pip install dataclasses`, for Python 3.6 support.
    - Changed annotation syntax to more backward-compatible forms, such as `list[str]` --> `List[str]`.
- Modified `config.py` and introduced `config.yaml`.
- Changed `config.py` to an instance-based form.
  - Configuration information can now be referred to through `config` from classes and methods without directly pulling values such as `cfg_name`.
  - Editable parts through `config.yml`.

## v0.3.0 nakada

- Changed the specification so that INPUT-related files can be handled and managed from the class library.
  - `vasp_incar.py`
  - `vasp_potcar.py`
  - `vasp_kpoints.py`
  - `rmc_pot_dat.py`

## v0.2.3 nakada

- Reconstructed functionality equivalent to v0.2.2.
  - Rebuilt the processing units for RMC/VASP.
    - Organized methods.
- Performed minimum tests for each function.
- Tested cooperation between the individual RMC/VASP classes.
- Tested RMC/VASP calls from RMC-DFT.

## v0.2.2 nakada

- Generalized `dft_rmc` so that it reads and uses classes such as `vasp` and `rmc_pot`.
  - Clearly separated examples, programs that read the module and actually run `rmc_dft`, from modules.
- Bug fixes.
- Various adjustments.
- Cleaned up confusion related mainly to repository changes from `rm_vasp` to `rmd_dft`.

## v0.2.1 nakada

- Bug fixes and tests.

## v0.2.0, nakada

- Major cleanup of `rmc_vasp`.
  - Completely changed the class and function structure.
    - Converted individual methods into classes.
    - Kept utility-only methods as methods.
    - Made log-related functionality independent classes, to be handled later inside classes rather than by file output.

## v0.1.x kabayashi

- Added a few RMC/VASP methods.
- Added and tested `input_sample`.
- Basic RMC-VASP operation and testing.

## v0.0.x nakada

- Prepared the skeleton structure: subprocess, class, and basic method structure.
