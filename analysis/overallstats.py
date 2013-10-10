'''
This script reads experiment results from different directories and
writes the average and standard deviation of these results

Requires experiments to be organized in a certain 
directory structure.

TODO resume from here

Created on May 18, 2013

@author: anderson

'''
import numpy
import os
import sys
from optparse import OptionParser

def overallstats(exp_prefix, directory, num_experiments, num_iter, oprefix = '',
                 datafname = 'avg_norm_tt.csv', header_size = 0):
     
    path_str = os.path.join(exp_prefix + '_%d', directory, datafname) 
    
    #print [path_str % i for i in range(1,num_experiments+1)]
    #stores the experiment data in a big array
    alldata = []
    for i in range(1,num_experiments+1):
        try:
            alldata.append(numpy.genfromtxt(path_str % i, skip_header = header_size, delimiter=','))
        except IOError:# as ioe:
            print 'WARNING: file %s not found. Skipping...' % (path_str % i)
    
    #crops all experiments to consider only the given number of iterations
    for i in range(len(alldata)):
        alldata[i] = alldata[i][:num_iter] 
        
    #print alldata
        
    stddev_array = numpy.std(alldata, axis=0)
    mean_array = numpy.mean(alldata, axis=0)
    
    #print mean_array
    
    numpy.savetxt('%smean%s.csv' % (oprefix, directory), mean_array, delimiter = ',', fmt='%.5f')
    numpy.savetxt('%sstddev%s.csv' % (oprefix, directory), stddev_array, delimiter = ',', fmt='%.5f')
    
    
def parse_args():
    
    parser = OptionParser(description='''Calculates the mean and standard deviation of results of a series of experiments''')
            
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
        '-o', '--output-prefix', type=str, help = 'the prefix of the output'
    )
    
    parser.add_option(
        '-f', '--data-file', help='name of the file where the data is read from', 
        type=str, default='avg_norm_tt.csv'
    )
    
    parser.add_option(
        '--header-size', help='ammout of lines to skip in input file', type=int, 
         default=0
    )
    
    return parser.parse_args(sys.argv)
    
    
    
if __name__ == '__main__':
    (options, args) = parse_args()
    overallstats(
         options.exp_prefix, options.directory, options.num_experiments, 
         options.num_iter, options.output_prefix, options.data_file, options.header_size
    )
    print 'DONE'
    
    
    