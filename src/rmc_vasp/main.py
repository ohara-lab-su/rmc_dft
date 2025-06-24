import shutil

from vasp.vasp import UtilVasp
from rmc.rmc_pot import UtilRmc
from vasp.conv_vasp2cfg import conv_vasp2cfg
from Rcfg2vasp_nonLIB import conv_cfg2vasp


def get_main():
    ###############################################
    ## optparse
    # parser = optparse.OptionParser()
    #
    # parser.add_option(
    #     "-n",
    #     "--num",
    #     dest="INPUT",
    #     default=cname,
    # )
    # options, args = parser.parse_args()
    #
    # if options.INPUT:
    #     cname = options.INPUT
    #
    #if len(args) > 0:
    #    cname = int(args[0])
    #    return cname
    #else:
    #    return 1000
    return 2


def run(max: int = 1000):
    vasp = UtilVasp()
    rmc = UtilR

    # for i in range(0, max):
    vasp.run()
    vasp.conv_vasp2cfg("aaa")
    rmc_run("aaa")
    conv_POSCAR2vasp("aaa.vasp")
    conv_cfg2vasp("aaa")

    # if reach_threshold():
    #     return


if __name__ == "__main__":
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

    num = get_main()
    run(num)
