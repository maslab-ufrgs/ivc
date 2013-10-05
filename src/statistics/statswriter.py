'''
Created on Oct 6, 2012

@author: anderson
'''
from fileinput import close
from string import rstrip

class StatsWriter(object):
    '''
    Default statistics writer
    '''

    outFile = None#the output outFile to write stats into
    
    def __init__(self, filename, mode = 'a'):
        '''
        Constructor
        '''
        self.outFile = open(filename, mode)
    
    def writeLine(self, dataName, collection, attrCall, separator = ','):
        '''
        Writes dataName as the first column, then traverses the collection, 
        calling attrCall() and writing it separated by 'separator' parameter
        
        '''
        line = str(dataName) + separator
        
        for dataHolder in collection:
            line += str(getattr(dataHolder, attrCall)()) + separator
            
        self.outFile.write(rstrip(line, ',') + '\n')
        self.outFile.flush()
        
    def __del__(self):
        if self.outFile is not None:
            self.outFile.close()
        