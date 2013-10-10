'''
Provides functions to draw districts and trips in a SUMO-gui window.

A good way to use this script is to call it like:

$ python -i drawdistricts.py [params]

so that the user can call a function to draw the desired entity.

Read each function documentation to know what it does.

Note that this script has a hard-coded dependency with odpopulator module
from NetPopulate project. 

Created on May 30, 2013

@author: anderson

'''
import os
import sys
import traci
import sumolib
import subprocess
import random as rd
import xml.etree.ElementTree as ET
from optparse import OptionParser

sys.path.append(os.path.expanduser('~/workspace/NetPopulate/src'))
#print sys.path
import odpopulator

def randomcolor():
    return (rd.randint(0,255), rd.randint(0,255), rd.randint(0,255), 0)

def drawdistricts(scale=1, fixedcolor = False):#netfile, tazfile, odmfile):
    '''
    Draws triangles in the origins and destinations of the map.
    Upward triangles for origins and downward triangles for destinations of trips.
    Size of triangle is proportional to the ammount of trips it generates
    or receives.
    Only one triangle is plotted by district (in case the district has
    more than one origin or destination of trips, only one is
    considered)
    
    '''
    taztree = ET.parse(options.tazfile)
    net = sumolib.net.readNet(options.netfile)
    
    odm = odpopulator.generate_odmatrix(options.tazfile,options.odmfile)
    acolor = randomcolor()
    for taz in taztree.getroot():
        tazcolor = randomcolor() if not fixedcolor else acolor
        
        dist = odm.find(taz.get('id'))
        #print 'id, inc, out - %s\t%d\t%d' % (taz.get('id'), odm.incoming_trips(taz.get('id')), dist.outgoing_trips())
        #print taz.get('id'), tazcolor
        for source_or_sink in taz:
            if source_or_sink.tag == 'tazSource':
                node = net.getEdge(source_or_sink.get('id'))._from
                yoffset =  - 40 * scale * dist.outgoing_trips()  #will draw upward triangle
                xoffset =  + 30 * scale * dist.outgoing_trips()
            else:
                
                node = net.getEdge(source_or_sink.get('id'))._to
                yoffset =  + 40 * scale * odm.incoming_trips(taz.get('id')) #will draw downward triangle
                xoffset =  + 30 * scale * odm.incoming_trips(taz.get('id'))
            nc = node._coord
            #print source_or_sink.get('id'), nc
            #shape contains 3 points to draw a triangle (direction depends on yoffset
            tazshape = (nc, (nc[0]-xoffset, nc[1] + yoffset), (nc[0]+xoffset,nc[1]+yoffset ) )    
            traci.polygon.add(
                  taz.get('id') + source_or_sink.get('id'), 
                  tazshape, tazcolor, 1
            )
            traci.simulationStep()
        #print tazshape
    #traci.close()
    
def drawtaztrip(taz_id):
    '''
    Draws an arrow for a connection between two districts. Arrow base points to
    origin and head points to destination. Size of arrow base is proportional
    to the number of trips between districts
      
    '''
    taztree = ET.parse(options.tazfile)
    net = sumolib.net.readNet(options.netfile)
    
    odm = odpopulator.generate_odmatrix(options.tazfile,options.odmfile)
    otaz = odm.find(taz_id)
    
    asource = otaz.select_source()
        
    for dtaz_id,numtrips in otaz.destinations.iteritems():
        
        adest = odm.find(dtaz_id).select_sink()
        #print asource
        ocoord = net.getEdge(asource['id'])._from._coord
        #oshape = ( (ocoord[0],ocoord[1]),(ocoord[0]-150,ocoord[1]-125),(ocoord[0]-150,ocoord[1]+125) )
        
        dcoord = net.getEdge(adest['id'])._to._coord
        #dshape = ( (dcoord[0],dcoord[1]),(dcoord[0]+150,dcoord[1]+125),(dcoord[0]+150,dcoord[1]-125) )
        
        #the three points that form the triangle
        pshape = ( 
            (ocoord[0] - 25*numtrips, ocoord[1] + 25*numtrips), 
            (ocoord[0] + 25*numtrips, ocoord[1] - 25*numtrips), 
            (dcoord[0], dcoord[1])
        )
        
        traci.polygon.add(
            otaz.taz_id + 'to' + dtaz_id, pshape, randomcolor(), 1         
        )
        traci.simulationStep()
        
        
