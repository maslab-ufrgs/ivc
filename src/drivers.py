'''
Created on 31/08/2012

@author: artavares

'''

import sys, os
import traci
import traci.constants as tc
import xml.etree.ElementTree as ET
import collections
from copy import copy
import math

#looks up on ../lib to import Guilherme's implementation of Dijkstra algorithm
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
if not path in sys.path: sys.path.append(path)

from search import dijkstra
#from gpsdrivers import RoutedDriver

def eucDist(x1, y1, x2, y2):
    xDiff = x2 - x1
    yDiff = y2 - y1
    return math.sqrt(xDiff*xDiff + yDiff*yDiff)

class Drivers(object):
    
    drvFileList = None
    roadNetwork = None
    
    '''
    Stores a drivers list and encapsulates operations over it
    '''
    drvList = []

    def __init__(self,drvFileList,roadNetwork):
        '''
        Parses the drivers' file and build the drivers list
        RoadNetwork is needed so that drivers will be able to build routes on it
        '''
        
        #Parsing is OK
        
        self.drvFileList = drvFileList
        self.roadNetwork = roadNetwork
        
        for inFile in self.drvFileList:
            tree = ET.parse(inFile)
            root = tree.getroot()
            
            #for-switch is bad practice, but for code complexity reduction it is used here
            for element in root:
                for route in element:
                    edgeList = route.get('edges').split(" ")

                self.drvList.append(StandardDriver(
                    element.get('id'),
                    element.get('type'),
                    edgeList[0],
                    edgeList[-1],
                    element.get('depart'),
                    roadNetwork
                ))
                
            #extends the road network to add the driver info at each edge
            for edge in roadNetwork._edges:
                edge.drivers = collections.deque()
                
    def getDriverList(self):
        return self.drvList
    
    def _save_attr_to_file(self, filename, getter):
        '''
        Saves one attribute of the drivers regarding the road network to a file in the format:
        drv\road,road1,road2,...
        drv1,val1-1,val1-2,...
        drv2,val2-1,val2-2,...
        
        '''
        outfile = open(filename, 'w')
        
        #writes the file header
        outfile.write('drv_id\\road_id,' + ','.join([e.getID() for e in self.roadNetwork.getEdges()]) + '\n')
        
        #writes the file data
        for d in self.drvList:
            outfile.write(d.getId() + ',')
            outfile.write(','.join([str(getter(d,e.getID())) for e in self.roadNetwork.getEdges()]) + '\n')
        outfile.close()
    
    def save_known_travel_times(self, filename):
        '''
        Saves the known travel times of the drivers to a file in the format:
        drv\road,road1,road2,...
        drv1,50,60,...
        drv2,55,67,...
        
        '''
        get_known_travel_time = lambda driver, edge_id: driver.known_travel_time(edge_id)
        self._save_attr_to_file(filename, get_known_travel_time)
        
    def save_info_ages(self, filename):
        '''
        Saves the information ages of the drivers to a file in the format:
        drv\road,road1,road2,...
        drv1,15,20,...
        drv2,0,3,...
        
        '''
        get_info_age = lambda driver, edge_id: driver.info_age(edge_id)
        self._save_attr_to_file(filename, get_info_age)
        
        
    def _load_data(self, filename, setter):
        '''
        Loads data of drivers regarding the road network from a file in the format:
        drv\road,road1,road2,...
        drv1,50,60,...
        drv2,55,67,...
        
        '''
        
        #makes a dict {id: driver,...} from the list of drivers
        drvdict = dict((d.getId(), d) for d in self.drvList)
        
        indata = open(filename).readlines()
        #edges ids are in the first row, from 2nd col onwards 
        edges = indata[0].strip().split(',')[1:]
        for line in indata[1:]:
            #removes the new line and splits the csv into a list
            line_spl = line.strip().split(',')
            
            #drv id is in 1st col and edge data are from 2nd col onwards in each line
            drv_id = line_spl[0]
            edg_data = line_spl[1:]
            
            #writes the edge data into each edge of driver knowledge base
            for i in range(len(edges)):
                setter(drvdict[drv_id], edges[i], float(edg_data[i]))
        
    def load_known_travel_times(self, filename):
        '''
        Loads the known travel times of drivers from a file in the format:
        drv\road,road1,road2,...
        drv1,50,60,...
        drv2,55,67,...
        
        '''
        set_known_travel_time = lambda drv, edg_id, tt: drv.set_known_travel_time(edg_id, tt)
        self._load_data(filename, set_known_travel_time)
        
    def load_info_ages(self, filename):
        '''
        Loads the information ages of drivers from a file in the format:
        drv\road,road1,road2,...
        drv1,10,15,...
        drv2,0,7,...
        
        '''
        set_info_age = lambda drv, edg_id, tt: drv.set_info_age(edg_id, tt)
        self._load_data(filename, set_info_age)
    
    def getIvcDriversInRange(self, driver, commRange):
        '''
        Returns a list of drivers (ivc-capable) closer than 'commRange' 
        meters from the given driver
        
        '''
        #if not driver.onTrip():
        #   return []
        
        #print '    Getting neighbors for vehicle %s' % driver.getId()
        #drvPos = traci.vehicle.getPosition(driver.getTraciId())
        
        if not driver._isValidEdge(driver.currentEdge()):
            return []
        
        #store the neighbor vehicles
        neighborVeh = []
        
        #builds the list of edges of interest
            
        #print '%s in %s interested in %s' % (driver.getId(), driver.currentEdge(), [e.getID() for e in driver.getInterestEdges()])
        
        #traverses the vehicle list querying for the distance
        drvInNeighLinks = []
        
        for neighLink in driver.getInterestEdges():
            drvInNeighLinks += neighLink.drivers
            
        for otherDriver in drvInNeighLinks:
            #skips if is not another driver or if has arrived or is not ivc-capable
            if driver == otherDriver or not otherDriver.onTrip() or not otherDriver.isIvcCapable(): 
                continue
            #print '        testing %s' % otherDriver.getId()

            #print otherPos
            theDist = eucDist(
                driver.posX, driver.posY, 
                otherDriver.posX, otherDriver.posY
            )
            
            #print 'me other dist',driver.getId(), otherDriver.getId(), theDist
            if theDist < commRange:
                neighborVeh.append(otherDriver)
            
        return neighborVeh
    
    def addDriver(self,drv):
        self.drvList.append(drv)
        
    def allArrived(self):
        for drv in self.drvList:
            if not drv.arrived():
                return False
            
        return True
    
