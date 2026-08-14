#!/usr/bin/env bash
# 最初に script 関係を指定フォルダにコピーする
# その後の　z.sh 作業は指定フォルダからのコピーとする
#
# scriptバージョン同一性の担保となる
# (module バージョンは今入れているモジュールバージョンになる)

SCRIPT="$HOME/zaiene_dev/rmc_dft/example"
#DST="$HOME/LiSPC/script"
DST="./script"

rm -rf "$DST"
mkdir -p "$DST"
# if [ ! -d "$DST" ]; then
#     mkdir -p "$DST"
# fi

#####################
# パラメータ群
cp $SCRIPT/rmc_vasp_init.py $DST/
cp $SCRIPT/rmc_vasp_init_safe.py $DST/
cp $SCRIPT/rmc_vasp_init_normal.py $DST/
cp $SCRIPT/rmc_init.py $DST
cp $SCRIPT/rmc_vasp_script.py $DST/
cp $SCRIPT/config.yml $DST/

#####################
# 初期構造作成
# cp $SCRIPT/config.yml ./
# cp $SCRIPT/make_mass_density.py ./
# cp $SCRIPT/make_number_density.py ./
#####################

cp $SCRIPT/conv_poscar2cfg.py $DST/
cp $SCRIPT/conv_cfg2poscar.py $DST/

cp $SCRIPT/rmc.py $DST/
cp $SCRIPT/rmc_vasp.py $DST/
cp $SCRIPT/clean_rmc.py $DST/
cp $SCRIPT/make_log_dirname.py $DST/
cp $SCRIPT/plot_fit.py $DST/
cp $SCRIPT/plot_multi_fit.py $DST/
cp $SCRIPT/plot_multi_hst.py $DST/

cp $SCRIPT/analyze_* $DST/

chmod u+x $DST/*.py

cp $SCRIPT/job_hpcs2024_node1.sh $DST/
cp $SCRIPT/job_hpcs2024_node2.sh $DST/
