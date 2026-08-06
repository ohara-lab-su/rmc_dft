#!/usr/bin/env bash
# 最初に script 関係を指定フォルダにコピーする
# その後の　z.sh 作業は指定フォルダからのコピーとする
#
# scriptバージョン同一性の担保となる
# (module バージョンは今入れているモジュールバージョンになる)

SCRIPT="$HOME/zaiene_dev/rmc_dft/example"
#DST="$HOME/LiSPC/script"
DST="./script"

if [ ! -d "$DST" ]; then
    mkdir -p "$DST"
fi

#####################
# パラメータ群
command cp -f -- "$SCRIPT/rmc_vasp_init.py" "$DST/"
command cp -f -- "$SCRIPT/rmc_vasp_init_safe.py" "$DST/"
command cp -f -- "$SCRIPT/rmc_vasp_init_normal.py" "$DST/"
command cp -f -- "$SCRIPT/rmc_init.py" "$DST/"
command cp -f -- "$SCRIPT/rmc_vasp_script.py" "$DST/"
command cp -f -- "$SCRIPT/config.yml" "$DST/"

#####################
# 初期構造作成
# cp $SCRIPT/config.yml ./
# cp $SCRIPT/make_mass_density.py ./
# cp $SCRIPT/make_number_density.py ./
#####################

command cp -f -- "$SCRIPT/conv_poscar2cfg.py" "$DST/"
command cp -f -- "$SCRIPT/conv_cfg2poscar.py" "$DST/"

command cp -f -- "$SCRIPT/rmc.py" "$DST/"
command cp -f -- "$SCRIPT/rmc_vasp.py" "$DST/"
command cp -f -- "$SCRIPT/clean_rmc.py" "$DST/"
command cp -f -- "$SCRIPT/make_log_dirname.py" "$DST/"
command cp -f -- "$SCRIPT/plot_fit.py" "$DST/"
command cp -f -- "$SCRIPT/plot_multi_fit.py" "$DST/"
command cp -f -- "$SCRIPT/plot_multi_hst.py" "$DST/"

command cp -f -- "$SCRIPT"/analyze_* "$DST/"

chmod u+x $DST/*.py

command cp -f -- "$SCRIPT/job_hpcs2024_node1.sh" "$DST/"
command cp -f -- "$SCRIPT/job_hpcs2024_node2.sh" "$DST/"
