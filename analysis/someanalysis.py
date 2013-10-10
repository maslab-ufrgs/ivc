'''
This script provides several functions to analyse and plot experiment data.

A good way to use it is by calling:

$ python -i someanalysis.py 

This way, all script functions become available to use. Check the documentation
of each function to know what it does.

Many functions assume a certain directory structure (used in Anderson's dissertation).
This is hardcoded and needs to be changed if a different structure is used

'''
import numpy as np
import matplotlib.pyplot as plt
from plotparams import *

def distcorrmin(fname='vsblast5.csv'):
    '''
    Prints and plots the correlation between distance and vsblast of the best performance fleets
    on experiments performed for Anderson's dissertation
     
    '''
    if fname=='vsblast5.csv':
        expseries = [
             '6k-2k_4/5mal/%s',# % fname,
             '6k-2k_2/10mal/%s',# % fname,
             #'6k-2k_2/15mal/%s' % datafname,
             #'6k-2k_3/20mal/%s' % datafname,
             '6k-2k_3/25mal/%s',# % fname,
             '6k-2k_5/50mal/%s',# % fname,
             #'6k-2k_3/75mal/%s' % datafname
        ]
    else:

        expseries = [
             '6k-2k_4/5mal/%s',# % fname,
             '6k-2k_5/10mal/%s',# % fname,
             #'6k-2k_2/15mal/%s' % datafname,
             #'6k-2k_3/20mal/%s' % datafname,
             '6k-2k_5/25mal/%s',# % fname,
             '6k-2k_5/50mal/%s',# % fname,
             #'6k-2k_2/75mal/%s' % datafname
        ]
        
    allddata = [np.genfromtxt(i % 'distlast5.csv', skip_header=2, delimiter=',') for i in expseries]
    allmdata = [np.genfromtxt(i % fname, skip_header=2, delimiter=',') for i in expseries]
    
    
    
    for i in range(len(allmdata)):
        plt.figure(i+1)
        ax = plt.subplot(111)
        plt.plot(allmdata[i],allddata[i],'bo',ms=10)
        #plt.annotate(pointlabels[i], (i+0.95,np.mean(alldata[i])), xytext=(i+0.5,np.mean(alldata[i])), arrowprops=dict(arrowstyle="->"))
        print 'corr(%s)=%.2f' % (expseries[i],np.corrcoef(allmdata[i], allddata[i])[0][1])
        
    plt.show()

def distcorrmax(fname='vsblast5.csv'):
    '''
    Prints and plots the correlation between distance and vsblast of the worst performance fleets
    on experiments performed for Anderson's dissertation
     
    '''
    if fname == 'vsblast5.csv':
        expseries = [
             '6k-2k_2/5mal/%s',# % fname,
             '6k-2k_4/10mal/%s',# % fname,
             #'6k-2k_4/15mal/%s',# % fname,
             #'6k-2k_5/20mal/%s',# % fname,
             '6k-2k_1/25mal/%s',# % fname,
             '6k-2k_2/50mal/%s',# % fname,
             #'6k-2k_5/75mal/%s' % fname,
        ]
    else:
        expseries = [
             '6k-2k_3/5mal/%s',# % fname,
             '6k-2k_1/10mal/%s',# % fname,
             #'6k-2k_4/15mal/%s' % fname,
             #'6k-2k_5/20mal/%s' % fname,
             '6k-2k_1/25mal/%s',# % fname,
             '6k-2k_2/50mal/%s',# % fname,
             #'6k-2k_5/75mal/%s' % fname,
        ]
        
    allddata = [np.genfromtxt(i % 'distlast5.csv', skip_header=2, delimiter=',') for i in expseries]
    allmdata = [np.genfromtxt(i % fname, skip_header=2, delimiter=',') for i in expseries]
    
    
    
    for i in range(len(allmdata)):
        plt.figure(i+1)
        ax = plt.subplot(111)
        plt.plot(allmdata[i],allddata[i],'bo',ms=10)
        #plt.annotate(pointlabels[i], (i+0.95,np.mean(alldata[i])), xytext=(i+0.5,np.mean(alldata[i])), arrowprops=dict(arrowstyle="->"))
        print 'corr(%s)=%.2f' % (expseries[i],np.corrcoef(allmdata[i], allddata[i])[0][1])
        
    plt.show()
        
    
    
