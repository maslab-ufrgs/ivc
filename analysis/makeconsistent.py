'''
Checks whether vehicle types are consistent in .rou.xml and resulting .csv files

IT DOES NOT CORRECT FILES, CONTRARILY TO WHAT NAME SAYS.

Created on May 27, 2013

@author: anderson

'''
import sys
import xml.etree.ElementTree as ET
from optparse import OptionParser

def from_last_header(fname):
    '''
    Returns the lines starting from the last header found in file
    
    '''
    f = open(fname)
    flines = f.readlines()
    
    filtlines = []
    
    for i in range(len(flines)):
        if flines[i][0] == 'x':
            filtlines  = flines[i:]
    
    return filtlines
    
   
def checkconsistency(roufile, csvfile):
    lines = from_last_header(csvfile)
    
    ids = lines[0].strip().split(',')[1:]
    types = lines[1].strip().split(',')[1:]
    
    veh_types = dict((vid,typ) for (vid,typ) in zip(ids,types))
    
    rtree = ET.parse(roufile)
    
    num_adjusts = 0
    for veh in rtree.getroot():
        #if type in .csv is different from .rou, it is overwritten by the value in .rou
        if veh_types[veh.get('id')] != veh.get('type'):
            veh_types[veh.get('id')] = veh.get('type')
            num_adjusts += 1
            
    #writes the results file with correct header
    
    print 'DONE. %d corrections made.' % num_adjusts
             
def parse_args():
    parser = OptionParser(
        description='''Checks whether vehicle types are consistent in .rou.xml and resulting .csv files
IT DOES NOT CORRECT FILES, CONTRARILY TO WHAT NAME SAYS.''')
            
    parser.add_option(
        '-r', '--route-file', type=str, help = 'path to the .rou.xml data'
    )
    
    parser.add_option(
        '-c', '--csv-file', help='path to the .csv file', type=str
    )
    
    parser.add_option(
        '-o', '--out-prefix', help='prefix of the output file to be generated', type=str,
        default = 'odcmp_'
    )
    
    parser.add_option(
        '-i', '--iterations', help='number of iterations to consider', type=int,
        default=10
    )
    
    return parser.parse_args(sys.argv)
    
if __name__ == '__main__':
    (options, args) = parse_args()
    checkconsistency(options.route_file, options.csv_file)    
    