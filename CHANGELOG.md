# CHANGELOG

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/shimane-dev/rmc_dft/blob/main/CHANGELOG.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/shimane-dev/rmc_dft/blob/main/CHANGELOG.ja.md)

# v0.6.12

## RMC / VASP init handling, symmetry, and restart fixes

Reworked init handling for repeated RMC--DFT runs and restart operation so that RMC and VASP follow the same basic
input-initialization model.

The main bug fixed in this release was that, when an existing `INCAR`
was present and an RMC--DFT calculation was restarted, the normal
`rmc_vasp_init.py` was not applied and VASP parameters could not be updated.

### `VaspIncar` initialization

Implemented a formal `VaspIncar.init()` method corresponding to the role of `RmcPotDat.init()` on the RMC side.

Initialization now behaves as follows.

- If `INCAR` already exists:
    - Read the existing `INCAR` as the initial input.
    - `init()` itself does not overwrite the existing file.
- If `INCAR` does not exist:
    - Create an initial `INCAR` and load it.
- If the object has already been initialized:
    - Repeated calls to `init()` do not reinitialize it.
    - Repeated initialization calls are therefore safe.
- INCAR tag modification remains the responsibility of `set()` /
  `set_tag()`, not `init()`.

This separates input-file initialization from parameter modification for both RMC `*.dat` files and the VASP `INCAR`.

### Updating an existing `INCAR`

An existing `INCAR` is now retained as the initial state, while tags specified by `rmc_vasp_init.py` can still be
updated through
`set_tag()`.

VASP init is no longer skipped merely because an `INCAR` already exists.

This allows parameters such as `EDIFF`, `EDIFFG`, `IBRION`, and `SIGMA`
to be changed on an existing `INCAR`, including during restart operation.

### `rmc_vasp_init.py`

`rmc_vasp_init.py` now calls `vasp_incar.init()` before applying VASP parameter settings.

Corresponding to the RMC-side initialization,

``` python
rmc_dat.init(...)
```

the VASP side now uses

``` python
vasp_incar.init()
```

as its formal input initialization.

An intermediate inconsistent implementation that called the nonexistent

``` python
vasp_incar.init(prefer_existing=True)
```

has also been removed.

`prefer_existing` is related to RMC Free/Fixed format selection and is not carried over into VASP `INCAR`
initialization.

### Normal and numbered init files

Normal init files and run-number-specific init files are supported symmetrically for RMC and VASP.

- RMC
    - `rmc_init.py`
    - `rmc_init_N.py`
- VASP
    - `rmc_vasp_init.py`
    - `rmc_vasp_init_N.py`

Run number `N` corresponds to the common sequential run number shared by RMC and DFT.

If a numbered init file corresponding to the current run exists, that numbered init is used.

In ordinary operation without numbered init files, the normal init file is used.

### Continuing a numbered init

A numbered init file can specify whether it is used only for the current run or continues to be used for subsequent runs
of the same type.

Both RMC and VASP use:

``` python
CONTINUE_NUMBERED_INIT = False
```

When `False`:

- The numbered init is used only for the current run.
- The next run of the same type returns to the normal `rmc_init.py` /
  `rmc_vasp_init.py`.

When `True`:

- The numbered init continues to be used for subsequent runs of the same type.
- It remains active until another numbered init is encountered.

This behavior is controlled from the init file itself rather than through execution parameters in `rmc_vasp_script.py`,
`rmc.py`, or
`rmc_vasp.py`.

### Dynamic loading of init files

Init files are loaded from disk immediately before each run.

Therefore, while an RMC--DFT script is running, the following files can be edited:

- `rmc_init.py`
- `rmc_init_N.py`
- `rmc_vasp_init.py`
- `rmc_vasp_init_N.py`

The updated file is read the next time that init is used.

The init mechanism intentionally does not use a normal Python import that would fix the init module at process startup.

### Init behavior during restart

Removed restart-specific behavior that disabled the normal VASP init.

In particular, fixed the case where a normal workflow using only
`rmc_vasp_init.py`, with no numbered `rmc_vasp_init_N.py`, failed to apply `rmc_vasp_init.py` after restart.

Restart now follows the same init-selection rules as normal execution.

As a result, an `INCAR` that already exists before restart can be loaded as the initial state, updated by the settings
in `rmc_vasp_init.py`, and then used for the VASP run.

### Symmetric RMC / VASP behavior

Init handling was reorganized so that RMC and VASP follow the same basic model wherever applicable.

- Existing input files are used as the initial input.
- An initial input file is created when no input file exists.
- `init()` is responsible for establishing the input file.
- Parameter modification is handled by setters.
- Both normal and numbered init files are supported.
- Continuation of numbered init files is controlled from the init file.
- Init files are dynamically reloaded for each applicable run.
- Restart uses the same rules as normal execution.

### Simplification of internal control flow

The following unnecessary or incorrect mechanisms considered during development are not used, or were removed:

- disabling the normal VASP init specifically during restart
- special `use_base_vasp_init` control
- historical searches through previous numbered init files
- unnecessary helper functions used only for init selection
- unnecessary init-control parameters in the execution scripts
- carrying the RMC-specific `prefer_existing` mechanism into VASP
- treating YAML as an INCAR-tag update mechanism
- treating init processing as a special "delta application" mechanism

Existing valid RMC / VASP execution logic, setters, postprocessing, and log backup behavior are retained. Changes are
limited to the input initialization and init-selection behavior required for this fix.

# v0.6.11

## Added execution modes for RMC-VASP sequence runs

Added an option to `rmc_vasp_script_sequence.py` to control what happens after the manually defined sequence has
completed.

The option is configured in `rmc_vasp_script_sequence_dat.py`.

```python
continue_rmc_dft = False
```

### `continue_rmc_dft = False`

Only the operations listed in `manual_sequence` are executed. The program terminates when the manual sequence is
complete.

In this mode, `rmc_vasp_script_sequence.py` can be used as a supplementary tool for running only selected RMC/VASP steps
alongside the normal RMC-DFT workflow.

Example:

```python
continue_rmc_dft = False

manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
]
```

Only these three operations are executed, and no additional normal RMC-DFT loop is started.

### `continue_rmc_dft = True`

After completing the operations listed in `manual_sequence`, execution continues into the normal RMC-DFT loop.

