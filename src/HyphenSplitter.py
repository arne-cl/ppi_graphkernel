from optparse import OptionParser
try:
    import cElementTree as ElementTree
except ImportError:
    import xml.etree.cElementTree as ElementTree
import gzip
import sys
import re

# This regular expression determines which hyphenated tokens to split.
# The first and second groups determine how the split is performed.
# The current re is a rough heuristic rule: the text after the last
# hyphen must be either "(in)?dependent" or "like" or
# lowercase alphabetic ending with "ed" or "ing".
# should split: actin-based, actin-binding, cyclin-dependent, talin-like
# should not split: alpha-catenin, down-regulation, cell-cell, 10-fold
splitTokenRe = r'^(.+-)((in)?dependent|like|[a-z]+(ed|ing))$'

# the prefix to use for split token ids
tokenIdPrefix = "st_"

# the default name of the new tokenization
splitTokenizationName = "split"

# the default name of the new parse
newParseName = "split_parse"

# the special dependency type to connect split tokens with
splitDepName = "hyphen"

# returns a cElementTree element corresponding to a new tokenization
# in the given sentence element.
def addTokenization(tokenization, sentence, sentenceId):
    toks = sentence.find("sentenceanalyses/tokenizations")
    assert toks, "Missing <tokenizations> in sentence %s" % sentenceId

    # assume new-style XML format if there's at least one <tokenization> with
    # a "tokenizer" attribute. Also check duplicates.
    isNew = False
    for t in toks.getiterator("tokenization"):
        if t.get("tokenizer") is not None:
            assert t.get("tokenizer") is not None, "Split tokenization '%s' already exists in sentence %s!" % (tokenization, sentenceId)
            isNew = True

    if isNew:
        newTok = ElementTree.SubElement(toks, "tokenization")
        newTok.attrib["tokenizer"] = tokenization
    else:
        assert toks.find(tokenization) is None, "Split tokenization '%s' already exists in sentence %s!" % (tokenization, sentenceId)
        newTok = ElementTree.SubElement(toks, tokenization)

    return newTok

# returns a cElementTree element corresponding to the given tokenization
# in the given sentence element.
def getTokenization(tokenization, sentence, sentenceId):
    # first try the old-style XML format where there's an element with the
    # name of the tokenization
    tokPath = "sentenceanalyses/tokenizations/"+tokenization
    found = sentence.find(tokPath)

    if found is not None:
        return found
                                                                                    # then try the new-style format
    tokenizations = sentence.find("sentenceanalyses/tokenizations")
    assert tokenizations is not None, "ERROR: missing tokenizations for sentence %s" % sentenceId

    for t in tokenizations.getiterator("tokenization"):
        if t.get("tokenizer") == options.tokenization:
            return t

    return None


# returns a cElementTree element corresponding to a new parse in the
# given sentence element.
def addParse(parse, tokenization, sentence, sentenceId):
    # check whether the XML is new-style or old-style.
    parses = sentence.find("sentenceanalyses/parses")
    assert parses, "Missing <parses> in sentence %s" % sentenceId

    # assume new-style if we have at least one <parse> with a "parser"
    # attribute. Also check that a parse under the given name isn't there
    # already
    isNew = False
    for p in parses.getiterator("parse"):
        if p.get("parser") is not None:
            assert p.get("parser") != parse, "New parse '%s' already exists in sentence %s!" % (parse, sentenceId)
            isNew = True

    if isNew:
        newParse = ElementTree.SubElement(parses, "parse")
        newParse.attrib["parser"] = parse
        newParse.attrib["tokenizer"] = tokenization
    else:
        # check for overlap
        assert parses.find(parse) is None, "New parse '%s' already exists in sentence %s!" % (options.newparse, sentenceId)
        newParse = ElementTree.SubElement(parses, parse)

    return newParse
        
# returns a cElementTree element correspoding to the given parse
# in the given sentence element. Also checks that the parse is created
# for the given tokenization.
def getParse(parse, tokenization, sentence, sentenceId):
    # first try old-style format, then new.
    parsePath = "sentenceanalyses/parses/"+parse
    found = sentence.find(parsePath)

    if found is not None:
        return found

    parses = sentence.find("sentenceanalyses/parses")
    assert parses is not None, "ERROR: missing parses for sentence %s" % sentenceId

    for p in parses.getiterator("parse"):
        if p.get("parser") == parse:
            assert p.get("tokenizer") == tokenization, "ERROR: tokenization/parse mismatch: parse %s has tokenizer %s, not %s" % (parse, p.get("tokenizer"), tokenization)
            return p
            
    return None

# represents a token in the analysis XML.
class Token:
    def __init__(self, id, origId, pos, charOffset, text, splitFrom=None):
        self.id         = id
        self.origId     = origId
        self.pos        = pos
        self.charOffset = charOffset
        self.text       = text
        self.splitFrom  = splitFrom

