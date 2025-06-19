#!/bin/bash

for i in {1..1000}
do
  # run vasp
  vasp_gam

  cat POSCAR > aaa.vasp

  # aaa.vasp -> aaa.cfg
  python3 Rvasp2cfg_nonLIB.py aaa

  #run rmc pot
  rmcp_v2023.1_lin.exe aaa

  # aaa.cfg -> aaa.vasp
  python3 Rcfg2vasp_nonLIB.py aaa

  cat aaa.cfg > POSCAR
done
