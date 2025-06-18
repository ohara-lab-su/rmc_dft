# rmc_vasp


Just download https://github.com/shimane-dev/sae/blob/main/StructureAnalysisEnvironment/bin/Rcfg2vasp_nonLIB.py

If you have "aaa.cfg",
````
$ python Rcfg2vasp_nonLIB.py aaa
````
to get "aaa.vasp".

````
$ cd library
$ python
$ import StructureAnalysisEnvironment as SAE
$ cell = SAE.io.Read(filename='POSCAR', code='VASP')
$ cell.write(code='FDMNES')
````