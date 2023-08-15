import json
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
import uuid
from ..twitter import *
import os

def countsaidwords(workdir, channel):
    name = str(uuid.uuid4())+'.png'
    filename = os.path.join(workdir, name)
    txt = os.path.join(workdir, 'output.txt')
    darray = []
    farray = []
    with open(txt, 'r') as datafile:
        for line in datafile:
            try:
                line = str(line.rstrip())
                line = line.replace("\"", ",")
                line = line.replace("\'", "\"")
                line = json.loads(line)
            except:
                pass
            time = line['start'] // 60
            farray.append(time)
    
    median_words = sum(farray) / len(farray)      
    
    plt.style.use('dark_background')
    plt.hist(farray, bins=120)
    plt.title(f'Word-Count over Time:{channel}')
    plt.ylabel('Words')
    plt.xlabel('Time in Minutes')
    plt.axhline(median_words, color='#fc4f30', label='Durchschnitt')
    plt.legend()
    plt.savefig(filename)
    tweet_pic(filename, f"chart of word count over stream from: {channel}") 