In this mode, `rmc_vasp_script_sequence.py` can be used as an alternative to the normal `rmc_vasp_script.py`.

```python
continue_rmc_dft = True
```

After the manual sequence is complete, the normal RMC-DFT loop resumes from RMC.

## Unified the sequence configuration filename

The manual sequence configuration file is now consistently named:

```text
rmc_vasp_script_sequence_dat.py
```

`rmc_vasp_script_sequence.py` reads the following settings from this file:

```python
continue_rmc_dft
manual_sequence
```

This allows the sequence functionality to be used in two distinct ways:

- as a supplementary manual sequence for the normal workflow
- as a replacement entry point that continues into the normal RMC-DFT loop

# v0.6.10

- bugfix

# v0.6.9

## Improved RMC/DFT log layout in `plot_multi_converge.py`

Updated `plot_multi_converge.py` to support execution sequences where RMC and DFT logs do not necessarily alternate.

- Detect `logN_rmc` and `logN_dft` in log-number order, including consecutive RMC or DFT runs.
- The convergence plot continues to display RMC results in the upper row and DFT results in the lower row.
- When a DFT run immediately follows an RMC run, the corresponding RMC and DFT results are aligned in the same column.
- Consecutive RMC runs are placed in separate columns in the upper row.
- Consecutive DFT runs are placed in separate columns in the lower row.
- Columns without a corresponding RMC or DFT result are left empty.
- Removed the assumption that the numbers of RMC and DFT datasets are equal, allowing arbitrary RMC/DFT execution
  sequences to be plotted.

For example,

```text
log0_rmc
log1_rmc
log2_dft
log3_dft
log4_rmc
log5_dft
```

is arranged as:

```text
RMC: log0  log1  (empty)  log4
DFT: (empty)  log2  log3  log5
```

# v0.6.8

## Added manual RMC-VASP execution sequences

Added `rmc_vasp_script_sequence.py` as a separate script for manually specifying the execution order of RMC and VASP
runs, while keeping the standard
`rmc_vasp_script.py` unchanged.

The manual sequence is defined separately in
`rmc_vasp_script_sequence_dat.py`, so the execution order can be changed without editing the main sequence script.

For example:

```python
manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
    "rmc_init_4.py",
    "rmc_init_5.py",
    "rmc_vasp_init_6.py",
]
```

This executes the following sequence:

```text
rmc_init_1.py      -> log1_rmc
rmc_init_2.py      -> log2_rmc
rmc_vasp_init_3.py -> log3_dft
rmc_init_4.py      -> log4_rmc
rmc_init_5.py      -> log5_rmc
rmc_vasp_init_6.py -> log6_dft
```

The number in each `init_N.py` file is kept consistent with the corresponding
`logN_*` directory number.

After the manual sequence is completed, execution returns to the normal RMC-DFT loop and continues alternating between
RMC and VASP.

The standard `rmc_vasp_script.py` remains available for normal execution.
`rmc_vasp_script_sequence.py` is used only when a manually defined execution sequence is required.

# v0.6.7

## Reorganized RMC / VASP initialization

Reorganized the initialization flow so that RMC and VASP parameters for the next loop can be changed independently while
an RMC-DFT run is in progress.

### RMC

When RMC is executed from `rmc_vasp_script.py`, the initialization file corresponding to the current RMC loop number is
loaded immediately before that RMC run.

```text
log0_rmc -> rmc_init.py
log1_rmc -> rmc_init_1.py
log2_rmc -> rmc_init_2.py
...
```

This allows parameters for the next RMC loop to be changed during an RMC-DFT run by creating or editing the
corresponding `rmc_init_N.py` before that loop starts.

When `rmc.py` is executed directly, it continues to use `rmc_init.py`.

### VASP

The VASP initialization flow has been made symmetric with the RMC initialization flow.

When VASP is executed from `rmc_vasp_script.py`, the initialization file corresponding to the current VASP loop number
is loaded immediately before that VASP run.

```text
log0_dft -> rmc_vasp_init.py
log1_dft -> rmc_vasp_init_1.py
log2_dft -> rmc_vasp_init_2.py
...
```

This allows parameters for the next VASP loop to be changed during an RMC-DFT run by creating or editing the
corresponding `rmc_vasp_init_N.py` before that loop starts.

When `rmc_vasp.py` is executed directly, it uses `rmc_vasp_init.py`.

### Removed duplicate VASP initialization

Removed the separate first-run VASP initialization path using `run_vasp_init_safe()` from `rmc_vasp_script.py`.

VASP initialization is now handled only by the corresponding `rmc_vasp_init_N.py` immediately before each loop,
preventing INCAR and related settings from being applied through multiple initialization paths.

The logic in `rmc_vasp.py` that dynamically searched for `rmc_vasp_init_N.py` was also removed, giving each component a
clear responsibility:

```text
Direct execution:
rmc.py      -> rmc_init.py
rmc_vasp.py -> rmc_vasp_init.py

RMC-DFT loop:
rmc_vasp_script.py -> rmc_init_N.py      -> run_rmc()
rmc_vasp_script.py -> rmc_vasp_init_N.py -> run_vasp()
```

This makes the RMC and VASP initialization flows consistent and symmetric.

## v0.6.6

### Initialization scripts for individual RMC runs

- Added support for running an initialization script corresponding to each RMC run immediately before that run starts in
  RMC-DFT.
- RMC log indices are mapped to initialization scripts as follows:
    - `log0_rmc` → `rmc_init.py`
    - `log1_rmc` → `rmc_init_1.py`
    - `log2_rmc` → `rmc_init_2.py`
    - `logN_rmc` → `rmc_init_N.py`
- If the corresponding `rmc_init_N.py` does not exist, the initialization step is skipped and the RMC run proceeds
  normally.
- All `rmc_init_N.py` files no longer need to exist when RMC-DFT is started; the corresponding file is checked
  immediately before each RMC run.
- Initialization scripts are loaded directly from the `.py` file immediately before execution instead of relying on a
  normal module import.
    - A later-run `rmc_init_N.py` can therefore be added while RMC-DFT is already running.
    - Changes to `rmc_init_N.py` are reflected as long as they are made before the corresponding RMC run starts.
- The actual `logN_rmc` index is used to determine the RMC run number instead of the RMC-DFT loop counter.
    - When RMC-DFT is restarted, the correct `rmc_init_N.py` corresponding to the next log index is selected.
