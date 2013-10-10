'''
Contains the Iterations class, which is responsible for running
an IVC experiment.

'''
import logging, sys, os
import traci, sumolib
from time import time
from drivers import Drivers
import collections
from drivers import StandardDriver
import subprocess
from statistics.statswriter import StatsWriter
from overloadcontrol import OverloadControl, AuxiliaryOverloadControl
import loadkeeper
#from src.overloadcontrol import AuxiliaryOverloadControl

#looks up on ../lib to import Guilherme's implementation of Dijkstra algorithm
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
if not path in sys.path: sys.path.append(path)

from search import dijkstra

class Iterations(object):
    '''
    Runs the iterations, write out statistics, etc.
    
    '''
    
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
                  iterations, first_iter, warmUpTime, warmUpLoad, mua = False, delta = 200, beta = 15, cheat = None,
                  ivcfreq = 2, nogamma = False, summary_output = None, routeinfo_output = None,
                  mal_strategy = None, use_lk = False, sumoPath = None):
        
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.netFile = netFile
        
        self.warmUpTime = warmUpTime 
        self.iterations = iterations
        
        self.auxDemandFile = auxDemandFile
        self.activateGui = gui
        
        self.mua = mua
        
        self.port = port
        self.summary_output = summary_output
        self.routeinfo_output = routeinfo_output
        
        self.commRange    = delta
        self.cheatNumber  = cheat
        self.beta         = beta
        self.ivcfreq      = ivcfreq
        self.nogamma      = nogamma
        self.mal_strategy = mal_strategy
        
        self.sumo_path = sumoPath
        self.use_lk = use_lk
        
        try:
            self.roadNetwork = sumolib.net.readNet(netFile)
        except IOError as err:
            self.logger.error('Error reading roadNetwork file: %s' % err)
            self.logger.info('Exiting on error.')
            sys.exit(1)
        
        #TODO: parametrize 900 and ctrl
        #self.overloadControl = AuxiliaryOverloadControl(700, 'ctrl')
        self.overloadControl = OverloadControl(warmUpLoad, 'ctrl')
        self.loadkeeper = loadkeeper.LoadKeeper(self.roadNetwork, None, 'ctrl')
        
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
                
            d.setKnownTT(self.knownTT[d.getId()])
            d.setInfoAges(self.infoAge[d.getId()])
            
            
    def calculateRoutes(self,tripNo):
        '''
        Calculates routes and adds vehicles in SUMO for each driver.
        Also, records the links used by the self-interested fleet
        
        '''
        currentTs = traci.simulation.getCurrentTime() / 1000
        self.fleetLinks = {} #resets the list of links used by the fleet
        
        for d in self.drivers.getDriverList():
            if d.isFromFleet():
                self.fleetLinks[d.fleetID()] = []
                #print '%s fleet ID is %s' % (d.getId(), d.fleetID())
                #print 'Fleet links init: %s' % self.fleetLinks 
                
        for d in self.drivers.getDriverList():
            
            weight_function = lambda edge: self.knownTT[d.getId()][edge.getID()]
            
            if d.isFromFleet() and self.mal_strategy == 'shortest-path':
                weight_function = lambda edge: 1.0 / edge.getLaneNumber()
            
            routeID = d.getId() + '_' + str(tripNo) #cannot use d.getTraciId() because it isn't updated yet
            try:
                route = dijkstra(
                    self.roadNetwork, 
                    self.roadNetwork.getEdge(d.getOrigin()), 
                    self.roadNetwork.getEdge(d.getDestination()),
                    weight_function #need to make sure lambda is OK
                )
            except KeyError as k:
                self.logger.error('Tried to route on non-existing edge:' + str(k))
                self.logger.info('Exiting on error...')
                traci.close()
                exit()
            #need to add the vehicles before, right?
            edges = [edge.getID().encode('utf-8') for edge in route]
