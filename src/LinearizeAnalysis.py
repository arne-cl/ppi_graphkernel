#Linearizes the instances in a given analysis.xml-file, based
#on a dictionary of feature-index mappings built from the
#training data using the buldDictionaryMapping.py script.
import sys
import gzip
import GraphMatrices
import MatrixBuilders
from optparse import OptionParser

#The graph kerne is initialized with the settings
#used for the paper
settings = MatrixBuilders.MatrixSettings()
command = "binary:all_shortest:nondirected:0.9"
settings.paths = command

def readDictionaryMapping(file):
    dictionary = {}
    for line in file:
        line = line.strip().split()
        assert len(line) == 2
        dictionary[line[0]] = int(line[1])
    return dictionary

def getOptions():
    optparser = OptionParser(usage="%prog [options]\n-h for help")
    optparser.add_option("-i", "--input", dest="input", help="Gzipped xml-file containing the parsed data")
    optparser.add_option("-o", "--output", dest="output", help="Output file for writing the linearized data")
    optparser.add_option("-p", "--parser", dest="parser", help="Name of the parser", default="split_parse")
    optparser.add_option("-t", "--tokenizer", dest="tokenizer", help="Name of the tokenizer", default="split")
    optparser.add_option("-d", "--dictionary", dest="dictionary", help="Path to to the dictionary file")
    optparser.add_option("-m", "--mode", dest="mode", type = "choice", choices = ["max", "sum"], default = "max",  help="Two alternative modes. 'max' takes the maximum value of the weights of paths connecting two labels, sum takes the sum. (default: max)") 
    (options, args) = optparser.parse_args()
    if not options.input:
        optparser.error("No input file defined")
    if not options.output:
        optparser.error("No output file defined")
    if not options.dictionary:
        optparser.error("No dictionary file defined")
    return options, args


if __name__=="__main__":
    options, args = getOptions()
    f = gzip.GzipFile(options.dictionary, 'r')
    dictionary = readDictionaryMapping(f)
    f.close()
    f = gzip.GzipFile(options.input, 'r')
    documents = GraphMatrices.readInstances(f)
    instances = GraphMatrices.buildAMFromFullSentences(documents, MatrixBuilders.buildAdjacencyMatrix, settings, options.parser, options.tokenizer)
    f.close()
    f = gzip.GzipFile(options.output,'w')
    datavector = []
    identities = []
    for document in instances.itervalues():
        for sentence in document.itervalues():
            for identity, instance in sentence.iteritems():
                identities.append(identity)
                datavector.append(instance)
    outputs = [x[2] for x in datavector]
    datavector = [(x[0], x[1]) for x in datavector]
    datavector = GraphMatrices.LinearizeGraphs(datavector, dictionary, options.mode)
    for id, output, features in zip(identities, outputs, datavector):
        keys = features.keys()
        keys.sort()
        line = id + " " + str(output) + "".join(" %d:%.5f" %(x,features[x]) for x in keys)+"\n"
        f.write(line)
    f.close()

