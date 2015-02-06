"""This script reads a xml with the ammount of vehicle types and changes SUMO's .rou.xml
redefining vehicle types"""

import xml.etree.ElementTree as ET
from optparse import OptionParser, OptionGroup
import logging, sys, random



class VehicleTyper(object):
    
    #vehicle type names definition
    FROM_FLEET      = 'fromFleet'
    IVC             = 'ivc'
    NOIVC           = 'noivc'
    REPLAN          = 'replan'
    NOREPLAN        = 'noreplan'
    IVC_REPLAN      = 'ivc-replan'
    IVC_NOREPLAN    = 'ivc-noreplan'
    NOIVC_REPLAN    = 'noivc-replan'
    NOIVC_NOREPLAN  = 'noivc-noreplan'
    
    """Vehicle types. The noivc-replan ammount should be zero, because it makes no sense
    to replan when one has no updated information about traffic"""
    vehTypes = {
        FROM_FLEET    : 0, 
        IVC_REPLAN    : 0,
        IVC_NOREPLAN  : 0,
        NOIVC_REPLAN  : 0,
        NOIVC_NOREPLAN: 0
    }       
    
    totalAmmount= 0
    typesFile   = None
    routesFiles = None
        
        
    def __init__(self, typesFile, routesFiles):
        self.typesFile   = typesFile
        self.routesFiles = routesFiles
        self.fillVehicleTypes()
        self.calculateTotals()
    
    def fillVehicleTypes(self):
        """Parses the vehicle types file and fills the ammount in vehTypes dict
        """
        tree = ET.parse(self.typesFile)
        root = tree.getroot()
        
        #for-switch is bad practice, but for code complexity reduction it is used here
        for element in root:
            vehFeatures = []
            
            #if the element is about the fleet vehicles, the ammount will be added to it
            if element.get(self.FROM_FLEET) is not None and element.get(self.FROM_FLEET) == 'yes':
                vehFeatures.append(self.FROM_FLEET)
            
            #...otherwise, it will be added to ivc or noivc, depending on the ivc attribute
            else:
                if element.get(self.IVC) is None or element.get(self.IVC) == 'no':
                    vehFeatures.append(self.NOIVC)
                    
                else: vehFeatures.append(self.IVC)
                
                #check whether en-route replanning will be activated or not
                if element.get(self.REPLAN) is None or element.get(self.REPLAN) == 'no':
                    vehFeatures.append(self.NOREPLAN)
                else:    
                    vehFeatures.append(self.REPLAN)
                
            #assembles the vehicle type name from the features detected
            vehTypeName = '-'.join(vehFeatures)
            
            #sets the ammount of vehicles of that type
            self.vehTypes[vehTypeName] = int(element.get('proportion'))
        
    def calculateTotals(self):
        """Adds up the ammounts of each vehicle type and stores the total
        """
        self.totalAmmount = 0
        for type,ammount in self.vehTypes.iteritems():
            self.totalAmmount += int(ammount)
            
        return self.totalAmmount
    
    def selectVehicleType(self):
        """Selects a vehicle type with a probability according to its proportion
        related to the total ammount of vehicle types.
        Algorithm source: 
        http://stackoverflow.com/questions/3655430/selection-based-on-percentage-weighting/3655453#3655453
        """
        
        variate = random.random() * self.totalAmmount
        cumulative = 0.0
        for item, weight in self.vehTypes.items():
            cumulative += weight
            if variate < cumulative:
                return item
        return item # Shouldn't get here, but just in case of rounding...        
    def writeOutput(self, routeFile):
        """Parses the input route files, selects types for each vehicle
        and writes the output route inFile with the typed vehicles. It works with only
        one input inFile by now"""
        
        
        mainRoot = ET.Element('routes')
        
        #traverses all files in the received inFile list
        for inFile in self.routesFiles:
            tree = ET.parse(inFile)
            secRoot = tree.getroot()
            
            #appends all elements found in the created mainRoot
            for element in secRoot:
                element.set('type',self.selectVehicleType())
                mainRoot.append(element)
                
        #writes the resulting xml structure in the output inFile
        mainTree = ET.ElementTree(mainRoot)        
        mainTree.write(routeFile)
        
        
    
    def loadVehicles(self, routeFiles):
        for filename in routeFiles:
            try:
                parser.parse(filename)
            except IOError as err:
                print 'Error reading routes file:', err 
                sys.exit(1)

class StrictVehicleTyper(VehicleTyper):
    
    proportion = 1
    
    def setProportion(self, factor):
        '''Generates the exact proportion defined in .vtp.xml multiplied by this factor
        '''
        self.proportion = factor
        
        for typ,num in self.vehTypes.iteritems():
            self.vehTypes[typ] *= factor 
        
    
    def selectVehicleType(self):
        """Selects a vehicle type and decrement its counter 
        """

        number = 0
        while number == 0:
            typ,number = random.choice(self.vehTypes.items())
        self.vehTypes[typ] -= 1
        
        return typ
    