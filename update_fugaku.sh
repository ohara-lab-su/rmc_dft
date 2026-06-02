#!/usr/bin/env bash
#
#
server="fugaku"
dst_dir="rmc_dft/"

# ローカルからリモートへ同期
# rsync -avz -e ssh --delete ./ "$server:~/$dst_dir"
rsync -avz -e ssh ./ "$server:~/$dst_dir"

# 転送先で pip install . を実行
# ssh "$server" "cd ~/$dst_dir && ~/.pyenv/shims/pip install ."
