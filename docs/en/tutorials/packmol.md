# Preparing initial structures with Packmol

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/rmc_dft/en/tutorials/packmol.html)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/rmc_dft/ja/tutorials/packmol.html)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Frmc_dft-181717?logo=github)](https://github.com/ohara-lab-su/rmc_dft/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/rmc_dft/en/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.en.html)

Packmol places atoms or molecules in a region to generate an initial structure with the desired composition. A combined RMC–DFT run can use the resulting structure as `POSCAR0`.

```bash
rmc_dft install run
```

`make_amorphous_random.py` uses `packmol_util.builder.AmorphousBuilder` and the Packmol executable. Edit the copied script to set the elements, composition, density, and atom count for your system, and make the Packmol executable available. See `make_number_density.py` and `make_composition_ratio.py` for number-density and composition calculations.

- [Packmol source and installation instructions](https://github.com/m3g/packmol)
- [packmol_util input preparation and Python API](https://ohara-lab-su.github.io/packmol_util/en/)
