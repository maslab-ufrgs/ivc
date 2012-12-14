import logging, sys, os
import traci, sumolib
from time import time
from drivers import Drivers
import collections
from drivers import StandardDriver
import subprocess
from statistics.statswriter import StatsWriter
from overloadcontrol import OverloadControl, AuxiliaryOverloadControl
#from src.overloadcontrol import AuxiliaryOverloadControl

#looks up on ../lib to import Guilherme's implementation of Dijkstra algorithm
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
if not path in sys.path: sys.path.append(path)

from search import dijkstra

class Iterations(object):
    """Iterations object.
    """
    
    DEFAULT_LOG_FILE = 'experiment.log'
    LOGGER_NAME = 'experiment'
    
    DEFAULT_PORT = 8813
    DEFAULT_ITERATIONS = 50
    
    #DEFAULT_CHEATING = 1000000
    
    port        = None
    netFile     = None
    activateGui = False
    network     = None
    drivers     = None
    roadNetwork = None
    commRange   = 200
    auxDemandFile = None
    warmUpTime = 0
    mua = False
    cheatNumber = None
    overloadControl = None
    beta = 15
    ivcfreq = 2
    nogamma = False
    
    stats = []
    
    infoAge = collections.defaultdict(dict)
    knownTT = collections.defaultdict(dict)
    msgTT   = collections.defaultdict(dict)
    msgAge  = collections.defaultdict(dict)
    fleetLinks = []
    
    
    
    def __init__(self, netFile, mainDrvFiles, auxDemandFile, output, port, gui,
                  iterations, warmUpTime, mua = False, delta = 200, beta = 15, cheat = None,
                  ivcfreq = 2, nogamma = False):
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.netFile = netFile
        
        self.warmUpTime = warmUpTime 
        self.iterations = iterations
        
        self.auxDemandFile = auxDemandFile
        self.activateGui = gui
        
        self.mua = mua
        
        self.port = port
        
        self.commRange    = delta
        self.cheatNumber  = cheat
        self.beta         = beta
        self.ivcfreq      = ivcfreq
        self.nogamma      = nogamma
           
        try:
            self.roadNetwork = sumolib.net.readNet(netFile)
        except IOError as err:
            self.logger.error('Error reading roadNetwork file: %s' % err)
            self.logger.info('Exiting on error.')
            sys.exit(1)
        
        #TODO: parametrize 900 and ctrl
        #self.overloadControl = AuxiliaryOverloadControl(700, 'ctrl')
        self.overloadControl = OverloadControl(900, 'ctrl')
        
        self.drivers = Drivers(mainDrvFiles, self.roadNetwork)
        
        #just comment the stats that should not be generated
        if output is not None:
            self.stats = [
                {'attr': 'getSpeed', 'writer': StatsWriter(output + '_spd.csv')},
                {'attr': 'currentTravelTime', 'writer': StatsWriter(output + '_tt.csv')},
                {'attr': 'traveledDistance', 'writer': StatsWriter(output + '_dist.csv')},
                {'attr': 'getNumHops', 'writer': StatsWriter(output + '_hops.csv')},
                {'attr': 'getNumReplans', 'writer': StatsWriter(output + '_repl.csv')},
                #{'attr': 'traversedTripLinks', 'writer': StatsWriter(output + '_route.csv')},
            ] 
            
            paramFile = open(output + "_params.csv",'w')
            paramFile.write('netFile,warmUpTime,iterations,mainDemand,auxDemand,delta,beta,cheat,ivcfreq,replan,fleet?,nogamma?,gui\n')
            paramFile.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (
                self.netFile,
                self.warmUpTime, 
                self.iterations,
                mainDrvFiles,
                auxDemandFile,
                self.commRange,
                self.beta,
                self.cheatNumber,
                self.ivcfreq,
                '20 ~ 70%',
                not self.mua,
                self.nogamma,
                self.activateGui
            ))
            paramFile.close()
            self.logger.info('Finished writing parameters to file.')
        
        else:
            self.stats = []
        
        
        
        
        #initializes drivers knowledge base
        for d in self.drivers.getDriverList():
            for l in self.roadNetwork.getEdges():
                #initializes travel time optimistically as the FFTT
                self.infoAge[d.getId()][l.getID()] = sys.maxsize
                self.knownTT[d.getId()][l.getID()] = l.getLength() / l.getSpeed() #* 1000 / l.getLaneNumber()
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
                self.logger.info('Exiting on error...')
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
            
            #self.logger.info(d.getId() + "'s route: [" + ", ".join(edges) + ']')
            
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
        '''
        Performs the simulation iterations. It calls SUMO, warms up the network, 
        launches the main drivers and writes their statistics
        '''
        
        
        #sumoPath = options.sumopath if options.sumopath is not None else ''
        sumoExec = 'sumo-gui' if self.activateGui else 'sumo'
        sumoCmd = '%s -n %s --remote-port %d' % \
            (sumoExec, self.netFile, self.port)
            
        if self.auxDemandFile is not None:
            sumoCmd += ' -r ' + self.auxDemandFile
        
        self.logger.info('SUMO will be called with: %s' % sumoCmd)
        
        #writes the headers into the output files
        for stats in self.stats:
            stats['writer'].writeLine('x', self.drivers.getDriverList(), 'getId')
            stats['writer'].writeLine('type', self.drivers.getDriverList(), 'getType')
        
        for i in range(0,self.iterations):
            
            self.logger.info('Starting SUMO...')
            subprocess.Popen(['nohup'] + sumoCmd.split(' '))
            #self.logger.info('SUMO started...')
            
            self.logger.info('Connecting with TraCI server...')
            traci.init(self.port)
            self.warmUp()
            self.logger.info('Launching main drivers.')
            self.iteration(i)
            self.logger.info('Writing stats for iteration #%d' % (i + 1))
            
            for stats in self.stats:
                stats['writer'].writeLine(i+1, self.drivers.getDriverList(), stats['attr'])
            
            #self.logger.info('Statistics written')
                
            traci.close()
            self.logger.info('TraCI connection closed.')
            self.logger.info('Waiting for SUMO to be terminated...')
            
            #WAIT(SUMO)
            self.logger.info('Iteration #%d finished.' % (i + 1))
        
        #closes speedStats safely
        self.logger.info('All iterations finished')
        
        for stats in self.stats:
            del(stats['writer'])
        
        #FINISH :)
    
        
        
    def warmUp(self):
        """Run the simulation in SUMO until the desired number of warm-up steps"""
        if self.warmUpTime == 0:
            return
        
        self.logger.info('Warm-up started. Aux. demand control is activated')
        for i in range(0, self.warmUpTime):
            traci.simulationStep()
            self.overloadControl.act()
        self.logger.info('Warm-up finished. %d timesteps executed' % self.warmUpTime)
            
    def iteration(self, i):
        
        self.calculateRoutes(i)
        for d in self.drivers.getDriverList():
            d.prepareForTrip(i,self.knownTT[d.getId()]) 
            #d.debug()
            
        

        while not self.drivers.allArrived():
            start = time()
            traci.simulationStep()
            ts = traci.simulation.getCurrentTime() / 1000
        
            self.overloadControl.act()
            #print timesteps
            for d in self.drivers.getDriverList():
                
                #check: will it update link status upon arrival??
                d.updateStatus()
                #d.debug()
                
                #makes all information in Knowledge Base get older
                if d.onTrip(): 
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
            #print 'Building msgs...'        
            self.buildMessages()
            #print 'Done.'
            #self.__debugMessages()
            #test if ivc is working
            #print 'be4 ivc:'
            
            #dump_matrix(self.knownTT, sys.stdout)
            #print 'Starting IVC...'
            if ts % self.ivcfreq == 0: #performs IVC every X timesteps
                self.interVehicularCommunication()
            #print 'Done.'
            #debugMatrixPair(self.knownTT, self.infoAge)
            #print 'after ivc:'
            #dump_matrix(self.knownTT, sys.stdout)
