#!/usr/bin/env bash
#
#
server="zaiene-hpcs2024"
dst_dir="zaiene_dev/rmc_vasp/"

rsync -avz -e ssh --delete ./ "$server:~/$dst_dir"
