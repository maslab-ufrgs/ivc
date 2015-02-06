import os, sys, unittest
import xml.etree.ElementTree as ET

#sys.path.append(os.path.realpath('..'))
sys.path.append(os.path.join('..','src'))

#print sys.path
from vehicleTyper import VehicleTyper

class TestVehicleTyper(unittest.TestCase):


    def test_fillVehicleTypes(self):
        expectedVehTypes = {
            VehicleTyper.FROM_FLEET    : 50, 
            VehicleTyper.IVC_REPLAN    : 10,
            VehicleTyper.IVC_NOREPLAN  : 50,
            VehicleTyper.NOIVC_REPLAN  : 3,
            VehicleTyper.NOIVC_NOREPLAN: 25
        } 
        
        sample = VehicleTyper('input/simpleInput.vtp.xml',None)
        self.assertEqual(expectedVehTypes, sample.vehTypes)
        
    def test_getTotals(self):
        sample = VehicleTyper('input/simpleInput.vtp.xml',None)
        self.assertEqual(138, sample.calculateTotals())
        
    def test_selectVehicleType(self):
        vehTypes = {
            VehicleTyper.FROM_FLEET    : 0, 
            VehicleTyper.IVC_REPLAN    : 0,
            VehicleTyper.IVC_NOREPLAN  : 0,
            VehicleTyper.NOIVC_REPLAN  : 0,
            VehicleTyper.NOIVC_NOREPLAN: 0
        } 
        
        sample = VehicleTyper('input/simpleInput.vtp.xml',None)
        
        #selects 10k vehicle types and stores how many times each type was selected
        scale = 10000
        for i in range(0,scale):
            vehTypes[sample.selectVehicleType()] += 1
        
        #compare the selected types with the ones in the file (properly scaled)
        #accepts a error of 2% (100 units above or below)
        expectedVehTypes = {
            VehicleTyper.FROM_FLEET    : 50, 
            VehicleTyper.IVC_REPLAN    : 10,
            VehicleTyper.IVC_NOREPLAN  : 50,
            VehicleTyper.NOIVC_REPLAN  : 3,
            VehicleTyper.NOIVC_NOREPLAN: 25
        }    
        total = sum(expectedVehTypes.values())
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
        
    def test_typedOutputFile(self):
        vehTypes = {
            VehicleTyper.FROM_FLEET    : 0, 
            VehicleTyper.IVC_REPLAN    : 0,
            VehicleTyper.IVC_NOREPLAN  : 0,
            VehicleTyper.NOIVC_REPLAN  : 0,
            VehicleTyper.NOIVC_NOREPLAN: 0
        } 
        
        sample = VehicleTyper('input/simpleInput.vtp.xml',['input/input.rou.xml'])
        expectedVehTypes = {
            VehicleTyper.FROM_FLEET    : 50, 
            VehicleTyper.IVC_REPLAN    : 10,
            VehicleTyper.IVC_NOREPLAN  : 50,
            VehicleTyper.NOIVC_REPLAN  : 3,
            VehicleTyper.NOIVC_NOREPLAN: 25
        }    
        total = sum(expectedVehTypes.values())
        scale = 10000
        
        sample.writeOutput('theOutput.rou.xml')
        
        tree = ET.parse('theOutput.rou.xml')
        root = tree.getroot()
        
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

    def test_multipleInputFiles(self):
        inputFiles = ['input/inputPart1.rou.xml', 'input/inputPart2.rou.xml']
        
        vehTypes = {
            VehicleTyper.FROM_FLEET    : 0, 
            VehicleTyper.IVC_REPLAN    : 0,
            VehicleTyper.IVC_NOREPLAN  : 0,
            VehicleTyper.NOIVC_REPLAN  : 0,
            VehicleTyper.NOIVC_NOREPLAN: 0
        } 
        
        sample = VehicleTyper('input/simpleInput.vtp.xml',inputFiles)
        expectedVehTypes = {
            VehicleTyper.FROM_FLEET    : 50, 
            VehicleTyper.IVC_REPLAN    : 10,
            VehicleTyper.IVC_NOREPLAN  : 50,
            VehicleTyper.NOIVC_REPLAN  : 3,
            VehicleTyper.NOIVC_NOREPLAN: 25
        }    
        total = sum(expectedVehTypes.values())
        scale = 10000
        
        sample.writeOutput('theOutput.rou.xml')
        
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
    #import sys;sys.argv = ['', 'Test.testParser']
    unittest.main()        