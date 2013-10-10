'''
Contains classes to avoid overload in the road networks

Can be used as a standalone or imported in another script

'''
from optparse import OptionParser, OptionGroup
import logging, sys, os, random
import traci, sumolib

class OverloadControl (object):
    #net = sumolib.net.readNet(options.netfile)
    maxAllowed = sys.maxsize #the maximum #of vehicles allowed in the road network
    exclude = None           #a vehicle containing this string in its id won't be prevented from entering the network
    
    def __init__(self, maxAllowed, exclude):
        self.maxAllowed = maxAllowed
        self.exclude    = exclude
        
    def act(self):
        '''Must be called at each timestep. It checks the # of vehicles in the network
        and removes vehicles that entered in this timestep if load > maximum
        '''
        
        exceeding = len(traci.vehicle.getIDList()) - self.maxAllowed
        if exceeding <= 0:
            return
        
        departed = traci.simulation.getDepartedIDList()
        
        maxRemovals = min(exceeding, len(departed))
        excluded = 0
        for i in range(0, maxRemovals):
            if self.exclude is not None and self.exclude in departed[i]:
                #print departed[i], ' preserved.'
                continue
            
            traci.vehicle.remove(departed[i])
            excluded += 1
            
        #print 'Excluded %d vehicles in this timestep.' % excluded    
            
class AuxiliaryOverloadControl(OverloadControl):
    maxAllowed = sys.maxsize #the maximum #of auxiliary vehicles allowed in the network 
    exclude = None           #a vehicle containing this string in its id won't be prevented from entering the network
    
    def __init__(self, maxAllowed, exclude = None):
        self.maxAllowed = maxAllowed
        self.exclude    = exclude
        
    def act(self):
        '''Must be called at each timestep. It checks the # of auxiliary vehicles in the network
        and removes vehicles that entered in this timestep if load > maximum
        '''
        
        vehList = traci.vehicle.getIDList()
        numAux = 0
        
        for veh in vehList: 
            if not self.exclude in veh: numAux += 1
        
        exceeding = numAux - self.maxAllowed
        
        #sys.stdout.write('\r%d total, %d aux, %d exceeding...' % (len(vehList), numAux, exceeding))
        
        if exceeding <= 0:
            return
        
        departed = traci.simulation.getDepartedIDList()
        
        maxRemovals = min(exceeding, len(departed))
        excluded = 0
        for i in range(0, maxRemovals):
            if self.exclude is not None and self.exclude in departed[i]:
                #print departed[i], ' preserved.'
                continue
            
            traci.vehicle.remove(departed[i])
            excluded += 1    
            
        #print '%d removed.' % excluded

if __name__ == '__main__':
    
    optParser = OptionParser()

    optParser.add_option("-m", "--max-allowed", type="int", dest="maxallowed",
                         default=100, help="maximum allowed number of drivers")
    optParser.add_option("-b", "--begin", type="int", default=0, help="begin time")
    optParser.add_option("-e", "--end", type="int", default=4000, help="end time")
    optParser.add_option("-p", "--port", type="int", default=8813, help="TraCI port")
    optParser.add_option("-x", "--exclude", type="string", default=None, dest='exclude',
        help="Does not prevent drivers whose ID have the given value from entering the network")    
    
    #optParser.add_option("-s", "--seed", type="int", help="random seed")
    
    (options, args) = optParser.parse_args()
        
    traci.init(options.port)
    
    #controller = OverloadControl(options.maxallowed, options.exclude)
    controller = AuxiliaryOverloadControl(options.maxallowed, options.exclude)
    
    if options.begin > 0:
        traci.simulationStep(options.begin * 1000)
        
    for i in range(options.begin, options.end):
        traci.simulationStep()
        controller.act()
    
    traci.close()