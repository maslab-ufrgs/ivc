'''
This script is no longer used because the performed 
normalization makes less sense than comparing the performance of
the same driver in the presence and absence of the fleet

This script normalizes the values of 2nd iteration onward
compared to the 1st.

Created on 15/05/2013

@author: artavares

'''
import sys
from optparse import OptionParser

def normalize_results(infile, outfile):
    
    in_array = open(infile, 'r').readlines()
    out = open(outfile, 'w')
    
    #baseline is the first iteration (3rd row) from 2nd col onwards
    base = in_array[2].strip().split(',')[1:]
    
    out.writelines(in_array[:2])
    
    #traverses the data which are in 3rd row onwards of input
    lineno = 1
    for line in in_array[2:] :
        data = line.strip().split(',')[1:]
        
        out.write('%d,' % lineno)
        
        out.write(','.join([str(float(data[i]) / float(base[i])) for i in range(len(base))] ))
        
#        for i in range(len(base)):
#            out.write('%f,' % (float(data[i]) / float(base[i]) ) )
            
        out.write('\n')
        lineno += 1
            
def parse_args():
    
    parser = OptionParser()
            
    parser.add_option(
        '-o', '--output', type=str, help = 'output file'
    )
    
    parser.add_option(
        '-i', '--input', help='the input file', type=str
    )
    
    return parser.parse_args(sys.argv)


if __name__ == '__main__':
    (options, args) = parse_args()
    normalize_results(options.input, options.output)
