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

SPring8のBL04B2の解析ソフト（IGORマクロ）によって、全散乱測定を解析しようとすると、そのアウトプットとして、重み因子も出してくれます。
そのデータを持っていれば、計算はしなくてもいいです。
http://rud.spring8.or.jp/member/0020758/distrbution.html

# datファイル

```{code}
comment
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

以下、上から順に各行の説明です（サンプルの行番号を便宜上付けて説明します）。

1) comment
- 説明: コメント行。ファイル全体に対する簡単な説明や試料名を入れます（任意）。  

2) 0.0842566414       ! number density  
- 説明: 系の数密度（number density）。単位は原子数 / Å^3。  
- 備考: cfg ファイル中の原子数とシミュレーションボックス体積の関係で一致させる必要があります。（二重定義）

3) 1 1 1 1 1 1 ! cut offs  
- 説明: 原子種ごとのカットオフ距離（またはカットオフの有無フラグ）を指定するフィールド。サンプルは6要素になっていますが、これはシステム中のタイプ数やプログラムの内部フォーマットに依存します。  
- 実務上: 多くの実装では「最低許容距離（min separation）」や「ペアごとの距離カットオフ」を指定します。型の数 (ntypes) に応じた個数を並べる必要があります。  
- 並びは3元型の場合、11,12,13,22,23,33となっているはずです。
- n元型の場合、11,12,13,14, ... , 1n, 22, 23,...,2n, 33, 34, ..., 3n, ..., nn となるはずです。

4) 0.01 0.01 0.01   ! maximum moves  
- 説明: 原子移動の最大振幅（1 回の move での最大変位）を指定します。複数値が並んでいる場合はタイプごと、または移動タイプごとの設定になっていることがあります。単位は Å。  
- 備考: 値が小さいほど受理率が高くなるがサンプリング効率は落ちます。調整して受理率を 20–50% 程度に保つのが一般的です。

5) 0.025        ! r spacing  
- 説明: 近接分布関数 g(r) のビン幅（r の刻み幅）。単位は Å。  
- 備考: 小さいほど解像度は上がるが計算負荷が増えます。

6) .false.      ! whether to use moveout option  
- 説明: moveout オプションを使うか否かをブールで指定します（.true./.false.）。moveout は移動時の追加処理（例: 局所的最適化や移動先の制限）に関わる機能です。  
- 備考: 実装によって挙動が異なるため、マニュアルの該当項目を参照してください。

7) 0            ! number of configuration to collect  
- 説明: 収集する構成（configuration）数。0 の場合は特別扱い（例: 最終構成のみ）や収集しないことを意味する場合があります。  
- 備考: サンプルでは 0 なので構成保存を行わない設定になっています。

8) 5000         ! step for printing  
- 説明: 結果の経過出力（ログ出力）を行うステップ間隔。何ステップごとに情報をプリントするかを指定します。

9) 0 0          ! time limit, step for saving  
- 説明: 1つ目は時間制限（経過時間を使った停止条件、単位は分(minute)）、2つ目は保存のステップ間隔（何ステップごとにファイル保存するか）。  
- 備考: 両方 0 は無効/デフォルトを意味することが多いです。

10) 0 0 1 0      ! g(r), neutron, x-ray, EXAFS  
- 説明: 出力する物理量や計算フラグを並べたもの。順に g(r) の計算、中性子散乱、X線、EXAFS の計算フラグなどを意味します。  
- 例: 上記の例は「g(r) は出力しない、neutron は出力しない、x-ray を出力する、EXAFS は出力しない」（ただし順序・意味は実装依存なのでマニュアル参照）。

11) S_q_fqd_0.3_0.03_40.sq  
- 説明: sq データファイルのパス／ファイル名（先に出した S(q) データを読み込むファイル）。相対パスやフルパスで指定します。

12) 1 991  
- 説明: sq ファイルの読み込みに関する範囲指定など（例えば読み込む行の開始/終了インデックス、q インデックスの最小/最大など）。  
- 備考: 具体的な意味は RMC_POT のバージョンと入出力フォーマットによるので、マニュアルを参照してください。

13) 1.0  
- 説明: スケーリング因子（S(q) のスケール合わせに用いる係数）や正規化に関する値の可能性があります。上の sq データに対する正規化や重み付けで使われることが多いです。

14) 5E-3  
- 説明: S(q) の許容誤差（tolerance）や最小変化量の許容値などを表す数値。例えばフィッティングの収束条件や S(q) での最小分解能を指定することがあります。
- いや、たぶんこれが温度因子じゃないかな。メトロポリス法の。で、マニュアルでstatndard deviationとして示されているものじゃないかな。そうだとしたら(温度)^0.5 になる。
- マニュアルによると、「5E-3 0」、「5E-3 1」、など書き分けができて、前者ではΧ、後者ではRwを用いることになるらしい。

15) .false.  
- 説明: ブール値フラグ。例えば S(q) のバックグラウンド補正を行うか、平滑化をするかなどのフラグが入ります（正確な割当はマニュアル参照）。

16) .true.  
- 説明: 別のブールフラグ。例: データの重みを有効にする、誤差バーベースの重み付けを行う、など。

17) .false.  
18) .false.  
- 説明: 追加のブールフラグ（計4つ並ぶことで複数のオン/オフ設定を行っている）。それぞれの意味はソフトの仕様に従います。

19) 0         ! number of cos. distr of bond angles constraint, dcos_theta (spacing in cos(theta) space  
- 説明: 角度制約（bond angle distribution）の数。0 は角度分布による制約を適用しないことを意味します。カンマ以降は cos(theta) 空間での刻み幅 dcos_theta の指定に関する注記です。

20) 0  ! no of coord. constr.  
- 説明: 配位数（coordination）に基づく制約の数。0 は配位数制約を適用しないことを意味します。

21) 0         ! no of av. coord. contsr.  
- 説明: 平均配位数に関する制約数（平均的な配位数を固定/制限する制約）。0 で使用しない設定。

22) 0         ! potential  
- 説明: ポテンシャル関係のフラグか選択番号（ポテンシャルを使う/使わない、あるいはどのポテンシャルを使うかを指定）。0 はポテンシャル未使用を意味する場合が多いです。

23) 0         ! FNC switch  
- 説明: FNC（Fixed Neighbour Constraints など）スイッチ。0 はオフ。実装により異なるためマニュアル参照。

24) 0         ! initial bin shift;  
- 説明: g(r) 等の初期ビンシフト（ヒストグラムのオフセット）を指定する値。0 はシフトなし。

25) 1         ! xmax used in the run.  
- 説明: g(r) 等の計算に用いる最大 r 値（xmax）のスケーリングやフラグ。サンプルでは 1（意味は実装に依存）。

26) 1         ! number of atoms moved in a single move  
- 説明: 1 回の move で同時に移動させる原子の数。通常は 1（1 原子移動）だが、複数移動を許すことも可能。

27) 200       ! size of the history buffer  
- 説明: 履歴バッファのサイズ（過去の move 情報や受理率などを格納するバッファ）。解析用の統計に使われます。

28) 10        ! number of display update beteen each history buffering  
- 説明: 履歴バッファ更新間の表示更新回数。どの程度の頻度で進捗表示を更新するか。

29) 0         ! indicator of custom move  
- 説明: カスタムムーブ（ユーザー定義の移動アルゴリズム）を使うかどうかのインジケータ。0 で無効。

30) 0         ! whether to load the histgram form file, if posible [0:no 1:yes]  
- 説明: 既存のヒストグラムを外部ファイルからロードするか（0: ロードしない、1: ロードする）。

31) 5        ! maximum number of atoms in a gridcell  
- 説明: 空間分割（グリッドセル）あたりに許容する最大原子数。近接探索や近傍リスト作成時のパラメータ。

32) 0 0       ! frction of swaps, ntypes*(ntypes-1)/2 0 not allowded or 1 allowed for the possible mixed part  
- 説明: 交換（swap）に関する設定。最初の数値は交換の比率や制御値、2 番目の数値は swap を許可するか否か（0: 許可しない、1: 許可する）を示します。ntypes*(ntypes-1)/2 は可能な混合部分（タイプ間交換）の数に対応するという注釈です。

33) 4         ! total number of threads to use  
- 説明: 使用するスレッド数（並列度）。マシンスペックに合わせて設定してください。たぶんこれは変えたとしても、1スレッドになってしまう気がする。

---

補足と注意点
- 上記の各行の正確な順序・意味は RMC_POT（または RMC++）のバージョンや実装によって若干異なる場合があります。ここでの説明は一般的な役割と単位を示したもので、完全な仕様は公式マニュアル（https://www.szfki.hu/~nphys/rmc++/RMC_POT_user_guide.pdf）を参照してください。  
- cfg ファイル内の原子種数（ntypes）と dat ファイル中で期待される数（例えばカットオフやタイプごとのパラメータ列の要素数）は一致させる必要があります。  
- 値を変更した場合は、ログ（プリント間隔）や受理率・ビン幅等を見て適宜調整してください。特に移動最大振幅は受理率に大きく影響します。  
- sq データの重み（coeff）の計算や順序を間違えると S(q) の再現が不正確になるため、原子組成 c_i と散乱長（平均散乱長）を正しく扱ってください。