class DriverTypes():
    '''
    Basically an enum encoding the driver types
    
    '''
    
    FROM_FLEET      = 'fromFleet'
    IVC             = 'ivc'
    NOIVC           = 'noivc'
    REPLAN          = 'replan'
    NOREPLAN        = 'noreplan'
    IVC_REPLAN      = 'ivc-replan'
    IVC_NOREPLAN    = 'ivc-noreplan'
    NOIVC_REPLAN    = 'noivc-replan'
    NOIVC_NOREPLAN  = 'noivc-noreplan'
    
#dict with the colors of the drivers
DriversColors = {
    DriverTypes.FROM_FLEET      : [255,150,255,0], #salmon
#    DriverTypes.IVC             : 'ivc',
#    DriverTypes.NOIVC           : 'noivc',
#    DriverTypes.REPLAN          : 'replan',
#    DriverTypes.NOREPLAN        : 'noreplan',
    DriverTypes.IVC_REPLAN      : [200,200,200,0], #light gray
    DriverTypes.IVC_NOREPLAN    : [120,235,100,0], #pale green (?)
    DriverTypes.NOIVC_REPLAN    : [150,190,255,0], #pale blue (?)
    DriverTypes.NOIVC_NOREPLAN  : [255,255,255,0] #white
}    
    