def sortbyperformance(fname):
    '''
    Returns a dict(drvid, performance)
    sorted by driver performance
    
    '''
    data = open(fname,'r').readlines()
    ids = data[0].strip().split(',')    #1st line has the ids
    perfmc = [float(d) for d in data[2].strip().split(',')] #3rd line has the performance
    
    drvdict = dict((ids[i],perfmc[i]) for i in range(len(ids)))
    
    return sorted(drvdict,key=lambda x: drvdict[x])
    

def plot_vsnoivc(figsz=(8,5)):
    '''
    Plots the compared performance of drivers: 
    performance_with_ivc / performance_without_ivc
    
    Assumes a given directory structure (used in Anderson's dissertation)
    
    '''
    data = [np.genfromtxt('6k-2k_%s/0mal/vsnoivc.csv' % i, skip_header=2, delimiter=',') for i in range(1,6)]
    
    vmean = np.mean(data,axis=0)
    
    #np.mean(vmean[:,1:],axis=1)
    plt.figure(figsize=figsz)
    
    plt.plot(range(1,11),np.mean(vmean[:,1:],axis=1),'go-', label='com-ivc')
    plt.plot(range(1,11), [1]*10, 'y--', label='baseline')
    plt.axis([1,10,.8,1.201])
    plt.title("Com IVC vs. sem IVC")
    
    plt.xlabel('iteracao')
    plt.ylabel('tempo de viagem comparado')
    
    plt.legend()
    plt.show()
    
def plotodammount():
    '''
    Plots a bar graph with the ammounts of honest drivers with and without OD pair in
    common with fleet drivers. Ammounts are hardcoded
    
    '''
    ammount_same = [6, 39, 54, 100, 136, 165, 328, 463]
    ammount_other= [1993,    1956,    1936,    1885,    1844,    1810,    1622,    1462]
    labels = [str(i) for i in [1,5,10,15,20,25,50,75]]
    
    indices = np.arange(1,9)
    width = .35
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    rects1 = ax.bar(indices, ammount_same, width, color='y', hatch='+')
    rects2 = ax.bar(indices+width, ammount_other, width, color='r', hatch="x")
    
    ax.set_ylabel('Quantidade')
    ax.set_title('Pares OD dos motoristas honestos')
    ax.set_xticks(indices+width)
    ax.set_xticklabels( tuple(labels) )
    
    plt.show()
    
#    womenMeans = (25, 32, 34, 20, 25)
#    womenStd =   (3, 5, 2, 3, 3)
#    rects2 = ax.bar(ind+width, womenMeans, width, color='y', yerr=womenStd)

def findminmax(malsizes=[5,10,25,50], fname='vsblast5.csv'):
    '''
    Finds in which experiments are the best and worst fleet performances. Assumes
    a given directory structure (used in Anderson's dissertation)
    
    '''
    for m in malsizes:
        mdata = [np.genfromtxt('6k-2k_%d/%dmal/%s' % (e,m,fname), skip_header=2, delimiter=',') for e in range(1,6)]
        #print mdata
        mmeans = np.mean(mdata,axis=1)
        print '%2d mal: min=%.2f@6k-2k_%d - max=%.2f@6k-2k_%d' % (m,np.min(mmeans),np.argmin(mmeans)+1,np.max(mmeans),np.argmax(mmeans)+1)
                               
    
    