#            if d.isFromFleet():
#                print d.getId(), edges, [weight_function(self.roadNetwork.getEdge(e)) for e in edges]
            traci.route.add(routeID, edges)
            #traci.vehicle.setRoute(d.getId(), edges)
            traci.vehicle.add(
                d.getId() + '_' + str(tripNo), routeID, d.getDepartTime() + currentTs, 
                StandardDriver.DEPART_POS, 0
            )
            
            
            #adds the route links to the list of fleet links if the driver belongs to the fleet
            if d.isFromFleet():
                
                self.fleetLinks[d.fleetID()] += [l.getID() for l in route]
                #removes duplicates
                self.fleetLinks[d.fleetID()] = list(set(self.fleetLinks[d.fleetID()]))
                
                #print 'Fleet links added, result: %s' % self.fleetLinks 
            
    def evaluate_edge(self, edge, driver):
        return driver.knownTT(edge.getID())
            
    def run(self, first_iter):
        '''
        Performs the simulation iterations. It calls SUMO, warms up the network, 
        launches the main drivers and writes their statistics
        
        '''
        #print first_iter
        #sumoPath = options.sumopath if options.sumopath is not None else ''
        
        #writes the headers into the output files
        if first_iter == 1:
            #writes the headers in first iteration
            for stats in self.stats:
                stats['writer'].writeLine('x', self.drivers.getDriverList(), 'getId')
                stats['writer'].writeLine('type', self.drivers.getDriverList(), 'getType')
        else:
            #loads drivers data from the last iteration
            print 'Loading driver data...'
            self.drivers.load_known_travel_times('drvdata_tt_%d.csv' % (first_iter - 1) )
            self.drivers.load_info_ages('drvdata_age_%d.csv' % (first_iter - 1) )
        
        for i in range(first_iter - 1, self.iterations):
            sumoExec = 'sumo-gui' if self.activateGui else 'sumo'
            
            if self.sumo_path is not None:
                sumoExec = self.sumo_path + sumoExec
            
            sumoCmd = '%s -n %s --remote-port %d' % \
                (sumoExec, self.netFile, self.port)
            
            if self.auxDemandFile is not None:
                sumoCmd += ' -r ' + self.auxDemandFile
                
            if self.summary_output is not None:
                sumoCmd += ' --summary-output %s%d.xml' % (self.summary_output, i+1)
                
            if self.routeinfo_output is not None:
                sumoCmd += ' --vehroute-output %s --vehroute-output.exit-times' %\
                (self.routeinfo_output + '%d.xml' % (i+1))
                
            self.logger.info('SUMO will be called with: %s' % sumoCmd)
            
            subprocess.Popen(['nohup'] + sumoCmd.split(' '))
            
            self.logger.info('Connecting with TraCI server...')
            traci.init(self.port)
            self.warmUp()
            self.logger.info('Launching main drivers.')
            self.iteration(i)
            self.logger.info('Writing stats for iteration #%d' % (i + 1))
            
            for stats in self.stats:
                stats['writer'].writeLine(i+1, self.drivers.getDriverList(), stats['attr'])
            
            traci.close()
            self.logger.info('TraCI connection closed.')
            self.logger.info('Waiting for SUMO to be terminated...')
            self.logger.info('Writing driver data...')
            
            self.drivers.save_known_travel_times('drvdata_tt_%d.csv' % (i+1) )
            self.drivers.save_info_ages('drvdata_age_%d.csv' % (i+1) )
            
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
            start = time()
            traci.simulationStep()
            self.overloadControl.act()
            if self.use_lk: 
                self.loadkeeper.act()
                
            num_veh = len(traci.vehicle.getIDList())
                
            sys.stdout.write( "\rWarm-up step #%d took %5.3f ms. %6d vehicles in network" % (i+1,  time() - start, num_veh) )
            sys.stdout.flush()
        self.logger.info('\nWarm-up finished.')
            
    def iteration(self, i):
        sys.stdout.write('\tcalculating routes...')
        sys.stdout.flush()
        self.calculateRoutes(i)
        print ' done'
        
        sys.stdout.write('\tpreparing for trip...')
        sys.stdout.flush()
        #print 'ID list:', traci.vehicle.getIDList()
        for d in self.drivers.getDriverList():
            d.prepareForTrip(i,self.knownTT[d.getId()]) 
            #d.debug()
        print ' done'
        
        
        while not self.drivers.allArrived():
            start = time()
            traci.simulationStep()
            ts = traci.simulation.getCurrentTime() / 1000
            
            #sov = time()
            self.overloadControl.act()
            #print 'Sov: %5.3f' % (time() - sov)
            
            if self.use_lk: 
                self.loadkeeper.act()
            
            #chk_stats = time()
            arrivedList = traci.simulation.getArrivedIDList()
