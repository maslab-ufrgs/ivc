from optparse import OptionParser, OptionGroup
import logging, sys
from vehicleTyper import VehicleTyper, StrictVehicleTyper

class Application(object):
    DEFAULT_LOG_FILE = 'vehicletyper.log'
    LOGGER_NAME = 'vehicletyper'
    
    logger = None
    cmdLineOptions = None
    port = None
    netFile = None
    network = None
    
    def __init__(self,argv):
    
        self.logger = logging.getLogger(self.LOGGER_NAME)
        (self.cmdLineOptions, args) = self.__readOptions(argv)
        self.__initOptions(self.cmdLineOptions)        
        self.logger.info('Finished parsing command line parameters.')
        
        if self.cmdLineOptions.factor != 0:
            typer = StrictVehicleTyper(
                 self.cmdLineOptions.typesInput,
                 self.cmdLineOptions.routeFiles
            )
            self.logger.info('Using strict typing.')
            typer.setProportion(self.cmdLineOptions.factor)
            
            
        else:
            typer = VehicleTyper(
                 self.cmdLineOptions.typesInput,
                 self.cmdLineOptions.routeFiles
            )
            self.logger.info('Using noisy typing')
        self.logger.info('Finished parsing input file.')
        
        typer.writeOutput(self.cmdLineOptions.outputFile)
        self.logger.info('Finished writing output')
        
        
        
    def __readOptions(self, argv):
        """Reads and verifies command line options.
        """
        parser = OptionParser()
        self.__registerOptions(parser)
        (options, args) = parser.parse_args(argv)
        self.__checkOptions(options, args, parser)
        
        return (options, args)
    
    
    def __registerOptions(self, parser):
        
        
        parser.add_option(
          '-t','--types-input', dest='typesInput', type='string',
          default=None, help = 'the xml file with the types ammount definition'
        )
        
        parser.add_option(
            '-r', '--route-files', dest='routeFiles',
            help='Load vehicles from given files.',
            type='string', default=[], action='callback',
            callback=parse_list_to('routeFiles'),
            metavar='FILES'
        )
        
        parser.add_option(
          '-o','--output-file', dest='outputFile', type='string',
          default='vehicles.rou.xml', help = '.rou.xml output file name'
        )
        
        parser.add_option(
          '-f','--factor', type='int',
          default=0, help = 'Generates the exact proportion defined in .vtp.xml multiplied by this factor'
        )
        
        logging = OptionGroup(parser, 'Logging')
        logging.add_option('--log.level', dest='logLevel', default='INFO',
                           help='level of messages logged: DEBUG, INFO, '
                                'WARNING, ERROR or CRITICAL (with decreasing '
                                'levels of detail) [default: %default]')
        logging.add_option('--log.file', dest='logFile', metavar='FILE',
                           help='File to receive log output [default: ]'
                                + self.DEFAULT_LOG_FILE)
        logging.add_option('--log.stdout', dest='logStdout', 
                           action='store_true', default=True, 
                           help='Write log to the standard output stream.')
        logging.add_option('--log.stderr', dest='logStderr',
                           action='store_true', default=False,
                           help='Write log to the standard error stream.')
        parser.add_option_group(logging)
        
    def __initOptions(self, options):
        """Initializes the command-line options.
        
        All attributes initialized are directly from
        the command line options added by __registerOptions.
        """
        # Initialize logging
        if options.logStdout:
            handler = logging.StreamHandler(sys.stdout)
        elif options.logStderr:
            handler = logging.StreamHandler(sys.stderr)
        else:
            handler = logging.FileHandler(options.logFile or self.DEFAULT_LOG_FILE)

        self.logger.setLevel(options.logLevel)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(module)s - %(message)s"))
        self.logger.addHandler(handler)
        
        
        
    def __checkOptions(self, options, args, parser):
        if options.typesInput == None:
            parser.error("The option '-t' or '--types-input' is required.")
        
            
        if len(options.routeFiles) == 0:
            parser.error('At least one route file is required, none was given.')

        # Only one of the logging output options may be used at a time
        if len( filter(None, (options.logFile, 
                             options.logStdout, 
                             options.logStderr)) ) > 1:
            parser.error("No more than one logging output may be given.")

        # Verify the logging level
        strLevel = options.logLevel
        options.logLevel = getattr(logging, strLevel, None)
        if not isinstance(options.logLevel, int):
            parser.error('Invalid log level: %s', strLevel)
            
def parse_list_to(dest):
    """Creates a callback to parse a comma-separated list into dest.

    The returned function can be used as a callback for an
    OptionParser, and it takes the string value and splits
    it on commas.

    The resulting list is assigned to the attribute of the
    options object, identified by dest.
    """
    def callback(options, opt_str, value, parser):
        setattr(parser.values, dest, value.split(','))

    return callback