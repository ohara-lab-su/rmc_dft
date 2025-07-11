# rmc_vasp
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/shimane-dev/rmc_vasp/blob/main/README.ja.md)

"rmc_vasp" iteratively performs the ab initio molecular dynamics (MD) and the reverse monte carlo modeling (RMC).
It is based on Structure Analysis Environment package ( 
https://github.com/shimane-dev/sae.git ).


## Requirements
### VASP
VASP need to be installed.
(https://www.vasp.at/)
#### Input files
VASP input files.

### RMC
RMC POT need to be installed.
(https://www.szfki.hu/~nphys/rmc++/opening.html)
#### Input files
RMC POT input files especially experimental data.
(Xray diffraction, Neutron diffraction and so on. )

### Initial structure
Density, number of atoms (system size).


## Install

Download https://github.com/shimane-dev/rmc_vasp/ .
Also, https://github.com/shimane-dev/x_logger .
Install using pip:
````
$ pip install x_logger
$ pip install rmc_vasp
````

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