- This run-index control is kept in `rmc_vasp_script.py`, which manages the RMC-DFT iteration, rather than adding
  run-count management to `rmc.py`, which is responsible for a single RMC execution.

## v0.6.5

### Post-processing on Ctrl+C termination

- Updated the RMC_POT termination handling in `rmc.py`.
- Wrapped the `rmc.run()` execution in `try` / `finally` so that
  `postprocess()` is executed regardless of how RMC_POT terminates.
- When RMC is interrupted with `Ctrl+C` (`KeyboardInterrupt`), intermediate files such as `*.cfg` generated before
  RMCp.exe stops are now saved to the same log directory used for normal termination.
- Unified post-processing for normal termination, `Ctrl+C`
  interruption, and other exceptions.
- `KeyboardInterrupt` and other exceptions continue to propagate after the post-processing in `finally` has completed.
- Removed the previous `postprocess()` call after normal execution to avoid duplicate post-processing.

## v0.6.4

### Extended RMC_POT free-format APIs for structural constraints and potentials

Extended `RmcPotDatFree` to provide a more complete Python interface for structural constraints and potential-related
features available in RMC_POT free-format `*.dat` files.

In particular, support was expanded for multicomponent network structures such as zeolites by organizing and extending
the APIs for COORD / SNC / COS, BVS, tabulated pair potentials, and AENET.

### BVS (Bond Valence Sum) constraints

- Added support for the RMC_POT `[ BVS ]` section.
- Added Python API support for the following BVS parameters:
    - `CENT-TYPE_CHARGE`
    - `NEIGH-TYPE_RMAX_R0_B_CHARGE`
    - `VALENCE_SIGMA`
    - `VALENCE_SIGMA-MASTER`
    - `VALENCE_SIGMA-SCALABLE`
- Multiple neighbour atom types can be specified for a single central atom type.
- Added APIs to add, retrieve, remove, and clear BVS constraints.
- Since the RMC_POT BVS constraint is intended for atomic systems, the high-level API detects configurations conflicting
  with FNC / bonded potentials.
- BVS can be used together with non-bonded potentials.

Main APIs:

```python
set_bvs_constraint(...)
get_bvs_constraints(...)
remove_bvs_constraint(...)
clear_bvs_constraints(...)
```

### Tabulated pair potentials

- Added support for `NB-TYPE = TABULATED` in the RMC_POT `[ NBPOT ]` section.
- Arbitrary distance-dependent tabulated pair potentials can now be configured for atom-type pairs.
- Added support for the following RMC_POT keywords:
    - `NB-TYPE = TABULATED`
    - `CUTOFF-TAB`
    - `TEMPERATURE`
    - `IND_SIGMA_FILE`
    - `IND_SIGMA-MASTER_FILE`
    - `IND_SIGMA-SCALABLE_FILE`
- Potential sigma prefixes `m`, `s`, and `ms` are preserved when reading and writing settings.
- Added APIs to retrieve and clear pair-potential settings.
- Added a utility for generating RMC_POT tabulated potential files directly from Python.
- Generated tabulated potential files contain equally spaced distance `r` values and potential energies `U(r)` in the
  format expected by RMC_POT.

Main APIs:

```python
set_pair_potential(...)
get_pair_potential_settings(...)
clear_pair_potential(...)
write_pair_potential_file(...)
```

### SNC API

- Added `set_snc_constraint()` as an API name directly corresponding to the RMC_POT `[ SNC ]` section.
- The existing SNC implementation used by `set_qn_constraint()` is reused rather than duplicated.
- Multiple second-neighbour atom types can be specified using multiple `STYPE_FROM_TO` entries.
- This allows multicomponent network relationships such as Si-O- (Si/Al) and Al-O- (Si/Al) to be represented directly.

Main APIs:

```python
set_snc_constraint(...)
get_snc_constraints(...)
```

The existing `set_qn_constraint()` API remains available.

### COS API

- Added `set_cos_constraint()` as an API name directly corresponding to the RMC_POT `[ COS ]` section.
- The existing angle-constraint implementation is reused without duplicating the underlying processing.
- Local angular constraints such as O-Si-O, O-Al-O, Si-O-Si, and Si-O-Al can be configured as RMC_POT COS constraints.

Main APIs:

```python
set_cos_constraint(...)
get_cos_constraints(...)
```

The existing angle-constraint APIs remain available.

### AENET / ANN potential API

- Added ANN-oriented API names while preserving the existing RMC_POT `[ AENET ]` implementation.
- The new APIs reuse the existing AENET configuration implementation rather than maintaining separate ANN and AENET
  processing paths.

Main APIs:

```python
set_ann_potential(...)
get_ann_potential_settings(...)
```

The existing `set_aenet_potential()` API remains available.

### API and implementation cleanup

- Organized COORD / SNC / COS / BVS / pair potential / AENET as the main structural-constraint and potential APIs for
  RMC_POT free-format `*.dat` files.
- Where multiple API names refer to the same RMC_POT functionality, the implementation is shared to avoid duplicated
  code.
- Added the new high-level APIs without changing the existing behavior of COORD / SNC / COS / AENET.
- Backward compatibility with existing scripts is maintained.

## v0.6.3

### Reorganized COORD / SNC Constraint APIs for Free-Format Input

- Reorganized the `[ COORD ]` and `[ SNC ]` constraint APIs in the free-format `RmcPotDatFree` implementation.
- Standardized explicit selection of multiple `[ COORD ]` / `[ SNC ]` sections using zero-based `index` values.
- `set_coord_constraint(index=...)` now updates the specified `[ COORD ]` section if it already exists, or creates it if
  it does not exist.
- `set_qn_constraint(index=...)` now behaves similarly for `[ SNC ]` sections.
- Repeated calls with the same `index` no longer increase the number of `[ COORD ]` / `[ SNC ]` sections.
- When an existing `.dat` file is loaded and updated, constraint sections and settings at other indexes are preserved.

### COORD Constraints

- Reorganized the implementation so that a single `[ COORD ]` section can contain multiple `NEIGH-TYPE_FROM_TO` entries.
- Multiple target coordination-number fractions for the same central/neighbor definition are represented by multiple
  `COORDNUM_FRACT_SIGMA`-type entries within the same `[ COORD ]` section.
