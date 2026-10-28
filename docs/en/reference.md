# Reference

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/reference.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/reference.html)

This page describes the responsibilities and behavior of the public components. The generated API documentation provides the complete signatures, type annotations, and docstrings.

## Components

| Component | Main APIs | Responsibility |
| --- | --- | --- |
| `AmorphousBuilder` | `__init__`, `multiplier`, `add_template`, `build` | End-to-end amorphous model generation |
| `PackmolInp` | `__init__`, `add_structure`, `write` | Packmol `.inp` generation |
| `Packmol` | `number_density_from_mass_density`, `mass_density_from_number_density`, `cell_length_from_number_density` | Density and cell dimensions |
| `Packmol` | `compute_element_counts`, `compute_cell_sizes`, `get_unit_atom_count` | Composition and atom counts |
| `Packmol` | `run_packmol`, `xyz_to_poscar`, `write_fnc_file`, `count_atoms_in_xyz` | Execution, conversion, FNC output |
| `model` | `write_xyz_template`, `write_single_atom_xyz`, `write_tetrahedral_unit_xyz` | XYZ template generation |
| `model` | `StructureSpec`, `MaterialRecipe`, `make_material_recipe`, `make_atomic_mixture_recipe` | Placement recipes |
| `model` | `make_tetrahedral_unit_fnc_pairs`, `make_tetrahedral_unit_fnc_spec_from_ranges`, `TetrahedralUnitFncSpec` | Tetrahedral FNC specifications |
| `model` | `solve_packing_radii_from_pair_distances` | Approximate element radii from pair distances |
| `Config` | `__init__(yaml_path=...)`, `load_yaml()` | YAML configuration |
| `param` | Atomic weights and constants | Density conversion |

## `AmorphousBuilder`

`AmorphousBuilder(symbols, ratios, total_atom_count, minimum_separation, mass_density=None, number_density=None, packmol_bin="packmol")` takes the elements, stoichiometric integer ratios, desired atom count, Packmol `tolerance`, density in g/cm³ or Å⁻³, and executable path. When both densities are given, **number density takes precedence**. The requested atom count is adjusted to the nearest positive multiple of the ratio sum.

`add_template(xyz_file, number, packing_radii=None, fnc_pairs_in_template=None, fnc_distance_ranges=None, fnc_output_constraint_types=None)` registers one structure. `number` means the **number of template copies**, not the total number of atoms in the template. FNC pairs use local 1-based atom indices. `build(output_prefix, fnc_file=None)` writes Packmol input and output, POSCAR files, and optionally FNC constraints.

## `Packmol` and `PackmolInp`

`Packmol` computes atomic weights and densities, cell sizes, and element counts; executes Packmol; converts XYZ to POSCAR; and writes RMC_POT FNC files. `compute_element_counts()` distributes rounding remainders and may not preserve exact stoichiometry. `xyz_to_poscar()` reads the first `inside box` line in the `.inp` file to determine the cubic cell edge.

`PackmolInp(minimum_separation_distance, output_xyz, box_length, use_pbc=False)` writes a cubic Packmol input. `add_structure(xyz_file, number, packing_radii_by_atom_symbol=None)` accepts optional radii keyed by element symbol; `write(inp_file)` maps them to 1-based XYZ atom indices and writes `atoms ... radius ... end atoms` blocks.

## `model`

`write_xyz_template()` writes arbitrary XYZ coordinates; `write_single_atom_xyz()` creates a one-atom template; `write_tetrahedral_unit_xyz()` creates a five-atom regular tetrahedron and validates its geometry. `make_material_recipe()` computes the atom count from XYZ headers and copy counts. `make_atomic_mixture_recipe()` requires the total count to be an exact multiple of the ratio sum. `make_tetrahedral_unit_fnc_pairs()` generates tetrahedral local FNC pairs, while `make_tetrahedral_unit_fnc_spec_from_ranges()` derives template distances from FNC distance ranges. `solve_packing_radii_from_pair_distances()` uses a discrete search for element radii compatible with a supplied pair-distance table.

## `Config` and `param`

`Config(yaml_path="settings.yaml")` loads known YAML keys into instance attributes. `Config.load_yaml("settings.yaml")` changes class attributes. With no argument, `load_yaml()` checks `PACKMOL_UTIL_CONFIG_YAML`. Omitting `yaml_path` in the constructor does not load YAML. Unknown keys are reported as `NO SUCH VAR:`. Default values are Fe–Si–B example settings and are not automatically consumed by `AmorphousBuilder`. `param` contains atomic weights and physical constants.

## Constraints

FNC types must be consecutive positive integers starting at 1. Packing radii control placement, not the geometry inside a template. `PackmolInp` uses the same cubic cell edge for `pbc` and `inside box`. `POSCAR` and `POSCAR.vasp` are fixed output filenames and can be overwritten.

## API reference

```{toctree}
:maxdepth: 2

api/modules
```

The API pages are generated from the package source during the documentation build.
