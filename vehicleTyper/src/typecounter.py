import xml.etree.ElementTree as ET
from optparse import OptionParser, OptionGroup
import logging, sys, random


vehTypes = {}

tree = ET.parse(sys.argv[1])
root = tree.getroot()
    
#for-switch is bad practice, but for code complexity reduction it is used here
for element in root:
    key = element.get('type')
    if not key in vehTypes:
        vehTypes[key] = 0
        
    vehTypes[key] = vehTypes[key] + 1
    
    
for key,val in vehTypes.iteritems():
    print '%s\t%s' % (key, val)