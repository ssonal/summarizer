from __future__ import division
import re
import numpy as np
from goose import Goose
import nltk.data
from nltk.corpus import stopwords
from nltk.stem.porter import *
from nltk.tokenize import word_tokenize, sent_tokenize
import sys

# summarizer class - adopted from - http://thetokenizer.com/, https://gist.github.com/shlomibabluki/5473521

class summarizer(object):
    
#   split a paragraph into sentences.
    def splitToSentences(self, content):
        # tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        return sent_tokenize(content)
       
#    split text into paragraphs
#    need to find out if there is a better way to do this with nltk
    def splitToParagraphs(self, content):
        return content.split("\n\n")
        
        
#   get the intersection between two sentences
#   using python native intersection function 
#   to find if an item of a set exist in another set
    def getIntersection(self, s1, s2):
        s1 = set(s1)
        s2 = set(s2)
        
#       if the sentences are empty the rank of this will be 0
        if (len(s1) + len(s2)) == 0:
            return 0
        
#       return the length of the intersection divided by half the length of the two original sentences
        return len(s1 & s2)/((len(s1) + len(s2))/2.)
        
        
#   purify a sentence, we use this to create a key for an object form a sentence, 
    def sentenceKey(self, sentence):
        sentence = re.sub( r'\W+', '', sentence)
        return sentence
    
#    stem a sentence
    def stemSentence(self, sentence, stemmer):
        words = [stemmer.stem(word) for word in sentence]
        return words
    
#    steam and remove any stop words form a sentence
#    this will remove words such as 'The', 'and', 'or' that has 
#    no value in regard to the value of the sentence
    def stemAndRemoveStopWords(self, sentence, stemmer ):  
           s = word_tokenize(sentence)
           s = [w for w in s if not w in stopwords.words('english')]
           s = self.stemSentence(s, stemmer)
           return s
    
#   this function is the heart of the summerize
#   here we'll give each sentence rank based on 
#   how many words it has in similarity to other sentences
    def rankSentences(self, content):
        
#       create a list of all sentences
        paragraphs = self.splitToParagraphs(content)

        # sentences = self.splitToSentences(content)
        sentences = []
        
        for p in paragraphs:
            s = self.splitToSentences(p) 
            for x in s:
                sentences.append(x)
            
        n = len(sentences)
        # print sentences[:4]
#       stem and remove stopwords
        stemmer = PorterStemmer()
        clean_sentences = [ self.stemAndRemoveStopWords(x, stemmer) for x in sentences]
        
#       create an empty values set and fill it with the 
#       intersection value with all the other sentences
        # values = [ [0 for x in xrange(n)] for x in xrange(n) ]
        values = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                values[i][j] = self.getIntersection(clean_sentences[i], clean_sentences[j])
        
#       create sentence dictionary set and fill it with the accumulated value of each sentence
        sentence_dictionary = {}
        values = np.dot(values, (np.ones((n,n)) - np.eye(n)))
        score = np.sum(values, axis=1)
        sentence_dictionary = {self.sentenceKey(sentences[i]):score[i] for i in range(n)}
        
        return sentence_dictionary


#   get the best sentence from each paragraph
    def getBestSentence(self, paragraph, sentence_dictionary):
        sentences = self.splitToSentences(paragraph)
        
#       ignore sentences that are too short
        if len( sentences ) < 2:
            return ""
         
        best_sentence = ""
        max_score = 0
        
#       loop through each sentence and find it its value 
#       in the sentence dictionary is the highest in the paragraph
        for s in sentences:
            key = self.sentenceKey(s)
            if key:
                  if sentence_dictionary[key] > max_score:
                    max_score = sentence_dictionary[key]
                    best_sentence = s
        
        return best_sentence
        
        
        
#   summarize the text    
    def summarize(self, content, sentence_dictionary, title):
        
        paragraphs = self.splitToParagraphs(content)
        summary = []
        
#       this is actually not recommanded as the title many times is not relevant for the topic
#       or written in a provocative way, many times a title will be the opposite of the subject
        if title:
            summary.append(title.strip())
            summary.append("")
        
        for p in paragraphs:
            sentence = self.getBestSentence(p, sentence_dictionary)
            if sentence:
                summary.append(sentence)
        
        return ("\n").join(summary)
        


#---------------------------------end of summarizer class ---------------------------------#
   
# using the Goose library to extract the content of a url
def get_content(url):    
    g = Goose()
    article = g.extract(url=url)
    
    return article.title, article.cleaned_text

# Summarize the content
def summarize(content, title, summarizer, max_len):
    
    sentence_dictionary = summarizer.rankSentences( content )  
    summary = summarizer.summarize(content, sentence_dictionary, title)
    return summary


# grab the content of a url and return a summarized version of it
def URLSummarizer(url, max_len):
    pat = ['/[.*/]',]
    title, content = get_content( url )
    content =   re.sub(pat[0], "", content)
    print len(content)
    sm = summarizer()
    return summarize( content, title, sm, max_len )


if __name__ == '__main__':
    
    if len( sys.argv ) > 1:
        url = sys.argv[1]
        max_len = sys.argv[2]
    else:
        url = "http://www.fullstackpython.com/django.html"
        max_len = 2500
    summary = URLSummarizer( url, max_len )
    print len(summary)
    print summary.encode('UTF-8')