- Independent coordination constraints, such as Si-O, Al-O, and O- (Si,Al), can be represented by separate `[ COORD ]`
  sections selected explicitly by `index`.

### SNC / Qn Constraints

- `set_qn_constraint(index=...)` is now the standard API for configuring `[ SNC ]` Qn constraints.
- Only the `[ SNC ]` section specified by `index` is updated; other `[ SNC ]` sections are left unchanged.
- A new `[ SNC ]` section is created when the specified `index` does not yet exist.

### Backward Compatibility

- The following legacy APIs are retained exclusively for backward compatibility with scripts written for previous
  versions:
    - `add_coord_constraint()`
    - `add_qn_constraint()`
    - `initialize_qn_constraints()`
- These legacy APIs are compatibility wrappers only. Constraint creation, validation, and update logic is implemented
  exclusively in the current `set_*_constraint()` / `clear_*_constraints()` APIs.
- `add_coord_constraint()` obtains the current number of `[ COORD ]` sections and delegates to `set_coord_constraint()`
  using that value as the new `index`.
- `add_qn_constraint()` obtains the current number of `[ SNC ]` sections and delegates to `set_qn_constraint()` using
  that value as the new `index`.
- `initialize_qn_constraints()` delegates to the current `clear_qn_constraints()` implementation.
- The legacy `add_*` APIs preserve their original append behavior. Repeated execution against an existing `.dat` file
  can therefore create duplicate constraint sections.
- Legacy scripts that rebuild constraints should continue to explicitly clear the corresponding constraints with
  `clear_coord_constraints()` or `initialize_qn_constraints()` before calling the legacy `add_*` APIs.
- New code should use `set_coord_constraint(index=...)` and `set_qn_constraint(index=...)`, which provide stable
  behavior across repeated executions.

## v0.6.2

### Unified fixed/free format initialization

- Refactored the initialization flow of `RmcPotDat` to provide a unified initialization interface for both fixed and
  free formats.
- Added lazy initialization so that a `.dat` file is created or loaded only when initialization is actually required.
- Existing `.dat` files are now detected automatically and their format (fixed/free) is reused instead of recreating the
  file.
- Improved the initialization API to support both explicit initialization and automatic initialization through the
  normal workflow.
- Preserved the existing parameter-setting API after initialization, allowing scripts to update parameters without
  changing their usage.

## v0.6.1

- Generalized the FNC/cutoff consistency checker to support arbitrary multi-component systems instead of a hard-coded
  SiO₂ mapping.
- Removed the fixed mapping between FNC constraint types and cutoff indices. Cutoff entries are now resolved from the
  actual atom-type pair defined by each FNC constraint.
- Improved FNC/cutoff validation to evaluate each constrained atom pair independently.
- Modified the consistency condition to allow `rmin == cutoff`; only `rmin < cutoff` is now treated as an error.
- Refactored the CFG atom-type lookup to reuse the existing CFG layout instead of relying on SiO₂-specific assumptions.

## v0.6.0

- Refactored the Qn-related programs into an independent package and separated them from the main codebase.

## v0.5.4

### SiO2 Qn structure analysis script

The standalone script for analyzing the Qn distribution in an SiO2 structure was reorganized and corrected.

#### Removed the external JSON configuration

- Removed the requirement to load Qn analysis settings from an external JSON file.
- Consolidated the analysis settings into `QN_CONFIG` at the beginning of the script.
- Qn analysis conditions can now be changed by editing only `QN_CONFIG`.
- Resolved `FileNotFoundError` failures caused by missing external files such as `aaa.json`.

#### Automatic structure-file discovery

When no structure file is explicitly specified, the analysis script now searches the default candidates in order.

```text
CONTCAR
POSCAR
POSCAR.vasp
aaa.vasp
aaa.cfg
```

### Fixed

#### Unified fixed-format and free-format APIs

The free-format implementation has been revised to provide API compatibility with the fixed-format implementation.

The goal of this update is to allow the same initialization script (`rmc_init.py`) to generate either fixed-format or
free-format RMC_POT input files without requiring changes to the calling code.

#### Improved fixed/free format compatibility

The free-format implementation now follows the behavior of the fixed-format implementation more closely.

Major compatibility improvements include:

- Added compatibility methods corresponding to fixed-format APIs.
- Unified method names and keyword argument names between fixed-format and free-format implementations.
- Corrected internal parameter mappings that did not correspond to the fixed-format implementation.
- Improved handling of constraint-count APIs so that existing initialization scripts behave consistently.
- Improved potential enable/disable handling for compatibility with the fixed-format interface.

#### X-ray experiment parameter compatibility

Corrected the mapping of X-ray experiment parameters.

Changes include:

- `READ-COEFFS` now defaults to reading coefficients from the experimental data file, matching the behavior of the
  fixed-format implementation.
- Corrected the mapping of fixed-format experiment parameters to the corresponding free-format keywords.
- Replaced the incorrect use of `SCALE` with the appropriate `CONST-SUBTRACT` parameter.
- Corrected the mapping of background correction flags using `POLY-BACK-FLAGS`.
- Updated `RENORM` handling to match the fixed-format implementation.

#### Internal consistency improvements

Improved consistency between the fixed-format and free-format implementations.

- Added compatibility methods where necessary while preserving the existing fixed-format behavior.
- Improved compatibility of getter/setter APIs used by initialization scripts.
- Existing fixed-format workflows remain unchanged.

## v0.5.3 nakada

### Qn Network Analysis

- Added a Qn network analysis tool for VASP/POSCAR structures.

- Added automatic input structure detection.

    - `POSCAR`

    - `POSCAR.vasp`

    - `aaa.vasp`

    - `aaa.cfg`

- Added automatic conversion from RMC_POT `cfg` files to VASP format.

- Embedded Qn analysis parameters directly into the analysis script.

    - External JSON configuration is no longer required for simple analysis.

- Improved the configuration layout so that atom types and distance cutoffs can be edited in one place.

- Improved output messages and structure detection.

- Refactored the Qn analysis utility.

- Bug fixes and internal code cleanup.

### RMC_POT

- Minor bug fixes and code cleanup.

# v0.5.2

- Cumulative bug fixes, primarily related to parameter tuning, binary rebuilds, and execution testing.