class StandardDriver(object):
    
    #type        = None
    roadNetwork = None
    tripNo      = 0
    #travelTime  = 0
    #departTime = 0
    
    DEPART_POS = 5.10
    
    delayTolerance      = 1.0 #1.3
    #estimatedTravelTime = 0
    #route = None
    #numReplans = 0
    
    interestEdges = []
    
    def __init__(self, veh_id, veh_type,origin, destination, depart, roadNetwork):
        
        self.id = veh_id
        self.type = veh_type
        self.origin = origin
        self.destination = destination
        self.departTime = float(depart)
        self.roadNetwork = roadNetwork
        
        self.linkOnLastTimestep = None
        self.currentLink        = None
        self.previousLink       = None #previous link on driver's route
        
        self.timeSpentOnLastLink = 0
        self.timeEnteredLastLink = 0
        
        self.route = None
        self.numReplans = 0
        
        self.estimatedTTs = collections.defaultdict(dict)
        self.tripFinished = False
        
        self.posX = None
        self.posY = None
        
        self.knownTT = None
        self.info_ages = None
        
        self.message = None
        
        self.last_comm_time = {} #{id: time,} stores the time I received msgs from other vehicles
        self._newest_info_age = sys.maxsize
   
    def getId(self):
        return self.id  
    
    def getType(self):
        return self.type
    
    def getDepartTime(self):
        return self.departTime 
    
    @property
    def newest_info_age(self):
        return self._newest_info_age
    
    def getSpeed(self):
        '''
        Returns the ratio: distance traversed / travel time spent; a.k.a.: speed
        
        '''
        travDistance = 0
        for l in self.route:
            travDistance += self.roadNetwork.getEdge(l).getLength()
                
        return travDistance / self.currentTravelTime()
            
    def getInterestEdges(self):
        '''
        Returns the set of edges in the range of IVC for this driver 
        
        '''
        return self.interestEdges
    
    def getNumHops(self):
        '''
        Returns the number of edges in the driver's route
        
        '''
        return len(self.route)
    
    def getNumReplans(self):
        '''
        Returns the number of times that this driver recalculated its route
        
        '''
        return self.numReplans
            
    def traveledDistance(self):
        '''
        Returns the distance (#links x length) for each link traversed by the driver
        
        '''
        #Assumes that lengths of the lanes in the same edge are equal (which is the case for the 6x6 grid)
        travDistance = 0
        for l in self.traversedTripLinks():
            travDistance += self.roadNetwork.getEdge(l).getLength()
        
        return travDistance
    
    def build_message(self, fleet_links, mua, cheat_number):
        self.message = {}#collections.defaultdict(dict)
        
        if self.isFromFleet():
            interestSet = self.getRoute() if mua else fleet_links[self.fleetID()]
            self._newest_info_age = 0 
            
            for l in self.roadNetwork.getEdges():
                #reports false information on the links belonging to the set of interest
                if l.getID() in interestSet:
                    self.info_ages[l.getID()] = 0
                    
                    if cheat_number is None:
                        cheat = (3.0 * l.getLength()) / l.getSpeed() #float division? --yes
                    else:
                        cheat = self.cheatNumber
                    #print '\tCheating about %s. False info: %s' % (l.getID(), cheat)
                    self.message[l.getID()] = cheat
                #reports truthful data for links not in interest set, whose age is less than 20min
                elif self.info_ages[l.getID()] < 1200:
                    self.message[l.getID()] = self.knownTT[l.getID()]
            #print fleet_links, self.getRoute()
            
        else: #in this case, driver is not malicious
            for l in self.roadNetwork.getEdges():
                #updates the lowest information age if necessary
                if self.info_age(l.getID()) < self._newest_info_age:
                    self._newest_info_age = self.info_age(l.getID())
                    
                #reports the travel dime for links whose info. age is less than 20min.
                if self.info_age(l.getID()) < 1200: #20 minutes
                    self.message[l.getID()] = self.knownTT[l.getID()]
                #self.msgTT[d.getId()][l.getID()] = self.knownTT[d.getId()][l.getID()]
                
                    
                    
    
    def onTrip(self):
        '''
        Returns whether this driver is on trip (has departed and not yet arrived)
        
        '''
        return not self.arrived() \
            and self.currentEdge() is not None \
            and self.currentEdge() != ''
    
    def arrived(self):
        '''
        Returns whether driver has finished his trip
        
        '''
        #print traci.simulation.getArrivedIDList()
