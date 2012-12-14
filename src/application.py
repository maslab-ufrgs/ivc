from optparse import OptionParser, OptionGroup
import logging, sys, os
import traci, sumolib
from drivers import Drivers
import collections
from drivers import StandardDriver

#looks up on ../lib to import Guilherme's implementation of Dijkstra algorithm
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
if not path in sys.path: sys.path.append(path)

from search import dijkstra

class Application(object):
    """Application object. Manages the command-line options and 
    controls the execution flow"""
    
    DEFAULT_PORT = 8813
    DEFAULT_LOG_FILE = 'netpopulate.log'
    LOGGER_NAME = 'netpopulate'
    
    DEFAULT_ITERATIONS = 50
    
    options = None
    port = None
    netFile = None
    network = None
    drivers = None
    roadNetwork = None
    traciClient = None
    commRange   = 100
    
    infoAge = collections.defaultdict(dict)
    knownTT = collections.defaultdict(dict)
    msgTT   = collections.defaultdict(dict)
    msgAge  = collections.defaultdict(dict)
    fleetLinks = []
    
    def __init__(self,argv):
        self.logger = logging.getLogger(self.LOGGER_NAME)
        (self.options, args) = self.__readOptions(argv)
        self.__initOptions(self.options)        
        self.logger.info('Finished parsing command line parameters.')
        
        try:
            self.roadNetwork = sumolib.net.readNet(self.options.netFile)
        except IOError as err:
            print 'Error reading roadNetwork file:', err
            sys.exit(1)
            
        self.drivers = Drivers(self.options.routeFiles,self.roadNetwork)
        self.traciClient = traci
        
        for d in self.drivers.getDriverList():
            for l in self.roadNetwork.getEdges():
                #estimates travel time in a way that 1st route selection will be greedy regarding no. of lanes
                #TODO: estimate TT as fftt
                self.infoAge[d.getId()][l.getID()] = sys.maxsize
                self.knownTT[d.getId()][l.getID()] = 100000#l.getLength() * 1000 / l.getLaneNumber()
        #dump_matrix(self.infoAge)
        #dump_matrix(self.knownTT)        
        
    def calculateRoutes(self,tripNo):
        """
        Calculates routes and adds vehicles in SUMO for each driver.
        Also, records the links used by the self-interested fleet
        """
        currentTs = traci.simulation.getCurrentTime() / 1000
        self.fleetLinks = [] #resets the list of links used by the fleet
        for d in self.drivers.getDriverList():
            
            routeID = d.getId() + '_' + str(tripNo)
            try:
                route = dijkstra(
                    self.roadNetwork, 
                    self.roadNetwork.getEdge(d.getOrigin()), 
                    self.roadNetwork.getEdge(d.getDestination()),
                    lambda edge: self.knownTT[d.getId()][edge.getID()] #need to make sure lambda is OK
                )
            except KeyError as k:
                self.logger.error('Tried to route on non-existing edge:' + str(k))
                self.logger.info('Exiting...')
                traci.close()
                exit()
            #need to add the vehicles before, right?
            edges = [edge.getID().encode('utf-8') for edge in route]
            
            traci.route.add(routeID, edges)
            #traci.vehicle.setRoute(d.getId(), edges)
            traci.vehicle.add(
                d.getId() + '_' + str(tripNo), routeID, d.getDepartTime() + currentTs, 
                StandardDriver.DEPART_POS, 0
            )
            
            self.logger.info(d.getId() + "'s route: [" + ", ".join(edges) + ']')
            
            #adds the route links to the list of fleet links if the driver belongs to the fleet
            if d.isFromFleet():
                self.fleetLinks += [l.getID() for l in route]
            
            #removes duplicates
            self.fleetLinks = list(set(self.fleetLinks))
            #self.logger.info("Links belonging to the fleet:")
            #self.logger.info([l.getID() for l in self.fleetLinks])
            
    def evaluate_edge(self,edge,driver):
        return self.knownTT[driver.getId()][edge.getID()]
            
    def run(self):
        traci.init(self.options.port)
        
        for i in range(0,self.DEFAULT_ITERATIONS):
            self.calculateRoutes(i)
            for d in self.drivers.getDriverList():
                d.prepareForTrip(i,self.knownTT[d.getId()]) 
                d.debug()
            timesteps = 1

            while not self.drivers.allArrived():
                traci.simulationStep()
                #print timesteps
                for d in self.drivers.getDriverList():
                    
                    #check: will it update link status upon arrival??
                    d.updateStatus()
                    #d.debug()
                    
                    #makes all information in Knowledge Base get older
                    if not d.arrived(): 
                        for l in self.roadNetwork.getEdges():
                            self.infoAge[d.getId()][l.getID()] = self.infoAge[d.getId()][l.getID()]  + 1
                    
                    #print self.knownTT[self.drivers.getDriverList()[0].getId()]
                    #print d.getId(),'-',self.knownTT[d.getId()]
                    if d.changedLink():
                        #self.logger.info('Driver ' + d.getId() + ' changed link.')
                        #print 'Last TT, lastLink', d.lastTT(),',', d.lastLinkId()
                        
                        #prevents the insertion of key 'None' in knowledge base
                        if d.lastLinkId() is not None and d.lastLinkId() != '':
                            self.knownTT[d.getId()][d.lastLinkId()] = d.lastTT()
                            self.infoAge[d.getId()][d.lastLinkId()] = 0
                        
                    #d.debug()
                    #print d.traversedTripLinks(), d.remainingTripLinks()
                    #print d.onTrip(), d.remainingTripLinks()
                        
                self.buildMessages()
                #self.__debugMessages()
                #test if ivc is working
                #print 'be4 ivc:'
                
                #dump_matrix(self.knownTT, sys.stdout)
                self.interVehicularCommunication()
                #debugMatrixPair(self.knownTT, self.infoAge)
                #print 'after ivc:'
                #dump_matrix(self.knownTT, sys.stdout)