## Building with SNC Support

To enable SNC support, rebuild `rmc_pot` with:

```text

make AGC=0

```

## Bug Fixes for Fugaku `rmc_pot` (Nakada Version)

A bug was identified in the SNC implementation of the Fugaku-specific `rmc_pot` (Nakada version).

Due to incomplete implementation during the initial development, the SNC functionality contained defects that caused
incorrect behavior whenever SNC was enabled.

This issue was **not** caused by the usage of `rmc_dft` or by incorrect input files, but by the implementation of the
`rmc_pot` program itself (Nakada version).

The implementation has been corrected.

## Free Format and Fixed Format Verification

Additional verification was performed using the standard (non-AGC) build.

Both Free Format and Fixed Format input modes were tested under the normal execution environment.

## SNC Verification

Comparative validation was performed between:

- Original `rmc_pot`

- Fugaku `rmc_pot` (Nakada version)

The SNC functionality and execution behavior were compared to confirm consistency after the bug fixes.

# v0.5.1

- bugfix

## v0.5.0 nakada

### Added

- Added support for RMC_POT free-format `*.dat` files.
- Added `RmcPotDatFree`, which preserves the existing fixed-format `RmcPotDat` public interface while reading and
  writing free-format `#002` / `#003` input files.
- Added free-format-only support for second-neighbour constraints (`[ SNC ]`) used to specify Qn network fractions.
    - Added methods for adding, updating, reading, removing, and clearing Qn/SNC constraints.
    - Added support for `CTYPE_FTYPE_FROM_TO`, repeated `STYPE_FROM_TO`, and `COORDNUM_FRACT_SIGMA` variants.
- Added free-format-only support for AENET artificial neural-network potentials (`[ AENET ]`).
    - Added methods for configuring trained ANN potential files for each RMC atom type.
    - Added support for `CUTOFF-AENET`, `WRITE-ATOMIC-ENERGY`, `AENET-STEP`, and sigma variants.
    - Added validation for settings explicitly incompatible with AENET.
- Added `make_qn_snc.py`.
    - Generates a free-format RMC_POT `*.dat` file for SiO2 with specified Q4/Q3/Q2 fractions.
    - Converts percentages to the SNC fraction values used by RMC_POT.
- Added `analize_sio2_snqq_from_poscar.py`.
    - Reads an existing VASP POSCAR structure and calculates the Qn distribution of Si atoms.
    - Reports Q4/Q3/Q2 and any other detected Qn states.
    - Reports Si atoms that do not satisfy any Qn state under the configured first- and second-neighbour distance
      ranges.

## v0.4.34

### Added

- Added support for PPCF files with an arbitrary number of atom types.
- Automatically detect the number of atom types from the PPCF header.
- Automatically determine the number of partial PPCFs using `N(N+1)/2`.

### Changed

- Updated `plot_ppcf.py` to automatically plot all available partial PPCFs.
- Updated `plot_ppcf2.py` to automatically generate the required subplot layout.
- Partial PPCF labels (`g11`, `g12`, ... `gnn`) are now generated automatically.

## v0.4.33 nakada

### Fixed

- Added support for POTCAR identifier suffixes in VASP 6 POSCAR/CONTCAR files (e.g. `Si/xxxxxxxxxxxx`).
- Normalized element names when reading POSCAR files, converting `Si/xxxxxxxxxxxx` → `Si` and `O/xxxxxxxxxxxx` → `O`.
- Fixed Qn network analysis (`make_qn`) after VASP restart so that the standard RMC→DFT workflow and restart workflow
  both handle VASP 6 POSCAR files correctly.

## v0.4.32 nakada

### Added

- Added fault-tolerant handling for FNC pair generation during Qn network construction.
- Qn topology generation no longer aborts when an FNC pair does not satisfy the configured distance constraints.
- FNC pair generation errors are captured and reported as warnings instead of terminating the entire build process.
- Enabled generation of topology and network analysis outputs even when FNC pair generation fails.
- `make_qn.py` now reports FNC generation failures while continuing to generate all available outputs.

## v0.4.31 nakada

### Documentation

- Added a comprehensive manual for RMC `top` / `fnc` generation.
- Documented the design and workflow of the new Qn network analysis module.
- Added explanations of the architecture and responsibilities of each Qn-related class.
- Documented how atomic networks are analyzed and converted into RMC `top` and `fnc` files.
- Added an overview of the RMC_POT `top` / `fnc` file formats, including their purposes and basic syntax.
- Explained the relationship between network topology, Qn analysis, and force-constraint generation.
- Added descriptions of the applicability and limitations of the current implementation, including SiO₂-specific
  assumptions and reusable components for other network-forming materials.
- Added examples and implementation notes for future extension to other material systems.

## v0.4.30 nakada

### Changed

- Moved the Qn network analysis and RMC_POT constraint generation workflow from the monolithic `qn_network.py`
  implementation into the package-side `rmc_dft.rmc_pot.qn` module.
- Split the Qn-related implementation into class-oriented files.
    - `vasp_structure.py`
    - `qn_network_analysis.py`
    - `rmc_constraint_writer.py`
    - `qn_network_builder.py`
    - `config_error.py`
- Reorganized the responsibilities of `VaspStructure`, `QnNetworkAnalysis`, `RmcConstraintWriter`, and
  `QnNetworkBuilder`.
- Reworked `QnNetworkBuilder` as a facade for the former `qn_network.py` workflow.
- Added Qn topology / FNC generation to `rmc_vasp_script.py` so that RMC_POT topology and FNC files can be generated
  from the structure updated by the VASP postprocess step.
- Unified the RMC-DFT-side Qn topology / FNC output names as `aaa.top` and `aaa.fnc`.
- Cleaned up the handling of temporary prefix-based output names used by standalone scripts and the filenames used by
  the RMC-DFT workflow.
- Simplified argument handling in `conv_cfg2poscar.py`.
    - `conv_cfg2poscar aaa Si,O` is treated as `cfg_name=aaa` and `element_info=["Si", "O"]`.
    - `conv_cfg2poscar xxxx.yml` reads `cfg_name` and `element_info` from `rmc_dft.config.Config`.

### Fixed

