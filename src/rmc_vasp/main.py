from vasp.vasp import UtilVasp
from rmc.rmc_pot import UtilRmc
from x_logger.x_logger import XLogger
import os


def run(vasp, rmc, max=2, logger: XLogger = None):

    _vasp = vasp
    _rmc = rmc
    print("print ",_vasp)
    print("print ",_rmc)
    print("print ",_vasp.run)
    print("print ",_rmc.run)

    _vasp.u_conv_vasp2cfg("aaa")

    i=0
    for i in range(0, max):

        log_dir= "log" + str(i)
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
    max = 1
    vasp = UtilVasp(logger=logger)
    rmc = UtilRmc()
    run(vasp, rmc, max, logger)
