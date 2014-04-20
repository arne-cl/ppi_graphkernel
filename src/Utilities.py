import sys

#Utility functions

def optimalFThreshold(predictions, correct):
    """Seeks the optimal threshold in terms of F-score for dividing
    the positive and negative classes"""
    assert len(predictions) == len(correct)
    pairs = [(predictions[i], correct[i]) for i in range(len(predictions))]
    pairs.sort(compare)
    best = 0.

    real_positives = 0
    for c in correct:
        if c == 1.:
            real_positives += 1
    real_negatives = len(correct) - real_positives

    TP = real_positives
    FP = real_negatives
    FN = 0
    F, P, R = F1(TP, FP, FN)
    threshold = pairs[0][0]-1.
    
    for i in range(0, len(pairs)):
        #print "TP%d: FP:%d FN:%d" %(TP, FP, FN) 
        pair = pairs[i]
        if pair[1] == -1:
            FP -= 1
        else:
            TP -= 1
            FN += 1
        F_score, prec, rec = F1(TP, FP, FN)
        if F_score > F:
            F = F_score
            P = prec
            R = rec
            threshold = pair[0]+0.00000001
    return F, P, R, threshold

def F1(TP, FP, FN):
    if (TP == 0. and (FP == 0. or FN == 0.)):
        F = 0.
        prec = 0
        rec = 0
    else:
        prec = float(TP) / float(TP+FP)
        rec = float(TP) / float(TP + FN)
        if (prec == 0 and rec == 0):
            F = 0.
        else:
            F = (2.*prec*rec)/(prec+rec)
    return F, prec, rec

def compare(x,y):
    if x[0]>y[0]:
        return 1
    elif x[0] == y[0]:
        return 0
    else:
        return -1

if __name__=="__main__":
    #This calculates F-score using the optimal threshold.
    #This will result in overoptimistic results, thus do
    #not use this for performance evaluation, only for
    #parameter selection.
    f = sys.stdin
    predictions = []
    correct = []
    for line in f:
        line = line.strip()
        line = line.split()
        predictions.append(float(line[2]))
        correct.append(float(line[1]))
    F, P, R, threshold = optimalFThreshold(predictions, correct)
    print "optimal values: F:%f, P:%f, R:%f, threshold:%f" %(F,P,R,threshold)
