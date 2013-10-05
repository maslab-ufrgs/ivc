'''
Created on May 29, 2013

@author: anderson
'''

import sys
import numpy as np
from optparse import OptionParser

def last5mean(dfile, ofile, headersz = 2):
    
    data = np.genfromtxt(dfile, skip_header=headersz, delimiter=',')[:,1:]
    numlines = data.shape[0]
    
    inf = open(dfile, 'r')
    out = open(ofile, 'w')
    
    header = []
    #transfer the header from input to output, discarding 1st col
    for i in range(headersz):
        header.append(inf.readline().split(',')[1:])
        
    drvtypes = header[1] #ok
    
    indexes = [i for i in range(len(drvtypes)) if 'fromFleet' in drvtypes[i]]
    
    filt_header = []
    for line in header:
        filt_header.append([line[idx] for idx in indexes])
    #filt_header = [header[:,idx] for idx in indexes]
    
    odata = None
    for idx in indexes:
        if odata is None:
            odata = data[:,idx].reshape(numlines, 1)#numpy.delete(odata, col, axis=1)
        else:
            odata = np.append(odata, data[:,idx].reshape(numlines, 1), 1)
    
    #print filt_header,len(drvtypes),indexes,odata

    #calculates the average, reshapes it to line vector and save
    smean = np.mean(odata[5:,:], axis=0)
    newshape = (1, smean.shape[0])
    
    
    out.writelines([','.join(line)+'\n' for line in filt_header])
    np.savetxt(out, smean.reshape(newshape), fmt='%.5f', delimiter=',')
    
    out.close()
    
def parse_args():
    
    parser = OptionParser()
            
    parser.add_option(
        '-e', '--exp-prefix', type=str, help = 'the prefix of the experiment name'
    )
    
    parser.add_option(
        '-d', '--directory', help='the directory inside each experiment dir where the data file is', type=str
    )
    
    parser.add_option(
        '-n', '--num-experiments', help='number of experiments to generate statistics from', type=int,
        default=5
    )
    
    parser.add_option(
        '-i', '--num-iter', help='number of iterations to generate statistics of', type=int,
        default=10
    )
    
    parser.add_option(
        '-o', '--output', type=str, help = 'the path to the output file'
    )
    
    parser.add_option(
        '-f', '--data-file', help='name of the file where the data is read from', 
        type=str, default='vsbase_avg.csv'
    )
    
    parser.add_option(
        '-s', '--sdfile', help='name of the file where the stddev of the data is located', 
        type=str, default=None
    )
    
    parser.add_option(
        '-c', '--data-col', help='number of the column (first=0) in the data file to plot the data from', 
        type=int, default=2
    )
    
    parser.add_option(
        '--header-size', help='number of header rows', type=int, 
         default=2
    )
    
    return parser.parse_args(sys.argv)
    
    
    
if __name__ == '__main__':
    (options, args) = parse_args()
    last5mean(
         options.data_file, options.output, options.header_size
    )
    print 'DONE'