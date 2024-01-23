import json

from deepmultilingualpunctuation import PunctuationModel
from germansentiment import SentimentModel


class analyser:

    textmodel = PunctuationModel()
    model = SentimentModel()

    def __init__(self, outputpath):
        self.outputpath = outputpath

    def analyse_text(self, text):
        return self.model.predict_sentiment([text], output_probabilities=True)[-1][0]

    def readfile(self):
        try:
            ofile = open(self.outputpath, 'r')
        except Exception as e:
            print("something wrong with opening the file:\r"+e)
        text = ""
        for line in ofile:
            try:
                line = str(line.rstrip())
                line = line.replace("\"", ",")
                line = line.replace("\'", "\"")
                line = json.loads(line)
                text += ' '+line['word']
            except Exception as e:
                print(line)
                print(e)
                pass

        print("done with text, starting puctuation")
        result = self.textmodel.restore_punctuation(text)
        print("done with puntuation starting sentiment analysis")
        return self.analyse_text(result)
