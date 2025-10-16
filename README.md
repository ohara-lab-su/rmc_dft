# rmc_vasp
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.ja.md)

"rmc_vasp" iteratively performs the ab initio molecular dynamics (MD)/ geometry optimization and the reverse monte carlo modeling (RMC).
It is based on Structure Analysis Environment package ( 
https://github.com/shimane-dev/sae.git ).

## Table of Contents

- [Requirements](#requirements)
    - [VASP](#vasp)
        - [Input files](#input-files)
    - [RMC](#rmc)
        - [Input files](#input-files-1)
    - [Initial structure](#initial-structure)
- [Install](#install)
- [Using without installation](#using-without-installation)
- [How to run](#how-to-run)
    - [Beta version](#beta-version-middle-of-august-2025)
- [Output](#output)

## Requirements
### VASP
VASP need to be installed.
(https://www.vasp.at/).
Tested versions: 6.4.2, 5.3.5.

#### Input files
VASP input files.

### RMC
RMC POT need to be installed.
(https://www.szfki.hu/~nphys/rmc++/opening.html).
Tested version: 2023.1.

#### Input files
RMC POT input files especially experimental data.
(Xray diffraction, Neutron diffraction and so on. )

### Initial structure
Density, number of atoms (system size).
(Initial structure can be generated using Packmol. (https://m3g.github.io/packmol/). For random structure, set minimal interatomic distance to about 2Å, avoiding error.)


## Install

Download https://github.com/shimane-dev/rmc_vasp/ .
Also, https://github.com/shimane-dev/x_logger .
Install using pip:
````
$ pip install x_logger
$ pip install rmc_vasp
````

<details>

<summary> Using without installation </summary>

Download https://github.com/shimane-dev/rmc_vasp/ .

Also, https://github.com/shimane-dev/x_logger .

Put "x_logger/" under "rmc_vasp/src/rmc_vasp/"

</details>


## How to run

Put input files in a folder (work??) and open python:
````
$ python3
````
then,
````
>>> import rmc_vasp
````
and,
````
>>> run()
````

### Beta version (Middle of August, 2025)
We put input files at "rmc_vasp/src/rmc_vasp/" and run the code as follows:
````
$ python ./main.py
````

### Output
The output files are placed in the log0, log1, log2, ... folders.
The output files include the RMC POT input files, VASP input files, and ...
aaa.chi : Chi value of RMC modeling. Agreement of S(Q) with experimental data or something else depending on the RMC input data.
grep_E0_OSZICAR.txt : Energy