#            myArrivedList = list(set(arrivedList).intersection(set([d.getTraciId() for d in self.drivers.getDriverList()])))
#            for d in myArrivedList:
#                
            #print arrivedList, traci.simulation.getDepartedIDList(), traci.vehicle.getIDList(), traci.simulation.getLoadedIDList()
            #print 'routes:', [traci.route.getEdges(rid) for rid in traci.route.getIDList()]
            
            for d in self.drivers.getDriverList():
                if d.getTraciId() in arrivedList:
                    d.tripFinished = True 
                    d.currentLink = None
                    #print '%s has finished its trip' % d.getId()
                    
                #check: will it update link status upon arrival??
                d.updateStatus(self.commRange, ts)
                #d.debug()
                
                #makes all information in Knowledge Base get older
                if d.onTrip(): 
                    for l in self.roadNetwork.getEdges():
                        self.infoAge[d.getId()][l.getID()] = self.infoAge[d.getId()][l.getID()]  + 1
                
                if d.changedLink():
                    
                    #prevents the insertion of key 'None' in knowledge base
                    if d.lastLinkId() is not None and d.lastLinkId() != '':
                        self.knownTT[d.getId()][d.lastLinkId()] = d.lastTT() / 1000
                        self.infoAge[d.getId()][d.lastLinkId()] = 0
                
            #print 'chk_stats: %5.3f' % (time() - chk_stats)        
                #d.debug()
            #print 'Starting IVC...'
            if ts % self.ivcfreq == 0: #performs IVC every X timesteps
                #print 'Building msgs...'
                msg = time()        
                self.buildMessages()
                #print ' msg: %5.3f' % (time() - msg)
                #print 'Done.'
                ivc = time()
                self.interVehicularCommunication(ts)
                #print ' ivc: %5.3f' % (time() - ivc)
                #print 'Done.'
                rpl = time()
                self.replanRoutes()
                #print ' rpl: %5.3f' % (time() - rpl)
            
            sys.stdout.write( "\rIteration %d's timestep #%d took %5.3f ms" % (i+1, ts, time() - start))
            sys.stdout.flush()
            
#            if ts > 2000:
#                for d in traci.vehicle.getIDList():
#                    if 'ctrl' in d:
#                        print d, 'is lost in edge', traci.vehicle.getLaneID(d)
            #timesteps += 1
        self.logger.info('Trip #' + str(i) + ' finished.')
            
    def buildMessages(self):
        '''
        Builds the messages to be exchanged in this step. 
        
        '''
        #print self.fleetLinks
        
        for d in self.drivers.getDriverList():
            #skips the drivers with no IVC or not on trip
            if not d.isIvcCapable() or not d.onTrip(): 
                continue
            
            d.build_message(self.fleetLinks, self.mua, self.cheatNumber)
