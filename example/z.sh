#!/usr/bin/env bash

NAME="SiO2_750_S1_nvt4"
#NAME="D1100"

#SCRIPT="$HOME/zaiene_dev/rmc_dft/example"

#SCRIPT="$HOME/LiSPC/script"
#SCRIPT="$HOME/SiC/script"
#SCRIPT="$HOME/Li3PO4/script"
SCRIPT="./script"

#DATA="$HOME/SiO2/data"
#DATA="$HOME/LiSPC/data"

# cp --remove-destination -r $SCRIPT/fnc/SiO2_03/* .
#cp --remove-destination -r $SCRIPT/LiSPC/data/* .

# 一部ファイルを上書きする(こっちのほうが優先)
#cp --remove-destination -r $DATA/* .
cp --remove-destination -r $SCRIPT/* .

#####################
# パラメータ群
#cp --remove-destination $SCRIPT/rmc_vasp_init.py ./
#cp --remove-destination $SCRIPT/rmc_vasp_init_safe.py ./
#cp --remove-destination $SCRIPT/rmc_vasp_init_normal.py ./
#cp --remove-destination $SCRIPT/rmc_init.py ./
#cp --remove-destination $SCRIPT/rmc_vasp_script.py ./

#####################
# 初期構造作成
cp --remove-destination $SCRIPT/config.yml ./
cp --remove-destination $SCRIPT/make_mass_density.py ./
cp --remove-destination $SCRIPT/make_number_density.py ./
#####################

#cp --remove-destination $SCRIPT/rmc.py ./
#cp --remove-destination $SCRIPT/rmc_vasp.py ./
#cp --remove-destination $SCRIPT/clean_rmc.py ./
#cp --remove-destination $SCRIPT/make_log_dirname.py ./
cp --remove-destination $SCRIPT/plot_fit.py ./
cp --remove-destination $SCRIPT/plot_multi_fit.py ./
cp --remove-destination $SCRIPT/plot_multi_hst.py ./
cp --remove-destination $SCRIPT/plot_multi_converge.py ./

#####################
# cp --remove-destination $SCRIPT/analyze_* ./
#####################

chmod u+x *.py

###########################
# 初期構造をどこから始めるか？
# # convert
# ./cfg2poscar.py "$NAME" POSCAR0 Li,S,P,C
# cp --remove-destination POSCAR0.vasp POSCAR0
# cp --remove-destination $NAME.cfg aaa.cfg

# convert
# cp --remove-destination POSCAR0 aaa.vasp
# ./poscar2cfg.py aaa
###########################

#####################
# qn/TOP/FNC
# json
# cp --remove-destination $SCRIPT/fnc/SiO2_03/qn_config_sio2_fnc.json .

# make
# ./make_sio2_qn_fnc.py

# ln -sf ${NAME}_rmc_unit.top aaa.top
# ln -sf ${NAME}_rmc_fnc3.fnc aaa.fnc
#####################


chmod u+x *.py