- Fixed an invalid class reference in `QnNetworkAnalysis.from_poscar()`.
- Fixed a possible `KeyError` in `build_network()` when a bridge atom is not present in `bridge_second_map`.
- Fixed circular imports in the Qn-related modules.
- Adjusted the internal implementation while preserving the public interfaces used by the Qn topology / FNC generation
  workflow.

## v0.4.29

### Fixed

- Fixed invalid RMC_POT FNC file generation.
- Corrected the FNC writer to output the fixed record layout required by the RMC_POT manual, including required blank
  records in the header.
- Fixed FNC atom-record generation so generated `.fnc` files are no longer written as an arbitrary neighbor-list dump.
- Fixed FNC constraint generation to use validated unit-based pairs instead of directly exporting Q-network-wide pairs.
- Fixed FNC constraint definitions so constraint types are defined by `kind` and `atom_types`, rather than hidden
  `source` strings.

### Changed

- Reworked FNC generation to use the same independent unit assignment as unit topology generation.
- Moved shared unit-assignment settings to `network.unit`, while keeping TOP-specific output parameters under
  `rmc.top.unit`.
- Renamed internal unit-assignment terminology from `ligand` to `neighbor`.
- Refactored independent unit construction so it can be shared by TOP and FNC generation.
- Changed FNC output to preserve generated record order instead of sorting neighbors during output.
- Reorganized FNC validation logic for atom types and distance ranges.
- Updated FNC configuration to define constraints explicitly using `kind`, `atom_types`, `rmin`, and `rmax`.

### Removed

- Removed DAT snippet generation from `qn_network.py`.
- Removed `get_dat_config()`.
- Removed `write_dat_snippets()` and related DAT snippet writer code.

## v0.4.28 nakada

Reorganized the Qn network analysis and RMC_POT input generation workflow by redesigning the class structure.

- `qn_network.py`
    - Added the `VaspStructure` class to encapsulate VASP/POSCAR loading and structural data management.
    - Added the `QnNetworkAnalysis` class to consolidate Qn network construction, analysis, statistics, and report
      generation.
    - Moved the generation of `qn.csv`, `network_bonds.csv`, and `report.txt` into `QnNetworkAnalysis`.
    - Added the `RmcConstraintWriter` class to consolidate generation of RMC_POT FNC, topology, and DAT snippet files.
    - Moved analysis and output routines from scattered module-level functions into their corresponding classes.
    - Reimplemented `QnNetworkBuilder` as a compatibility facade while preserving the existing public interface.

- `analyze_sio2_qn.py`
    - Refactored into an analysis-only utility based on `QnNetworkAnalysis`.
    - Limited the script to analysis outputs without generating RMC_POT FNC or topology files.
    - Changed the output naming to use the input structure name as the filename prefix.

## v0.4.27 nakada

Reorganized the RMC_POT topology generation workflow and refined the default output behavior and configuration
structure.

- `qn_network.py`
    - Refactored the topology generation workflow to clearly separate RMC_POT topology generation from FNC generation.
    - Restored the independent-unit topology as the default topology output instead of the current-network topology.
    - Reorganized the output file naming for topology, FNC, and DAT snippet files.
    - Removed compatibility handling for the legacy JSON configuration and unified the implementation with the new JSON
      hierarchy.
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
- The relationship between `charge` and the non-bonded potential in RMC_POT will be further verified against the
  official User Guide and source code.

## v0.4.25 nakada

Bug-fix release for the experimental FNC=4 topology generation introduced in v0.4.24.

- Fixed multiple issues in the SiO2 FNC=4 topology generation workflow.
    - Corrected topology generation based on the actual requirements of RMC_POT rather than a plain GROMACS topology.
    - Fixed molecule and topology generation logic in `qn_network.py`.
    - Improved generation of the example script `example/fnc/SiO2_03/make_sio2_qn_fnc.py`.
    - Corrected inconsistencies found while validating generated topology files with RMC_POT.
- Updated comments and internal implementation to clarify the differences between GROMACS topology files and RMC_POT
  topology files.

Notes:

- The FNC=4 topology generation remains experimental.
- Further validation against the official RMC_POT topology specification is still in progress.

## v0.4.24 nakada

Added experimental support for generating RMC_POT FNC / Qn-network files for SiO2 glass.

This release freezes the current implementation state first, regardless of whether the new workflow is already fully
validated.

- Added `src/rmc_dft/rmc_pot/fnc/`.
    - Added `qn_network.py`.
    - Collected the basic functionality for Qn-network analysis, FNC=3 `.fnc` generation, and FNC=4 GROMACS-style
      topology generation.
    - The package-side implementation is treated as a generic `central - bridge - second` Qn-network analyzer, not as a
      SiO2-specific module.
- Moved SiO2-specific settings to the example side.
    - Added `example/fnc/SiO2_03/make_sio2_qn_fnc.py`.
    - Added `example/fnc/SiO2_03/qn_config_sio2.json`.
    - SiO2-specific settings such as `central=Si`, `bridge=O`, `second=Si`, FNC distance ranges, and FNC=4 topology
      parameters are collected in the JSON configuration.
- Cleaned up intermediate scripts that are no longer needed.
    - The package-side `make_qn_network_constraints.py` is marked for removal because its functionality has been moved
      into `qn_network.py`.
    - The package-side `sio2.py` is marked for removal because SiO2-specific defaults should not live in the generic
      module.
    - SiO2-specific helper code is kept only under the example directory.
- Clarified the role of FNC files.
    - FNC=3 is used to generate distance-window `.fnc` constraints from the extracted network.
    - FNC=4 is used to generate a flexible-molecule topology for RMC_POT.
    - A GROMACS BKS-MD `.top` file and an RMC_POT FNC=4 topology are treated as different files with different purposes.
- Added docstrings and comments.
    - Added explanations for the Qn definition, RMC index handling, assumptions about POSCAR/cfg atom order, and the
      roles of FNC=3 and FNC=4.
    - The current code is organized as an explanatory implementation for understanding and further refinement.

Notes:

- The Qn/FNC generation feature in v0.4.24 is experimental. Before production use, the generated `.fnc` / `.top` files,
  RMC_POT acceptance ratio, Qn distribution, bond-length distribution, and angle distribution must be checked.
- The numerical parameters for SiO2 are initial values and are expected to be tuned based on RMC fitting against the
  experimental profile.

## v0.4.23 nakada

