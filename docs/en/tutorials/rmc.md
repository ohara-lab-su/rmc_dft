# RMC Execution Tutorial

> Applies to: **rmc_dft v0.6.13**
>
> This tutorial explains the basic procedure for running RMC_POT independently by executing `rmc.py` directly.

## 1. Overview

`rmc.py` runs RMC_POT on the current `*.cfg` structure.

RMC input parameters are specified in `rmc_init.py`.

The basic workflow is:

```text
config.yml
    |
    +--> RmcPotDat
    |
rmc_init.py
    |
    +--> run_rmc_init()
            |
            +--> Initialize *.dat
            +--> Set RMC parameters
    |
rmc.py
    |
    +--> run_rmc()
            |
            +--> Execute RMC_POT
            +--> Save to logN_rmc
```

## 2. Required Files

At minimum, prepare the following files in the calculation directory:

```text
config.yml
rmc.py
rmc_init.py
aaa.cfg
```

The `aaa` part depends on `cfg_name` in `config.yml`.

The RMC_POT executable, experimental data, and any other files referenced by `config.yml` or `*.dat` are also required.

## 3. `rmc_init.py`

When `rmc.py` is launched directly, the following function is called before execution:

```python
run_rmc_init(
    config=config_,
    rmc_dat=rmc_dat_,
    logger=logger_,
)
```

RMC parameter changes should generally be defined in `rmc_init.py`, rather than in `rmc.py`.

For example, use setters:

```python
rmc_dat.set_density(0.0570880440)

rmc_dat.set_maximum_moves(
    [
        0.01,
        0.01,
        0.01,
        0.01,
    ]
)

rmc_dat.set_sigma_factor(0.05)
rmc_dat.set_moveout_option(True)
rmc_dat.set_time_and_save(15, 1)
```

Free-format settings, including COORD, SNC/Qn, and angular constraints, are also configured in `rmc_init.py`.

## 4. `rmc_dat.init()`

`run_rmc_init()` first calls `RmcPotDat.init()`.

The basic behavior in v0.6.13 is:

- If an existing `*.dat` file is present, use it as the initial input.
- If no `*.dat` file exists, create the initial input.
- Calling `init()` again on an already initialized `RmcPotDat` does not repeat initialization.
- Subsequent `set_*()` calls perform the actual parameter changes.

Thus, `init()` and the setters have distinct responsibilities.

## 5. Execution

Run:

```bash
python rmc.py
```

`rmc.py` applies `rmc_init.py` and then executes RMC_POT.

## 6. Log Directories

The RMC output directory is determined by `next_log_dir_name("rmc")`.

For example:

```text
log0_rmc
log1_rmc
log2_rmc
...
```

When RMC and DFT are combined, the numbering is a **single shared sequence** across RMC and DFT, not separate RMC and DFT counters.

## 7. Ctrl+C

In v0.6.13, `rmc.py` / `run_rmc()` wraps the RMC_POT execution in `try/finally`.

Consequently, even if RMC_POT is interrupted with `Ctrl+C`, postprocessing is performed on partially generated files such as `*.cfg`, and the files are archived in the log directory.

## 8. `CONTINUE_NUMBERED_INIT`

`rmc_init.py` contains:

```python
CONTINUE_NUMBERED_INIT = False
```

This setting is effectively unused when `rmc_init.py` is used for standalone RMC execution.

It matters when `rmc_vasp_script.py` or `rmc_vasp_script_sequence.py` uses a numbered initialization file:

```text
rmc_init_N.py
```

See `rmc_dft.md` and `rmc_dft_sequence.md` for details.

## 9. Typical Parameters to Edit

Normally, edit `rmc_init.py` rather than `rmc.py` to change RMC conditions.

Typical settings include:

```text
density
cutoff
maximum move
sigma
moveout
RMC time / save interval
experimental range
r spacing
experimental data
FNC / topology
COORD
SNC / Qn
angle constraint
```

The basic design separates execution control from input-parameter configuration, keeping calculation conditions in the initialization file.
