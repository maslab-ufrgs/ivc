'''
Created on 05/10/2012

@author: artavares
'''

import sys, logging
from optparse import OptionParser, OptionGroup
from iterations import Iterations
import configparser

def readOptions(argv):
    """
    Reads and verifies command line options.
    
    """
    parser = OptionParser()
    registerOptions(parser)
    (options, args) = parser.parse_args(argv)
    checkOptions(options, args, parser)
    initOptions(options)
    
    return (options, args)

    
def registerOptions(parser):
    """
    Registers the options used in the experiment
    
    """
    parser.add_option(
      '-p', '--port', dest='port', type='int',
      default = Iterations.DEFAULT_PORT,
      help = 'the port used to communicate with the TraCI server'
    )
    
    parser.add_option(
        '-r', '--route-files', dest='maindemand',
        help='files defining the main drivers, the ones participating in the experiment',
        type='string', default=[], action='callback',
        callback=_parse_list_to('maindemand'),
        metavar='FILES'
    )
    
    parser.add_option(
      '-n','--net-file', dest='netfile', type='string',
      default=None, help = 'the .net.xml file with the network definition'
    )
    
    parser.add_option(
      '-i','--iterations', dest='iterations', type='int',
      default=50, help = 'the number of iterations in the experiment'
    )
    
    parser.add_option(
      '-s','--sumo-path', dest='sumopath', type='string',
      default=None, help = 'path to call the sumo executable'
    )
    
    parser.add_option(
      '-w','--warm-up-time', dest='warmuptime', type='int',
      default=0, help = 'the number of timesteps needed to the road network achieve a steady state'
    )
    
    parser.add_option(
      '-a','--aux-demand', dest='auxdemand', type='string',
      default=None, help = '.rou.xml file with the auxiliary demand to populate the road network'
    )
    
    parser.add_option(
      '-o','--outputprefix', dest='outputprefix', type='string',
      default=None, help = 'prefix of output files to be written with the statistics'
    )
    
    parser.add_option(
        "-g", "--usegui", action="store_true",
        default=False, help="activate graphical user interface"
    )
    
    parser.add_option(
        "-u", "--uncoordinated", action="store_true",
        default=False, help="whether the malicious agents will not be cooperative among themselves"
    )
    
    parser.add_option('-c','--config-file',
        default=None, help="loads experiment configuration from a file"
    )
    
    parser.add_option(
        "--commrange", type="int",
        default=200, help="The communication commrange"
    )
    
    parser.add_option(
        "--cheatvalue", type="int",
        default=None, help="The value that cheater will tell others. Default: 3 x free-flow travel time"
    )
    
    parser.add_option(
        "--beta", type="int",
        default=15, help="The factor that adjusts how fast the gamma function will decay"
    )
    
    parser.add_option(
        "--ivcfreq", type="int",
        default=2, help="How often (in timesteps) drivers will perform IVC"
    )
    
    parser.add_option(
        "--nogamma", action="store_true",
        default=False, help="deactivate info decay with its age"
    )
    
    
    logging = OptionGroup(parser, 'Logging')
    logging.add_option('--log.level', dest='logLevel', default='INFO',
                       help='level of messages logged: DEBUG, INFO, '
                            'WARNING, ERROR or CRITICAL (with decreasing '
                            'levels of detail) [default: %default]')
    logging.add_option('--log.file', dest='logFile', metavar='FILE',
                       help='File to receive log output [default: ]'
                            + Iterations.DEFAULT_LOG_FILE)
    logging.add_option('--log.stdout', dest='logStdout', 
                       action='store_true', default=True, 
                       help='Write log to the standard output stream.')
    logging.add_option('--log.stderr', dest='logStderr',
                       action='store_true', default=False,
                       help='Write log to the standard error stream.')
    parser.add_option_group(logging)
    


def initOptions(options):
        """
        Initializes the command-line options.
        
        All attributes initialized are directly from
        the command line options added by __registerOptions.
        
        """
        # Initialize logging
        if options.logStdout:
            handler = logging.StreamHandler(sys.stdout)
        elif options.logStderr:
            handler = logging.StreamHandler(sys.stderr)
        else:
            handler = logging.FileHandler(options.logFile or Iterations.DEFAULT_LOG_FILE)
        
        logger = logging.getLogger(Iterations.LOGGER_NAME)
        logger.setLevel(options.logLevel)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(module)s - %(message)s"))
        logger.addHandler(handler)
        
        # Initialize the port and road network, if a network file was supplied
#        self.port = options.port or Iterations.DEFAULT_PORT
#        self.auxDemandFile = options.auxdemand
#        self.netfile = options.netfile
#        self.activateGui = options.usegui
        
        
def checkOptions(options, args, parser):
#    if len(options.maindemand) == 0:
#        parser.error('At least one route file is required, none was given.')
    
#    if options.netfile is None:
#        parser.error('Network file required.')

    # Only one of the logging output options may be used at a time
    if len( filter(None, (options.logFile, 
                         options.logStdout, 
                         options.logStderr)) ) > 1:
        parser.error("No more than one logging output shall be given.")

    # Verify the logging level
    strLevel = options.logLevel
    options.logLevel = getattr(logging, strLevel, None)
    if not isinstance(options.logLevel, int):
        parser.error('Invalid log level: %s', strLevel)
        
        
def _parse_list_to(dest):
    """
    Creates a callback to parse a comma-separated list into dest.

    The returned function can be used as a callback for an
    OptionParser, and it takes the string value and splits
    it on commas.

    The resulting list is assigned to the attribute of the
    options object, identified by dest.
    
    """
    def callback(options, opt_str, value, parser):
        setattr(parser.values, dest, value.split(','))

    return callback        



if __name__ == '__main__':
    (options, args) = readOptions(sys.argv)
    
    logger = logging.getLogger(Iterations.LOGGER_NAME)
    logger.info('Finished parsing command line parameters.')
    if options.config_file:
        cfg = configparser.ConfigParser(options.config_file)
    else:
        cfg = options
    
    experiment = Iterations(
        cfg.netfile, 
        cfg.maindemand, 
        cfg.auxdemand, 
        cfg.outputprefix,
        cfg.port, 
        cfg.usegui, 
        cfg.iterations,
        cfg.first_iter, 
        cfg.warmuptime,
        cfg.warmupload,
        cfg.uncoordinated,
        cfg.commrange,
        cfg.beta,
        cfg.cheatvalue,
        cfg.ivcfreq,
        cfg.nogamma,
        cfg.summary_prefix,
        cfg.routeinfo_prefix,
        cfg.mal_strategy,
        cfg.use_lk,
        cfg.sumopath
    )
    #self.coordinated = True
    #self.sumopath = None
    #print cfg.first_iter
    experiment.run(cfg.first_iter)
    