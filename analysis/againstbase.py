'''
Plots the ratio of the performances contained in two files: 'current' / 'base'

Created on May 23, 2013

@author: anderson

'''
import sys
from optparse import OptionParser
import numpy as np

def againstbase(base_fname, curr_fname, out_fname, base_header = 0, curr_header = 2, iterations = 0 ):
    #loads base and current_data, discards 2 first rows and first col (headers and iteration number)
    base_data = np.genfromtxt(base_fname, skip_header = base_header, delimiter=',')[:,1:]
    curr_data = np.genfromtxt(curr_fname, skip_header = curr_header, delimiter=',')[:,1:]
    
    #resizes the arrays if the iteration number was given
    if iterations != 0:
        base_data = base_data[:iterations]
        curr_data = curr_data[:iterations]
    
    try:
        ndata = curr_data / base_data
    
    except ValueError as v:  
        print 'curr_data and base_data have different shapes'
        print 'curr_data shape: %s; base_data shape: %s' % (curr_data.shape, base_data.shape)
        print 'More info:', v.message 
        exit(1)
    #generates a column vector corresponding to the iteration number
    itnums = np.arange(1, len(ndata)+1).reshape(len(ndata),1)
    
    out_file = open(out_fname, 'w')
    curr_file = open(curr_fname, 'r')
    
    #copy the 2 first lines of curr_file to out_file
    out_file.write(curr_file.readline())
    out_file.write(curr_file.readline())
    
    curr_file.close()
    
    np.savetxt(out_file, np.append(itnums, ndata, 1), '%.5f', ',')
    
    
    
def parse_args():
    
    parser = OptionParser()
            
    parser.add_option(
        '-b', '--base-file', type=str, help = 'path to the file with the baseline data'
    )
    
    parser.add_option(
        '-c', '--curr-file', help='path to the file with the current data', type=str
    )
    
    parser.add_option(
        '-o', '--out-file', help='path of the output file to be generated', type=str
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
        default=0
    )
    
    return parser.parse_args(sys.argv)

if __name__ == '__main__':
    (options, args) = parse_args()
    
    againstbase(
        options.base_file, options.curr_file, options.out_file, 
        options.base_header, options.curr_header, options.iterations
    )
    
    print options.out_file, 'written.'