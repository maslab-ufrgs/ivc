'''
Writes the average performance of fleet drivers to an output file.

Created on May 18, 2013

@author: anderson

'''
import numpy
import os
import sys
from optparse import OptionParser

#def onlyfleet(exp_prefix, directory, num_experiments, num_iter, datafname = 'avg_norm_tt.csv'):
def onlyfleet(datafname,output='fleetdata.csv'):
    # path_str = os.path.join(exp_prefix + '_%d', directory, datafname) 
    
    #print [path_str % i for i in range(1,num_experiments+1)]
    #stores the experiment data in a big array
    data = numpy.genfromtxt(datafname, skip_header = 2, delimiter=',') 
    strdata = open(datafname,'r').readlines()[:2]
    drvtypes = strdata[1].strip().split(',') #ok
    
    col = 0
    odata = data
    for typ in drvtypes:
        if 'fromFleet' not in typ:
            odata = numpy.delete(odata, col, axis=1)
        else:
            col += 1
        
    #print odata #correct
    mn = numpy.mean(odata, axis=1).reshape(10,1)
    st = numpy.std(odata, axis=1).reshape(10,1)
    #print mn, st
    
    #creates a single array with mean, stddev and all data
    mean_st_odata = numpy.append(mn,numpy.append(st,odata,1),1)
    
    numpy.savetxt(output, mean_st_odata, delimiter = ',', fmt='%5.5f')
    #numpy.savetxt('stddev%s.csv' % directory, stddev_array, delimiter = ',', fmt='%5.5f')
    
    
def parse_args():
    
    parser = OptionParser(description='''Writes the average performance of fleet drivers to an output file.''')
            
    parser.add_option(
        '-e', '--exp-prefix', type=str, help = 'the prefix of the experiment name'
    )
    
    parser.add_option(
        '-d', '--directory', help='the directory inside each experiment dir where the data file is', type=str
    )
    
    parser.add_option(
        '-n', '--num-experiments', help='number of experiments to generate statistics from', type=int
    )
    
    parser.add_option(
        '-i', '--num-iter', help='number of iterations to generate statistics of', type=int
    )
    
    parser.add_option(
        '-f', '--data-file', help='name of the file where the data is read from', 
        type=str, default='norm_tt.csv'
    )
    return parser.parse_args(sys.argv)
    
    
    
if __name__ == '__main__':
    (options, args) = parse_args()
    onlyfleet(
         options.data_file
    )
    print 'DONE'
    
    
    