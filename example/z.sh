#!/usr/bin/env bash

#NAME="SiO2_750_S1_nvt4"
NAME="D1100"

SCRIPT="$HOME/zaiene_dev/rmc_dft/example"
#DATA="$HOME/SiO2/data"
DATA="$HOME/LiSPC/data"

# cp -r $SCRIPT/fnc/SiO2_03/* .
#cp -r $SCRIPT/LiSPC/data/* .

# 一部ファイルを上書きする(こっちのほうが優先)
cp -r $DATA/* .

#####################
# パラメータ群
cp $SCRIPT/rmc_vasp_init.py ./
cp $SCRIPT/rmc_vasp_init_safe.py ./
cp $SCRIPT/rmc_vasp_init_normal.py ./
cp $SCRIPT/rmc_init.py ./
cp $SCRIPT/rmc_vasp_script.py ./

#####################
# 初期構造作成
# cp $SCRIPT/config.yml ./
# cp $SCRIPT/make_mass_density.py ./
# cp $SCRIPT/make_number_density.py ./
#####################

cp $SCRIPT/rmc.py ./
cp $SCRIPT/rmc_vasp.py ./
cp $SCRIPT/clean_rmc.py ./
cp $SCRIPT/make_log_dirname.py ./
cp $SCRIPT/plot_fit.py ./
cp $SCRIPT/plot_multi_fit.py ./
cp $SCRIPT/plot_multi_hst.py ./

#####################
# cp $SCRIPT/analyze_* ./
#####################

chmod u+x *.py

###########################
# 初期構造をどこから始めるか？
# # convert
# ./cfg2poscar.py "$NAME" POSCAR0 Li,S,P,C
# cp POSCAR0.vasp POSCAR0
# cp $NAME.cfg aaa.cfg

# convert
cp POSCAR0 aaa.vasp
./poscar2cfg.py aaa
###########################

#####################
# qn/TOP/FNC
# json
# cp $SCRIPT/fnc/SiO2_03/qn_config_sio2_fnc.json .

# make
# ./make_sio2_qn_fnc.py

# ln -sf ${NAME}_rmc_unit.top aaa.top
# ln -sf ${NAME}_rmc_fnc3.fnc aaa.fnc
#####################


chmod u+x *.py