#                    if REPLAN_CONDITIONS:
#                        d.replan()

            self.replanRoutes()
            
            sys.stdout.write( "\rIteration %d's timestep #%d took %5.3f ms" % (i+1, ts, time() - start))
            sys.stdout.flush()
            #timesteps += 1
        #dump_matrix(self.knownTT)
        #dump_matrix(self.infoAge)
        self.logger.info('Trip #' + str(i) + ' finished.')
        #self.logger.info([(d.getId(), d.currentTravelTime()) for d in self.drivers.getDriverList()])
            
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
                
                #sets the msg element accordingly
                self.msgTT[d.getId()][l.getID()] = self.knownTT[d.getId()][l.getID()]
                
                if d.isFromFleet():
                    interestSet = d.getRoute() if self.mua else self.fleetLinks
                    #reports false information on the links belonging to the set of interest
                    if l.getID() in interestSet:
                        
                        if self.cheatNumber is None:
                            cheat = (3.0 * l.getLength()) / l.getSpeed() #float division?
                        else:
                            cheat = self.cheatNumber
                        
                        self.msgTT[d.getId()][l.getID()] = cheat
                        self.infoAge[d.getId()][l.getID()] = 0
                        #mwahahaha
                    
    def interVehicularCommunication(self):
        """
        Performs the message exchanging procedure
        """
        for d in self.drivers.getDriverList():
            #skips the drivers with no IVC and the ones that arrived
            if not d.onTrip() or not d.isIvcCapable():
                continue
            
            #print ("Driver " + d.getId() + " receiving messages.")
            #print "In range:",[e.getId() for e in self.drivers.getIvcDriversInRange(d,self.commRange)]
