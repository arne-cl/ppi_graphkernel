#Does the predictions with a trained learner

import sys
import FileReader
import gzip
from optparse import OptionParser

def getOptions():
    optparser = OptionParser(usage="%prog [options]\n-h for help")
    optparser.add_option("-i", "--input", dest="input", help="Gzipped file containgin the test data")
    optparser.add_option("-o", "--output", dest="output", help="Output file for writing the predictions")
    optparser.add_option("-m", "--model", dest="model", help="Model file containing the coefficients corresponding to the learned hypothesis")
    (options, args) = optparser.parse_args()
    if not options.input:
        optparser.error("No input file defined")
    if not options.output:
        optparser.error("No output file defined")
    return options, args

if __name__=="__main__":
    options, args = getOptions()
    instance_file = options.input
    model_file = options.model
    output_file = options.output
    f = open(model_file)
    W = f.readline().strip().split()
    W = [float(x) for x in W]
    f.close()

    f = gzip.GzipFile(instance_file)
    identities, datavector, Y, feaspace_dim = FileReader.readData(f, 'l')
    f.close()

    outputs = []

    for instance in datavector:
        prediction = 0.
        for key in instance.keys():
            value = instance[key]
            if key < len(W):
                prediction += value*W[key]
        outputs.append(prediction)
    f = open(output_file, 'w')
    for identity, prediction, correct in zip(identities, outputs, Y):
        correct = correct[0,0]
        f.write("%s %f %f\n" %(identity, correct, prediction))
    f.close()
