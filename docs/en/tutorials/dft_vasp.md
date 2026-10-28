# VASP Execution Tutorial

> Applies to: **rmc_dft v0.6.13**
>
> This tutorial describes running VASP independently by executing `rmc_vasp.py` directly, as well as using `rmc_vasp_init.py`.

## 1. Overview

`rmc_vasp.py` runs VASP using existing VASP input files.

VASP input conditions are specified in `rmc_vasp_init.py`.

```text
config.yml
    |
rmc_vasp_init.py
    |
    +--> KPOINTS
    +--> POTCAR
    +--> VaspIncar.init()
    +--> Set INCAR tags
    |
rmc_vasp.py
    |
    +--> run_vasp()
            |
            +--> Execute VASP
            +--> postprocess
            +--> Save to logN_dft
```

## 2. Required Files

A typical setup includes:

```text
config.yml
rmc_vasp.py
rmc_vasp_init.py
POSCAR
```

`INCAR`, `KPOINTS`, and `POTCAR` can either be provided as existing files or prepared by the initialization script.

## 3. `rmc_vasp_init.py`

When `rmc_vasp.py` is launched directly, the following function is called before VASP execution:

```python
run_vasp_init(
    config=config_,
    vasp_incar=vasp_incar_,
    logger=logger_,
)
```

### KPOINTS

The current initialization script creates `KPOINTS` only if it does not already exist:

```python
if not os.path.exists("KPOINTS"):
    ...
```

An existing `KPOINTS` file is used unchanged.

### POTCAR

Likewise, `POTCAR` is created only when it is absent.

Element information is taken from `config.element_info`.

### INCAR

For INCAR, first execute:

```python
vasp_incar.init()
```

This initialization corresponds to `rmc_dat.init()` on the RMC side.

## 4. `VaspIncar.init()`

In v0.6.13, VASP also has an explicit initialization procedure.

Its basic behavior is:

```text
INCAR exists
    -> Read the existing INCAR
    -> init() itself does not rewrite it

INCAR does not exist
    -> Create an initial INCAR

Already initialized
    -> init() does not initialize again
```

After initialization, explicitly configured tags are set in `rmc_vasp_init.py`, for example:

```python
vasp_incar.set_tag("EDIFF", 1e-4)
vasp_incar.set_tag("EDIFFG", 1e-3)
vasp_incar.set_tag("ISMEAR", 0)
vasp_incar.set_tag("SIGMA", 0.1)
vasp_incar.set_tag("NSW", 30)
vasp_incar.set_tag("ISIF", 2)
vasp_incar.set_tag("IBRION", 2)
```

Importantly, **the initialization script is not skipped when an existing `INCAR` is present**.

The existing INCAR is loaded as the initial input, and the setters in `rmc_vasp_init.py` are then applied.

## 5. Execution

Run:

```bash
python rmc_vasp.py
```

The execution mode normally comes from `run_mode` in `config.yml`.

Inside `run_vasp()`, VASP is launched using:

```python
if run_mode is None:
    run_mode = config.run_mode
```

## 6. Postprocessing

After VASP finishes, postprocessing is normally performed:

```python
vasp.postprocess(
    log_dir=log_dir_vasp,
    cfg_name=config.cfg_name,
)
```

This archives calculation results and converts or updates the structural files required by the next RMC calculation.

## 7. Log Directories

The destination is determined by:

```python
next_log_dir_name("dft")
```

For example:

```text
log0_dft
log1_dft
log2_dft
...
```

In RMC-DFT operation, the numeric part is a shared sequence number across RMC and DFT.

## 8. `CONTINUE_NUMBERED_INIT`

`rmc_vasp_init.py` contains:

```python
CONTINUE_NUMBERED_INIT = False
```

This is normally unused when `rmc_vasp.py` is run independently.

When invoked through `rmc_vasp_script.py` / `rmc_vasp_script_sequence.py` with a numbered initialization file:

```text
rmc_vasp_init_N.py
```

it determines whether the numbered initialization file continues to be used for subsequent VASP runs.

## 9. General Editing Guidelines

To change VASP conditions, edit `rmc_vasp_init.py` rather than the main `rmc_vasp.py` script.

For example:

```text
EDIFF
EDIFFG
ISTART
ISMEAR
SIGMA
NELM
NSW
ISIF
IBRION
LREAL
ISPIN
ALGO
KPAR
NCORE
NSIM
```

The responsibilities are separated: `rmc_vasp.py` handles execution, while `rmc_vasp_init.py` defines input conditions.
