PPI-learning with all-dependency-paths kernel
=============================================

This is my "fork" of the graph kernel implemented in Python by
Airola et al. (2008), which is described
`on their website <http://mars.cs.utu.fi/PPICorpora/GraphKernel.html>`_.
My intention for playing with the original code is to understand graph kernels
on dependency graphs better.

So far, I have made the following changes:

- structured the codebase into a package `ppi_graphkernels` and subpackages
- added a setup.py to install the package system-wide with dependencies
- added documentation to some methods/functions
- replaced some JAVAisms with more 'pythonic' code

The rest of this document contains the original README (converted to
restructuredText).


SOFTWARE FOR PPI-EXTRACTION WITH GRAPH KERNELS
----------------------------------------------

This package contains an implementation of the all-dependency-paths graph kernel
described in the paper "A Graph Kernel for Protein-Protein Interaction
Extraction", presented at the ACL 2008 BioNLP Workshop. In addition, many of the
scripts used in experiments done with the kernel are provided, including software
for preprocessing the data, an implementation of the Sparse RLS learning
algorithm, and software for doing efficient cross-validation using the algorithm.

The graph kernel is based on calculating the similarities of dependency graph
representations of sentences. Thus prior to running the system you should parse
your sentences with a parser capable of supplying such analysis, and supply
this infomation in the xml format used by the system. The system has been
developed based on the collapsed Stanford format.

The analysis xml format that the graph kernel software processes is derived from
the xml format used for the transformations introduced in the paper "Comparative
Analysis of Five Protein-protein Interaction Corpora" presented at the LBM07
conference. The transformation software for five publicly available corpora is
available at

http://mars.cs.utu.fi/PPICorpora/

These are the same corpora for which the test results for the graph-kernel are
reported for. The fold-split used when cross-validating on the full corpora
is also provided. 

Note that many of the scripts assume that the input and output files are compressed
in the gzip format.

This is research software, provided as is without express or implied warranties
etc. see licence.txt for more details. We have tried to make it reasonably usable and
provided help options, but adapting the system to new environments or transforming
a corpus to the format used by the system may require significant effort. 
Contact us in case of having problems or requiring further information about the
experimental procedure used when testing the kernel.

QUICKSTART
----------

Note that most of the scripts used here have -h (help) option you can use
to check available options.

Example files, such as the binarized version of the BioInfer corpus are provided in
the xml format processed by the system. To train a system on a file CORPUS.XML, which
contains a parse produced by MYPARSER and a tokenization produced by MYTOKENIZER,
proceed as follows (in the example file MYPARSER = split_parse and
MYTOKENIZER = split).

Script named ConvertCorpus.py can be used to transform the xml format used
in the aforementioned LBM07 paper to the format used by the graph kernel
software. The resulting file will still need parses and tokenizations.
Once they are in the script HyphenSplitter.py can be used to modify the
tokenization and parse so that tokens such as "actin-binding" are split in
two, so that words such as "binding" in this case will not be blinded when protein
names are blinded.

First, build a dictionary that maps the possible features to a running indexing.

::

    python BuildDictionaryMapping.py -i CORPUS.XML.gz -p MYPARSER -t MYTOKENIZER
    -o dictionary.txt.gz

Second, compute the graph kernels for your data, producing a linearized feature
representation corresponding to the graph kernels.

::

    python LinearizeAnalysis.py -i CORPUS.XML.gz -o LinearCorpus.gz -p MYPARSER
    -t MYTOKENIZER

The software can be run in two modes, which affect how the G matrix is
constructed. "-m max" is the default option which corresponds to how


Should you wish to convert a data file containing separate test
data, linearize it using the dictionary produced from the training
data. Still, there is no harm in creating the dictionary from a file that
contains both the training and test data, the features that appear only in
the test data will not affect the learned hypothesis for the RLS learner.
Thus for cross-validation the dictionary doesn't have to be reformed for
each split.

Third, you can normalize the data vectors to unit length. Sometimes this
can boost the results, sometimes it makes them worse.

::

    python NormalizeData.py -i LinearCorpus.gz -o NormalizedCorpus.gz

From now on, let us assume that you have created two data files linearized
using a dictionary created from the training data. One of them is the
TRAIN_SET, and one the TEST_SET.

To choose optimal parameters (according to F-score), you can do leave-one
document-out cross-validation on the TRAIN_SET.

::

    python CrossValidate.py -i TRAIN_SET -o CV_predictions.o -p Parameters.p
    -r -10_10 -b 500

This command will run cross-validation on the sparse RLS algorithm using
500 basis vectors (or less, if your data set is smaller that that).
The predictions for each data point are written to CV_predictions.o
file, and the F-score results with different parameter values to file
Parameters.p. The serached grid for the regularization parameter is
in this example 2^-10 ... 2^10.

To build a model using these learned parameters you can run

::

    python TrainLinearized.py -i TRAIN_SET -p Parameters.p -b 500
    -o Model.m

Alternatively you can supply the value of the regularization
paremeter directly with the r -option.

To make predictions with this model run

::

    python TestLinearized.py -i TEST_SET -m Model.m -o Predictions

When calculating the performance, use the threshold selected
in cross-validation, if your performance metric needs such a
thing. Separating the classes at zero can produce quite bad results.
Be aware that selecting the threshold on the training data can
also fail, if the "identically distributed" assumption does not
hold between the training and test data.
