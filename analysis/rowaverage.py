'''
Reads a result file with a series of values such as:

ctrl21908,ctrl25031,ctrl24215,ctrl21456,ctrl25899,ctrl25934,ctrl26065,ctrl26222,ctrl26255,ctrl22289,
fromFleet0,fromFleet0,fromFleet0,fromFleet0,fromFleet0,fromFleet0,fromFleet0,fromFleet0,fromFleet0,fromFleet0,
1.00569,0.99811,1.68559,1.32182,1.03419,1.37795,1.01110,1.09316,1.79814,1.06880

and outputs the average of the numeric row(s) (number of lines to be ignored
must be informed):

1.23945


Created on May 30, 2013

@author: anderson

'''
import numpy as np
import sys
from optparse import OptionParser

def rowaverage(ifile, ofile, headersz=2):
    data = np.genfromtxt(ifile, skip_header=headersz, delimiter=',')
    mean = [np.mean(data)] if len(data.shape) == 1 else np.mean(data,axis=1)
    
    #print mean
    np.savetxt(ofile, mean, fmt='%.5f', delimiter=',')
    

def parse_args():
    
    parser = OptionParser()
            
    parser.add_option(
        '-o', '--output', type=str, help = 'the path to the output file'
    )
    
    parser.add_option(
        '-f', '--data-file', help='name of the file where the data is read from', 
        type=str
    )
    
#    parser.add_option(
#        '-c', '--data-col', help='number of the column (first=0) in the data file to plot the data from', 
#        type=int, default=2
#    )
    
    parser.add_option(
        '--header-size', help='number of header rows', type=int, 
         default=2
    )
    
    return parser.parse_args(sys.argv)


if __name__ == '__main__':
    (options,args) = parse_args()
    rowaverage(options.data_file, options.output, options.header_size)
    print 'DONE.'
    