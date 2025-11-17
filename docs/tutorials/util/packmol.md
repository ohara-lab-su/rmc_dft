# Packmol

## 公式サイト

- [公式サイト](https://m3g.iqm.unicamp.br/packmol/)
- [公式 tar.gz (最新版)](https://m3g.iqm.unicamp.br/packmol/packmol.tar.gz)

## linux
```aiignore
wget https://m3g.iqm.unicamp.br/packmol/packmol.tar.gz
tar xzf packmol.tar.gz
cd packmol
make
```

## for Mac

```aiignore
brew install gcc
tar xzf packmol.tar.gz
cd packmol
FC=gfortran-14 F77=gfortran-14 ./configure
make
```
フォルダに対してパスを通すか、コピーして使う

## 入力ファイル(packmol.inp)


