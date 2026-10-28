# Design philosophy

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/philosophy.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/philosophy.html)

## Inputs above the Packmol level

Packmol accepts structure templates, copy counts, placement regions, and minimum separation conditions. For amorphous model construction, the primary inputs are composition, total atom count, mass or number density, and molecular or structural units. `packmol_util` converts these physical specifications into Packmol input.

```text
composition / atom count / density / structural units
                       |
                  packmol_util
                       |
       structure / number / inside box / radius
                       |
                     Packmol
```

Users specify conditions as Python data rather than assembling Packmol input strings manually.

## High-level and low-level interfaces

`AmorphousBuilder` coordinates structure creation. Lower-level operations, including cell-size calculations, Packmol input generation, execution, and XYZ-to-POSCAR conversion, are available independently.

```text
AmorphousBuilder
      |
      +-- model
      +-- PackmolInp
      +-- Packmol
```

## `builder`

`AmorphousBuilder` stores the element symbols, stoichiometric ratios, desired atom count, mass or number density, minimum separation, and templates. It determines the stoichiometric multiplier and cubic cell size, registers the templates, and runs the packing workflow. `builder.multiplier` is used to determine template copy counts. Template copy counts must account for the number of atoms within each template.

## `packmol`

`Packmol` provides atomic-weight and density calculations, Packmol execution, XYZ-to-POSCAR conversion, and RMC_POT FNC file output. It does not construct molecular geometries; those are defined in XYZ templates.

## `packmol_inp`

`PackmolInp` writes the Packmol `.inp` syntax from Python values:

```text
structure ...
    number ...
    inside box ...
end structure
```

When packing radii are given by element symbol, `PackmolInp` reads the XYZ template and maps each element to the corresponding 1-based Packmol atom indices.

## `model`

`model` creates single-atom XYZ templates and multi-atom structural units such as PO4 tetrahedra. The internal geometry of a unit is distinct from the packing exclusion radii used to position units relative to one another. For example, the P–O distances inside a PO4 unit are determined by the XYZ coordinates, not by `packing_radii`.

`StructureSpec` and `MaterialRecipe` represent template placement data. `make_material_recipe()` calculates the total number of atoms by multiplying each template's atom count by its number of copies.

## Composition and atom count

The ratio `[3, 1, 4]` contains eight atoms per formula unit. `AmorphousBuilder` adjusts the requested total atom count to the nearest positive multiple of the sum of the ratios and exposes the resulting multiplier as `builder.multiplier`. `Packmol.compute_element_counts()` has different semantics: it preserves the requested total count and apportions rounding remainders across elements, potentially changing the exact ratio.

## Density and cell dimensions

For number density $n$ [Å$^{-3}$] and atom count $N$, the cubic cell edge length is

$$
L = \left(\frac{N}{n}\right)^{1/3}.
$$

For mass density $\rho$ [g/cm³], mean atomic molar mass $\bar M$ [g/mol], and Avogadro constant $N_A$, the number density is $n=\rho N_A 10^{-24}/\bar M$. Packmol receives the calculated box dimensions rather than the density itself.

## FNC constraints and atom indices

A template-local FNC pair uses 1-based indices. After Packmol places the templates, `AmorphousBuilder` maps those indices through the Packmol XYZ ordering to the element-grouped POSCAR ordering and writes the final 1-based atom indices to an RMC_POT FNC file. FNC output filtering does not change packing or template geometry. The FNC writer requires consecutive constraint types starting at 1.
