import optparse
import shutil

from vasp.vasp import UtilVasp
from rmc.rmc_pot import UtilRmc
from vasp.conv_vasp2cfg import conv_vasp2cfg
from Rcfg2vasp_nonLIB import conv_cfg2vasp
from x_logger.x_logger import XLogger


def run(vasp, rmc, max, logger: XLogger = None):

    _vasp = vasp
    _rmc = rmc
    print("print ",_vasp)
    print("print ",_rmc)
    print("print ",_vasp.run)
    print("print ",_rmc.run)

    # for i in range(0, max):
#    print("print o")
#    _rmc.run("aaa")
#    print("print a")
#    conv_cfg2vasp("aaa")
#    print("print b")
#    _vasp.run()
    print("print c")
    _vasp.u_conv_vasp2cfg("aaa")
    print("print d")

    # if reach_threshold():
    #     return


if __name__ == "__main__":
    from x_logger.x_logger import XLogger

    ###############################################
    ## optparse
    # parser = optparse.OptionParser()

    # parser.add_option(
    #    "-i",
    #    "--input",
    #    dest="INPUT",
    #    default=cname,
    # )
    # options, args = parser.parse_args()

    # if options.INPUT:
    #     cname = options.INPUT

    # print args,options
    # if len(args) > 0:
    #     # print "script name:",argvs[0]
    #     cname = args[0]

    logger = XLogger(log_level="debug", logger_name="kobayashi")
    max = 1
    vasp = UtilVasp(logger=logger)
    rmc = UtilRmc()
    run(vasp, rmc, max, logger)
