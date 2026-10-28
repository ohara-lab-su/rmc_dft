# README

基本的に RMC_DFT (rmc_vasp) は module として用いる
一番単純には

```python
#!/usr/bin/env python
import os
import shutil
from config import Config

from rmc_dft import Vasp, VaspLog, RmcPot, RmcPotLog, RmcDft
from x_logger import XLogger


if __name__ == "__main__":
    logger = XLogger(log_level="debug", logger_name="rmc_vasp_run")
    config = Config()

    # POSCAR to CFG (rmc用のCFG変換)
    cfg_name = "aaa"

    rmc_dft = RmcDft(
        rmc_code="RmcPot",
        dft_code="Vasp",
        # cfg_name="aaa",
        max_rmc_dft_loop=3,
        config=config,
        logger=logger,
    )

    # RMCの初期構造をPOSCAR から作る
    shutil.copyfile("input/POSCAR", "POSCAR")
    poscar2cfg(cfg_name=cfg_name)

    rmc_dft.run(mode="local", cfg_name=cfg_name)
```
となる
 
- rmc_code: 用いるRMCコード (現在は RmcPot のみ対応)
- dft_code: 用いるDFTコード (現在は Vasp のみ対応)