def last5(save=False, prefix='odcmp', malsizes = [5,10,25,50], exprange = range(1,6), axis=[0,5,0.8,1.8],txtoffset=.05, figsz=(8,5)):
    '''
    Plots the average fleet performance on the last 5 iterations of each experiment.
    
    Assumes a certain directory structure of experiments (used in Anderson's dissertation)
     
    '''
    alldata = []
    fig = plt.figure(figsize = figsz)
    ax = fig.add_subplot(111)
    basestr = 'sem maliciosos' if prefix == 'odcmp' else '$\sharp=individual$'
    
    markers= ['d','o','v','^','h','1','p']
    colors = ['g', 'r', 'c', '#BF00BF','y']
    maxlabels = ['A','B','C','D'] #if prefix == 'odcmp' else ["A'","B'","C '","D'"]
    minlabels = ['E','F','G','H'] #if prefix == 'odcmp' else ["E'","F'","G'","H'"]
    
    plt.plot(range(6), [1]*6, 'y--', label='baseline')  
    
    #sz = [15,15,25,15]
    for i in range(len(malsizes)):
        #loads 5 last iterations of each malsz
        fdata = np.array( [np.genfromtxt('6k-2k_%d/%dmal/%s_fleet.csv' % (e,malsizes[i],prefix)) for e in exprange] )[:,5:]
        alldata.append(fdata)
        
        means = [np.mean(fdata[e]) for e in range(len(exprange))]
        print malsizes[i], np.mean(means)
        plt.plot(
            [i+1]*len(exprange), means, ms=MARKER_SIZE, 
            color=colors[i],marker=markers[i],linestyle='',
            label='|$D^\sharp|=%d$' % malsizes[i],
            
        )
        '''
        plt.plot(
            i+1, np.mean(means), 
            color='k',marker='*',linestyle='',ms=MARKER_SIZE#,markerfacecolor='None'
            #label='|$D^\sharp|=%d$' % malsizes[i]     
         )
        '''
        #print i+1, np.min(fdata), np.max(fdata)
        plt.text(i+1, np.min(means) - txtoffset-.02, minlabels[i], size=18)
        plt.text(i+1, np.max(means) + txtoffset-.01, maxlabels[i], size=18)
        
    
    plt.title("$D^\sharp$ nas 5 simulacoes / base: %s" % basestr, size=TITLE_SIZE)
    #plt.xlabel('$|D^\sharp|$',  size='20')
    plt.ylabel('media do desemp. - epis. 6-10',  size=AXIS_FONTSIZE)
    plt.legend(ncol=2, numpoints=1, prop={'size': LGND_FONTSIZE})
    plt.axis(axis)
    ax.set_xticklabels('')
    
    for label in ax.get_yticklabels():
        label.set_size(TICK_FONTSIZE)
    
    plt.show()
    if save:
        fname = 'last5.eps' if prefix == 'odcmp' else 'last5vsmua.eps'
        plt.savefig('6k-2k_summary/%s' % fname)
        


def honestcmp(dprefix='', malsizes=[5,10,25,50]):
    '''
    Prints the average performance of honest drivers with and without OD pair in common 
    with fleet drivers. 
    
    '''
    sdata = [np.genfromtxt('%s6k-2k_summary/odc_same_mean%dmal.csv' % (dprefix,i), skip_header=0, delimiter=',') for i in malsizes]
    odata = [np.genfromtxt('%s6k-2k_summary/odc_others_mean%dmal.csv' % (dprefix,i), skip_header=0, delimiter=',') for i in malsizes]
    sarray = np.array(sdata)
    oarray = np.array(odata)

    smean = np.mean(sarray[:,5:],axis=1)
    omean = np.mean(oarray[:,5:],axis=1)
    
    print smean, omean

    print smean / omean