#            continue
#        
#            if d.isFromFleet():
#                interestSet = d.getRoute() if self.mua else self.fleetLinks[d.fleetID()]
#                #print '%s interest set is %s' % (d.getId(), interestSet)
#                
#            for l in self.roadNetwork.getEdges():
#                
#                #sets the msg element accordingly
#                self.msgTT[d.getId()][l.getID()] = self.knownTT[d.getId()][l.getID()]
#                
#                if d.isFromFleet():
#                    
#                    #reports false information on the links belonging to the set of interest
#                    if l.getID() in interestSet:
#                        
#                        if self.cheatNumber is None:
#                            cheat = (3.0 * l.getLength()) / l.getSpeed() #float division? --yes
#                        else:
#                            cheat = self.cheatNumber
#                        #print '\tCheating about %s. False info: %s' % (l.getID(), cheat)
#                        self.msgTT[d.getId()][l.getID()] = cheat
#                        self.infoAge[d.getId()][l.getID()] = 0
                        #mwahahaha
                    
    def interVehicularCommunication(self, curr_time):
        '''
        Performs the message exchanging procedure
        
        '''
        #print ' Performing IVC...'
        for d in self.drivers.getDriverList():
            #skips the drivers with no IVC and the ones that arrived
            if not d.onTrip() or not d.isIvcCapable():
                #print '(OnTrip, IVC-capable): (%s, %s)' % (d.onTrip(), d.isIvcCapable())
                continue

            #print ' Searching neighbors...'
            neighbors = self.drivers.getIvcDriversInRange(d, self.commRange)
            #print ' %s neighbors: %s' % (d.getId(), len(neighbors) ) #[c.getId() for c in neighbors])
            for c in neighbors:
                #if d already exchanged messages with c...
                #print '\t\t%s ' % d.last_comm_time
                if c.getId() in d.last_comm_time:
                    time_since_last_comm = curr_time - d.last_comm_time[c.getId()]
                    #...and if c has no newer information since last comm, skips message from c
                    #also skips c if its newest info is older than 20 minutes
                    if  time_since_last_comm <= c.newest_info_age or c.newest_info_age > 1200 :
                        #print '\t%s disregarded' % c.getId()
                        continue
                #print '\t%s regarded' % c.getId()
                #sets the time of message receipt from c
                d.last_comm_time[c.getId()] = curr_time
                
                for l in c.message:# self.roadNetwork.getEdges():
                    #d will use c's information only if it is newer than his
                    #c_kb = self.knownTT[c.getId()]
                    #c_age= self.infoAge[c.getId()] 
                    #continue
                    link_id = l#.getID()
                    the_link = self.roadNetwork.getEdge(l)
                    #if c.info_age(link_id) > 10:    #dbg
                    #    continue                    #dbg
                    
                    if c.info_age(link_id) >= d.info_age(link_id):
#                        DEBUG:
#                        if c.isFromFleet() and l.getID() in c.getRoute():
#                            print '\t%s: disregarded info of %s from %s. (age_inc, age_curr) = (%d, %d)' %\
#                             (d.getId(), l.getID(), c.getId(), self.infoAge[c.getId()][l.getID()], self.infoAge[d.getId()][l.getID()])
#                        END-DEBUG
                        #print '\t%s disregarded, old info' % l
                        continue
                    #continue #<<slow already
                    #a malicious agent will disregard heavy load information (> 3* fftt)
                    if d.isFromFleet() and c.message[link_id] >= 3 * (the_link.getLength() / the_link.getSpeed()):
                        #print '\t%s: Disregarded heavy load info of %s from %s' % (d.getId(), l.getID(), c.getId())
                        continue
                    
                    gamma = 1 if self.nogamma else self.decay(c.info_age(link_id))
                    newTT = gamma * c.message[link_id] + (1 - gamma) * d.known_travel_time(link_id) #self.knownTT[d.getId()][l.getID()]
                    #continue
                    #DEBUG
                    #print '%s: using %s from %s for %s' % (d.getId(), newTT, c.getId(), l.getID())
                    
                    d.set_known_travel_time(l, newTT) #self.knownTT[d.getId()][l.getID()] = newTT
                    d.set_info_age(l, c.info_age(link_id)) # self.infoAge[d.getId()][l.getID()] = self.infoAge[c.getId()][l.getID()]
                    
                        
    def decay(self,infoAge):
        '''
        Returns the factor that exponentially decay the information relevance
        given its age
        
        '''
        a = 2.7182818284590451 #euler's
        #when infoAge approaches 60, decay approaches zero
        return pow(a, -infoAge / self.beta)
    
    def replanRoutes(self):
        '''
        Checks the replan conditions and recalculate drivers' routes, if needed
        
        '''
        #print 'Replan procedure...'
        for d in self.drivers.getDriverList():
            # does not try replanning if it is disabled, if drv is not on trip, 
            # if driver just exited a link or if current edge is internal
            
            if not d.canReplan() or not d.onTrip() or d.changedLink() or not d._isValidEdge(d.currentEdge()):
                continue    
            
            '''
            ### new replan ###
            if d.currentEdge() != d.getDestination() and d._isValidEdge(d.currentEdge()):
                
                #current_route = traci.vehicle.getRoute(d.id)
                route_until_dest = d.remainingTripLinks()#d.getRoute()[d.getRoute().index(d.currentEdge()):]
                
                
                new_route = dijkstra(
                    self.roadNetwork, 
                    self.roadNetwork.getEdge(d.currentEdge()), 
                    self.roadNetwork.getEdge(d.getDestination()),
                    lambda edge: d.known_travel_time(edge.getID()) # self.knownTT[d.getId()][edge.getID()]
                )
                
                new_route_edg_ids = [e.getID() for e in new_route]
                
                #print '%s (%d, %d)' % (d.getId(), self.routeCost(d, route_until_dest), self.routeCost(d, new_route_edg_ids))
                
                if self.routeCost(d, route_until_dest) > d.acceptableDelay() * self.routeCost(d, new_route_edg_ids):
                    #print '%s replanned to %s ' % (d.getId(), new_route_edg_ids)
                    d.setRoute(d.traversedTripLinks() + [e.encode('utf-8') for e in new_route_edg_ids])
                    d.incReplanNumber()
                    #print 'Vehicle %s has new route. Old cost: %s. New cost %s.' % (d.id, self.route_cost(route_until_dest), self.route_cost(new_route_edg_ids))
            
            '''
            ### old_replan ###
            
            #td = d.currentTravelTime()
            remaining = d.remainingTripLinks()
            
