#Does leave-one-document cross-validation on the training set for
#the purpose of choosing the regularization parameter, and possibly
#the threshold separating the negative and positive classes.

import sys

from numpy import *

import SparseRLS
import PerformanceMeasures
import gzip
import Kernel
from math import sqrt
import random
from Utilities import optimalFThreshold
floattype = float64
import FileReader
from optparse import OptionParser

def getOptions():
    optparser = OptionParser(usage="%prog [options]\n-h for help\nProgram does leave-one-document out cross-validation, where on each round all pairs related to a given document are left out.")
    optparser.add_option("-i", "--input", dest="input", help="training data file", metavar="FILE")
    optparser.add_option("-o", "--output", dest="output", help="output file, where the predictions from the cross-validation are stored", metavar="FILE")
    optparser.add_option("-p", "--parameters", dest="params", help="Parameter file, where the F-score results of running the cross-validation are stored, together with parameters that resulted in the F-scores.", metavar="FILE")
    optparser.add_option("-r", "--reggrid", dest="reggrid", help="The grid to be searched for optimal regularization parameter. Given in formate a_b, which is interpreted as 2^a...2^b. Thus -5_5 will mean a grid 2^-5, 2^-4 ... 2^5", default="-10_10")
    optparser.add_option("-b", "--bvectors", type="int", dest="bvectors", help="Number of basis vectors used. If this exceeds the size of the training set, all of the training examples are used as basis vectors.", metavar="FILE", default=500)
    optparser.add_option("-s", "--seed", type="int", dest="seed", help="Random seed number for sampling the basis vectors.", default=13)
    (options, args) = optparser.parse_args()
    if not options.input:
       optparser.error("No input file defined")
    if not options.output:
        optparser.error("No output file defined")
    reggrid = options.reggrid
    reggrid = reggrid.split("_")
    try:
        lower = int(reggrid[0])
        upper = int(reggrid[1])
    except ValueError:
        optparser.error("Malformed regularization grid supplied")
    if lower >= upper:
        optparser.error("First value of the regularization parameter grid is not smaller than the last")
    if lower < -30 or upper > 30:
        optparser.error("The values supplied for the regularization parameter grid are unreasonably large/small\nRemember, the supplied values are logarithms of the actual values used during training.\nLeaving the values unspecified will use the default grid, which should usually be quite reasonable.")
    return options, args


if __name__=="__main__":
    options, args = getOptions()
    filename = options.input
    output_file = options.output
    parameter_file = options.params
    bv_count = options.bvectors
    rseed = options.seed
    print 'Reading data'

    f = gzip.GzipFile(filename)
    identities, datavector, Y, fspace_dim = FileReader.readData(f, "l")

    instanceids_to_indices = {}
    indices_to_instanceids = {}
    folds = {}
    #Instantiate the document-based folds
    for i, identity in enumerate(identities):
        docid = identity.split(".")[1]
        instanceids_to_indices[identity] = i
        indices_to_instanceids[i] = identity
        if not docid in folds:
            folds[docid] = []
        folds[docid].append(i)
    folds = folds.values()
    #We split the instances from the outputs for the fun of it
    if len(datavector) < bv_count:
        bv_count = len(datavector)

    tsetsize = len(datavector)
    reggrid = options.reggrid.split("_")
    loglambdavec = range(int(reggrid[0]), int(reggrid[1])+1)
    results = []
    predictions = [[] for x in range(len(loglambdavec))]
    correct = []
    bestperf = -1000000.
    bestloglambda = None
    bestindex = 0
    print "Reading and linearizing data"

    kernel = Kernel.Kernel()

    #Sparse version is created next
    random.seed(rseed)
    indices = range(tsetsize)
    #As experimentally shown by Rifkin, random sampling
    #seems to be as good way of choosing basis vectors as any
    includedindices = random.sample(indices, bv_count)
    includedindices.sort()
    indices = list(set(indices).difference(includedindices))

    print "Generating kernel matrix"
    #We create a basis_vectors*training_set sized kernel matrix
    km = mat(zeros((bv_count,tsetsize), dtype=floattype))

    #Instantiate the kernel matrix
    #This could be optimized, because the kernels between the basis
    #vectors are in this version each counted twice, as the symmetry
    #of the bv-indexed submatrix is not taken advantage of.
    for i in range(bv_count):
        for j in range(tsetsize):
            val = kernel.kernel(datavector[includedindices[i]], datavector[j])
            km[i,j] = val

    #free possibly some memory
    del(datavector)

    #Force positive definitivness of the submatrix by a diagonal shift
    for i, j in enumerate(includedindices):
        km[i,j] += 0.0001
    print "Kernel matrix shifted and ready"
    print km
    print 'Creating sparse RLS...'
    rls = SparseRLS.SparseRLS(km, Y, includedindices)
    print 'sparse RLS ready'
    for loglambdaindex in range(0, len(loglambdavec)):
        loglambda = loglambdavec[loglambdaindex]
        print
        print 'loglambda', loglambda
        lamb = (2.) ** loglambda
        rls.solve(lamb)
        favg = 0.
        #For each foldindex
        TP = 0.
        FP = 0.
        FN = 0.
        TN = 0.
        for foldind in range(len(folds)):
            #Pick a fold
            fold = folds[foldind]
            fold_complement = list(set(range(tsetsize)).difference(fold))
            #Calculate predictions for the holdout set
            HO = rls.rectangularCV(fold, fold_complement)
            for prediction in HO.A:
                predictions[loglambdaindex].extend(prediction)
            #For each indice in the fold
            if loglambdaindex == 0:
                for ind1 in range(len(fold)):
                    real_inst_ind = fold[ind1]
                    correct.append(Y[real_inst_ind, 0])
        F, prec, rec, threshold = optimalFThreshold(predictions[loglambdaindex], correct)
        print "Threshold:", threshold
        print "Precision:", prec
        print "Recall:", rec
        print "F:", F
        results.append((F, prec, rec, threshold))
        if F > bestperf:
            bestperf = F
            bestloglambda = loglambda
            bestindex = loglambdaindex
        print 'Average F-score:', F, "(best so far", bestperf, "with loglambda", bestloglambda, ")"
        print 'Best F1',bestperf*100,'% (loglambda', bestloglambda,')'
    if options.params:
        f = open(parameter_file,'w')
        for loglambda, perf in zip(loglambdavec, results):
            f.write("loglambda:%d threshold:%f F:%f P:%f R%f\n" %(loglambda, perf[3], perf[0], perf[1], perf[2]))
        f.close()
    f = open(output_file,'w')
    for pred, cor in zip(predictions[bestindex], correct):
        f.write("%f %f\n" %(pred, cor))
    f.close()
