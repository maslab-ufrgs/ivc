'''
This script reads a .rou.xml file and an experiment data file.
It generates three outputs containing the average performance of:

1) fleet drivers
2) honest drivers with same origin and destination of a fleet driver
3) honest drivers with different origin and destination of all fleet drivers 

Created on May 24, 2013

@author: anderson

'''
import sys
import xml.etree.ElementTree as ET
import numpy as np
from optparse import OptionParser

def againstfleetods(routefile, data_file, out_prefix, num_iter, stddev=False):
    f_ods = fleet_ods(routefile)
    #print f_ods
    rtree = ET.parse(routefile)
    
    same_ods = {}
    diff_ods = {}
    for veh in rtree.getroot():
        if veh.get('id') in f_ods:
            continue
        
        route = veh[0].get('edges').split(' ')
        if (route[0],route[-1]) in f_ods.values():
            same_ods[veh.get('id')] = (route[0],route[-1]) 
            
        else:
            diff_ods[veh.get('id')] = (route[0],route[-1])
            
    in_file = open(data_file, 'r') #.readlines()
    
    #ids are in 1st line from 2nd col onwards
    ids = in_file.readline().strip().split(',')[1:]
    
    #reads data file ignoring first column and the rows after num_iter
    data = np.genfromtxt(data_file, skip_header = 2, delimiter=',')[:num_iter,1:] 
    
    other_array = None#data
    same_array = None #np.array([])
    flt_array = None #np.array([])
    
    #print data[:,0].reshape(10,1)    
    #traverses the data columnwise, separating the fleet, same-od and diff-od columns
    #col = 0
    for col in range(len(ids)):
        
        if ids[col] in f_ods:
            if flt_array is None:
                flt_array = data[:,col].reshape(num_iter, 1)
            else:
                flt_array = np.append(flt_array, data[:,col].reshape(num_iter, 1), 1)
            
            #print'flt',col,ids[col],flt_array#.reshape(10,1)
            #exit()
        elif ids[col] in same_ods:            
            if same_array is None:
                #print col, data[:,col]
                same_array = data[:,col].reshape(num_iter, 1)
            else:
                same_array = np.append(same_array, data[:,col].reshape(num_iter, 1), 1)
                
            #print 'same', same_array, col,ids[col] , data[:,col].reshape(10,1)
            
        else:
            if other_array is None:
                other_array = data[:,col].reshape(num_iter, 1)
            else:
                other_array = np.append(other_array, data[:,col].reshape(num_iter, 1), 1)
            #print 'oth', col,ids[col], data[:,col]
            
    #generates the output files
    np.savetxt('%sothers.csv' % out_prefix, np.mean(other_array,axis=1), '%.5f', ',')
    np.savetxt('%sfleet.csv' % out_prefix, np.mean(flt_array,axis=1), '%.5f', ',')
    if same_array is None:
        print 'WARNING: no driver has OD equals to a driver in the fleet.'
    else:
        np.savetxt('%ssame.csv' % out_prefix, np.mean(same_array,axis=1), '%.5f', ',')
        
    if stddev:
        #generates the standard deviation output files
        np.savetxt('%sothers-sdev.csv' % out_prefix, np.std(other_array,axis=1), '%.5f', ',')
        np.savetxt('%sfleet-sdev.csv' % out_prefix, np.std(flt_array,axis=1), '%.5f', ',')
        if same_array is not None:
            np.savetxt('%ssame-sdev.csv' % out_prefix, np.std(same_array,axis=1), '%.5f', ',')
            
    #print other_array.shape, np.mean(other_array,axis=1)
    #print flt_array.shape, np.mean(flt_array,axis=1)
    #print data.shape
    #print same_array.shape, np.mean(same_array,axis=1)
    #print 
    #print flt_array.shape, np.mean(flt_array,axis=1)
    
    #prints final message, same_array is defaulted to empty list to avoid crash
    if same_array is None:
        same_array = [[]]
    print 'DONE. %d, %d, %d veh in fleet, same and others, respecively.' %\
    ( len(flt_array[0]), len(same_array[0]), len(other_array[0]) ) 
    
def fleet_ods(routefile):
    '''
    Returns a dict {'id':('orig','dest'),...}
    containing the ids, origins and destinations of the fleet vehicles
    
    '''
    rtree = ET.parse(routefile)

    #builds the dict {veh_id: (orig, dest), }    
    fleet_ods = {}
    for veh in rtree.getroot():
        if 'fromFleet' in veh.get('type'):
            route = veh[0].get('edges').split(' ')
            fleet_ods[veh.get('id')] = (route[0],route[-1]) 
            
    return fleet_ods
            
def parse_args():
    parser = OptionParser(
        description='''Separates performance of fleet drivers, honest drivers
with same OD and honest drivers w/ different ODs.'''
    )
            
    parser.add_option(
        '-r', '--route-file', type=str, help = 'path to the .rou.xml data'
    )
    
    parser.add_option(
        '-d', '--data-file', help='path to the file with the data to be separated', type=str
    )
    
    parser.add_option(
        '-o', '--out-prefix', help='prefix of the output file to be generated', type=str,
        default = 'odcmp_'
    )
    
    parser.add_option(
        '--base-header', type=int, help = '# of header rows in the base file',
        default=0
    )
    
    parser.add_option(
        '--curr-header', type=int, help = '# of header rows in the current file, default=2',
        default=2
    )
    
    parser.add_option(
        '-i', '--iterations', help='number of iterations to consider', type=int,
        default=10
    )
    
    parser.add_option(
        '-s', '--stddev', help='writes the standard deviation too', action='store_true',
        default=False
    )
    
    return parser.parse_args(sys.argv)

if __name__ == '__main__':
    (options, args) = parse_args()
    againstfleetods(
        options.route_file, options.data_file, options.out_prefix, 
        options.iterations, options.stddev
    )
    
    