def loadInteractionWords(filename):
    if filename.find(".") != -1:
        extension = filename.rsplit(".",1)[-1]
    else:
        extension = ""
    
    if extension == "riw": # Relex Interaction Words
        return loadRelexInteractionWords(filename)
    else:
        return loadInteractionWordsFromList(filename)

def loadRelexInteractionWords(filename):
    allWords = []
    f = open(filename)
    for line in f:
        text = line.strip()
        stem, words = text.split(":")
        words = words.split("|")
        allWords.extend(words)
    f.close()
    return allWords

def loadInteractionWordsFromList(filename):
    allWords = []
    f = open(filename)
    for line in f:
        text = line.strip()
        allWords.append(text)
    f.close()
    return allWords
