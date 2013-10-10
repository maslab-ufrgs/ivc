'''
Outputs the average values of drivers performance 
grouped per driver type (ivc-replan, noivc-noreplan, etc.)

Created on 15/05/2013

@author: artavares

'''
import sys
from optparse import OptionParser


def group_averages(infile, outfile):
    in_array = open(infile, 'r').readlines()
    out = open(outfile, 'w')
    
    #ids are in 1st line from 2nd col onwards
    ids = in_array[0].strip().split(',')[1:]
    
    #types are in 2nd line from 2nd col onwards
    types = in_array[1].strip().split(',')[1:]
    
    #build a dict {id: type,...} of all drivers
    drv_types = dict((ids[i],types[i]) for i in range(len(ids)))
    
    unique_types = list(set(types))
    
    #writes the output header
    out.write('x,' + ','.join(unique_types) + '\n')
    
    #traverses the data which are in 3rd row onwards of input
    lineno = 1
    for line in in_array[2:] :
        averages = dict((typ,0) for typ in unique_types)
        count = dict((typ,0) for typ in unique_types)
        
        data = line.strip().split(',')[1:]
        
        for i in range(len(data)):
            averages[types[i]] = new_average(averages[types[i]], data[i], count[types[i]])
            count[types[i]] += 1
            
        out.write('%d,' % lineno)
        
        out.write(','.join([str(avg) for avg in averages.values()]))
        
        #print ','.join([str(cnt) for cnt in count.values()])        
            
        out.write('\n')
        lineno += 1
        
def new_average(old_avg, new_value, stepnum):
    return ( (float(new_value) - float(old_avg)) / (stepnum + 1)) + old_avg

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
    group_averages(options.input, options.output)
    print 'DONE'
    
    