#        if self.getTraciId() in traci.simulation.getArrivedIDList():
#            self.tripFinished = True 
#            self.currentLink = None
            #print '%s finished! TT = %s' % (self.getId(), self.currentTravelTime())
        return self.tripFinished
    
    def getOrigin(self):
        return self.origin
    
    def setKnownTT(self, travel_times):
        self.knownTT = travel_times
        
    def setInfoAges(self, info_ages):
        self.info_ages = info_ages
        
    def knownTT(self, edge_id):
        return self.knownTT[edge_id]
    
    def known_travel_time(self, edge_id):
        return self.knownTT[edge_id]
    
    def info_age(self, edge_id):
        return self.info_ages[edge_id]
    
    def set_known_travel_time(self, edge_id, tt):
        self.knownTT[edge_id] = tt
        
    def set_info_age(self, edge_id, age):
        self.info_ages[edge_id] = age        
    
    
    def completedTripFraction(self):
        '''
        Returns how much of the trip is completed (# traversed links / # links in route)
        
        '''
        #numerator casted to float, otherwise would do integer division
        return float(len(self.traversedTripLinks())) / len(self.route)
            
    def getDestination(self):
        return self.destination
    
    def estimatedTT(self):
        '''
        Returns the estimated travel time on current route
        
        '''
        return sum([self.estimatedTTs[j] for j in self.route])
    
    def incReplanNumber(self):
        '''
        Increments the number of route replans performed by this driver
        
        '''
        self.numReplans += 1
    
    def updateStatus(self, commRange, curr_time):
        '''
        MUST BE CALLED AT EACH TIMESTEP
        Checks whether link was changed and keeps track of travel time spent in it.
        Should not be called more than once after car arrive at destination 
        
        '''
        
        #Untested behavior when this is called a timestep after vehicle arrival
        subsc = traci.vehicle.getSubscriptionResults(self.getTraciId())
        self.linkOnLastTimestep = self.currentLink
        #return <<fast here
        if self.arrived(): #prevents traci error when vehicle arrives
            self.currentLink = None
            self.posX        = None
            self.posY        = None
        else:
            #return <<fast here
            #warning: this makes currentLink be '' when vehicle hasn't departed yet
            self.currentLink = subsc[tc.VAR_ROAD_ID] #traci.vehicle.getRoadID(self.getTraciId())
            (self.posX, self.posY) = subsc[tc.VAR_POSITION]
