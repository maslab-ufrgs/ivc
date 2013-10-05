'''
Created on Feb 7, 2013

@author: anderson
'''

import sys
print sys.argv
infiles = sys.argv[1:]

print 'Input files:', infiles

files = [open(infile) for infile in infiles]

#for i in range(2):
#    print files[i].readline()
#print files[0].readlines()


all_data = [[line.strip().split(',') for line in f] for f in files]
#data = [l for l in [lines for lines in [f.readlines() for f in files]]]

#numbers = [[[float(elem) for elem in line[2:]]] for line in all_data]
#numbers = [[[float(elem) for elem in line[1:]] for line in lines[2:] ] for lines in all_data]
numbers = [[[float(elem) for elem in line] for line in lines[2:] ] for lines in all_data]

averages = [[sum(x)/len(x) for x in (numbers[i][j]])] for j in range(len(numbers[i])) for i in range(numbers)]

#[n[i][0][0] for i in range(len(n))]