def plotmcavsmua(
    axis=[1,10,.9,1.6], save=False, prefix='vmodc', 
    malsizes=[5,10,25,50], figsz=(8,6), lcols=3
):
    '''
    Plots compared performance of malicious coordinated agents (fleet) vs.
    malicious un-coordinated agents. Assumes a given directory structure.
    
    '''
    #malsizes = [5,10,25,50]
    savestr = 'vsmua' if prefix == 'vmodc' else 'vsbase'
    basestr = '$\sharp=individual$' if prefix == 'vmodc' else 'sem maliciosos'
    mdata = [np.genfromtxt('6k-2k_summary/%s_fleet_mean%dmal.csv' % (prefix, i), skip_header=0, delimiter=',') for i in malsizes]
    odata = [np.genfromtxt('6k-2k_summary/%s_others_mean%dmal.csv' % (prefix, i), skip_header=0, delimiter=',') for i in malsizes]
    sdata = [np.genfromtxt('6k-2k_summary/%s_same_mean%dmal.csv' % (prefix, i), skip_header=0, delimiter=',') for i in malsizes]
    
    markers= ['d-','o-','v-','^-','h-','1-','p-']
    colors = ['g', 'r', 'c', '#BF00BF','y']
    sizes = [2,2,3,3]
    
    ds = [(2,4), (None,None), (None,None), (2,4,6,8)]
    
    plt.figure(1, figsize=figsz)
    ax = plt.subplot(111)
#    plt.axis(axis)
    [plt.plot(
        range(1,11), mdata[i], markers[i], 
        color=colors[i], ms=MARKER_SIZE, 
        label='$|D^\sharp|=%d$' % malsizes[i],
        lw=sizes[i], dashes=ds[i]
    ) for i in range(len(mdata))]
    
    plt.plot(range(1,11), [1]*10, '--', color='orange', lw=3, label='base')
    # plt.title("Agentes maliciosos, $\sharp$=frota", size='22')
    plt.title("Motoristas de $D^\sharp$", size=TITLE_SIZE + 3)
    plt.xlabel('episodio', size=AXIS_FONTSIZE)
    plt.ylabel('tempo de viagem comparado', size=AXIS_FONTSIZE)
    plt.legend(
        ncol=lcols, prop={'size':LGND_FONTSIZE}, 
        numpoints=1
    )
    plt.axis(axis)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size(TICK_FONTSIZE)
    if save:
        plt.savefig('6k-2k_summary/mca-mal-%s.eps' % savestr,  bbox_inches='tight')
    
    plt.figure(2, figsize=figsz)
    ax = plt.subplot(111)
    plt.axis(axis)
    [plt.plot(
        range(1,11), sdata[i],markers[i], 
        color=colors[i], ms=MARKER_SIZE, label='$|D^\sharp|=%d$' % malsizes[i],
        lw=sizes[i], dashes=ds[i]
    ) for i in range(len(sdata))]
    
    plt.plot(range(1,11), [1]*10, '--', color='orange', lw=3, label='base')
    #plt.title("Agentes honestos - mesmos ODs", size='22')
    plt.title("Motoristas de $D_{=}$", size=TITLE_SIZE + 3)
    plt.xlabel('episodio', size=AXIS_FONTSIZE)
    plt.ylabel('tempo de viagem comparado', size=AXIS_FONTSIZE)
    plt.legend(
        ncol=lcols, prop={'size':LGND_FONTSIZE}, 
        numpoints=1
    )
    plt.axis(axis)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size(TICK_FONTSIZE)
    if save:
        plt.savefig('6k-2k_summary/mca-same-%s.eps' % savestr,  bbox_inches='tight')
    
    plt.figure(3, figsize=figsz)
    ax = plt.subplot(111)
#    plt.axis(axis)
    [plt.plot(
        range(1,11), odata[i],markers[i], 
        color=colors[i], ms=MARKER_SIZE, 
        label='$|D^\sharp|=%d$' % malsizes[i],
        lw=sizes[i], dashes=ds[i]
    ) for i in range(len(odata))]
    plt.plot(range(1,11), [1]*10, '--', color='orange', lw=3, label='base')
    #plt.title("Agentes honestos - outros ODs", size='22')
    plt.title("Motoristas de $D_{\\neq}$", size=TITLE_SIZE + 3)
    plt.xlabel('episodio', size=AXIS_FONTSIZE)
    plt.ylabel('tempo de viagem comparado', size=AXIS_FONTSIZE)
    plt.legend(
        ncol=lcols, prop={'size':LGND_FONTSIZE}, 
        numpoints=1
    )
    plt.axis(axis)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size(TICK_FONTSIZE)
    if save:
        plt.savefig('6k-2k_summary/mca-others-%s.eps' % savestr,  bbox_inches='tight')
    
    plt.show()
    
