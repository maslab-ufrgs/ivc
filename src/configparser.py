'''
Created on Feb 1, 2013

@author: anderson
'''

import os
import xml.etree.ElementTree as ET

def str_to_bool(value):
    if value in ['True', 'true']:
        return True
    return False
    
class ConfigParser(object):
    '''
    Parses the .xml file with the configs
    
    '''
    def __init__(self, cfgpath):
        '''
        Constructor

        '''
        self._set_defaults()
        
        self.cfgdir = os.path.dirname(os.path.realpath(cfgpath))
        cfgtree = ET.parse(cfgpath)
        
        
        print 'Config file parsing started...'
        
        for io_element in cfgtree.find('input-output'):
            #TODO: check if io_element refers to absolute path
            if io_element.tag == 'net-file':
                self.netfile = self._parse_path(io_element.get('value'))
            
            if io_element.tag == 'main-demand':
                self.maindemand = [self._parse_path(io_element.get('value'))]
            
            if io_element.tag == 'aux-demand':
                self.auxdemand = self._parse_path(io_element.get('value'))
            
            if io_element.tag == 'output-prefix':
                self.outputprefix = self._parse_path(io_element.get('value'))
                
        for param_element in cfgtree.find('parameters'):
            if param_element.tag == 'comm-range':
                self.commrange = int(param_element.get('value'))
            
            if param_element.tag == 'cheat-value':
                self.cheatvalue = int(param_element.get('value'))
            
            if param_element.tag == 'beta':
                self.beta = int(param_element.get('value'))
            
            if param_element.tag == 'ivcfreq':
                self.ivcfreq = int(param_element.get('value'))
            
            if param_element.tag == 'nogamma':
                self.nogamma = str_to_bool(param_element.get('value'))
            
            if param_element.tag == 'uncoordinated':
                self.uncoordinated = str_to_bool(param_element.get('value'))
            
            if param_element.tag == 'iterations': 
                self.iterations = int(param_element.get('value'))
                
            if param_element.tag == 'first-iteration': 
                self.first_iter = int(param_element.get('value'))    
                
            if param_element.tag == 'mal-strategy':
                self.mal_strategy = param_element.get('value')
            
            if param_element.tag == 'use-load-keeper':
                self.use_lk = str_to_bool(param_element.get('value'))
                
        for sumo_element in cfgtree.find('sumo'):
            if sumo_element.tag == 'port':
                self.port = int(sumo_element.get('value'))
            
            if sumo_element.tag == 'use-gui':
                self.usegui = str_to_bool(sumo_element.get('value'))

            if sumo_element.tag == 'sumo-path':
                self.sumopath = self._parse_path(sumo_element.get('value'))
            
            if sumo_element.tag == 'warm-up-time':
                self.warmuptime = int(sumo_element.get('value'))
                
            if sumo_element.tag == 'warm-up-load':
                self.warmupload = int(sumo_element.get('value'))
            
                
            if sumo_element.tag == 'summary-output-prefix':
                self.summary_prefix = self._parse_path(sumo_element.get('value'))
                
            if sumo_element.tag == 'routeinfo-output-prefix':
                self.routeinfo_prefix = self._parse_path(sumo_element.get('value'))

    def _parse_path(self, value):
        return os.path.join(
            self.cfgdir, os.path.expanduser(value)
        )
        
    def _set_defaults(self):
        
        
        self.netfile = None
        self.maindemand = None
        self.auxdemand = None
        self.outputprefix = 'exp'
        
        self.commrange = 200
        self.cheatvalue = None
        self.beta = 50
        self.ivcfreq = 3 
        self.nogamma = False
        self.uncoordinated = False
        self.iterations = 5
        self.first_iter = 1
        self.mal_strategy = None
        self.use_lk = False
        
        self.port = 8813
        self.usegui = False
        self.sumopath = None
        self.summary_prefix = None
        self.routeinfo_prefix = None
        self.warmuptime = 1000
        self.warmupload = 0
