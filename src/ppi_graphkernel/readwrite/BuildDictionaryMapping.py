"""
This module reads an analysis.xml-formatted training data file and
builds a dictionary of feature-mappings out of it, for the purpose of
linearizing the graph kernels.
"""

import sys
import gzip
from ppi_graphkernel import GraphMatrices
from ppi_graphkernel import MatrixBuilders
from optparse import OptionParser

#The graph kerne is initialized with the settings
#used for the paper
settings = MatrixBuilders.MatrixSettings()
command = "binary:all_shortest:nondirected:0.9"
settings.paths = command
settings.weightByDistance = False


def getOptions():
    optparser = OptionParser(usage="%prog [options]\n-h for help")
    optparser.add_option("-i", "--input", dest="input", help="Gzipped xml-file containing the parsed data")
    optparser.add_option("-o", "--output", dest="output", help="Output file for writing the dictionary")
    optparser.add_option("-p", "--parser", dest="parser", help="Name of the parser", default="split_parse")
    optparser.add_option("-t", "--tokenizer", dest="tokenizer", help="Name of the tokenizer", default="split")
    (options, args) = optparser.parse_args()
    if not options.input:
        optparser.error("No input file defined")
    if not options.output:
        optparser.error("No output file defined")
    return options, args

if __name__ == "__main__":
    options, args = getOptions()
    f = gzip.GzipFile(options.input, 'r')
    dict_out = gzip.GzipFile(options.output, 'w')
    documents = GraphMatrices.readInstances(f)
    instances = GraphMatrices.buildAMFromFullSentences(documents, MatrixBuilders.buildAdjacencyMatrix, settings, options.parser, options.tokenizer)
    f.close()
    datavector = []
    for document in instances.itervalues():
        for sentence in document.itervalues():
            for identity, instance in sentence.iteritems():
                datavector.append(instance)
    datavector = [(x[0], x[1]) for x in datavector]
    fmap = GraphMatrices.buildDictionary(datavector)
    for key in fmap.keys():
        dict_out.write(key+" %d\n" %(fmap[key]))
    dict_out.close()
    