Bug-fix release for the FNC distance-range editing feature introduced in v0.4.22.

- Fixed FNC header parsing in `RmcPotDat.set_fnc_distance_ranges()`.
    - Removed fixed line-index parsing such as `lines[1]`.
    - The parser now searches for the `No. of possible rmin-rmax pairs` line and reads the type count, rmin line, and
      rmax line after it.
    - `.fnc` files containing title lines or blank lines are now handled correctly.
- Preserved the FNC file existence check.
    - Missing `.fnc` files raise `FileNotFoundError`.
    - RMC no longer proceeds silently with a missing or unintended FNC file when FNC is enabled.
- Preserved `get_fnc_distance_ranges()`, `set_fnc_distance_ranges()`, and `_resolve_fnc_path()`.
    - Existing FNC pair definitions, neighbor indices, and constraint type assignments are not changed.
    - Only the rmin/rmax values in the FNC header are rewritten.
- Organized the FNC range setting example in `rmc_init.py` so that it specifies only constraint types that actually
  exist in the `.fnc` file.
    - In the current Li3PO4 example, only type 1 P-O is targeted.
    - The assumption that O-O is not constrained by FNC is preserved.

## v0.4.22 nakada

Improved FNC configuration handling during RMC execution so that FNC settings can be adjusted from `rmc_init.py`.

- Added methods to `RmcPotDat` for handling FNC file distance ranges.
    - Added `get_fnc_distance_ranges()`.
    - Added `set_fnc_distance_ranges()`.
    - By default, handles `.fnc` files with the same basename as the cfg/dat files, such as `aaa.fnc`.
    - Rewrites only the rmin/rmax values in the FNC header without changing FNC pair definitions or constraint type
      assignments.
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

The sample `rmc.py` did not call `rmc_init.py` because that line had been commented out. This was not wrong in terms of
the original purpose of `rmc.py`, but it was extremely inconvenient for RMC testing. Therefore, `rmc.py` now calls
`rmc_init.py` by uncommenting that call.

## v0.4.19 nakada

- The Packmol-related functionality was enhanced and moved into an independent package, `packmol_util`, so the
  Packmol-related code was removed from the `rmc-dft` tree.
- The Packmol-related examples were replaced with examples from `packmol_util`.
    - Removed `make_amorphous.py`.
    - Added `make_FeSiB.py`.
    - Added `make_Li3PO4.py`.

## v0.4.18 nakada

Added default VASP/RMC_POT sample settings for Fugaku.

## v0.4.17 nakada

The flow of configuration values during RMC-DFT execution was reorganized because duplicate definitions were mixed
between `config` and initialization scripts.

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

- Values set through `RmcPotDat` `set_*()` methods are now reflected not only in the current state of `.dat`, but also
  in `Config`.
- For the experimental data filename (`exp_filename`), `get_exp_filename()` now prioritizes the current state and falls
  back to the default value in `config.yml` only when necessary.
- The pre-execution existence check for `RMC` was reviewed on the assumption that it refers to the current state of the
  `RmcPotDat` instance.

### VASP side

- The assumption that `VaspIncar` / `VaspKpoints` are handled with a shared `config` was organized.
- `run_vasp_init()` / `run_vasp()` were reviewed so that settings shared through helper instances remain consistent.
- In the setting resolution of `Vasp.run()`, values explicitly specified on the script side now take priority over
  `config`.

### Notes

- `restart` remains not only for inheriting the log number, but also for determining whether to restart from `RMC` or
  `VASP` by checking existing `logNN_rmc` / `logNN_dft` directories.
- Normal startup begins from initialization, but the log directory name uses the number following the current maximum
  existing number.

## v0.4.16 nakada

As a continuation of the configuration cleanup started in v0.4.15, minor inconsistencies in the VASP execution system
were fixed.

- Fixed remaining typos around VASP execution.
- Improved error handling when `dft_bin` is unset or does not exist on `PATH`.
- Organized command construction and log output in `Vasp.run()`.
- Removed unused processing in `vasp_kpoints.py`.
- Fixed inconsistent variable names in `xdatcar2poscar.py`.

Updated the version to `0.4.16`.

## v0.4.15 nakada

The configuration handling was reorganized.

Previously, values changed by `set_*()` on the script side could become inconsistent with the values observed by other
classes through `config`. This made consistency fragile across RMC/DFT loops or when another class referred to
configuration values.

The current policy is:

- explicitly set values have the highest priority;
- those values are also reflected in the `Config` instance;
- `Config` defaults are used only when there is no explicit setting;
- if neither exists, the value is treated as unset.

### RMC side

- Major `set_*()` methods in `RmcPotDat` now update not only the corresponding `.dat` line, but also the mirror value on
  the `Config` side.
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

This makes values set by `set_exp_filename()` in `run_rmc_init()` also be used directly by the existence check in
`RmcPot.preprocess()`.

### VASP side

- `Config` can now be shared with `VaspIncar` / `VaspKpoints`.
- Values set by `set_tag()` or `set_mode()` / `set_grid()` / `set_shift()` on the script side are now reflected not only
  inside the helper class, but also on the `Config` side.
- When creating `Vasp`, the same `Config` is passed to the internally created `VaspIncar` / `VaspKpoints`.
- Values changed by `set_mpi()` / `set_job_cmd()` are also reflected in `Config`.

### Overall RMC-DFT

- `RmcDft.set_cfg_name()` and `RmcDft.set_max_rmc_dft_loop()` now reflect their values not only internally, but also in
  `Config`.
- `example/rmc_vasp_script.py` now creates `VaspIncar` / `VaspKpoints` with shared `config`.

### Remaining cautions

- `Config` still serves both as a user-facing mirror and as a shared data container across classes.
- Therefore, when adding new `set_*()` methods, the principle should be to update not only the internal state but also
  `Config`.
- Getter-side behavior also needs to be aligned so that current values in `.dat` / `INCAR` / `KPOINTS` are prioritized,
  and only absent values fall back to `Config` defaults.

## v0.4.14 nakada

Because the tag/branch was forgotten, the following content is carried over to v0.4.15.

- Various fixes to realize basic RMC-DFT runs (`rmc` / `vasp` / `rmc-dft`) on Fugaku.
- Existing issues:
    - parameters that should be set in `config`;
    - parameters that should be edited in the script.
