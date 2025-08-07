from vasp.vasp import UtilVasp
from rmc.rmc_pot import UtilRmc
from x_logger.x_logger import XLogger
import os


def run(vasp, rmc, max=2, logger: XLogger = None):

    # require
    # INCAR, KPOINTS, POTCAR,
    # aaa.vasp, XDATCAR (same data). (As of 2025-08-07, it should be created by hand using Packmol.)
    # Also, high precision cell length need to be set (manually) from "number density".
    # aaa.dat, ???.??? (e.g. Hg.sq specified in aaa.dat)

    _vasp = vasp
    _rmc = rmc
    print("print ",_vasp)
    print("print ",_rmc)
    print("print ",_vasp.run)
    print("print ",_rmc.run)

    _vasp.u_conv_vasp2cfg("aaa")
    # This doesn't work because the vasp module is not imported correctly ???
    # put both aaa.vasp and XDATCAR (same data).
    # (aaa.vasp and XDATCAR) -> aaa.cfg

    # At this stage, maybe it is possible to create label.txt from aaa.vasp. Or store it  in a class.
    _vasp.u_get_label("aaa.vasp")

    i=0
    for i in range(0, max):

        log_dir= "log" + str(i)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        
        print("rmc"+ str(i))
        _rmc.run("aaa")
        _rmc.u_rmc_log()
        _rmc.u_rmc_copy(log_dir)
        
        print("cfg2vasp"+ str(i))
        _rmc.u_conv_cfg2vasp("aaa")

        print("vasp"+ str(i))
        _vasp.run()
        _vasp.u_vasp_log()
        _vasp.u_vasp_copy(log_dir)
        
        print("vasp2cfg"+ str(i))
        _vasp.cp_XDATCAR("aaa")
        _vasp.u_conv_vasp2cfg("aaa")
        print("loop end "+ str(i))

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
    max = 2
    vasp = UtilVasp(logger=logger)
    rmc = UtilRmc()
    run(vasp, rmc, max, logger)