#            if self.onTrip():
#                print self.posX, self.posY
        #return <<already slow
        if self.onTrip():
            self.travelTime += 1000
        #return <<already slow    
        #calculates the edges within ivc range
        #can be improved by updating only when driver changes zone    
        if self._isValidEdge(self.currentEdge()):
            myPos = traci.vehicle.getLanePosition(self.getTraciId())
            currEdge = self.roadNetwork.getEdge(self.currentEdge())
            
            if myPos + commRange > currEdge.getLength(): #TODO: pog
                self.interestEdges =  [currEdge] + currEdge._to.getIncoming() + currEdge._to.getOutgoing()
            
            elif myPos - commRange < 0:
                self.interestEdges = [currEdge] + currEdge._from.getIncoming() + currEdge._from.getOutgoing()
                
            else:
                self.interestEdges = [currEdge]
                
            #removes duplicates    
            self.interestEdges = list(set(self.interestEdges))
            
        if self.changedLink():
            
            self.previousLink = self.linkOnLastTimestep
            self.timeSpentOnLastLink = curr_time * 1000 - self.timeEnteredLastLink
            self.timeEnteredLastLink = curr_time * 1000 #traci.simulation.getCurrentTime()
        
            #updates the link data when it leaves or arrives to a new link
            if self._isValidEdge(self.previousLink):
                self.roadNetwork.getEdge(self.previousLink).drivers.remove(self)
                
            if self._isValidEdge(self.currentEdge()):
                self.roadNetwork.getEdge(self.currentEdge()).drivers.append(self)
            
            #updates the list of edges of interest
            if self._isValidEdge(self.currentEdge()):
                currEdge = self.roadNetwork.getEdge(self.currentEdge())
                self.interestEdges = \
                    currEdge._from.getIncoming() + currEdge._from.getOutgoing() + \
                    currEdge._to.getIncoming() + currEdge._to.getOutgoing()
                
                #removes duplicates    
                self.interestEdges = list(set(self.interestEdges))
        
            
            #self.travelTime += self.timeSpentOnLastLink
    
    
    def _isValidEdge(self, edge):
        '''
        Returns whether the edge is valid (not None, != '' and is not internal edge
        
        '''
        return edge is not None and edge != '' and ':' not in edge
    
    def acceptableDelay(self):
        '''
        Returns the factor saying how much the route can take longer to finish w/o 
        triggering replan. Ex.: if acceptableDelay() is 1.2, driver accepts its 
        current trip to be 20% longer than expected before triggering replan
        
        '''
        return self.delayTolerance 
    
    def canReplan(self):
        '''
        Returns whether this driver does en-route replanning and is within the 
        portion of the route that allows replanning
        
        '''
        return not self.isFromFleet() and DriverTypes.NOREPLAN not in self.type \
            and len(self.remainingTripLinks()) > 1 #\
            #and self.completedTripFraction() > 0.2 and self.completedTripFraction() < 0.7
            
    def isIvcCapable(self):
        '''
        Returns whether this driver is able to exchange messages
        
        '''
        #tests whether the vehicle type does not contains the 'noivc' sequence
        return DriverTypes.NOIVC not in self.type        
    
    def isFromFleet(self):
        '''
        Returns whether this driver belongs to a self-interested fleet
        
        '''
        #tests whether the vehicle type contains the 'fromFleet' sequence
        return DriverTypes.FROM_FLEET in self.type
    
    def fleetID(self):
        '''
        Returns the ID of the fleet this driver belongs to
        
        '''
        return self.type.split(DriverTypes.FROM_FLEET)[1]
    
    def prepareForTrip(self, tripNo, knownTT):
        '''
        Sets up for a trip
        
        '''
        self.tripNo         = tripNo #need to be updated to make correct calls to TRACI
        self.travelTime     = 0
        self.tripFinished   = False 
        self.numReplans     = 0
        self.posX           = None
        self.posY           = None
        self.last_comm_time = {} 
        self._newest_info_age = sys.maxsize
        self.route = traci.vehicle.getRoute(self.getTraciId())
        
        
        #print self.route
        for j in self.route:
            self.estimatedTTs[j] = knownTT[j]
        #self.estimatedTravelTime = sum([knownTT[j] for j in route])
        #TODO fix estimated travel time (does it need to consider internal links?)
        
        #drivers from experiment are white
        traci.vehicle.setColor(self.getTraciId(), self.getColor())
        traci.vehicle.subscribe(self.getTraciId(), (tc.VAR_ROAD_ID, tc.VAR_POSITION) )
        
    
    def updateETT(self, edges, knownTT):
        '''
        Update the estimated travel time for the given edges based on the knowledge base
        
        '''
        for j in edges:
            self.estimatedTTs[j] = knownTT[j] 
    
    def changedLink(self):
        #HACK to prevent bugs when driver leaves an internal edge and enters in another
        if not self._isValidEdge(self.linkOnLastTimestep) and not self._isValidEdge(self.currentLink):
            return False
        
        return self.linkOnLastTimestep != self.currentLink
    
    def getTraciId(self):
        '''
        Returns the id of the vehicle in the simulation for this trip
        
        '''
        return self.id + '_' + str(self.tripNo)
    
    def lastLinkId(self):
        '''
        Returns the id of the last link this driver has been on
        
        '''
        return self.linkOnLastTimestep
        
    def lastTT(self):
        '''
        Returns the travel time spent on last link
        
        '''
        return self.timeSpentOnLastLink
    
    def traversedTripLinks(self):
        '''
        Returns the links that this driver traversed on the current trip.
        EXCLUDES the current link of the driver
        
        '''
        
        #TODO: check whether current link should be included
        
        #returns the whole route if already arrived
        if self.arrived(): 
            return self.getRoute()
        
        #returns empty list if trip has not started
        if not self.onTrip():
            return []
        
        #currRoute = copy(self.route)
        try:
            cLinkPos = self.route.index(self.currentEdge())
        except ValueError as e:
            #an internal link will not be on the route and raise this error
            if ':' not in self.currentEdge():
                #check, because if current link is not internal, then we have an error
                raise RuntimeError("Non internal edge is not on the route: " + self.currentEdge())
            #if current link is internal, then get the position of the previous one
            #print self.currentEdge(), self.previousLink
            try:
                cLinkPos = self.route.index(self.previousLink)
            except ValueError as e:
                print 'ERROR! previousLink=%s not on route?' % self.previousLink
                print 'My route: ', self.route
                print 'Curr. edge: ', self.currentEdge()
                exit()
            
        
        #for i in range(0,cLinkPos):
        #    traversed.append(self.route[i])
        traversed = self.route[0 : cLinkPos]
        return traversed
    
    def getColor(self):
        '''
        Returns an array with the color of this car, depending on its type
        
        '''
        
        #prevents error when using multiple fleets:
        if self.isFromFleet():
            return DriversColors[DriverTypes.FROM_FLEET]
        
        return DriversColors[self.getType()]
    
    def getRoute(self):
        '''
        Returns the current route of this driver
        
        '''
        return self.route
    
    def setRoute(self, theRoute):
        '''
        Updates the route of this driver via TraCI
        
        '''
        self.route = theRoute
        traci.vehicle.setRoute(self.getTraciId(), self.route)
    
    def currentEdge(self):
        '''
        Returns the current edge the vehicle is in
        
        '''
        return self.currentLink
        
    
    def currentTravelTime(self):
        '''
        Returns the travel time spent on the current trip
        
        '''
        #divides per 1000 to obtain tt in seconds
        #-1000 is because traci time starts at 1000 instead of zero
        return self.travelTime / 1000 # - 1000 +\
             #traci.simulation.getCurrentTime() - self.timeEnteredLastLink
    
    def remainingTripLinks(self):
        '''
        Returns a list of links that have not yet been traversed in the current trip
        (current is INCLUDED)
        
        '''
        #returns empty list if already arrived
        if self.arrived(): 
            return []
        
        #returns the whole route if trip has not started
        if not self.onTrip():
            return self.route
        currRoute = copy(self.route)