#            if td + sum([d.known_travel_time(j) for j in remaining]) >\
            actual_remaining_cost = sum([d.known_travel_time(j) for j in remaining])
            estimt_remaining_cost = sum([d.estimatedTTs[j] for j in remaining])
            
            if int(actual_remaining_cost) > int(d.acceptableDelay() * estimt_remaining_cost):
                #print d.getId(), 'will replan' 
                route = dijkstra(
                    self.roadNetwork, 
                    self.roadNetwork.getEdge(d.currentEdge()), 
                    self.roadNetwork.getEdge(d.getDestination()),
                    lambda edge: d.known_travel_time(edge.getID()) #need to make sure lambda is OK
                )
                #need to add the vehicles before, right?
                edges = [edge.getID().encode('utf-8') for edge in route]
                
                d.updateETT(edges, self.knownTT[d.getId()])
                
                if (d.getRoute() != d.traversedTripLinks() + edges):
                    if sum([d.known_travel_time(l) for l in d.getRoute()]) < sum([d.known_travel_time(l) for l in d.traversedTripLinks() + edges]):
                        
                        print 'WARNING:', d.getId(), ' is about to change to a more expensive route!'
                        print 'oldroute:', d.getRoute(), '- cost:', [d.known_travel_time(l) for l in d.getRoute()]
                        print 'newroute:',  d.traversedTripLinks() + edges, ' - cost:', [d.known_travel_time(l) for l in d.traversedTripLinks() + edges]
                        print 'current:', d.currentEdge(), ' - remaining:', remaining, ' - newpart:', [l.getID() for l in route]
                        print 'rmncost > delay * ett: %s > %s * %s -- %s --- %d > %d' %\
                        (int(sum([d.known_travel_time(j) for j in remaining])), 
                         d.acceptableDelay(), int(sum([d.estimatedTTs[j] for j in remaining])), 
                         int(actual_remaining_cost) > int(d.acceptableDelay() * estimt_remaining_cost),
                         int(actual_remaining_cost), int(d.acceptableDelay() * estimt_remaining_cost) ) 
                        
#                    print d.getId() + ' has a new route!' 
#                    print d.getRoute(), d.traversedTripLinks() + edges
#                    print [self.knownTT[d.getId()][l] for l in d.getRoute()], [self.knownTT[d.getId()][l] for l in d.traversedTripLinks() + edges]
#                    print sum([self.knownTT[d.getId()][l] for l in d.getRoute()]), sum([self.knownTT[d.getId()][l] for l in d.traversedTripLinks() + edges])
                    
                    d.setRoute(d.traversedTripLinks() + edges)
                    d.incReplanNumber()
                    #print d.getId(), 'has replanned'
        
    
    def routeCost(self, driver, route):
        '''
        Returns the cost of the edges for the given driver
        
        '''
        return sum([self.knownTT[driver.getId()][e] for e in route])
                
    def __debugMessages(self):
        for drv,line in self.msgTT.iteritems():
            print 'Drv:',drv
            
            strLine = ''
            for lnk,col in line.iteritems():
                print lnk,'\t',col,'\t',self.infoAge[drv][lnk]
        
def evaluate_edge(edge):
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
        
        for colKey,col in line.iteritems():
            strLine += str(col) + '\t'
        outStream.write(strLine + '\n')
        
