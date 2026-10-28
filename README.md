# packmol_util

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/README.ja.md)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Fpackmol_util-181717?logo=github)](https://github.com/ohara-lab-su/packmol_util/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/packmol_util/en/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.en.html)



A **Python utility kit for automatically generating amorphous initial structures (POSCAR)** for first-principles calculations (VASP) and molecular dynamics (MD) simulations using Packmol.

By specifying only the stoichiometric ratio, density (mass density or number density), and total number of atoms, this tool automatically completes the full workflow: generating the Packmol input file, running Packmol, and outputting a POSCAR in VASP format with Direct coordinates.

---

## 💡 Features

1. **Intuitive density specification**
   - Packmol itself does not interpret density or atomic weights, but this tool performs the required internal calculations and determines the cubic cell length $L$ that satisfies the specified density.
2. **Exclusion radius specification by element symbol**
   - This hides Packmol's inconvenient atom-index-based specification inside XYZ files. Interatomic avoidance distances can be controlled using an intuitive element-name-based dictionary, such as `{"P": 0.25, "O": 1.05}`.
3. **Preservation of molecular units (geometries)**
   - For systems such as $\text{Li}_3\text{PO}_4$, amorphization through mixing and packing can be performed while preserving intramolecular bond lengths, such as those in $\text{PO}_4$ tetrahedra.
4. **Extremely simple high-level API**
   - By using `AmorphousBuilder`, the cumbersome file relay workflow (`.inp` construction $\rightarrow$ external execution $\rightarrow$ coordinate conversion) can be condensed into only a few lines of script.

---

## 📁 Directory structure

```text
src/
├── packmol_util/
│
│   ├── __init__.py          # Package initialization file
│   ├── builder.py           # High-level integrated builder (AmorphousBuilder) ★NEW
│   ├── model.py             # Template XYZ generation and structure-definition module
│   ├── packmol.py           # Core density calculation, Packmol execution, and POSCAR conversion
│   ├── packmol_inp.py       # Parsing engine for constructing packmol.inp
│   ├── param.py             # Atomic weights and physical constants for the periodic table

└── example/                 # Location for material-specific generation scripts
    ├── Li3PO4/
    │   └── make_Li3PO4.py
    └── FeSiB/
        └── make_FeSiB.py
```

## Example

```python
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz

for symbol in ("Fe", "Si", "B"):
    write_single_atom_xyz(f"{symbol}.xyz", symbol)

builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"], ratios=[80, 9, 11],
    total_atom_count=500, minimum_separation=2.0,
    mass_density=7.35,
)
for symbol, ratio in zip(builder.symbols, builder.ratios):
    builder.add_template(f"{symbol}.xyz", ratio * builder.multiplier)
builder.build("FeSiB")
```

The outputs are `FeSiB_packmol.inp`, `FeSiB_packmol.xyz`, `FeSiB_packmol.log`, `POSCAR`, and `POSCAR.vasp`. An `.fnc` file is written when FNC pairs are registered. The POSCAR filenames are fixed. `AmorphousBuilder` adjusts the requested atom count to a nearby integer multiple of the stoichiometric ratio sum when needed.

## Packmol and documentation

The Packmol executable must be installed separately. See the [English tutorial](https://ohara-lab-su.github.io/packmol_util/en/tutorial.html) for installation and input format, the [reference](https://ohara-lab-su.github.io/packmol_util/en/reference.html) for API and FNC details, and the [design philosophy](https://ohara-lab-su.github.io/packmol_util/en/philosophy.html) for component responsibilities.
