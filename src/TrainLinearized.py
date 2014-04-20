#Trains a sparse RLS learner and stores the learned model to a file

import sys

from numpy import *
import Kernel
import SparseRLS
import PerformanceMeasures
import gzip
from math import sqrt
import random
import MatrixBuilders
from Utilities import optimalFThreshold
floattype = float64
import FileReader
from optparse import OptionParser

def readParameters(source):
    best = 0., 0.
    for line in source:
        line = line.strip().split()
        F = float(line[2].split(":")[1])
        if F > best[0]:
            lamb = float(line[0].split(":")[1])
            best = F, lamb
    assert best[0] > 0.
    lamb = best[1]
    return lamb

def getOptions():
    optparser = OptionParser(usage="%prog [options]\n-h for help")
    optparser.add_option("-i", "--input", dest="input", help="training data file", metavar="FILE")
    optparser.add_option("-o", "--output", dest="output", help="output file, where the model (coefficients of the hyperplane) is written", metavar="FILE")
    optparser.add_option("-p", "--parameters", dest="params", help="Optional parameter file, where the results of running the cross-validation are stored. If this is supplied, value of the regularization parameter is read from here.", metavar="FILE")
    optparser.add_option("-r", "--regparam", type="float", dest="regparam", help="Value of the regularization parameter", default=1.0)
    optparser.add_option("-b", "--bvectors", type="int", dest="bvectors", help="Number of basis vectors used. If this exceeds the size of the training set, all of the training examples are used as basis vectors.", metavar="FILE", default=500)
    optparser.add_option("-s", "--seed", type="int", dest="seed", help="Random seed number for sampling the basis vectors.", default=13)
    (options, args) = optparser.parse_args()
    if not options.input:
       optparser.error("No input file defined")
    if not options.output:
        optparser.error("No output file defined")
    return options, args

if __name__=="__main__":
    options, args = getOptions()
    rseed = options.seed
    filename = options.input
    output_file = options.output
    bv_count = options.bvectors
    print 'Reading data'
    f = gzip.GzipFile(filename)
    if options.params:
        f2 = open(options.params)
        regparam = readParameters(f2)
        regparam = 2**regparam
        f2.close()
    else:
        regparam = options.regparam
    print "Chosen regularization parameter", regparam
    print "Reading data"
    identities, datavector, Y, fspace_dim = FileReader.readData(f, "l")
    f.close()
    print "data read in"
    tsetsize = len(datavector)
    if bv_count > tsetsize:
        bv_count = tsetsize
    #Sparse version is created next
    random.seed(rseed)
    indices = range(tsetsize)
    #As experimentally shown by Rifkin, random sampling
    #seems to be as good way of choosing basis vectors as any
    includedindices = random.sample(indices, bv_count)
    includedindices.sort()

    print "Generating kernel matrix"
    #We create a basis_vectors*training_set sized kernel matrix
    km = mat(zeros((bv_count, tsetsize), dtype =floattype))
    print "Forming kernel matrix of shape", km.shape
    kernel = Kernel.Kernel()
    #Instantiate the kernel matrix
    #This could be optimized, because the kernels between the basis
    #vectors are in this version each counted twice, as the symmetry
    #of the bv-indexed submatrix is not taken advantage of.
    for i in range(bv_count):
        for j in range(tsetsize):
            val = kernel.kernel(datavector[includedindices[i]], datavector[j])
            km[i,j] = val

    #Force positive definitivness by a diagonal shift
    #This may have negative effect on the quality of results, but not
    #doing this leads to problems.
    for i, j in enumerate(includedindices):
        km[i,j] += 0.0001
    print "Kernel matrix shifted and ready"
    print km
    print 'Creating sparse RLS...'
    rls = SparseRLS.SparseRLS(km, Y, includedindices)
    print 'sparse RLS ready'
    rls.solve(regparam)
    W = rls.getHyperplane(fspace_dim, includedindices, datavector)
    f = open(output_file,'w')
    output = "".join("%f " %(x[0,0]) for x in W)+"\n"
    f.write(output)
    f.close()

