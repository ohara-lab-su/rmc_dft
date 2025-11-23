#!/usr/bin/env python
from rmc_dft import VaspIncar

# 例: 2つの INCAR を読み込む
incar_a = VaspIncar("INCAR")
incar_b = VaspIncar("mistake/incarGGAU_1")

# 差分を取得
diff = incar_a.diff_with(incar_b)

# 結果を表示
for tag, (v1, v2) in diff.items():
    print(f"{tag}: {v1}  ->  {v2}")
