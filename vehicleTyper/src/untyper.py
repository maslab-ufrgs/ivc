import xml.etree.ElementTree as ET
import sys

tree    = ET.parse(sys.argv[1])
#dTime   = sys.argv[3] if len(sys.argv) > 3 else '0.00'
root = tree.getroot()

for element in root:
    del element.attrib['type']
    
    
tree.write(sys.argv[2])