def plotmuavsbase2(axis=[1,10,0.8,2],save=False, malsizes=[5,10,25,50],figsz=(15,5),lcols=3):
    '''
    This is a more elaborate function than plotmuavsbase. It plots the compared performance 
    of drivers in the presence of malicious un-coordinated agents vs. the situation
    where all drivers are honest (base case). Three plots are generated: one for malicious
    drivers, one for honest with OD pair in common with a malicious and one for the 
    remaining honest drivers.
    
    Assumes a certain directory structure (used in Anderson's dissertation)
    
    '''
    #TODO: plot std in errorbars 
    #malsizes = [5,10,25,50]
    
    mdata = [np.genfromtxt('mua-6k-2k_summary/odc_fleet_mean%dmal.csv' % (i), skip_header=0, delimiter=',') for i in malsizes]
    odata = [np.genfromtxt('mua-6k-2k_summary/odc_others_mean%dmal.csv' % (i), skip_header=0, delimiter=',') for i in malsizes]
    sdata = [np.genfromtxt('mua-6k-2k_summary/odc_same_mean%dmal.csv' % (i), skip_header=0, delimiter=',') for i in malsizes]
    
    #appends mua-1-mal
    mdata = [np.genfromtxt('6k-2k_summary/odc_fleet_mean1mal.csv', skip_header=0, delimiter=',')] + mdata
    odata = [np.genfromtxt('6k-2k_summary/odc_others_mean1mal.csv', skip_header=0, delimiter=',')] + odata
    sdata = [np.genfromtxt('6k-2k_summary/odc_same_mean1mal.csv', skip_header=0, delimiter=',')] + sdata
    
    malsizes = [1] + malsizes
    
    markers= ['s-','d-','o-','v-','^-','h-','1-','p-']
    ds = [(2,4), (None,None), (None,None), (None,None), (2,4,6,8)]
    sizes = [2,2,2,3,3]
    
    plt.figure(1, figsize=figsz)
    ax = plt.subplot(111)
#    plt.axis(axis)
    [plt.plot(
        range(1,11), mdata[i], markers[i], 
        label='$|D^\sharp|=%d$' % malsizes[i], 
        ms=MARKER_SIZE, lw=sizes[i], dashes=ds[i]
    ) for i in range(len(mdata))]
    plt.plot(range(1,11), [1]*10, '--', color='orange', lw=3, label='base')
    #plt.title("Agentes maliciosos, $\sharp$=individual", size='22')
    plt.title("Motoristas de $D^\sharp$", size=TITLE_SIZE + 3)
    plt.xlabel('episodio',  size=AXIS_FONTSIZE)
    plt.ylabel('tempo de viagem comparado',  size=AXIS_FONTSIZE)
    plt.legend(
        ncol=lcols,prop={'size':LGND_FONTSIZE},
        numpoints=1,bbox_to_anchor=(1, 1.035)
    )
    plt.axis(axis)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size(TICK_FONTSIZE)
    if save:
        plt.savefig('mua-6k-2k_summary/mua-mal.eps',  bbox_inches='tight')
    
    plt.figure(2,figsize=figsz)
    ax = plt.subplot(111)
