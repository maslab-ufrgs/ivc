'''
Created on 31/08/2012

@author: artavares
'''

import sys, os
import traci
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
    
    def getIvcDriversInRange(self,driver,commRange):
        """
        Returns a list of drivers (ivc-capable) closer than 'commRange' 
        meters from the given driver
        """
        #if not driver.onTrip():
         #   return []
        
        #print '    Getting neighbors for vehicle %s' % driver.getId()
        drvPos = traci.vehicle.getPosition(driver.getTraciId())
        
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
            if driver == otherDriver or otherDriver.arrived() or not otherDriver.isIvcCapable(): 
                continue
            #print '        testing %s' % otherDriver.getId()
            otherPos = traci.vehicle.getPosition(otherDriver.getTraciId())

            #print otherPos
            theDist = eucDist(drvPos[0], drvPos[1], otherPos[0], otherPos[1])
#            traci.simulation.getDistance2D(
#                drvPos[0],
#                drvPos[1], 
#                otherPos[0],
#                otherPos[1]
#            )
            
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
    """Basically an enum encoding the driver types
    """
    
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
    
    type        = None
    roadNetwork = None
    tripNo      = 0
    travelTime  = 0
    departTime = 0
    
    DEPART_POS = 5.10
    
    delayTolerance      = 1.3
    estimatedTravelTime = 0
    estimatedTTs = collections.defaultdict(dict)
    
    route = None
    
    numReplans = 0
    
    interestEdges = []
    
    def __init__(self,id,type,origin, destination, depart, roadNetwork):
        
        self.id = id
        self.type = type
        self.origin = origin
        self.destination = destination
        self.departTime = float(depart)
        self.roadNetwork = roadNetwork
        
        self.linkOnLastTimestep = None
        self.currentLink        = None
        self.previousLink       = None #previous link on driver's route
        
        self.timeSpentOnLastLink = 0
        self.timeEnteredLastLink = 0
        
        self.tripFinished = False
        
   
    def getId(self):
        return self.id  
    
    def getType(self):
        return self.type
    
    def getDepartTime(self):
        return self.departTime 
    
    def getSpeed(self):
        '''Returns the ratio: distance traversed / travel time spent; a.k.a.: speed
        '''
        travDistance = 0
        for l in self.route:
            travDistance += self.roadNetwork.getEdge(l).getLength()
                
        return travDistance / self.currentTravelTime()
            
    def getInterestEdges(self):
        '''Returns the set of edges in the range of IVC for this driver 
        '''
        return self.interestEdges
    
    def getNumHops(self):
        '''Returns the number of edges in the driver's route
        '''
        return len(self.route)
    
    def getNumReplans(self):
        '''Returns the number of times that this driver recalculated its route
        '''
        return self.numReplans
            
    def traveledDistance(self):
        '''Returns the distance (#links x length) for each link traversed by the driver'''
        
        #Assumes that lengths of the same edge are equal (which is the case for the 6x6 grid)
        travDistance = 0
        for l in self.traversedTripLinks():
            travDistance += self.roadNetwork.getEdge(l).getLength()
        
        return travDistance
    
    def onTrip(self):
        """
        Returns whether this driver is on trip (has departed and not yet arrived)
        """
        return not self.arrived() \
            and self.currentEdge() is not None \
            and self.currentEdge() != ''
    
    def arrived(self):
        """
        Returns whether driver has finished his trip
        """
        #print traci.simulation.getArrivedIDList()
        if self.getTraciId() in traci.simulation.getArrivedIDList():
            self.tripFinished = True 
            self.currentLink = None
            #print '%s finished! TT = %s' % (self.getId(), self.currentTravelTime())
        return self.tripFinished
    
    def getOrigin(self):
        return self.origin
    
    def completedTripFraction(self):
        """
        Returns how much of the trip is completed (# traversed links / # links in route)
        """
        #numerator casted to float, otherwise would do integer division
        return float(len(self.traversedTripLinks())) / len(self.route)
            
    def getDestination(self):
        return self.destination
    
    def estimatedTT(self):
        """
        Returns the estimated travel time on current route
        """
        return sum([self.estimatedTTs[j] for j in self.route])
    
    def incReplanNumber(self):
        '''Increments the number of route replans performed by this driver
        '''
        self.numReplans += 1
    
    def updateStatus(self):
        """
        MUST BE CALLED AT EACH TIMESTEP
        Checks whether link was changed and keeps track of travel time spent in it.
        Should not be called more than once after car arrive at destination 
        """
        
        #Untested behavior when this is called a timestep after vehicle arrival
        
        self.linkOnLastTimestep = self.currentLink
        
        if self.arrived(): #prevents traci error when vehicle arrives
            self.currentLink = None
        else:
            #warning: this makes currentLink be '' when vehicle hasn't departed yet
            self.currentLink = traci.vehicle.getRoadID(self.getTraciId())
        
        if self.onTrip():
            self.travelTime += 1000
            
        #calculates the edges within ivc range
        #can be improved by updating only when driver changes zone    
        if self._isValidEdge(self.currentEdge()):
            myPos = traci.vehicle.getLanePosition(self.getTraciId())
            currEdge = self.roadNetwork.getEdge(self.currentEdge())
            
            if myPos + 100 > currEdge.getLength(): #TODO: pog
                self.interestEdges =  [currEdge] + currEdge._to.getIncoming() + currEdge._to.getOutgoing()
            
            elif myPos - 100 < 0:
                self.interestEdges = [currEdge] + currEdge._from.getIncoming() + currEdge._from.getOutgoing()
                
            else:
                self.interestEdges = [currEdge]
                
            #removes duplicates    
            self.interestEdges = list(set(self.interestEdges))
            
        if self.changedLink():
            
            self.previousLink = self.linkOnLastTimestep
            self.timeSpentOnLastLink = traci.simulation.getCurrentTime() - self.timeEnteredLastLink
            self.timeEnteredLastLink = traci.simulation.getCurrentTime()
        
            #updates the link data when it leaves or arrives to a new link
            if self._isValidEdge(self.previousLink):
                self.roadNetwork.getEdge(self.previousLink).drivers.remove(self)
                
            if self._isValidEdge(self.currentEdge()):
                self.roadNetwork.getEdge(self.currentEdge()).drivers.append(self)
            
            #updates the list of edges of interest