#            if d.getId() == 'ctrl106':
#                print [c.getId() for c in self.drivers.getIvcDriversInRange(d,self.commRange)]
                
            for c in self.drivers.getIvcDriversInRange(d,self.commRange):
                
                #print c.getId(),'is in',d.getId(),'\'s range'
                for l in self.roadNetwork.getEdges():
                    #d will use c's information only if it is newer than his 
                    if self.infoAge[c.getId()][l.getID()] >= self.infoAge[d.getId()][l.getID()]:
                        continue
                    
                    #a malicious agent will disregard heavy load information (> 3* fftt)
                    if d.isFromFleet() and self.msgTT[c.getId()][l.getID()] >= 3 * (l.getLength() / l.getSpeed()):
                        continue
                    gamma = 1 if self.nogamma else self.decay(self.infoAge[c.getId()][l.getID()])
                    
                    self.knownTT[d.getId()][l.getID()] = gamma * self.msgTT[c.getId()][l.getID()] + (1 - gamma) * self.knownTT[d.getId()][l.getID()] 
                    self.infoAge[d.getId()][l.getID()] = self.infoAge[c.getId()][l.getID()]
                    
                        
    def decay(self,infoAge):
        """
        Returns the factor that exponentially decay the information relevance
        given its age
        """
        a = 2.7182818284590451 #euler's
        #when infoAge approaches 60, decay approaches zero
        return pow(a, -infoAge / self.beta)
    
    def replanRoutes(self):
        """
        Checks the replan conditions and recalculate drivers' routes, if needed
        """
        
        for d in self.drivers.getDriverList():
            # does not try replanning if it is disabled, if drv is not on trip, 
            # if driver just exited a link or if current edge is internal
            
            if not d.canReplan() or not d.onTrip() or d.changedLink() or not d._isValidEdge(d.currentEdge()):
                continue
            
            td = d.currentTravelTime()
            remaining = d.remainingTripLinks()
            
            #print remaining

            if td + sum([self.knownTT[d.getId()][j] for j in remaining]) >\
             d.acceptableDelay() * d.estimatedTT():
                #print d.getId(), 'will replan' 
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
                d.incReplanNumber()
                #print d.getId(), '\'s new route ', d.getRoute()
                #traci.insert(route)
            
#            else:
#                print d.getId(), 'won\'t replan'
                
    def __debugMessages(self):
        for drv,line in self.msgTT.iteritems():
            print 'Drv:',drv
            
            strLine = ''
            for lnk,col in line.iteritems():
                print lnk,'\t',col,'\t',self.infoAge[drv][lnk]
        
def evaluate_edge(edge):
    #print type(edge)
    return edge.getLength() / edge.getLaneNumber()

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
        
#if __name__ == '__main__':
#    app = Iterations(sys.argv)
#    app.run()