- These had become somewhat chaotic, although they worked through an empirically tuned balance. This state is recognized
  as a problem and is expected to be resolved in v0.4.15.

## v0.4.13 nakada

### Changes

- OpenMP thread counts can now be set separately for RMC execution and VASP execution.
- `rmc_omp_num_threads` is applied only to `OMP_NUM_THREADS` when running `rmc_pot`.
- `dft_omp_num_threads` is applied only to `OMP_NUM_THREADS` when running VASP.
- This prevents the VASP side from being constrained by the OpenMP thread count specified for the RMC side.

### Fixes

- The asynchronous execution path of `rmc_pot` now also passes the configured environment variables to the child
  process.
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

In previous example scripts, the RMC-side and DFT-side input-file setting updates and execution processing were grouped
into the same functions. Therefore, when changing parameters for each RMC-DFT loop, it was necessary to edit the
internal processing of `run_rmc` / `run_vasp` directly, making it somewhat difficult to create custom RMC-DFT scripts.

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

Specifically, on the RMC side, `run_rmc_init()` calls the `set_*` methods of `RmcPotDat` and updates the contents of the
`.dat` file, then `run_rmc()` executes RMC_POT. On the DFT side, `run_vasp_init()` updates input conditions such as
`INCAR`, and then `run_vasp()` executes VASP.

With this structure, RMC and DFT parameters can be changed explicitly from the script side for each loop. For example,
changing RMC conditions only for the first few loops, or changing VASP convergence conditions midway, can now be written
relatively directly in `run_rmc_init()` / `run_vasp_init()`.

Structurally, this was the originally intended usage, but functionality had gradually been pushed into subfunctions for
convenience, which ultimately made the scripts harder to use.

With this change, the example script may look slightly longer at first glance, but the responsibilities of RMC input
setting, RMC execution, DFT input setting, and DFT execution are separated at the top-level loop-control stage. This
should make it easier to create custom RMC-DFT calculation scripts. In effect, the structure returns to the
early-version style of instance calls on the RMC-DFT side.

## v0.4.11 nakada

The log numbering rule in normal mode was aligned with the automated log-numbering rule in restart mode. The numbering
is now made a simple complete sequence.

When RMC automatic convergence detection, which is still unstable, is used, the NEW-style numbering may become:

```aiignore
log1_rmc
...
log10_dft
log11_rmc
...
```

Because `rmc` and `dft` no longer necessarily form a one-to-one correspondence, the previous OLD-style counting, where
one RMC-DFT pair was counted as one loop, is no longer used even in normal mode:

```aiignore
log1_rmc
log1_dft
log2_rmc
log2_dft
...
```

Restart mode already used the NEW-style from the beginning. For example, if the calculation directory already ended
with:

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

The same applies when the calculation ended with RMC. If `log11_rmc` exists and `rmc_vasp_script.py` is run, `log12_dft`
starts. These directories are result-storage directories.

These functions make it much easier to recover calculations midway. The reliability of calculation restart depends on
each calculation result, so the script does not check that. In earlier versions, the script unnecessarily checked
calculation completion, which made conditional branching very complicated and made casual restarts feel risky. This has
been simplified.

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
    - **Caution: when running RMC for a short time, the number of steps in `hst` is small, so automatic determination
      can enter an endless state.**

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
- Made Hst/Log analysis use methods that are as similar as possible, although the concepts may differ between `total`
  and `global`.
- Added Hst analysis in a form that can extract all information.

## v0.4.0 nakada

- Investigated and implemented restart handling for cases where RMC-DFT is stopped midway.

Policy:

- In the current working directory, assumed to be the current directory, determine whether the calculation ended during
  RMC or during DFT.
    - Add a termination-detection method, meaning detection of whether the program ended normally, not convergence
      detection.
- On the script side, find which termination flag is missing and restart that calculation.
- Since RMC_POT writes usable judgment information only to standard output, the code was modified so that this output
  can be saved.

- `RMC_POT.py`
    - Added switching between blocking and non-blocking subprocess execution.
    - Added the ability to record subprocess standard output to a file.
        - Expanded the `rmc_pot_log.py` class so that log files can be analyzed and organized.
        - The log file is normally obtained as RMC_POT standard output, but even when it is obtained as a job-file log,
          RMC_POT start/end can now be detected from log-file behavior.

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

- Added the S (Q) filename to the default settings of `config.yml` / `config.py`.
- Bug fix for `rmc_vasp_script`, RMC preprocessing.
- Added file checks related to RMC in `rmc_vasp_script`.

Classes:

- Changed the exception-handling policy for DFT-related `rmc_vasp.run()`: even when an exception occurs, execution
  proceeds to RMC.

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

The Pythonization of the create/run system seems reasonably complete for RMC/DFT. However, after writing this much, it
became clear that the VASP side should have used `pymatgen` / `ase` more extensively. Because the design direction
changed midway, the classes became large.

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
- For major classes such as `Vasp` / `RmcPot`, changed the specification so that when delegated log-result classes such
  as `VaspLog()` or `RmcPotLog()` are `None`, they are created in the constructor. The previous style is also supported.

## v0.3.2 nakada

- Python 3.6 compatibility.
    - Fixed several parts that were not compatible with 3.6.

## v0.3.1 nakada

- Support for Python 3.6 and non-network environments, corresponding to the Ohara Lab HPCS environment.
    - Added `setup.py`, coexisting with TOML.
    - Removed Python 3.10-or-later syntax such as `config: str | None = None`.
        - Changed to forms that also work with Python 3.6, such as `config: Optional[str] = None`.
        - Moved `dataclass` from the internal module to an external module, `pip install dataclasses`, for Python 3.6
          support.
        - Changed annotation syntax to more backward-compatible forms, such as `list[str]` --> `List[str]`.
- Modified `config.py` and introduced `config.yaml`.
- Changed `config.py` to an instance-based form.
    - Configuration information can now be referred to through `config` from classes and methods without directly
      pulling values such as `cfg_name`.
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
        - Made log-related functionality independent classes, to be handled later inside classes rather than by file
          output.

## v0.1.x kabayashi

- Added a few RMC/VASP methods.
- Added and tested `input_sample`.
- Basic RMC-VASP operation and testing.

## v0.0.x nakada

- Prepared the skeleton structure: subprocess, class, and basic method structure.
