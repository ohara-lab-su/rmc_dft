# Qn network constraints for RMC_POT

This package contains a generic Qn-network analyser and RMC_POT constraint generator.

The script is not hard-coded to SiO2.  It uses a `central - bridge - second` definition from the JSON config.  The included config is the Si-O-Si case:

```text
central = Si
bridge  = O
second  = Si
```

For SiO2, this corresponds to the usual Qn definition: each central Si has O first neighbours, and Qn is the number of those O atoms that connect to another Si.

## Files

```text
make_qn_network_constraints.py      Generic Qn/FNC/topology generator
qn_config_sio2.json                 Si-O-Si settings
SiO2_750_S1_nvt4_qn.csv             Qn result for each central Si
SiO2_750_S1_nvt4_network_bonds.csv  Detected Si-O network bonds
SiO2_750_S1_nvt4_fnc3.fnc           RMC_POT FNC=3 distance-constraint file
SiO2_750_S1_nvt4_fnc4.top           RMC_POT FNC=4 bonded-potential topology draft
SiO2_750_S1_nvt4_dat_snippet_fnc3.txt
SiO2_750_S1_nvt4_dat_snippet_fnc4.txt
SiO2_750_S1_nvt4_report.txt
```

## Reproduce

```bash
python ./make_qn_network_constraints.py \
    ./SiO2_750_S1_nvt4.vasp \
    ./qn_config_sio2.json \
    --prefix SiO2_750_S1_nvt4
```

If the POSCAR file is VASP4 style without an element-symbol line, the script uses `atom_types` in the JSON config.  For the present structure this is `Si O`.

## Current SiO2 result

```text
Q3: 1
Q4: 249
```

The Si-O network was selected with `first_mode = nearest` and `first_nearest_n = 4`.  This avoids treating a fifth near oxygen as a real Si-O network bond in a tetrahedral silica model.

## FNC=3 output

`SiO2_750_S1_nvt4_fnc3.fnc` contains distance-window constraints for:

```text
type 1: central_bridge_bond              Si-O      1.45-1.85 A
type 2: central_second_through_bridge    Si-Si     2.40-3.50 A
type 3: bridge_bridge_around_central     O-O       2.10-3.40 A
```

This is the conservative distance-constraint route.  It preserves the detected network, but it is still a rigid FNC-type treatment.

## FNC=4 output

`SiO2_750_S1_nvt4_fnc4.top` treats the detected network as one flexible molecule and writes GROMACS-type bonded terms:

```text
Si-O bonds
O-Si-O angles
Si-O-Si angles
```

The numerical force constants and sigmas are intentionally weak starting values.  They should be tuned from short RMC_POT tests by checking the acceptance ratio, chi2 terms, and the resulting Si-O/O-Si-O/Si-O-Si distributions.

## Generalization

To use this for another Qn network, edit only the JSON config.  For example:

```text
B-O-(Si,B): central_types=["B"], bridge_types=["O"], second_types=["Si", "B"]
P-O-P    : central_types=["P"], bridge_types=["O"], second_types=["P"]
Ge-O-Ge  : central_types=["Ge"], bridge_types=["O"], second_types=["Ge"]
```

Then adjust the distance ranges and FNC/topology parameters.
