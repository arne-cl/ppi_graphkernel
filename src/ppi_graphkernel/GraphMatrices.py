"""
This module contains utilities meant to help the forming of graph
kernels for the PPI-extraction task.
"""

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import cElementTree as ET
import sys

from numpy import float64, identity, mat
from numpy.linalg import inv

from ppi_graphkernel import Kernel
from ppi_graphkernel.MatrixBuilders import MatrixSettings

# TODO: are these constants used anywhere?
FLOATTYPE = float64
PARSER = "split_parse"
TOKENIZER = "split"
KERNEL = Kernel.Kernel()

feature_counter = 0
# TODO: why is this a global variable? It's only used in
# buildDictionary()?


def readInstances(a_file):
    """Parses the analysis file to extract the analyses on which the
    graphs will be based on"""
    result = {}
    acontent = iter(ET.iterparse(a_file,events=("start","end")))
    event, root = acontent.next()
    for event, elem in [(a,b) for a,b in acontent if a=="end" and b.tag=="document"]:
        doc_id = elem.get("id")
        result[doc_id] = elem
    return result

def belongsTo(offset, charOffsets):
    for of in charOffsets:
        if (of[0]<= offset[0] and of[1]>= offset[0]) or (of[1]>= offset[1] and of[0] <= offset[1]):
            return True
    return False

def buildAMFromFullSentences(documents, AM_builder, matrixSettings, parser, tokenizer, prepMatrix = True, limit = None):
    """Builds adjacency matrices that have the same structure for all pairs from the
    same sentence, and differ only by their labels. Returns a nested dictionary,
    where a dictionary of document ids contains a dictionary of sentence ids,
    which contains a dictionary of pair_id-matrix pairs."""
    doc_dictionary = {}
    print >> sys.stderr, "Processing", len(documents), "documents"
    documentCount = 0
    for doc_id in documents:
        if limit != None and documentCount >= limit:
            break
        print >> sys.stderr, "\rProcessing document " + str(documentCount+1),
        document = documents[doc_id]
        doc_sent_dictionary = {}
        for child in document:
            if child.tag == "sentence":
                sent_dictionary = {}
                it = child.getiterator("tokenization")
                tokenlist = None
                for toks in it:
                    if toks.get("tokenizer")== tokenizer:
                        tokenlist = toks
                #tokenlist = it.next()
                tokens = [x for x in tokenlist]
                it = child.getiterator("parse")
                deplist = None
                for deps in it:
                    if deps.get("parser") == parser and deps.get("tokenizer") == tokenizer:
                        deplist = deps
                #deplist = it.next()
                if tokenlist == None:
                    print "Tokenizer %s unknown" %(tokenizer)
                    sys.exit(0)
                elif deplist == None:
                    print child.get("id")
                    print "Parser %s unknown" %(parser)
                    sys.exit(0)
                dependencies = [x for x in deplist]
                it = child.getiterator("entity")
                entities = [x for x in it]
                mappings = None
                if matrixSettings.metamappings == MatrixSettings.metamappings.direct:
                    metanode = child.getiterator("metamappings")
                    metanode = metanode.next()
                    for node in metanode:
                        if node.get("relToParse")==parser and node.get("relToTokenization")==tokenizer:
                            mappings = node
                            break
                    assert mappings
                    mappings = [x for x in mappings]
                for pair in child.getiterator("pair"):
                    W, labels, output = AM_builder(tokens, dependencies, entities, mappings, pair, matrixSettings)
                    if prepMatrix:
                        node_count = 2*len(tokens) + len(dependencies)
                        W = prepareMatrix(W, node_count)
                    sent_dictionary[pair.get("id")] = W, labels, output
                doc_sent_dictionary[child.get("id")] = sent_dictionary
        doc_dictionary[doc_id] = doc_sent_dictionary
        documentCount += 1
    print >> sys.stderr
    return doc_dictionary


def buildDictionary(instances):
    feature_map = {}
    global feature_counter
    for instance in instances:
        W = instance[0]
        labels = instance[1]
        for i in range(W.shape[0]):
            for j in range(W.shape[1]):
                if W[i,j] > 0.00001:
                    for label1 in labels[i]:
                        for label2 in labels[j]:
                            label = label1+"_$_"+label2
                            if not label in feature_map:
                                feature_map[label] = feature_counter
                                feature_counter += 1
    return feature_map

def LinearizeGraph(W, labels, feature_map, mode):
    #proteins = set(["PROTEIN1", "PROTEIN2", "$$PROTEIN1", "$$PROTEIN2"]) 
    """Linearizes the representation of the graph"""
    linear = {}
    for i in range(W.shape[0]):
        for j in range(W.shape[1]):
            if W[i,j] > 0.00001:
                for label1 in labels[i]:
                    for label2 in labels[j]:
                        #if label1 in proteins or label2 in proteins:
                        label = label1+"_$_"+label2
                        if label in feature_map:
                            if not feature_map[label] in linear:
                                linear[feature_map[label]] = 0.
                            if mode == "max":
                                if W[i,j] > linear[feature_map[label]]:
                                    linear[feature_map[label]] = W[i,j]
                            elif mode == "sum":
                                linear[feature_map[label]] += W[i,j]
                            else:
                                print "Error at GraphMatrices LinearizeGraph: Unsupported Mode %s" %mode
                                sys.exit(0)
                                
    return linear

def prepareMatrix(adjacencyMatrix, node_count, dtyp=float64):
    #W = inv(W) - mat(identity(node_count, dtype=float64))
    W = adjacencyMatrix * -1.0
    W += mat(identity(node_count, dtype = dtyp))    
    return inv(W) - mat(identity(node_count, dtype=dtyp))

def LinearizeGraphs(instances, feature_map, mode):
    result = []
    for instance in instances:
        result.append(LinearizeGraph(instance[0], instance[1], feature_map, mode))
    return result
