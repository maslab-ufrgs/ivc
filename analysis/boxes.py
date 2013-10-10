'''
Provides functions for generation of boxplots of drivers performance.

It looks in specific experiment directories for data files. 
This information is hardcoded.

Created on May 29, 2013

@author: anderson

'''
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from optparse import OptionParser

def maxboxes(output = None, fname = 'vsblast5.csv', axis=[0,5,.2,2.1], header_size = 2):
    '''
    Generates boxplots of the drivers of experiments where 
    their performance compared to the absence of 
    malicious drivers was the worst
    
    ''' 
    #print [path_str % i for i in range(1,num_experiments+1)]
    #stores the experiment data in a big array
    basestr = 'sem maliciosos' if fname == 'vsblast5.csv' else '$\sharp=individual$'
    pointlabels = ['A','B','C','D'] #if fname == 'vsblast5.csv' else ["A'","B'","C '","D'"]
    
    markers,colors = getmarkerscolors()
    
    if fname == 'vsblast5.csv':
        expseries = [
             '6k-2k_2/5mal/%s' % fname,
             '6k-2k_4/10mal/%s' % fname,
             #'6k-2k_4/15mal/%s' % fname,
             #'6k-2k_5/20mal/%s' % fname,
             '6k-2k_1/25mal/%s' % fname,
             '6k-2k_2/50mal/%s' % fname,
             #'6k-2k_5/75mal/%s' % fname,
        ]
    else:
        expseries = [#correct
             '6k-2k_3/5mal/%s' % fname,
             '6k-2k_1/10mal/%s' % fname,
             #'6k-2k_4/15mal/%s' % fname,
             #'6k-2k_5/20mal/%s' % fname,
             '6k-2k_1/25mal/%s' % fname,
             '6k-2k_2/50mal/%s' % fname,
             #'6k-2k_5/75mal/%s' % fname,
        ]
        
    alldata = [np.genfromtxt(i, skip_header = header_size, delimiter=',') for i in expseries]
    
    #print alldata
            
    plots = {}
    plt.figure(1)
    ax = plt.subplot(111)
        
    #plot baseline
    baseticks = len(alldata)
    plots['base'] = plt.plot(range(baseticks+2),[1]*(baseticks+2),'y--',label='base')
    
    #plot data
    plt.boxplot(alldata)
    
    #plot mean
    for i in range(len(alldata)):
        plt.plot(i+1,np.mean(alldata[i]),'b*',ms=15)
        plt.annotate(pointlabels[i], (i+0.95,np.mean(alldata[i])), xytext=(i+0.5,np.mean(alldata[i])), size=18, arrowprops=dict(arrowstyle="->"))
        print np.mean(alldata[i])
    
    plt.title("Piores $D^\sharp$ / base: %s" % basestr, size='22')
    plt.xlabel('$|D^\sharp|$',  size='20')
    plt.ylabel('tempo de viagem comparado',  size='20')
    
    #xlabels = ax.get_xticklabels()
    #for i in range(len(xlabels)): #label in  + 
    #   xlabels[i].set_size('20')
        
    xtickNames = plt.setp(ax, xticklabels=[5,10,25,50])
    plt.setp(xtickNames)#, rotation=45, fontsize=8)
        
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size(20)
    
    #legend(plots.values(), )
    plt.axis(axis)
    plt.legend()
    plt.show()
    
    if output is not None:
        plt.savefig(output)
        
def getmarkerscolors():
    return( ['d','o','+','^','h','1','p'], ['g', 'r', 'c', '#BF00BF','y'])

def minboxes(output = None, fname = 'vsblast5.csv', axis=[0,5,.2,2.1], header_size = 2):
    '''
    Generates boxplots of the drivers of experiments where 
    their performance compared to the absence of 
    malicious drivers was the best
    
    '''  
    #print [path_str % i for i in range(1,num_experiments+1)]
    #stores the experiment data in a big array
    basestr = 'sem maliciosos' if fname == 'vsblast5.csv' else '$\sharp=individual$'
    pointlabels = ['E','F','G','H'] #if fname == 'vsblast5.csv' else ["E'","F'","G'","H'"]
    
    markers,colors = getmarkerscolors()
    
    if fname=='vsblast5.csv':
        expseries = [
             '6k-2k_4/5mal/%s' % fname,
             '6k-2k_2/10mal/%s' % fname,
             #'6k-2k_2/15mal/%s' % datafname,
             #'6k-2k_3/20mal/%s' % datafname,
             '6k-2k_3/25mal/%s' % fname,
             '6k-2k_5/50mal/%s' % fname,
             #'6k-2k_3/75mal/%s' % datafname
        ]
    else:

        expseries = [#wrong?
             '6k-2k_4/5mal/%s' % fname,
             '6k-2k_5/10mal/%s' % fname,
             #'6k-2k_2/15mal/%s' % datafname,
             #'6k-2k_3/20mal/%s' % datafname,
             '6k-2k_5/25mal/%s' % fname,
             '6k-2k_5/50mal/%s' % fname,
             #'6k-2k_2/75mal/%s' % datafname
        ]
    alldata = [np.genfromtxt(i, skip_header = header_size, delimiter=',') for i in expseries]
    
    #print alldata
            
    plots = {}
    plt.figure(1)
    ax = plt.subplot(111)
        
    #plot baseline
    baseticks = len(alldata)
    plots['base'] = plt.plot(range(baseticks+2),[1]*(baseticks+2),'y--',label='base')
    
    #plot data
    plt.boxplot(alldata)
    
    #plot mean
    for i in range(len(alldata)):
        plt.plot(i+1,np.mean(alldata[i]),'b*',ms=15)
        plt.annotate(pointlabels[i], (i+0.95,np.mean(alldata[i])), size=18, xytext=(i+0.5,np.mean(alldata[i])), arrowprops=dict(arrowstyle="->"))
    
    plt.title("Melhores $D^\sharp$ / base: %s" % basestr, size='22')
    plt.xlabel('$|D^\sharp|$',  size='20')
    plt.ylabel('tempo de viagem comparado',  size='20')
    
    #xlabels = ax.get_xticklabels()
    #for i in range(len(xlabels)): #label in  + 
     #   xlabels[i].set_size('20')
        
    xtickNames = plt.setp(ax, xticklabels=[5,10,25,50])
    plt.setp(xtickNames)#, rotation=45, fontsize=8)
        
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size(20)
    
    #legend(plots.values(), )
    plt.axis(axis)
    plt.legend()
    plt.show()
    
    if output is not None:
        plt.savefig(output)
    #plt.savefig(output)

#if __name__ == '__main__':
#    plotxmal('6k-2k', '1mal', 5, 10, header_size = 1)

def bp_manysources(datafiles, output='boxplot-many.eps', header_size=2):
    '''
    Generates boxplots of the drivers of experiments whose data
    files are specified in the first parameter (a comma-separated string)
    
    ''' 
    alldata = [np.genfromtxt(path, skip_header = header_size, delimiter=',') for path in datafiles.split(',')]
    
    baseticks = len(alldata)
    plt.plot(range(1,baseticks+1),[1]*baseticks,'y--',label='base')
    plt.boxplot(alldata)
    
    #legend(plots.values(), )
    #plt.legend()
    #plt.show()
    plt.savefig(output)
    
    