import sys
import numpy

try:
    import cElementTree as ET
except ImportError:
    import xml.etree.cElementTree as ET

from enum import Enum

from ppi_graphkernel import ParseGraph
from ppi_graphkernel.readwrite import LoadInteractionWords

floattype = numpy.float64

class MatrixSettings:
    """
    MatrixSettings is used to define the various options for generating
    the adjacency matrix.
    """
    ppiTexts = Enum("full", "stem")
    markedInteractionWords = Enum("fromTertiaryPaths")
    metamappings = Enum("none", "direct")
    
    def __init__(self):
        # Interaction xml modification
        self.removeDependencies = ["punct"]
        # Parse graph settings
        self.directed = True 
        self.linearOrderWeight = 0.9
        self.weightByDistance = False
        self.mergeDependencies = False
        self.paths = "binary:all:0.9"
        self.pathTimeout = None # None or time in seconds
        self.interactionWords = []
        self.markInteractionWords = MatrixSettings.markedInteractionWords.fromTertiaryPaths
        # Dependency weights
        self.depBaseWeight = 0.3
        self.depPathWeight = 0.9
        self.depWeightReductionThreshold = 0.9
        self.depWeightReductionFactor = 0.5
        # Dependency prefix
        self.depPrefixThreshold = 0.9
        self.depPrefix = "sp"
        # Token text modification
        self.tokenPPIText = MatrixSettings.ppiTexts.full
        self.maskPPIText = True
        self.tokenPositionTags = True
        #Metamap settings
        self.metamappings = MatrixSettings.metamappings.none
    
    def toString(self):
        string = "----- Adjacency Matrix Settings -----\n"
        string += "Interaction xml modification\n"
        string += "  removed dependencies: " + str(self.removeDependencies) + "\n"
        string += "Parse graph settings\n"
        string += "  directed: " + str(self.directed) + "\n"
        string += "  linear order weight: " + str(self.linearOrderWeight) + "\n"
        string += "  reduce weight by distance: " + str(self.weightByDistance) + "\n"
        string += "  merge dependencies:" + str(self.mergeDependencies) + "\n"
        string += "  paths: " + self.paths + "\n"
        string += "  path timeout:" + str(self.pathTimeout) + "\n"
        string += "Dependency weights\n"
        string += "  base weight: " + str(self.depBaseWeight) + "\n"
        string += "  path weight: " + str(self.depPathWeight) + "\n"
        string += "  reduction threshold: " + str(self.depWeightReductionThreshold) + "\n"
        string += "  reduction factor: " + str(self.depWeightReductionFactor) + "\n"
        string += "Dependency prefix\n"
        string += "  threshold: " + str(self.depPrefixThreshold) + "\n"
        string += "  prefix: " + self.depPrefix + "\n"
        string += "Token text modification\n"
        string += "  ppi text: " + str(self.tokenPPIText) + "\n"
        string += "  mask: " + str(self.maskPPIText) + "\n"
        string += "  position tags: " + str(self.tokenPositionTags) + "\n"
        string += "Metamap\n"
        string += "  mapping: " + str(self.metamappings)
        return string

def getMatrixSettingsForShortestTertiaryPaths(weightByDistance=True, stem=False):
    m = MatrixSettings()
    m.paths = "all_tertiary:all_shortest:nondirected:0.9"
    m.interactionWords = LoadInteractionWords.loadInteractionWords("../../JariSandbox/PPIDependencies/Data/InteractionWordsAllWords.txt")
    m.weightByDistance = weightByDistance
    if stem:
        m.tokenPPIText = MatrixSettings.ppiTexts.stem
    return m

def getMatrixSettingsForShortestBinaryPaths(weightByDistance=True, stem=False):
    m = MatrixSettings()
    m.paths = "binary:all_shortest:nondirected:0.9"
    m.weightByDistance = weightByDistance
    if stem:
        m.tokenPPIText = MatrixSettings.ppiTexts.stem
    return m

def getMatrixSettingsForAllBinaryPaths(weightByDistance=True, stem=False):
    m = MatrixSettings()
    m.paths = "binary:all:nondirected:0.9"
    m.weightByDistance = weightByDistance
    if stem:
        m.tokenPPIText = MatrixSettings.ppiTexts.stem
    return m

# Common helper functions #####################################################

def removeDependencies(dependencyElements, typesToRemove):
    for dependencyElement in dependencyElements[:]:
        if dependencyElement.get("type") in typesToRemove:
            dependencyElements.remove(dependencyElement)
    return dependencyElements

# Adjacency Matrix Builders ###################################################