#    plt.axis(axis)
    [plt.plot(
        range(1,11), sdata[i],markers[i], 
        ms=MARKER_SIZE, label='$|D^\sharp|=%d$' % malsizes[i],
        lw=sizes[i], dashes=ds[i]
    ) for i in range(len(sdata))]
    plt.plot(range(1,11), [1]*10, '--', color='orange', lw=3, label='base')
    plt.title("Motoristas de $D_{=}$", size=TITLE_SIZE+3)
    plt.xlabel('episodio',  size=AXIS_FONTSIZE)
    plt.ylabel('tempo de viagem comparado',  size='20')
    plt.legend(
        ncol=lcols, prop={'size':LGND_FONTSIZE},
        numpoints=1,bbox_to_anchor=(1, 1.035)
    )
    plt.axis(axis)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size(TICK_FONTSIZE)
    if save:
        plt.savefig('mua-6k-2k_summary/mua-same.eps',  bbox_inches='tight')
    
    plt.figure(3, figsize=figsz)
    ax = plt.subplot(111)
#    plt.axis(axis)
    [plt.plot(
        range(1,11), odata[i],markers[i], 
        ms=MARKER_SIZE, label='$|D^\sharp|=%d$' % malsizes[i],
        lw=sizes[i], dashes=ds[i]
    ) for i in range(len(odata))]
    plt.plot(range(1,11), [1]*10, '--', color='orange', lw=3, label='base')
    plt.title("Motoristas de $D_{\\neq}$", size=TITLE_SIZE + 3)
    plt.xlabel('episodio',  size=AXIS_FONTSIZE)
    plt.ylabel('tempo de viagem comparado',  size=AXIS_FONTSIZE)
    plt.legend(
        ncol=lcols, prop={'size':LGND_FONTSIZE},
        numpoints=1,bbox_to_anchor=(1, 1.035)
    )
    plt.axis(axis)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size(TICK_FONTSIZE)
    if save:
        plt.savefig('mua-6k-2k_summary/mua-others.eps',  bbox_inches='tight')
    
    plt.show()
    

def _plotmuavsbase1(axis = [1,10,.8,2.11], save=False, figsz=(8,5)):
    '''
    Deprecated
    
    '''
    mdata = [np.genfromtxt('6k-2k_%s/1mal/odcmp_fleet.csv' % (i), skip_header=0, delimiter=',') for i in range(1,6)]
    sdata = [np.genfromtxt('6k-2k_%s/1mal/odcmp_same.csv' % (i), skip_header=0, delimiter=',') for i in range(1,6)]
    odata = [np.genfromtxt('6k-2k_%s/1mal/odcmp_others.csv' % (i), skip_header=0, delimiter=',') for i in range(1,6)]
    
    mmean = np.mean(mdata, axis=0)
    smean = np.mean(sdata, axis=0)
    omean = np.mean(odata, axis=0)
     
    plt.figure(1,figsize=figsz)
    ax = plt.subplot(111)
    
    plt.plot(range(1,11),mmean,'rd-', label='maliciosos')
    plt.plot(range(1,11),smean,'go-', label='honestos - mesmos ODs')
    plt.plot(range(1,11),omean,'bs-', label='honestos - outros ODs')
    
    plt.plot(range(1,11), [1]*10, 'y--', label='baseline')
    plt.axis(axis)
    #plt.title("%d agentes maliciosos sem coordenacao" % mal_number)
    plt.title("$|D^\sharp|=%d$; $\sharp$=individual / base: todos honestos" % 1, size='22')
    
    plt.xlabel('iteracao',  size='20')
    plt.ylabel('tempo de viagem comparado',  size='20')
    plt.legend()
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size('20')
    
    if save:
        plt.savefig('mua-6k-2k_summary/%d_muavsbase.eps' % 1, bbox_inches='tight')
    else:    
        plt.show()

