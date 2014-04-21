"""
This module reads an analysis.xml-formatted training data file and
builds a dictionary of feature-mappings out of it, for the purpose of
linearizing the graph kernels.
"""

import sys
import gzip
from argparse import ArgumentParser

from ppi_graphkernel import GraphMatrices
from ppi_graphkernel import MatrixBuilders


#The graph kernel is initialized with the settings
#used in the paper
settings = MatrixBuilders.MatrixSettings()
command = "binary:all_shortest:nondirected:0.9"
settings.paths = command
settings.weightByDistance = False


def getOptions():
    argparser = ArgumentParser(usage="%prog [options]\n-h for help")
    argparser.add_argument("-i", "--input", dest="input", help="Gzipped xml-file containing the parsed data")
    argparser.add_argument("-o", "--output", dest="output", help="Output file for writing the dictionary")
    argparser.add_argument("-p", "--parser", dest="parser", help="Name of the parser", default="split_parse")
    argparser.add_argument("-t", "--tokenizer", dest="tokenizer", help="Name of the tokenizer", default="split")
    args = argparser.parse_args()
    if not args.input:
        argparser.error("No input file defined")
    if not args.output:
        argparser.error("No output file defined")
    return args

if __name__ == "__main__":
    args = getOptions()
    with gzip.open(args.input, 'r') as f:
        documents = GraphMatrices.readInstances(f)

    instances = GraphMatrices.buildAMFromFullSentences(documents,
        MatrixBuilders.buildAdjacencyMatrix, settings, args.parser,
        args.tokenizer)

    datavector = []
    for document in instances.itervalues():
        for sentence in document.itervalues():
            for identity, instance in sentence.iteritems():
                datavector.append(instance)
    datavector = [(x[0], x[1]) for x in datavector]
    fmap = GraphMatrices.buildDictionary(datavector)

    with gzip.open(args.output, 'w') as dict_out:
        for key in fmap.keys():
            dict_out.write(key+" %d\n" %(fmap[key]))


