# rmc_vasp


Just download https://github.com/shimane-dev/sae/

If you have "aaa.cfg",
````
$ python ./sae/StructureAnalysisEnvironment/bin/Rcfg2vasp_nonLIB.pyRcfg2vasp_nonLIB.py aaa
````
to get "aaa.vasp".

````
$ cd sae
$ python
$ import StructureAnalysisEnvironment as SAEnv
$ cell = SAEnv.io.Read(filename='POSCAR', code='VASP')
$ cell.write(code='FDMNES')
````