#            if self._isValidEdge(self.currentEdge()):
#                currEdge = self.roadNetwork.getEdge(self.currentEdge())
#                self.interestEdges = \
#                    currEdge._from.getIncoming() + currEdge._from.getOutgoing() + \
#                    currEdge._to.getIncoming() + currEdge._to.getOutgoing()
#                
#                #removes duplicates    
#                self.interestEdges = list(set(self.interestEdges))
        
            
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
        """
        Returns whether this driver does en-route replanning and is within the 
        portion of the route that allows replanning
        """
        return not self.isFromFleet() and self.type.find(DriverTypes.NOREPLAN) == -1 \
            and self.completedTripFraction() > 0.2 and self.completedTripFraction() < 0.7
            
    def isIvcCapable(self):
        """
        Returns whether this driver is able to exchange messages
        """
        #tests whether the vehicle type does not contains the 'noivc' sequence
        return self.type.find(DriverTypes.NOIVC) == -1        
    
    def isFromFleet(self):
        """
        Returns whether this driver belongs to the self-interested fleet
        """
        #tests whether the vehicle type contains the 'fromFleet' sequence
        return self.type.find(DriverTypes.FROM_FLEET) > -1
    
    def prepareForTrip(self,tripNo,knownTT):
        """
        Sets up for a trip
        """
        
        self.tripNo         = tripNo #need to be updated to make correct calls to TRACI
        self.travelTime     = 0
        self.tripFinished   = False 
        self.numReplans     = 0
        
        self.route = traci.vehicle.getRoute(self.getTraciId())
        
        #print self.route
        for j in self.route:
            self.estimatedTTs[j] = knownTT[j]
        #self.estimatedTravelTime = sum([knownTT[j] for j in route])
        #TODO fix estimated travel time (does it need to consider internal links?)
        
        #drivers from experiment are white
        traci.vehicle.setColor(self.getTraciId(), self.getColor())
        
    
    def updateETT(self, edges, knownTT):
        """
        Update the estimated travel time for the given edges based on the knowledge base
        """
        for j in edges:
            self.estimatedTTs[j] = knownTT[j] 
    
    def changedLink(self):
        #HACK to prevent bugs when driver leaves an internal edge and enters in another
        if not self._isValidEdge(self.linkOnLastTimestep) and not self._isValidEdge(self.currentLink):
            return False
        
        return self.linkOnLastTimestep != self.currentLink
    
    def getTraciId(self):
        """
        Returns the id of the vehicle in the simulation for this trip
        """
        return self.id + '_' + str(self.tripNo)
    
    def lastLinkId(self):
        """
        Returns the id of the last link this driver has been on
        """
        return self.linkOnLastTimestep
        
    def lastTT(self):
        """
        Returns the travel time spent on last link
        """
        return self.timeSpentOnLastLink
    
    def traversedTripLinks(self):
        """
        Returns the links that this driver traversed on the current trip.
        EXCLUDES the current link of the driver
        """
        
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
        return DriversColors[self.getType()]
    
    def getRoute(self):
        """
        Returns the current route of this driver
        """
        return self.route
    
    def setRoute(self, theRoute):
        """
        Updates the route of this driver via TraCI
        """
        self.route = theRoute
        traci.vehicle.setRoute(self.getTraciId(), self.route)
    
    def currentEdge(self):
        """
        Returns the current edge the vehicle is in
        """
        return self.currentLink
        
    
    def currentTravelTime(self):
        """
        Returns the travel time spent on the current trip
        """
        #divides per 1000 to obtain tt in seconds
        #-1000 is because traci time starts at 1000 instead of zero
        return self.travelTime / 1000 # - 1000 +\
             #traci.simulation.getCurrentTime() - self.timeEnteredLastLink
    
    def remainingTripLinks(self):
        """
        Returns a list of links that have not yet been traversed in the current trip
        (current is INCLUDED)
        """
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
                raise RuntimeError("Non internal edge is not on the route")

            cLinkPos = currRoute.index(self.previousLink)
        
        #print self.currentLink, self.previousLink, cLinkPos
        
        currRoute = self.route[cLinkPos : len(self.route)]
        
        return currRoute
    
    def debug(self):
        #print "ID\tType\tOrigin\tDestination\tLastLink\tCurrLink\tlastTT\tlastEntryTime"
        #print self.id + '\t' + self.type + '\t' + self.origin + '\t' + self.destination +\
        print self.id +\
            '\t' + str(self.currentLink) + '\t' + str(self.estimatedTT()) +\
            '\t' + str(self.lastTT()) + '\t' + str(self.completedTripFraction()) +\
            '\t' + str(self.timeEnteredLastLink) + '\t' + str(self.currentTravelTime()) +\
            '\t' + str(traci.simulation.getCurrentTime())
