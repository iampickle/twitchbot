import os
import json
from ..twitter import *
from .GerVADER.vaderSentimentGER import SentimentIntensityAnalyzer

vaderanalyzer = SentimentIntensityAnalyzer()

def moodpercent(workdir, channel):
    allwords = []
    ofile = os.path.join(workdir, 'output.txt')
    with open(str(ofile), 'r') as fr:
        for line in fr:
            line = str(line.rstrip())
            line = line.replace("\"", ",")
            line = line.replace("\'", "\"")
            try:
                line = json.loads(line)
                if line['conf'] >= 0.8:
                    allwords.append(line['word'])
            except:
                pass


    longsentence = ' '.join(allwords)

    vs = vaderanalyzer.polarity_scores(longsentence)
    all_neg = round(vs['neg'] * 100, 3)
    all_pos = round(vs['pos'] * 100, 3)
    all_neu = round(vs['neu'] * 100, 3)


    text = '#'+channel+' Die Stimmung im Stream war,\nzu '+str(all_neg)+'% neagtiv😡,'+'\nzu '+str(all_pos)+'% positiv😊,'+'\nund zu '+str(all_neu)+'% neutral😐'
    #+'\n\nai-tweet-test: '+aisent

    # tweet sentiment
    tweet_text(text)