#                    if REPLAN_CONDITIONS:
#                        d.replan()

                self.replanRoutes()
                
                timesteps += 1
            #dump_matrix(self.knownTT)
            #dump_matrix(self.infoAge)
            self.logger.info('Trip #' + str(i) + ' finished. Drivers TT')
            self.logger.info([d.currentTravelTime() for d in self.drivers.getDriverList()])
        #FINISH
    
        traci.close()
    def getTraciClient(self):
        return self.traciClient
    
    def buildMessages(self):
        """
        Builds the messages to be exchanged in this step. 
        """
        #print [l for l in self.fleetLinks]
        for d in self.drivers.getDriverList():
            #skips the drivers with no IVC
            if not d.isIvcCapable(): 
                continue
            
            for l in self.roadNetwork.getEdges():
                if d.isFromFleet() and l.getID() in self.fleetLinks:
                    self.msgTT[d.getId()][l.getID()] = 1000000
                    self.infoAge[d.getId()][l.getID()] = 0
                    #mwahahaha
                    
                else:
                    self.msgTT[d.getId()][l.getID()] = self.knownTT[d.getId()][l.getID()]
                    #self.msgAge[d.getId()][l.getID()] = self.infoAge[d.getId()][l.getID()]
    def interVehicularCommunication(self):
        """
        Performs the message exchanging procedure
        """
        for d in self.drivers.getDriverList():
            #skips the drivers with no IVC and the ones that arrived
            if d.arrived() or not d.isIvcCapable():
                continue
            
            #print ("Driver " + d.getId() + " receiving messages.")
            #print "In range:",[e.getId() for e in self.drivers.getIvcDriversInRange(d,self.commRange)]
            for c in self.drivers.getIvcDriversInRange(d,self.commRange):
                
                #print c.getId(),'is in',d.getId(),'\'s range'
                for l in self.roadNetwork.getEdges():
                    #d will use c's information only if it is newer than his 
                    if self.infoAge[c.getId()][l.getID()] >= self.infoAge[d.getId()][l.getID()]:
                        continue
                    
                    gamma = self.decay(self.infoAge[c.getId()][l.getID()])
                    
                    self.knownTT[d.getId()][l.getID()] = gamma * self.msgTT[c.getId()][l.getID()] + (1 - gamma) * self.knownTT[d.getId()][l.getID()] 
                    self.infoAge[d.getId()][l.getID()] = self.infoAge[c.getId()][l.getID()]
                    
                        
    def decay(self,infoAge):
        """
        Returns the factor that exponentially decay the information relevance
        given its age
        """
        a = 2.7182818284590451 #euler's
        b = 15
        #when infoAge approaches 60, decay approaches zero
        return pow(a, -infoAge / b)
    
    def replanRoutes(self):
        """
        Checks the replan conditions and recalculate drivers' routes, if needed
        """
        
        for d in self.drivers.getDriverList():
            # does not try replanning if it is disabled, if drv is not on trip
            # or if driver just exited a link
            if not d.canReplan() or not d.onTrip() or d.changedLink():
                continue
            
            td = d.currentTravelTime()
            remaining = d.remainingTripLinks()
            
            #print remaining

            if td + sum([self.knownTT[d.getId()][j] for j in remaining]) >\
             d.acceptableDelay() * d.estimatedTT():
                print d.getId(), 'will replan' 
                route = dijkstra(
                    self.roadNetwork, 
                    self.roadNetwork.getEdge(d.currentEdge()), 
                    self.roadNetwork.getEdge(d.getDestination()),
                    lambda edge: self.knownTT[d.getId()][edge.getID()] #need to make sure lambda is OK
                )
                #need to add the vehicles before, right?
                edges = [edge.getID().encode('utf-8') for edge in route]
                #print 'recalc.ed route:', edges
                
                d.updateETT(edges, self.knownTT[d.getId()])
                #update ESTIMATED TT
                
                d.setRoute(d.traversedTripLinks() + edges)
                print d.getId(), '\'s new route ', d.getRoute()
                #traci.insert(route)
            
