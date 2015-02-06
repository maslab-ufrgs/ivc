'''
Created on 20/08/2012

@author: artavares
'''
import sys, os, unittest
import xml.etree.ElementTree as ET

sys.path.append(os.path.join('..','src'))
from application import Application
from vehicleTyper import VehicleTyper


class Test(unittest.TestCase):


    def testApplication(self):
        args = [
            '-r','input/inputPart1.rou.xml,input/inputPart2.rou.xml',
            '-t','input/simpleInput.vtp.xml',
            '-o','theOutput.rou.xml'
        ]
        
        app = Application(args)
        
        vehTypes = {
            VehicleTyper.FROM_FLEET    : 0, 
            VehicleTyper.IVC_REPLAN    : 0,
            VehicleTyper.IVC_NOREPLAN  : 0,
            VehicleTyper.NOIVC_REPLAN  : 0,
            VehicleTyper.NOIVC_NOREPLAN: 0
        } 
        
        expectedVehTypes = {
            VehicleTyper.FROM_FLEET    : 50, 
            VehicleTyper.IVC_REPLAN    : 10,
            VehicleTyper.IVC_NOREPLAN  : 50,
            VehicleTyper.NOIVC_REPLAN  : 3,
            VehicleTyper.NOIVC_NOREPLAN: 25
        }    
        total = sum(expectedVehTypes.values())
        scale = 10000
        
        tree = ET.parse('theOutput.rou.xml')
        root = tree.getroot()
        
        self.assertEquals(scale, len(root))
        
        for element in root:
            vehTypes[element.get('type')] += 1
        
        #accepts 2% of error
        self.assertAlmostEquals(
            expectedVehTypes[VehicleTyper.FROM_FLEET] * scale / total, 
            vehTypes[VehicleTyper.FROM_FLEET], None, VehicleTyper.FROM_FLEET, 100
        )
        
        self.assertAlmostEquals(
            expectedVehTypes[VehicleTyper.IVC_REPLAN] * scale / total, 
            vehTypes[VehicleTyper.IVC_REPLAN], None, VehicleTyper.IVC_REPLAN, 100
        )
        
        self.assertAlmostEquals(
            expectedVehTypes[VehicleTyper.IVC_NOREPLAN] * scale / total, 
            vehTypes[VehicleTyper.IVC_NOREPLAN], None, VehicleTyper.IVC_NOREPLAN, 100
        )
        
        self.assertAlmostEquals(
            expectedVehTypes[VehicleTyper.NOIVC_REPLAN] * scale / total, 
            vehTypes[VehicleTyper.NOIVC_REPLAN], None, VehicleTyper.NOIVC_REPLAN, 100
        )
        
        self.assertAlmostEquals(
            expectedVehTypes[VehicleTyper.NOIVC_NOREPLAN] * scale / total, 
            vehTypes[VehicleTyper.NOIVC_NOREPLAN], None, VehicleTyper.NOIVC_NOREPLAN, 100
        )
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSingleInput']
    unittest.main()