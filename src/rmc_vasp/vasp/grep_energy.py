
# grep on python
input_file = 'OUTCAR'
output_file = 'grep-_e_0_energy_OUTCAR.txt'
key = 'energy  without entropy'

with open(output_file, 'w') as outfile:
    with open(input_file, 'r') as f:
        for line in f.readlines():
            if key in line:
                print(line)
                outfile.writelines(line)

