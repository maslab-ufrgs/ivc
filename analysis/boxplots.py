'''
Created on May 29, 2013

@author: anderson

boxplots all experiments: x is the #of mal agents

'''
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from optparse import OptionParser

def boxplots(exp_suffix, exp_series, output = 'boxplot.eps',
                 datafname = 'vsmlast.csv', header_size = 2):
     
    #print [path_str % i for i in range(1,num_experiments+1)]
    #stores the experiment data in a big array
    pathstr = os.path.join(exp_suffix,datafname)
    alldata = [np.genfromtxt(i + pathstr, skip_header = header_size, delimiter=',') for i in exp_series.split(',')]
    
    #print alldata
            
    plots = {}
    #print stds, stdfname, stdpath
    #plot data
   
        
    #plot baseline
    baseticks = len(alldata)
    plots['base'] = plt.plot(range(1,baseticks+1),[1]*baseticks,'y--',label='base')
    plt.boxplot(alldata)
    
    #legend(plots.values(), )
    #plt.legend()
    #plt.show()
    plt.savefig(output)

#if __name__ == '__main__':
#    plotxmal('6k-2k', '1mal', 5, 10, header_size = 1)

def bp_manysources(datafiles, output='boxplot-many.eps', header_size=2):
    alldata = [np.genfromtxt(path, skip_header = header_size, delimiter=',') for path in datafiles.split(',')]
    
    baseticks = len(alldata)
    plt.plot(range(1,baseticks+1),[1]*baseticks,'y--',label='base')
    plt.boxplot(alldata)
    
    #legend(plots.values(), )
    #plt.legend()
    #plt.show()
    plt.savefig(output)
    
   
def parse_args():
    
    parser = OptionParser()
            
    parser.add_option(
        '-e', '--exp-suffix', type=str, help = 'the suffix of the experiment name',
        default='mal'
    )
    
    parser.add_option(
        '-o', '--output', type=str, help = 'the prefix of the output',
        default='boxplot.eps'
    )
    
    parser.add_option(
        '-f', '--data-file', help='name of the file where the data is read from', 
        type=str, default='vsmlast.csv'
    )
    
    parser.add_option(
        '-s', '--exp-series', help='comma-separated values of the tests to be inspected. Eg: 5,10,15', 
        type=str, default='5,10,15,20,25,50,75'
    )
    
    parser.add_option(
        '-m', '--many-sources', help='comma-separated paths to load the values for the plots', 
        type=str, default=None
    )
    
    parser.add_option(
        '--header-size', help='ammout of lines to skip in input file', type=int, 
         default=2
    )
    
    return parser.parse_args(sys.argv)
    
    
    
if __name__ == '__main__':
    (options, args) = parse_args()
    
    if options.many_sources is not None:
        bp_manysources(options.many_sources, options.output, options.header_size)
        print 'Boxplot done for many sources.'
    else: 
        boxplots(
             options.exp_suffix, options.exp_series, options.output, 
             options.data_file, options.header_size
        )
        print 'Standard boxplot done'
    