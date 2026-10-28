# RMC-DFT Manual Sequence Execution Tutorial

> Applies to: **rmc_dft v0.6.13**
>
> This tutorial explains how to use `rmc_vasp_script_sequence.py` to specify the execution order of RMC and VASP runs explicitly by shared sequence number.

## 1. Purpose of a Sequence

The standard `rmc_vasp_script.py` automatically repeats:

```text
RMC -> VASP -> RMC -> VASP -> ...
```

A manual sequence instead allows an explicitly specified order, such as:

```text
RMC
RMC
VASP
RMC
RMC
VASP
```

For example, it can execute the following arbitrary sequence:

```text
rmc_init_1.py
rmc_init_2.py
rmc_vasp_init_3.py
rmc_init_4.py
rmc_init_5.py
rmc_vasp_init_6.py
```

## 2. Files Used

Sequence execution primarily uses:

```text
rmc_vasp_script_sequence.py
rmc_vasp_script_sequence_dat.py
rmc_init_N.py
rmc_vasp_init_N.py
```

Normally, edit the following file to change the execution order:

```text
rmc_vasp_script_sequence_dat.py
```

## 3. `manual_sequence`

Specify the execution order in `manual_sequence`:

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

Entries are executed from top to bottom.

In this example:

```text
1: RMC
2: RMC
3: VASP
4: RMC
5: RMC
6: VASP
```

## 4. Matching Sequence Numbers

The number in the initialization filename must match the next log sequence number that will actually be created.

For example, when executing:

```text
rmc_init_4.py
```

the next RMC log must be:

```text
log4_rmc
```

Otherwise, an error occurs.

Likewise, for:

```text
rmc_vasp_init_6.py
```

the next DFT log must be:

```text
log6_dft
```

The sequence runner checks the actual next number using `next_log_dir_name()` and stops with `RuntimeError` if the specified number does not match.

## 5. Running RMC Multiple Times in Succession

While standard RMC-DFT alternates RMC and VASP, a manual sequence can run RMC repeatedly:

```python
manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_init_3.py",
]
```

Different `rmc_init_N.py` files can be used for each run, enabling a staged procedure such as:

```text
run 1: Use a large sigma for initial relaxation
run 2: Reduce the maximum move
run 3: Lower sigma to tighten the fit
```

## 6. Inserting VASP at an Arbitrary Point

For example:

```python
manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
    "rmc_init_4.py",
]
```

This runs RMC twice, then VASP, and then RMC again.

The VASP conditions are defined in `rmc_vasp_init_3.py`.

## 7. Initialization Files Are Read Immediately Before Execution

Even in sequence mode, initialization files are loaded immediately before each run using:

```python
runpy.run_path(init_file)
```

Therefore, files for runs that have not yet started can be edited during sequence execution:

```text
rmc_init_N.py
rmc_vasp_init_N.py
```

The updated contents will be used when that run begins.

## 8. `continue_rmc_dft`

`rmc_vasp_script_sequence_dat.py` contains:

```python
continue_rmc_dft = False
```

### `False`: Execute Only the Sequence

With:

```python
continue_rmc_dft = False
```

the workflow is:

```text
manual_sequence
    |
    +--> Execute all entries
    |
    +--> Finish
```

Use this to run only the specified steps, as a complement to the standard `rmc_vasp_script.py` workflow.

### `True`: Switch to Standard RMC-DFT After the Sequence

With:

```python
continue_rmc_dft = True
```

the workflow becomes:

```text
manual_sequence
    |
    +--> Execute all entries
    |
    +--> Standard RMC-DFT loop
```

After the sequence finishes, the standard loop resumes starting with RMC.

## 9. `CONTINUE_NUMBERED_INIT` and Sequences

In v0.6.13, `CONTINUE_NUMBERED_INIT` is also honored when transitioning from a manual sequence to standard RMC-DFT.

For example, if the last RMC initialization file used contains:

```python
# rmc_init_5.py
CONTINUE_NUMBERED_INIT = True
```

then, with `continue_rmc_dft=True`, the next RMC run continues to use `rmc_init_5.py` after the standard loop begins.

If it is `False`, execution returns to the standard file:

```text
rmc_init.py
```

The same applies to VASP:

```python
# rmc_vasp_init_6.py
CONTINUE_NUMBERED_INIT = True
```

In this case, the continuation state of that VASP initialization file is carried over to the standard loop.

## 10. Dynamic Changes During a Sequence

A numbered initialization file that remains active is reloaded from disk for each run.

Therefore, even when:

```python
CONTINUE_NUMBERED_INIT = True
```

is set, you can edit the active `rmc_init_5.py` during execution.

The changes take effect the next time that initialization file is used.

## 11. Example: Gradual RMC Convergence Followed by DFT

```python
continue_rmc_dft = False

manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
]
```

For example, use different conditions:

```text
rmc_init_1.py
    large sigma
    large maximum move

rmc_init_2.py
    small sigma
    small maximum move

rmc_vasp_init_3.py
    VASP structure relaxation
```

## 12. Example: Return to Standard RMC-DFT After a Sequence

```python
continue_rmc_dft = True

manual_sequence = [
    "rmc_init_1.py",
    "rmc_init_2.py",
    "rmc_vasp_init_3.py",
]
```

In this case, the manual sequence controls runs through:

```text
log1_rmc
log2_rmc
log3_dft
```

Execution then switches to the standard RMC-DFT loop.

Whether the last numbered initialization files remain active or the standard initialization files are restored depends on their `CONTINUE_NUMBERED_INIT` settings.

## 13. Choosing Between the Standard Script and a Manual Sequence

Use `rmc_vasp_script.py` for ordinary alternating iterations:

```text
RMC -> VASP -> RMC -> VASP
```

Use `rmc_vasp_script_sequence.py` when the execution order itself must be explicitly controlled:

```text
RMC -> RMC -> VASP -> RMC -> RMC -> VASP
```

A manual sequence does not merely replace the standard script. With `continue_rmc_dft=False`, it can also perform a limited set of operations that complements the standard workflow.
