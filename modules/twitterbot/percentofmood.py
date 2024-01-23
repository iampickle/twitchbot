import os
import json
from ..twitter import *
from .GerVADER.vaderSentimentGER import SentimentIntensityAnalyzer
from .db import *
from dotenv import load_dotenv
load_dotenv()

vaderanalyzer = SentimentIntensityAnalyzer()


def moodpercent(results, channel, dbid=''):
    allwords = []
    # ofile = os.path.join(workdir, 'output.txt')
    # with open(str(ofile), 'r') as fr:
    for line in results:
        # line = str(line.rstrip())
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

    if os.environ.get("db-host") and dbid != None:
        db = database()
        db.dump_array_via_id(dbid, 'emotions', [all_neg, all_pos, all_neu])
        db.cd()

    text = '#'+channel+' Die Stimmung im Stream war,\nzu ' + \
        str(all_neg)+'% neagtiv😡,'+'\nzu '+str(all_pos ) \
        +'% positiv😊,'+'\nund zu '+str(all_neu)+'% neutral😐'
    # +'\n\nai-tweet-test: '+aisent

    # tweet sentiment
    tweet_text(text)
