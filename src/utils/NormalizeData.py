#Normalizes a given linearized data file
import sys
from math import sqrt
import gzip
from optparse import OptionParser

def getOptions():
    optparser = OptionParser(usage="%prog [options]\n-h for help")
    optparser.add_option("-i", "--input", dest="input", help="Gzipped file containing the linearized data")
    optparser.add_option("-o", "--output", dest="output", help="Output file")
    (options, args) = optparser.parse_args()
    if not options.input:
        optparser.error("No input file defined")
    if not options.output:
        optparser.error("No output file defined")
    return options, args
    
if __name__ == "__main__":
    options, args = getOptions()
    f = gzip.GzipFile(options.input)
    out = gzip.GzipFile(options.output, 'w')
    for line in f:
        line = line.strip().split()
        id = line.pop(0)
        output = line.pop(0)
        values = [float(x.split(":")[1]) for x in line]
        indices = [int(x.split(":")[0]) for x in line]
        norm = 0.
        for x in values:
            norm += x**2
        norm = sqrt(norm)
        values = [x/norm for x in values]
        line = id+" "+output+"".join(" %d:%f" %(x,y) for x,y in zip(indices, values))+"\n"
        out.write(line)
    f.close()
    out.close()
        
        

