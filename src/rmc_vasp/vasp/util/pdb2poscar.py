
def pdb2poscar(cname: str= "aaa"):
    from ase.io import read, write
    atoms = read((str+".pdb"), format='pdb')
    write((str+".vasp"), atoms, format='vasp', direct=True)
