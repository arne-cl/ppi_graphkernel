#Utilities for reading in the files used by the
#RLS software
#The format used is quite close to that of SVM light

from optparse import OptionParser
import sys
import re
#from scipy import sparse
from numpy import float64
from numpy import zeros
from numpy import mat

error = sys.stderr.write

def split_instance_line(line):
    """Splits an instance line, supplied in the similar format as
    that used by SVMLight package, to labels, qid, attributes and comment.
    Labels are the first sequence of characters at the start of line,
    then follows optionally a qid-attribute, then normal attributes,
    and finally # can be used to comment out rest of the line."""
    line = line.strip().split()
    identity = line.pop(0)
    #One or more labels, using separator |, are supposed to be at
    #the beginning of the line
    labels = line.pop(0)
    return labels, line, identity
    
def readInstanceFile(source):
    """Reads in the data and checks that the input file is correctly formatted. Additionally
    1. Calculates the number of examples
    2. Calculates the dimensionality of the feature space
    3. Calculates the number of outputs used
    4. Checks whether the data is sparse
    This information is returned to the caller.
    All of the data is read into memory"""
    #Regular expressions could be used also, but it is not any faster, main
    #overhead is from iterating through lines.

    #some interesting statistics are calculated
    labelcount = None
    linecounter = 0
    feaspace_dim = 0
    nonzeros = 0
    #Features, labels, comments and possibly qids are later returned to caller
    #The indexing, with respect to the instances, is the same in all the lists.
    all_labels = []
    all_features = []
    all_identities = []
    #Each line in the source represents an instance
    for line in source:
        linecounter += 1
        labels, attributes, identity = split_instance_line(line)
        all_identities.append(identity)
         #Multiple labels are allowed, but each instance must have the
        #same amount of them. Labels must be real numbers.
        labels = labels.split("|")
        if labelcount == None:
            labelcount = len(labels)
        #Check that the number of labels is the same for all instances
        #and that the labels are real valued numbers.
        else:
            if labelcount != len(labels):
                error("Error: Number of labels assigned to instances differs.\n")
                error("First instance had %d labels whereas instance on line %d has %d labels\n" %(labelcount, linecounter, len(labels)))
                sys.exit(-1)
        label_list = []
        #We check that the labels are real numbers and gather them
        for label in labels:
            try:
                label = float(label)
                label_list.append(label)
            except ValueError:
                error("Error: label %s on line %d not a real number\n" %(label, linecounter))
                sys.exit(-1)
        all_labels.append(label_list)
        previous = -1
        features = []
        #Attributes indices must be positive integers in an ascending order,
        #and the values must be real numbers.
        for att_val in attributes:
            index, value = att_val.split(":")
            try:
                index = int(index)
                value = float(value)
                features.append((index, value))
            except ValueError:
                error("Error: feature:value pair %s on line %d is not well-formed\n" %(att_val, linecounter))
                sys.exit(-1)
            if not index > previous:
                error("Error: line %d features must be in ascending order\n" %(linecounter))
                sys.exit(-1)
            previous = index
            if index > feaspace_dim:
                feaspace_dim = index
            if value != 0.:
                nonzeros += 1
        all_features.append(features)
    #That's all folks
    feaspace_dim +=1
    return all_labels, all_features, all_identities, feaspace_dim, nonzeros      

def buildLabelMatrix(labels):
    Y = mat(zeros((len(labels), len(labels[0])), dtype = float64))
    for i, labelset in enumerate(labels):
        for j, label in enumerate(labelset):
            Y[i,j] = label
    return Y
    

def buildDictionary(features):
    instances = []
    for fset in features:
        dictionary = {}
        for index, value in fset:
            dictionary[index] = value
        instances.append(dictionary)
    return instances

def buildDenseDataMatrix(features, feaspace_dim):
    X = mat(zeros((feaspace_dim, len(features)), dtype=float64))
    for i, instance in enumerate(features):
        for index, value in instance:
            #Indices range from 1..n in the data file, and from 0...n-1 in
            #the matrix representation
            index -= 1
            X[index, i] = value
    return X

def readData(source, kernelname):
    #Check that input is in order, and gather statistics nexessary for proceeding
    labels, features, identities, feaspace_dim, nonzeros = readInstanceFile(source)
    assert len(labels) == len(features)
    assert len(features) == len(identities)
    instance_count = len(features)
    nonzero_fraction = float(nonzeros)/float(instance_count*feaspace_dim)
    dictionary = buildDictionary(features)
    Y = buildLabelMatrix(labels)
    return identities, dictionary, Y, feaspace_dim    
