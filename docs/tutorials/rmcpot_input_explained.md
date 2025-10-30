# RMCPOT のインプットファイル解説

# cfgファイル
原子配置を指定するためのcfgファイルについては、以下のドキュメントで詳しく説明しています。
(https://github.com/shimane-dev/rmc_dft/docs/tutorials/rmcpot_cfg_explained.md)

# sqファイル
```{code}
2832
Dataset measured at BL04B2
0.263585 2.81259 0.308196 0.164155 0.329761 0.0218585 0.0878205 0.0882089 
0.281276 2.3427 0.308147 0.16408 0.329845 0.0218421 0.087817 0.0882679 
0.298966 1.91993 0.308095 0.164001 0.329935 0.0218247 0.0878133 0.0883307 
0.316656 1.57281 0.30804 0.163917 0.33003 0.0218063 0.0878092 0.0883972 
0.334346 1.29722 0.307982 0.163829 0.33013 0.0217868 0.0878049 0.0884676 
0.352037 1.06632 0.307921 0.163735 0.330235 0.0217663 0.0878003 0.0885417 
0.369727 0.88715 0.307857 0.163637 0.330346 0.0217447 0.0877954 0.0886195
   :        : 
```
1列目はq[Å^-1]、
2列目は実験で得られたS(q)値、
3列目以降は重み因子を示しています。

```math
coeff_{ii} = \frac{c_i^2 \overline{b_i}^2}{\sum_{i} \sum_{j} c_i c_j \overline{b_i b_j}} \qquad , \qquad 
coeff_{ij} = \frac{c_i c_j \overline{b_i b_j}}{\sum_{i} \sum_{j} c_i c_j \overline{b_i b_j}}
```
公式マニュアル　https://www.szfki.hu/~nphys/rmc++/RMC_POT_user_guide.pdf
のE3を参照してください。
Faber-Ziman型部分構造因子S_ij(q)を通して、全体のS(q)を構成するときに用いられる形式になります。
T. E. Faber　& J. M. Ziman, 1964, DOI: https://doi.org/10.1080/14786436508211931

# datファイル

```{code}
comment sio2 
0.0842566414       ! number density
1 1 1 1 1 1 ! cut offs
0.01 0.01 0.01   ! maximum moves
0.025        ! r spacing
.false.      ! whether to use moveout option
0            ! number of configurration to collect
5000         ! step for printing
0 0          ! time limit, step for saving
0 0 1 0      ! g(r), neutron, x-ray, EXAFS
S_q_fqd_0.3_0.03_40.sq
1 991
1.0
5E-3
.false.
.true.
.false.
.false.
0         ! number of cos. distr of bond angles constraint, dcos_theta (spacing in cos(theta) space
0  ! no of coord. constr.
0         ! no of av. coord. contsr.
0         ! potential
0         ! FNC switch
0         ! initial bin shift;
1         ! xmax used in the run.
1         ! number of atoms moved in a single move
200       ! size of the history buffer
10        ! number of display update beteen each history buffering
0         ! indicator of custom move
0         ! whether to load the histgram form file, if posible [0:no 1:yes]
5        ! maximum number of atoms in a gridcell
0 0       ! frction of swaps, ntypes*(ntypes-1)/2 0 not allowded or 1 allowed for the possible mixed part
4         ! total number of threads to use
```

1行目
```{code}
comment sio2
```
コメントです。


```{code}
```


```{code}
```


```{code}
```


```{code}
```


```{code}
```


```{code}
```


```{code}
```


```{code}
```

