# Tutorial

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/tutorial.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/tutorial.html)

## Installing Packmol

`packmol_util` requires a separate Packmol executable. Install it and make `packmol` available on `PATH`, or provide its path using `AmorphousBuilder(packmol_bin="...")`.

- [Official Packmol website](https://m3g.iqm.unicamp.br/packmol/)
- [Source repository](https://github.com/m3g/packmol)
- [Source archive](https://m3g.iqm.unicamp.br/packmol/packmol.tar.gz)

Example Linux source build:

```sh
wget https://m3g.iqm.unicamp.br/packmol/packmol.tar.gz
tar xzf packmol.tar.gz
cd packmol
make
```

Example macOS build using GNU Fortran:

```sh
brew install gcc
tar xzf packmol.tar.gz
cd packmol
FC=gfortran-14 F77=gfortran-14 ./configure
make
```

Adjust the compiler name to the installed version and follow the build instructions for the selected Packmol release.

## Fe–Si–B from single-atom templates

Create three XYZ templates, each containing one atom, and register their copy counts with `AmorphousBuilder`:

```python
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz

for element in ("Fe", "Si", "B"):
    write_single_atom_xyz(f"{element}.xyz", element)

builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    mass_density=7.0,
)
for element, ratio in zip(builder.symbols, builder.ratios):
    builder.add_template(f"{element}.xyz", ratio * builder.multiplier)
builder.build("FeSiB")
```

The ratio sum is 100, so the multiplier is 10. The resulting cell contains 800 Fe, 90 Si, and 110 B atoms. The `build()` call generates the Packmol input, runs Packmol, and converts the output to POSCAR.

### Specifying number density instead

```python
builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    number_density=0.08,
)
print(builder.box_length)
```

If both `number_density` and `mass_density` are supplied, `number_density` takes precedence.

## Li3PO4 using PO4 structural units

The PO4 template is a five-atom tetrahedron. The internal P–O and O–O distances are determined by the XYZ coordinates. Packing radii control inter-template exclusion and do not modify those internal distances.

```python
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz, write_tetrahedral_unit_xyz

write_single_atom_xyz("Li.xyz", "Li")
write_tetrahedral_unit_xyz(
    filename="PO4.xyz",
    center_element="P",
    vertex_element="O",
    center_vertex_distance=1.54,
    vertex_vertex_distance=2.515,
)

builder = AmorphousBuilder(
    symbols=["Li", "P", "O"],
    ratios=[3, 1, 4],
    total_atom_count=512,
    minimum_separation=1.5,
    number_density=0.09119,
)
builder.add_template("Li.xyz", 3 * builder.multiplier)
builder.add_template(
    "PO4.xyz", builder.multiplier,
    packing_radii={"P": 0.25, "O": 1.05},
)
builder.build("Li3PO4")
```

There are 64 formula units: 192 Li atoms and 64 PO4 units (320 atoms), for 512 atoms in total. For a regular tetrahedron, the vertex–vertex distance $a$ and center–vertex distance $d$ satisfy $a=d\sqrt{8/3}$; `write_tetrahedral_unit_xyz()` checks this within `distance_tolerance`.

## Packmol input format

The following example places 80 Fe, 9 Si, and 11 B atoms in a cubic box with a 20 Å edge. This illustrative box length is not calculated from a density.

```text
tolerance 2.0
pbc 20.0 20.0 20.0
filetype xyz
output FeSiB_packmol.xyz

structure Fe.xyz
  number 80
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure

structure Si.xyz
  number 9
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure

structure B.xyz
  number 11
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure
```

### Generating and running input through lower-level APIs

```python
from packmol_util.model import write_single_atom_xyz
from packmol_util.packmol_inp import PackmolInp
from packmol_util.packmol import Packmol

for symbol in ("Fe", "Si", "B"):
    write_single_atom_xyz(f"{symbol}.xyz", symbol)

inp = PackmolInp(
    minimum_separation_distance=2.0,
    output_xyz="FeSiB_packmol.xyz",
    box_length=20.0,
    use_pbc=True,
)
for symbol, count in (("Fe", 80), ("Si", 9), ("B", 11)):
    inp.add_structure(f"{symbol}.xyz", count)
inp.write("FeSiB_packmol.inp")

runner = Packmol()
runner.run_packmol("FeSiB_packmol.inp", "FeSiB_packmol.log")
index_map = runner.xyz_to_poscar(
    xyz_file="FeSiB_packmol.xyz",
    poscar_file="POSCAR",
    packmol_inp="FeSiB_packmol.inp",
    elements=["Fe", "Si", "B"],
)
```

`run_packmol()` supplies the input file on stdin and captures stdout and stderr in the log. `xyz_to_poscar()` reads the box length from `inside box`, converts Cartesian to Direct coordinates, groups atoms by element, and returns a dictionary mapping 1-based Packmol XYZ indices to 1-based POSCAR indices.

## Density and atom counts

For number density $n$ [Å$^{-3}$] and atom count $N$, the cubic cell edge is $L=(N/n)^{1/3}$. For mass density $\rho$ [g/cm³] and mean atomic molar mass $\bar M$ [g/mol], $n=\rho N_A 10^{-24}/\bar M$.

```python
from packmol_util.packmol import Packmol
pm = Packmol()
counts = pm.compute_element_counts(["Fe", "Si", "B"], [80, 9, 11], 503)
number_density = pm.number_density_from_mass_density(
    ["Fe", "Si", "B"], [80, 9, 11], 7.35
)
length = pm.cell_length_from_number_density(500, number_density)
print(counts, length)
```

`Packmol.compute_element_counts()` preserves the requested total and allocates rounding remainders to elements with the largest fractional parts; exact ratios are not guaranteed. `AmorphousBuilder` instead adjusts `total_atom_count` to the nearest positive multiple of `sum(ratios)`, preserving stoichiometry. The adjusted total and scale factor are available as `builder.total_atom_count` and `builder.multiplier`. `model.make_atomic_mixture_recipe()` rejects totals that are not exact multiples.

## Recipes and template definitions

`StructureSpec` stores an XYZ path, the number of copies, and optional element-specific packing radii. `MaterialRecipe` groups structures with composition information. `make_material_recipe()` reads the atom count from each XYZ header and computes the total as the sum of `number × template atom count`.

```python
from packmol_util.model import make_atomic_mixture_recipe
recipe = make_atomic_mixture_recipe(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=500,
)
assert recipe.total_atom_count == 500
```

Recipes do not run Packmol by themselves. To use a recipe with `AmorphousBuilder`, register each `recipe.structures` entry through `builder.add_template()`.

## RMC_POT FNC constraints

For a PO4 XYZ template ordered as P, O, O, O, O, local indices are P=1 and O=2–5. `make_tetrahedral_unit_fnc_pairs()` generates four P–O pairs of type 1 and six O–O pairs of type 2. The builder maps these 1-based local indices through the packed XYZ ordering to the element-grouped POSCAR indices.

```python
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import (
    write_single_atom_xyz,
    write_tetrahedral_unit_xyz,
    make_tetrahedral_unit_fnc_pairs,
)

write_single_atom_xyz("Li.xyz", "Li")
write_tetrahedral_unit_xyz(
    filename="PO4.xyz",
    center_element="P",
    vertex_element="O",
    center_vertex_distance=1.54,
    vertex_vertex_distance=2.515,
)
builder = AmorphousBuilder(
    symbols=["Li", "P", "O"], ratios=[3, 1, 4],
    total_atom_count=512, minimum_separation=1.5,
    number_density=0.09119,
)
builder.add_template("Li.xyz", 3 * builder.multiplier)
builder.add_template(
    "PO4.xyz", builder.multiplier,
    packing_radii={"P": 0.25, "O": 1.05},
    fnc_pairs_in_template=make_tetrahedral_unit_fnc_pairs(),
    fnc_distance_ranges={1: (1.45, 1.65), 2: (2.40, 2.65)},
    fnc_output_constraint_types=[1, 2],
)
builder.build("Li3PO4")
```

`fnc_output_constraint_types=None` selects all types; `[1]` selects only type 1. Filtering applies only to FNC output, not to packing or template geometry. `Packmol.write_fnc_file()` requires constraint type indices to be consecutive starting at 1, so selecting `[2]` alone raises an error in the current implementation.

`make_tetrahedral_unit_fnc_spec_from_ranges()` derives representative template distances from the midpoints of FNC ranges and validates tetrahedral geometry. Its `geometry_distance_tolerance` is a geometric consistency tolerance, not an FNC distance range. `solve_packing_radii_from_pair_distances()` approximates requested element-pair minimum distances with sums of element radii; all self- and cross-pair distances are required. `pair_distance_tolerance` is an approximation allowance, not Packmol's `tolerance`. The radius solver performs a discrete search and may reject incompatible distance tables.

## Generated files and limitations

`builder.build("FeSiB")` writes `FeSiB_packmol.inp`, `FeSiB_packmol.xyz`, `FeSiB_packmol.log`, `POSCAR`, and `POSCAR.vasp`. When FNC pairs are registered, it also writes `FeSiB.fnc` by default; use `build(output_prefix, fnc_file=...)` to select another FNC path. The POSCAR filenames are fixed and are overwritten by subsequent builds in the same directory.

The sum of `template atom count × number of copies` must equal the adjusted `builder.total_atom_count`. The current builder does not validate this equality at the beginning of `build()`. The FNC index mapping depends on Packmol's template ordering and the POSCAR element regrouping. All FNC indices are 1-based.