def buildAdjacencyMatrix(tokenElements, dependencyElements, entityElements, metamapElements, pairElement, matrixSettings):
    m = matrixSettings
    
    #Punctuation dependencies are mostly junk
    dependencyElements = removeDependencies(dependencyElements, m.removeDependencies)
    
    parseGraph = ParseGraph.ParseGraph(tokenElements, dependencyElements, m.mergeDependencies)
    parseGraph.shortestPathMethod = "dijkstra"
    parseGraph.markNamedEntities(entityElements)
    e1Id = pairElement.get("e1")
    e2Id = pairElement.get("e2")
    entity1TokenIds = parseGraph.getNamedEntityTokenIds( [e1Id] )
    entity2TokenIds = parseGraph.getNamedEntityTokenIds( [e2Id] )
    interactionWordTokenIds = parseGraph.getTokenIdsByText(m.interactionWords, False)

    # Give dependencies base weights
    parseGraph.setAllDependencyWeights(m.depBaseWeight)

    # Set dependencies' weights based on paths
    pathStyles = ParseGraph.splitPathStyles(m.paths)
    for style in pathStyles:
        paths = []
        if style["type"] == "binary":
            paths = parseGraph.buildBinaryPaths(entity1TokenIds, entity2TokenIds, style["length"], style["direction"]=="directed", m.pathTimeout)
        elif style["type"].find("tertiary") != -1:
            paths = parseGraph.buildTertiaryPaths(entity1TokenIds, interactionWordTokenIds, entity2TokenIds, style["type"]=="closest_tertiary", style["length"], style["direction"]=="directed", m.pathTimeout)
            if m.markInteractionWords == MatrixSettings.markedInteractionWords.fromTertiaryPaths:
                parseGraph.setPPIInteractionWords(paths)
            for i in range(len(paths)):
                paths[i] = paths[i][0]
        if paths != None:
            parseGraph.setDependencyWeightsByPath(paths, style["weight"])
    
    # Reduce dependencies' weights by distance from threshold
    if m.weightByDistance:
        parseGraph.reduceWeightByDistance(m.depWeightReductionThreshold, m.depWeightReductionFactor)
    # Set dependency prefixes
    if m.depPrefixThreshold > 0.0:
        parseGraph.setPPIPrefixForDependencies(m.depPrefix, m.depPrefixThreshold) # f.e. shortest path prefix
    
    # Set token texts
    if m.tokenPPIText == MatrixSettings.ppiTexts.full:
        parseGraph.ppiTextFromOriginalText()
    elif m.tokenPPIText == MatrixSettings.ppiTexts.stem:
        parseGraph.ppiTextFromStems()
    else:
        print >> sys.stderr, "Illegal ppiText setting", m.tokenPPIText
        sys.exit(0)
    
    # Add metamap codes
    if metamapElements != None:
        metamapDict = {}
        for metamapElement in metamapElements:
            metamapDict[metamapElement.get("tokenid")] = metamapElement.get("basecodes").split(",")
        parseGraph.addMetamapCodes(metamapDict)
    
    if m.maskPPIText:
        parseGraph.maskNames(e1Id, e2Id)
    if m.tokenPositionTags:
        parseGraph.addPositionTags(entity1TokenIds, entity2TokenIds)
    
    if pairElement.get("interaction") == "True":
        output = 1.
    else:
        output = -1.

    adjMatrix, labels = parseGraph.buildAdjacencyMatrix(floattype, m.directed, m.linearOrderWeight)
    return adjMatrix, labels, output    


def buildAdjacencyMatrixWithShortestPaths(tokenElements, dependencyElements, entityElements, pairElement, directed = True, weight_by_distance = False):
    #Punctuation dependencies are mostly junk
    dependencyElements = removeDependencies(dependencyElements, ["punct"])
    
    parseGraph = ParseGraph.ParseGraph(tokenElements, dependencyElements)
    parseGraph.markNamedEntities(entityElements)
    e1Id = pairElement.get("e1")
    e2Id = pairElement.get("e2")
    entity1TokenIds = parseGraph.getNamedEntityTokenIds( [e1Id] )
    entity2TokenIds = parseGraph.getNamedEntityTokenIds( [e2Id] )

    binaryPaths = parseGraph.buildBinaryPaths(entity1TokenIds, entity2TokenIds)
    shortestPaths = ParseGraph.getShortestPaths(binaryPaths)
    parseGraph.setAllDependencyWeights(0.3)
    parseGraph.setDependencyWeightsByPath(shortestPaths, 0.9)
    if weight_by_distance:
        parseGraph.reduceWeightByDistance(0.9, 0.5)
    parseGraph.setPPIPrefixForDependencies("sp", 0.9) # shortest path prefix
    parseGraph.maskNames(e1Id, e2Id)
    parseGraph.addPositionTags(entity1TokenIds, entity2TokenIds)
    
    if pairElement.get("interaction") == "True":
        output = 1.
    else:
        output = -1.

    adjMatrix, labels = parseGraph.buildAdjacencyMatrix(floattype)
    return adjMatrix, labels, output    

def buildAdjacencyMatrixWithAllPaths(tokenElements, dependencyElements, entityElements, pairElement, directed = True, weight_by_distance = False):
    #Punctuation dependencies are mostly junk
    dependencyElements = removeDependencies(dependencyElements, ["punct"])
    
    parseGraph = ParseGraph.ParseGraph(tokenElements, dependencyElements)
    parseGraph.markNamedEntities(entityElements)
    e1Id = pairElement.get("e1")
    e2Id = pairElement.get("e2")
    entity1TokenIds = parseGraph.getNamedEntityTokenIds( [e1Id] )
    entity2TokenIds = parseGraph.getNamedEntityTokenIds( [e2Id] )

    binaryPaths = parseGraph.buildBinaryPaths(entity1TokenIds, entity2TokenIds)
    parseGraph.setAllDependencyWeights(0.3)
    parseGraph.setDependencyWeightsByPath(binaryPaths, 0.9)
    if weight_by_distance:
        parseGraph.reduceWeightByDistance(0.9, 0.5)
    parseGraph.setPPIPrefixForDependencies("sp", 0.9) # shortest path prefix
    parseGraph.maskNames(e1Id, e2Id)
    parseGraph.addPositionTags(entity1TokenIds, entity2TokenIds)
    
    if pairElement.get("interaction") == "True":
        output = 1.
    else:
        output = -1.

    adjMatrix, labels = parseGraph.buildAdjacencyMatrix(floattype)
    return adjMatrix, labels, output