def drawtaztrips():
    '''
    Draws an arrow for every connection between two districts. Arrow base points to
    origin and head points to destination. Size of arrow base is proportional
    to the number of trips between districts.
    
    Tested only in poa-arterials
      
    '''
    taztree = ET.parse(options.tazfile)
    net = sumolib.net.readNet(options.netfile)
    
    odm = odpopulator.generate_odmatrix(options.tazfile,options.odmfile)
    
    for otaz in odm.taz_list:
        
        asource = otaz.select_source()
        
        for dtaz_id,numtrips in otaz.destinations.iteritems():
            
            adest = odm.find(dtaz_id).select_sink()
            #print asource
            ocoord = net.getEdge(asource['id'])._from._coord
            #oshape = ( (ocoord[0],ocoord[1]),(ocoord[0]-150,ocoord[1]-125),(ocoord[0]-150,ocoord[1]+125) )
            
            dcoord = net.getEdge(adest['id'])._to._coord
            #dshape = ( (dcoord[0],dcoord[1]),(dcoord[0]+150,dcoord[1]+125),(dcoord[0]+150,dcoord[1]-125) )
            
            #the three points that form the triangle
            pshape = ( 
                (ocoord[0] - 25*numtrips, ocoord[1] + 25*numtrips), 
                (ocoord[0] + 25*numtrips, ocoord[1] - 25*numtrips), 
                (dcoord[0], dcoord[1])
            )
            
            traci.polygon.add(
                otaz.taz_id + 'to' + dtaz_id, pshape, randomcolor(), 1         
            )
            traci.simulationStep()
    
def drawods(drvfile):
    '''
    Draws origins and destinations of trips for every vehicle
    in a experiment result file
    
    '''
    ids = open(drvfile).readline().strip().split(',')
    if ids[-1] == '':
        ids = ids[:-1]
        
    for i in ids:
        draw_orig_dest(i,options.roufile,options.netfile)
        
def clear_polygons():
    '''
    Deletes all drawings made by this script
    
    '''
    for p in traci.polygon.getIDList():
        traci.polygon.remove(p)
    traci.simulationStep()
    
def draw_orig_dest(veh_id, roufile, netfile):
    '''
    Draws an arrow from origin to destination of a vehicle
    
    '''
    rtree = ET.parse(roufile)
    net = sumolib.net.readNet(netfile)
    
    for veh in rtree.getroot():
        if veh.get('id') == veh_id:
            route = veh[0].get('edges').split(' ')
            
            vcolor = randomcolor()
            
            ocoord = net.getEdge(route[0])._from._coord
            oshape = ( (ocoord[0],ocoord[1]),(ocoord[0]-150,ocoord[1]-125),(ocoord[0]-150,ocoord[1]+125) )
            dcoord = net.getEdge(route[-1])._to._coord
            dshape = ( (dcoord[0],dcoord[1]),(dcoord[0]+150,dcoord[1]+125),(dcoord[0]+150,dcoord[1]-125) )
            
            pshape = ( (ocoord[0] - 50, ocoord[1] + 50), (ocoord[0] + 50, ocoord[1] - 50), (dcoord[0], dcoord[1]))
            
            traci.polygon.add(
                veh_id, pshape, vcolor, 1         
            )
            
            traci.simulationStep()
            return
    

def parse_args():
    
    parser = OptionParser(description='''Draws districts in a sumo-gui window''')
            
    parser.add_option(
        '-n', '--netfile', type=str, help = 'path to the network file'
    )
    
    parser.add_option(
        '-p', '--port', help='port number for sumo--traci', type=int,
        default=8813
    )
    
    parser.add_option(
        '-m', '--odmfile', type=str, help = 'path to the odm file'
    )
    
    parser.add_option(
        '-r', '--roufile', type=str, help = 'path to the .rou.xml file'
    )

    parser.add_option(
        '-t', '--tazfile', help='path to the districts file', 
        type=str
    )
    
    return parser.parse_args(sys.argv)
    
    
    
if __name__ == '__main__':
    (options, args) = parse_args()
#    drawdistricts(
#         options.netfile, options.tazfile, options.odmfile
#    )
    
    subprocess.Popen( ('sumo-gui -n %s --remote-port %d' % (options.netfile, options.port)) .split(' '))
    traci.init(options.port)
    
    print 'DONE'