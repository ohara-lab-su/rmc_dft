#!/usr/bin/env bash

#NAME="SiO2_750_S1_nvt4"
# NAME="D1100"

SCRIPT="$HOME/zaiene_dev/packmol_util/example"
#DATA="$HOME/SiO2/data"
# DATA="$HOME/LiSPC/data"

# cp -r $SCRIPT/fnc/SiO2_03/* .
#cp -r $SCRIPT/LiSPC/data/* .

# 一部ファイルを上書きする(こっちのほうが優先)
# cp -r $DATA/* .

cp $SCRIPT/make_amorphous_random.py ./
cp $SCRIPT/make_mass_density.py ./
cp $SCRIPT/make_number_density.py ./

chmod u+x *.py