#            else:
#                print d.getId(), 'won\'t replan'
                
    def __debugMessages(self):
        for drv,line in self.msgTT.iteritems():
            print 'Drv:',drv
            
            strLine = ''
            for lnk,col in line.iteritems():
                print lnk,'\t',col,'\t',self.infoAge[drv][lnk]
        
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
          '-p', '--port', dest='port', type='int',
          default = self.DEFAULT_PORT,
          help = 'the port used to communicate with the TraCI server'
        )
        
        parser.add_option(
            '-r', '--route-files', dest='routeFiles',
            help='Load vehicles from given files.',
            type='string', default=[], action='callback',
            callback=parse_list_to('routeFiles'),
            metavar='FILES'
        )
        
        parser.add_option(
          '-n','--net-file', dest='netFile', type='string',
          default=None, help = 'the .net.xml file with the network definition'
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
            handler = logging.FileHandler(options.logFile or Application.DEFAULT_LOG_FILE)

        self.logger.setLevel(options.logLevel)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(module)s - %(message)s"))
        self.logger.addHandler(handler)

        # Initialize the port and road network, if a network file was supplied
        self.port = options.port or Application.DEFAULT_PORT
        if options.netFile is not None:
            # Load the edges of the network
            try:
                self.network = sumolib.net.readNet(options.netFile)
            except IOError as err:
                print 'Error reading net file:', err
                sys.exit(1)
        
        
        
    def __checkOptions(self, options, args, parser):
        if len(options.routeFiles) == 0:
            parser.error('At least one route file is required, none was given.')
        
        if options.netFile is None:
            parser.error('Network file required.')

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

def evaluate_edge(edge):
    print type(edge)
    return edge.getLength() / edge.getLaneNumber()

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


def debugMatrixPair(matrix, matrix2, outStream = sys.stdout):
    for drv,line in matrix.iteritems():
        print 'CurrItem:',drv
        
        for lnk,col in line.iteritems():
            print lnk,'\t',col,'\t',matrix2[drv][lnk]

def dump_matrix(matrix, outStream = sys.stdout):
    #output = open(outStream,'w')
    
    for key,line in matrix.iteritems():
        strLine = ''
        #print line
        #exit()
        #print '\t'.join(map(str,line))
        #print '\t'.join(map(str,key))
        
        for colKey,col in line.iteritems():
            strLine += str(col) + '\t'
        outStream.write(strLine + '\n')
        
