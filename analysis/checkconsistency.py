'''
Checks whether vehicle types are consistent in .rou.xml and resulting .csv files

Created on May 27, 2013

@author: anderson

'''
import sys
import xml.etree.ElementTree as ET
from optparse import OptionParser

def last_header(fname):
    '''
    Returns the lines corresponding to the last header found in file
    
    '''
    f = open(fname)
    flines = f.readlines()

    for i in range(len(flines)):
        if flines[i][0] == 'x':
            idline  = flines[i]
            typeline= flines[i+1]
    
    return (idline, typeline)
    
   
def checkconsistency(roufile, csvfile):
    (idline, typesline) = last_header(csvfile)
    
    ids = idline.strip().split(',')[1:]
    types = typesline.strip().split(',')[1:]
    
    veh_types = dict((vid,typ) for (vid,typ) in zip(ids,types))
    
    rtree = ET.parse(roufile)
    
    for veh in rtree.getroot():
        if veh_types[veh.get('id')] != veh.get('type'):
            print 'Type mismatch for %s - csv: %s, rou:%s' %\
             (veh.get('id'), veh_types[veh.get('id')], veh.get('type'))
             
def parse_args():
    parser = OptionParser()
            
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
    