#        print currRoute
#        import pprint
#        pprint.pprint(self.currentEdge())
        try:
            cLinkPos = currRoute.index(self.currentEdge())
        except ValueError as e:
            #exception occurs when currentEdge() is an internal link
            #in this case, cLinkPos will consider the previous link position
            if ':' not in self.currentEdge():
                print 'WARNING! %s: non internal edge %s is not in route' % (self.getId(), self.currentEdge())
                
                if self.getRoute() != traci.vehicle.getRoute(self.getTraciId()):
                    print 'Changing old route %s to %s' % (self.getRoute(), traci.vehicle.getRoute(self.getTraciId()))
                    self.route = traci.vehicle.getRoute(self.getTraciId())
                    return [] 
                    
                else:
                    print '%s route: %s ' % (self.getId(), self.getRoute())
                    print '%s traci-route: %s ' % (self.getId(), traci.vehicle.getRoute(self.getTraciId()))
                    raise RuntimeError("Non internal edge %s is not in driver route" % self.currentEdge())
                
            cLinkPos = currRoute.index(self.previousLink)
        
        #print self.currentLink, self.previousLink, cLinkPos
        
        currRoute = self.route[cLinkPos : len(self.route)]
        
        return currRoute
    
    def debug(self):
        #prints id, currentLink, estimatedTT, lastTT, completedTripFraction, timeEnteredLastLink, 
        #currentTravelTime, currentSimulationtime
        print self.id +\
            '\t' + str(self.type) +\
            '\t' + str(self.currentLink) + '\t' + str(self.estimatedTT()) +\
            '\t' + str(self.lastTT()) + '\t' + str(self.completedTripFraction()) +\
            '\t' + str(self.timeEnteredLastLink) + '\t' + str(self.currentTravelTime()) +\
            '\t' + str(traci.simulation.getCurrentTime())
