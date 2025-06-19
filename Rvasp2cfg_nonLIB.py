#!/usr/bin/env python
# K.NAKADA, kengo.nakada@gmail.com
#
# convert from VASP POSCAR file to RMC_POT cfg file
# python3 ./Rvasp2cfg_nonLIB2025.py input_file_name_without_extention
################################################################################
# 2025.06.19
# vasp -> cfg
#
# 2018.08.17
#  Python2/3 両対応
#
# 2014.10.08
#    Rvasp2cfg.py に仕様を合わせる
#    --> オプション関係を追加
#
# 2014.10.01
#    1st version
#
################################################################################
from __future__ import print_function

################################################################################

import sys
import os
import optparse

# from numpy import *
import numpy as np


###############################################
## default name
##
cname = "igzo"  # INPUT BASE filename


###############################################
## optparse
parser = optparse.OptionParser()

parser.add_option(
    "-i",
    "--input",
    dest="INPUT",
    default=cname,
)
options, args = parser.parse_args()

if options.INPUT:
    cname = options.INPUT

# print args,options
if len(args) > 0:
    # print "script name:",argvs[0]
    cname = args[0]

if cname:
    print("INPUT file name :", cname + ".vasp")
    print("OUTPUT file name:", cname + ".cfg")

if not os.path.exists(cname + ".vasp"):
    sys.exit(cname + ".vasp file not found")


# def readcfg():
###############################################
# comment
# ntype
# type
# natom
# t1_x,t1_y,t1_z
# t2_x,t2_y,t2_z
# t3_x,t3_y,t3_z
# position


###############################################
## Open vasp file
##
tmp = open(cname + ".vasp")
datfile = tmp.read()
tmp.close
datlines = datfile.split("\n")


###############################################
## Read Header
##

#t = datlines[7].split()
#natom = t[0]
natom = sum(list(map(int,datlines[6].split())))

#t = datlines[8].split()
#ntype = t[0]
ntype = len(list(map(int,datlines[6].split())))

## We don't construct fixed molecule.
#nmoles = datlines[9]
#angles = datlines[10]


###############################################
## Read Lattice Vector
##
v = datlines[2].split()
t1_x = float(v[0])  # lattice constant/2
t1_y = float(v[1])
t1_z = float(v[2])

v = datlines[3].split()
t2_x = float(v[0])
t2_y = float(v[1])
t2_z = float(v[2])

v = datlines[4].split()
t3_x = float(v[0])
t3_y = float(v[1])
t3_z = float(v[2])



###############################################
## Read Atoms
##
#lines = 17
#type = np.zeros((int(ntype) + 1))
#for i in range(int(ntype)):
#    lines += 1
#    n = datlines[lines].split()
#    type[i] = n[0]
#    lines += 1
#    tmp = datlines[lines]
#    lines += 1
#    tmp = datlines[lines]
#    lines += 1
#    tmp = datlines[lines]
type = list(map(int,datlines[6].split()))  # length is different from original deffinition
###############################################
## Read Internal Coordinate
##
position = np.zeros((int(natom) + 1, 3)) # final row is dummy
lines=7
for i in range(int(natom)):
    lines += 1
    xyz = datlines[lines].split()
    position[i, 0] = xyz[0]
    position[i, 1] = xyz[1]
    position[i, 2] = xyz[2]
# print position[i,0], position[i,1], position[i,2]


###############################################
## DATA convert
##
t1_x = t1_x * 0.5
t1_y = t1_y * 0.5
t1_z = t1_z * 0.5

t2_x = t2_x * 0.5
t2_y = t2_y * 0.5
t2_z = t2_z * 0.5

t3_x = t3_x * 0.5
t3_y = t3_y * 0.5
t3_z = t3_z * 0.5

for i in range(int(natom)):
    position[i, 0] = position[i, 0] * 2 - 1
    position[i, 1] = position[i, 1] * 2 - 1
    position[i, 2] = position[i, 2] * 2 - 1

###############################################
## OUTPUT for cfg
cfg = open(cname + ".cfg", "w")

print(" (Version 3 format configuration file) !file created by SimpleCfg::save !", file=cfg)
print("comment", file=cfg)
print("", file=cfg)
print("", file=cfg)
print("                0               0               0 moves generated, tried, accepted", file=cfg)
print("          0              configurations saved", file=cfg)
print("", file=cfg)
print("      %d molecules of all types"%natom, file=cfg)
print("          %d types of molecules "%ntype, file=cfg)
print("          1 is the largest number of atoms in a molecule ", file=cfg)
print("          0 Euler angles are provided ", file=cfg)
print(" ", file=cfg)
print("          F (box is cubic)	", file=cfg)
print("            Defining vectors are: ", file=cfg)
print("             %13.9f %13.9f %13.9f" % (t1_x, t1_y, t1_z), file=cfg)
print("             %13.9f %13.9f %13.9f" % (t2_x, t2_y, t2_z), file=cfg)
print("             %13.9f %13.9f %13.9f" % (t3_x, t3_y, t3_z), file=cfg)
print("", file=cfg)

for i in range(ntype):
    print("       %d molecules of type  %d"%(type[i],(i+1)), file=cfg)
    print("          1 atomic sites ", file=cfg)
    print("              0.000000   0.000000   0.000000", file=cfg)
    print("", file=cfg)


for i in range(int(natom)):
    print(
        " %13.9f %13.9f %13.9f" % (position[i, 0], position[i, 1], position[i, 2]),
        file=cfg,
    )

cfg.close()
