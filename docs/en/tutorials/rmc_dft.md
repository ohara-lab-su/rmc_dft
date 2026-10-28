# RMC-DFT Execution Tutorial

> Applies to: **rmc_dft v0.6.13**
>
> This tutorial describes the standard automated RMC → VASP → RMC → VASP ... workflow using `rmc_vasp_script.py`, including the use of `rmc_init_N.py` and `rmc_vasp_init_N.py`.

## 1. Basic Operation

`rmc_vasp_script.py` alternates between RMC and VASP calculations.

Conceptually:

```text
RMC
 |
 v
DFT(VASP)
 |
 v
RMC
 |
 v
DFT(VASP)
 |
 ...
```

The structure obtained from RMC is passed to VASP, and the structure obtained from VASP is returned to the next RMC calculation.

## 2. Shared Sequence Numbers

In v0.6.13, RMC and DFT log directories use **one shared sequence of numbers**.

For example:

```text
log0_rmc
log1_dft
log2_rmc
log3_dft
log4_rmc
log5_dft
```

There are no separate RMC and DFT counters.

The current sequence number is determined by `next_log_dir_name()`.

## 3. Normal Start

Start normally with:

```bash
python rmc_vasp_script.py
```

A normal start creates the initial CFG from:

```text
POSCAR0
   |
   +--> POSCAR
           |
           +--> initial CFG
```

Execution then begins with RMC.

## 4. Restart

Restart with:

```bash
python rmc_vasp_script.py restart
```

The script examines existing `logN_rmc` / `logN_dft` directories to determine the next sequence number and whether to resume with RMC or VASP.

Restarting does not disable initialization files. The same initialization-file selection rules apply as in normal execution.

In particular, even when numbered VASP initialization files are not used, the normal:

```text
rmc_vasp_init.py
```

is applied after restart.

## 5. Standard Initialization Files

Normal input conditions are defined in:

```text
rmc_init.py
rmc_vasp_init.py
```

By default, RMC runs use `rmc_init.py`, and VASP runs use `rmc_vasp_init.py`.

Initialization files are loaded from disk immediately before each run, so they can be edited during a long RMC-DFT calculation.

For example, changing `sigma` or `maximum move` in:

```text
rmc_init.py
```

while the calculation is running causes the updated settings to be loaded for the next RMC run that uses that file.

The same applies to VASP initialization files.

## 6. Numbered Initialization Files

To use different conditions at a specific sequence number, create:

```text
rmc_init_N.py
rmc_vasp_init_N.py
```

For example, if:

```text
rmc_init_4.py
```

exists, it is used for the RMC run with sequence number 4.

Similarly:

```text
rmc_vasp_init_5.py
```

is used for the VASP run with sequence number 5.

`N` refers to the shared RMC/DFT sequence number, not an RMC-only or DFT-only counter.

## 7. Continuing a Numbered Initialization File

Numbered initialization files contain:

```python
CONTINUE_NUMBERED_INIT = False
```

### `False`

When:

```python
CONTINUE_NUMBERED_INIT = False
```

the numbered initialization file is used only for the current run.

The next run of the same type returns to the standard initialization file.

For example:

```text
log4_rmc -> rmc_init_4.py
log5_dft
log6_rmc -> rmc_init.py
```

### `True`

When:

```python
CONTINUE_NUMBERED_INIT = True
```

the numbered initialization file continues to be used for subsequent runs of the same type.

For example:

```text
log4_rmc -> rmc_init_4.py
log5_dft
log6_rmc -> rmc_init_4.py
log7_dft
log8_rmc -> rmc_init_4.py
```

If a newer numbered initialization file appears later, that file takes precedence.

## 8. Initialization Files Are Reloaded Dynamically

Even when `rmc_init_4.py` remains active through `CONTINUE_NUMBERED_INIT=True`, the initially loaded Python module is not kept fixed in memory.

Each run reloads the file using:

```python
runpy.run_path(...)
```

Therefore, editing `rmc_init_4.py` during execution changes the settings used for the next RMC run.

The same behavior applies on the VASP side.

## 9. RMC and VASP Initialization

On the RMC side:

```python
rmc_dat.init(...)
```

establishes the initial `*.dat` input, followed by `set_*()` calls to configure calculation conditions.

On the VASP side:

```python
vasp_incar.init()
```

establishes the initial `INCAR` input, followed by `set_tag()` calls.

Existing input files are used as the initial state when present.

The presence of an existing input file does not disable initialization.

## 10. Transferring Structures from RMC to VASP

After RMC completes:

```python
shutil.copy(f"{config.cfg_name}.vasp", "POSCAR")
```

copies the VASP-format structure obtained from RMC to `POSCAR` for the next VASP calculation.

## 11. Transferring Structures from VASP to RMC

VASP's `postprocess()` processes the calculated structure into a form usable by the next RMC run.

Repeating these transfers enables alternating RMC and DFT calculations.

## 12. Choosing the Appropriate Initialization Files

For normal operation, use only:

```text
rmc_init.py
rmc_vasp_init.py
```

Add numbered files only when conditions must change at a particular run:

```text
rmc_init_N.py
rmc_vasp_init_N.py
```

For a one-time change:

```python
CONTINUE_NUMBERED_INIT = False
```

For a persistent change:

```python
CONTINUE_NUMBERED_INIT = True
```

The design principle in v0.6.13 is to keep calculation conditions and their continuation settings in initialization files, rather than embedding them in the execution logic of `rmc_vasp_script.py`.