# splits the <token>s in the given tokenization, returns a list of Token
# representing the new split ones.
def splitTokens(tokenization):
    # store the tokens for the new split tokenization here
    splitTokens = []
    seqId = 1
    
    for token in tokenization.getiterator("token"):
        nextId = "%s%d" % (tokenIdPrefix, seqId)
        seqId += 1

        text   = token.get("text")
        origId = token.get("id")
        POS    = token.get("POS")
        off    = token.get("charOffset")
        m = re.match(splitTokenRe, text)
        if not m:
            # no split, new token will match old one
            splitTokens.append(Token(nextId, origId, POS, off, text))
        else:
            # split. determine text and offsets of split parts and create
            # two new tokens.
            text1, text2 = m.group(1), m.group(2)
            assert text1+text2 == text, "ERROR: incomplete split"

            m = re.match(r'^(\d+)-(\d+)$', off)
            assert m, "ERROR: failed to parse charOffset '%s'" % off
            start, end = int(m.group(1)), int(m.group(2))

            start1, end1 = start, start + len(text1) -1,
            start2, end2 = end1+1, end1+1 + len(text2) -1
            assert end == end2, "LOGIC ERROR: %s %s %s"% (text, text1, text2)

            # make a separate token for the hyphen. Assume it's at the
            # end of the first token.
            assert text1[-1] == "-", "INTERNAL ERROR: last char of first token is not a hyphen"
            text1 = text1[:-1]
            end1 -= 1

            off1   = "%d-%d" % (start1, end1)
            offhyp = "%d-%d" % (start2-1, start2-1)
            off2   = "%d-%d" % (start2, end2)

            splitTokens.append(Token(nextId, origId, POS, off1, text1))
            tok1id = nextId

            nextId = "%s%d" % (tokenIdPrefix, seqId)
            seqId += 1

            # the hyphen-only token. Note no splitFrom.
            splitTokens.append(Token(nextId, origId, "-", offhyp, "-"))

            nextId = "%s%d" % (tokenIdPrefix, seqId)
            seqId += 1

            splitTokens.append(Token(nextId, origId, POS, off2, text2, tok1id))

    return splitTokens

# writes the given Tokens as <token>s into the given ElementTree element.
def addTokensToTree(tokens, element):
    for t in tokens:
        newToken = ElementTree.SubElement(element, "token")
        newToken.attrib["id"]   = t.id
        newToken.attrib["text"] = t.text
        newToken.attrib["POS"]  = t.pos
        newToken.attrib["charOffset"] = t.charOffset

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

if __name__=="__main__":
    optParser = OptionParser(usage="%prog [OPTIONS]\nModifies one parse and associated tokenization to split (some) hyphenated\nwords, e.g. \"actin-binding\".")
    optParser.add_option("-f", "--analysisFile", dest="file", metavar="FILE", default=None, help = "Path to the xml-formatted analysis file")
    optParser.add_option("-p", "--parse", dest="parse", default = None, help = "Name of the parse to modify")
    optParser.add_option("-t", "--tokenization", dest="tokenization", default=None, help="Name of the tokenization to modify")
    optParser.add_option("-s", "--splittokenization", dest="splittokenization", default=splitTokenizationName, help="Name of the new split tokenization to create")
    optParser.add_option("-n", "--newparse", dest="newparse", default=newParseName, help="Name of the new parse to create")
    (options, args) = optParser.parse_args()

    if (options.file is None or options.parse is None or
        options.tokenization is None):
        print >> sys.stderr, "The -f, -p and -t options are mandatory."
        optParser.print_help()
        sys.exit(1)

    if options.file.endswith(".gz"):
        inFile = gzip.GzipFile(options.file)
    else:
        inFile = open(options.file)

    tree = ElementTree.parse(inFile)
    root = tree.getroot()

    for sentence in root.getiterator("sentence"):
        sId = sentence.get("id")

        tok   = getTokenization(options.tokenization, sentence, sId)
        assert tok is not None, "Missing tokenization '%s' in sentence %s!" % (options.tokenization, sId)

        parse = getParse(options.parse, options.tokenization, sentence, sId)
        assert parse is not None, "Missing parse '%s' in sentence %s!" % (options.parse, sId)
        
        split = splitTokens(tok)

        # add a new tokenization with the split tokens.
        splittok = addTokenization(options.splittokenization, sentence, sId)
        addTokensToTree(split, splittok)

        # make a mapping from original to split token ids. Note that for
        # split tokens, only the last of the split parts will be stored.
        tokenIdMap = {}
        for t in split:
            tokenIdMap[t.origId] = t.id

        # make a copy of the specified parse that refers to the split tokens
        # instead of the originals.
        newparse = addParse(options.newparse, options.splittokenization, sentence, sId)

        depSeqId = 1
        for d in parse.getiterator("dependency"):
            t1, t2, dType = d.get("t1"), d.get("t2"), d.get("type")
            assert t1 in tokenIdMap and t2 in tokenIdMap, "INTERNAL ERROR"

            dep = ElementTree.SubElement(newparse, "dependency")
            dep.attrib["t1"]   = tokenIdMap[t1]
            dep.attrib["t2"]   = tokenIdMap[t2]
            dep.attrib["type"] = dType
            dep.attrib["id"]   = "split_%d" % depSeqId
            depSeqId += 1

        # Add in new dependencies between the split parts.
        for t in [tok for tok in split if tok.splitFrom is not None]:
            dep = ElementTree.SubElement(newparse, "dependency")
            dep.attrib["t1"]   = t.id
            dep.attrib["t2"]   = t.splitFrom
            dep.attrib["type"] = splitDepName

    indent(root)
    tree.write(sys.stdout)
