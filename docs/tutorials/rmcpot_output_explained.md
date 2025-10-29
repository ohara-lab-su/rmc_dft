# RMC POTのアウトプットファイルの説明

例えば、以下のようなアウトプットファイルがあります。
.fit, .ppcf

# 構造因子S(Q)へのフィッティングの状況
aaa.fit
```{code}
Calculated and experimental total data for each data sets
0	 g(r) data sets
0	 S(Q) data sets
1	 F(Q) data sets
0	 F(g) data sets
0	 E(k) data sets

Total F(Q) for data set #1/1
Renormalization factor a=	1.000000e+00
Renormalization factor b=	-1.186518e+01
Renormalization factor c=	0.000000e+00
Renormalization factor d=	0.000000e+00
           Q	          F(Q) RMC++	       renorm exp. F(Q)	  original exp. F(Q)	          background
2.635850e-01	 -1.290579277856e+00	    -1.005258621913e+01	  1.812590000000e+00	 -1.186517621913e+01
2.812760e-01	 -1.294920422437e+00	    -1.052247621913e+01	  1.342700000000e+00	 -1.186517621913e+01
2.989660e-01	 -1.299385311315e+00	    -1.094524621913e+01	  9.199300000000e-01	 -1.186517621913e+01
   :                  :                      :                      :                      :
```
このファイルはRMC POTのアウトプットファイルで、計算されたデータと実験データの比較を示しています。
13行目からは、Q値に対するF(Q)の計算結果と実験結果が並んでいます。
```math
F(Q) = S(Q) - 1 
```
ここで用いられるF(Q)は、通常表示される構造因子S(Q)から1を引いたものであることに注意してください。
この結果をプロットするときには、
S(Q)=F(Q)+1
と、してプロットします。
詳細は以下のユーザーマニュアルの式(E3)周辺を参照してください
https://www.szfki.hu/~nphys/rmc++/RMC_POT_user_guide.pdf


# 二対分布関数 gij(r)
aaa.ppcf
```{code}
This is an object of Class PPCFSet 
3	 number of atom types

For data set(s) 1
306	 number of discretization bins for the ppcf 
0.000000000	 rmin value (Angstroms)
7.650000000	 rmax value (Angstroms)
0.025000000	 discretization step (Angstroms) 

r value + 6 partial g(r) at the middle of the histogram bin
0.012500000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         0.000000000
0.037500000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         0.000000000
0.062500000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         0.000000000
0.087500000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         0.000000000
0.112500000	         0.000000000	         0.000000000	         0.000000000	         0.000000000	         
    :                    :                   :                   :                   :                   :
```
このファイルは、二対分布関数gij(r)の計算結果を示しています。
11行目からは、r値に対する各原子種間のgij(r)が並んでいます。
今、3種類の原子種を扱っているので、6つのgij(r)が表示されています。
r[Å], g11(r), g12(r), g13(r), g22(r), g23(r), g33(r)の順で表示されています。
（ユーザーマニュアル、B章最終行）


# 原子配置（3次元モデリング）
aaa.cfg

これはインプットファイルと同じ形式のものです。
シミュレーションを続けると上書きされます。
適宜、変換して、VESTAなどで可視化します。


