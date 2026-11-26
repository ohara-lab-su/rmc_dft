# Packmol による初期構造の作成

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/rmc_dft/en/tutorials/packmol.html)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/rmc_dft/ja/tutorials/packmol.html)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Frmc_dft-181717?logo=github)](https://github.com/ohara-lab-su/rmc_dft/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/rmc_dft/ja/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.ja.html)

Packmol は、指定した組成や領域に原子・分子を配置して初期構造を作成します。RMC–DFT では、この構造を通常開始時の `POSCAR0` として使えます。

```bash
rmc_dft install run
```

`make_amorphous_random.py` は `packmol_util.builder.AmorphousBuilder` と Packmol 実行ファイルを使うサンプルです。作業ディレクトリのスクリプトで元素・組成・密度・原子数を対象系に合わせて設定し、Packmol の実行環境を用意します。数密度と組成の計算例は `make_number_density.py` と `make_composition_ratio.py` にあります。

- [Packmol のソースとインストール手順](https://github.com/m3g/packmol)
- [packmol_util の入力作成と Python API](https://ohara-lab-su.github.io/packmol_util/ja/)
