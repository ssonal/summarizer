from __future__ import division
import re
import numpy as np
from goose import Goose
import nltk.data
from nltk.corpus import stopwords
# from nltk.stem.porter import *
from nltk.stem.snowball import *
from nltk.tokenize import word_tokenize, sent_tokenize
import sys


title = ''
# split a paragraph into sentences.
def splitToSentences(content):
    return sent_tokenize(content)
   
# split text into paragraphs
def splitToParagraphs(content):
    return [c for c in content.split("\n") if len(c) is not 0]
      
# get the intersection between two sentences
def getIntersection(s1, s2):
    s1 = set(s1)
    s2 = set(s2)
    
    # if the sentences are empty the rank of this will be 0
    if (len(s1) + len(s2)) == 0:
        return 0
    
    # return the length of the intersection divided by half the length of the two original sentences
    return len(s1 & s2)/((len(s1) + len(s2))/2.)
    
# create a key for an object from a sentence
def sentenceKey(sentence):
    sentence = re.sub(r'\W+', '', sentence)
    return sentence

# stem and remove any stop words form a sentence
def stemAndRemoveStopWords(sentence, stemmer):  
    s = word_tokenize(sentence)
    s = [w for w in s if not w in stopwords.words('english')]
    s = [stemmer.stem(word) for word in s]
    return s

def rankSentences(content):
    # create a list of all sentences
    paragraphs = splitToParagraphs(content)

    # sentences = splitToSentences(content)
    sentences = []
    
    for p in paragraphs:
        s = splitToSentences(p) 
        for x in s:
            sentences.append(x)
        
    n = len(sentences)
    # print sentences[:4]
    
    # stem and remove stopwords
    # stemmer = PorterStemmer()
    stemmer = SnowballStemmer("english")
    clean_sentences = [stemAndRemoveStopWords(x, stemmer) for x in sentences]
    
    # Create the sentence adjacency matrix
    values = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            values[i][j] = getIntersection(clean_sentences[i], clean_sentences[j])
    
    # create sentence dictionary set and fill it with the accumulated value of each sentence
    sentence_dictionary = {}
    values = np.dot(values, (np.ones((n,n)) - np.eye(n)))
    score = np.sum(values, axis=1)
    sentence_dictionary = {sentenceKey(sentences[i]):score[i] for i in range(n)}
    
    return sentence_dictionary


# get the best sentence from each paragraph
def getBestSentence(paragraph, sentence_dictionary):
    sentences = splitToSentences(paragraph)
    
    # ignore sentences that are too short
    # if len(sentences) < 2:
    #     return ""
     
    best_sentence = ""
    max_score = 0
    
    # loop through each sentence and find it its value 
    # in the sentence dictionary is the highest in the paragraph
    for s in sentences:
        key = sentenceKey(s)
        if key:
            if sentence_dictionary[key] > max_score:
                max_score = sentence_dictionary[key]
                best_sentence = s
    
    return best_sentence
    
    
    
# summarize the text    
def summarize(content, sentence_dictionary):
    global title
    paragraphs = splitToParagraphs(content)
    
    # for para in paragraphs:
    #     print para.encode('UTF-8')
    #     raw_input()
    summary = []
    
    if title:
        summary.append(title.strip())
        summary.append("")
    
    for p in paragraphs:
        sentence = getBestSentence(p, sentence_dictionary).strip()
        if sentence:
            summary.append(sentence)
    
    return ("\n").join(summary)
    

# using the Goose library to extract the content of a url
def get_content(url):    
    g = Goose()
    article = g.extract(url=url)
    
    return article.title, article.cleaned_text

# Summarize the content
def doSummary(content, max_len): 
    sentence_dictionary = rankSentences(content)  
    summary = summarize(content, sentence_dictionary)
    return summary


# grab the content of a url and return a summarized version of it
def parseURL(url, max_len):
    global title
    pat = ['/[.*/]', '[\n\s].*([0-9]+.)']#, '((\n|.\s+)[A-Za-z0-9]+/)\s+']
    title, content = get_content(url)
    for pattern in pat:
        content =   re.sub(pattern, "", content)

    return doSummary(content, max_len)


if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        max_len = sys.argv[2]
    else:
        url = "http://grad.berkeley.edu/admissions/apply/statement-purpose/"
        max_len = 2500

    summary = parseURL(url, max_len)
    print summary.encode('UTF-8')
