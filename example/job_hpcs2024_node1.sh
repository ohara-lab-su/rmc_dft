#!/bin/bash
#PBS -j oe
#PBS -l select=1:ncpus=32:host=zaiene-hpcs2024-01:mpiprocs=32+1:ncpus=32:host=zaiene-hpcs2024-02:mpiprocs=32

# Check Environment
module list
unset FI_PROVIDER
#export FI_PROVIDER=tcp
env | grep I_MPI
env | grep FI_PROVIDER

# Go to Workdir
cd $PBS_O_WORKDIR

# Calc
# mpirun vasp_std
# mpirun vasp_gam
# $HOME/.pyenv/shims/python ./rmc_vasp0.py
# $HOME/.pyenv/shims/python ./rmc_vasp.py
$HOME/.pyenv/shims/python ./rmc_vasp_script.py
