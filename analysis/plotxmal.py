'''
Plots all experiments of a given number -- x -- of malicious agents.
Useful to compare different configurations with the same number of
malicious agents 

Created on May 29, 2013

@author: anderson

'''
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from optparse import OptionParser

def plotxmal(exp_prefix, directory, num_experiments, num_iter, output = '',
                 datafname = 'vsbase_avg.csv', header_size = 0, data_col = 2, stdfname = None):
     
    path_str = os.path.join(exp_prefix + '_%d', directory, datafname) 
    
    #print [path_str % i for i in range(1,num_experiments+1)]
    #stores the experiment data in a big array
    alldata = {}
    for i in range(1,num_experiments+1):
        try:
            alldata[i] = np.genfromtxt(path_str % i, skip_header = header_size, delimiter=',')
        except IOError:# as ioe:
            print 'WARNING: Data file %s not found. Skipping...' % (path_str % i)
            print 'dunno y'
            
    if stdfname is not None:
        stdpath = os.path.join(exp_prefix + '_%d', directory, stdfname)
        stds = {}
        for i in range(1,num_experiments+1):
            try:
                stds[i] = np.genfromtxt(stdpath % i)
            except IOError:# as ioe:
                print 'WARNING: SD file %s not found. Skipping...' % (stdpath % i)
            #print stds, stdpath
    
    plots = {}
    #print stds, stdfname, stdpath
    #plot data
    for index,data in alldata.iteritems():   
        #print data#[:,2:]     
        if stdfname is not None:
            plots[index] = plt.errorbar(range(1,num_iter+1), data[:,data_col], stds[i],label=str(index))
        else:
            plots[index] = plt.plot(range(1,num_iter+1),data[:,data_col],label=str(index))
        
    #plot baseline
    plots['base'] = plt.plot(range(1,num_iter+1),[1]*num_iter,'--',label='base')
    
    #legend(plots.values(), )
    plt.legend()
    #plt.show()
    plt.savefig(output)

#if __name__ == '__main__':
#    plotxmal('6k-2k', '1mal', 5, 10, header_size = 1)
    
   
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
        '-o', '--output-prefix', type=str, help = 'the prefix of the output'
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
        '--header-size', help='ammout of lines to skip in input file', type=int, 
         default=1
    )
    
    return parser.parse_args(sys.argv)
    
    
    
if __name__ == '__main__':
    (options, args) = parse_args()
    plotxmal(
         options.exp_prefix, options.directory, options.num_experiments, 
         options.num_iter, options.output_prefix, options.data_file, options.header_size,
         options.data_col, options.sdfile
    )
    print 'DONE'