def plotmuavsbase(mal_number, axis = [1,10,.8,2.11], save=False, figsz=(8,5)):
    '''
    This is a LESS elaborate function than plotmuavsbase2 (which should be rather used).
    It plots the compared performance of drivers in the presence of malicious un-coordinated agents vs. the situation
    where all drivers are honest (base case).
    
    Assumes a certain directory structure (used in Anderson's dissertation)
    
    '''
    
    if mal_number == 1:
        _plotmuavsbase1(axis, save, figsz)
        return
    
    mdata = [np.genfromtxt('mua-6k-2k_%s/%dmal/odcmp_fleet.csv' % (i,mal_number), skip_header=0, delimiter=',') for i in range(1,6)]
    sdata = [np.genfromtxt('mua-6k-2k_%s/%dmal/odcmp_same.csv' % (i,mal_number), skip_header=0, delimiter=',') for i in range(1,6)]
    odata = [np.genfromtxt('mua-6k-2k_%s/%dmal/odcmp_others.csv' % (i,mal_number), skip_header=0, delimiter=',') for i in range(1,6)]
    
    mmean = np.mean(mdata, axis=0)
    smean = np.mean(sdata, axis=0)
    omean = np.mean(odata, axis=0)
     
    plt.figure(mal_number,figsize=figsz)
    ax = plt.subplot(111)
    
    plt.plot(range(1,11),mmean,'rd-', label='maliciosos')
    plt.plot(range(1,11),smean,'go-', label='honestos - mesmos ODs')
    plt.plot(range(1,11),omean,'bs-', label='honestos - outros ODs')
    
    plt.plot(range(1,11), [1]*10, 'y--', label='baseline')
    plt.axis(axis)
    #plt.title("%d agentes maliciosos sem coordenacao" % mal_number)
    plt.title("$|D^\sharp|=%d$; $\sharp$=individual / base: todos honestos" % mal_number, size='22')
    
    plt.xlabel('iteracao',  size='20')
    plt.ylabel('tempo de viagem comparado',  size='20')
    plt.legend()
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size('20')
    
    if save:
        plt.savefig('mua-6k-2k_summary/%d_muavsbase.eps' % mal_number, bbox_inches='tight')
    else:    
        plt.show()
    
def plotfleet(mal_number, axis=[1,10,.9,1.601], save=False, vs='mua',figsz=(8,5)):
    '''
    Deprecated?
    
    '''
    fprefix = 'vmodc' if vs == 'mua' else 'odcmp'
    
    mdata = [np.genfromtxt('6k-2k_%d/%dmal/%s_fleet.csv' % (i,mal_number,fprefix), skip_header=0, delimiter=',') for i in range(1,6)]
    sdata = [np.genfromtxt('6k-2k_%d/%dmal/%s_same.csv' % (i,mal_number,fprefix), skip_header=0, delimiter=',') for i in range(1,6)]
    odata = [np.genfromtxt('6k-2k_%d/%dmal/%s_others.csv' % (i,mal_number,fprefix), skip_header=0, delimiter=',') for i in range(1,6)]
    
    mmean = np.mean(mdata, axis=0)
    smean = np.mean(sdata, axis=0)
    omean = np.mean(odata, axis=0)
     
    plt.figure(mal_number,figsize=figsz)
    ax = plt.subplot(111)
    
    plt.plot(range(1,11),mmean,'rd-', label='frota')
    plt.plot(range(1,11),smean,'go-', label='honestos - mesmos ODs')
    plt.plot(range(1,11),omean,'bs-', label='honestos - outros ODs')
    
    plt.plot(range(1,11), [1]*10, 'y--', label='baseline')
    plt.axis(axis)
    
    #base = '$\sharp$=individualsituacao c/ maliciosos s/ coord.' if vs=='mua' else 'todos honestos'
    base = '$\sharp$=individual' if vs=='mua' else 'todos honestos'
    #plt.title("%d agentes maliciosos na frota; base=%s" % (mal_number,base))
    plt.title("$|D^\sharp|=%d$; $\sharp$=frota / base: %s" % (mal_number,base), size='22')
    
    plt.xlabel('iteracao', size='20')
    plt.ylabel('tempo de viagem comparado', size='20')
    plt.legend()
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_size('20')
    
    if save:
        plt.savefig('6k-2k_summary/%d_vs%s.eps' % (mal_number,vs), bbox_inches='tight')
    else:    
        plt.show()
    
    