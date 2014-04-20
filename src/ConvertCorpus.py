"""
  Program:    GifXML corpus converter
  Date:       Oct. 9, 2007
  Author:     Jari Bjoerne

  Description: This program converts a corpus from GifXML to the XML-format used
               in the machine learning project. Interactions are replaced with
               all undirected pairs between entities. Analysis and Feature-sections
               are not written for now, because they would be empty. It might also
               be useful to write them at this stage, but this has to be still decided.
                
  Status: Early version, seems to work but largely untested.

  Dependencies: cElementTree-library
                CVSUtils.py
"""

import sys
import xml.etree.cElementTree as ElementTree

##
# Indents an element structure in place.
#
# @param elem Element structure.
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
        if not e.tail or not e.tail.strip():
            e.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

def convertCorpus(filename):
    """ 
    Takes a filename (or file-like object) as parameter and returns
    the modified XML-tree.
    """
    tree = ElementTree.parse(filename)
    root = tree.getroot()
    sentences = root.getiterator("sentence")
    
    
    sys.stderr.write("Processing sentences\n")
    for sentence in sentences:
        sentenceId = sentence.get("id")
        sys.stderr.write("Sentence: "+ str(sentenceId)+"\n")
        entities = sentence.findall("entity")
        interactions = sentence.findall("interaction")
        
        # Remove interactions from the XML-tree as they are going to be replaced with pairs
        for interaction in interactions:
            sentence.remove(interaction)
        
        # Create the pairs
        pairIndex = 0
        pair = None
        for i in range(len(entities)):
            for j in range(i+1,len(entities)):
                pair = ElementTree.Element("pair")
                pair.attrib["id"] = sentenceId + ".p" + str(pairIndex)
                pair.attrib["e1"] = entities[i].get("id")
                pair.attrib["e2"] = entities[j].get("id")
                
                isInteraction = False
                for interaction in interactions:
                    if (interaction.get("e1") == pair.get("e1") and interaction.get("e2") == pair.get("e2")) or \
                    (interaction.get("e2") == pair.get("e1") and interaction.get("e1") == pair.get("e2")):
                        isInteraction = True
                        break
                if isInteraction:
                    pair.attrib["interaction"] = "True"
                else:
                    pair.attrib["interaction"] = "False"
                
                # Add the new pair to the sentence element
                sentence.append(pair)
                pairIndex += 1
    sys.stderr.write("Sentences processed\n")
    sys.stderr.write("Indenting XML:")
    indent(root)
    sys.stderr.write("OK\n")
    return tree

if __name__=="__main__":
    from optparse import OptionParser

    optparser = OptionParser(usage="%prog [options]\nConvert a GifXMl corpus to the analysis format (with pairs etc).")
    optparser.add_option("-i", "--input", dest="input", help="GifXML-file", metavar="FILE")
    optparser.add_option("-o", "--output", dest="output",  help="Converted ML-XML-file", metavar="FILE")
    optparser.add_option("-s", "--stdout", dest="stdout", default=False, help="Print output to stdout", action="store_true")
    (options, args) = optparser.parse_args()
    
    sys.stderr.write("Converting corpus\n")
    convertedCorpusTree = convertCorpus(options.input)
    sys.stderr.write("Corpus converted\n")
    sys.stderr.write("Writing converted corpus:")
    if options.stdout:
        convertedCorpusTree.write(sys.stdout)
    else:
        convertedCorpusTree.write(options.output)
    sys.stderr.write("OK\n")
    
    

